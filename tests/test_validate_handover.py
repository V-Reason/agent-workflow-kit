"""Regression tests for the v3.0 handover validator."""

from __future__ import annotations

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
PLAN_HEADINGS = "\n".join(f"## {section}" for section in vh.PLAN_SECTIONS)
EXEC_HEADINGS = "\n".join(f"## {section}" for section in vh.EXEC_REPORT_SECTIONS)

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
    return (
        f"# PLAN v{version}\n"
        f"- Task ID: {TASK_ID}\n"
        f"- Plan Version: v{version}\n"
        f"- Status: {status}\n"
        f"- Task Level: {level} / Risk Level: R1\n\n"
        f"{PLAN_HEADINGS}\n\n正文略。\n"
    )


def make_brief() -> str:
    return "\n".join(
        [
            "# TASK BRIEF",
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
    extra_rows: list[tuple[str, str, str, int]] | None = None,
) -> str:
    rows = [
        (staged, layer_from_name(staged), source, 1)
        for staged, source in FEED_FILES.items()
    ]
    rows.extend(extra_rows or [])
    table = "\n".join(
        f"| `{staged}` | {layer} | `{source}` | {tokens} |"
        for staged, layer, source, tokens in rows
    )
    return (
        f"# 00 CONTEXT MANIFEST — {TASK_ID}\n\n"
        f"- Task ID: {TASK_ID}\n"
        f"- Base Commit: {commit}\n"
        "- Generated At: 2026-11-16T12:00:00+08:00\n\n"
        "| 暂存名 | 层级 | 原路径 | 估算 Token |\n"
        "| --- | --- | --- | ---: |\n"
        f"{table}\n"
    )


def make_approval(version: str = "01", decision: str = "APPROVED") -> str:
    return (
        "# APPROVAL RECORD\n"
        f"Task ID: {TASK_ID}\n"
        f"Approved Plan: v{version}\n"
        f"Decision: {decision}\n"
        "Approved Scope:\n- MODIFY src/app/interfaces/cli.py\n"
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
    return (
        f"# EXECUTION REPORT A{attempt}\n"
        f"Task ID: {task_id} / Plan Version: v{version} / Attempt: A{attempt}\n"
        f"{EXEC_HEADINGS}\n"
        f"Conclusion: {conclusion}\n"
        "所需决策: none\n"
    )


def make_acceptance(decision: str = "ACCEPT") -> str:
    return (
        f"# ACCEPTANCE — {TASK_ID}\n"
        "| AC-01 | 导出可用 | 通过 | 日志 |\n"
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
                (feed / name).write_text("staged\n", encoding="utf-8")
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
            "- MODIFY src/app/interfaces/cli.py",
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
        files["00_CONTEXT_MANIFEST.md"] = make_manifest(
            "无 Git 工作区，可恢复副本时间 2026-11-16 14:00"
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
    MINI_BRIEF = (
        "# L0 任务\n"
        "Task Level: L0\n"
        "目标与验收：导出 CSV，pytest 全绿\n"
        "文件范围：src/app/interfaces/cli.py\n"
        "执行人：Worker\n"
    )

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
                (feed / name).write_text("staged\n", encoding="utf-8")
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


if __name__ == "__main__":
    unittest.main()
