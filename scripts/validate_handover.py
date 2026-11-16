#!/usr/bin/env python3
"""validate_handover.py — 统一交接包校验器（Agent 工作流 v2.0 第 7 章 / 表 15）

校验 AI_Context/TASKS/GD-YYYY-NNNN/ 下交接包七件套的结构完整性。
只做结构校验，不替代编译、测试与人工审查。

用法：
    python scripts/validate_handover.py <task_dir> [--for planner|executor|verifier|archive] [--l0] [--json] [--list]

模式与必查件：
    planner  : TASK_BRIEF.md + CONTEXT_PACKET_vNN.md + PLAN_vNN.md（草案态）
    executor : planner 三件 + PLAN 状态为 APPROVED + APPROVAL_RECORD.md
    verifier : executor 四件 + EXECUTION_REPORT_Axx.md
    archive  : verifier 五件 + ACCEPTANCE.md

L0 快速通道（--l0，与 --for 正交）：
    - 放行无 PLAN_vNN.md、无 APPROVAL_RECORD.md；CONTEXT_PACKET_vNN.md 可选（存在则照常校验格式）。
    - TASK_BRIEF.md 允许标准 10 段，或 L0 三行 mini 任务书（含 L0 标识、目标与验收、文件范围，无 <> 占位符）。
    - 目录内若存在 PLAN_vNN.md，其 Task Level 必须为 L0（L1/L2/L3 → FAIL，防止借 L0 绕过审批）。
    - --l0 --for verifier 必查 TASK_BRIEF.md + EXECUTION_REPORT_A0x.md；--l0 --for archive 追加必查 ACCEPTANCE.md。

退出码：0 = 全部 PASS（WARN 不影响）；1 = 存在 FAIL。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

TASK_DIR_PATTERN = re.compile(r"^GD-\d{4}-\d{4}$")
PLAN_FILE_PATTERN = re.compile(r"^PLAN_v(\d{2})\.md$")
CONTEXT_PACKET_PATTERN = re.compile(r"^CONTEXT_PACKET_v(\d{2})\.md$")
EXEC_REPORT_PATTERN = re.compile(r"^EXECUTION_REPORT_A0([1-3])\.md$")

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
    "6. Context Packet",
    "7. Evidence",
]

PLAN_ALLOWED_STATUSES_PLANNER = {"DRAFT", "NEED_INVESTIGATION", "IN_REVIEW"}
PLAN_ALLOWED_STATUSES_EXECUTOR = {"APPROVED"}
CONCLUSION_ENUM = {"PASS", "PASS WITH WARNINGS", "FAIL", "BLOCKED", "NOT RUN"}
ACCEPTANCE_DECISIONS = {"ACCEPT", "ACCEPT WITH FOLLOW-UP", "REJECT"}
APPROVAL_DECISIONS = {"APPROVED", "APPROVED WITH CONDITIONS"}

MODES = ("planner", "executor", "verifier", "archive")

# ---- 占位符与字段正则 ----
ANGLE_PLACEHOLDER_RE = re.compile(r"<[^>\n]+>")
COMMIT_FIELD_RE = re.compile(r"commit[:：]?\s*([^\n]+)", re.MULTILINE | re.IGNORECASE)
COMMIT_HEX_RE = re.compile(r"^[0-9a-fA-F]{7,40}$")
COMMIT_TS_RE = re.compile(r"\d{4}-\d{2}-\d{2}([T ]\d{1,2}:\d{2}(:\d{2})?)?")
PLAN_VERSION_FIELD_RE = re.compile(r"Plan\s*Version[:：]?\s*v?(\d{2})", re.IGNORECASE)
TASK_LEVEL_FIELD_RE = re.compile(r"Task\s*Level[:：]?\s*L(\d)", re.IGNORECASE)
CONCLUSION_LINE_RE = re.compile(r"^(?:\*\*)?Conclusion(?:\*\*)?[:：][ \t]*(.+?)[ \t]*$", re.MULTILINE)
ACCEPTANCE_DECISION_LINE_RE = re.compile(
    r"^(?:\*\*)?(?:用户决定|Decision)(?:\*\*)?[:：][ \t]*(.+?)[ \t]*$", re.MULTILINE
)
APPROVAL_DECISION_LINE_RE = re.compile(r"^(?:\*\*)?Decision(?:\*\*)?[:：][ \t]*(.+?)[ \t]*$", re.MULTILINE)
APPROVAL_FIELD_KEYS = ["Approved Scope", "Base Commit", "Approver", "Approval Time"]
L0_MINI_REQUIRED_MARKS = ["目标与验收", "文件范围"]


def _is_commit_placeholder(value: str) -> bool:
    if ANGLE_PLACEHOLDER_RE.search(value):
        return True
    return "待填写" in value or "TBD" in value.upper()


def _is_commit_legal(value: str) -> bool:
    if COMMIT_HEX_RE.fullmatch(value):
        return True
    if "可恢复副本" in value:
        return True
    return bool(COMMIT_TS_RE.search(value))


@dataclass
class CheckResult:
    """单条校验结果。"""

    item: str
    status: str  # PASS / FAIL / WARN
    detail: str = ""

    @property
    def failed(self) -> bool:
        return self.status == "FAIL"


@dataclass
class Report:
    """一次校验运行的全部结果。"""

    task_dir: str
    mode: str
    l0: bool = False
    checks: list[CheckResult] = field(default_factory=list)

    def add(self, item: str, status: str, detail: str = "") -> None:
        self.checks.append(CheckResult(item=item, status=status, detail=detail))

    @property
    def fails(self) -> list[CheckResult]:
        return [c for c in self.checks if c.failed]

    @property
    def warns(self) -> list[CheckResult]:
        return [c for c in self.checks if c.status == "WARN"]

    @property
    def ok(self) -> bool:
        return not self.fails

    def render(self) -> str:
        tag = f" / L0 快速通道" if self.l0 else ""
        lines = [f"交接包校验：{self.task_dir}（模式 {self.mode}{tag}）", "-" * 64]
        for c in self.checks:
            mark = {"PASS": "[PASS]", "FAIL": "[FAIL]", "WARN": "[WARN]"}[c.status]
            line = f"{mark} {c.item}"
            if c.detail:
                line += f" — {c.detail}"
            lines.append(line)
        lines.append("-" * 64)
        lines.append(
            f"结果：PASS {len(self.checks) - len(self.fails) - len(self.warns)}"
            f" / FAIL {len(self.fails)} / WARN {len(self.warns)}"
        )
        lines.append("结论：通过" if self.ok else "结论：未通过（先修复 FAIL 再交接）")
        return "\n".join(lines)

    def to_json(self) -> str:
        return json.dumps(
            {
                "task_dir": self.task_dir,
                "mode": self.mode,
                "l0": self.l0,
                "ok": self.ok,
                "checks": [
                    {"item": c.item, "status": c.status, "detail": c.detail}
                    for c in self.checks
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
    """匹配 Markdown 标题行（## 1. Objective），容忍多余空格与可选序号句点。"""
    tokens = [re.escape(t) for t in heading.split()]
    pattern = re.compile(
        r"^#{1,4}\s*" + r"\s+".join(tokens) + r"\s*$", re.MULTILINE | re.IGNORECASE
    )
    return bool(pattern.search(text))


def _find_latest(directory: Path, pattern: re.Pattern[str]) -> tuple[Path | None, int]:
    """按版本号取最新文件；返回 (最新文件, 匹配文件总数)。pattern 须含一个版本号捕获组。"""
    found = [p for p in directory.iterdir() if p.is_file() and pattern.match(p.name)]
    if not found:
        return None, 0
    latest = max(found, key=lambda p: int(pattern.match(p.name).group(1)))  # type: ignore[union-attr]
    return latest, len(found)


def _latest_detail(name: str, count: int) -> str:
    if count > 1:
        return f"已选最新（共 {count} 个版本）：{name}"
    return name


def check_task_brief(directory: Path, report: Report, l0: bool = False) -> None:
    path = directory / "TASK_BRIEF.md"
    if not path.is_file():
        report.add("1. TASK_BRIEF.md", "FAIL", "缺少文件（用户任务简报，附录 C）")
        return
    text = _read(path)
    missing = [s for s in TASK_BRIEF_SECTIONS if s not in text]
    if not missing:
        report.add("1. TASK_BRIEF.md", "PASS", "10 段结构齐全")
        return
    if l0:
        if _check_l0_mini_brief(text):
            report.add("1. TASK_BRIEF.md", "PASS", "L0 三行 mini 任务书（要素齐全）")
            return
        report.add(
            "1. TASK_BRIEF.md",
            "FAIL",
            "非标准 10 段，且不满足 L0 mini 要求（须含 L0 标识、目标与验收、文件范围，且无 <> 占位符）",
        )
        return
    report.add("1. TASK_BRIEF.md", "FAIL", f"缺少 {len(missing)} 段：{'、'.join(missing)}")


def _check_l0_mini_brief(text: str) -> bool:
    if not re.search(r"\bL0\b", text):
        return False
    if any(mark not in text for mark in L0_MINI_REQUIRED_MARKS):
        return False
    if ANGLE_PLACEHOLDER_RE.search(text):
        return False
    return True


def check_context_packet(directory: Path, report: Report, mode: str) -> None:
    path, count = _find_latest(directory, CONTEXT_PACKET_PATTERN)
    if path is None:
        report.add(
            "2. CONTEXT_PACKET_vNN.md", "FAIL", "缺少文件（须含版本号 + 核验 commit）"
        )
        return
    text = _read(path)
    version_ok = re.search(r"v\d{2}", path.name) or re.search(
        r"版本[:：]?\s*v\d{2}", text
    )
    if not version_ok:
        report.add(
            "2. CONTEXT_PACKET_vNN.md", "FAIL", "须写明上下文包版本号（第 6.4 节硬性条款）"
        )
        return

    field_match = COMMIT_FIELD_RE.search(text)
    if field_match is None:
        report.add(
            "2. CONTEXT_PACKET_vNN.md",
            "FAIL",
            "未找到 commit 字段（须写明核验 commit 或可恢复副本时间）",
        )
        return
    value = field_match.group(1).strip().strip("`").strip()
    if _is_commit_placeholder(value):
        if mode == "planner":
            report.add(
                "2. CONTEXT_PACKET_vNN.md",
                "WARN",
                f"commit 仍为占位符（{value}）：规划阶段允许，交接执行前必须落实为真实 commit 或副本时间",
            )
        else:
            report.add(
                "2. CONTEXT_PACKET_vNN.md",
                "FAIL",
                f"commit 为占位符（{value}）：{mode} 模式下必须为真实值",
            )
        return
    if _is_commit_legal(value):
        report.add("2. CONTEXT_PACKET_vNN.md", "PASS", _latest_detail(f"{path.name}（commit: {value}）", count))
    else:
        report.add(
            "2. CONTEXT_PACKET_vNN.md",
            "FAIL",
            f"commit 值非法（{value}）：须为 7–40 位十六进制哈希，或可恢复副本时间戳（如 2026-11-16 14:00）",
        )


def check_plan(directory: Path, report: Report, mode: str, plan_ver: str | None) -> None:
    path, count = _find_latest(directory, PLAN_FILE_PATTERN)
    if path is None:
        report.add("4. PLAN_vNN.md", "FAIL", "缺少任务书草案（附录 D，14 章）")
        return
    text = _read(path)
    missing = [s for s in PLAN_SECTIONS if not _has_heading(text, s)]
    if missing:
        report.add(
            "4. PLAN_vNN.md", "FAIL", f"缺少 {len(missing)} 章：{'; '.join(missing)}"
        )
    else:
        report.add("4. PLAN_vNN.md", "PASS", _latest_detail(f"{path.name}，0.Metadata + 14 章齐全", count))

    status_match = re.search(r"Status[:：]?\s*([A-Z_]+)", text)
    status = status_match.group(1) if status_match else ""
    allowed = (
        PLAN_ALLOWED_STATUSES_EXECUTOR
        if mode in ("executor", "verifier", "archive")
        else PLAN_ALLOWED_STATUSES_PLANNER | PLAN_ALLOWED_STATUSES_EXECUTOR
    )
    if status in allowed:
        report.add("4a. PLAN 状态", "PASS", f"Status: {status}")
    elif status in PLAN_ALLOWED_STATUSES_PLANNER | PLAN_ALLOWED_STATUSES_EXECUTOR:
        report.add(
            "4a. PLAN 状态",
            "FAIL",
            f"Status: {status} 在 {mode} 模式下不合法，允许 {'/'.join(sorted(allowed))}",
        )
    else:
        report.add(
            "4a. PLAN 状态",
            "FAIL",
            "Metadata 中未找到合法 Status 字段（DRAFT / NEED_INVESTIGATION / APPROVED）",
        )

    task_id = directory.name
    if not TASK_DIR_PATTERN.match(task_id):
        report.add(
            "4b. Task ID 一致",
            "WARN",
            f"目录名 {task_id or '<空>'} 不符合 GD-YYYY-NNNN，跳过一致性核对",
        )
    elif re.search(rf"\b{re.escape(task_id)}\b", text):
        report.add("4b. Task ID 一致", "PASS", f"任务书引用 {task_id}")
    else:
        report.add("4b. Task ID 一致", "FAIL", f"任务书未引用目录名 {task_id}")

    # 4c. 文件名版本与正文 Plan Version 字段一致性
    if plan_ver is None:
        report.add("4c. 版本一致", "WARN", "无法从文件名解析版本号，跳过核对")
    else:
        field_ver = PLAN_VERSION_FIELD_RE.search(text)
        if field_ver is None:
            report.add(
                "4c. 版本一致", "FAIL", "正文 Metadata 缺少 Plan Version 字段"
            )
        elif field_ver.group(1) != plan_ver:
            report.add(
                "4c. 版本一致",
                "FAIL",
                f"文件名 v{plan_ver} 与正文 Plan Version: v{field_ver.group(1)} 不一致",
            )
        else:
            report.add("4c. 版本一致", "PASS", f"文件名与正文均为 v{plan_ver}")


def check_plan_l0(directory: Path, plan_path: Path, report: Report) -> None:
    """L0 快速通道下存在 PLAN 时的级别核验：防止高风险任务借 L0 绕过审批。"""
    text = _read(plan_path)
    level_match = TASK_LEVEL_FIELD_RE.search(text)
    if level_match is None:
        report.add(
            "4d. L0 级别核验",
            "FAIL",
            f"目录内存在 {plan_path.name} 但未标注 Task Level，无法确认符合 L0 快速通道",
        )
        return
    level = int(level_match.group(1))
    if level == 0:
        report.add("4d. L0 级别核验", "PASS", f"{plan_path.name} 为 L0 级")
    else:
        report.add(
            "4d. L0 级别核验",
            "FAIL",
            f"L0 快速通道不允许 Task Level L{level} 的任务书（防止高风险任务借 L0 绕过审批）",
        )


def _approval_field_block(text: str, key: str) -> str | None:
    """提取批准记录字段块：字段行 + 后续缩进/列表续行，直到空行或下一个字段。

    容忍复合键名前缀（如模板中的 "Branch / Base Commit:"）。
    """
    match = re.search(
        rf"^[^\n]*?{re.escape(key)}[:：][ \t]*([^\n]*)$", text, re.MULTILINE
    )
    if match is None:
        return None
    lines = [match.group(1)]
    for line in text[match.end():].splitlines():
        if not line.strip() or re.match(r"^[A-Za-z][A-Za-z /_]+[:：]", line):
            break
        lines.append(line)
    return "\n".join(lines)


def check_approval_record(
    directory: Path, report: Report, task_id: str, plan_ver: str | None
) -> None:
    path = directory / "APPROVAL_RECORD.md"
    if not path.is_file():
        report.add("5. APPROVAL_RECORD.md", "FAIL", "缺少批准记录（第 10.3 节）")
        return
    text = _read(path)

    decision_match = APPROVAL_DECISION_LINE_RE.search(text)
    if decision_match is None:
        report.add(
            "5. APPROVAL_RECORD.md",
            "FAIL",
            "未找到整行 Decision 字段（须为 APPROVED / APPROVED_WITH_CONDITIONS / APPROVED WITH CONDITIONS）",
        )
    else:
        raw = decision_match.group(1).strip()
        if "/" in raw or "或" in raw:
            report.add(
                "5. APPROVAL_RECORD.md",
                "FAIL",
                f"Decision 含未消除的选项分隔（{raw}）：必须落实为单一决定",
            )
        else:
            normalized = re.sub(r"\s+", " ", raw.replace("_", " ")).strip().upper()
            if normalized in APPROVAL_DECISIONS:
                report.add("5. APPROVAL_RECORD.md", "PASS", f"Decision: {raw}")
            else:
                report.add(
                    "5. APPROVAL_RECORD.md",
                    "FAIL",
                    f"Decision 非法（{raw}）：必须为 APPROVED / APPROVED_WITH_CONDITIONS / APPROVED WITH CONDITIONS",
                )

    missing = [k for k in APPROVAL_FIELD_KEYS if _approval_field_block(text, k) is None]
    placeholder_keys = [
        k
        for k in APPROVAL_FIELD_KEYS
        if (block := _approval_field_block(text, k)) is not None and ANGLE_PLACEHOLDER_RE.search(block)
    ]
    if missing:
        report.add("5a. 批准记录字段", "FAIL", f"缺少：{'、'.join(missing)}")
    elif placeholder_keys:
        report.add(
            "5a. 批准记录字段",
            "FAIL",
            f"字段仍为占位符：{'、'.join(placeholder_keys)}（不得残留 <...>）",
        )
    else:
        report.add("5a. 批准记录字段", "PASS", "Scope / Base Commit / Approver / Time 齐全且已落实")

    # 5b. 批准版本一致性：批准记录须引用目录 Task ID 与批准的 PLAN 版本
    if not TASK_DIR_PATTERN.match(task_id):
        report.add("5b. 批准版本一致", "WARN", "目录命名不符合 GD-YYYY-NNNN，跳过核对")
        return
    id_ok = re.search(rf"\b{re.escape(task_id)}\b", text) is not None
    if plan_ver is None:
        report.add("5b. 批准版本一致", "WARN", "目录内无 PLAN_vNN.md，跳过版本核对")
        return
    ver_ok = re.search(rf"\bv{plan_ver}\b", text) is not None
    if id_ok and ver_ok:
        report.add("5b. 批准版本一致", "PASS", f"批准记录引用 {task_id} / v{plan_ver}")
    else:
        detail = []
        if not id_ok:
            detail.append(f"未引用 Task ID {task_id}")
        if not ver_ok:
            detail.append(f"未引用批准版本 v{plan_ver}")
        report.add("5b. 批准版本一致", "FAIL", "；".join(detail))


def check_execution_report(
    directory: Path, report: Report, mode: str, plan_ver: str | None
) -> None:
    path, count = _find_latest(directory, EXEC_REPORT_PATTERN)
    if path is None:
        report.add(
            "6. EXECUTION_REPORT_Axx.md", "FAIL", "缺少执行报告（附录 E，11 节，A01–A03）"
        )
        return
    text = _read(path)
    missing = [s for s in EXEC_REPORT_SECTIONS if not _has_heading(text, s)]
    if missing:
        report.add(
            "6. EXECUTION_REPORT_Axx.md",
            "FAIL",
            f"缺少 {len(missing)} 节：{'; '.join(missing)}",
        )
    else:
        report.add(
            "6. EXECUTION_REPORT_Axx.md", "PASS", _latest_detail(f"{path.name}，11 节齐全", count)
        )

    conclusion_match = CONCLUSION_LINE_RE.search(text)
    if conclusion_match is None:
        report.add(
            "6a. 报告结论",
            "FAIL",
            "未找到整行 Conclusion 字段",
        )
    else:
        conclusion = conclusion_match.group(1).strip()
        if "/" in conclusion or "<" in conclusion:
            report.add(
                "6a. 报告结论",
                "FAIL",
                f"Conclusion 含未消除的选项（{conclusion}）：必须落实为单一枚举值",
            )
        elif conclusion in CONCLUSION_ENUM:
            report.add("6a. 报告结论", "PASS", f"Conclusion: {conclusion}")
        else:
            report.add(
                "6a. 报告结论",
                "FAIL",
                "Conclusion 必须为 PASS / PASS WITH WARNINGS / FAIL / BLOCKED / NOT RUN",
            )

    if not TASK_DIR_PATTERN.match(directory.name):
        report.add(
            "6b. Task ID 一致",
            "WARN",
            "目录命名不符合 GD-YYYY-NNNN，跳过一致性核对",
        )
    elif re.search(rf"\b{re.escape(directory.name)}\b", text):
        report.add("6b. Task ID 一致", "PASS", "")
    else:
        report.add("6b. Task ID 一致", "WARN", "执行报告未引用目录名，请人工核对")

    # 6c. 执行报告须引用批准的任务书版本（verifier / archive 模式）
    if mode in ("verifier", "archive"):
        if plan_ver is None:
            report.add("6c. 版本引用一致", "WARN", "目录内无 PLAN_vNN.md，跳过版本核对")
        elif re.search(rf"\bv{plan_ver}\b", text):
            report.add("6c. 版本引用一致", "PASS", f"执行报告引用批准版本 v{plan_ver}")
        else:
            report.add(
                "6c. 版本引用一致",
                "FAIL",
                f"执行报告未引用批准版本 v{plan_ver}（须在 Preflight 或 Metadata 写明）",
            )


def check_acceptance(directory: Path, report: Report) -> None:
    path = directory / "ACCEPTANCE.md"
    if not path.is_file():
        report.add("7. ACCEPTANCE.md", "FAIL", "缺少验收记录（用户决定）")
        return
    text = _read(path)
    decision_match = ACCEPTANCE_DECISION_LINE_RE.search(text)
    if decision_match is None:
        report.add(
            "7. ACCEPTANCE.md",
            "FAIL",
            "未找到整行「用户决定 / Decision」字段",
        )
    else:
        decision = decision_match.group(1).strip()
        if "/" in decision or "<" in decision:
            report.add(
                "7. ACCEPTANCE.md",
                "FAIL",
                f"决定含未消除的选项（{decision}）：必须落实为单一枚举值",
            )
        elif decision in ACCEPTANCE_DECISIONS:
            report.add("7. ACCEPTANCE.md", "PASS", f"决定：{decision}")
        else:
            report.add(
                "7. ACCEPTANCE.md",
                "FAIL",
                "必须为 ACCEPT / ACCEPT WITH FOLLOW-UP / REJECT 三者之一",
            )
    if "AC-" in text:
        report.add("7a. 逐条验收", "PASS", "含 AC 条目映射")
    else:
        report.add("7a. 逐条验收", "WARN", "未见 AC-xx 逐条结果，请人工确认逐条验收")


def check_recon_report(directory: Path, report: Report) -> None:
    path = directory / "RECON_REPORT.md"
    if not path.is_file():
        report.add("3. RECON_REPORT.md", "PASS", "未触发只读调查（可选项缺省）")
        return
    text = _read(path)
    missing = [s for s in RECON_SECTIONS if not _has_heading(text, s)]
    if missing:
        report.add(
            "3. RECON_REPORT.md", "FAIL", f"缺少 {len(missing)} 节：{'; '.join(missing)}"
        )
    else:
        report.add("3. RECON_REPORT.md", "PASS", "7 节齐全（附录 F）")


def validate(task_dir: Path, mode: str, l0: bool = False) -> Report:
    report = Report(task_dir=str(task_dir), mode=mode, l0=l0)

    if not task_dir.is_dir():
        report.add("任务目录", "FAIL", f"{task_dir} 不存在")
        return report
    if not TASK_DIR_PATTERN.match(task_dir.name):
        report.add(
            "任务目录命名", "FAIL", f"{task_dir.name} 不符合 GD-YYYY-NNNN 约定"
        )
    else:
        report.add("任务目录命名", "PASS", task_dir.name)

    plan_path, _ = _find_latest(task_dir, PLAN_FILE_PATTERN)
    plan_ver = (
        PLAN_FILE_PATTERN.match(plan_path.name).group(1)  # type: ignore[union-attr]
        if plan_path is not None
        else None
    )

    if l0:
        # L0 快速通道：PLAN / APPROVAL_RECORD / CONTEXT_PACKET 均可省略；
        # 存在则照常校验（PLAN 必须为 L0 级）。
        check_task_brief(task_dir, report, l0=True)
        if any(
            p.is_file() and CONTEXT_PACKET_PATTERN.match(p.name)
            for p in task_dir.iterdir()
        ):
            check_context_packet(task_dir, report, mode)
        if plan_path is not None:
            check_plan_l0(task_dir, plan_path, report)
        approval_path = task_dir / "APPROVAL_RECORD.md"
        if approval_path.is_file():
            check_approval_record(task_dir, report, task_dir.name, plan_ver)
        if mode in ("verifier", "archive"):
            check_execution_report(task_dir, report, mode, plan_ver)
        if mode == "archive":
            check_acceptance(task_dir, report)
        return report

    check_task_brief(task_dir, report)
    check_context_packet(task_dir, report, mode)
    check_recon_report(task_dir, report)
    check_plan(task_dir, report, mode, plan_ver)

    if mode in ("executor", "verifier", "archive"):
        check_approval_record(task_dir, report, task_dir.name, plan_ver)
    if mode in ("verifier", "archive"):
        check_execution_report(task_dir, report, mode, plan_ver)
    if mode == "archive":
        check_acceptance(task_dir, report)

    return report


def list_required(mode: str, l0: bool = False) -> str:
    if l0:
        per_mode = {
            "planner": ["TASK_BRIEF.md（标准 10 段或 L0 三行 mini）"],
            "executor": ["TASK_BRIEF.md（标准 10 段或 L0 三行 mini）"],
            "verifier": [
                "TASK_BRIEF.md（标准 10 段或 L0 三行 mini）",
                "EXECUTION_REPORT_A0x.md",
            ],
            "archive": [
                "TASK_BRIEF.md（标准 10 段或 L0 三行 mini）",
                "EXECUTION_REPORT_A0x.md",
                "ACCEPTANCE.md",
            ],
        }
        lines = [
            f"模式 {mode}（--l0 快速通道）必查件"
            f"（目录 {TASK_DIR_PATTERN.pattern}；PLAN/APPROVAL_RECORD/CONTEXT_PACKET 可省略，"
            "存在 PLAN 时其 Task Level 必须为 L0）："
        ]
        lines += [f"  - {name}" for name in per_mode[mode]]
        return "\n".join(lines)
    per_mode = {
        "planner": ["TASK_BRIEF.md", "CONTEXT_PACKET_vNN.md", "PLAN_vNN.md（DRAFT/NEED_INVESTIGATION）"],
        "executor": [
            "TASK_BRIEF.md",
            "CONTEXT_PACKET_vNN.md",
            "PLAN_vNN.md（Status: APPROVED）",
            "APPROVAL_RECORD.md",
        ],
        "verifier": [
            "TASK_BRIEF.md",
            "CONTEXT_PACKET_vNN.md",
            "PLAN_vNN.md（Status: APPROVED）",
            "APPROVAL_RECORD.md",
            "EXECUTION_REPORT_A0x.md",
        ],
        "archive": [
            "TASK_BRIEF.md",
            "CONTEXT_PACKET_vNN.md",
            "PLAN_vNN.md（Status: APPROVED）",
            "APPROVAL_RECORD.md",
            "EXECUTION_REPORT_A0x.md",
            "ACCEPTANCE.md",
        ],
    }
    lines = [f"模式 {mode} 必查件（目录 {TASK_DIR_PATTERN.pattern}，RECON_REPORT.md 按需可选）："]
    lines += [f"  - {name}" for name in per_mode[mode]]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="统一交接包七件套结构校验器（v2.0 第 7 章 / 表 15）"
    )
    parser.add_argument("task_dir", nargs="?", help="任务目录，如 AI_Context/TASKS/GD-2026-0001")
    parser.add_argument(
        "--for",
        dest="mode",
        choices=MODES,
        default="executor",
        help="校验模式：planner 草案齐全 / executor 批准完整 / verifier 执行报告 / archive 归档齐全",
    )
    parser.add_argument(
        "--l0",
        action="store_true",
        help="L0 快速通道：放行无 PLAN/APPROVAL_RECORD，CONTEXT_PACKET 可选；存在 PLAN 时必须为 L0 级",
    )
    parser.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    parser.add_argument("--list", action="store_true", help="列出当前模式的必查件后退出")
    args = parser.parse_args(argv)

    if args.list:
        print(list_required(args.mode, args.l0))
        return 0
    if not args.task_dir:
        parser.error("请提供任务目录，例如 AI_Context/TASKS/GD-2026-0001（或用 --list 查看必查件）")

    report = validate(Path(args.task_dir), args.mode, args.l0)
    print(report.to_json() if args.json else report.render())
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
