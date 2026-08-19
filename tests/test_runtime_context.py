from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "nova_context.sh"


class RuntimeContextTest(unittest.TestCase):
    def run_hook(self, mode: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["/bin/sh", str(HOOK), mode],
            cwd=ROOT,
            input="{}",
            capture_output=True,
            text=True,
            check=False,
        )

    def test_session_start_returns_context_without_building_an_index(self) -> None:
        index_path = ROOT / ".runtime" / "skill-index.json"
        index_path.unlink(missing_ok=True)

        result = self.run_hook("session-start")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        output = payload["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "SessionStart")
        self.assertIn("memories/USER.md", output["additionalContext"])
        self.assertIn("skills/", output["additionalContext"])
        self.assertFalse(index_path.exists())

    def test_prompt_submit_returns_skill_routing_context(self) -> None:
        result = self.run_hook("prompt-submit")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        output = payload["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "UserPromptSubmit")
        self.assertIn("skills/", output["additionalContext"])
        self.assertIn("durable learning", output["additionalContext"])

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
