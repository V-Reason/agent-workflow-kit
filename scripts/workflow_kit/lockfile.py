"""Read and write the tracked workflow profile and lock files."""

from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import LOCK_SCHEMA_VERSION, PROFILE_SCHEMA_VERSION, WORKFLOW_VERSION
from .errors import UsageError

PROFILE_PATH = "AI_Context/WORKFLOW_PROFILE.toml"
LOCK_PATH = "AI_Context/WORKFLOW_LOCK.toml"


def _toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _toml_array(values: list[str]) -> str:
    return "[" + ", ".join(_toml_string(value) for value in values) + "]"


@dataclass(frozen=True)
class ProjectProfile:
    name: str
    layers: tuple[str, ...]
    variables: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ManagedFileRecord:
    path: str
    ownership: str
    sha256: str
    fragment_sha256: str | None
    block_id: str | None
    layers: tuple[str, ...]


@dataclass(frozen=True)
class WorkflowLock:
    kit_version: str
    workflow_version: str
    project_name: str
    profile_hash: str
    layers: tuple[str, ...]
    layer_versions: tuple[str, ...]
    files: tuple[ManagedFileRecord, ...]


def render_profile(profile: ProjectProfile) -> str:
    lines = [
        f"schema_version = {PROFILE_SCHEMA_VERSION}",
        f"workflow_version = {_toml_string(WORKFLOW_VERSION)}",
        f"name = {_toml_string(profile.name)}",
        f"layers = {_toml_array(list(profile.layers))}",
        "",
        "[parameters]",
    ]
    if profile.variables:
        lines.extend(
            f"{key} = {_toml_string(value)}"
            for key, value in sorted(profile.variables.items())
        )
    else:
        lines.append("# 无额外参数")
    return "\n".join(lines) + "\n"


def render_lock(lock: WorkflowLock) -> str:
    lines = [
        f"schema_version = {LOCK_SCHEMA_VERSION}",
        f"kit_version = {_toml_string(lock.kit_version)}",
        f"workflow_version = {_toml_string(lock.workflow_version)}",
        f"project_name = {_toml_string(lock.project_name)}",
        f"profile_hash = {_toml_string(lock.profile_hash)}",
        f"layers = {_toml_array(list(lock.layers))}",
        f"layer_versions = {_toml_array(list(lock.layer_versions))}",
        "",
    ]
    for record in sorted(lock.files, key=lambda item: (item.path, item.block_id or "")):
        lines.append("[[managed_files]]")
        lines.append(f"path = {_toml_string(record.path)}")
        lines.append(f"ownership = {_toml_string(record.ownership)}")
        lines.append(f"sha256 = {_toml_string(record.sha256)}")
        if record.fragment_sha256 is not None:
            lines.append(f"fragment_sha256 = {_toml_string(record.fragment_sha256)}")
        if record.block_id is not None:
            lines.append(f"block_id = {_toml_string(record.block_id)}")
        lines.append(f"layers = {_toml_array(list(record.layers))}")
        lines.append("")
    return "\n".join(lines)


def read_profile(project_root: Path) -> ProjectProfile:
    path = project_root / PROFILE_PATH
    if not path.is_file():
        raise UsageError(f"项目未装配 v4.0 workflow profile：{path}")
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise UsageError(f"WORKFLOW_PROFILE.toml 无效：{exc}") from exc
    if data.get("schema_version") != PROFILE_SCHEMA_VERSION:
        raise UsageError("WORKFLOW_PROFILE.toml schema_version 不兼容")
    if data.get("workflow_version") != WORKFLOW_VERSION:
        raise UsageError(
            f"项目 workflow_version 必须是 {WORKFLOW_VERSION}，"
            f"收到 {data.get('workflow_version')!r}"
        )
    name = data.get("name")
    layers = data.get("layers")
    parameters = data.get("parameters", {})
    if not isinstance(name, str) or not name.strip():
        raise UsageError("WORKFLOW_PROFILE.toml name 必须是非空字符串")
    if not isinstance(layers, list) or not all(isinstance(item, str) for item in layers):
        raise UsageError("WORKFLOW_PROFILE.toml layers 必须是字符串数组")
    if not isinstance(parameters, dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in parameters.items()
    ):
        raise UsageError("WORKFLOW_PROFILE.toml parameters 必须是字符串键值表")
    return ProjectProfile(name=name, layers=tuple(layers), variables=dict(parameters))


def read_lock(project_root: Path) -> WorkflowLock:
    path = project_root / LOCK_PATH
    if not path.is_file():
        raise UsageError(f"项目缺少 workflow lock：{path}")
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise UsageError(f"WORKFLOW_LOCK.toml 无效：{exc}") from exc
    if data.get("schema_version") != LOCK_SCHEMA_VERSION:
        raise UsageError("WORKFLOW_LOCK.toml schema_version 不兼容")
    profile_hash = data.get("profile_hash")
    if not isinstance(profile_hash, str) or re.fullmatch(
        r"sha256:[0-9a-f]{64}", profile_hash
    ) is None:
        raise UsageError("WORKFLOW_LOCK.toml profile_hash 非法")
    layers = data.get("layers", [])
    layer_versions = data.get("layer_versions", [])
    if (
        not isinstance(layers, list)
        or not isinstance(layer_versions, list)
        or len(layers) != len(layer_versions)
        or not all(isinstance(value, str) for value in layers + layer_versions)
    ):
        raise UsageError("WORKFLOW_LOCK.toml layers/layer_versions 不一致")
    files: list[ManagedFileRecord] = []
    for item in data.get("managed_files", []):
        if not isinstance(item, dict):
            raise UsageError("WORKFLOW_LOCK.toml managed_files 项必须是表")
        files.append(
            ManagedFileRecord(
                path=str(item["path"]),
                ownership=str(item["ownership"]),
                sha256=str(item["sha256"]),
                fragment_sha256=(
                    str(item["fragment_sha256"])
                    if item.get("fragment_sha256") is not None
                    else None
                ),
                block_id=(
                    str(item["block_id"]) if item.get("block_id") is not None else None
                ),
                layers=tuple(str(value) for value in item.get("layers", [])),
            )
        )
    return WorkflowLock(
        kit_version=str(data.get("kit_version", "")),
        workflow_version=str(data.get("workflow_version", "")),
        project_name=str(data.get("project_name", "")),
        profile_hash=profile_hash,
        layers=tuple(layers),
        layer_versions=tuple(layer_versions),
        files=tuple(files),
    )


def lock_by_key(lock: WorkflowLock | None) -> dict[tuple[str, str], ManagedFileRecord]:
    if lock is None:
        return {}
    return {
        (record.path, record.block_id or ""): record
        for record in lock.files
    }


def lock_to_dict(lock: WorkflowLock) -> dict[str, Any]:
    return {
        "kit_version": lock.kit_version,
        "workflow_version": lock.workflow_version,
        "project_name": lock.project_name,
        "profile_hash": lock.profile_hash,
        "layers": list(lock.layers),
        "layer_versions": list(lock.layer_versions),
        "files": [record.__dict__ for record in lock.files],
    }
