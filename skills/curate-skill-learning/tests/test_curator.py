from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/curator.py"
SPEC = importlib.util.spec_from_file_location("nova_curator", SCRIPT)
assert SPEC and SPEC.loader
curator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(curator)


class CuratorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def write_proposal(self, proposal_id: str = "proposal-one") -> Path:
        path = self.root / f"learning/proposals/pending/{proposal_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        document = {
            "version": 1,
            "id": proposal_id,
            "status": "pending",
            "created_at": "2026-08-18T00:00:00+00:00",
            "source_summary": "A completed task found reusable learning.",
            "target_skill": "example-skill",
            "target_ownership": "new",
            "owner_hint": "",
            "action": "create",
            "change_summary": "Create a reusable example skill.",
            "rationale": "The workflow repeated successfully.",
            "proposed_content": "Use the verified workflow.",
            "history": [
                {
                    "status": "pending",
                    "at": "2026-08-18T00:00:00+00:00",
                    "note": "Created by a Nova learning review.",
                }
            ],
        }
        path.write_text(json.dumps(document), encoding="utf-8")
        return path

    def add_target_skill(self) -> None:
        path = self.root / "skills/example-skill/SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "---\nname: example-skill\ndescription: Example.\n---\n",
            encoding="utf-8",
        )

    def run_cli(self, *arguments: str) -> tuple[int, str, str]:
        stdout = StringIO()
        stderr = StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            result = curator.main(list(arguments), root=self.root)
        return result, stdout.getvalue(), stderr.getvalue()

    def test_status_and_list_work_with_lazy_state_directories(self) -> None:
        self.write_proposal()

        status, output, error = self.run_cli("status")
        listed, listing, _ = self.run_cli("list")

        self.assertEqual((status, error), (0, ""))
        self.assertIn("pending: 1", output)
        self.assertIn("applied: 0", output)
        self.assertEqual(listed, 0)
        self.assertIn("proposal-one", listing)

    def test_approve_requires_a_note_and_preserves_history(self) -> None:
        self.write_proposal()

        with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
            curator.main(["approve", "proposal-one"], root=self.root)

        result, _, error = self.run_cli(
            "approve", "proposal-one", "--note", "Approved by owner"
        )

        self.assertEqual((result, error), (0, ""))
        approved = self.root / "learning/proposals/approved/proposal-one.json"
        document = json.loads(approved.read_text(encoding="utf-8"))
        self.assertEqual(document["status"], "approved")
        self.assertEqual(document["history"][-1]["status"], "approved")
        self.assertFalse(
            (self.root / "learning/proposals/pending/proposal-one.json").exists()
        )

    def test_reject_can_be_reopened(self) -> None:
        self.write_proposal()
        self.run_cli("reject", "proposal-one", "--note", "Too specific")

        result, _, error = self.run_cli(
            "reopen", "proposal-one", "--note", "New evidence"
        )

        self.assertEqual((result, error), (0, ""))
        reopened = self.root / "learning/proposals/pending/proposal-one.json"
        document = json.loads(reopened.read_text(encoding="utf-8"))
        self.assertEqual(document["status"], "pending")
        self.assertEqual(
            [event["status"] for event in document["history"]],
            ["pending", "rejected", "pending"],
        )

    def test_mark_applied_requires_the_target_skill(self) -> None:
        self.write_proposal()
        self.run_cli("approve", "proposal-one", "--note", "Approved")

        result, _, error = self.run_cli(
            "mark-applied", "proposal-one", "--note", "Applied"
        )

        self.assertEqual(result, 1)
        self.assertIn("target skill does not exist", error)

    def test_mark_applied_closes_a_validated_proposal(self) -> None:
        self.write_proposal()
        self.run_cli("approve", "proposal-one", "--note", "Approved")
        self.add_target_skill()

        result, _, error = self.run_cli(
            "mark-applied", "proposal-one", "--note", "Validated and applied"
        )

        self.assertEqual((result, error), (0, ""))
        applied = self.root / "learning/proposals/applied/proposal-one.json"
        document = json.loads(applied.read_text(encoding="utf-8"))
        self.assertEqual(document["status"], "applied")

    def test_audit_detects_a_state_mismatch(self) -> None:
        path = self.write_proposal()
        document = json.loads(path.read_text(encoding="utf-8"))
        document["status"] = "approved"
        path.write_text(json.dumps(document), encoding="utf-8")

        result, _, error = self.run_cli("audit")

        self.assertEqual(result, 1)
        self.assertIn("stored under the wrong state", error)


if __name__ == "__main__":
    unittest.main()
