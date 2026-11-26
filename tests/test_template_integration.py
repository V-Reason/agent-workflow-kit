"""End-to-end rehearsal in the system temporary directory."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
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
    environment = os.environ.copy()
    environment["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        encoding="utf-8",
        capture_output=True,
        env=environment,
        check=False,
    )


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _profile_identity(project: Path) -> tuple[str, str]:
    lock = tomllib.loads(
        (project / "AI_Context" / "WORKFLOW_LOCK.toml").read_text(encoding="utf-8")
    )
    return " + ".join(lock["layer_versions"]), lock["profile_hash"]


def _brief(project: Path) -> str:
    profile, profile_hash = _profile_identity(project)
    return "\n".join(
        [
            "# TASK BRIEF",
            "Workflow Version: v4.0",
            f"Project Profile: {profile}",
            f"Profile Hash: {profile_hash}",
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


def _plan(status: str, base_commit: str, project: Path) -> str:
    profile, profile_hash = _profile_identity(project)
    lines = [
        "# PLAN v01",
        f"Task ID: {_TASK_ID}",
        "Plan Version: v01",
        "Workflow Version: v4.0",
        f"Project Profile: {profile}",
        f"Profile Hash: {profile_hash}",
        f"Status: {status}",
        "Task Level: L1 / Risk Level: R1",
        f"Branch / Base Commit: main / {base_commit}",
        "Computer-Use Authorization: NONE",
        "",
    ]
    for heading in PLAN_HEADINGS:
        lines.extend([f"## {heading}", ""])
        if heading == "6. File Scope":
            lines.extend(
                [
                    "### Write Boundaries",
                    "- MODIFY `src/app/**`",
                    "### Forbidden",
                    "- `pyproject.toml`",
                    "### Read Policy",
                    "- REPO_READ_ONLY_EXCEPT_SENSITIVE",
                    "### Protected Changes",
                    "- 依赖、配置、公共接口与序列化变更必须升版",
                    "",
                ]
            )
        elif heading == "9. Acceptance Criteria":
            lines.extend(
                [
                    "| AC | Class | Executor | Criterion | Primary Evidence |",
                    "| --- | --- | --- | --- | --- |",
                    "| AC-01 | WORKER_AUTOMATABLE | WORKER | 交接通过 | TEST_RESULT+LOG |",
                    "",
                ]
            )
        elif heading == "10. Test Plan":
            lines.extend(
                [
                    "| AC | Command / Action | CWD | Expected |",
                    "| --- | --- | --- | --- |",
                    "| AC-01 | python -m unittest | . | exit 0 |",
                    "",
                ]
            )
    return "\n".join(lines) + "\n"


def _approval(commit: str) -> str:
    return (
        "# APPROVAL RECORD\n"
        f"Task ID / Approved Plan: {_TASK_ID} / v01\n"
        "Workflow Version: v4.0\n"
        "Decision: APPROVED\n"
        "Approved Write Boundaries:\n"
        "- MODIFY src/app/**\n"
        "Explicitly Forbidden:\n"
        "- pyproject.toml\n"
        "Computer-Use Authorization: NONE\n"
        "Conditions: 无\n"
        f"Branch / Base Commit: main / {commit}\n"
        "Approver: CEO\n"
        "Approval Time: 2026-11-16 19:00 (UTC+8)\n"
    )


def _execution_report(task_id: str = _TASK_ID) -> str:
    lines = [
        "# EXECUTION REPORT A01",
        f"Task ID: {task_id} / Plan Version: v01 / Attempt: A01",
        "Workflow Version: v4.0",
        "",
    ]
    for heading in EXEC_HEADINGS:
        lines.extend([f"## {heading}", ""])
        if heading == "4. Commands":
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
        elif heading == "5. AC Mapping":
            lines.extend(
                [
                    "| AC | Result | Evidence Type | Evidence |",
                    "| --- | --- | --- | --- |",
                    "| AC-01 | PASS | TEST_RESULT+LOG | evidence.log |",
                    "",
                ]
            )
    lines.append("Conclusion: PASS")
    return "\n".join(lines) + "\n"


def _acceptance() -> str:
    return (
        f"# ACCEPTANCE — {_TASK_ID}\n"
        "Workflow Version: v4.0\n\n"
        "| AC | Class | Executor | Expected | Result | Primary Evidence |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        "| AC-01 | WORKER_AUTOMATABLE | WORKER | 交接通过 | PASS | TEST_RESULT+LOG |\n\n"
        "## Unplanned Change Review\n\n"
        "| Path | Decision | Reason |\n"
        "| --- | --- | --- |\n"
        "| none | NOT APPLICABLE | 无未计划改动 |\n\n"
        "Watchdog 结论建议: PASS\n"
        "用户决定: ACCEPT\n"
    )


class TemplateIntegrationTests(unittest.TestCase):
    def test_python_template_full_and_l0_handover_rehearsal(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "software-py"
            create = _run(
                [
                    sys.executable,
                    str(_ROOT / "scripts" / "workflow.py"),
                    "create",
                    str(project),
                    "--layers",
                    "core,generic,python,python-starter",
                    "--name",
                    "Python Rehearsal",
                    "--yes",
                    "--json",
                ],
                _ROOT,
            )
            self.assertEqual(create.returncode, 0, create.stdout + create.stderr)
            self.assertEqual(_run(["git", "init", "-b", "main"], project).returncode, 0)
            _run(["git", "config", "user.name", "Temp CEO"], project)
            _run(["git", "config", "user.email", "temp-ceo@example.invalid"], project)
            self.assertEqual(_run(["git", "add", "-A"], project).returncode, 0)
            self.assertEqual(
                _run(["git", "commit", "-m", "test: template baseline"], project).returncode,
                0,
            )
            base_commit = _run(["git", "rev-parse", "HEAD"], project).stdout.strip()

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

            _write(task / "TASK_BRIEF.md", _brief(project))
            _write(task / "PLAN_v01.md", _plan("DRAFT", base_commit, project))
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

            _write(task / "PLAN_v01.md", _plan("APPROVED", base_commit, project))
            _write(task / "APPROVAL_RECORD.md", _approval(base_commit))
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
            profile, profile_hash = _profile_identity(project)
            _write(
                l0_task / "TASK_BRIEF.md",
                "# L0\n"
                f"Task ID: GD-2026-0009 / Task Level: L0 / Workflow Version: v4.0 / "
                f"Base Commit: {base_commit}\n"
                f"Project Profile: {profile}\n"
                f"Profile Hash: {profile_hash}\n"
                "目标与验收: WORKER_AUTOMATABLE / WORKER / TEST_RESULT / exit 0\n"
                "文件边界: MODIFY `src/app/**`; FORBIDDEN `pyproject.toml`; "
                "Computer-Use Authorization: NONE\n",
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

    def test_unity_template_v40_handover_structure(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "unity2d"
            (project / "Assets").mkdir(parents=True)
            (project / "ProjectSettings").mkdir()
            (project / "Packages").mkdir()
            (project / "ProjectSettings" / "ProjectVersion.txt").write_text(
                "m_EditorVersion: 2022.3.60f1\n", encoding="utf-8"
            )
            (project / "Packages" / "manifest.json").write_text(
                '{\n  "dependencies": {}\n}\n', encoding="utf-8"
            )
            create = _run(
                [
                    sys.executable,
                    str(_ROOT / "scripts" / "workflow.py"),
                    "create",
                    str(project),
                    "--layers",
                    "core,generic,unity2d,unity2d-starter",
                    "--name",
                    "Unity Rehearsal",
                    "--yes",
                    "--accept-protected",
                    "--json",
                ],
                _ROOT,
            )
            self.assertEqual(create.returncode, 0, create.stdout + create.stderr)
            self.assertEqual(_run(["git", "init", "-b", "main"], project).returncode, 0)
            _run(["git", "config", "user.name", "Temp CEO"], project)
            _run(["git", "config", "user.email", "temp-ceo@example.invalid"], project)
            self.assertEqual(_run(["git", "add", "-A"], project).returncode, 0)
            self.assertEqual(
                _run(["git", "commit", "-m", "test: unity baseline"], project).returncode,
                0,
            )
            base_commit = _run(["git", "rev-parse", "HEAD"], project).stdout.strip()

            task = project / "AI_Context" / "TASKS" / _TASK_ID
            stage = _run(
                [
                    sys.executable,
                    "scripts/stage_context.py",
                    str(task),
                    "--files",
                    "Assets/Scripts/Core/GameClock.cs",
                    "--json",
                ],
                project,
            )
            self.assertEqual(stage.returncode, 0, stage.stderr)

            plan = _plan("DRAFT", base_commit, project).replace(
                "src/app/**", "Assets/Scripts/**"
            )
            _write(task / "TASK_BRIEF.md", _brief(project))
            _write(task / "PLAN_v01.md", plan)
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

            _write(task / "PLAN_v01.md", plan.replace("Status: DRAFT", "Status: APPROVED"))
            _write(
                task / "APPROVAL_RECORD.md",
                _approval(base_commit).replace("src/app/**", "Assets/Scripts/**"),
            )
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


if __name__ == "__main__":
    unittest.main()
