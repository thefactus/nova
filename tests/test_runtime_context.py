from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "nova_context.sh"


class RuntimeContextTest(unittest.TestCase):
    def run_hook(
        self, mode: str, cwd: Path = ROOT
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["/bin/sh", str(HOOK), mode],
            cwd=cwd,
            input="{}",
            capture_output=True,
            text=True,
            check=False,
        )

    def test_session_start_builds_and_returns_the_skill_index(self) -> None:
        index_path = ROOT / ".runtime" / "skill-index.json"
        index_path.unlink(missing_ok=True)
        markdown_index_path = ROOT / ".runtime" / "skill-index.md"
        markdown_index_path.unlink(missing_ok=True)

        result = self.run_hook("session-start")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        output = payload["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "SessionStart")
        self.assertIn("memories/USER.md", output["additionalContext"])
        self.assertIn(".runtime/skill-index.md", output["additionalContext"])
        self.assertIn("Nova skills are additive", output["additionalContext"])
        self.assertIn("config.yaml", output["additionalContext"])
        self.assertLessEqual(len(output["additionalContext"]), 500)
        self.assertFalse(index_path.exists())
        self.assertTrue(markdown_index_path.is_file())
        skill_index = markdown_index_path.read_text(encoding="utf-8")
        self.assertIn("# Nova skill index", skill_index)
        self.assertIn("`capture`", skill_index)
        self.assertIn("`skills/capture/SKILL.md`", skill_index)

    def test_session_start_indexes_skills_from_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            hook_path = temporary_path / "hooks" / "nova_context.sh"
            hook_path.parent.mkdir()
            hook_path.write_text(HOOK.read_text(encoding="utf-8"), encoding="utf-8")
            skill_path = temporary_path / "skills" / "review-code" / "SKILL.md"
            skill_path.parent.mkdir(parents=True)
            skill_path.write_text(
                "---\n"
                "name: review-code\n"
                'description: "Review a change safely."\n'
                "---\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                ["/bin/sh", str(hook_path), "session-start"],
                cwd=temporary_path,
                input="{}",
                capture_output=True,
                text=True,
                check=False,
            )

            index = (temporary_path / ".runtime" / "skill-index.md").read_text(
                encoding="utf-8"
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(
            "- `review-code`: Review a change safely. "
            "(`skills/review-code/SKILL.md`)",
            index,
        )

    def test_prompt_submit_returns_skill_routing_context(self) -> None:
        result = self.run_hook("prompt-submit")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        output = payload["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "UserPromptSubmit")
        self.assertIn(".runtime/skill-index.md", output["additionalContext"])
        self.assertIn("actively review", output["additionalContext"])
        self.assertIn("corrections", output["additionalContext"])
        self.assertIn("missing steps", output["additionalContext"])
        self.assertIn("repeated workflows", output["additionalContext"])
        self.assertIn("Do not stop at classification", output["additionalContext"])
        self.assertIn("skills.write_approval", output["additionalContext"])
        self.assertIn("autonomously", output["additionalContext"])
        self.assertLessEqual(len(output["additionalContext"]), 500)

    def test_prompt_submit_surfaces_enabled_write_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            (temporary_path / "config.yaml").write_text(
                "skills:\n  write_approval: TRUE\n",
                encoding="utf-8",
            )

            result = self.run_hook("prompt-submit", cwd=temporary_path)

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        context = payload["hookSpecificOutput"]["additionalContext"]
        self.assertIn("skills.write_approval=true", context)
        self.assertIn("updates and creations", context)
        self.assertIn("owner review", context)

    def test_prompt_submit_fails_safe_for_invalid_write_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            (temporary_path / "config.yaml").write_text(
                "skills:\n  write_approval: invalid\n",
                encoding="utf-8",
            )

            result = self.run_hook("prompt-submit", cwd=temporary_path)

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        context = payload["hookSpecificOutput"]["additionalContext"]
        self.assertIn("skills.write_approval=true", context)
        self.assertIn("owner review", context)

    def test_prompt_submit_defaults_to_autonomous_without_config(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.run_hook("prompt-submit", cwd=Path(temporary))

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        context = payload["hookSpecificOutput"]["additionalContext"]
        self.assertIn("skills.write_approval=false", context)
        self.assertIn("updates and creations", context)
        self.assertIn("autonomously", context)

    def test_unrelated_event_is_ignored(self) -> None:
        result = self.run_hook("post-tool-use")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_both_runtimes_call_the_shared_hook(self) -> None:
        codex = json.loads((ROOT / ".codex/hooks.json").read_text(encoding="utf-8"))
        claude = json.loads(
            (ROOT / ".claude/settings.json").read_text(encoding="utf-8")
        )

        expected = {
            "SessionStart": "sh hooks/nova_context.sh session-start",
            "UserPromptSubmit": "sh hooks/nova_context.sh prompt-submit",
        }
        for config in (codex, claude):
            with self.subTest(config=config):
                events = config["hooks"]
                self.assertEqual(set(events), set(expected))
                for event, registrations in events.items():
                    command = registrations[0]["hooks"][0]["command"]
                    self.assertEqual(command, expected[event])
                    self.assertNotIn("python", command)

    def test_claude_imports_the_canonical_instructions(self) -> None:
        self.assertEqual((ROOT / "CLAUDE.md").read_text(encoding="utf-8"), "@AGENTS.md\n")


if __name__ == "__main__":
    unittest.main()
