"""Read-only workflow status and offline doctor checks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import KIT_VERSION, WORKFLOW_VERSION
from .errors import DoctorError, UsageError
from .lockfile import ManagedFileRecord, read_lock, read_profile
from .merge import extract_managed_block, sha256_bytes, target_path

_EXPECTED_SKILLS = {
    "game-systems-designer",
    "planner-orchestrator",
    "secretary-router",
    "software-architect",
    "task-brief-writer",
    "unity2d-architect",
    "watchdog-inspector",
    "worker-engine",
}


def _managed_record_state(project_root: Path, record: ManagedFileRecord) -> str:
    path = target_path(project_root, record.path)
    if not path.is_file():
        return "missing"
    data = path.read_bytes()
    if record.ownership == "MANAGED_BLOCK" and record.block_id:
        try:
            text = data.decode("utf-8")
            fragment = extract_managed_block(text, record.path, record.block_id)
        except (UnicodeDecodeError, UsageError):
            return "invalid"
        if fragment is None:
            return "invalid"
        current_fragment = sha256_bytes(fragment.encode("utf-8"))
        if current_fragment != record.fragment_sha256:
            return "modified"
    if sha256_bytes(data) == record.sha256:
        return "clean"
    if record.ownership == "MANAGED_BLOCK":
        return "user-edited-outside-managed-block"
    return "modified"


def project_status(project_root: Path) -> dict[str, Any]:
    project_root = project_root.resolve()
    profile = read_profile(project_root)
    lock = read_lock(project_root)
    counts = {
        "clean": 0,
        "modified": 0,
        "missing": 0,
        "invalid": 0,
        "user-edited-outside-managed-block": 0,
    }
    details: list[dict[str, str]] = []
    for record in lock.files:
        state = _managed_record_state(project_root, record)
        counts[state] += 1
        details.append(
            {
                "path": record.path,
                "ownership": record.ownership,
                "block_id": record.block_id or "",
                "state": state,
            }
        )
    status = "ok"
    if counts["modified"] or counts["missing"] or counts["invalid"]:
        status = "drifted"
    return {
        "status": status,
        "project": str(project_root),
        "project_name": profile.name,
        "workflow_version": lock.workflow_version,
        "kit_version": lock.kit_version,
        "profile_hash": lock.profile_hash,
        "layers": list(lock.layers),
        "layer_versions": list(lock.layer_versions),
        "counts": counts,
        "files": details,
    }


def doctor_project(project_root: Path) -> dict[str, Any]:
    project_root = project_root.resolve()
    errors: list[str] = []
    warnings: list[str] = []
    try:
        profile = read_profile(project_root)
        lock = read_lock(project_root)
    except UsageError as exc:
        raise DoctorError(str(exc)) from exc

    if lock.workflow_version != WORKFLOW_VERSION:
        errors.append(
            f"workflow lock 版本为 {lock.workflow_version}，期望 {WORKFLOW_VERSION}"
        )
    if lock.kit_version != KIT_VERSION:
        warnings.append(f"kit 版本为 {lock.kit_version}，当前为 {KIT_VERSION}")
    if tuple(profile.layers) != tuple(lock.layers):
        errors.append("WORKFLOW_PROFILE layers 与 WORKFLOW_LOCK layers 不一致")
    if profile.name != lock.project_name:
        errors.append("WORKFLOW_PROFILE name 与 WORKFLOW_LOCK project_name 不一致")

    for record in lock.files:
        state = _managed_record_state(project_root, record)
        if state == "user-edited-outside-managed-block":
            warnings.append(f"{record.path}: 托管块外存在用户编辑")
        elif state != "clean":
            errors.append(f"{record.path}: {state}")

    required = [
        "AGENTS.md",
        "AI_Context/PROJECT_BOARD.md",
        "AI_Context/TASKS/_templates/TASK_BRIEF.md",
        "scripts/workflow.py",
        "scripts/stage_context.py",
        "scripts/validate_handover.py",
    ]
    for relative in required:
        if not (project_root / relative).is_file():
            errors.append(f"缺少必需文件：{relative}")

    skill_root = project_root / ".agents" / "skills"
    skills = {path.name for path in skill_root.iterdir()} if skill_root.is_dir() else set()
    missing_skills = sorted(_EXPECTED_SKILLS - skills)
    extra_skills = sorted(skills - _EXPECTED_SKILLS)
    if missing_skills:
        errors.append(
            f".agents/skills 缺少 v4.0 技能：{missing_skills}"
        )
    if extra_skills:
        warnings.append(f".agents/skills 含团队扩展技能：{extra_skills}")

    if "unity2d" in lock.layers:
        for relative in (
            "Assets",
            "ProjectSettings/ProjectVersion.txt",
            "Packages/manifest.json",
        ):
            if not (project_root / relative).exists():
                errors.append(f"Unity 项目标记缺失：{relative}")

    if "python" in lock.layers:
        pyproject = project_root / "pyproject.toml"
        if pyproject.is_file():
            text = pyproject.read_text(encoding="utf-8", errors="replace")
            if "AI_Context" not in text:
                warnings.append(
                    "pyproject.toml 未显式排除 AI_Context；请人工确认 Ruff/mypy/pytest 隔离"
                )

    return {
        "status": "fail" if errors else ("warn" if warnings else "ok"),
        "project": str(project_root),
        "workflow_version": lock.workflow_version,
        "kit_version": lock.kit_version,
        "errors": errors,
        "warnings": warnings,
    }
