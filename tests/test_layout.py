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
            "SECURITY.md",
            "VERSION",
            "hooks/nova_context.sh",
            "install.sh",
            "memories/USER.md",
            "memories/MEMORY.md",
            "second_brain/README.md",
            "second_brain/agents-second-brain/README.md",
            "second_brain/agents-second-brain/dailies/README.md",
            "second_brain/projects/README.md",
            "skills/README.md",
            "learning/README.md",
            "learning/proposal-schema.json",
            "learning/proposals/README.md",
            "learning/feedback/README.md",
            "skills/curate-skill-learning/SKILL.md",
            "skills/update-nova/SKILL.md",
            "skills/update-nova/agents/openai.yaml",
            "scripts/build-release.sh",
        ]

        for relative_path in expected:
            with self.subTest(path=relative_path):
                self.assertTrue((ROOT / relative_path).is_file())

    def test_version_is_semantic_and_visible(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        installer = (ROOT / "install.sh").read_text(encoding="utf-8")

        self.assertRegex(version, r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
        self.assertIn(f"Current version `{version}`.", readme)
        self.assertIn(f"such as `v{version}`.", readme)
        self.assertIn(f"NOVA_INSTALL_VERSION={version}\n", installer)

    def test_public_security_channel_is_visible(self) -> None:
        security = (ROOT / "SECURITY.md").read_text(encoding="utf-8")

        self.assertIn(
            "https://github.com/thefactus/nova/security/advisories/new",
            security,
        )
        self.assertIn("Rotate or revoke it first.", security)

    def test_nova_is_presented_as_an_ai_assistant(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

        self.assertIn("Nova is an AI assistant", readme)
        self.assertIn("Nova is the owner's AI assistant", agents)
        self.assertIn("Is Nova just memory between sessions?", readme)

    def test_proposal_schema_defines_the_review_states(self) -> None:
        schema_path = ROOT / "learning/proposal-schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        self.assertEqual(schema["properties"]["version"]["const"], 1)
        self.assertEqual(
            schema["properties"]["status"]["enum"],
            ["pending", "approved", "rejected", "applied"],
        )
        self.assertIn("history", schema["required"])
        self.assertEqual(schema["properties"]["history"]["minItems"], 1)

    def test_agent_native_learning_has_no_product_runtime(self) -> None:
        removed_runtime_paths = [
            "learning/config.json",
            "learning/review-schema.json",
            "nova/learning.py",
            "nova/skills.py",
            "skills/curate-skill-learning/scripts/curator.py",
        ]

        for relative_path in removed_runtime_paths:
            with self.subTest(path=relative_path):
                self.assertFalse((ROOT / relative_path).exists())


if __name__ == "__main__":
    unittest.main()
