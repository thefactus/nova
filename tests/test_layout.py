from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CanonicalLayoutTest(unittest.TestCase):
    def test_canonical_sources_exist(self) -> None:
        expected = [
            ".claude/settings.json",
            ".codex/hooks.json",
            "AGENTS.md",
            "CLAUDE.md",
            "hooks/nova_context.sh",
            "memories/USER.md",
            "memories/MEMORY.md",
            "second_brain/README.md",
            "second_brain/agents-second-brain/README.md",
            "second_brain/agents-second-brain/dailies/README.md",
            "second_brain/projects/README.md",
            "skills/README.md",
            "learning/README.md",
            "learning/config.json",
            "learning/proposals/README.md",
            "learning/feedback/README.md",
            "skills/curate-skill-learning/SKILL.md",
            "skills/curate-skill-learning/scripts/curator.py",
            "skills/update-nova/SKILL.md",
            "skills/update-nova/agents/openai.yaml",
            "nova/skills.py",
        ]

        for relative_path in expected:
            with self.subTest(path=relative_path):
                self.assertTrue((ROOT / relative_path).is_file())

    def test_proposal_schema_defines_the_review_states(self) -> None:
        schema_path = ROOT / "learning/proposal-schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        self.assertEqual(schema["properties"]["version"]["const"], 1)
        self.assertEqual(
            schema["properties"]["status"]["enum"],
            ["pending", "approved", "rejected", "applied"],
        )
        self.assertIn("history", schema["required"])

    def test_review_schema_is_runtime_neutral(self) -> None:
        schema_path = ROOT / "learning/review-schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        self.assertEqual(
            set(schema["required"]),
            {"classification", "memory_entries", "skill_proposals", "summary"},
        )
        self.assertEqual(
            schema["properties"]["memory_entries"]["maxItems"],
            3,
        )


if __name__ == "__main__":
    unittest.main()
