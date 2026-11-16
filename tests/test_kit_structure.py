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
    "executor-engine",
    "engineering-verifier",
    "failure-retrospector",
    "验证员",
    "复盘员",
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
            self.assertNotIn("全栈闭环", text, name)
            self.assertNotIn("下场写", text, name)

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


if __name__ == "__main__":
    unittest.main()
