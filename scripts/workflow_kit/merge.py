"""Safe filesystem merge primitives."""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path, PurePosixPath
from typing import Any

from .errors import UsageError

_SENSITIVE_NAMES = {
    ".env",
    "id_rsa",
    "id_ed25519",
    "credentials",
    "secrets",
}


def sha256_bytes(data: bytes) -> str:
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def normalize_relpath(value: str) -> str:
    candidate = PurePosixPath(value.replace("\\", "/"))
    if candidate.is_absolute() or ".." in candidate.parts or not candidate.parts:
        raise UsageError(f"非法项目相对路径：{value}")
    return candidate.as_posix()


def target_path(root: Path, relative: str) -> Path:
    normalized = normalize_relpath(relative)
    result = (root / normalized).resolve()
    try:
        result.relative_to(root.resolve())
    except ValueError as exc:
        raise UsageError(f"目标路径逃逸项目根：{relative}") from exc
    _reject_symlink_ancestors(root.resolve(), result)
    return result


def _reject_symlink_ancestors(root: Path, target: Path) -> None:
    current = target
    while current != root:
        if current.exists() and current.is_symlink():
            raise UsageError(f"拒绝写入符号链接路径：{current}")
        current = current.parent


def is_sensitive_path(relative: str) -> bool:
    parts = [part.lower() for part in PurePosixPath(relative).parts]
    name = parts[-1] if parts else ""
    if name in {".env.example", ".env.sample"}:
        return False
    lowered_name = name.replace("secretary", "")
    return (
        name in _SENSITIVE_NAMES
        or name.startswith(".env.")
        or "secret" in lowered_name
        or "credential" in lowered_name
        or any(part in {".git", "__pycache__"} for part in parts)
    )


def marker_prefix(relative: str) -> tuple[str, str]:
    if relative.lower().endswith(".md"):
        return "<!--", "-->"
    return "#", ""


def marker_lines(relative: str, marker: str) -> tuple[str, str]:
    prefix, suffix = marker_prefix(relative)
    if prefix == "<!--":
        return (
            f"<!-- BEGIN AGENT_WORKFLOW_KIT:{marker} -->",
            f"<!-- END AGENT_WORKFLOW_KIT:{marker} -->",
        )
    return (
        f"# BEGIN AGENT_WORKFLOW_KIT:{marker}",
        f"# END AGENT_WORKFLOW_KIT:{marker}",
    )


def extract_managed_block(text: str, relative: str, marker: str) -> str | None:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    begin, end = marker_lines(relative, marker)
    begin_count = text.count(begin)
    end_count = text.count(end)
    if begin_count == 0 and end_count == 0:
        return None
    if begin_count != 1 or end_count != 1:
        raise UsageError(
            f"{relative}: 托管块 {marker} 标记损坏（begin={begin_count}, end={end_count}）"
        )
    start = text.index(begin) + len(begin)
    stop = text.index(end)
    if stop < start:
        raise UsageError(f"{relative}: 托管块 {marker} 顺序错误")
    return text[start:stop]


def apply_managed_block(
    existing: str | None,
    relative: str,
    marker: str,
    fragment: str,
) -> str:
    existing = (
        existing.replace("\r\n", "\n").replace("\r", "\n")
        if existing is not None
        else None
    )
    begin, end = marker_lines(relative, marker)
    normalized_fragment = fragment.replace("\r\n", "\n").replace("\r", "\n").strip(
        "\n"
    )
    block = f"{begin}\n{normalized_fragment}\n{end}"
    if existing is None or not existing.strip():
        return block + "\n"
    current_fragment = extract_managed_block(existing, relative, marker)
    if current_fragment is None:
        return existing.rstrip() + "\n\n" + block + "\n"
    start = existing.index(begin)
    stop = existing.index(end) + len(end)
    return existing[:start] + block + existing[stop:]


def render_placeholders(text: str, variables: dict[str, str]) -> str:
    pattern = re.compile(r"\{\{([a-z][a-z0-9_]*)\}\}")
    missing: set[str] = set()

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in variables:
            missing.add(key)
            return match.group(0)
        return variables[key]

    rendered = pattern.sub(replace, text)
    if missing:
        raise UsageError(f"未提供模板变量：{', '.join(sorted(missing))}")
    return rendered


def decode_text(data: bytes, relative: str) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise UsageError(f"{relative}: 模板文本必须为 UTF-8") from exc


def merge_json_missing(existing: bytes | None, incoming: bytes, relative: str) -> tuple[bytes, bool]:
    try:
        incoming_data = json.loads(incoming.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise UsageError(f"{relative}: incoming JSON 无效：{exc}") from exc
    if existing is None:
        return (
            (json.dumps(incoming_data, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
            False,
        )
    try:
        existing_data = json.loads(existing.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise UsageError(f"{relative}: 现有 JSON 无效：{exc}") from exc
    changed = False

    def merge(dst: Any, src: Any) -> Any:
        nonlocal changed
        if isinstance(dst, dict) and isinstance(src, dict):
            for key, value in src.items():
                if key not in dst:
                    dst[key] = value
                    changed = True
                else:
                    dst[key] = merge(dst[key], value)
            return dst
        return dst

    merged = merge(existing_data, incoming_data)
    if not changed:
        return existing, False
    return (json.dumps(merged, ensure_ascii=False, indent=2) + "\n").encode("utf-8"), True


def git_worktree_dirty(root: Path) -> bool:
    git_marker = root / ".git"
    if not git_marker.exists():
        return False
    environment = os.environ.copy()
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    import subprocess

    result = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain"],
        text=True,
        encoding="utf-8",
        capture_output=True,
        env=environment,
        check=False,
    )
    return result.returncode != 0 or bool(result.stdout.strip())
