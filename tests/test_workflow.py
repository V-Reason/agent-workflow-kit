"""End-to-end tests for the v4.0 project workflow assembler."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_WORKFLOW = _ROOT / "scripts" / "workflow.py"


def _run(
    *args: str,
    cwd: Path | None = None,
    stdin: str | None = None,
) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, str(_WORKFLOW), *args],
        cwd=cwd or _ROOT,
        text=True,
        encoding="utf-8",
        capture_output=True,
        env=environment,
        input=stdin,
        check=False,
    )


class WorkflowCreateTests(unittest.TestCase):
    def test_interactive_wizard_creates_generic_project(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "wizard"
            result = _run(
                stdin=(
                    "1\n"
                    f"{project}\n"
                    "Wizard Project\n"
                    "1\n"
                    "n\n"
                    "y\n"
                )
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue((project / "AI_Context" / "WORKFLOW_LOCK.toml").is_file())

    def test_create_generic_project_installs_complete_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "demo"
            result = _run(
                "create",
                str(project),
                "--layers",
                "core,generic",
                "--name",
                "Demo Project",
                "--yes",
                "--json",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["project"], str(project.resolve()))
            self.assertTrue((project / "AGENTS.md").is_file())
            self.assertTrue((project / "AI_Context" / "WORKFLOW_PROFILE.toml").is_file())
            self.assertTrue((project / "AI_Context" / "WORKFLOW_LOCK.toml").is_file())
            self.assertTrue((project / "scripts" / "workflow.py").is_file())
            self.assertTrue((project / "scripts" / "stage_context.py").is_file())
            self.assertTrue(
                (project / ".agents" / "skills" / "worker-engine" / "SKILL.md").is_file()
            )
            self.assertIn(
                'name = "Demo Project"',
                (project / "AI_Context" / "WORKFLOW_PROFILE.toml").read_text(
                    encoding="utf-8"
                ),
            )
            for source in [
                _ROOT / "scripts" / "workflow.py",
                _ROOT / "scripts" / "stage_context.py",
                _ROOT / "scripts" / "validate_handover.py",
                *_ROOT.glob("scripts/workflow_kit/*.py"),
            ]:
                relative = source.relative_to(_ROOT)
                self.assertEqual(
                    (project / relative).read_bytes(),
                    source.read_bytes(),
                    relative,
                )
            generated_context = "\n".join(
                path.read_text(encoding="utf-8", errors="replace")
                for path in (project / "AI_Context").glob("*.md")
            )
            self.assertNotIn("{{", generated_context)

    def test_create_preview_cancel_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "cancelled"
            result = _run(
                "create",
                str(project),
                "--layers",
                "core,generic",
                "--name",
                "Cancelled",
                stdin="n\n",
            )
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertFalse(project.exists())

    def test_create_dry_run_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "dry-run"
            result = _run(
                "create",
                str(project),
                "--layers",
                "core,generic",
                "--dry-run",
                "--json",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "dry-run")
            self.assertFalse(project.exists())

    def test_json_preview_requires_noninteractive_choice(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "json-preview"
            result = _run(
                "create",
                str(project),
                "--layers",
                "core,generic",
                "--json",
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("--yes", json.loads(result.stdout)["error"])
            self.assertFalse(project.exists())

    def test_create_python_starter_installs_optional_code_skeleton(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "python"
            result = _run(
                "create",
                str(project),
                "--layers",
                "core,generic,python,python-starter",
                "--name",
                "Python Starter",
                "--yes",
                "--json",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue((project / "pyproject.toml").is_file())
            self.assertTrue((project / "src" / "app" / "domain" / "models.py").is_file())
            self.assertTrue((project / "tests" / "unit" / "test_models.py").is_file())
            doctor = _run("doctor", str(project), "--json")
            self.assertEqual(doctor.returncode, 0, doctor.stdout + doctor.stderr)


class WorkflowAttachTests(unittest.TestCase):
    def _attach_generic(self, project: Path) -> subprocess.CompletedProcess[str]:
        return _run(
            "attach",
            str(project),
            "--layers",
            "core,generic",
            "--name",
            "Existing Project",
            "--yes",
            "--json",
        )

    def test_attach_preserves_existing_files_and_context(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "existing"
            project.mkdir()
            (project / "AGENTS.md").write_text("# Existing Rules\n\nKeep me.\n", encoding="utf-8")
            (project / "README.md").write_text("# Existing README\n", encoding="utf-8")
            context = project / "AI_Context"
            context.mkdir()
            (context / "PROJECT_BOARD.md").write_text(
                "# User Board\n\nDo not replace.\n", encoding="utf-8"
            )

            result = self._attach_generic(project)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            agents = (project / "AGENTS.md").read_text(encoding="utf-8")
            readme = (project / "README.md").read_text(encoding="utf-8")
            board = (context / "PROJECT_BOARD.md").read_text(encoding="utf-8")
            self.assertIn("# Existing Rules", agents)
            self.assertIn("AGENT_WORKFLOW_KIT:core", agents)
            self.assertIn("AGENT_WORKFLOW_KIT:generic", readme)
            self.assertIn("# Existing README", readme)
            self.assertEqual(board, "# User Board\n\nDo not replace.\n")

    def test_attach_twice_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "repeat"
            project.mkdir()
            first = self._attach_generic(project)
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            before = {
                path.relative_to(project).as_posix(): path.read_bytes()
                for path in project.rglob("*")
                if path.is_file()
            }

            second = self._attach_generic(project)
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            after = {
                path.relative_to(project).as_posix(): path.read_bytes()
                for path in project.rglob("*")
                if path.is_file()
            }
            self.assertEqual(before, after)

    def test_attach_rejects_dirty_git_without_allow_dirty(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "dirty"
            project.mkdir()
            subprocess.run(["git", "init", "-b", "main"], cwd=project, check=True, capture_output=True)
            (project / "user.txt").write_text("dirty\n", encoding="utf-8")
            result = self._attach_generic(project)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertFalse((project / "AGENTS.md").exists())

    def test_attach_rejects_starter_layers(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "starter"
            project.mkdir()
            result = _run(
                "attach",
                str(project),
                "--layers",
                "core,generic,python,python-starter",
                "--yes",
                "--json",
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("只允许 create", json.loads(result.stdout)["error"])
            self.assertFalse((project / "AGENTS.md").exists())


class WorkflowUnityTests(unittest.TestCase):
    def _make_unity(self, root: Path, *, include_test_framework: bool = True) -> None:
        (root / "Assets").mkdir(parents=True)
        (root / "ProjectSettings").mkdir()
        (root / "Packages").mkdir()
        (root / "ProjectSettings" / "ProjectVersion.txt").write_text(
            "m_EditorVersion: 2022.3.60f1\n", encoding="utf-8"
        )
        dependencies = (
            {"com.unity.test-framework": "1.1.33"}
            if include_test_framework
            else {"com.unity.2d.sprite": "1.0.0"}
        )
        (root / "Packages" / "manifest.json").write_text(
            json.dumps({"dependencies": dependencies}, indent=2) + "\n",
            encoding="utf-8",
        )

    def test_attach_existing_unity_installs_workflow_without_starter_code(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "unity"
            project.mkdir()
            self._make_unity(project)
            result = _run(
                "attach",
                str(project),
                "--layers",
                "core,generic,unity2d",
                "--name",
                "Unity Existing",
                "--yes",
                "--json",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(
                (project / "Assets" / "AgentWorkflow" / "Editor" / "WorkflowAuditWindow.cs").is_file()
            )
            self.assertFalse((project / "Assets" / "Scripts" / "Core" / "GameBootstrap.cs").exists())

    def test_invalid_unity_project_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "not-unity"
            (project / "Assets").mkdir(parents=True)
            result = _run(
                "attach",
                str(project),
                "--layers",
                "core,generic,unity2d",
                "--yes",
                "--json",
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertFalse((project / "AGENTS.md").exists())

    def test_protected_manifest_change_blocks_without_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "unity-protected"
            project.mkdir()
            self._make_unity(project, include_test_framework=False)
            result = _run(
                "attach",
                str(project),
                "--layers",
                "core,generic,unity2d",
                "--yes",
                "--json",
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertFalse((project / "AGENTS.md").exists())
            self.assertTrue((project / "AI_Context" / "WORKFLOW_CONFLICTS.md").is_file())


class WorkflowStatusAndSyncTests(unittest.TestCase):
    def _create_custom_kit(self, root: Path) -> Path:
        profile = root / "team-doc"
        (profile / "files").mkdir(parents=True)
        (profile / "profile.toml").write_text(
            "\n".join(
                [
                    "schema_version = 1",
                    'id = "team-doc"',
                    'version = "1.0.0"',
                    'display_name = "Team Doc"',
                    'description = "team file"',
                    'requires = ["core"]',
                    "conflicts = []",
                    "required_paths = []",
                    "recommended_gates = []",
                    "[detection]",
                    "all_paths = []",
                    "any_paths = []",
                    "[[actions]]",
                    'type = "copy_file"',
                    'source = "files/team.txt"',
                    'target = "TEAM.txt"',
                    'ownership = "KIT_OWNED"',
                    "",
                ]
            ),
            encoding="utf-8",
        )
        (profile / "files" / "team.txt").write_text("v1\n", encoding="utf-8")
        return profile

    def test_status_and_doctor_detect_managed_file_tamper(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "project"
            created = _run(
                "create",
                str(project),
                "--layers",
                "core,generic",
                "--yes",
                "--json",
            )
            self.assertEqual(created.returncode, 0, created.stdout + created.stderr)

            status = _run("status", str(project), "--json")
            self.assertEqual(status.returncode, 0, status.stdout + status.stderr)
            self.assertEqual(json.loads(status.stdout)["status"], "ok")
            doctor = _run("doctor", str(project), "--json")
            self.assertEqual(doctor.returncode, 0, doctor.stdout + doctor.stderr)

            (project / "scripts" / "stage_context.py").write_text(
                "# tampered\n", encoding="utf-8"
            )
            status = _run("status", str(project), "--json")
            self.assertEqual(status.returncode, 1, status.stdout + status.stderr)
            self.assertEqual(json.loads(status.stdout)["status"], "drifted")
            doctor = _run("doctor", str(project), "--json")
            self.assertEqual(doctor.returncode, 1, doctor.stdout + doctor.stderr)

    def test_status_on_unassembled_project_returns_json_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            result = _run("status", str(project), "--json")
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "error")
            self.assertNotIn("Traceback", result.stderr)

    def test_sync_check_and_apply_update_custom_kit_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            custom_root = Path(temp) / "custom"
            profile = self._create_custom_kit(custom_root)
            project = Path(temp) / "project"
            created = _run(
                "create",
                str(project),
                "--layers",
                "core,generic,team-doc",
                "--profile-root",
                str(custom_root),
                "--yes",
                "--json",
            )
            self.assertEqual(created.returncode, 0, created.stdout + created.stderr)
            self.assertEqual((project / "TEAM.txt").read_text(encoding="utf-8"), "v1\n")

            (profile / "files" / "team.txt").write_text("v2\n", encoding="utf-8")
            check = _run(
                "sync",
                str(project),
                "--from",
                str(_ROOT),
                "--profile-root",
                str(custom_root),
                "--check",
                "--json",
            )
            self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
            self.assertIn("TEAM.txt", json.loads(check.stdout)["changes"])
            self.assertEqual((project / "TEAM.txt").read_text(encoding="utf-8"), "v1\n")

            apply = _run(
                "sync",
                str(project),
                "--from",
                str(_ROOT),
                "--profile-root",
                str(custom_root),
                "--apply",
                "--json",
            )
            self.assertEqual(apply.returncode, 0, apply.stdout + apply.stderr)
            self.assertEqual((project / "TEAM.txt").read_text(encoding="utf-8"), "v2\n")

    def test_sync_blocks_user_modified_managed_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            custom_root = Path(temp) / "custom"
            profile = self._create_custom_kit(custom_root)
            project = Path(temp) / "project"
            created = _run(
                "create",
                str(project),
                "--layers",
                "core,generic,team-doc",
                "--profile-root",
                str(custom_root),
                "--yes",
                "--json",
            )
            self.assertEqual(created.returncode, 0, created.stdout + created.stderr)
            (project / "TEAM.txt").write_text("local edit\n", encoding="utf-8")
            (profile / "files" / "team.txt").write_text("v2\n", encoding="utf-8")

            result = _run(
                "sync",
                str(project),
                "--from",
                str(_ROOT),
                "--profile-root",
                str(custom_root),
                "--apply",
                "--json",
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertEqual(
                (project / "TEAM.txt").read_text(encoding="utf-8"),
                "local edit\n",
            )
            self.assertTrue((project / "AI_Context" / "WORKFLOW_CONFLICTS.md").is_file())

    def test_sync_updates_managed_block_without_touching_user_text(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            custom_root = Path(temp) / "custom"
            profile = custom_root / "team-block"
            (profile / "blocks").mkdir(parents=True)
            (profile / "profile.toml").write_text(
                "\n".join(
                    [
                        "schema_version = 1",
                        'id = "team-block"',
                        'version = "1.0.0"',
                        'display_name = "Team Block"',
                        'description = "managed block"',
                        'requires = ["core"]',
                        "conflicts = []",
                        "required_paths = []",
                        "recommended_gates = []",
                        "[detection]",
                        "all_paths = []",
                        "any_paths = []",
                        "[[actions]]",
                        'type = "managed_block"',
                        'source = "blocks/agents.md"',
                        'target = "AGENTS.md"',
                        'block_id = "team"',
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            (profile / "blocks" / "agents.md").write_text(
                "## Team Rule\n\nVersion one.\n", encoding="utf-8"
            )
            project = Path(temp) / "project"
            created = _run(
                "create",
                str(project),
                "--layers",
                "core,generic,team-block",
                "--profile-root",
                str(custom_root),
                "--yes",
                "--json",
            )
            self.assertEqual(created.returncode, 0, created.stdout + created.stderr)
            agents_path = project / "AGENTS.md"
            agents_path.write_text(
                agents_path.read_text(encoding="utf-8") + "\nUSER OWNED TEXT\n",
                encoding="utf-8",
            )
            (profile / "blocks" / "agents.md").write_text(
                "## Team Rule\n\nVersion two.\n", encoding="utf-8"
            )

            result = _run(
                "sync",
                str(project),
                "--from",
                str(_ROOT),
                "--profile-root",
                str(custom_root),
                "--apply",
                "--json",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            agents = agents_path.read_text(encoding="utf-8")
            self.assertIn("Version two.", agents)
            self.assertIn("USER OWNED TEXT", agents)

    def test_custom_profile_path_traversal_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            custom_root = Path(temp) / "custom"
            profile = custom_root / "escape"
            (profile / "files").mkdir(parents=True)
            (Path(temp) / "outside.txt").write_text("outside\n", encoding="utf-8")
            (profile / "profile.toml").write_text(
                "\n".join(
                    [
                        "schema_version = 1",
                        'id = "escape"',
                        'version = "1.0.0"',
                        'display_name = "Escape"',
                        'description = "bad path"',
                        'requires = ["core"]',
                        "conflicts = []",
                        "required_paths = []",
                        "recommended_gates = []",
                        "[detection]",
                        "all_paths = []",
                        "any_paths = []",
                        "[[actions]]",
                        'type = "copy_file"',
                        'source = "../outside.txt"',
                        'target = "ESCAPE.txt"',
                        'ownership = "SEEDED"',
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            project = Path(temp) / "project"
            result = _run(
                "create",
                str(project),
                "--layers",
                "core,generic,escape",
                "--profile-root",
                str(custom_root),
                "--yes",
                "--json",
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertFalse(project.exists())

    def test_custom_profile_required_path_is_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            custom_root = Path(temp) / "custom"
            profile = custom_root / "required"
            (profile / "files").mkdir(parents=True)
            (profile / "profile.toml").write_text(
                "\n".join(
                    [
                        "schema_version = 1",
                        'id = "required"',
                        'version = "1.0.0"',
                        'display_name = "Required"',
                        'description = "required path"',
                        'requires = ["core"]',
                        "conflicts = []",
                        'required_paths = ["MUST_EXIST.txt"]',
                        "recommended_gates = []",
                        "[detection]",
                        "all_paths = []",
                        "any_paths = []",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            project = Path(temp) / "project"
            result = _run(
                "create",
                str(project),
                "--layers",
                "core,generic,required",
                "--profile-root",
                str(custom_root),
                "--yes",
                "--json",
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertFalse((project / "AGENTS.md").exists())

    def test_profile_init_and_validate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            profile = Path(temp) / "profile"
            init = _run("profile", "init", str(profile), "--id", "team-stack", "--json")
            self.assertEqual(init.returncode, 0, init.stdout + init.stderr)
            validate = _run("profile", "validate", str(profile), "--json")
            self.assertEqual(validate.returncode, 0, validate.stdout + validate.stderr)
            self.assertEqual(json.loads(validate.stdout)["id"], "team-stack")


if __name__ == "__main__":
    unittest.main()
