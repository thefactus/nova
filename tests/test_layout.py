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
            ".github/workflows/verify.yml",
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
            "skills/capture/SKILL.md",
            "skills/capture/agents/openai.yaml",
            "skills/curate-skill-learning/SKILL.md",
            "skills/herdr/SKILL.md",
            "skills/herdr/agents/openai.yaml",
            "skills/herdr/references/cli.md",
            "skills/organize-project-knowledge/SKILL.md",
            "skills/organize-project-knowledge/agents/openai.yaml",
            "skills/skill-library-audit/SKILL.md",
            "skills/skill-library-audit/agents/openai.yaml",
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
        compact_readme = " ".join(readme.split())

        self.assertIn("Nova is an AI assistant", readme)
        self.assertIn("Nova is the owner's AI assistant", agents)
        self.assertIn("Is Nova just memory between sessions?", readme)
        self.assertIn("small, understandable layer of shared context", compact_readme)
        self.assertIn("burying coding agents in rules", compact_readme)
        self.assertIn("requiring a complex setup", compact_readme)

    def test_external_project_continuity_has_a_compact_pointer(self) -> None:
        agents = " ".join(
            (ROOT / "AGENTS.md").read_text(encoding="utf-8").split()
        )

        self.assertIn("pointer under `second_brain/projects/`", agents)
        self.assertIn("name, location, and purpose", agents)
        self.assertIn("project's own repository", agents)

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

    def test_public_skills_have_no_private_source_assumptions(self) -> None:
        private_markers = ["/Users/", "Pablo", "Stitch Fix"]

        for skill_path in (ROOT / "skills").glob("*/SKILL.md"):
            contents = skill_path.read_text(encoding="utf-8")
            for marker in private_markers:
                with self.subTest(skill=skill_path.parent.name, marker=marker):
                    self.assertNotIn(marker, contents)


if __name__ == "__main__":
    unittest.main()
