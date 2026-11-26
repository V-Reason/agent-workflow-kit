"""Plan and apply deterministic project assembly."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import KIT_VERSION, WORKFLOW_VERSION
from .errors import UsageError
from .lockfile import (
    LOCK_PATH,
    PROFILE_PATH,
    ManagedFileRecord,
    ProjectProfile,
    WorkflowLock,
    lock_by_key,
    render_lock,
    render_profile,
)
from .merge import (
    apply_managed_block,
    decode_text,
    extract_managed_block,
    git_worktree_dirty,
    is_sensitive_path,
    merge_json_missing,
    normalize_relpath,
    render_placeholders,
    sha256_bytes,
    target_path,
)
from .profile import (
    Profile,
    discover_profiles,
    expand_layers,
    profile_fingerprint,
    profile_label,
)

_TEXT_SUFFIXES = {
    "",
    ".bat",
    ".cfg",
    ".cmd",
    ".cs",
    ".css",
    ".editorconfig",
    ".gitattributes",
    ".gitignore",
    ".html",
    ".ini",
    ".json",
    ".md",
    ".ps1",
    ".py",
    ".sh",
    ".toml",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}


@dataclass
class PlannedFile:
    path: str
    content: bytes
    ownership: str
    layers: set[str] = field(default_factory=set)
    block_id: str | None = None


@dataclass
class AssemblyResult:
    status: str
    project: Path
    project_name: str
    layers: list[dict[str, str]]
    profile_hash: str
    changes: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    protected: list[str] = field(default_factory=list)
    dry_run: bool = False

    @property
    def exit_code(self) -> int:
        return 0 if self.status in {"ok", "dry-run"} else 2

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "project": str(self.project),
            "project_name": self.project_name,
            "workflow_version": WORKFLOW_VERSION,
            "kit_version": KIT_VERSION,
            "layers": self.layers,
            "profile_hash": self.profile_hash,
            "changes": self.changes,
            "skipped": self.skipped,
            "conflicts": self.conflicts,
            "protected": self.protected,
            "dry_run": self.dry_run,
        }


def _is_text_candidate(path: Path) -> bool:
    name = path.name.lower()
    suffix = path.suffix.lower()
    return suffix in _TEXT_SUFFIXES or name in {
        ".editorconfig",
        ".gitattributes",
        ".gitignore",
        ".python-version",
    }


def _source_path(kit_root: Path, profile: Profile, source: str) -> Path:
    if source.startswith("kit:"):
        candidate = (kit_root / source[4:]).resolve()
        try:
            candidate.relative_to(kit_root.resolve())
        except ValueError as exc:
            raise UsageError(f"profile source 逃逸 kit 根：{source}") from exc
        return candidate
    return (profile.root / source).resolve()


def _read_source(
    path: Path,
    relative_for_error: str,
    variables: dict[str, str],
    *,
    render_templates: bool,
) -> bytes:
    if not path.is_file():
        raise UsageError(f"profile source 不存在：{relative_for_error}（{path}）")
    data = path.read_bytes()
    if not _is_text_candidate(path):
        return data
    text = decode_text(data, relative_for_error)
    if not render_templates:
        return data
    try:
        rendered = render_placeholders(text, variables)
    except UsageError:
        if "{{" not in text:
            raise
        raise
    return rendered.encode("utf-8")


def _excluded(relative: Path, patterns: list[str]) -> bool:
    normalized = relative.as_posix()
    parts = relative.parts
    return any(
        fnmatch.fnmatch(normalized, pattern)
        or fnmatch.fnmatch(relative.name, pattern)
        or pattern.rstrip("/") in parts
        for pattern in patterns
    )


def _tree_sources(source: Path) -> list[Path]:
    if not source.is_dir():
        raise UsageError(f"copy_tree source 不是目录：{source}")
    return sorted(path for path in source.rglob("*") if path.is_file())


def _safe_source_relative(path: Path, root: Path) -> str:
    if path.is_symlink():
        raise UsageError(f"拒绝符号链接 source：{path}")
    try:
        relative = path.relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise UsageError(f"profile source 逃逸 profile 根：{path}") from exc
    if is_sensitive_path(relative):
        raise UsageError(f"拒绝装配敏感 source：{relative}")
    return relative


def _validate_profile_detection(
    project_root: Path,
    layers: list[Profile],
    mode: str,
) -> None:
    if mode == "sync":
        return
    for profile in layers:
        if profile.id in {"core", "generic"}:
            continue
        if profile.id.startswith("python") and mode == "create":
            continue
        if profile.detects(project_root):
            continue
        requirements = [*profile.detect_all, *profile.detect_any]
        raise UsageError(
            f"项目不匹配 profile {profile.id}；至少需要检测到：{', '.join(requirements)}"
        )


def _derive_variables(name: str, variables: dict[str, str]) -> dict[str, str]:
    slug = "".join(
        character.lower() if character.isalnum() else "-"
        for character in name
    ).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    derived = {
        "project_name": name,
        "project_slug": slug or "project",
        "python_package": (slug.replace("-", "_") or "app"),
    }
    derived.update({key: str(value) for key, value in variables.items()})
    return derived


def _conflict_report(result: AssemblyResult) -> str:
    lines = [
        "# Workflow Assembly Conflicts",
        "",
        f"Workflow Version: {WORKFLOW_VERSION}",
        f"Project: {result.project_name}",
        "",
        "没有写入任何托管文件。请解决以下冲突后重跑同一命令。",
        "",
        "## Conflicts",
    ]
    if result.conflicts:
        lines.extend(f"- {item}" for item in result.conflicts)
    else:
        lines.append("- 无")
    lines.extend(["", "## Protected Changes"])
    if result.protected:
        lines.extend(f"- {item}" for item in result.protected)
    else:
        lines.append("- 无")
    lines.extend(
        [
            "",
            "确认允许受保护配置变更时可追加 `--accept-protected`。",
            "",
        ]
    )
    return "\n".join(lines)


def _apply_changes(
    project_root: Path,
    changes: dict[str, bytes],
) -> None:
    created_files: list[Path] = []
    previous: dict[Path, bytes | None] = {}
    try:
        for relative, content in sorted(changes.items()):
            destination = target_path(project_root, relative)
            previous[destination] = destination.read_bytes() if destination.is_file() else None
            destination.parent.mkdir(parents=True, exist_ok=True)
            if previous[destination] is None:
                created_files.append(destination)
            destination.write_bytes(content)
    except Exception:
        for destination, data in reversed(list(previous.items())):
            try:
                if data is None:
                    if destination in created_files and destination.exists():
                        destination.unlink()
                else:
                    destination.write_bytes(data)
            except OSError:
                pass
        raise


def assemble_project(
    *,
    kit_root: Path,
    project_root: Path,
    layer_ids: list[str],
    name: str | None,
    variables: dict[str, str] | None,
    extra_profile_roots: tuple[Path, ...] = (),
    mode: str = "create",
    dry_run: bool = False,
    accept_protected: bool = False,
    allow_dirty: bool = False,
    old_lock: WorkflowLock | None = None,
) -> AssemblyResult:
    kit_root = kit_root.resolve()
    project_root = project_root.resolve()
    if mode not in {"create", "attach", "sync"}:
        raise UsageError(f"未知装配模式：{mode}")
    project_name = (name or project_root.name).strip()
    if not project_name:
        raise UsageError("项目名称不能为空")
    effective_variables = _derive_variables(project_name, variables or {})

    registry = discover_profiles(kit_root, extra_profile_roots)
    layers = expand_layers(layer_ids, registry)
    if mode == "attach":
        create_only = [profile.id for profile in layers if profile.create_only]
        if create_only:
            raise UsageError(
                "以下 layer 只允许 create，不允许 attach："
                + ", ".join(create_only)
            )
    _validate_profile_detection(project_root, layers, mode)

    if mode != "create" and not project_root.is_dir():
        raise UsageError(f"目标项目不存在：{project_root}")
    if (
        project_root.is_dir()
        and not dry_run
        and not allow_dirty
        and git_worktree_dirty(project_root)
    ):
        raise UsageError(
            "目标 Git 工作区有未提交修改；先清理，或显式传入 `--allow-dirty`"
        )

    profile_hash = profile_fingerprint(layers, effective_variables)
    old_records = lock_by_key(old_lock)
    virtual: dict[str, bytes | None] = {}
    changes: dict[str, bytes] = {}
    skipped: set[str] = set()
    conflicts: list[str] = []
    protected: list[str] = []
    records: dict[tuple[str, str], dict[str, Any]] = {}
    origins: dict[tuple[str, str], str] = {}

    def current_bytes(relative: str) -> bytes | None:
        if relative in virtual:
            return virtual[relative]
        destination = target_path(project_root, relative)
        return destination.read_bytes() if destination.is_file() else None

    def set_current(relative: str, content: bytes) -> None:
        virtual[relative] = content
        if current_bytes_original(relative) != content:
            changes[relative] = content
        else:
            changes.pop(relative, None)

    def current_bytes_original(relative: str) -> bytes | None:
        destination = target_path(project_root, relative)
        return destination.read_bytes() if destination.is_file() else None

    def add_copy_action(
        relative: str,
        content: bytes,
        ownership: str,
        layer_id: str,
        action_key: str,
        protected_change: bool = False,
    ) -> None:
        relative = normalize_relpath(relative)
        key = (relative, "")
        if key in origins and origins[key] != action_key:
            if current_bytes(relative) != content:
                conflicts.append(
                    f"{relative}: profile 层 {origins[key]} 与 {action_key} 写入不同内容"
                )
            return
        origins[key] = action_key
        existing = current_bytes(relative)
        incoming_hash = sha256_bytes(content)

        if ownership == "SEEDED":
            if existing is not None:
                skipped.add(relative)
                return
            set_current(relative, content)
            return

        if ownership == "MERGED_CONFIG" and existing is not None:
            merged, changed = merge_json_missing(existing, content, relative)
            if not changed:
                skipped.add(relative)
            elif protected_change and not accept_protected:
                protected.append(f"{relative}: 需要追加缺失配置项")
            else:
                set_current(relative, merged)
        elif existing is None:
            set_current(relative, content)
        elif existing == content:
            skipped.add(relative)
        elif mode == "attach" and old_lock is None:
            conflicts.append(f"{relative}: 现有文件与 {ownership} 内容不同")
        else:
            old = old_records.get(key)
            if old is None or sha256_bytes(existing) != old.sha256:
                conflicts.append(f"{relative}: 用户已修改或未经本套件管理")
            else:
                set_current(relative, content)

        records[key] = {
            "path": relative,
            "ownership": ownership,
            "layers": {layer_id},
            "block_id": None,
        }

    for profile in layers:
        for action in profile.actions:
            source_root = (
                kit_root
                if str(action["source"]).startswith("kit:")
                else profile.root
            )
            source = _source_path(kit_root, profile, str(action["source"]))
            render_templates = not str(action["source"]).startswith("kit:")
            action_type = str(action["type"])
            target_base = normalize_relpath(str(action["target"]))
            ownership = str(action["ownership"])
            action_key = f"{profile.id}:{action_type}:{target_base}"

            if action_type in {"copy_file", "json_merge"}:
                _safe_source_relative(source, source_root)
                content = _read_source(
                    source,
                    source.name,
                    effective_variables,
                    render_templates=render_templates,
                )
                add_copy_action(
                    target_base,
                    content,
                    "MERGED_CONFIG" if action_type == "json_merge" else ownership,
                    profile.id,
                    action_key,
                    protected_change=action_type == "json_merge"
                    or bool(action.get("protected", False)),
                )
                continue

            if action_type == "copy_tree":
                if not source.is_dir():
                    raise UsageError(f"copy_tree source 不是目录：{source}")
                excludes = [str(value) for value in action.get("exclude", [])]
                for child in _tree_sources(source):
                    relative_to_source = child.relative_to(source)
                    if _excluded(relative_to_source, excludes):
                        continue
                    _safe_source_relative(child, source)
                    target = f"{target_base}/{relative_to_source.as_posix()}"
                    content = _read_source(
                        child,
                        child.as_posix(),
                        effective_variables,
                        render_templates=render_templates,
                    )
                    add_copy_action(
                        target,
                        content,
                        ownership,
                        profile.id,
                        f"{profile.id}:copy_tree:{target_base}:{relative_to_source.as_posix()}",
                        protected_change=bool(action.get("protected", False)),
                    )
                continue

            if action_type == "managed_block":
                _safe_source_relative(source, source_root)
                fragment = decode_text(
                    _read_source(
                        source,
                        source.name,
                        effective_variables,
                        render_templates=True,
                    ),
                    source.name,
                )
                block_id = f"{profile.id}:{action['block_id']}"
                key = (target_base, block_id)
                origins.setdefault(key, action_key)
                existing = current_bytes(target_base)
                existing_text = (
                    decode_text(existing, target_base) if existing is not None else None
                )
                if (
                    old_lock is not None
                    and existing_text is not None
                    and key in old_records
                    and old_records[key].block_id
                ):
                    try:
                        current_fragment = extract_managed_block(
                            existing_text, target_base, block_id
                        )
                    except UsageError as exc:
                        conflicts.append(str(exc))
                        continue
                    if (
                        current_fragment is None
                        or sha256_bytes(current_fragment.encode("utf-8"))
                        != old_records[key].fragment_sha256
                    ):
                        conflicts.append(
                            f"{target_base}: 托管块 {block_id} 已被用户修改或缺失"
                        )
                        continue
                try:
                    merged_text = apply_managed_block(
                        existing_text, target_base, block_id, fragment
                    )
                except UsageError as exc:
                    conflicts.append(str(exc))
                    continue
                rendered = merged_text.encode("utf-8")
                if existing == rendered:
                    skipped.add(target_base)
                else:
                    set_current(target_base, rendered)
                records[key] = {
                    "path": target_base,
                    "ownership": "MANAGED_BLOCK",
                    "layers": {profile.id},
                    "block_id": block_id,
                }
                continue

            raise UsageError(f"未实现 action type：{action_type}")

    def required_exists(relative: str) -> bool:
        relative = relative.replace("\\", "/").rstrip("/")
        if relative in virtual and virtual[relative] is not None:
            return True
        actual = target_path(project_root, relative)
        if actual.exists():
            return True
        prefix = f"{relative}/"
        return any(
            path.startswith(prefix) and content is not None
            for path, content in virtual.items()
        )

    for profile in layers:
        for required in profile.required_paths:
            if not required_exists(required):
                conflicts.append(
                    f"{profile.id}: 必需路径未装配或不存在：{required}"
                )

    profile_file_path = target_path(project_root, PROFILE_PATH)
    desired_profile = render_profile(
        ProjectProfile(
            name=project_name,
            layers=tuple(profile.id for profile in layers),
            variables=effective_variables,
        )
    ).encode("utf-8")
    if mode in {"create", "attach"}:
        existing_profile = (
            profile_file_path.read_bytes() if profile_file_path.is_file() else None
        )
        if existing_profile is not None and existing_profile != desired_profile:
            if old_lock is None:
                conflicts.append(
                    f"{PROFILE_PATH}: 已经存在且不同于本次装配配置"
                )
        else:
            virtual[PROFILE_PATH] = desired_profile
            if existing_profile != desired_profile:
                changes[PROFILE_PATH] = desired_profile

    final_records: list[ManagedFileRecord] = []
    for key, record in sorted(records.items()):
        relative, block_id = key
        content = current_bytes(relative)
        if content is None:
            continue
        fragment_hash: str | None = None
        if record["ownership"] == "MANAGED_BLOCK":
            assert block_id
            text = decode_text(content, relative)
            try:
                fragment = extract_managed_block(text, relative, block_id)
            except UsageError as exc:
                conflicts.append(str(exc))
                continue
            if fragment is None:
                conflicts.append(f"{relative}: 找不到托管块 {block_id}")
                continue
            fragment_hash = sha256_bytes(fragment.encode("utf-8"))
        final_records.append(
            ManagedFileRecord(
                path=relative,
                ownership=str(record["ownership"]),
                sha256=sha256_bytes(content),
                fragment_sha256=fragment_hash,
                block_id=block_id or None,
                layers=tuple(sorted(record["layers"])),
            )
        )

    # A single physical file may contain several managed blocks. The file hash
    # must describe the final state for every record that points to it.
    final_records = [
        ManagedFileRecord(
            path=record.path,
            ownership=record.ownership,
            sha256=(
                sha256_bytes(current_bytes(record.path))
                if current_bytes(record.path) is not None
                else record.sha256
            ),
            fragment_sha256=record.fragment_sha256,
            block_id=record.block_id,
            layers=record.layers,
        )
        for record in final_records
    ]

    if old_lock is not None:
        new_keys = {(record.path, record.block_id or "") for record in final_records}
        for key, record in sorted(old_records.items()):
            if key in new_keys:
                continue
            if target_path(project_root, record.path).exists():
                conflicts.append(
                    f"{record.path}: 新 profile 不再管理该路径；请人工审阅并移除"
                )

    lock = WorkflowLock(
        kit_version=KIT_VERSION,
        workflow_version=WORKFLOW_VERSION,
        project_name=project_name,
        profile_hash=profile_hash,
        layers=tuple(profile.id for profile in layers),
        layer_versions=tuple(
            f"{profile.id}@{profile.version}" for profile in layers
        ),
        files=tuple(final_records),
    )
    if not conflicts:
        desired_lock = render_lock(lock).encode("utf-8")
        existing_lock = (
            (project_root / LOCK_PATH).read_bytes()
            if (project_root / LOCK_PATH).is_file()
            else None
        )
        if existing_lock != desired_lock:
            changes[LOCK_PATH] = desired_lock

    result = AssemblyResult(
        status="blocked" if conflicts or protected else ("dry-run" if dry_run else "ok"),
        project=project_root,
        project_name=project_name,
        layers=[
            {"id": profile.id, "version": profile.version, "label": profile_label([profile])}
            for profile in layers
        ],
        profile_hash=profile_hash,
        changes=sorted(changes),
        skipped=sorted(skipped),
        conflicts=sorted(set(conflicts)),
        protected=sorted(set(protected)),
        dry_run=dry_run,
    )
    if result.status == "blocked" or dry_run:
        return result

    project_root.mkdir(parents=True, exist_ok=True)
    _apply_changes(project_root, changes)
    return result


def write_conflict_report(result: AssemblyResult) -> Path:
    result.project.mkdir(parents=True, exist_ok=True)
    path = result.project / "AI_Context" / "WORKFLOW_CONFLICTS.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_conflict_report(result), encoding="utf-8")
    return path
