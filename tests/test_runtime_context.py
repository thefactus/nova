from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "nova_context.sh"
LEARNING_STATE = ROOT / ".runtime" / "learning"


class RuntimeContextTest(unittest.TestCase):
    def setUp(self) -> None:
        shutil.rmtree(LEARNING_STATE, ignore_errors=True)

    def tearDown(self) -> None:
        shutil.rmtree(LEARNING_STATE, ignore_errors=True)

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

    def prepare_fixture(self, root: Path, config: str) -> Path:
        hook_path = root / "hooks" / "nova_context.sh"
        hook_path.parent.mkdir(parents=True)
        hook_path.write_text(HOOK.read_text(encoding="utf-8"), encoding="utf-8")
        (root / "config.yaml").write_text(config, encoding="utf-8")
        return hook_path

    def run_fixture_hook(
        self, root: Path, hook_path: Path, mode: str
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["/bin/sh", str(hook_path), mode],
            cwd=root,
            input="{}",
            capture_output=True,
            text=True,
            check=False,
        )

    def test_periodic_review_is_injected_after_turn_interval(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            hook_path = self.prepare_fixture(
                root,
                "learning:\n"
                "  periodic_review:\n"
                "    enabled: true\n"
                "    turn_interval: 2\n"
                "    action_interval: 100\n",
            )

            first_prompt = self.run_fixture_hook(root, hook_path, "prompt-submit")
            first_stop = self.run_fixture_hook(root, hook_path, "stop")
            second_prompt = self.run_fixture_hook(root, hook_path, "prompt-submit")
            second_stop = self.run_fixture_hook(root, hook_path, "stop")
            due_path = root / ".runtime" / "learning" / "review-due"
            due_before_next_prompt = due_path.exists()
            review_prompt = self.run_fixture_hook(root, hook_path, "prompt-submit")
            due_after_next_prompt = due_path.exists()

            turn_count = (
                root / ".runtime" / "learning" / "turn-count"
            ).read_text(encoding="utf-8")

        for result in (first_prompt, first_stop, second_prompt, second_stop):
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(due_before_next_prompt)
        context = json.loads(review_prompt.stdout)["hookSpecificOutput"][
            "additionalContext"
        ]
        self.assertIn("Periodic learning review is due", context)
        self.assertFalse(due_after_next_prompt)
        self.assertEqual(turn_count, "1\n")

    def test_periodic_review_is_injected_after_action_interval(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            hook_path = self.prepare_fixture(
                root,
                "learning:\n"
                "  periodic_review:\n"
                "    enabled: true\n"
                "    turn_interval: 100\n"
                "    action_interval: 2\n",
            )

            first_action = self.run_fixture_hook(root, hook_path, "post-tool-use")
            second_action = self.run_fixture_hook(root, hook_path, "post-tool-use")
            stop = self.run_fixture_hook(root, hook_path, "stop")
            review_prompt = self.run_fixture_hook(root, hook_path, "prompt-submit")

        for result in (first_action, second_action, stop, review_prompt):
            self.assertEqual(result.returncode, 0, result.stderr)
        context = json.loads(review_prompt.stdout)["hookSpecificOutput"][
            "additionalContext"
        ]
        self.assertIn("Periodic learning review is due", context)

    def test_periodic_review_can_be_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            hook_path = self.prepare_fixture(
                root,
                "learning:\n"
                "  periodic_review:\n"
                "    enabled: false\n"
                "    turn_interval: 1\n"
                "    action_interval: 1\n",
            )

            prompt = self.run_fixture_hook(root, hook_path, "prompt-submit")
            action = self.run_fixture_hook(root, hook_path, "post-tool-use")
            stop = self.run_fixture_hook(root, hook_path, "stop")

            state_exists = (root / ".runtime" / "learning").exists()

        for result in (prompt, action, stop):
            self.assertEqual(result.returncode, 0, result.stderr)
        context = json.loads(prompt.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertNotIn("Periodic learning review is due", context)
        self.assertFalse(state_exists)

    def test_parallel_actions_are_counted_without_lost_updates(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            hook_path = self.prepare_fixture(
                root,
                "learning:\n"
                "  periodic_review:\n"
                "    enabled: true\n"
                "    turn_interval: 100\n"
                "    action_interval: 20\n",
            )

            processes = [
                subprocess.Popen(
                    ["/bin/sh", str(hook_path), "post-tool-use"],
                    cwd=root,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                for _ in range(20)
            ]
            results = [process.communicate(timeout=10) for process in processes]
            return_codes = [process.returncode for process in processes]
            action_count = (
                root / ".runtime" / "learning" / "action-count"
            ).read_text(encoding="utf-8")
            stop = self.run_fixture_hook(root, hook_path, "stop")
            review_due = (root / ".runtime" / "learning" / "review-due").exists()

        self.assertEqual(return_codes, [0] * 20, results)
        self.assertEqual(action_count, "20\n")
        self.assertEqual(stop.returncode, 0, stop.stderr)
        self.assertTrue(review_due)

    def test_stale_learning_lock_is_recovered(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            hook_path = self.prepare_fixture(root, "")
            lock_path = root / ".runtime" / "learning" / "lock"
            lock_path.mkdir(parents=True)
            (lock_path / "owner").write_text("999999999\n", encoding="utf-8")

            result = self.run_fixture_hook(root, hook_path, "prompt-submit")
            turn_count = (
                root / ".runtime" / "learning" / "turn-count"
            ).read_text(encoding="utf-8")
            lock_exists = lock_path.exists()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(turn_count, "1\n")
        self.assertFalse(lock_exists)

    def test_unrelated_event_is_ignored(self) -> None:
        result = self.run_hook("unrelated-event")

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
            "PostToolUse": "sh hooks/nova_context.sh post-tool-use",
            "Stop": "sh hooks/nova_context.sh stop",
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
