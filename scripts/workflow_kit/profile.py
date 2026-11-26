"""Declarative profile discovery, validation, and layer composition."""

from __future__ import annotations

import hashlib
import json
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import PROFILE_SCHEMA_VERSION, WORKFLOW_VERSION
from .errors import UsageError
from .merge import normalize_relpath

_ID_RE = re.compile(r"^[a-z][a-z0-9-]*$")
_ALLOWED_ACTIONS = {"copy_file", "copy_tree", "managed_block", "json_merge"}
_ALLOWED_OWNERSHIP = {"KIT_OWNED", "SEEDED", "MERGED_CONFIG"}


@dataclass(frozen=True)
class Profile:
    id: str
    version: str
    display_name: str
    description: str
    requires: tuple[str, ...]
    conflicts: tuple[str, ...]
    create_only: bool
    detect_all: tuple[str, ...]
    detect_any: tuple[str, ...]
    actions: tuple[dict[str, Any], ...]
    required_paths: tuple[str, ...]
    recommended_gates: tuple[str, ...]
    root: Path
    source_hash: str

    def detects(self, project_root: Path) -> bool:
        if self.detect_all and not all(
            _glob_exists(project_root, pattern) for pattern in self.detect_all
        ):
            return False
        if self.detect_any and not any(
            _glob_exists(project_root, pattern) for pattern in self.detect_any
        ):
            return False
        return True

    def canonical(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "version": self.version,
            "requires": list(self.requires),
            "conflicts": list(self.conflicts),
            "create_only": self.create_only,
            "actions": list(self.actions),
            "source_hash": self.source_hash,
        }


@dataclass
class ProfileRegistry:
    profiles: dict[str, Profile] = field(default_factory=dict)

    def add(self, profile: Profile, replace: bool = False) -> None:
        if profile.id in self.profiles and not replace:
            raise UsageError(f"profile id 重复：{profile.id}（{profile.root}）")
        self.profiles[profile.id] = profile

    def get(self, profile_id: str) -> Profile:
        try:
            return self.profiles[profile_id]
        except KeyError as exc:
            available = ", ".join(sorted(self.profiles))
            raise UsageError(
                f"未知 profile：{profile_id}；可用 profile：{available}"
            ) from exc


def _glob_exists(root: Path, pattern: str) -> bool:
    if not root.exists():
        return False
    return any(candidate.exists() for candidate in root.glob(pattern))


def _as_tuple_strings(value: object, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise UsageError(f"{field_name} 必须是字符串数组")
    return tuple(value)


def _profile_hash(profile_root: Path, raw: bytes, actions: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    digest.update(raw)
    for action in actions:
        source = str(action["source"])
        if source.startswith("kit:"):
            continue
        source_path = (profile_root / source).resolve()
        files = (
            [source_path]
            if source_path.is_file()
            else sorted(path for path in source_path.rglob("*") if path.is_file())
        )
        for file_path in files:
            if file_path.is_symlink():
                raise UsageError(f"profile source 含符号链接文件：{file_path}")
            relative = file_path.relative_to(profile_root.resolve()).as_posix()
            digest.update(b"\0")
            digest.update(relative.encode("utf-8"))
            digest.update(b"\0")
            digest.update(file_path.read_bytes())
    return f"sha256:{digest.hexdigest()}"


def load_profile(path: Path) -> Profile:
    path = path.resolve()
    if not path.is_file():
        raise UsageError(f"profile 不存在：{path}")
    raw = path.read_bytes()
    try:
        data = tomllib.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise UsageError(f"profile TOML 无效：{path}: {exc}") from exc

    schema = data.get("schema_version")
    if schema != PROFILE_SCHEMA_VERSION:
        raise UsageError(
            f"{path}: schema_version 必须是 {PROFILE_SCHEMA_VERSION}，收到 {schema!r}"
        )
    profile_id = data.get("id")
    if not isinstance(profile_id, str) or not _ID_RE.fullmatch(profile_id):
        raise UsageError(f"{path}: id 必须匹配 {_ID_RE.pattern}")
    version = data.get("version")
    if not isinstance(version, str) or not version.strip():
        raise UsageError(f"{path}: version 必须是非空字符串")
    display_name = data.get("display_name", profile_id)
    description = data.get("description", "")
    if not isinstance(display_name, str) or not isinstance(description, str):
        raise UsageError(f"{path}: display_name/description 必须是字符串")

    requires = _as_tuple_strings(data.get("requires"), f"{path}: requires")
    conflicts = _as_tuple_strings(data.get("conflicts"), f"{path}: conflicts")
    create_only = data.get("create_only", False)
    if not isinstance(create_only, bool):
        raise UsageError(f"{path}: create_only 必须是布尔值")
    detection = data.get("detection", {})
    if not isinstance(detection, dict):
        raise UsageError(f"{path}: [detection] 必须是表")
    detect_all = _as_tuple_strings(
        detection.get("all_paths"), f"{path}: detection.all_paths"
    )
    detect_any = _as_tuple_strings(
        detection.get("any_paths"), f"{path}: detection.any_paths"
    )
    required_paths = _as_tuple_strings(data.get("required_paths"), f"{path}: required_paths")
    for required in required_paths:
        normalize_relpath(required)
    gates = _as_tuple_strings(data.get("recommended_gates"), f"{path}: recommended_gates")

    actions_value = data.get("actions", [])
    if not isinstance(actions_value, list):
        raise UsageError(f"{path}: actions 必须是数组")
    actions: list[dict[str, Any]] = []
    for index, action in enumerate(actions_value, start=1):
        if not isinstance(action, dict):
            raise UsageError(f"{path}: action #{index} 必须是表")
        normalized = dict(action)
        action_type = normalized.get("type")
        if action_type not in _ALLOWED_ACTIONS:
            raise UsageError(
                f"{path}: action #{index} type 必须是 {sorted(_ALLOWED_ACTIONS)}"
            )
        source = normalized.get("source")
        target = normalized.get("target")
        if not isinstance(source, str) or not source.strip():
            raise UsageError(f"{path}: action #{index} 缺少 source")
        if not isinstance(target, str) or not target.strip():
            raise UsageError(f"{path}: action #{index} 缺少 target")
        normalize_relpath(target)
        ownership = normalized.get("ownership", "SEEDED")
        if action_type == "managed_block":
            ownership = "MANAGED_BLOCK"
        if ownership not in _ALLOWED_OWNERSHIP and ownership != "MANAGED_BLOCK":
            raise UsageError(
                f"{path}: action #{index} ownership 必须是 "
                f"{sorted(_ALLOWED_OWNERSHIP | {'MANAGED_BLOCK'})}"
            )
        normalized["ownership"] = ownership
        block_id = normalized.get("block_id", profile_id)
        if not isinstance(block_id, str) or not _ID_RE.fullmatch(block_id):
            raise UsageError(f"{path}: action #{index} block_id 无效")
        excludes = normalized.get("exclude", [])
        if not isinstance(excludes, list) or not all(
            isinstance(item, str) for item in excludes
        ):
            raise UsageError(f"{path}: action #{index} exclude 必须是字符串数组")
        if not source.startswith("kit:"):
            source_candidate = path.parent / source
            if source_candidate.is_symlink():
                raise UsageError(
                    f"{path}: action #{index} 拒绝符号链接 source：{source}"
                )
            source_path = source_candidate.resolve()
            try:
                source_path.relative_to(path.parent.resolve())
            except ValueError as exc:
                raise UsageError(
                    f"{path}: action #{index} source 逃逸 profile 根：{source}"
                ) from exc
            if not source_path.exists():
                raise UsageError(
                    f"{path}: action #{index} source 不存在：{source}"
                )
        actions.append(normalized)

    return Profile(
        id=profile_id,
        version=version,
        display_name=display_name,
        description=description,
        requires=requires,
        conflicts=conflicts,
        create_only=create_only,
        detect_all=detect_all,
        detect_any=detect_any,
        actions=tuple(actions),
        required_paths=required_paths,
        recommended_gates=gates,
        root=path.parent,
        source_hash=_profile_hash(path.parent, raw, actions),
    )


def _iter_profile_dirs(path: Path) -> list[Path]:
    path = path.resolve()
    if (path / "profile.toml").is_file():
        return [path]
    if not path.is_dir():
        raise UsageError(f"profile root 不存在：{path}")
    return sorted(
        child for child in path.iterdir() if child.is_dir() and (child / "profile.toml").is_file()
    )


def discover_profiles(
    kit_root: Path,
    extra_roots: tuple[Path, ...] = (),
) -> ProfileRegistry:
    registry = ProfileRegistry()
    roots = [kit_root.resolve() / "profiles", *extra_roots]
    for index, root in enumerate(roots):
        for profile_dir in _iter_profile_dirs(root):
            profile = load_profile(profile_dir / "profile.toml")
            registry.add(profile, replace=index > 0)
    if "core" not in registry.profiles:
        raise UsageError("profile registry 缺少必需的 core layer")
    return registry


def expand_layers(
    requested: list[str],
    registry: ProfileRegistry,
) -> list[Profile]:
    normalized = [item.strip() for item in requested if item.strip()]
    if "core" not in normalized:
        normalized.insert(0, "core")
    if not normalized:
        normalized = ["core"]

    ordered: list[Profile] = []
    state: dict[str, int] = {}

    def visit(profile_id: str) -> None:
        marker = state.get(profile_id, 0)
        if marker == 1:
            raise UsageError(f"profile 依赖出现循环：{profile_id}")
        if marker == 2:
            return
        state[profile_id] = 1
        profile = registry.get(profile_id)
        for dependency in profile.requires:
            visit(dependency)
        state[profile_id] = 2
        ordered.append(profile)

    for profile_id in normalized:
        visit(profile_id)

    ids = {profile.id for profile in ordered}
    for profile in ordered:
        for conflict in profile.conflicts:
            if conflict in ids:
                raise UsageError(
                    f"profile {profile.id} 与 {conflict} 冲突，不能同时装配"
                )
    if ordered[0].id != "core":
        core = registry.get("core")
        ordered = [core, *[item for item in ordered if item.id != "core"]]
    return ordered


def profile_fingerprint(
    layers: list[Profile],
    variables: dict[str, str],
) -> str:
    payload = {
        "workflow_version": WORKFLOW_VERSION,
        "layers": [profile.canonical() for profile in layers],
        "variables": dict(sorted(variables.items())),
    }
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def profile_label(layers: list[Profile]) -> str:
    return "+".join(f"{profile.id}@{profile.version}" for profile in layers)
