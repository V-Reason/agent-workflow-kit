"""Regression tests for the v3.1 handover validator."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_SPEC = importlib.util.spec_from_file_location(
    "validate_handover", _ROOT / "scripts" / "validate_handover.py"
)
vh = importlib.util.module_from_spec(_SPEC)
sys.modules["validate_handover"] = vh
_SPEC.loader.exec_module(vh)

TASK_ID = "GD-2026-0001"
COMMIT_HASH = "b64326037c36ff8dce842d0496d4c0894532ae7c"
SHA_A = "a" * 64
BASELINE_CONTENT = b"staged\n"
BASELINE_HASH = hashlib.sha256(BASELINE_CONTENT).hexdigest()
FEED_FILES = {
    "L1__PROJECT_OVERVIEW.md": "AI_Context/PROJECT_OVERVIEW.md",
    "L1__CODING_STANDARDS.md": "AI_Context/CODING_STANDARDS.md",
    "L1__BUILD_AND_TEST.md": "AI_Context/BUILD_AND_TEST.md",
    "L2__PROJECT_BOARD.md": "AI_Context/PROJECT_BOARD.md",
    "L2__ARCHITECTURE.md": "AI_Context/ARCHITECTURE.md",
    "L2__MODULE_MAP.md": "AI_Context/MODULE_MAP.md",
    "L2__DEPENDENCIES.md": "AI_Context/DEPENDENCIES.md",
}


def make_plan(status: str = "APPROVED", version: str = "01", level: str = "L1") -> str:
    body = f"""# PLAN v{version}
Task ID: {TASK_ID}
Plan Version: v{version}
Workflow Version: v3.1
Status: {status}
Task Level: {level} / Risk Level: R1
Branch / Base Commit: main / {COMMIT_HASH}
Computer-Use Authorization: NONE

## 0. Metadata
Metadata.

## 1. Objective
导出 CSV。

## 2. Non-goals
不做 Excel。

## 3. Current State
VERIFIED。

## 4. Constraints
兼容旧数据。

## 5. Proposed Design
在现有 CLI 内实现。

## 6. File Scope
### Write Boundaries
- MODIFY `src/app/**`
- CREATE `tests/**`
### Forbidden
- `pyproject.toml`
### Read Policy
- REPO_READ_ONLY_EXCEPT_SENSITIVE
### Protected Changes
- 依赖、配置、公共接口与序列化变更必须升版重审

## 7. Execution Steps
1. 实现并测试。

## 8. Engineering Rules
不删断言。

## 9. Acceptance Criteria
| AC | Class | Executor | Criterion | Primary Evidence |
| --- | --- | --- | --- | --- |
| AC-01 | WORKER_AUTOMATABLE | WORKER | 测试通过 | TEST_RESULT+LOG |

## 10. Test Plan
| AC | Command / Action | CWD | Expected |
| --- | --- | --- | --- |
| AC-01 | python -m unittest | . | exit 0 |

## 11. Risks
低风险。

## 12. Rollback
按 Diff 回退。

## 13. Open Questions
无阻塞。

## 14. Approval
PENDING。
"""
    return body


def make_l0_brief() -> str:
    return (
        "# L0 任务\n"
        "Task ID: GD-2026-0001 / Task Level: L0 / Workflow Version: v3.1 / "
        f"Base Commit: {COMMIT_HASH}\n"
        "目标与验收: WORKER_AUTOMATABLE / WORKER / TEST_RESULT / pytest exit 0\n"
        "文件边界: MODIFY `src/app/**`; FORBIDDEN `pyproject.toml`; "
        "Computer-Use Authorization: NONE\n"
    )


def make_brief() -> str:
    return "\n".join(
        [
            "# TASK BRIEF",
            "Workflow Version: v3.1",
            "1. Objective: 导出 CSV",
            "2. Background: 用户需要",
            "3. Current Behavior: 无导出",
            "4. Expected Behavior: 可导出",
            "5. Non-goals: 不做 Excel",
            "6. 已知约束: 兼容旧数据",
            "7. 相关模块与文件: interfaces/cli.py",
            "8. 已观察到的错误: 无",
            "9. 验收方式: pytest 通过",
            "10. 其他说明: 无",
        ]
    )


def layer_from_name(name: str) -> str:
    return name[:2]


def make_manifest(
    commit: str = COMMIT_HASH,
    *,
    workflow_version: str = "v3.1",
    round_count: int = 0,
    round_section: str = "",
    extra_rows: list[tuple[str, str, str, int]] | None = None,
) -> str:
    rows = [
        (staged, layer_from_name(staged), source, 1)
        for staged, source in FEED_FILES.items()
    ]
    rows.extend(extra_rows or [])
    table = "\n".join(
        f"| `{staged}` | {layer} | `{source}` | {tokens} | "
        f"{BASELINE_HASH if not extra_rows else SHA_A} |"
        for staged, layer, source, tokens in rows
    )
    return (
        f"# 00 CONTEXT MANIFEST — {TASK_ID}\n\n"
        f"- Workflow Version: {workflow_version}\n"
        f"- Task ID: {TASK_ID}\n"
        f"- Base Commit: {commit}\n"
        "- Baseline Generated At: 2026-11-16T12:00:00+08:00\n"
        "- Baseline Generation Mode: baseline\n"
        f"- Need Files Rounds: {round_count}\n\n"
        "| 暂存名 | 层级 | 原路径 | 估算 Token | SHA-256 |\n"
        "| --- | --- | --- | ---: | --- |\n"
        f"{table}\n\n"
        "## NEED_FILES Round Index\n\n"
        f"{round_section}"
    )


def make_round_section(
    round_number: int,
    *,
    source: str,
    staged: str,
    content: bytes = b"round data\n",
) -> str:
    digest = hashlib.sha256(content).hexdigest()
    return (
        f"### ROUND_{round_number:02d}\n\n"
        "- Created At: 2026-11-16T12:30:00+08:00\n"
        "- Reason: 确认接口\n"
        f"- Source Commit: {COMMIT_HASH}\n"
        f"- Round Manifest: `NEED_FILES/ROUND_{round_number:02d}/ROUND_MANIFEST.md`\n\n"
        "| 暂存名 | 层级 | 原路径 | 估算 Token | SHA-256 |\n"
        "| --- | --- | --- | ---: | --- |\n"
        f"| `{staged}` | L3 | `{source}` | 3 | {digest} |\n"
    )


def make_approval(version: str = "01", decision: str = "APPROVED") -> str:
    return (
        "# APPROVAL RECORD\n"
        f"Task ID: {TASK_ID}\n"
        f"Approved Plan: v{version}\n"
        "Workflow Version: v3.1\n"
        f"Decision: {decision}\n"
        "Approved Write Boundaries:\n"
        "- MODIFY src/app/**\n"
        "- CREATE tests/**\n"
        "Explicitly Forbidden:\n"
        "- pyproject.toml\n"
        "Computer-Use Authorization: NONE\n"
        "Conditions: 无\n"
        f"Branch / Base Commit: main / {COMMIT_HASH}\n"
        "Approver: 用户\n"
        "Approval Time: 2026-11-16 12:00 (UTC+8)\n"
    )


def make_exec_report(
    version: str = "01",
    attempt: str = "01",
    conclusion: str = "PASS",
    task_id: str = TASK_ID,
) -> str:
    lines = [
        f"# EXECUTION REPORT A{attempt}",
        f"Task ID: {task_id} / Plan Version: v{version} / Attempt: A{attempt}",
        "Workflow Version: v3.1",
        "",
    ]
    for heading in vh.EXEC_REPORT_SECTIONS:
        lines.extend([f"## {heading}", ""])
        if heading.startswith("4. Commands"):
            lines.extend(
                [
                    "Computer-Use Used: NO",
                    "Computer-Use Authorization: NONE",
                    "Necessity: NOT APPLICABLE",
                    "Scope: NOT APPLICABLE",
                    "Result: NOT APPLICABLE",
                    "",
                ]
            )
        elif heading.startswith("5. AC Mapping"):
            lines.extend(
                [
                    "| AC | Result | Evidence Type | Evidence |",
                    "| --- | --- | --- | --- |",
                    "| AC-01 | PASS | TEST_RESULT+LOG | evidence.log |",
                    "",
                ]
            )
    lines.extend([f"Conclusion: {conclusion}", "所需决策: none"])
    return "\n".join(lines) + "\n"


def make_acceptance(decision: str = "ACCEPT") -> str:
    return (
        f"# ACCEPTANCE — {TASK_ID}\n"
        "Workflow Version: v3.1\n\n"
        "| AC | Class | Executor | Expected | Result | Primary Evidence |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        "| AC-01 | WORKER_AUTOMATABLE | WORKER | 导出可用 | PASS | TEST_RESULT+LOG |\n\n"
        "## Unplanned Change Review\n\n"
        "| Path | Decision | Reason |\n"
        "| --- | --- | --- |\n"
        "| none | NOT APPLICABLE | 无未计划改动 |\n\n"
        "Watchdog 结论建议: PASS\n"
        f"用户决定: {decision}\n"
        "后续动作: none\n"
    )


class ValidatorTestBase(unittest.TestCase):
    def run_validate(
        self,
        files: dict[str, str],
        mode: str,
        l0: bool = False,
        *,
        feed_names: set[str] | None = None,
        extra_files: dict[str, str | bytes] | None = None,
    ) -> vh.Report:
        with tempfile.TemporaryDirectory() as tmp:
            task_dir = Path(tmp) / TASK_ID
            task_dir.mkdir()
            for name, content in files.items():
                (task_dir / name).write_text(content, encoding="utf-8")
            feed = task_dir / "FEED_DROP"
            feed.mkdir()
            names = set(FEED_FILES) if feed_names is None else feed_names
            for name in names:
                (feed / name).write_bytes(BASELINE_CONTENT)
            for relative, content in (extra_files or {}).items():
                target = task_dir / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                if isinstance(content, bytes):
                    target.write_bytes(content)
                else:
                    target.write_text(content, encoding="utf-8")
            return vh.validate(task_dir, mode, l0)

    def status_of(self, report: vh.Report, item_prefix: str) -> vh.CheckResult:
        for check in report.checks:
            if check.item.startswith(item_prefix):
                return check
        self.fail(f"未找到校验项 {item_prefix}\n{report.render()}")

    def base_files(self, *, status: str = "APPROVED") -> dict[str, str]:
        return {
            "TASK_BRIEF.md": make_brief(),
            "00_CONTEXT_MANIFEST.md": make_manifest(),
            "PLAN_v01.md": make_plan(status=status),
        }


class TestLatestVersionSelection(ValidatorTestBase):
    def test_latest_plan_selected_numerically(self) -> None:
        files = self.base_files()
        files["PLAN_v02.md"] = make_plan(version="02")
        files["APPROVAL_RECORD.md"] = make_approval(version="02")

        report = self.run_validate(files, "worker")

        self.assertTrue(report.ok, report.render())
        detail = self.status_of(report, "4. PLAN").detail
        self.assertIn("PLAN_v02.md", detail)
        self.assertIn("共 2 个版本", detail)

    def test_latest_execution_report_selected(self) -> None:
        files = self.base_files()
        files["APPROVAL_RECORD.md"] = make_approval()
        files["EXECUTION_REPORT_A01.md"] = make_exec_report(conclusion="FAIL")
        files["EXECUTION_REPORT_A02.md"] = make_exec_report(
            attempt="02", conclusion="PASS"
        )

        report = self.run_validate(files, "watchdog")

        self.assertTrue(report.ok, report.render())
        self.assertIn(
            "EXECUTION_REPORT_A02.md",
            self.status_of(report, "6. EXECUTION").detail,
        )


class TestContextManifest(ValidatorTestBase):
    def test_manifest_requires_v31_workflow_version(self) -> None:
        files = self.base_files(status="DRAFT")
        files["00_CONTEXT_MANIFEST.md"] = make_manifest(workflow_version="v3.0")

        report = self.run_validate(files, "planner")

        self.assertFalse(report.ok)
        self.assertIn("Workflow Version", report.render())

    def test_valid_round_manifest_and_entities_pass(self) -> None:
        content = b"additional context\n"
        files = self.base_files(status="DRAFT")
        files["00_CONTEXT_MANIFEST.md"] = make_manifest(
            round_count=1,
            round_section=make_round_section(
                1,
                source="src/extra.py",
                staged="L3__src_extra.py",
                content=content,
            ),
        )

        report = self.run_validate(
            files,
            "planner",
            extra_files={
                "NEED_FILES/ROUND_01/L3__src_extra.py": content,
                "NEED_FILES/ROUND_01/ROUND_MANIFEST.md": "# ROUND 01\n",
            },
        )

        self.assertTrue(report.ok, report.render())

    def test_round_manifest_hash_mismatch_fails(self) -> None:
        files = self.base_files(status="DRAFT")
        files["00_CONTEXT_MANIFEST.md"] = make_manifest(
            round_count=1,
            round_section=make_round_section(
                1,
                source="src/extra.py",
                staged="L3__src_extra.py",
                content=b"expected\n",
            ),
        )

        report = self.run_validate(
            files,
            "planner",
            extra_files={
                "NEED_FILES/ROUND_01/L3__src_extra.py": b"different\n",
                "NEED_FILES/ROUND_01/ROUND_MANIFEST.md": "# ROUND 01\n",
            },
        )

        self.assertFalse(report.ok)
        self.assertIn("SHA-256", report.render())

    def test_round_gap_or_missing_round_manifest_fails(self) -> None:
        content = b"additional context\n"
        files = self.base_files(status="DRAFT")
        files["00_CONTEXT_MANIFEST.md"] = make_manifest(
            round_count=1,
            round_section=make_round_section(
                1,
                source="src/extra.py",
                staged="L3__src_extra.py",
                content=content,
            ),
        )

        report = self.run_validate(
            files,
            "planner",
            extra_files={
                "NEED_FILES/ROUND_01/L3__src_extra.py": content,
                "NEED_FILES/ROUND_02/ROUND_MANIFEST.md": "# ROUND 02\n",
            },
        )

        self.assertFalse(report.ok)
        self.assertIn("不一致", report.render())

    def test_round_files_must_remain_flat(self) -> None:
        content = b"additional context\n"
        files = self.base_files(status="DRAFT")
        files["00_CONTEXT_MANIFEST.md"] = make_manifest(
            round_count=1,
            round_section=make_round_section(
                1,
                source="src/extra.py",
                staged="L3__src_extra.py",
                content=content,
            ),
        )

        report = self.run_validate(
            files,
            "planner",
            extra_files={
                "NEED_FILES/ROUND_01/L3__src_extra.py": content,
                "NEED_FILES/ROUND_01/ROUND_MANIFEST.md": "# ROUND 01\n",
                "NEED_FILES/ROUND_01/nested/extra.txt": "nested\n",
            },
        )

        self.assertFalse(report.ok)
        self.assertIn("平铺", report.render())

    def test_valid_manifest_and_feed_pass(self) -> None:
        report = self.run_validate(self.base_files(status="DRAFT"), "planner")

        self.assertTrue(report.ok, report.render())
        self.assertEqual(self.status_of(report, "2. CONTEXT").status, "PASS")

    def test_missing_manifest_fails(self) -> None:
        files = self.base_files(status="DRAFT")
        files.pop("00_CONTEXT_MANIFEST.md")

        report = self.run_validate(files, "planner")

        self.assertFalse(report.ok)
        self.assertEqual(self.status_of(report, "2. CONTEXT").status, "FAIL")

    def test_empty_feed_drop_fails(self) -> None:
        report = self.run_validate(
            self.base_files(status="DRAFT"),
            "planner",
            feed_names=set(),
        )

        self.assertFalse(report.ok)
        self.assertIn("FEED_DROP", report.render())

    def test_missing_mapped_file_fails(self) -> None:
        names = set(FEED_FILES)
        names.remove("L2__MODULE_MAP.md")

        report = self.run_validate(
            self.base_files(status="DRAFT"),
            "planner",
            feed_names=names,
        )

        self.assertFalse(report.ok)
        self.assertEqual(self.status_of(report, "2d.").status, "FAIL")

    def test_baseline_feed_hash_mismatch_fails(self) -> None:
        files = self.base_files(status="DRAFT")
        report = self.run_validate(
            files,
            "planner",
            extra_files={
                "FEED_DROP/L2__MODULE_MAP.md": b"tampered\n",
            },
        )

        self.assertFalse(report.ok)
        self.assertIn("SHA-256", report.render())

    def test_unlisted_extra_feed_file_warns(self) -> None:
        report = self.run_validate(
            self.base_files(status="DRAFT"),
            "planner",
            feed_names=set(FEED_FILES) | {"extra.txt"},
        )

        self.assertTrue(report.ok, report.render())
        self.assertEqual(self.status_of(report, "2e.").status, "WARN")

    def test_manifest_mapping_traversal_fails(self) -> None:
        files = self.base_files(status="DRAFT")
        files["00_CONTEXT_MANIFEST.md"] = make_manifest(
            extra_rows=[("L3__escape.txt", "L3", "../outside.txt", 1)]
        )

        report = self.run_validate(files, "planner")

        self.assertFalse(report.ok)
        self.assertIn("越界", report.render())

    def test_manifest_commit_placeholder_fails_worker(self) -> None:
        files = self.base_files()
        files["00_CONTEXT_MANIFEST.md"] = make_manifest("<当前 commit>")
        files["APPROVAL_RECORD.md"] = make_approval()

        report = self.run_validate(files, "worker")

        self.assertFalse(report.ok)
        self.assertEqual(self.status_of(report, "2a.").status, "FAIL")

    def test_recon_report_uses_context_manifest_section(self) -> None:
        files = self.base_files(status="DRAFT")
        headings = "\n".join(f"## {section}" for section in vh.RECON_SECTIONS)
        files["RECON_REPORT.md"] = f"# RECON\n{headings}\n正文。\n"

        report = self.run_validate(files, "planner")

        self.assertTrue(report.ok, report.render())
        self.assertEqual(self.status_of(report, "3. RECON").status, "PASS")


class TestPlaceholderRejection(ValidatorTestBase):
    def test_template_conclusion_line_rejected(self) -> None:
        files = self.base_files()
        files["APPROVAL_RECORD.md"] = make_approval()
        files["EXECUTION_REPORT_A01.md"] = make_exec_report(
            conclusion="PASS / PASS WITH WARNINGS / FAIL / BLOCKED / NOT RUN"
        )

        report = self.run_validate(files, "watchdog")

        self.assertFalse(report.ok)
        self.assertEqual(self.status_of(report, "6a.").status, "FAIL")

    def test_angle_placeholder_field_rejected(self) -> None:
        files = self.base_files()
        files["APPROVAL_RECORD.md"] = make_approval().replace(
            "Approver: 用户", "Approver: <批准人>"
        )

        report = self.run_validate(files, "worker")

        self.assertFalse(report.ok)
        self.assertEqual(self.status_of(report, "5a.").status, "FAIL")

    def test_scope_list_placeholder_rejected(self) -> None:
        files = self.base_files()
        files["APPROVAL_RECORD.md"] = make_approval().replace(
            "- MODIFY src/app/**",
            "- MODIFY <待填路径>",
        )

        report = self.run_validate(files, "worker")

        self.assertFalse(report.ok)
        self.assertEqual(self.status_of(report, "5a.").status, "FAIL")

    def test_acceptance_option_line_rejected(self) -> None:
        files = self.base_files()
        files["APPROVAL_RECORD.md"] = make_approval()
        files["EXECUTION_REPORT_A01.md"] = make_exec_report()
        files["ACCEPTANCE.md"] = make_acceptance(
            "ACCEPT / ACCEPT WITH FOLLOW-UP / REJECT"
        )

        report = self.run_validate(files, "archive")

        self.assertFalse(report.ok)
        self.assertEqual(self.status_of(report, "7. ACCEPTANCE").status, "FAIL")

    def test_full_value_angle_text_in_business_doc_allowed(self) -> None:
        files = self.base_files()
        files["APPROVAL_RECORD.md"] = make_approval().replace(
            "Conditions: 无", "Conditions: 保留 List<int> 兼容"
        )

        report = self.run_validate(files, "worker")

        self.assertTrue(report.ok, report.render())


class TestCommitAndDecisionForms(ValidatorTestBase):
    def test_non_git_timestamp_passes_planner(self) -> None:
        files = self.base_files(status="DRAFT")
        timestamp = "无 Git 工作区，可恢复副本时间 2026-11-16 14:00"
        files["00_CONTEXT_MANIFEST.md"] = make_manifest(timestamp)
        files["PLAN_v01.md"] = make_plan(status="DRAFT").replace(
            COMMIT_HASH, timestamp
        )

        report = self.run_validate(files, "planner")

        self.assertTrue(report.ok, report.render())

    def test_approval_conditions_forms_accepted(self) -> None:
        for decision in (
            "APPROVED",
            "APPROVED_WITH_CONDITIONS",
            "APPROVED WITH CONDITIONS",
        ):
            files = self.base_files()
            files["APPROVAL_RECORD.md"] = make_approval(decision=decision)
            report = self.run_validate(files, "worker")
            self.assertTrue(report.ok, f"{decision}\n{report.render()}")

    def test_approval_option_separator_rejected(self) -> None:
        files = self.base_files()
        files["APPROVAL_RECORD.md"] = make_approval(
            decision="APPROVED / APPROVED_WITH_CONDITIONS"
        )

        report = self.run_validate(files, "worker")

        self.assertFalse(report.ok)
        self.assertEqual(self.status_of(report, "5. APPROVAL").status, "FAIL")


class TestV31TaskContracts(ValidatorTestBase):
    def test_task_brief_requires_workflow_version(self) -> None:
        files = self.base_files()
        files["TASK_BRIEF.md"] = make_brief().replace(
            "Workflow Version: v3.1\n", ""
        )
        files["APPROVAL_RECORD.md"] = make_approval()

        report = self.run_validate(files, "worker")

        self.assertFalse(report.ok)
        self.assertEqual(self.status_of(report, "1a.").status, "FAIL")

    def test_plan_requires_workflow_version(self) -> None:
        files = self.base_files()
        files["PLAN_v01.md"] = make_plan().replace("Workflow Version: v3.1\n", "")
        files["APPROVAL_RECORD.md"] = make_approval()

        report = self.run_validate(files, "worker")

        self.assertFalse(report.ok)
        self.assertEqual(self.status_of(report, "4d. Workflow Version").status, "FAIL")

    def test_plan_requires_each_ac_class_and_evidence(self) -> None:
        files = self.base_files()
        files["PLAN_v01.md"] = make_plan().replace(
            "| AC-01 | WORKER_AUTOMATABLE | WORKER | 测试通过 | TEST_RESULT+LOG |",
            "| AC-01 |  | WORKER | 测试通过 |  |",
        )
        files["APPROVAL_RECORD.md"] = make_approval()

        report = self.run_validate(files, "worker")

        self.assertFalse(report.ok)
        self.assertIn("AC-01", report.render())

    def test_worker_automatable_rejects_screenshot_primary_evidence(self) -> None:
        files = self.base_files()
        files["PLAN_v01.md"] = make_plan().replace(
            "TEST_RESULT+LOG", "SCREENSHOT"
        )
        files["APPROVAL_RECORD.md"] = make_approval()

        report = self.run_validate(files, "worker")

        self.assertFalse(report.ok)
        self.assertIn("截图", report.render())

    def test_test_plan_must_cover_every_ac(self) -> None:
        files = self.base_files()
        files["PLAN_v01.md"] = make_plan().replace(
            "| AC-01 | python -m unittest | . | exit 0 |",
            "| AC-02 | python -m unittest | . | exit 0 |",
        )
        files["APPROVAL_RECORD.md"] = make_approval()

        report = self.run_validate(files, "worker")

        self.assertFalse(report.ok)
        self.assertIn("Test Plan", report.render())

    def test_gui_worker_executor_requires_matching_authorization(self) -> None:
        files = self.base_files()
        files["PLAN_v01.md"] = make_plan().replace(
            "| AC-01 | WORKER_AUTOMATABLE | WORKER | 测试通过 | TEST_RESULT+LOG |",
            "| AC-01 | UNITY_GUI_REQUIRED | WORKER_COMPUTER_USE | "
            "场景通过 | OBSERVATION |",
        )
        files["APPROVAL_RECORD.md"] = make_approval()

        report = self.run_validate(files, "worker")

        self.assertFalse(report.ok)
        self.assertIn("Computer-Use", report.render())

    def test_complete_computer_use_authorization_allows_gui_worker(self) -> None:
        authorization = (
            "AUTHORIZED: TARGET=Unity Editor; ACTIONS=Run EditMode Tests; "
            "SCOPE=Assets/Tests/**"
        )
        files = self.base_files()
        files["PLAN_v01.md"] = make_plan().replace(
            "| AC-01 | WORKER_AUTOMATABLE | WORKER | 测试通过 | TEST_RESULT+LOG |",
            "| AC-01 | UNITY_GUI_REQUIRED | WORKER_COMPUTER_USE | "
            "场景通过 | OBSERVATION |",
        ).replace("Computer-Use Authorization: NONE", f"Computer-Use Authorization: {authorization}")
        files["APPROVAL_RECORD.md"] = make_approval().replace(
            "Computer-Use Authorization: NONE",
            f"Computer-Use Authorization: {authorization}",
        )

        report = self.run_validate(files, "worker")

        self.assertTrue(report.ok, report.render())

    def test_incomplete_computer_use_authorization_is_rejected(self) -> None:
        files = self.base_files()
        files["PLAN_v01.md"] = make_plan().replace(
            "| AC-01 | WORKER_AUTOMATABLE | WORKER | 测试通过 | TEST_RESULT+LOG |",
            "| AC-01 | UNITY_GUI_REQUIRED | WORKER_COMPUTER_USE | "
            "场景通过 | OBSERVATION |",
        ).replace(
            "Computer-Use Authorization: NONE",
            "Computer-Use Authorization: AUTHORIZED: TARGET=Unity Editor",
        )
        files["APPROVAL_RECORD.md"] = make_approval().replace(
            "Computer-Use Authorization: NONE",
            "Computer-Use Authorization: AUTHORIZED: TARGET=Unity Editor",
        )

        report = self.run_validate(files, "worker")

        self.assertFalse(report.ok)
        self.assertIn("ACTIONS", report.render())

    def test_approval_write_boundaries_must_match_plan(self) -> None:
        files = self.base_files()
        files["APPROVAL_RECORD.md"] = make_approval().replace(
            "- MODIFY src/app/**", "- MODIFY scripts/**"
        )

        report = self.run_validate(files, "worker")

        self.assertFalse(report.ok)
        self.assertIn("写入边界", report.render())

    def test_plan_and_approval_base_commit_must_match(self) -> None:
        files = self.base_files()
        files["PLAN_v01.md"] = make_plan().replace(
            COMMIT_HASH, "f" * 40
        )
        files["APPROVAL_RECORD.md"] = make_approval()

        report = self.run_validate(files, "worker")

        self.assertFalse(report.ok)
        self.assertIn("Base Commit", report.render())

    def test_plan_base_commit_must_match_manifest(self) -> None:
        files = self.base_files(status="DRAFT")
        files["PLAN_v01.md"] = make_plan(status="DRAFT").replace(
            COMMIT_HASH, "f" * 40
        )

        report = self.run_validate(files, "planner")

        self.assertFalse(report.ok)
        self.assertEqual(self.status_of(report, "4j.").status, "FAIL")

    def test_approval_computer_use_authorization_must_match_plan(self) -> None:
        files = self.base_files()
        files["APPROVAL_RECORD.md"] = make_approval().replace(
            "Computer-Use Authorization: NONE",
            "Computer-Use Authorization: AUTHORIZED Unity Editor:open_scene",
        )

        report = self.run_validate(files, "worker")

        self.assertFalse(report.ok)
        self.assertIn("Computer-Use", report.render())


class TestV31EvidenceContracts(ValidatorTestBase):
    def test_execution_report_ac_set_must_match_plan(self) -> None:
        files = self.base_files()
        files["APPROVAL_RECORD.md"] = make_approval()
        files["EXECUTION_REPORT_A01.md"] = make_exec_report().replace(
            "| AC-01 | PASS | TEST_RESULT+LOG | evidence.log |",
            "| AC-02 | PASS | TEST_RESULT+LOG | evidence.log |",
        )

        report = self.run_validate(files, "watchdog")

        self.assertFalse(report.ok)
        self.assertIn("AC-02", report.render())

    def test_computer_use_yes_requires_authorization_and_details(self) -> None:
        files = self.base_files()
        files["APPROVAL_RECORD.md"] = make_approval()
        files["EXECUTION_REPORT_A01.md"] = make_exec_report().replace(
            "Computer-Use Used: NO", "Computer-Use Used: YES"
        )

        report = self.run_validate(files, "watchdog")

        self.assertFalse(report.ok)
        self.assertIn("Computer-Use", report.render())

    def test_execution_report_rejects_unknown_ac_result(self) -> None:
        files = self.base_files()
        files["APPROVAL_RECORD.md"] = make_approval()
        files["EXECUTION_REPORT_A01.md"] = make_exec_report().replace(
            "| AC-01 | PASS |", "| AC-01 | MAYBE |"
        )

        report = self.run_validate(files, "watchdog")

        self.assertFalse(report.ok)
        self.assertIn("MAYBE", report.render())

    def test_acceptance_ac_set_must_match_plan(self) -> None:
        files = self.base_files()
        files["APPROVAL_RECORD.md"] = make_approval()
        files["EXECUTION_REPORT_A01.md"] = make_exec_report()
        files["ACCEPTANCE.md"] = make_acceptance().replace("AC-01", "AC-02")

        report = self.run_validate(files, "archive")

        self.assertFalse(report.ok)
        self.assertIn("AC-02", report.render())

    def test_unjustified_unplanned_change_fails_acceptance(self) -> None:
        files = self.base_files()
        files["APPROVAL_RECORD.md"] = make_approval()
        files["EXECUTION_REPORT_A01.md"] = make_exec_report()
        files["ACCEPTANCE.md"] = make_acceptance().replace(
            "| none | NOT APPLICABLE | 无未计划改动 |",
            "| src/app/extra.py | UNJUSTIFIED | 不属于目标 |",
        )

        report = self.run_validate(files, "archive")

        self.assertFalse(report.ok)
        self.assertIn("UNJUSTIFIED", report.render())

    def test_acceptance_visual_evidence_requires_observation_notes(self) -> None:
        files = self.base_files()
        files["PLAN_v01.md"] = make_plan().replace(
            "| AC-01 | WORKER_AUTOMATABLE | WORKER | 测试通过 | TEST_RESULT+LOG |",
            "| AC-01 | UNITY_GUI_REQUIRED | CEO | 场景通过 | OBSERVATION |",
        )
        files["APPROVAL_RECORD.md"] = make_approval()
        files["EXECUTION_REPORT_A01.md"] = make_exec_report().replace(
            "| AC-01 | PASS | TEST_RESULT+LOG | evidence.log |",
            "| AC-01 | PASS | OBSERVATION | capture.png |",
        ).replace(
            "Conclusion: PASS",
            "Visual Purpose: 验证布局\n"
            "Visual Scenario: 打开场景\n"
            "Visual Expected: HUD 对齐\n"
            "Conclusion: PASS",
        )
        files["ACCEPTANCE.md"] = make_acceptance().replace(
            "| AC-01 | WORKER_AUTOMATABLE | WORKER | 导出可用 | PASS | TEST_RESULT+LOG |",
            "| AC-01 | UNITY_GUI_REQUIRED | CEO | 场景通过 | PASS | OBSERVATION |",
        )

        report = self.run_validate(files, "archive")

        self.assertFalse(report.ok)
        self.assertIn("ACCEPTANCE 视觉", report.render())


class TestCrossFileConsistency(ValidatorTestBase):
    def test_combined_task_id_and_plan_header_accepted(self) -> None:
        files = self.base_files()
        files["APPROVAL_RECORD.md"] = make_approval().replace(
            f"Task ID: {TASK_ID}\nApproved Plan: v01",
            f"Task ID / Approved Plan: {TASK_ID} / v01",
        )

        report = self.run_validate(files, "worker")

        self.assertTrue(report.ok, report.render())

    def test_plan_body_version_mismatch_rejected(self) -> None:
        files = self.base_files()
        files["PLAN_v01.md"] = make_plan(version="02")
        files["APPROVAL_RECORD.md"] = make_approval()

        report = self.run_validate(files, "worker")

        self.assertFalse(report.ok)
        self.assertEqual(self.status_of(report, "4c.").status, "FAIL")

    def test_approval_task_id_mismatch_rejected(self) -> None:
        files = self.base_files()
        files["APPROVAL_RECORD.md"] = make_approval().replace(
            TASK_ID, "GD-2026-9999"
        )

        report = self.run_validate(files, "worker")

        self.assertFalse(report.ok)
        self.assertEqual(self.status_of(report, "5b.").status, "FAIL")

    def test_execution_report_task_id_mismatch_rejected(self) -> None:
        files = self.base_files()
        files["APPROVAL_RECORD.md"] = make_approval()
        files["EXECUTION_REPORT_A01.md"] = make_exec_report(
            task_id="GD-2026-9999"
        )

        report = self.run_validate(files, "watchdog")

        self.assertFalse(report.ok)
        self.assertEqual(self.status_of(report, "6b.").status, "FAIL")

    def test_execution_report_version_mismatch_rejected(self) -> None:
        files = self.base_files()
        files["APPROVAL_RECORD.md"] = make_approval()
        files["EXECUTION_REPORT_A01.md"] = make_exec_report(version="99")

        report = self.run_validate(files, "watchdog")

        self.assertFalse(report.ok)
        self.assertEqual(self.status_of(report, "6c.").status, "FAIL")


class TestL0FastTrack(ValidatorTestBase):
    MINI_BRIEF = make_l0_brief()

    def test_l0_mini_brief_passes_worker(self) -> None:
        report = self.run_validate(
            {"TASK_BRIEF.md": self.MINI_BRIEF},
            "worker",
            l0=True,
            feed_names=set(),
        )

        self.assertTrue(report.ok, report.render())

    def test_l0_missing_brief_fails(self) -> None:
        report = self.run_validate({}, "worker", l0=True, feed_names=set())
        self.assertFalse(report.ok)

    def test_l0_requires_v31_execution_and_evidence_contract(self) -> None:
        brief = (
            "# L0 任务\n"
            "Task Level: L0\n"
            "目标与验收: pytest 全绿\n"
            "文件范围: src/app/interfaces/cli.py\n"
        )
        report = self.run_validate(
            {"TASK_BRIEF.md": brief},
            "worker",
            l0=True,
            feed_names=set(),
        )
        self.assertFalse(report.ok)

    def test_l0_rejects_any_non_l0_plan(self) -> None:
        files = {
            "TASK_BRIEF.md": self.MINI_BRIEF,
            "PLAN_v01.md": make_plan(level="L1", version="01"),
            "PLAN_v02.md": make_plan(level="L0", version="02"),
        }
        report = self.run_validate(files, "worker", l0=True, feed_names=set())

        self.assertFalse(report.ok)
        self.assertEqual(self.status_of(report, "4d.").status, "FAIL")
        self.assertIn("PLAN_v01.md", self.status_of(report, "4d.").detail)

    def test_l0_accepts_only_l0_plans(self) -> None:
        files = {
            "TASK_BRIEF.md": self.MINI_BRIEF,
            "PLAN_v01.md": make_plan(level="L0", version="01"),
            "PLAN_v02.md": make_plan(level="L0", version="02"),
        }
        report = self.run_validate(files, "worker", l0=True, feed_names=set())
        self.assertTrue(report.ok, report.render())

    def test_l0_watchdog_requires_execution_report(self) -> None:
        files = {"TASK_BRIEF.md": self.MINI_BRIEF}
        report = self.run_validate(files, "watchdog", l0=True, feed_names=set())
        self.assertFalse(report.ok)
        self.assertEqual(self.status_of(report, "6. EXECUTION").status, "FAIL")

        files["EXECUTION_REPORT_A01.md"] = make_exec_report()
        report = self.run_validate(files, "watchdog", l0=True, feed_names=set())
        self.assertTrue(report.ok, report.render())

    def test_l0_archive_requires_acceptance(self) -> None:
        files = {
            "TASK_BRIEF.md": self.MINI_BRIEF,
            "EXECUTION_REPORT_A01.md": make_exec_report(),
        }
        report = self.run_validate(files, "archive", l0=True, feed_names=set())
        self.assertFalse(report.ok)

        files["ACCEPTANCE.md"] = make_acceptance()
        report = self.run_validate(files, "archive", l0=True, feed_names=set())
        self.assertTrue(report.ok, report.render())


class TestCliContract(unittest.TestCase):
    def test_json_outer_structure(self) -> None:
        files = {
            "TASK_BRIEF.md": make_brief(),
            "00_CONTEXT_MANIFEST.md": make_manifest(),
            "PLAN_v01.md": make_plan(status="DRAFT"),
        }
        with tempfile.TemporaryDirectory() as tmp:
            task_dir = Path(tmp) / TASK_ID
            task_dir.mkdir()
            for name, content in files.items():
                (task_dir / name).write_text(content, encoding="utf-8")
            feed = task_dir / "FEED_DROP"
            feed.mkdir()
            for name in FEED_FILES:
                (feed / name).write_bytes(BASELINE_CONTENT)
            payload = json.loads(vh.validate(task_dir, "planner").to_json())

        self.assertEqual(
            set(payload),
            {"task_dir", "mode", "l0", "ok", "checks"},
        )
        for check in payload["checks"]:
            self.assertEqual(set(check), {"item", "status", "detail"})

    def test_list_supports_v3_modes(self) -> None:
        for mode in ("planner", "worker", "watchdog", "archive"):
            self.assertEqual(vh.main(["--list", "--for", mode]), 0)

    def test_old_mode_is_rejected_with_migration_hint(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(_ROOT / "scripts" / "validate_handover.py"),
                "--list",
                "--for",
                "exec" + "utor",
            ],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        message = result.stderr + result.stdout
        self.assertIn("worker", message)
        self.assertIn("v3", message.lower())

    def test_missing_directory_exit_code_is_one(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "GD-9999-0000"
            self.assertEqual(vh.main([str(missing), "--for", "worker"]), 1)


class TestAutomaticDiffAudit(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.project = Path(self._temp.name) / "project"
        self.task_dir = self.project / "AI_Context" / "TASKS" / TASK_ID
        self.project.mkdir(parents=True)
        for name, content in {
            "AI_Context/PROJECT_OVERVIEW.md": "# Overview\n",
            "AI_Context/CODING_STANDARDS.md": "# Standards\n",
            "AI_Context/BUILD_AND_TEST.md": "# Build\n",
            "AI_Context/PROJECT_BOARD.md": "# Board\n",
            "AI_Context/ARCHITECTURE.md": "# Architecture\n",
            "AI_Context/MODULE_MAP.md": "# Modules\n",
            "AI_Context/DEPENDENCIES.md": "# Dependencies\n",
            "src/app/feature.py": "VALUE = 1\n",
            "pyproject.toml": "[project]\nname = 'demo'\n",
            "README.md": "# Demo\n",
        }.items():
            path = self.project / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

        self._git("init", "-b", "main")
        self._git("config", "user.name", "Temp CEO")
        self._git("config", "user.email", "temp-ceo@example.invalid")
        self._git("add", "-A")
        self._git("commit", "-m", "baseline")
        self.base_commit = self._git("rev-parse", "HEAD").stdout.strip()
        self._write_task_documents()

    def tearDown(self) -> None:
        self._temp.cleanup()

    def _git(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=self.project,
            text=True,
            capture_output=True,
            check=False,
        )

    def _write(self, relative: str, content: str) -> Path:
        path = self.project / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def _write_task_documents(self) -> None:
        self.task_dir.mkdir(parents=True)
        (self.task_dir / "TASK_BRIEF.md").write_text(make_brief(), encoding="utf-8")
        (self.task_dir / "00_CONTEXT_MANIFEST.md").write_text(
            make_manifest(commit=self.base_commit), encoding="utf-8"
        )
        (self.task_dir / "PLAN_v01.md").write_text(
            make_plan().replace(COMMIT_HASH, self.base_commit),
            encoding="utf-8",
        )
        (self.task_dir / "APPROVAL_RECORD.md").write_text(
            make_approval().replace(COMMIT_HASH, self.base_commit),
            encoding="utf-8",
        )
        (self.task_dir / "EXECUTION_REPORT_A01.md").write_text(
            make_exec_report(), encoding="utf-8"
        )
        (self.task_dir / "ACCEPTANCE.md").write_text(
            make_acceptance(), encoding="utf-8"
        )
        feed = self.task_dir / "FEED_DROP"
        feed.mkdir()
        for name in FEED_FILES:
            (feed / name).write_bytes(BASELINE_CONTENT)

    def test_allowed_unplanned_changes_are_reported_as_warning(self) -> None:
        self._write("src/app/feature.py", "VALUE = 2\n")
        self._write("tests/test_feature.py", "def test_feature(): pass\n")

        report = vh.validate(self.task_dir, "watchdog")

        self.assertTrue(report.ok, report.render())
        scope = next(check for check in report.checks if check.item == "8. Git Diff Scope")
        self.assertEqual(scope.status, "WARN")
        self.assertIn("src/app/feature.py", scope.detail)
        self.assertIn("tests/test_feature.py", scope.detail)

    def test_forbidden_change_fails_automatic_scope_audit(self) -> None:
        self._write("pyproject.toml", "[project]\nname = 'changed'\n")

        report = vh.validate(self.task_dir, "watchdog")

        self.assertFalse(report.ok)
        self.assertIn("pyproject.toml", report.render())

    def test_basename_forbidden_pattern_matches_nested_asset(self) -> None:
        plan_path = self.task_dir / "PLAN_v01.md"
        plan = plan_path.read_text(encoding="utf-8").replace(
            "- `pyproject.toml`",
            "- `pyproject.toml`\n- `*.prefab`",
        )
        plan_path.write_text(plan, encoding="utf-8")
        approval_path = self.task_dir / "APPROVAL_RECORD.md"
        approval = approval_path.read_text(encoding="utf-8").replace(
            "- pyproject.toml",
            "- pyproject.toml\n- *.prefab",
        )
        approval_path.write_text(approval, encoding="utf-8")
        self._write("Assets/Art/icon.prefab", "serialized asset\n")

        report = vh.validate(self.task_dir, "watchdog")

        self.assertFalse(report.ok)
        self.assertIn("FORBIDDEN Assets/Art/icon.prefab", report.render())

    def test_change_outside_write_boundary_fails(self) -> None:
        self._write("README.md", "# Changed\n")

        report = vh.validate(self.task_dir, "watchdog")

        self.assertFalse(report.ok)
        self.assertIn("README.md", report.render())

    def test_workflow_artifacts_are_excluded_from_business_scope(self) -> None:
        report = vh.validate(self.task_dir, "watchdog")

        scope = next(check for check in report.checks if check.item == "8. Git Diff Scope")
        self.assertEqual(scope.status, "PASS", scope.detail)

    def test_planned_change_inside_boundary_passes_without_warning(self) -> None:
        self._write("src/app/feature.py", "VALUE = 4\n")
        report_path = self.task_dir / "EXECUTION_REPORT_A01.md"
        report_text = report_path.read_text(encoding="utf-8").replace(
            "## 1. Preflight\n",
            "## 1. Preflight\nPlanned Writes:\n- MODIFY `src/app/feature.py`\n",
        )
        report_path.write_text(report_text, encoding="utf-8")

        report = vh.validate(self.task_dir, "watchdog")

        scope = next(check for check in report.checks if check.item == "8. Git Diff Scope")
        self.assertEqual(scope.status, "PASS", scope.detail)

    def test_delete_requires_delete_write_boundary(self) -> None:
        (self.project / "src" / "app" / "feature.py").unlink()

        report = vh.validate(self.task_dir, "watchdog")

        self.assertFalse(report.ok)
        self.assertIn("DELETE src/app/feature.py", report.render())

    def test_rename_requires_delete_and_create_boundaries(self) -> None:
        plan_path = self.task_dir / "PLAN_v01.md"
        plan = plan_path.read_text(encoding="utf-8").replace(
            "- CREATE `tests/**`",
            "- CREATE `tests/**`\n"
            "- DELETE `src/app/feature.py`\n"
            "- CREATE `src/app/renamed.py`",
        )
        plan_path.write_text(plan, encoding="utf-8")
        approval_path = self.task_dir / "APPROVAL_RECORD.md"
        approval = approval_path.read_text(encoding="utf-8").replace(
            "- CREATE tests/**",
            "- CREATE tests/**\n"
            "- DELETE src/app/feature.py\n"
            "- CREATE src/app/renamed.py",
        )
        approval_path.write_text(approval, encoding="utf-8")
        (self.project / "src" / "app" / "feature.py").rename(
            self.project / "src" / "app" / "renamed.py"
        )

        report = vh.validate(self.task_dir, "watchdog")

        scope = next(check for check in report.checks if check.item == "8. Git Diff Scope")
        self.assertEqual(scope.status, "WARN", scope.detail)
        self.assertIn("src/app/renamed.py", scope.detail)

    def test_mismatched_manifest_and_approval_base_fails(self) -> None:
        manifest_path = self.task_dir / "00_CONTEXT_MANIFEST.md"
        manifest = manifest_path.read_text(encoding="utf-8").replace(
            self.base_commit, "f" * 40
        )
        manifest_path.write_text(manifest, encoding="utf-8")

        report = vh.validate(self.task_dir, "watchdog")

        self.assertFalse(report.ok)
        self.assertIn("Base Commit", report.render())

    def test_archive_requires_justification_for_unplanned_allowed_path(self) -> None:
        self._write("src/app/feature.py", "VALUE = 3\n")

        report = vh.validate(self.task_dir, "archive")

        self.assertFalse(report.ok)
        self.assertIn("src/app/feature.py", report.render())


if __name__ == "__main__":
    unittest.main()
