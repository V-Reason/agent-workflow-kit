"""Structural checks for the v3.0 role and template layout."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent

EXPECTED_SKILLS = {
    "game-systems-designer",
    "planner-orchestrator",
    "secretary-router",
    "software-architect",
    "task-brief-writer",
    "unity2d-architect",
    "watchdog-inspector",
    "worker-engine",
}
ADVISOR_SKILLS = {
    "game-systems-designer",
    "software-architect",
    "unity2d-architect",
}
FORBIDDEN_OLD_TERMS = (
    "exec" + "utor-engine",
    "engineering-" + "verifier",
    "failure-" + "retrospector",
    "验" + "证员",
    "复" + "盘员",
)


class SkillLayoutTests(unittest.TestCase):
    def test_exact_eight_orthogonal_skills_exist(self) -> None:
        skill_dirs = {path.name for path in (_ROOT / "skills").iterdir() if path.is_dir()}
        self.assertEqual(skill_dirs, EXPECTED_SKILLS)
        for name in EXPECTED_SKILLS:
            skill = _ROOT / "skills" / name / "SKILL.md"
            self.assertTrue(skill.is_file(), skill)
            text = skill.read_text(encoding="utf-8")
            match = re.search(r"^name:\s*([a-z0-9-]+)\s*$", text, re.MULTILINE)
            self.assertIsNotNone(match, skill)
            self.assertEqual(match.group(1), name)

    def test_advisors_are_planning_only(self) -> None:
        for name in ADVISOR_SKILLS:
            text = (_ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("规划期只读顾问", text, name)
            self.assertIn("施工期", text, name)
            self.assertNotIn("全栈" + "闭环", text, name)
            self.assertNotIn("下场" + "写", text, name)

    def test_old_role_terms_are_absent_from_skills(self) -> None:
        combined = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (_ROOT / "skills").glob("*/SKILL.md")
        ).lower()
        for term in FORBIDDEN_OLD_TERMS:
            self.assertNotIn(term.lower(), combined)


class UnityAssemblyTests(unittest.TestCase):
    def test_editor_tools_only_reference_core(self) -> None:
        path = (
            _ROOT
            / "templates"
            / "unity2d"
            / "Assets"
            / "Scripts"
            / "Editor"
            / "Editor.asmdef"
        )
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["name"], "GAMEDEV.EditorTools")
        self.assertEqual(data["references"], ["GAMEDEV.Core"])
        self.assertEqual(data["includePlatforms"], ["Editor"])

    def test_project_audit_has_v3_files_and_headless_exit(self) -> None:
        path = (
            _ROOT
            / "templates"
            / "unity2d"
            / "Assets"
            / "Scripts"
            / "Editor"
            / "Tools"
            / "ProjectAuditWindow.cs"
        )
        text = path.read_text(encoding="utf-8")
        self.assertIn("RunBatchAudit()", text)
        self.assertIn("EditorApplication.Exit", text)
        self.assertIn("AI_Context/PROJECT_BOARD.md", text)
        self.assertIn("scripts/stage_context.py", text)
        self.assertIn("scripts/validate_handover.py", text)

    def test_unity_brief_has_no_python_toolchain_residue(self) -> None:
        path = (
            _ROOT
            / "templates"
            / "unity2d"
            / "AI_Context"
            / "TASKS"
            / "_templates"
            / "TASK_BRIEF.md"
        )
        text = path.read_text(encoding="utf-8")
        for term in ("Python", "uv ", "ruff", "mypy", "pytest"):
            self.assertNotIn(term, text)


class TemplateHygieneTests(unittest.TestCase):
    def test_templates_ignore_feed_drop(self) -> None:
        for name in ("software-py", "unity2d"):
            text = (_ROOT / "templates" / name / ".gitignore").read_text(
                encoding="utf-8"
            )
            self.assertIn("AI_Context/TASKS/**/FEED_DROP/", text)

    def test_python_tooling_excludes_ai_context(self) -> None:
        text = (_ROOT / "templates" / "software-py" / "pyproject.toml").read_text(
            encoding="utf-8"
        )
        self.assertIn('extend-exclude = ["AI_Context"]', text)
        self.assertIn('norecursedirs = [".*", "AI_Context", "build", "dist"]', text)
        self.assertIn('exclude = ["^AI_Context/"]', text)

    def test_project_boards_and_manifest_templates_exist(self) -> None:
        for name in ("software-py", "unity2d"):
            base = _ROOT / "templates" / name / "AI_Context"
            self.assertTrue((base / "PROJECT_BOARD.md").is_file())
            self.assertTrue(
                (base / "TASKS" / "_templates" / "00_CONTEXT_MANIFEST.md").is_file()
            )
            self.assertFalse(
                (
                    base
                    / "TASKS"
                    / "_templates"
                    / ("CONTEXT_" + "PACKET_v01.md")
                ).exists()
            )


class ConsistencyTests(unittest.TestCase):
    def _text_files(self) -> list[Path]:
        excluded = {".git", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
        suffixes = {".md", ".py", ".toml", ".yml", ".yaml", ".txt", ".cs"}
        files: list[Path] = []
        for path in _ROOT.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in suffixes:
                continue
            if any(part in excluded for part in path.parts):
                continue
            if path == _ROOT / "docs" / "DESIGN_CHARTER.md":
                continue
            files.append(path)
        return files

    def test_old_workflow_terms_are_absent(self) -> None:
        banned = [
            "exec" + "utor-engine",
            "engineering-" + "verifier",
            "failure-" + "retrospector",
            "验" + "证员",
            "复" + "盘员",
            "CONTEXT_" + "PACKET",
            "A/" + "B/" + "C",
            "全栈" + "闭环",
            "下场" + "写",
        ]
        for path in self._text_files():
            text = path.read_text(encoding="utf-8", errors="replace").lower()
            for term in banned:
                self.assertNotIn(term.lower(), text, f"{term} in {path}")

    def test_relative_markdown_links_resolve(self) -> None:
        pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
        for path in self._text_files():
            if path.suffix.lower() != ".md":
                continue
            text = path.read_text(encoding="utf-8")
            for target in pattern.findall(text):
                if target.startswith(("http://", "https://", "#", "mailto:")):
                    continue
                resolved = (path.parent / target).resolve()
                self.assertTrue(resolved.exists(), f"Broken link {target} in {path}")


if __name__ == "__main__":
    unittest.main()
