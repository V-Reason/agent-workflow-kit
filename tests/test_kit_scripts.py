"""Standard-library regression tests for the v3.1 kit scripts."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
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

    def test_incremental_append_creates_round_and_preserves_baseline(self) -> None:
        self._write("src/one.py", "print('one')\n")
        source = self._write("src/two.py", "print('two')\n")
        first = self.run_stage("--files", "src/one.py")
        self.assertEqual(first.returncode, 0, first.stderr)

        second, payload = self.run_stage_json(
            "--append",
            "--reason",
            "确认调用契约",
            "--files",
            "src/two.py",
        )

        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["mode"], "need-files")
        self.assertEqual(payload["round"], 1)
        feed = self.task_dir / "FEED_DROP"
        self.assertTrue((feed / "L3__src_one.py").is_file())
        self.assertFalse((feed / "L3__src_two.py").exists())

        round_dir = self.task_dir / "NEED_FILES" / "ROUND_01"
        self.assertTrue((round_dir / "L3__src_two.py").is_file())
        self.assertTrue((round_dir / "ROUND_MANIFEST.md").is_file())
        round_manifest = (round_dir / "ROUND_MANIFEST.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("确认调用契约", round_manifest)
        self.assertIn(hashlib.sha256(source.read_bytes()).hexdigest(), round_manifest)
        manifest = (self.task_dir / "00_CONTEXT_MANIFEST.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Workflow Version: v3.1", manifest)
        self.assertIn("Need Files Rounds: 1\n\n## Token Budget", manifest)
        self.assertIn("## NEED_FILES Round Index", manifest)
        self.assertIn("### ROUND_01", manifest)
        self.assertIn("确认调用契约", manifest)
        self.assertIn(
            hashlib.sha256(source.read_bytes()).hexdigest(),
            manifest,
        )

    def test_append_requires_reason(self) -> None:
        self._write("src/one.py", "print('one')\n")
        self.assertEqual(self.run_stage("--files", "src/one.py").returncode, 0)

        result = self.run_stage("--append", "--files", "src/one.py", "--json")

        self.assertEqual(result.returncode, 1)
        self.assertIn("reason", json.loads(result.stdout)["error"].lower())
        self.assertFalse((self.task_dir / "NEED_FILES").exists())

    def test_reason_is_rejected_without_append(self) -> None:
        self._write("src/one.py", "print('one')\n")

        result = self.run_stage(
            "--reason",
            "误用参数",
            "--files",
            "src/one.py",
            "--json",
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("--append", json.loads(result.stdout)["error"])

    def test_append_is_append_only_across_rounds(self) -> None:
        self._write("src/base.py", "base\n")
        self._write("src/one.py", "one\n")
        self._write("src/two.py", "two\n")
        self.assertEqual(self.run_stage("--files", "src/base.py").returncode, 0)
        self.assertEqual(
            self.run_stage(
                "--append",
                "--reason",
                "第一未知项",
                "--files",
                "src/one.py",
            ).returncode,
            0,
        )
        manifest_path = self.task_dir / "00_CONTEXT_MANIFEST.md"
        first_round = manifest_path.read_text(encoding="utf-8").split(
            "### ROUND_01", 1
        )[1]

        result, payload = self.run_stage_json(
            "--append",
            "--reason",
            "第二未知项",
            "--files",
            "src/two.py",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(payload["round"], 2)
        self.assertTrue(
            (self.task_dir / "NEED_FILES" / "ROUND_02" / "L3__src_two.py").is_file()
        )
        manifest = manifest_path.read_text(encoding="utf-8")
        self.assertIn(first_round.rstrip(), manifest)
        self.assertIn("### ROUND_02", manifest)

    def test_append_rejects_duplicate_content_without_creating_round(self) -> None:
        self._write("src/one.py", "print('one')\n")
        self.assertEqual(self.run_stage("--files", "src/one.py").returncode, 0)

        result = self.run_stage(
            "--append",
            "--reason",
            "重复项",
            "--files",
            "src/one.py",
            "--json",
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("没有新文件", json.loads(result.stdout)["error"])
        self.assertFalse((self.task_dir / "NEED_FILES").exists())

    def test_append_rejects_v30_manifest(self) -> None:
        self._write("src/one.py", "print('one')\n")
        self.assertEqual(self.run_stage("--files", "src/one.py").returncode, 0)
        manifest_path = self.task_dir / "00_CONTEXT_MANIFEST.md"
        manifest_path.write_text(
            manifest_path.read_text(encoding="utf-8").replace(
                "Workflow Version: v3.1", "Workflow Version: v3.0"
            ),
            encoding="utf-8",
        )

        result = self.run_stage(
            "--append",
            "--reason",
            "旧任务兼容",
            "--files",
            "src/one.py",
            "--json",
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("v3.1", json.loads(result.stdout)["error"])

    def test_append_rejects_round_number_gap(self) -> None:
        self._write("src/base.py", "base\n")
        self._write("src/extra.py", "extra\n")
        self.assertEqual(self.run_stage("--files", "src/base.py").returncode, 0)
        (self.task_dir / "NEED_FILES" / "ROUND_02").mkdir(parents=True)

        result = self.run_stage(
            "--append",
            "--reason",
            "非法跳轮",
            "--files",
            "src/extra.py",
            "--json",
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("连续", json.loads(result.stdout)["error"])

    def test_append_rejects_flat_name_collision_without_writing_round(self) -> None:
        self._write("src/base.py", "base\n")
        self._write("a/b.py", "nested\n")
        self._write("a_b.py", "flat\n")
        self.assertEqual(self.run_stage("--files", "src/base.py").returncode, 0)

        result = self.run_stage(
            "--append",
            "--reason",
            "碰撞",
            "--files",
            "a/b.py",
            "a_b.py",
            "--json",
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("冲突", json.loads(result.stdout)["error"])
        self.assertFalse((self.task_dir / "NEED_FILES").exists())

    def test_append_can_stage_changed_content_as_new_round(self) -> None:
        source = self._write("src/one.py", "print('old')\n")
        self.assertEqual(self.run_stage("--files", "src/one.py").returncode, 0)
        source.write_text("print('new')\n", encoding="utf-8")

        result, payload = self.run_stage_json(
            "--append",
            "--reason",
            "冻结快照更新",
            "--files",
            "src/one.py",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(payload["round"], 1)
        staged = self.task_dir / "NEED_FILES" / "ROUND_01" / "L3__src_one.py"
        self.assertEqual(staged.read_text(encoding="utf-8"), "print('new')\n")

    def test_append_preserves_manifest_base_commit_in_result(self) -> None:
        self._write("src/base.py", "base\n")
        self._write("src/extra.py", "extra\n")
        self.assertEqual(self.run_stage("--files", "src/base.py").returncode, 0)
        manifest_path = self.task_dir / "00_CONTEXT_MANIFEST.md"
        manifest = manifest_path.read_text(encoding="utf-8")
        manifest = re.sub(
            r"^- Base Commit:.*$",
            "- Base Commit: 2026-11-16T12:00:00+08:00（可恢复副本时间）",
            manifest,
            count=1,
            flags=re.MULTILINE,
        )
        manifest_path.write_text(manifest, encoding="utf-8")

        result, payload = self.run_stage_json(
            "--append",
            "--reason",
            "保留基线",
            "--files",
            "src/extra.py",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            payload["base_commit"],
            "2026-11-16T12:00:00+08:00（可恢复副本时间）",
        )

    def test_baseline_rebuild_is_rejected_after_round_exists(self) -> None:
        self._write("src/one.py", "print('one')\n")
        self._write("src/two.py", "print('two')\n")
        self.assertEqual(self.run_stage("--files", "src/one.py").returncode, 0)
        self.assertEqual(
            self.run_stage(
                "--append",
                "--reason",
                "补调用方",
                "--files",
                "src/two.py",
            ).returncode,
            0,
        )

        result = self.run_stage("--files", "src/two.py", "--json")

        self.assertEqual(result.returncode, 1)
        self.assertIn("基线", json.loads(result.stdout)["error"])
        self.assertTrue(
            (self.task_dir / "NEED_FILES" / "ROUND_01" / "L3__src_two.py").is_file()
        )

    def test_baseline_rebuild_stays_blocked_even_if_round_directory_is_missing(self) -> None:
        self._write("src/one.py", "print('one')\n")
        self._write("src/two.py", "print('two')\n")
        self.assertEqual(self.run_stage("--files", "src/one.py").returncode, 0)
        self.assertEqual(
            self.run_stage(
                "--append",
                "--reason",
                "补调用方",
                "--files",
                "src/two.py",
            ).returncode,
            0,
        )
        shutil.rmtree(self.task_dir / "NEED_FILES")

        result = self.run_stage("--files", "src/two.py", "--json")

        self.assertEqual(result.returncode, 1)
        self.assertIn("基线", json.loads(result.stdout)["error"])

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
        self._write("skills/secretary-router/SKILL.md", "# Secretary\n")

        rejected = self.run_stage("--files", "private/.env", "--json")
        allowed = self.run_stage("--files", ".env.example", "--json")
        secretary = self.run_stage(
            "--files",
            "skills/secretary-router/SKILL.md",
            "--json",
        )

        self.assertEqual(rejected.returncode, 1)
        self.assertFalse(json.loads(rejected.stdout)["ok"])
        self.assertEqual(allowed.returncode, 0, allowed.stderr)
        self.assertTrue(json.loads(allowed.stdout)["ok"])
        self.assertEqual(secretary.returncode, 0, secretary.stderr)
        self.assertTrue(json.loads(secretary.stdout)["ok"])
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
