#!/usr/bin/env python3
"""validate_handover.py - v4.0 handover, evidence and Git-scope validator."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path, PurePath

for _stream in (sys.stdout, sys.stderr):
    _reconfigure = getattr(_stream, "reconfigure", None)
    if _reconfigure is not None:
        _reconfigure(encoding="utf-8")

TASK_DIR_PATTERN = re.compile(r"^GD-\d{4}-\d{4}$")
WORKFLOW_VERSION = "v4.0"
PLAN_FILE_PATTERN = re.compile(r"^PLAN_v(\d{2})\.md$")
EXEC_REPORT_PATTERN = re.compile(r"^EXECUTION_REPORT_A0([1-3])\.md$")
ROUND_DIR_PATTERN = re.compile(r"^ROUND_(\d{2})$")
MANIFEST_ENTRY_RE = re.compile(
    r"^\|\s*`?(?P<staged>[^|`]+?)`?\s*\|\s*(?P<layer>L[123])\s*\|"
    r"\s*`?(?P<source>[^|`]+?)`?\s*\|\s*(?P<tokens>\d+)\s*\|"
    r"\s*(?P<sha256>[0-9a-f]{64})\s*\|$"
)
COMMIT_HEX_RE = re.compile(r"^[0-9a-fA-F]{7,40}$")
COMMIT_TS_RE = re.compile(r"\d{4}-\d{2}-\d{2}([T ]\d{1,2}:\d{2}(:\d{2})?)?")
PLAN_VERSION_FIELD_RE = re.compile(r"Plan\s*Version[:：]?\s*v?(\d{2})", re.IGNORECASE)
TASK_LEVEL_FIELD_RE = re.compile(r"Task\s*Level[:：]?\s*L(\d)", re.IGNORECASE)
CONCLUSION_LINE_RE = re.compile(
    r"^(?:\*\*)?Conclusion(?:\*\*)?[:：][ \t]*(.+?)[ \t]*$", re.MULTILINE
)
ACCEPTANCE_DECISION_LINE_RE = re.compile(
    r"^(?:\*\*)?(?:用户决定|Decision)(?:\*\*)?[:：][ \t]*(.+?)[ \t]*$",
    re.MULTILINE,
)
APPROVAL_DECISION_LINE_RE = re.compile(
    r"^(?:\*\*)?Decision(?:\*\*)?[:：][ \t]*(.+?)[ \t]*$", re.MULTILINE
)

TASK_BRIEF_SECTIONS = [
    "Objective",
    "Background",
    "Current Behavior",
    "Expected Behavior",
    "Non-goals",
    "已知约束",
    "相关模块与文件",
    "已观察到的错误",
    "验收方式",
    "其他说明",
]
PLAN_SECTIONS = [
    "0. Metadata",
    "1. Objective",
    "2. Non-goals",
    "3. Current State",
    "4. Constraints",
    "5. Proposed Design",
    "6. File Scope",
    "7. Execution Steps",
    "8. Engineering Rules",
    "9. Acceptance Criteria",
    "10. Test Plan",
    "11. Risks",
    "12. Rollback",
    "13. Open Questions",
    "14. Approval",
]
EXEC_REPORT_SECTIONS = [
    "1. Preflight",
    "2. Actual Changes",
    "3. Step Results",
    "4. Commands",
    "5. AC Mapping",
    "6. Tests",
    "7. Usage",
    "8. Deviations",
    "9. Remaining Issues",
    "10. Rollback",
    "11. Conclusion",
]
RECON_SECTIONS = [
    "1. Scope",
    "2. Repo Map Check",
    "3. Key Files",
    "4. Interface Facts",
    "5. Risks",
    "6. Context Manifest",
    "7. Evidence",
]

PLAN_ALLOWED_STATUSES_PLANNER = {"DRAFT", "NEED_INVESTIGATION", "IN_REVIEW", "APPROVED"}
PLAN_ALLOWED_STATUSES_WORKER = {"APPROVED"}
CONCLUSION_ENUM = {"PASS", "PASS WITH WARNINGS", "FAIL", "BLOCKED", "NOT RUN"}
ACCEPTANCE_DECISIONS = {"ACCEPT", "ACCEPT WITH FOLLOW-UP", "REJECT"}
APPROVAL_DECISIONS = {"APPROVED", "APPROVED WITH CONDITIONS"}
AC_CLASSES = {
    "WORKER_AUTOMATABLE",
    "UNITY_GUI_REQUIRED",
    "CEO_MANUAL_ACCEPTANCE",
}
AC_EXECUTORS = {"WORKER", "CEO", "WORKER_COMPUTER_USE"}
EVIDENCE_TYPES = {
    "COMMAND",
    "EXIT_CODE",
    "TEST_RESULT",
    "DIFF",
    "MANIFEST",
    "HASH",
    "LOG",
    "RUNTIME_OUTPUT",
    "SCREENSHOT",
    "VIDEO",
    "OBSERVATION",
}
VISUAL_EVIDENCE = {"SCREENSHOT", "VIDEO", "OBSERVATION"}
AC_RESULTS = {"PASS", "FAIL", "NOT RUN", "BLOCKED", "NOT APPLICABLE"}
MODES = ("planner", "worker", "watchdog", "archive")
LEGACY_MODE_HINTS = {
    "exec" + "utor": "worker",
    "veri" + "fier": "watchdog",
}
L0_MINI_REQUIRED_MARKS = ["目标与验收", "文件边界"]

REQUIRED_FEED_FILES = {
    "L1__PROJECT_OVERVIEW.md",
    "L1__CODING_STANDARDS.md",
    "L1__BUILD_AND_TEST.md",
    "L2__ARCHITECTURE.md",
    "L2__MODULE_MAP.md",
}
APPROVAL_FIELD_KEYS = [
    "Workflow Version",
    "Approved Write Boundaries",
    "Explicitly Forbidden",
    "Computer-Use Authorization",
    "Base Commit",
    "Approver",
    "Approval Time",
]


@dataclass
class CheckResult:
    item: str
    status: str
    detail: str = ""

    @property
    def failed(self) -> bool:
        return self.status == "FAIL"


@dataclass
class Report:
    task_dir: str
    mode: str
    l0: bool = False
    checks: list[CheckResult] = field(default_factory=list)

    def add(self, item: str, status: str, detail: str = "") -> None:
        self.checks.append(CheckResult(item=item, status=status, detail=detail))

    @property
    def fails(self) -> list[CheckResult]:
        return [check for check in self.checks if check.failed]

    @property
    def warns(self) -> list[CheckResult]:
        return [check for check in self.checks if check.status == "WARN"]

    @property
    def ok(self) -> bool:
        return not self.fails

    def render(self) -> str:
        tag = " / L0 快速通道" if self.l0 else ""
        lines = [f"交接包校验：{self.task_dir}（模式 {self.mode}{tag}）", "-" * 64]
        for check in self.checks:
            mark = {"PASS": "[PASS]", "FAIL": "[FAIL]", "WARN": "[WARN]"}[check.status]
            line = f"{mark} {check.item}"
            if check.detail:
                line += f" - {check.detail}"
            lines.append(line)
        lines.extend(
            [
                "-" * 64,
                f"结果：PASS {len(self.checks) - len(self.fails) - len(self.warns)}"
                f" / FAIL {len(self.fails)} / WARN {len(self.warns)}",
                "结论：通过" if self.ok else "结论：未通过（先修复 FAIL 再交接）",
            ]
        )
        return "\n".join(lines)

    def to_json(self) -> str:
        return json.dumps(
            {
                "task_dir": self.task_dir,
                "mode": self.mode,
                "l0": self.l0,
                "ok": self.ok,
                "checks": [
                    {"item": check.item, "status": check.status, "detail": check.detail}
                    for check in self.checks
                ],
            },
            ensure_ascii=False,
            indent=2,
        )


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def _has_heading(text: str, heading: str) -> bool:
    tokens = [re.escape(token) for token in heading.split()]
    pattern = re.compile(
        r"^#{1,4}\s*" + r"\s+".join(tokens) + r"\s*$",
        re.MULTILINE | re.IGNORECASE,
    )
    return bool(pattern.search(text))


def _section_text(text: str, heading: str) -> str:
    tokens = [re.escape(token) for token in heading.split()]
    pattern = re.compile(
        r"^(#{1,4})\s*" + r"\s+".join(tokens) + r"\s*$",
        re.MULTILINE | re.IGNORECASE,
    )
    match = pattern.search(text)
    if match is None:
        return ""
    level = len(match.group(1))
    next_heading = re.compile(rf"^#{{1,{level}}}\s+", re.MULTILINE).search(
        text, match.end()
    )
    end = next_heading.start() if next_heading else len(text)
    return text[match.end() : end].strip()


def _subheading_bullets(text: str, heading: str) -> list[str]:
    pattern = re.compile(
        rf"^###\s*{re.escape(heading)}\s*$(.*?)(?=^###\s+|\Z)",
        re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    match = pattern.search(text)
    if match is None:
        return []
    return [
        re.sub(r"^\s*[-*]\s*", "", line).strip()
        for line in match.group(1).splitlines()
        if re.match(r"^\s*[-*]\s+", line)
    ]


def _normalize_table_cell(value: str) -> str:
    return _normalize_value(value)


def _markdown_table(text: str) -> tuple[list[str], list[list[str]]]:
    rows: list[list[str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [_normalize_table_cell(cell) for cell in stripped.strip("|").split("|")]
        if cells and all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells):
            continue
        rows.append(cells)
    if not rows:
        return [], []
    return rows[0], rows[1:]


def _parse_scope_item(value: str) -> str | None:
    normalized = value.strip().replace("`", "")
    match = re.fullmatch(
        r"(MODIFY|CREATE|DELETE)\s+(.+)",
        normalized,
        re.IGNORECASE,
    )
    if match is None:
        return None
    path = match.group(2).strip().replace("\\", "/")
    if (
        not path
        or path in {".", "/", "**", "**/*"}
        or path.startswith("/")
        or ".." in PurePath(path).parts
    ):
        return None
    return f"{match.group(1).upper()} {path}"


def _parse_forbidden_item(value: str) -> str | None:
    path = value.strip().replace("`", "").replace("\\", "/")
    if (
        not path
        or path in {".", "/", "**", "**/*"}
        or path.startswith("/")
        or ".." in PurePath(path).parts
    ):
        return None
    return path


def _scope_from_plan(text: str) -> tuple[list[str], list[str], str]:
    section = _section_text(text, "6. File Scope")
    write_items = [
        parsed
        for value in _subheading_bullets(section, "Write Boundaries")
        if (parsed := _parse_scope_item(value)) is not None
    ]
    forbidden = [
        parsed
        for value in _subheading_bullets(section, "Forbidden")
        if (parsed := _parse_forbidden_item(value)) is not None
    ]
    read_policy = ", ".join(_subheading_bullets(section, "Read Policy"))
    return sorted(write_items), sorted(forbidden), read_policy


def _parse_plan_ac_contract(text: str) -> tuple[list[dict[str, str]], list[str]]:
    section = _section_text(text, "9. Acceptance Criteria")
    headers, rows = _markdown_table(section)
    required = {"AC", "Class", "Executor", "Criterion", "Primary Evidence"}
    if not required.issubset(headers):
        return [], ["Acceptance Criteria 必须使用 AC/Class/Executor/Criterion/Primary Evidence 表"]
    positions = {header: index for index, header in enumerate(headers)}
    contracts: list[dict[str, str]] = []
    errors: list[str] = []
    seen: set[str] = set()
    for row in rows:
        if len(row) < len(headers):
            errors.append("Acceptance Criteria 存在列数不足的行")
            continue
        contract = {key: row[positions[key]] for key in required}
        ac_id = contract["AC"]
        if not re.fullmatch(r"AC-\d{2,}", ac_id):
            errors.append(f"非法 AC ID：{ac_id or '空'}")
            continue
        if ac_id in seen:
            errors.append(f"{ac_id} 重复")
        seen.add(ac_id)
        if contract["Class"] not in AC_CLASSES:
            errors.append(f"{ac_id} Class 非法：{contract['Class'] or '空'}")
        if contract["Executor"] not in AC_EXECUTORS:
            errors.append(f"{ac_id} Executor 非法：{contract['Executor'] or '空'}")
        if _is_placeholder_value(contract["Criterion"]):
            errors.append(f"{ac_id} Criterion 为空或占位")
        evidence = {
            token.strip().upper()
            for token in re.split(r"[+|]", contract["Primary Evidence"])
            if token.strip()
        }
        invalid_evidence = sorted(evidence - EVIDENCE_TYPES)
        if not evidence or invalid_evidence:
            errors.append(
                f"{ac_id} Primary Evidence 非法：{', '.join(invalid_evidence) or '空'}"
            )
        if contract["Class"] == "WORKER_AUTOMATABLE":
            if contract["Executor"] != "WORKER":
                errors.append(f"{ac_id} 自动项 Executor 必须为 WORKER")
            visual = sorted(evidence & VISUAL_EVIDENCE)
            if visual:
                errors.append(
                    f"{ac_id} 自动项不得以截图、视频或观察作为主证据：{', '.join(visual)}"
                )
        elif contract["Class"] == "CEO_MANUAL_ACCEPTANCE":
            if contract["Executor"] != "CEO":
                errors.append(f"{ac_id} CEO 人工验收项 Executor 必须为 CEO")
        elif contract["Class"] == "UNITY_GUI_REQUIRED":
            if contract["Executor"] not in {"CEO", "WORKER_COMPUTER_USE"}:
                errors.append(f"{ac_id} GUI 项 Executor 必须为 CEO 或 WORKER_COMPUTER_USE")
        contracts.append(contract)
    if not contracts and not errors:
        errors.append("Acceptance Criteria 不得为空")
    return contracts, errors


def _parse_plan_test_plan(text: str) -> tuple[dict[str, dict[str, str]], list[str]]:
    headers, rows = _markdown_table(_section_text(text, "10. Test Plan"))
    required = {"AC", "Command / Action", "CWD", "Expected"}
    if not required.issubset(headers):
        return {}, ["Test Plan 必须使用 AC/Command / Action/CWD/Expected 表"]
    positions = {header: index for index, header in enumerate(headers)}
    items: dict[str, dict[str, str]] = {}
    errors: list[str] = []
    for row in rows:
        if len(row) < len(headers):
            errors.append("Test Plan 存在列数不足的行")
            continue
        item = {key: row[positions[key]] for key in required}
        ac_id = item["AC"]
        if not re.fullmatch(r"AC-\d{2,}", ac_id):
            errors.append(f"Test Plan 非法 AC ID：{ac_id or '空'}")
            continue
        if ac_id in items:
            errors.append(f"Test Plan {ac_id} 重复")
        if any(_is_placeholder_value(item[key]) for key in required - {"AC"}):
            errors.append(f"Test Plan {ac_id} 含空值或占位")
        items[ac_id] = item
    return items, errors


def _computer_use_authorization_errors(value: str | None) -> list[str]:
    normalized = _normalize_value(value or "")
    if not normalized.upper().startswith("AUTHORIZED"):
        return ["缺少 AUTHORIZED"]
    missing: list[str] = []
    for label in ("TARGET", "ACTIONS", "SCOPE"):
        match = re.search(
            rf"\b{label}\s*=\s*([^;]+)",
            normalized,
            re.IGNORECASE,
        )
        if match is None or _is_placeholder_value(match.group(1)):
            missing.append(label)
    return missing


def _computer_use_is_authorized(value: str | None) -> bool:
    return not _computer_use_authorization_errors(value)


def _evidence_tokens(value: str) -> set[str]:
    return {
        token.strip().upper()
        for token in re.split(r"[+|]", value)
        if token.strip()
    }


def _parse_report_ac_mapping(text: str) -> tuple[dict[str, dict[str, str]], list[str]]:
    headers, rows = _markdown_table(_section_text(text, "5. AC Mapping"))
    required = {"AC", "Result", "Evidence Type", "Evidence"}
    if not required.issubset(headers):
        return {}, ["AC Mapping 必须使用 AC/Result/Evidence Type/Evidence 表"]
    positions = {header: index for index, header in enumerate(headers)}
    mapping: dict[str, dict[str, str]] = {}
    errors: list[str] = []
    for row in rows:
        if len(row) < len(headers):
            errors.append("AC Mapping 存在列数不足的行")
            continue
        item = {key: row[positions[key]] for key in required}
        ac_id = item["AC"]
        if not re.fullmatch(r"AC-\d{2,}", ac_id):
            errors.append(f"AC Mapping 非法 AC ID：{ac_id or '空'}")
            continue
        if ac_id in mapping:
            errors.append(f"AC Mapping {ac_id} 重复")
        mapping[ac_id] = item
    if not mapping and not errors:
        errors.append("AC Mapping 不得为空")
    return mapping, errors


def _check_computer_use_record(
    text: str,
    *,
    approved_authorization: str,
) -> list[str]:
    errors: list[str] = []
    used_value = _field_value(text, "Computer-Use Used")
    used = _normalize_value(used_value or "").upper()
    if used not in {"YES", "NO"}:
        errors.append("Computer-Use Used 必须为 YES 或 NO")
    authorization = _normalize_value(
        _field_value(text, "Computer-Use Authorization") or ""
    )
    if authorization != approved_authorization:
        errors.append(
            f"Computer-Use 报告授权 {authorization or '缺失'} 与批准值 "
            f"{approved_authorization or '缺失'} 不一致"
        )
    if used == "YES":
        if not _computer_use_is_authorized(approved_authorization):
            errors.append("Computer-Use 使用未获得专项授权")
        for field in ("Necessity", "Scope", "Result"):
            value = _field_value(text, field)
            if value is None or _is_placeholder_value(value):
                errors.append(f"Computer-Use {field} 不得为空或占位")
    return errors


def _check_visual_evidence_notes(text: str) -> list[str]:
    purpose = _field_value(text, "Visual Purpose")
    scenario = _field_value(text, "Visual Scenario")
    expected = _field_value(text, "Visual Expected")
    missing = [
        key
        for key, value in (
            ("Visual Purpose", purpose),
            ("Visual Scenario", scenario),
            ("Visual Expected", expected),
        )
        if value is None
        or _is_placeholder_value(value)
        or _normalize_value(value).upper() == "NOT APPLICABLE"
    ]
    return [f"视觉证据缺少 {', '.join(missing)}"] if missing else []


def _parse_acceptance_contract(
    text: str,
) -> tuple[dict[str, dict[str, str]], list[dict[str, str]], list[str]]:
    before_review = text.split("## Unplanned Change Review", 1)[0]
    headers, rows = _markdown_table(before_review)
    required = {"AC", "Class", "Executor", "Expected", "Result", "Primary Evidence"}
    if not required.issubset(headers):
        return {}, [], ["ACCEPTANCE 必须使用 AC/Class/Executor/Expected/Result/Primary Evidence 表"]
    positions = {header: index for index, header in enumerate(headers)}
    contracts: dict[str, dict[str, str]] = {}
    errors: list[str] = []
    for row in rows:
        if len(row) < len(headers):
            errors.append("ACCEPTANCE 存在列数不足的行")
            continue
        item = {key: row[positions[key]] for key in required}
        ac_id = item["AC"]
        if not re.fullmatch(r"AC-\d{2,}", ac_id):
            errors.append(f"ACCEPTANCE 非法 AC ID：{ac_id or '空'}")
            continue
        if ac_id in contracts:
            errors.append(f"ACCEPTANCE {ac_id} 重复")
        contracts[ac_id] = item

    review_headers, review_rows = _markdown_table(
        _section_text(text, "Unplanned Change Review")
    )
    review_required = {"Path", "Decision", "Reason"}
    if not review_required.issubset(review_headers):
        errors.append("Unplanned Change Review 必须使用 Path/Decision/Reason 表")
        review_rows = []
    review_positions = {
        header: index for index, header in enumerate(review_headers)
    }
    reviews: list[dict[str, str]] = []
    for row in review_rows:
        if len(row) < len(review_headers):
            errors.append("Unplanned Change Review 存在列数不足的行")
            continue
        item = {key: row[review_positions[key]] for key in review_required}
        if item["Decision"] not in {"JUSTIFIED", "UNJUSTIFIED", "NOT APPLICABLE"}:
            errors.append(f"未计划改动 Decision 非法：{item['Decision']}")
        if item["Decision"] == "UNJUSTIFIED":
            errors.append(f"未计划改动 UNJUSTIFIED：{item['Path']}")
        if _is_placeholder_value(item["Reason"]):
            errors.append(f"未计划改动 {item['Path']} 缺少理由")
        reviews.append(item)
    if not reviews and not errors:
        errors.append("Unplanned Change Review 不得为空")
    return contracts, reviews, errors


def _find_latest(directory: Path, pattern: re.Pattern[str]) -> tuple[Path | None, int]:
    found = [path for path in directory.iterdir() if path.is_file() and pattern.match(path.name)]
    if not found:
        return None, 0
    latest = max(found, key=lambda path: int(pattern.match(path.name).group(1)))  # type: ignore[union-attr]
    return latest, len(found)


def _find_all_plans(directory: Path) -> list[Path]:
    return sorted(
        (
            path
            for path in directory.iterdir()
            if path.is_file() and PLAN_FILE_PATTERN.match(path.name)
        ),
        key=lambda path: (
            int(PLAN_FILE_PATTERN.match(path.name).group(1)),  # type: ignore[union-attr]
            path.name,
        ),
    )


def _latest_detail(name: str, count: int) -> str:
    return f"已选最新（共 {count} 个版本）：{name}" if count > 1 else name


def _normalize_value(value: str) -> str:
    normalized = value.strip().strip("`").strip("*").strip()
    return re.sub(r"\s+", " ", normalized)


def _is_placeholder_value(value: str) -> bool:
    normalized = _normalize_value(value)
    if not normalized:
        return True
    if re.fullmatch(r"<[^>\n]+>", normalized):
        return True
    if normalized.casefold() in {"tbd", "todo", "待填写", "待填"}:
        return True
    return False


def _field_block_is_placeholder(block: str) -> bool:
    if _is_placeholder_value(block):
        return True
    for line in block.splitlines():
        value = re.sub(r"^\s*[-*]\s*", "", line).strip()
        if not value:
            continue
        if _is_placeholder_value(value):
            return True
        if re.fullmatch(
            r"(?:READ|CREATE|MODIFY|DELETE|RENAME)\s+<[^>]+>",
            value,
            re.IGNORECASE,
        ):
            return True
    return False


def _is_commit_legal(value: str) -> bool:
    normalized = _normalize_value(value)
    if COMMIT_HEX_RE.fullmatch(normalized):
        return True
    if "可恢复副本" in normalized:
        return True
    return bool(COMMIT_TS_RE.search(normalized))


def _field_value(text: str, key: str) -> str | None:
    match = re.search(
        rf"^[^\n]*?{re.escape(key)}[:：][ \t]*(.+?)[ \t]*$",
        text,
        re.MULTILINE,
    )
    return match.group(1) if match else None


def _project_root_for_task(directory: Path) -> Path | None:
    for candidate in (directory, *directory.parents):
        if (candidate / "AI_Context" / "WORKFLOW_LOCK.toml").is_file():
            return candidate
    return None


def _load_profile_identity(directory: Path) -> tuple[str, str] | None:
    root = _project_root_for_task(directory)
    if root is None:
        return None
    profile_path = root / "AI_Context" / "WORKFLOW_PROFILE.toml"
    lock_path = root / "AI_Context" / "WORKFLOW_LOCK.toml"
    try:
        profile = tomllib.loads(profile_path.read_text(encoding="utf-8"))
        lock = tomllib.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
        return None
    if (
        profile.get("workflow_version") != WORKFLOW_VERSION
        or lock.get("workflow_version") != WORKFLOW_VERSION
    ):
        return None
    profile_hash = lock.get("profile_hash")
    layer_versions = lock.get("layer_versions")
    if (
        not isinstance(profile_hash, str)
        or re.fullmatch(r"sha256:[0-9a-f]{64}", profile_hash) is None
        or not isinstance(layer_versions, list)
        or not layer_versions
        or not all(isinstance(item, str) and "@" in item for item in layer_versions)
    ):
        return None
    return " + ".join(layer_versions), profile_hash


def _check_profile_identity_text(
    directory: Path,
    text: str,
    report: Report,
    prefix: str,
) -> None:
    expected = _load_profile_identity(directory)
    if expected is None:
        report.add(f"{prefix}. Profile Identity", "FAIL", "缺少合法 v4.0 Profile Lock")
        return
    profile_value = (_field_value(text, "Project Profile") or "").strip()
    hash_value = (_field_value(text, "Profile Hash") or "").strip()
    expected_profile, expected_hash = expected
    failures: list[str] = []
    if profile_value != expected_profile:
        failures.append(
            f"Project Profile={profile_value or '缺失'}，期望 {expected_profile}"
        )
    if hash_value != expected_hash:
        failures.append(
            f"Profile Hash={hash_value or '缺失'}，期望 {expected_hash}"
        )
    if failures:
        report.add(f"{prefix}. Profile Identity", "FAIL", "；".join(failures))
    else:
        report.add(f"{prefix}. Profile Identity", "PASS", expected_profile)


def check_project_profile(directory: Path, report: Report) -> None:
    identity = _load_profile_identity(directory)
    if identity is None:
        report.add(
            "0. Project Profile",
            "FAIL",
            "项目缺少 Workflow v4.0 WORKFLOW_PROFILE.toml / WORKFLOW_LOCK.toml",
        )
    else:
        report.add("0. Project Profile", "PASS", identity[0])


def _approval_field_block(text: str, key: str) -> str | None:
    match = re.search(
        rf"^[^\n]*?{re.escape(key)}[:：][ \t]*([^\n]*)$",
        text,
        re.MULTILINE,
    )
    if match is None:
        return None
    lines = [match.group(1)]
    for line in text[match.end() :].splitlines():
        if not line.strip():
            continue
        if re.match(r"^[A-Za-z][A-Za-z0-9 /_-]+[:：]", line):
            break
        lines.append(line)
    block = "\n".join(lines).strip()
    return block or None


def _approval_task_id_value(text: str) -> str | None:
    match = re.search(
        r"^[^\n]*?Task ID(?:\s*/\s*Approved Plan)?[:：][ \t]*(.+?)[ \t]*$",
        text,
        re.MULTILINE,
    )
    return match.group(1) if match else None


def check_task_brief(directory: Path, report: Report, l0: bool = False) -> None:
    path = directory / "TASK_BRIEF.md"
    if not path.is_file():
        report.add("1. TASK_BRIEF.md", "FAIL", "缺少用户任务简报")
        return
    text = _read(path)
    _check_profile_identity_text(directory, text, report, "1b")
    if not l0:
        workflow = _normalize_value(_field_value(text, "Workflow Version") or "")
        if workflow == WORKFLOW_VERSION:
            report.add("1a. Brief Workflow Version", "PASS", workflow)
        else:
            report.add(
                "1a. Brief Workflow Version",
                "FAIL",
                f"TASK_BRIEF 必须声明 Workflow Version: {WORKFLOW_VERSION}",
            )
    missing = [section for section in TASK_BRIEF_SECTIONS if section not in text]
    if not missing:
        report.add("1. TASK_BRIEF.md", "PASS", "10 段结构齐全")
        return
    if l0 and _check_l0_mini_brief(text):
        report.add("1. TASK_BRIEF.md", "PASS", "L0 三行 mini 任务书要素齐全")
        return
    if l0:
        report.add(
            "1. TASK_BRIEF.md",
            "FAIL",
            "须为标准 10 段，或含 v4.0 L0、目标与验收、文件边界、Base Commit 与 Computer-Use 的 mini 简报",
        )
        return
    report.add("1. TASK_BRIEF.md", "FAIL", f"缺少 {len(missing)} 段：{'、'.join(missing)}")


def _check_l0_mini_brief(text: str) -> bool:
    if not re.search(r"\bL0\b", text):
        return False
    if WORKFLOW_VERSION not in text:
        return False
    if any(mark not in text for mark in L0_MINI_REQUIRED_MARKS):
        return False
    if "Base Commit" not in text or "Computer-Use Authorization" not in text:
        return False
    if _parse_l0_contract(text) is None:
        return False
    scopes, forbidden, _ = _parse_l0_scope(text)
    if not scopes or not forbidden:
        return False
    for line in text.splitlines():
        if any(mark in line for mark in L0_MINI_REQUIRED_MARKS):
            value = re.split(r"[:：]", line, maxsplit=1)[-1].strip()
            if _is_placeholder_value(value):
                return False
    return True


def _parse_l0_contract(text: str) -> dict[str, str] | None:
    line = _field_value(text, "目标与验收") or ""
    match = re.search(
        r"(WORKER_AUTOMATABLE|UNITY_GUI_REQUIRED|CEO_MANUAL_ACCEPTANCE)"
        r"\s*/\s*(WORKER|CEO|WORKER_COMPUTER_USE)"
        r"\s*/\s*([A-Z_+| ]+?)\s*/",
        line,
    )
    if match is None:
        return None
    evidence = match.group(3).strip()
    if not _evidence_tokens(evidence) or _evidence_tokens(evidence) - EVIDENCE_TYPES:
        return None
    return {
        "AC": "AC-01",
        "Class": match.group(1),
        "Executor": match.group(2),
        "Criterion": line,
        "Primary Evidence": evidence,
    }


def _safe_manifest_mapping(staged: str, source: str) -> str | None:
    path = PurePath(staged)
    if path.is_absolute() or path.name != staged or ".." in path.parts:
        return f"暂存名越界：{staged}"
    if source == "git:recent":
        return None
    source_path = PurePath(source)
    if source_path.is_absolute() or ".." in source_path.parts:
        return f"原路径越界：{source}"
    return None


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _manifest_entries(text: str) -> list[tuple[str, str, str, int, str]]:
    entries: list[tuple[str, str, str, int, str]] = []
    for line in text.splitlines():
        match = MANIFEST_ENTRY_RE.match(line)
        if match:
            entries.append(
                (
                    match.group("staged").strip(),
                    match.group("layer").strip(),
                    match.group("source").strip(),
                    int(match.group("tokens")),
                    match.group("sha256").strip(),
                )
            )
    return entries


def _round_sections(text: str) -> dict[int, str]:
    marker = "## NEED_FILES Round Index"
    if marker not in text:
        return {}
    index_text = text.split(marker, 1)[1]
    matches = list(re.finditer(r"^### ROUND_(\d{2})\s*$", index_text, re.MULTILINE))
    sections: dict[int, str] = {}
    for position, match in enumerate(matches):
        start = match.end()
        end = (
            matches[position + 1].start()
            if position + 1 < len(matches)
            else len(index_text)
        )
        sections[int(match.group(1))] = index_text[start:end]
    return sections


def _check_needs_files_rounds(directory: Path, text: str, report: Report) -> None:
    sections = _round_sections(text)
    count_value = _field_value(text, "Need Files Rounds")
    try:
        declared_count = int(_normalize_value(count_value or ""))
    except ValueError:
        report.add("2f. NEED_FILES Rounds", "FAIL", "缺少或非法 Need Files Rounds 字段")
        return

    root = directory / "NEED_FILES"
    round_dirs: dict[int, Path] = {}
    if root.exists():
        if root.is_symlink() or not root.is_dir():
            report.add("2f. NEED_FILES Rounds", "FAIL", "NEED_FILES 必须是普通目录")
            return
        for child in root.iterdir():
            match = ROUND_DIR_PATTERN.fullmatch(child.name)
            if match is None or not child.is_dir() or child.is_symlink():
                report.add(
                    "2f. NEED_FILES Rounds",
                    "FAIL",
                    f"非法轮目录：{child.name}",
                )
                return
            round_dirs[int(match.group(1))] = child

    numbers = sorted(round_dirs)
    if numbers != list(range(1, len(numbers) + 1)):
        report.add(
            "2f. NEED_FILES Rounds",
            "FAIL",
            f"ROUND_NN 必须连续编号，当前为 {numbers}",
        )
        return
    if numbers != sorted(sections):
        report.add(
            "2f. NEED_FILES Rounds",
            "FAIL",
            f"Manifest 轮次 {sorted(sections)} 与目录 {numbers} 不一致",
        )
        return
    if declared_count != len(numbers):
        report.add(
            "2f. NEED_FILES Rounds",
            "FAIL",
            f"Need Files Rounds={declared_count}，实际 {len(numbers)}",
        )
        return
    if declared_count == 0:
        report.add("2f. NEED_FILES Rounds", "PASS", "无增量补料轮")
        return

    errors: list[str] = []
    for number in numbers:
        round_dir = round_dirs[number]
        section = sections[number]
        non_flat = sorted(
            child.name
            for child in round_dir.iterdir()
            if not child.is_file() or child.is_symlink()
        )
        if non_flat:
            errors.append(
                f"ROUND_{number:02d} 补料文件必须平铺：{', '.join(non_flat)}"
            )
        for field in ("Reason", "Source Commit", "Round Manifest"):
            value = _field_value(section, field)
            if value is None or _is_placeholder_value(value):
                errors.append(f"ROUND_{number:02d} 缺 {field}")
        manifest_path = round_dir / "ROUND_MANIFEST.md"
        if not manifest_path.is_file():
            errors.append(f"ROUND_{number:02d} 缺 ROUND_MANIFEST.md")
        entries = _manifest_entries(section)
        if not entries:
            errors.append(f"ROUND_{number:02d} 无文件映射")
            continue
        mapped_names: set[str] = set()
        for staged, _, source, _, expected_hash in entries:
            mapped_names.add(staged)
            mapping_error = _safe_manifest_mapping(staged, source)
            if mapping_error:
                errors.append(f"ROUND_{number:02d} {mapping_error}")
                continue
            path = round_dir / staged
            if not path.is_file():
                errors.append(f"ROUND_{number:02d} 缺实体 {staged}")
                continue
            actual_hash = _sha256_file(path)
            if actual_hash != expected_hash:
                errors.append(
                    f"ROUND_{number:02d} {staged} SHA-256 不匹配"
                )
        extras = sorted(
            path.name
            for path in round_dir.iterdir()
            if path.is_file()
            and path.name != "ROUND_MANIFEST.md"
            and path.name not in mapped_names
        )
        if extras:
            errors.append(f"ROUND_{number:02d} 未映射文件：{', '.join(extras)}")
    if errors:
        report.add("2f. NEED_FILES Rounds", "FAIL", "；".join(errors))
    else:
        report.add(
            "2f. NEED_FILES Rounds",
            "PASS",
            f"{declared_count} 轮目录、映射与 SHA-256 一致",
        )


def _find_project_root(task_dir: Path) -> Path | None:
    resolved = task_dir.resolve()
    for candidate in (resolved, *resolved.parents):
        if (candidate / "AI_Context").is_dir():
            return candidate
    return None


def _run_git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    return subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        capture_output=True,
        check=False,
        env=environment,
    )


def _glob_pattern_regex(pattern: str) -> re.Pattern[str]:
    position = 0
    output = "^"
    while position < len(pattern):
        char = pattern[position]
        if char == "*":
            if position + 1 < len(pattern) and pattern[position + 1] == "*":
                position += 2
                if position < len(pattern) and pattern[position] == "/":
                    output += "(?:.*/)?"
                    position += 1
                else:
                    output += ".*"
                continue
            output += "[^/]*"
        elif char == "?":
            output += "[^/]"
        else:
            output += re.escape(char)
        position += 1
    return re.compile(output + "$")


def _path_matches(
    path: str,
    patterns: list[str],
    *,
    basename_patterns: bool = False,
) -> bool:
    name = PurePath(path).name
    return any(
        _glob_pattern_regex(pattern).fullmatch(
            name if basename_patterns and "/" not in pattern else path
        )
        for pattern in patterns
    )


def _scope_patterns(scope_items: list[str], action: str) -> list[str]:
    prefix = f"{action} "
    return [item[len(prefix) :] for item in scope_items if item.startswith(prefix)]


def _parse_l0_scope(text: str) -> tuple[list[str], list[str], str]:
    boundary = _field_value(text, "文件边界") or ""
    scopes = [
        f"{match.group(1).upper()} {match.group(2)}"
        for match in re.finditer(
            r"(MODIFY|CREATE|DELETE)\s+`([^`]+)`",
            boundary,
            re.IGNORECASE,
        )
    ]
    forbidden = [
        match.group(1)
        for match in re.finditer(r"FORBIDDEN\s+`([^`]+)`", boundary, re.IGNORECASE)
    ]
    return scopes, forbidden, boundary


def _approval_base_commit(text: str) -> str:
    block = _approval_field_block(text, "Base Commit") or ""
    values = re.split(r"\s+/\s+", block.strip())
    return _normalize_value(values[-1])


def _plan_base_commit(text: str) -> str:
    value = _field_value(text, "Base Commit") or ""
    values = re.split(r"\s+/\s+", value.strip())
    return _normalize_value(values[-1])


def _git_base_commit(
    directory: Path,
    *,
    l0: bool,
) -> str | None:
    if l0:
        text = _read(directory / "TASK_BRIEF.md") if (directory / "TASK_BRIEF.md").is_file() else ""
        commit = _normalize_value(_field_value(text, "Base Commit") or "")
    else:
        approval = directory / "APPROVAL_RECORD.md"
        text = _read(approval) if approval.is_file() else ""
        commit = _approval_base_commit(text)
    return commit if COMMIT_HEX_RE.fullmatch(commit) else None


def _git_changes(root: Path, base: str) -> list[tuple[str, str]]:
    result = _run_git(root, "diff", "--name-status", "-z", base, "--")
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git diff 失败")
    tokens = [token for token in result.stdout.split("\0") if token]
    changes: list[tuple[str, str]] = []
    index = 0
    while index < len(tokens):
        status = tokens[index].strip()
        index += 1
        if status.startswith("R") or status.startswith("C"):
            if index + 1 >= len(tokens):
                break
            old_path = tokens[index].replace("\\", "/")
            new_path = tokens[index + 1].replace("\\", "/")
            index += 2
            if status.startswith("R"):
                changes.extend([("D", old_path), ("A", new_path)])
            else:
                changes.append(("A", new_path))
            continue
        if index >= len(tokens):
            break
        path = tokens[index].replace("\\", "/")
        index += 1
        changes.append((status[:1], path))

    untracked = _run_git(root, "ls-files", "--others", "--exclude-standard", "-z")
    if untracked.returncode == 0:
        changes.extend(
            ("A", path.replace("\\", "/"))
            for path in untracked.stdout.split("\0")
            if path
        )
    return sorted(set(changes), key=lambda item: (item[1], item[0]))


def _workflow_artifact(path: str, _task_id: str) -> bool:
    return (
        path.startswith("AI_Context/TASKS/")
        or path.startswith("AI_Context/EVIDENCE/")
        or path in {"AI_Context/PROJECT_BOARD.md", "AI_Context/METRICS.md"}
    )


def _planned_writes(report_text: str) -> set[str]:
    start = re.search(
        r"^Planned Writes[:：]\s*$",
        report_text,
        re.MULTILINE | re.IGNORECASE,
    )
    if start is None:
        return set()
    end = re.search(
        r"^(?:Discovered Inputs|##\s+|[-*]\s+[A-Z][^\n]*:)\s*",
        report_text[start.end() :],
        re.MULTILINE,
    )
    block = (
        report_text[start.end() : start.end() + end.start()]
        if end is not None
        else report_text[start.end() :]
    )
    planned: set[str] = set()
    for line in block.splitlines():
        value = re.sub(r"^\s*[-*]\s*", "", line)
        match = re.search(r"`?([^`\s]+)`?\s*$", value)
        if match and "/" in match.group(1):
            planned.add(match.group(1).replace("\\", "/"))
    return planned


def _acceptance_review_map(text: str) -> dict[str, str]:
    _, reviews, _ = _parse_acceptance_contract(text)
    return {
        item["Path"].replace("`", ""): item["Decision"]
        for item in reviews
        if item["Path"] not in {"none", "NONE"}
    }


def check_diff_scope(
    directory: Path,
    report: Report,
    *,
    mode: str,
    l0: bool,
) -> None:
    root = _find_project_root(directory)
    base = _git_base_commit(directory, l0=l0)
    if root is None or not (root / ".git").exists():
        report.add(
            "8. Git Diff Scope",
            "WARN",
            "Diff 未自动核验：非 Git 工作区，需 Watchdog 与 CEO 补充证据",
        )
        return
    if base is None:
        report.add(
            "8. Git Diff Scope",
            "WARN",
            "Diff 未自动核验：批准 Base Commit 不是可解析的 Git 哈希",
        )
        return
    exists = _run_git(root, "cat-file", "-e", f"{base}^{{commit}}")
    if exists.returncode != 0:
        report.add(
            "8. Git Diff Scope",
            "WARN",
            f"Diff 未自动核验：Base Commit {base} 不存在于当前仓库",
        )
        return

    try:
        changes = _git_changes(root, base)
    except RuntimeError as exc:
        report.add("8. Git Diff Scope", "WARN", f"Diff 未自动核验：{exc}")
        return

    manifest_path = directory / "00_CONTEXT_MANIFEST.md"
    manifest_text = _read(manifest_path) if manifest_path.is_file() else ""
    manifest_commit = _normalize_value(_field_value(manifest_text, "Base Commit") or "")
    if (
        COMMIT_HEX_RE.fullmatch(manifest_commit)
        and manifest_commit.lower() != base.lower()
    ):
        report.add(
            "8a. Base Commit Consistency",
            "FAIL",
            f"Manifest={manifest_commit}，Approval={base}",
        )
    else:
        report.add("8a. Base Commit Consistency", "PASS", base)

    if l0:
        brief = _read(directory / "TASK_BRIEF.md") if (directory / "TASK_BRIEF.md").is_file() else ""
        scopes, forbidden, _ = _parse_l0_scope(brief)
    else:
        plan_path, _ = _find_latest(directory, PLAN_FILE_PATTERN)
        plan_text = _read(plan_path) if plan_path is not None else ""
        scopes, forbidden, _ = _scope_from_plan(plan_text)

    business_changes = [
        (status, path)
        for status, path in changes
        if not _workflow_artifact(path, directory.name)
    ]
    failures: list[str] = []
    unplanned: list[str] = []
    execution_path, _ = _find_latest(directory, EXEC_REPORT_PATTERN)
    report_text = _read(execution_path) if execution_path is not None else ""
    planned = _planned_writes(report_text)
    for status, path in business_changes:
        if _path_matches(path, forbidden, basename_patterns=True):
            failures.append(f"FORBIDDEN {path}")
            continue
        action = {"M": "MODIFY", "A": "CREATE", "D": "DELETE"}.get(status, "MODIFY")
        patterns = _scope_patterns(scopes, action)
        if not _path_matches(path, patterns):
            failures.append(f"OUTSIDE {action} {path}")
            continue
        if path not in planned:
            unplanned.append(path)

    if failures:
        report.add("8. Git Diff Scope", "FAIL", "；".join(sorted(set(failures))))
        return
    if unplanned:
        unique = sorted(set(unplanned))
        if mode == "archive":
            acceptance_path = directory / "ACCEPTANCE.md"
            acceptance_text = (
                _read(acceptance_path) if acceptance_path.is_file() else ""
            )
            review_map = _acceptance_review_map(acceptance_text)
            missing = [path for path in unique if review_map.get(path) != "JUSTIFIED"]
            if missing:
                report.add(
                    "8. Git Diff Scope",
                    "FAIL",
                    f"未计划改动缺少 JUSTIFIED 审阅：{', '.join(missing)}",
                )
                return
            report.add(
                "8. Git Diff Scope",
                "PASS",
                f"{len(business_changes)} 个业务改动均在边界内，未计划项已审阅",
            )
        else:
            report.add(
                "8. Git Diff Scope",
                "WARN",
                f"边界内未计划改动，Watchdog 需逐项审阅：{', '.join(unique)}",
            )
        return
    report.add(
        "8. Git Diff Scope",
        "PASS",
        f"{len(business_changes)} 个业务改动均符合批准边界与 Preflight 清单",
    )


def check_context_manifest(directory: Path, report: Report, task_id: str) -> None:
    manifest = directory / "00_CONTEXT_MANIFEST.md"
    if not manifest.is_file():
        report.add(
            "2. CONTEXT MANIFEST + FEED_DROP",
            "FAIL",
            "缺少 00_CONTEXT_MANIFEST.md",
        )
        return
    text = _read(manifest)
    _check_profile_identity_text(directory, text, report, "2g")

    version = _field_value(text, "Workflow Version")
    if version is None or _normalize_value(version) != WORKFLOW_VERSION:
        report.add(
            "2. Workflow Version",
            "FAIL",
            f"必须为 {WORKFLOW_VERSION}，当前为 {version or '缺失'}",
        )
    else:
        report.add("2. Workflow Version", "PASS", WORKFLOW_VERSION)

    manifest_task_id = _field_value(text, "Task ID")
    if manifest_task_id is None or TASK_DIR_PATTERN.fullmatch(task_id) is None:
        report.add("2b. Manifest Task ID", "FAIL", f"无法核对 Task ID：{task_id}")
    elif manifest_task_id.strip() == task_id:
        report.add("2b. Manifest Task ID", "PASS", task_id)
    else:
        report.add(
            "2b. Manifest Task ID",
            "FAIL",
            f"Manifest 为 {manifest_task_id.strip()}，目录为 {task_id}",
        )

    commit = _field_value(text, "Base Commit")
    if commit is None:
        report.add("2a. Manifest 基线", "FAIL", "缺少 Base Commit 字段")
    elif _is_placeholder_value(commit):
        report.add("2a. Manifest 基线", "FAIL", f"Base Commit 仍为占位符：{commit}")
    elif _is_commit_legal(commit):
        report.add("2a. Manifest 基线", "PASS", _normalize_value(commit))
    else:
        report.add("2a. Manifest 基线", "FAIL", f"Base Commit 非法：{commit}")

    feed = directory / "FEED_DROP"
    feed_files = (
        {path.name for path in feed.iterdir() if path.is_file()} if feed.is_dir() else set()
    )
    if not feed_files:
        report.add("2. CONTEXT MANIFEST + FEED_DROP", "FAIL", "FEED_DROP 不存在或为空")
    else:
        report.add(
            "2. CONTEXT MANIFEST + FEED_DROP",
            "PASS",
            f"Manifest 存在，FEED_DROP 含 {len(feed_files)} 个文件",
        )

    baseline_text = text.split("## NEED_FILES Round Index", 1)[0]
    mappings = _manifest_entries(baseline_text)
    if not mappings:
        report.add("2c. 文件映射表", "FAIL", "Manifest 未包含可解析的文件映射表")
        _check_needs_files_rounds(directory, text, report)
        return

    mapping_errors = [
        error
        for staged, _, source, _, _ in mappings
        if (error := _safe_manifest_mapping(staged, source)) is not None
    ]
    if mapping_errors:
        report.add("2c. 文件映射表", "FAIL", "；".join(mapping_errors))
    else:
        report.add("2c. 文件映射表", "PASS", f"{len(mappings)} 条映射路径合法")

    hash_errors: list[str] = []
    for staged, _, source, _, expected_hash in mappings:
        if _safe_manifest_mapping(staged, source) is not None:
            continue
        path = feed / staged
        if source != "git:recent" and path.is_file():
            actual_hash = _sha256_file(path)
            if actual_hash != expected_hash:
                hash_errors.append(f"{staged} SHA-256 不匹配")

    mapped_names = {staged for staged, _, _, _, _ in mappings}
    missing_required = sorted(REQUIRED_FEED_FILES - mapped_names)
    missing_files = sorted(mapped_names - feed_files)
    missing_required_files = sorted(REQUIRED_FEED_FILES - feed_files)
    if missing_required or missing_files or missing_required_files or hash_errors:
        details: list[str] = []
        if missing_required:
            details.append(f"映射表缺必需项：{', '.join(missing_required)}")
        if missing_files:
            details.append(f"映射文件实体缺失：{', '.join(missing_files)}")
        if missing_required_files:
            details.append(f"FEED_DROP 缺必需文件：{', '.join(missing_required_files)}")
        if hash_errors:
            details.append("；".join(hash_errors))
        report.add("2d. 映射实体", "FAIL", "；".join(details))
    else:
        report.add("2d. 映射实体", "PASS", "所有映射与必需文件均存在")

    extras = sorted(feed_files - mapped_names)
    if extras:
        report.add("2e. 额外文件", "WARN", f"未列入清单：{', '.join(extras)}")
    else:
        report.add("2e. 额外文件", "PASS", "无未映射文件")

    _check_needs_files_rounds(directory, text, report)


def check_plan(directory: Path, report: Report, mode: str, plan_ver: str | None) -> None:
    path, count = _find_latest(directory, PLAN_FILE_PATTERN)
    if path is None:
        report.add("4. PLAN_vNN.md", "FAIL", "缺少任务书草案（0.Metadata + 14 章）")
        return
    text = _read(path)
    _check_profile_identity_text(directory, text, report, "4k")
    missing = [section for section in PLAN_SECTIONS if not _has_heading(text, section)]
    if missing:
        report.add("4. PLAN_vNN.md", "FAIL", f"缺少章节：{'; '.join(missing)}")
    else:
        report.add(
            "4. PLAN_vNN.md",
            "PASS",
            _latest_detail(f"{path.name}，0.Metadata + 14 章齐全", count),
        )

    status_value = _field_value(text, "Status")
    status = _normalize_value(status_value or "").upper()
    allowed = (
        PLAN_ALLOWED_STATUSES_WORKER
        if mode in {"worker", "watchdog", "archive"}
        else PLAN_ALLOWED_STATUSES_PLANNER
    )
    if status in allowed:
        report.add("4a. PLAN 状态", "PASS", f"Status: {status}")
    else:
        report.add(
            "4a. PLAN 状态",
            "FAIL",
            f"Status: {status or '缺失'}，允许 {'/'.join(sorted(allowed))}",
        )

    task_id = directory.name
    if TASK_DIR_PATTERN.fullmatch(task_id) is None:
        report.add("4b. Task ID 一致", "WARN", f"目录名 {task_id} 不符合 GD-YYYY-NNNN")
    elif re.search(rf"\b{re.escape(task_id)}\b", text):
        report.add("4b. Task ID 一致", "PASS", task_id)
    else:
        report.add("4b. Task ID 一致", "FAIL", f"任务书未引用 {task_id}")

    field_version = PLAN_VERSION_FIELD_RE.search(text)
    if plan_ver is None:
        report.add("4c. 版本一致", "WARN", "无法从文件名解析版本号")
    elif field_version is None:
        report.add("4c. 版本一致", "FAIL", "正文缺少 Plan Version 字段")
    elif field_version.group(1) != plan_ver:
        report.add(
            "4c. 版本一致",
            "FAIL",
            f"文件名 v{plan_ver} 与正文 v{field_version.group(1)} 不一致",
        )
    else:
        report.add("4c. 版本一致", "PASS", f"文件名与正文均为 v{plan_ver}")

    workflow_version = _field_value(text, "Workflow Version")
    if (
        workflow_version is None
        or _normalize_value(workflow_version) != WORKFLOW_VERSION
    ):
        report.add(
            "4d. Workflow Version",
            "FAIL",
            f"PLAN 必须声明 Workflow Version: {WORKFLOW_VERSION}",
        )
    else:
        report.add("4d. Workflow Version", "PASS", WORKFLOW_VERSION)

    plan_base = _plan_base_commit(text)
    if not plan_base or _is_placeholder_value(plan_base) or not _is_commit_legal(plan_base):
        report.add(
            "4i. PLAN Base Commit",
            "FAIL",
            "PLAN 必须声明有效的 Branch / Base Commit 或可恢复副本时间",
        )
    else:
        report.add("4i. PLAN Base Commit", "PASS", plan_base)

    manifest_path = directory / "00_CONTEXT_MANIFEST.md"
    manifest_base = _normalize_value(
        (_field_value(_read(manifest_path), "Base Commit") if manifest_path.is_file() else "")
        or ""
    )
    if not manifest_base or plan_base.casefold() != manifest_base.casefold():
        report.add(
            "4j. Manifest / PLAN Base Commit",
            "FAIL",
            f"Manifest={manifest_base or '缺失'}，PLAN={plan_base or '缺失'}",
        )
    else:
        report.add("4j. Manifest / PLAN Base Commit", "PASS", plan_base)

    write_items, forbidden, read_policy = _scope_from_plan(text)
    scope_errors: list[str] = []
    if not write_items:
        scope_errors.append("Write Boundaries 为空或含非法路径模式")
    if not forbidden:
        scope_errors.append("Forbidden 为空或含非法路径模式")
    if "REPO_READ_ONLY_EXCEPT_SENSITIVE" not in read_policy.upper():
        scope_errors.append("Read Policy 必须包含 REPO_READ_ONLY_EXCEPT_SENSITIVE")
    protected = _subheading_bullets(_section_text(text, "6. File Scope"), "Protected Changes")
    if not protected:
        scope_errors.append("Protected Changes 不得为空")
    if scope_errors:
        report.add("4e. Write Boundary Contract", "FAIL", "；".join(scope_errors))
    else:
        report.add(
            "4e. Write Boundary Contract",
            "PASS",
            f"{len(write_items)} 条写入边界，{len(forbidden)} 条禁止项",
        )

    contracts, contract_errors = _parse_plan_ac_contract(text)
    if contract_errors:
        report.add("4f. AC Contract", "FAIL", "；".join(contract_errors))
    else:
        report.add("4f. AC Contract", "PASS", f"{len(contracts)} 条 AC 分类合法")

    test_plan, test_plan_errors = _parse_plan_test_plan(text)
    contract_ids = {item["AC"] for item in contracts}
    if set(test_plan) != contract_ids:
        test_plan_errors.append(
            f"AC 集合不一致：Acceptance Criteria {sorted(contract_ids)}，"
            f"Test Plan {sorted(test_plan)}"
        )
    if test_plan_errors:
        report.add("4h. Test Plan Contract", "FAIL", "；".join(test_plan_errors))
    else:
        report.add("4h. Test Plan Contract", "PASS", f"{len(test_plan)} 条 AC 测试映射齐全")

    computer_auth = _field_value(text, "Computer-Use Authorization")
    worker_computer_use = any(
        item["Executor"] == "WORKER_COMPUTER_USE" for item in contracts
    )
    if worker_computer_use and not _computer_use_is_authorized(computer_auth):
        missing = _computer_use_authorization_errors(computer_auth)
        report.add(
            "4g. Computer-Use Authorization",
            "FAIL",
            "WORKER_COMPUTER_USE 授权不完整，缺少："
            + "、".join(missing),
        )
    elif computer_auth is None or _is_placeholder_value(computer_auth):
        report.add(
            "4g. Computer-Use Authorization",
            "FAIL",
            "缺少 Computer-Use Authorization；未使用时必须明确写 NONE",
        )
    else:
        report.add(
            "4g. Computer-Use Authorization",
            "PASS",
            _normalize_value(computer_auth),
        )


def check_plan_l0(directory: Path, report: Report) -> None:
    plans = _find_all_plans(directory)
    if not plans:
        return
    invalid: list[str] = []
    missing_level: list[str] = []
    for path in plans:
        text = _read(path)
        level_match = TASK_LEVEL_FIELD_RE.search(text)
        if level_match is None:
            missing_level.append(path.name)
        elif int(level_match.group(1)) != 0:
            invalid.append(f"{path.name}=L{level_match.group(1)}")
    if missing_level or invalid:
        details: list[str] = []
        if invalid:
            details.append(f"存在非 L0 计划：{', '.join(invalid)}")
        if missing_level:
            details.append(f"无法确认级别：{', '.join(missing_level)}")
        report.add("4d. L0 级别核验", "FAIL", "；".join(details))
    else:
        report.add("4d. L0 级别核验", "PASS", f"全部 {len(plans)} 个 PLAN 均为 L0")


def check_approval_record(
    directory: Path,
    report: Report,
    task_id: str,
    plan_ver: str | None,
) -> None:
    path = directory / "APPROVAL_RECORD.md"
    if not path.is_file():
        report.add("5. APPROVAL_RECORD.md", "FAIL", "缺少批准记录")
        return
    text = _read(path)
    decision_match = APPROVAL_DECISION_LINE_RE.search(text)
    if decision_match is None:
        report.add("5. APPROVAL_RECORD.md", "FAIL", "未找到整行 Decision 字段")
    else:
        raw = _normalize_value(decision_match.group(1))
        normalized = re.sub(r"\s+", " ", raw.replace("_", " ")).strip().upper()
        if "/" in raw:
            report.add(
                "5. APPROVAL_RECORD.md",
                "FAIL",
                f"Decision 含未消除选项：{raw}",
            )
        elif normalized in APPROVAL_DECISIONS:
            report.add("5. APPROVAL_RECORD.md", "PASS", f"Decision: {raw}")
        else:
            report.add(
                "5. APPROVAL_RECORD.md",
                "FAIL",
                "Decision 必须为 APPROVED / APPROVED_WITH_CONDITIONS / APPROVED WITH CONDITIONS",
            )

    missing: list[str] = []
    placeholders: list[str] = []
    invalid_commit: list[str] = []
    for key in APPROVAL_FIELD_KEYS:
        block = _approval_field_block(text, key)
        if block is None:
            missing.append(key)
            continue
        if _field_block_is_placeholder(block):
            placeholders.append(key)
        if key == "Base Commit":
            values = re.split(r"\s+/\s+", block.strip())
            commit_value = values[-1]
            if not _is_commit_legal(commit_value):
                invalid_commit.append(commit_value)
    if missing:
        report.add("5a. 批准记录字段", "FAIL", f"缺少：{', '.join(missing)}")
    elif placeholders:
        report.add("5a. 批准记录字段", "FAIL", f"仍为占位符：{', '.join(placeholders)}")
    elif invalid_commit:
        report.add("5a. 批准记录字段", "FAIL", f"Base Commit 非法：{invalid_commit[0]}")
    else:
        report.add(
            "5a. 批准记录字段",
            "PASS",
            "Workflow / 写入边界 / 禁止区 / Computer-Use / Base Commit / Approver / Time 齐全",
        )

    approval_task_id = _approval_task_id_value(text)
    id_ok = (
        approval_task_id is not None
        and re.search(rf"\b{re.escape(task_id)}\b", approval_task_id) is not None
    )
    ver_ok = plan_ver is not None and re.search(rf"\bv{plan_ver}\b", text)
    if id_ok and ver_ok:
        report.add("5b. 批准对象一致", "PASS", f"{task_id} / v{plan_ver}")
    else:
        details = []
        if not id_ok:
            details.append(f"Task ID 不是 {task_id}")
        if not ver_ok:
            details.append(f"未锁定 Plan Version v{plan_ver or 'NN'}")
        report.add("5b. 批准对象一致", "FAIL", "；".join(details))

    plan_path, _ = _find_latest(directory, PLAN_FILE_PATTERN)
    plan_text = _read(plan_path) if plan_path is not None else ""
    plan_writes, plan_forbidden, _ = _scope_from_plan(plan_text)
    approval_write_values = _approval_field_block(
        text, "Approved Write Boundaries"
    )
    approval_forbidden_values = _approval_field_block(text, "Explicitly Forbidden")
    approval_writes = [
        parsed
        for value in (approval_write_values or "").splitlines()
        if (parsed := _parse_scope_item(re.sub(r"^\s*[-*]\s*", "", value))) is not None
    ]
    approval_forbidden = [
        parsed
        for value in (approval_forbidden_values or "").splitlines()
        if (parsed := _parse_forbidden_item(re.sub(r"^\s*[-*]\s*", "", value)))
        is not None
    ]
    if sorted(approval_writes) != plan_writes:
        report.add(
            "5c. 批准写入边界",
            "FAIL",
            f"批准记录 {sorted(approval_writes)} 与 PLAN {plan_writes} 不一致",
        )
    elif sorted(approval_forbidden) != plan_forbidden:
        report.add(
            "5c. 批准写入边界",
            "FAIL",
            f"批准记录禁止区 {sorted(approval_forbidden)} 与 PLAN {plan_forbidden} 不一致",
        )
    else:
        report.add("5c. 批准写入边界", "PASS", "写入边界与禁止区同 PLAN 一致")

    plan_auth = _normalize_value(_field_value(plan_text, "Computer-Use Authorization") or "")
    approval_auth = _normalize_value(
        _field_value(text, "Computer-Use Authorization") or ""
    )
    if plan_auth != approval_auth or not approval_auth:
        report.add(
            "5d. Computer-Use Authorization",
            "FAIL",
            f"PLAN={plan_auth or '缺失'}，批准记录={approval_auth or '缺失'}",
        )
    else:
        report.add(
            "5d. Computer-Use Authorization",
            "PASS",
            approval_auth,
        )

    approval_workflow = _normalize_value(
        _field_value(text, "Workflow Version") or ""
    )
    plan_workflow = _normalize_value(_field_value(plan_text, "Workflow Version") or "")
    if approval_workflow != WORKFLOW_VERSION or plan_workflow != approval_workflow:
        report.add(
            "5e. Approval Workflow Version",
            "FAIL",
            f"PLAN={plan_workflow or '缺失'}，批准记录={approval_workflow or '缺失'}",
        )
    else:
        report.add("5e. Approval Workflow Version", "PASS", approval_workflow)

    approved_base = _approval_base_commit(text)
    planned_base = _plan_base_commit(plan_text)
    if (
        not approved_base
        or not planned_base
        or approved_base.casefold() != planned_base.casefold()
    ):
        report.add(
            "5f. Approval Base Commit",
            "FAIL",
            f"PLAN={planned_base or '缺失'}，批准记录={approved_base or '缺失'}",
        )
    else:
        report.add("5f. Approval Base Commit", "PASS", approved_base)


def check_execution_report(
    directory: Path,
    report: Report,
    plan_ver: str | None,
    l0: bool = False,
) -> None:
    path, count = _find_latest(directory, EXEC_REPORT_PATTERN)
    if path is None:
        report.add("6. EXECUTION_REPORT_Axx.md", "FAIL", "缺少 A01-A03 执行报告")
        return
    text = _read(path)
    missing = [section for section in EXEC_REPORT_SECTIONS if not _has_heading(text, section)]
    if missing:
        report.add(
            "6. EXECUTION_REPORT_Axx.md",
            "FAIL",
            f"缺少章节：{'; '.join(missing)}",
        )
    else:
        report.add(
            "6. EXECUTION_REPORT_Axx.md",
            "PASS",
            _latest_detail(f"{path.name}，11 节齐全", count),
        )

    conclusion_match = CONCLUSION_LINE_RE.search(text)
    if conclusion_match is None:
        report.add("6a. 报告结论", "FAIL", "未找到整行 Conclusion")
    else:
        conclusion = _normalize_value(conclusion_match.group(1))
        if "/" in conclusion or _is_placeholder_value(conclusion):
            report.add("6a. 报告结论", "FAIL", f"结论仍有占位或选项：{conclusion}")
        elif conclusion in CONCLUSION_ENUM:
            report.add("6a. 报告结论", "PASS", f"Conclusion: {conclusion}")
        else:
            report.add(
                "6a. 报告结论",
                "FAIL",
                "Conclusion 必须为 PASS / PASS WITH WARNINGS / FAIL / BLOCKED / NOT RUN",
            )

    task_value = _field_value(text, "Task ID")
    if task_value is not None and directory.name in task_value:
        report.add("6b. Task ID 一致", "PASS", directory.name)
    else:
        report.add("6b. Task ID 一致", "FAIL", f"报告未引用目录 Task ID {directory.name}")

    if plan_ver is None and l0:
        report.add("6c. 版本引用一致", "PASS", "L0 快速通道无 PLAN，跳过版本引用")
    elif plan_ver is None:
        report.add("6c. 版本引用一致", "FAIL", "目录内无 PLAN_vNN.md")
    elif re.search(rf"\bv{plan_ver}\b", text):
        report.add("6c. 版本引用一致", "PASS", f"引用批准版本 v{plan_ver}")
    else:
        report.add("6c. 版本引用一致", "FAIL", f"未引用批准版本 v{plan_ver}")

    workflow = _normalize_value(_field_value(text, "Workflow Version") or "")
    if workflow != WORKFLOW_VERSION:
        report.add(
            "6d. Report Workflow Version",
            "FAIL",
            f"执行报告必须声明 Workflow Version: {WORKFLOW_VERSION}",
        )
    else:
        report.add("6d. Report Workflow Version", "PASS", workflow)

    plan_path, _ = _find_latest(directory, PLAN_FILE_PATTERN)
    plan_text = _read(plan_path) if plan_path is not None else ""
    if plan_path is None and l0:
        brief_path = directory / "TASK_BRIEF.md"
        brief_text = _read(brief_path) if brief_path.is_file() else ""
        l0_contract = _parse_l0_contract(brief_text)
        plan_contracts = [l0_contract] if l0_contract else []
        approved_auth = _normalize_value(
            _field_value(brief_text, "Computer-Use Authorization") or ""
        )
    else:
        plan_contracts, _ = _parse_plan_ac_contract(plan_text)
        approval_path = directory / "APPROVAL_RECORD.md"
        approval_text = _read(approval_path) if approval_path.is_file() else ""
        approved_auth = _normalize_value(
            _field_value(approval_text, "Computer-Use Authorization") or ""
        )
    plan_by_id = {item["AC"]: item for item in plan_contracts}
    mapping, mapping_errors = _parse_report_ac_mapping(text)
    if plan_by_id and set(mapping) != set(plan_by_id):
        mapping_errors.append(
            f"AC 集合不一致：PLAN {sorted(plan_by_id)}，报告 {sorted(mapping)}"
        )
    for ac_id, item in mapping.items():
        evidence = _evidence_tokens(item["Evidence Type"])
        invalid = sorted(evidence - EVIDENCE_TYPES)
        if invalid:
            mapping_errors.append(f"{ac_id} Evidence Type 非法：{', '.join(invalid)}")
        if _is_placeholder_value(item["Result"]) or item["Result"] not in AC_RESULTS:
            mapping_errors.append(
                f"{ac_id} Result 必须为 {'/'.join(sorted(AC_RESULTS))}，当前 {item['Result'] or '空'}"
            )
        if _is_placeholder_value(item["Evidence"]):
            mapping_errors.append(f"{ac_id} Evidence 为空或占位")
        plan_item = plan_by_id.get(ac_id)
        if (
            plan_item is not None
            and plan_item["Class"] == "WORKER_AUTOMATABLE"
            and evidence & VISUAL_EVIDENCE
        ):
            mapping_errors.append(
                f"{ac_id} 自动项不得用截图、视频或观察作为主证据"
            )
    if mapping_errors:
        report.add("6e. AC Mapping Contract", "FAIL", "；".join(mapping_errors))
    else:
        report.add(
            "6e. AC Mapping Contract",
            "PASS",
            f"{len(mapping)} 条 AC 与 PLAN 一致",
        )

    has_visual = any(
        _evidence_tokens(item["Evidence Type"]) & VISUAL_EVIDENCE
        for item in mapping.values()
    )
    visual_errors = _check_visual_evidence_notes(text) if has_visual else []
    if visual_errors:
        report.add("6f. Visual Evidence", "FAIL", "；".join(visual_errors))
    elif has_visual:
        report.add("6f. Visual Evidence", "PASS", "视觉目的、场景与期望已记录")

    computer_errors = _check_computer_use_record(
        text,
        approved_authorization=approved_auth,
    )
    if computer_errors:
        report.add("6g. Computer-Use Record", "FAIL", "；".join(computer_errors))
    else:
        report.add("6g. Computer-Use Record", "PASS", "使用状态、授权与记录一致")


def check_acceptance(directory: Path, report: Report, l0: bool = False) -> None:
    path = directory / "ACCEPTANCE.md"
    if not path.is_file():
        report.add("7. ACCEPTANCE.md", "FAIL", "缺少 CEO 验收记录")
        return
    text = _read(path)
    decision_match = ACCEPTANCE_DECISION_LINE_RE.search(text)
    if decision_match is None:
        report.add("7. ACCEPTANCE.md", "FAIL", "未找到整行用户决定/Decision")
    else:
        decision = _normalize_value(decision_match.group(1))
        if "/" in decision or _is_placeholder_value(decision):
            report.add("7. ACCEPTANCE.md", "FAIL", f"决定仍有占位或选项：{decision}")
        elif decision in ACCEPTANCE_DECISIONS:
            report.add("7. ACCEPTANCE.md", "PASS", f"用户决定：{decision}")
        else:
            report.add(
                "7. ACCEPTANCE.md",
                "FAIL",
                "必须为 ACCEPT / ACCEPT WITH FOLLOW-UP / REJECT",
            )
    workflow = _normalize_value(_field_value(text, "Workflow Version") or "")
    if workflow != WORKFLOW_VERSION:
        report.add(
            "7a. Acceptance Workflow Version",
            "FAIL",
            f"ACCEPTANCE 必须声明 Workflow Version: {WORKFLOW_VERSION}",
        )
    else:
        report.add("7a. Acceptance Workflow Version", "PASS", workflow)

    plan_path, _ = _find_latest(directory, PLAN_FILE_PATTERN)
    plan_text = _read(plan_path) if plan_path is not None else ""
    if plan_path is None and l0:
        brief_path = directory / "TASK_BRIEF.md"
        brief_text = _read(brief_path) if brief_path.is_file() else ""
        l0_contract = _parse_l0_contract(brief_text)
        plan_contracts = [l0_contract] if l0_contract else []
    else:
        plan_contracts, _ = _parse_plan_ac_contract(plan_text)
    plan_by_id = {item["AC"]: item for item in plan_contracts}
    contracts, _, errors = _parse_acceptance_contract(text)
    if plan_by_id and set(contracts) != set(plan_by_id):
        errors.append(
            f"AC 集合不一致：PLAN {sorted(plan_by_id)}，ACCEPTANCE {sorted(contracts)}"
        )
    for ac_id, item in contracts.items():
        evidence = _evidence_tokens(item["Primary Evidence"])
        invalid = sorted(evidence - EVIDENCE_TYPES)
        if invalid:
            errors.append(f"{ac_id} Primary Evidence 非法：{', '.join(invalid)}")
        if _is_placeholder_value(item["Result"]) or item["Result"] not in AC_RESULTS:
            errors.append(
                f"{ac_id} Result 必须为 {'/'.join(sorted(AC_RESULTS))}，当前 {item['Result'] or '空'}"
            )
        plan_item = plan_by_id.get(ac_id)
        if plan_item is not None:
            if item["Class"] != plan_item["Class"] or item["Executor"] != plan_item["Executor"]:
                errors.append(f"{ac_id} Class/Executor 与 PLAN 不一致")
            if plan_item["Class"] == "WORKER_AUTOMATABLE" and evidence & VISUAL_EVIDENCE:
                errors.append(f"{ac_id} 自动项不得以视觉证据为主")
    has_visual = any(
        _evidence_tokens(item["Primary Evidence"]) & VISUAL_EVIDENCE
        for item in contracts.values()
    )
    if has_visual:
        errors.extend(
            f"ACCEPTANCE 视觉证据：{error}"
            for error in _check_visual_evidence_notes(text)
        )
    if errors:
        report.add("7b. AC 验收契约", "FAIL", "；".join(errors))
    else:
        report.add("7b. AC 验收契约", "PASS", f"{len(contracts)} 条 AC 与 PLAN 一致")


def check_recon_report(directory: Path, report: Report) -> None:
    path = directory / "RECON_REPORT.md"
    if not path.is_file():
        report.add("3. RECON_REPORT.md", "PASS", "未触发只读调查")
        return
    text = _read(path)
    missing = [section for section in RECON_SECTIONS if not _has_heading(text, section)]
    if missing:
        report.add("3. RECON_REPORT.md", "FAIL", f"缺少章节：{'; '.join(missing)}")
    else:
        report.add("3. RECON_REPORT.md", "PASS", "7 节齐全")


def validate(task_dir: Path, mode: str, l0: bool = False) -> Report:
    report = Report(task_dir=str(task_dir), mode=mode, l0=l0)
    if mode not in MODES:
        report.add("校验模式", "FAIL", f"v4.0 仅支持 {'/'.join(MODES)}")
        return report
    if not task_dir.is_dir():
        report.add("任务目录", "FAIL", f"{task_dir} 不存在")
        return report
    if TASK_DIR_PATTERN.fullmatch(task_dir.name):
        report.add("任务目录命名", "PASS", task_dir.name)
    else:
        report.add("任务目录命名", "FAIL", f"{task_dir.name} 不符合 GD-YYYY-NNNN")

    check_project_profile(task_dir, report)
    plan_path, _ = _find_latest(task_dir, PLAN_FILE_PATTERN)
    plan_ver = (
        PLAN_FILE_PATTERN.match(plan_path.name).group(1)  # type: ignore[union-attr]
        if plan_path is not None
        else None
    )

    if l0:
        check_task_brief(task_dir, report, l0=True)
        check_plan_l0(task_dir, report)
        approval = task_dir / "APPROVAL_RECORD.md"
        if approval.is_file():
            check_approval_record(task_dir, report, task_dir.name, plan_ver)
        if mode in {"watchdog", "archive"}:
            check_execution_report(task_dir, report, plan_ver, l0=True)
            check_diff_scope(task_dir, report, mode=mode, l0=True)
        if mode == "archive":
            check_acceptance(task_dir, report, l0=True)
        return report

    check_task_brief(task_dir, report)
    check_context_manifest(task_dir, report, task_dir.name)
    check_recon_report(task_dir, report)
    check_plan(task_dir, report, mode, plan_ver)
    if mode in {"worker", "watchdog", "archive"}:
        check_approval_record(task_dir, report, task_dir.name, plan_ver)
    if mode in {"watchdog", "archive"}:
        check_execution_report(task_dir, report, plan_ver)
        check_diff_scope(task_dir, report, mode=mode, l0=False)
    if mode == "archive":
        check_acceptance(task_dir, report, l0=False)
    return report


def list_required(mode: str, l0: bool = False) -> str:
    if l0:
        mode_items = {
            "planner": ["TASK_BRIEF.md（L0 mini 即可）"],
            "worker": ["TASK_BRIEF.md（L0 mini 即可）"],
            "watchdog": ["TASK_BRIEF.md", "EXECUTION_REPORT_A0x.md"],
            "archive": ["TASK_BRIEF.md", "EXECUTION_REPORT_A0x.md", "ACCEPTANCE.md"],
        }
        lines = [
            f"模式 {mode}（v4.0 L0）：PLAN/APPROVAL_RECORD/FEED_DROP 可省略；"
            "若存在 PLAN，任意非 L0 计划均失败。"
        ]
        lines.extend(f"  - {item}" for item in mode_items[mode])
        return "\n".join(lines)
    common = [
        "TASK_BRIEF.md",
        "00_CONTEXT_MANIFEST.md（Workflow Version: v4.0）",
        "FEED_DROP/（非空、映射与 SHA-256 存在）",
        "PLAN_vNN.md（写入边界/AC/Test Plan）",
    ]
    mode_items = {
        "planner": common,
        "worker": common + ["APPROVAL_RECORD.md（PLAN 必须 APPROVED）"],
        "watchdog": common
        + ["APPROVAL_RECORD.md（PLAN 必须 APPROVED）", "EXECUTION_REPORT_A0x.md"],
        "archive": common
        + [
            "APPROVAL_RECORD.md（PLAN 必须 APPROVED）",
            "EXECUTION_REPORT_A0x.md",
            "ACCEPTANCE.md",
        ],
    }
    lines = [
        f"模式 {mode} 必查件（v4.0；目录 ^GD-\\d{{4}}-\\d{{4}}$；"
        "RECON_REPORT.md 按需；watchdog/archive 自动审计 Git Diff）："
    ]
    lines.extend(f"  - {item}" for item in mode_items[mode])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="agent-workflow-kit v4.0 交接、证据与 Diff 边界校验器"
    )
    parser.add_argument("task_dir", nargs="?", help="任务目录，如 AI_Context/TASKS/GD-2026-0001")
    parser.add_argument(
        "--for",
        dest="mode",
        default="worker",
        metavar="MODE",
        help="planner|worker|watchdog|archive（默认 worker）",
    )
    parser.add_argument("--l0", action="store_true", help="L0 CEO 快速通道")
    parser.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    parser.add_argument("--list", action="store_true", help="列出当前模式必查件后退出")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.mode not in MODES:
        hint = LEGACY_MODE_HINTS.get(args.mode)
        migration = f"；请改用 --for {hint}" if hint else ""
        parser.error(
            f"v4.0 模式仅支持 {'/'.join(MODES)}，收到 {args.mode}{migration}"
        )
    if args.list:
        print(list_required(args.mode, args.l0))
        return 0
    if not args.task_dir:
        parser.error("请提供任务目录，或使用 --list")
    report = validate(Path(args.task_dir), args.mode, args.l0)
    print(report.to_json() if args.json else report.render())
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
