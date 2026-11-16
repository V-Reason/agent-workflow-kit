"""End-to-end rehearsal in the system temporary directory."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_TEMPLATE = _ROOT / "templates" / "software-py"
_TASK_ID = "GD-2026-0001"

PLAN_HEADINGS = [
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
EXEC_HEADINGS = [
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


def _run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _brief() -> str:
    return "\n".join(
        [
            "# TASK BRIEF",
            "1. Objective: 验证 FEED_DROP 集成",
            "2. Background: 临时演练",
            "3. Current Behavior: 无",
            "4. Expected Behavior: 门禁通过",
            "5. Non-goals: 不修改业务逻辑",
            "6. 已知约束: Python 3.12+",
            "7. 相关模块与文件: src/app/domain/models.py",
            "8. 已观察到的错误: 无",
            "9. 验收方式: validate_handover 全模式通过",
            "10. 其他说明: 无",
        ]
    )


def _plan(status: str) -> str:
    headings = "\n".join(f"## {heading}" for heading in PLAN_HEADINGS)
    return (
        f"# PLAN v01\nTask ID: {_TASK_ID}\nPlan Version: v01\n"
        f"Status: {status}\nTask Level: L1 / Risk Level: R1\n"
        f"{headings}\n"
    )


def _approval() -> str:
    commit = "b64326037c36ff8dce842d0496d4c0894532ae7c"
    return (
        "# APPROVAL RECORD\n"
        f"Task ID / Approved Plan: {_TASK_ID} / v01\n"
        "Decision: APPROVED\n"
        "Approved Scope:\n- MODIFY src/app/domain/models.py\n"
        "Conditions: 无\n"
        f"Branch / Base Commit: main / {commit}\n"
        "Approver: CEO\n"
        "Approval Time: 2026-11-16 19:00 (UTC+8)\n"
    )


def _execution_report(task_id: str = _TASK_ID) -> str:
    headings = "\n".join(f"## {heading}" for heading in EXEC_HEADINGS)
    return (
        "# EXECUTION REPORT A01\n"
        f"Task ID: {task_id} / Plan Version: v01 / Attempt: A01\n"
        f"{headings}\n"
        "Conclusion: PASS\n"
    )


def _acceptance() -> str:
    return (
        f"# ACCEPTANCE — {_TASK_ID}\n"
        "| AC-01 | 临时演练 | 通过 | 命令 exit 0 |\n"
        "Watchdog 结论建议: PASS\n"
        "用户决定: ACCEPT\n"
    )


class TemplateIntegrationTests(unittest.TestCase):
    def test_python_template_full_and_l0_handover_rehearsal(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "software-py"
            shutil.copytree(
                _TEMPLATE,
                project,
                ignore=shutil.ignore_patterns(
                    ".venv",
                    "__pycache__",
                    ".pytest_cache",
                    ".mypy_cache",
                    ".ruff_cache",
                ),
            )
            self.assertEqual(_run(["git", "init", "-b", "main"], project).returncode, 0)
            _run(["git", "config", "user.name", "Temp CEO"], project)
            _run(["git", "config", "user.email", "temp-ceo@example.invalid"], project)
            self.assertEqual(_run(["git", "add", "-A"], project).returncode, 0)
            self.assertEqual(
                _run(["git", "commit", "-m", "test: template baseline"], project).returncode,
                0,
            )

            task = project / "AI_Context" / "TASKS" / _TASK_ID
            stage = _run(
                [
                    sys.executable,
                    "scripts/stage_context.py",
                    str(task),
                    "--files",
                    "src/app/domain/models.py",
                    "--json",
                ],
                project,
            )
            self.assertEqual(stage.returncode, 0, stage.stderr)
            self.assertTrue((task / "FEED_DROP" / "L3__src_app_domain_models.py").is_file())

            status = _run(["git", "status", "--short"], project)
            self.assertEqual(status.returncode, 0)
            self.assertNotIn("FEED_DROP", status.stdout)

            _write(task / "TASK_BRIEF.md", _brief())
            _write(task / "PLAN_v01.md", _plan("DRAFT"))
            planner = _run(
                [
                    sys.executable,
                    "scripts/validate_handover.py",
                    str(task),
                    "--for",
                    "planner",
                ],
                project,
            )
            self.assertEqual(planner.returncode, 0, planner.stdout + planner.stderr)

            _write(task / "PLAN_v01.md", _plan("APPROVED"))
            _write(task / "APPROVAL_RECORD.md", _approval())
            worker = _run(
                [
                    sys.executable,
                    "scripts/validate_handover.py",
                    str(task),
                    "--for",
                    "worker",
                ],
                project,
            )
            self.assertEqual(worker.returncode, 0, worker.stdout + worker.stderr)

            _write(task / "EXECUTION_REPORT_A01.md", _execution_report())
            watchdog = _run(
                [
                    sys.executable,
                    "scripts/validate_handover.py",
                    str(task),
                    "--for",
                    "watchdog",
                ],
                project,
            )
            self.assertEqual(watchdog.returncode, 0, watchdog.stdout + watchdog.stderr)

            _write(task / "ACCEPTANCE.md", _acceptance())
            archive = _run(
                [
                    sys.executable,
                    "scripts/validate_handover.py",
                    str(task),
                    "--for",
                    "archive",
                ],
                project,
            )
            self.assertEqual(archive.returncode, 0, archive.stdout + archive.stderr)

            l0_task = project / "AI_Context" / "TASKS" / "GD-2026-0009"
            _write(
                l0_task / "TASK_BRIEF.md",
                "# L0\nTask Level: L0\n"
                "目标与验收: 局部修复 exit 0\n"
                "文件范围: MODIFY src/app/domain/models.py\n",
            )
            _write(
                l0_task / "EXECUTION_REPORT_A01.md",
                _execution_report("GD-2026-0009"),
            )
            _write(l0_task / "ACCEPTANCE.md", _acceptance().replace(_TASK_ID, "GD-2026-0009"))
            l0_archive = _run(
                [
                    sys.executable,
                    "scripts/validate_handover.py",
                    str(l0_task),
                    "--l0",
                    "--for",
                    "archive",
                ],
                project,
            )
            self.assertEqual(l0_archive.returncode, 0, l0_archive.stdout + l0_archive.stderr)


if __name__ == "__main__":
    unittest.main()
