"""tests/test_validate_handover.py — validate_handover.py 回归测试（仅 Python 标准库）

覆盖 KIT-2026-0001 五类修复场景：
1. 多版本文件取最新（PLAN_vNN / EXECUTION_REPORT_Axx）
2. 空白模板占位符拦截（Conclusion / 用户决定 / commit / APPROVAL 字段）
3. 无 Git 副本时间戳放行（含时区与"可恢复副本"字样）
4. APPROVED WITH CONDITIONS 空格与下划线兼容
5. 跨文件版本一致性拦截（文件名 vs 正文 / 批准记录 / 执行报告）
6. --l0 快速通道正反用例
7. --json 既有外层结构与 CLI 参数向后兼容

运行：python -m unittest discover -s tests -v
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_SPEC = importlib.util.spec_from_file_location(
    "validate_handover", _ROOT / "scripts" / "validate_handover.py"
)
vh = importlib.util.module_from_spec(_SPEC)
sys.modules["validate_handover"] = vh  # dataclass 解析自引用类型需要模块已注册
_SPEC.loader.exec_module(vh)

TASK_ID = "GD-2026-0001"
COMMIT_HASH = "b64326037c36ff8dce842d0496d4c0894532ae7c"

PLAN_HEADINGS = "\n".join(f"## {s}" for s in vh.PLAN_SECTIONS)
EXEC_HEADINGS = "\n".join(f"## {s}" for s in vh.EXEC_REPORT_SECTIONS)


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


def make_context_packet(commit: str = COMMIT_HASH) -> str:
    return f"# CONTEXT PACKET v01\n版本: v01\n核验 commit: {commit}\n预算: 合计 <tokens>\n"


def make_approval(version: str = "01", decision: str = "APPROVED") -> str:
    return (
        f"# APPROVAL RECORD\nTask ID / Approved Plan: {TASK_ID} / v{version}\n"
        f"Decision: {decision}\n"
        "Approved Scope:\n- MODIFY src/app/interfaces/cli.py\n"
        f"Conditions: 无\nBranch / Base Commit: main / {COMMIT_HASH}\n"
        "Approver: 用户\nApproval Time: 2026-11-16 12:00 (UTC+8)\n"
    )


def make_exec_report(version: str = "01", attempt: str = "01", conclusion: str = "PASS") -> str:
    return (
        f"# EXECUTION REPORT A{attempt}\nTask ID: {TASK_ID} / Plan Version: v{version} / Attempt: A{attempt}\n"
        f"{EXEC_HEADINGS}\nConclusion: {conclusion}\n所需决策: none\n"
    )


def make_acceptance(decision: str = "ACCEPT") -> str:
    return (
        f"# ACCEPTANCE — {TASK_ID}\n| AC-01 | 导出可用 | 通过 | 日志 |\n"
        f"结论建议: PASS\n用户决定: {decision}\n后续动作: none\n"
    )


class ValidatorTestBase(unittest.TestCase):
    def run_validate(self, files: dict[str, str], mode: str, l0: bool = False) -> vh.Report:
        with tempfile.TemporaryDirectory() as tmp:
            task_dir = Path(tmp) / TASK_ID
            task_dir.mkdir()
            for name, content in files.items():
                (task_dir / name).write_text(content, encoding="utf-8")
            return vh.validate(task_dir, mode, l0)

    def status_of(self, report: vh.Report, item_prefix: str) -> vh.CheckResult:
        for check in report.checks:
            if check.item.startswith(item_prefix):
                return check
        self.fail(f"未找到校验项 {item_prefix}")


class TestLatestVersionSelection(ValidatorTestBase):
    """修复 1：多版本文件按版本号取最新，而非 sorted()[0] 取最旧。"""

    def test_latest_plan_selected(self):
        files = {
            "TASK_BRIEF.md": make_brief(),
            "CONTEXT_PACKET_v01.md": make_context_packet(),
            "PLAN_v01.md": make_plan(status="DRAFT", version="01"),
            "PLAN_v02.md": make_plan(status="APPROVED", version="02"),
            "APPROVAL_RECORD.md": make_approval(version="02"),
        }
        report = self.run_validate(files, "executor")
        self.assertTrue(report.ok, report.render())
        plan_item = self.status_of(report, "4. PLAN")
        self.assertEqual(plan_item.status, "PASS")
        self.assertIn("PLAN_v02.md", plan_item.detail)
        self.assertIn("共 2 个版本", plan_item.detail)

    def test_latest_exec_report_selected(self):
        files = {
            "TASK_BRIEF.md": make_brief(),
            "CONTEXT_PACKET_v01.md": make_context_packet(),
            "PLAN_v01.md": make_plan(version="01"),
            "APPROVAL_RECORD.md": make_approval(version="01"),
            "EXECUTION_REPORT_A01.md": make_exec_report(conclusion="FAIL"),
            "EXECUTION_REPORT_A02.md": make_exec_report(attempt="02", conclusion="PASS"),
        }
        report = self.run_validate(files, "verifier")
        exec_item = self.status_of(report, "6. EXECUTION")
        self.assertEqual(exec_item.status, "PASS")
        self.assertIn("EXECUTION_REPORT_A02.md", exec_item.detail)
        conclusion_item = self.status_of(report, "6a.")
        self.assertEqual(conclusion_item.status, "PASS")
        self.assertEqual(conclusion_item.detail, "Conclusion: PASS")


class TestPlaceholderRejection(ValidatorTestBase):
    """修复 2：空白模板行（含 / 选项分隔）必须判 FAIL，不得误放行。"""

    def test_template_conclusion_line_rejected(self):
        files = {
            "TASK_BRIEF.md": make_brief(),
            "CONTEXT_PACKET_v01.md": make_context_packet(),
            "PLAN_v01.md": make_plan(version="01"),
            "APPROVAL_RECORD.md": make_approval(version="01"),
            "EXECUTION_REPORT_A01.md": make_exec_report(
                conclusion="PASS / PASS WITH WARNINGS / FAIL / BLOCKED / NOT RUN"
            ),
        }
        report = self.run_validate(files, "verifier")
        self.assertFalse(report.ok)
        self.assertEqual(self.status_of(report, "6a.").status, "FAIL")

    def test_angle_placeholder_conclusion_rejected(self):
        files = {
            "TASK_BRIEF.md": make_brief(),
            "CONTEXT_PACKET_v01.md": make_context_packet(),
            "PLAN_v01.md": make_plan(version="01"),
            "APPROVAL_RECORD.md": make_approval(version="01"),
            "EXECUTION_REPORT_A01.md": make_exec_report(conclusion="<填写结论>"),
        }
        report = self.run_validate(files, "verifier")
        self.assertFalse(report.ok)
        self.assertEqual(self.status_of(report, "6a.").status, "FAIL")

    def test_bold_conclusion_accepted(self):
        content = make_exec_report().replace("Conclusion: PASS", "**Conclusion**: PASS")
        files = {
            "TASK_BRIEF.md": make_brief(),
            "CONTEXT_PACKET_v01.md": make_context_packet(),
            "PLAN_v01.md": make_plan(version="01"),
            "APPROVAL_RECORD.md": make_approval(version="01"),
            "EXECUTION_REPORT_A01.md": content,
        }
        report = self.run_validate(files, "verifier")
        self.assertEqual(self.status_of(report, "6a.").status, "PASS")

    def test_template_acceptance_line_rejected(self):
        files = {
            "TASK_BRIEF.md": make_brief(),
            "CONTEXT_PACKET_v01.md": make_context_packet(),
            "PLAN_v01.md": make_plan(version="01"),
            "APPROVAL_RECORD.md": make_approval(version="01"),
            "EXECUTION_REPORT_A01.md": make_exec_report(),
            "ACCEPTANCE.md": make_acceptance("ACCEPT / ACCEPT WITH FOLLOW-UP / REJECT"),
        }
        report = self.run_validate(files, "archive")
        self.assertFalse(report.ok)
        self.assertEqual(self.status_of(report, "7. ACCEPTANCE").status, "FAIL")

    def test_acceptance_enum_forms_accepted(self):
        for decision in ("ACCEPT", "ACCEPT WITH FOLLOW-UP", "REJECT"):
            files = {
                "TASK_BRIEF.md": make_brief(),
                "CONTEXT_PACKET_v01.md": make_context_packet(),
                "PLAN_v01.md": make_plan(version="01"),
                "APPROVAL_RECORD.md": make_approval(version="01"),
                "EXECUTION_REPORT_A01.md": make_exec_report(),
                "ACCEPTANCE.md": make_acceptance(decision),
            }
            report = self.run_validate(files, "archive")
            self.assertTrue(report.ok, f"{decision}: {report.render()}")
            self.assertEqual(
                self.status_of(report, "7. ACCEPTANCE").detail, f"决定：{decision}"
            )

    def test_commit_placeholder_warn_in_planner_fail_in_executor(self):
        for commit in ("<当前 commit>", "待填写", "TBD"):
            files = {
                "TASK_BRIEF.md": make_brief(),
                "CONTEXT_PACKET_v01.md": make_context_packet(commit),
                "PLAN_v01.md": make_plan(status="DRAFT", version="01"),
            }
            planner_report = self.run_validate(files, "planner")
            self.assertEqual(
                self.status_of(planner_report, "2. CONTEXT").status, "WARN", commit
            )
            self.assertTrue(planner_report.ok, commit)

            files["PLAN_v01.md"] = make_plan(version="01")
            files["APPROVAL_RECORD.md"] = make_approval(version="01")
            executor_report = self.run_validate(files, "executor")
            self.assertFalse(executor_report.ok, commit)
            self.assertEqual(
                self.status_of(executor_report, "2. CONTEXT").status, "FAIL", commit
            )

    def test_approval_placeholder_field_rejected(self):
        approval = make_approval().replace("Approver: 用户", "Approver: <批准人>")
        files = {
            "TASK_BRIEF.md": make_brief(),
            "CONTEXT_PACKET_v01.md": make_context_packet(),
            "PLAN_v01.md": make_plan(version="01"),
            "APPROVAL_RECORD.md": approval,
        }
        report = self.run_validate(files, "executor")
        self.assertFalse(report.ok)
        field_item = self.status_of(report, "5a.")
        self.assertEqual(field_item.status, "FAIL")
        self.assertIn("Approver", field_item.detail)


class TestCommitTimestampForms(ValidatorTestBase):
    """修复 2c：无 Git 副本时间戳（含时区 / 可恢复副本字样）放行。"""

    CASES = [
        COMMIT_HASH,
        "abc1234",
        "2026-11-16 14:00",
        "2026-11-16T14:00",
        "2026-11-16 14:00 (UTC+8)",
        "2026-11-16T14:00+08:00",
        "2026-11-16 14:00:35",
        "无 Git 工作区，可恢复副本时间 2026-11-16 14:00",
    ]

    def test_legal_commit_values_pass_planner(self):
        for commit in self.CASES:
            files = {
                "TASK_BRIEF.md": make_brief(),
                "CONTEXT_PACKET_v01.md": make_context_packet(commit),
                "PLAN_v01.md": make_plan(status="DRAFT", version="01"),
            }
            report = self.run_validate(files, "planner")
            self.assertEqual(
                self.status_of(report, "2. CONTEXT").status, "PASS", commit
            )


class TestApprovalDecisionForms(ValidatorTestBase):
    """修复 2d：批准决定空格/下划线兼容，选项分隔拦截。"""

    def run_approval(self, decision: str) -> vh.Report:
        files = {
            "TASK_BRIEF.md": make_brief(),
            "CONTEXT_PACKET_v01.md": make_context_packet(),
            "PLAN_v01.md": make_plan(version="01"),
            "APPROVAL_RECORD.md": make_approval(decision=decision),
        }
        return self.run_validate(files, "executor")

    def test_approved_forms_accepted(self):
        for decision in ("APPROVED", "APPROVED_WITH_CONDITIONS", "APPROVED WITH CONDITIONS"):
            report = self.run_approval(decision)
            self.assertEqual(
                self.status_of(report, "5. APPROVAL").status, "PASS", decision
            )

    def test_option_separator_rejected(self):
        for decision in ("APPROVED / APPROVED_WITH_CONDITIONS", "APPROVED 或 REJECTED"):
            report = self.run_approval(decision)
            self.assertFalse(report.ok, decision)
            self.assertEqual(
                self.status_of(report, "5. APPROVAL").status, "FAIL", decision
            )


class TestVersionConsistency(ValidatorTestBase):
    """修复 3：文件名版本、正文 Plan Version、批准记录、执行报告交叉一致。"""

    def base_files(self) -> dict[str, str]:
        return {
            "TASK_BRIEF.md": make_brief(),
            "CONTEXT_PACKET_v01.md": make_context_packet(),
            "PLAN_v01.md": make_plan(version="01"),
            "APPROVAL_RECORD.md": make_approval(version="01"),
        }

    def test_plan_filename_body_mismatch_rejected(self):
        files = self.base_files()
        files["PLAN_v01.md"] = make_plan(version="02")
        report = self.run_validate(files, "executor")
        self.assertFalse(report.ok)
        self.assertEqual(self.status_of(report, "4c.").status, "FAIL")

    def test_plan_missing_version_field_rejected(self):
        files = self.base_files()
        files["PLAN_v01.md"] = make_plan(version="01").replace(
            "- Plan Version: v01\n", ""
        )
        report = self.run_validate(files, "executor")
        self.assertFalse(report.ok)
        self.assertEqual(self.status_of(report, "4c.").status, "FAIL")

    def test_approval_missing_version_reference_rejected(self):
        files = self.base_files()
        files["APPROVAL_RECORD.md"] = make_approval(version="01").replace(
            f"{TASK_ID} / v01", f"{TASK_ID} / vNN"
        )
        report = self.run_validate(files, "executor")
        self.assertFalse(report.ok)
        self.assertEqual(self.status_of(report, "5b.").status, "FAIL")

    def test_exec_report_missing_version_reference_rejected(self):
        files = self.base_files()
        files["EXECUTION_REPORT_A01.md"] = make_exec_report(version="NN")
        report = self.run_validate(files, "verifier")
        self.assertFalse(report.ok)
        self.assertEqual(self.status_of(report, "6c.").status, "FAIL")

    def test_consistent_versions_pass(self):
        files = self.base_files()
        files["EXECUTION_REPORT_A01.md"] = make_exec_report(version="01")
        report = self.run_validate(files, "verifier")
        self.assertTrue(report.ok, report.render())
        self.assertEqual(self.status_of(report, "4c.").status, "PASS")
        self.assertEqual(self.status_of(report, "5b.").status, "PASS")
        self.assertEqual(self.status_of(report, "6c.").status, "PASS")


class TestL0FastTrack(ValidatorTestBase):
    """修复 4：--l0 快速通道正反用例。"""

    MINI_BRIEF = (
        "# L0 任务\nTask Level: L0\n目标与验收：导出 CSV，pytest 全绿\n"
        "文件范围：src/app/interfaces/cli.py\n执行人：Executor\n"
    )

    def test_l0_mini_brief_passes_executor(self):
        files = {"TASK_BRIEF.md": self.MINI_BRIEF}
        report = self.run_validate(files, "executor", l0=True)
        self.assertTrue(report.ok, report.render())
        self.assertEqual(self.status_of(report, "1. TASK_BRIEF").status, "PASS")

    def test_l0_standard_brief_passes(self):
        files = {"TASK_BRIEF.md": make_brief()}
        report = self.run_validate(files, "executor", l0=True)
        self.assertTrue(report.ok, report.render())

    def test_l0_mini_brief_with_placeholder_rejected(self):
        bad = self.MINI_BRIEF.replace("src/app/interfaces/cli.py", "<文件范围待填>")
        files = {"TASK_BRIEF.md": bad}
        report = self.run_validate(files, "executor", l0=True)
        self.assertFalse(report.ok)
        self.assertEqual(self.status_of(report, "1. TASK_BRIEF").status, "FAIL")

    def test_l0_without_brief_rejected(self):
        report = self.run_validate({}, "executor", l0=True)
        self.assertFalse(report.ok)

    def test_l0_rejects_l1_plan(self):
        files = {"TASK_BRIEF.md": self.MINI_BRIEF, "PLAN_v01.md": make_plan(level="L1")}
        report = self.run_validate(files, "executor", l0=True)
        self.assertFalse(report.ok)
        self.assertEqual(self.status_of(report, "4d.").status, "FAIL")

    def test_l0_accepts_l0_plan(self):
        files = {"TASK_BRIEF.md": self.MINI_BRIEF, "PLAN_v01.md": make_plan(level="L0")}
        report = self.run_validate(files, "executor", l0=True)
        self.assertTrue(report.ok, report.render())

    def test_l0_rejects_plan_without_level(self):
        plan = make_plan(level="L0").replace("- Task Level: L0 / Risk Level: R1\n", "")
        files = {"TASK_BRIEF.md": self.MINI_BRIEF, "PLAN_v01.md": plan}
        report = self.run_validate(files, "executor", l0=True)
        self.assertFalse(report.ok)
        self.assertEqual(self.status_of(report, "4d.").status, "FAIL")

    def test_l0_context_packet_placeholder_still_fail_in_executor(self):
        files = {
            "TASK_BRIEF.md": self.MINI_BRIEF,
            "CONTEXT_PACKET_v01.md": make_context_packet("<当前 commit>"),
        }
        report = self.run_validate(files, "executor", l0=True)
        self.assertFalse(report.ok)
        self.assertEqual(self.status_of(report, "2. CONTEXT").status, "FAIL")

    def test_l0_verifier_requires_exec_report(self):
        files = {"TASK_BRIEF.md": self.MINI_BRIEF}
        report = self.run_validate(files, "verifier", l0=True)
        self.assertFalse(report.ok)
        self.assertEqual(self.status_of(report, "6. EXECUTION").status, "FAIL")

        files["EXECUTION_REPORT_A01.md"] = make_exec_report()
        report = self.run_validate(files, "verifier", l0=True)
        self.assertTrue(report.ok, report.render())

    def test_l0_archive_requires_acceptance(self):
        files = {
            "TASK_BRIEF.md": self.MINI_BRIEF,
            "EXECUTION_REPORT_A01.md": make_exec_report(),
        }
        report = self.run_validate(files, "archive", l0=True)
        self.assertFalse(report.ok)
        self.assertEqual(self.status_of(report, "7. ACCEPTANCE").status, "FAIL")

        files["ACCEPTANCE.md"] = make_acceptance()
        report = self.run_validate(files, "archive", l0=True)
        self.assertTrue(report.ok, report.render())

    def test_normal_mode_still_requires_full_package(self):
        files = {"TASK_BRIEF.md": self.MINI_BRIEF}
        report = self.run_validate(files, "executor", l0=False)
        self.assertFalse(report.ok)


class TestBackwardCompat(ValidatorTestBase):
    """约束 2：--json 外层结构与既有 CLI 参数向后兼容。"""

    def test_json_outer_structure_unchanged(self):
        files = {
            "TASK_BRIEF.md": make_brief(),
            "CONTEXT_PACKET_v01.md": make_context_packet(),
            "PLAN_v01.md": make_plan(version="01"),
            "APPROVAL_RECORD.md": make_approval(version="01"),
        }
        report = self.run_validate(files, "executor")
        payload = json.loads(report.to_json())
        self.assertEqual(
            set(payload.keys()) - {"l0"}, {"task_dir", "mode", "ok", "checks"}
        )
        self.assertEqual(payload["mode"], "executor")
        self.assertIsInstance(payload["ok"], bool)
        for check in payload["checks"]:
            self.assertEqual(set(check.keys()), {"item", "status", "detail"})

    def test_cli_list_and_flags_still_work(self):
        self.assertEqual(vh.main(["--list", "--for", "executor"]), 0)
        self.assertEqual(vh.main(["--list", "--for", "archive", "--l0"]), 0)
        self.assertEqual(vh.main(["--list", "--for", "planner", "--json"]), 0)

    def test_missing_dir_exit_code_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "GD-9999-0000"
            self.assertEqual(vh.main([str(missing), "--for", "executor"]), 1)


if __name__ == "__main__":
    unittest.main()
