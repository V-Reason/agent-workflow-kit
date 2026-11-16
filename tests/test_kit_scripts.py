"""Standard-library regression tests for the v3.0 kit scripts."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_STAGE = _ROOT / "scripts" / "stage_context.py"
_VALIDATE = _ROOT / "scripts" / "validate_handover.py"
_TASK_ID = "GD-2026-0001"


class StageContextTestBase(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.root = Path(self._temp.name)
        self.context = self.root / "AI_Context"
        self.tasks = self.context / "TASKS"
        self.task_dir = self.tasks / _TASK_ID
        self.task_dir.mkdir(parents=True)
        self._write_default_context()

    def tearDown(self) -> None:
        self._temp.cleanup()

    def _write(self, relative: str, content: str | bytes) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
        return path

    def _write_default_context(self) -> None:
        self._write("AI_Context/PROJECT_OVERVIEW.md", "# Overview\n项目说明。\n")
        self._write("AI_Context/CODING_STANDARDS.md", "# Standards\nUse clear names.\n")
        self._write("AI_Context/BUILD_AND_TEST.md", "# Build\npython -m unittest\n")
        self._write("AI_Context/ARCHITECTURE.md", "# Architecture\nLayered.\n")
        self._write("AI_Context/MODULE_MAP.md", "# Modules\n- app\n")
        self._write("AI_Context/PROJECT_BOARD.md", "# Board\n")
        self._write("AI_Context/DEPENDENCIES.md", "# Dependencies\n")

    def run_stage(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(_STAGE), str(self.task_dir), *args],
            cwd=cwd or self.root,
            text=True,
            capture_output=True,
            check=False,
        )

    def run_stage_json(self, *args: str) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
        result = self.run_stage(*args, "--json")
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            self.fail(f"stdout 不是 JSON：{exc}\nstdout={result.stdout}\nstderr={result.stderr}")
        self.assertIsInstance(payload, dict)
        return result, payload


class StageContextTests(StageContextTestBase):
    def test_flattens_fixed_layers_and_chat_safe_alias(self) -> None:
        self._write("Assets/Scripts/GameClock.cs", "public class GameClock {}\n")
        self._write("Assets/UI/Hud.uxml", "<ui />\n")

        result, payload = self.run_stage_json(
            "--files",
            "Assets/Scripts/GameClock.cs",
            "Assets/UI/Hud.uxml",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(payload["ok"])
        feed = self.task_dir / "FEED_DROP"
        expected = {
            "L1__PROJECT_OVERVIEW.md",
            "L1__CODING_STANDARDS.md",
            "L1__BUILD_AND_TEST.md",
            "L2__PROJECT_BOARD.md",
            "L2__ARCHITECTURE.md",
            "L2__MODULE_MAP.md",
            "L2__DEPENDENCIES.md",
            "L3__Assets_Scripts_GameClock.cs",
            "L3__Assets_UI_Hud.uxml.txt",
            "L3__git_recent_context.txt",
        }
        self.assertEqual({path.name for path in feed.iterdir()}, expected)
        self.assertFalse((feed / "L3__Assets_UI_Hud.uxml").exists())
        manifest = (self.task_dir / "00_CONTEXT_MANIFEST.md").read_text(encoding="utf-8")
        self.assertIn("`L3__Assets_UI_Hud.uxml.txt` | L3 | `Assets/UI/Hud.uxml`", manifest)
        self.assertIn("非 Git 工作区", manifest)

    def test_no_chat_safe_keeps_cold_extension(self) -> None:
        self._write("Assets/UI/Hud.uxml", "<ui />\n")

        result, payload = self.run_stage_json(
            "--no-chat-safe",
            "--files",
            "Assets/UI/Hud.uxml",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(payload["ok"])
        feed = self.task_dir / "FEED_DROP"
        self.assertTrue((feed / "L3__Assets_UI_Hud.uxml").is_file())
        self.assertFalse((feed / "L3__Assets_UI_Hud.uxml.txt").exists())

    def test_append_merges_previous_manifest_by_source_path(self) -> None:
        self._write("src/one.py", "print('one')\n")
        self._write("src/two.py", "print('two')\n")
        first = self.run_stage("--files", "src/one.py")
        self.assertEqual(first.returncode, 0, first.stderr)

        second, payload = self.run_stage_json("--append", "--files", "src/two.py")

        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertTrue(payload["ok"])
        feed = self.task_dir / "FEED_DROP"
        self.assertTrue((feed / "L3__src_one.py").is_file())
        self.assertTrue((feed / "L3__src_two.py").is_file())

    def test_default_mode_clears_stale_staged_files(self) -> None:
        self._write("src/one.py", "print('one')\n")
        self._write("src/two.py", "print('two')\n")
        self.assertEqual(self.run_stage("--files", "src/one.py").returncode, 0)
        feed = self.task_dir / "FEED_DROP"
        (feed / "stale.txt").write_text("stale", encoding="utf-8")

        result = self.run_stage("--files", "src/two.py")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((feed / "L3__src_one.py").exists())
        self.assertFalse((feed / "stale.txt").exists())
        self.assertTrue((feed / "L3__src_two.py").is_file())

    def test_from_list_combines_with_files(self) -> None:
        self._write("src/one.py", "print('one')\n")
        self._write("src/two.py", "print('two')\n")
        self._write("list.txt", "# source files\nsrc/two.py\n")

        result, payload = self.run_stage_json(
            "--files",
            "src/one.py",
            "--from-list",
            "list.txt",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(payload["ok"])
        feed = self.task_dir / "FEED_DROP"
        self.assertTrue((feed / "L3__src_one.py").is_file())
        self.assertTrue((feed / "L3__src_two.py").is_file())

    def test_rejects_traversal_and_outside_absolute_path(self) -> None:
        outside = self.root.parent / "outside.txt"
        outside.write_text("outside", encoding="utf-8")
        try:
            traversal = self.run_stage("--files", "../outside.txt", "--json")
            self.assertEqual(traversal.returncode, 1)
            self.assertFalse(json.loads(traversal.stdout)["ok"])

            absolute = self.run_stage("--files", str(outside), "--json")
            self.assertEqual(absolute.returncode, 1)
            self.assertFalse(json.loads(absolute.stdout)["ok"])
            self.assertFalse((self.task_dir / "FEED_DROP").exists())
        finally:
            outside.unlink(missing_ok=True)

    def test_rejects_sensitive_file_names_but_allows_example_env(self) -> None:
        self._write("private/.env", "TOKEN=secret\n")
        self._write(".env.example", "TOKEN=\n")

        rejected = self.run_stage("--files", "private/.env", "--json")
        allowed = self.run_stage("--files", ".env.example", "--json")

        self.assertEqual(rejected.returncode, 1)
        self.assertFalse(json.loads(rejected.stdout)["ok"])
        self.assertEqual(allowed.returncode, 0, allowed.stderr)
        self.assertTrue(json.loads(allowed.stdout)["ok"])
        manifest = (self.task_dir / "00_CONTEXT_MANIFEST.md").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("private/.env", manifest)

    def test_token_estimate_uses_cjk_and_ascii_rule(self) -> None:
        self._write("src/mixed.txt", "abcd中文")

        result, payload = self.run_stage_json("--files", "src/mixed.txt")

        self.assertEqual(result.returncode, 0, result.stderr)
        staged = {
            entry["staged"]: entry
            for entry in payload["files"]
            if isinstance(entry, dict)
        }
        self.assertEqual(staged["L3__src_mixed.txt"]["tokens"], 3)
        tokens = payload["tokens"]
        self.assertEqual(
            tokens["total"],
            tokens["l1"] + tokens["l2"] + tokens["l3"],
        )

    def test_rejects_flat_name_collision(self) -> None:
        self._write("a/b.py", "print('nested')\n")
        self._write("a_b.py", "print('flat')\n")

        result = self.run_stage(
            "--files",
            "a/b.py",
            "a_b.py",
            "--json",
        )

        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["ok"])
        self.assertIn("冲突", payload["error"])

    def test_budget_warning_is_non_blocking(self) -> None:
        self._write("src/large.txt", "a" * 100)

        result, payload = self.run_stage_json(
            "--files",
            "src/large.txt",
            "--budget-limit",
            "1",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(payload["ok"])
        self.assertTrue(any("预算" in warning for warning in payload["warnings"]))

    @unittest.skipUnless(hasattr(os, "symlink"), "platform does not support symlinks")
    def test_rejects_symlink_escape(self) -> None:
        outside = self.root.parent / f"outside-{self.root.name}.txt"
        outside.write_text("outside", encoding="utf-8")
        link = self.root / "src" / "escape.txt"
        link.parent.mkdir(parents=True)
        try:
            try:
                link.symlink_to(outside)
            except OSError as exc:
                self.skipTest(f"symlink unavailable: {exc}")

            result = self.run_stage("--files", "src/escape.txt", "--json")

            self.assertEqual(result.returncode, 1)
            self.assertFalse(json.loads(result.stdout)["ok"])
        finally:
            outside.unlink(missing_ok=True)


class ScriptSyncTests(unittest.TestCase):
    def _digest(self, path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def test_template_script_copies_are_byte_identical(self) -> None:
        pairs = [
            (
                _STAGE,
                _ROOT / "templates" / "software-py" / "scripts" / "stage_context.py",
                _ROOT / "templates" / "unity2d" / "scripts" / "stage_context.py",
            ),
            (
                _VALIDATE,
                _ROOT / "templates" / "software-py" / "scripts" / "validate_handover.py",
                _ROOT / "templates" / "unity2d" / "scripts" / "validate_handover.py",
            ),
        ]
        for source, py_copy, unity_copy in pairs:
            expected = self._digest(source)
            self.assertEqual(self._digest(py_copy), expected, py_copy)
            self.assertEqual(self._digest(unity_copy), expected, unity_copy)


if __name__ == "__main__":
    unittest.main()
