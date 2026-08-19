from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from nova.skills import InvalidSkill, discover_skills, write_skill_index


class SkillDiscoveryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def add_skill(
        self,
        directory: str,
        *,
        name: str | None = None,
        description: str = "Use for a tested workflow.",
    ) -> Path:
        path = self.root / "skills" / directory / "SKILL.md"
        path.parent.mkdir(parents=True)
        path.write_text(
            "---\n"
            f"name: {name or directory}\n"
            f'description: "{description}"\n'
            "---\n\n"
            f"# {directory}\n",
            encoding="utf-8",
        )
        return path

    def test_discovers_sorted_canonical_metadata(self) -> None:
        self.add_skill("review-code")
        first_path = self.add_skill("capture")

        skills = discover_skills(self.root)

        self.assertEqual([skill.name for skill in skills], ["capture", "review-code"])
        self.assertEqual(skills[0].description, "Use for a tested workflow.")
        self.assertEqual(skills[0].path, str(first_path.resolve()))

    def test_rejects_a_name_that_does_not_match_its_directory(self) -> None:
        self.add_skill("capture", name="other-skill")

        with self.assertRaises(InvalidSkill):
            discover_skills(self.root)

    def test_rejects_missing_or_multiline_description(self) -> None:
        path = self.add_skill("capture")
        path.write_text(
            "---\nname: capture\ndescription: >\n---\n",
            encoding="utf-8",
        )

        with self.assertRaises(InvalidSkill):
            discover_skills(self.root)

    def test_writes_a_runtime_index_without_changing_canonical_skills(self) -> None:
        skill_path = self.add_skill("capture")
        original = skill_path.read_text(encoding="utf-8")

        output = write_skill_index(self.root)

        self.assertEqual(output, self.root.resolve() / ".runtime/skill-index.json")
        index = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(index[0]["name"], "capture")
        self.assertEqual(index[0]["path"], str(skill_path.resolve()))
        self.assertEqual(skill_path.read_text(encoding="utf-8"), original)


if __name__ == "__main__":
    unittest.main()
