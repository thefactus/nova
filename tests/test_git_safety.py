from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class GitSafetyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.temporary_path = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def run_command(
        self,
        *command: str,
        cwd: Path,
        input_text: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            command,
            cwd=cwd,
            input=input_text,
            capture_output=True,
            text=True,
            check=False,
        )

    def create_working_nova(self, *, enable_hooks: bool = True) -> Path:
        working_nova = self.temporary_path / "working-nova"
        working_nova.mkdir()
        shutil.copytree(ROOT / "bin", working_nova / "bin")
        shutil.copytree(ROOT / ".githooks", working_nova / ".githooks")
        subprocess.run(
            ["git", "init", "-q", "-b", "main"], cwd=working_nova, check=True
        )
        subprocess.run(
            ["git", "config", "user.name", "Nova Test"],
            cwd=working_nova,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "nova-test@localhost"],
            cwd=working_nova,
            check=True,
        )
        if enable_hooks:
            subprocess.run(
                ["git", "config", "core.hooksPath", ".githooks"],
                cwd=working_nova,
                check=True,
            )
        (working_nova / "README.md").write_text("# My Nova\n", encoding="utf-8")
        subprocess.run(["git", "add", "--all"], cwd=working_nova, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "Start my Nova"],
            cwd=working_nova,
            check=True,
        )
        return working_nova

    def create_bare_remote(self, name: str) -> Path:
        remote = self.temporary_path / name
        subprocess.run(["git", "init", "-q", "--bare", remote], check=True)
        return remote

    def test_pre_commit_allows_safe_content(self) -> None:
        working_nova = self.create_working_nova()
        (working_nova / "memories.md").write_text(
            "Prefer concise explanations.\n", encoding="utf-8"
        )
        subprocess.run(["git", "add", "memories.md"], cwd=working_nova, check=True)

        result = self.run_command(
            "git", "commit", "-m", "Remember writing preference", cwd=working_nova
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_pre_commit_blocks_a_secret_without_printing_it(self) -> None:
        working_nova = self.create_working_nova()
        fake_token = "ghp_" + ("A" * 36)
        (working_nova / "private-note.md").write_text(
            f"temporary token {fake_token}\n", encoding="utf-8"
        )
        subprocess.run(
            ["git", "add", "private-note.md"], cwd=working_nova, check=True
        )

        result = self.run_command(
            "git", "commit", "-m", "Save private note", cwd=working_nova
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("GitHub token", result.stderr)
        self.assertNotIn(fake_token, result.stdout + result.stderr)
        self.assertEqual(
            self.run_command(
                "git", "log", "-1", "--pretty=%s", cwd=working_nova
            ).stdout.strip(),
            "Start my Nova",
        )

    def test_pre_commit_blocks_a_credential_like_password(self) -> None:
        working_nova = self.create_working_nova()
        fake_password = "tokenvalue" + ("7" * 20)
        (working_nova / "daily.md").write_text(
            f"password {fake_password}\n", encoding="utf-8"
        )
        subprocess.run(["git", "add", "daily.md"], cwd=working_nova, check=True)

        result = self.run_command(
            "git", "commit", "-m", "Save daily", cwd=working_nova
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("credential-like assignment", result.stderr)
        self.assertNotIn(fake_password, result.stdout + result.stderr)

    def test_pre_commit_blocks_a_sensitive_filename(self) -> None:
        working_nova = self.create_working_nova()
        credentials_file = working_nova / "credentials.json"
        credentials_file.write_text("{}\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", "-f", "credentials.json"],
            cwd=working_nova,
            check=True,
        )

        result = self.run_command(
            "git", "commit", "-m", "Save credentials", cwd=working_nova
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("blocked sensitive filename", result.stderr)

    def test_pre_push_blocks_an_unapproved_remote(self) -> None:
        working_nova = self.create_working_nova()
        remote = self.create_bare_remote("unapproved.git")
        subprocess.run(
            ["git", "remote", "add", "origin", str(remote)],
            cwd=working_nova,
            check=True,
        )

        result = self.run_command(
            "git", "push", "-u", "origin", "main", cwd=working_nova
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("has not been approved", result.stderr)
        self.assertEqual(
            self.run_command("git", "show-ref", cwd=remote).stdout,
            "",
        )

    def test_approved_private_remote_can_receive_a_clean_history(self) -> None:
        working_nova = self.create_working_nova()
        remote = self.create_bare_remote("private.git")
        subprocess.run(
            ["git", "remote", "add", "origin", str(remote)],
            cwd=working_nova,
            check=True,
        )

        approval = self.run_command(
            "sh",
            "bin/nova-safety",
            "approve",
            "origin",
            cwd=working_nova,
            input_text="PRIVATE\n",
        )
        pushed = self.run_command(
            "git", "push", "-u", "origin", "main", cwd=working_nova
        )

        self.assertEqual(approval.returncode, 0, approval.stderr)
        self.assertIn("Approved private backup remote", approval.stdout)
        self.assertEqual(pushed.returncode, 0, pushed.stderr)
        self.assertIn(
            "refs/heads/main",
            self.run_command("git", "show-ref", cwd=remote).stdout,
        )

    def test_pre_push_blocks_a_secret_retained_only_in_history(self) -> None:
        working_nova = self.create_working_nova()
        fake_token = "xoxb-" + ("9" * 24)
        note = working_nova / "daily.md"
        note.write_text(f"temporary token {fake_token}\n", encoding="utf-8")
        subprocess.run(["git", "add", "daily.md"], cwd=working_nova, check=True)
        subprocess.run(
            ["git", "commit", "-q", "--no-verify", "-m", "Save temporary token"],
            cwd=working_nova,
            check=True,
        )
        note.write_text("temporary token [REDACTED]\n", encoding="utf-8")
        subprocess.run(["git", "add", "daily.md"], cwd=working_nova, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "Redact temporary token"],
            cwd=working_nova,
            check=True,
        )
        remote = self.create_bare_remote("history.git")
        subprocess.run(
            ["git", "remote", "add", "origin", str(remote)],
            cwd=working_nova,
            check=True,
        )

        result = self.run_command(
            "sh",
            "bin/nova-safety",
            "approve",
            "origin",
            cwd=working_nova,
            input_text="PRIVATE\n",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("retained in Git history", result.stderr)
        self.assertNotIn(fake_token, result.stdout + result.stderr)

    def test_changing_the_remote_url_invalidates_approval(self) -> None:
        working_nova = self.create_working_nova()
        first_remote = self.create_bare_remote("first-private.git")
        second_remote = self.create_bare_remote("second-private.git")
        subprocess.run(
            ["git", "remote", "add", "origin", str(first_remote)],
            cwd=working_nova,
            check=True,
        )
        approval = self.run_command(
            "sh",
            "bin/nova-safety",
            "approve",
            "origin",
            cwd=working_nova,
            input_text="PRIVATE\n",
        )
        self.assertEqual(approval.returncode, 0, approval.stderr)
        subprocess.run(
            ["git", "remote", "set-url", "origin", str(second_remote)],
            cwd=working_nova,
            check=True,
        )

        result = self.run_command(
            "git", "push", "origin", "main", cwd=working_nova
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("has not been approved", result.stderr)

    def test_remote_with_embedded_credentials_is_rejected_without_echoing_them(
        self,
    ) -> None:
        working_nova = self.create_working_nova()
        fake_password = "remote-secret-value"
        remote_url = (
            "https" + "://" + f"nova:{fake_password}@github.com/example/nova.git"
        )
        subprocess.run(
            ["git", "remote", "add", "origin", remote_url],
            cwd=working_nova,
            check=True,
        )

        result = self.run_command(
            "sh", "bin/nova-safety", "approve", "origin", cwd=working_nova
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("embedded credentials", result.stderr)
        self.assertNotIn(fake_password, result.stdout + result.stderr)

    def test_public_distribution_source_can_push_after_scanning(self) -> None:
        working_nova = self.create_working_nova()
        (working_nova / ".nova-public-source").write_text(
            "Public distribution source.\n", encoding="utf-8"
        )
        subprocess.run(
            ["git", "add", ".nova-public-source"], cwd=working_nova, check=True
        )
        subprocess.run(
            ["git", "commit", "-q", "-m", "Mark public source"],
            cwd=working_nova,
            check=True,
        )
        remote = self.create_bare_remote("public-source.git")
        subprocess.run(
            ["git", "remote", "add", "origin", str(remote)],
            cwd=working_nova,
            check=True,
        )

        result = self.run_command(
            "git", "push", "-u", "origin", "main", cwd=working_nova
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_enable_adds_hooks_without_overwriting_a_custom_path(self) -> None:
        working_nova = self.create_working_nova(enable_hooks=False)

        enabled = self.run_command(
            "sh", "bin/nova-safety", "enable", cwd=working_nova
        )
        configured_path = self.run_command(
            "git", "config", "--get", "core.hooksPath", cwd=working_nova
        ).stdout.strip()
        self.assertEqual(enabled.returncode, 0, enabled.stderr)
        self.assertEqual(configured_path, ".githooks")

        subprocess.run(
            ["git", "config", "core.hooksPath", "custom-hooks"],
            cwd=working_nova,
            check=True,
        )
        preserved = self.run_command(
            "sh", "bin/nova-safety", "enable", cwd=working_nova
        )
        configured_path = self.run_command(
            "git", "config", "--get", "core.hooksPath", cwd=working_nova
        ).stdout.strip()

        self.assertEqual(preserved.returncode, 2)
        self.assertEqual(configured_path, "custom-hooks")
        self.assertIn("was preserved", preserved.stderr)

    def test_enable_on_an_existing_nova_preserves_owner_content_and_remote(
        self,
    ) -> None:
        working_nova = self.create_working_nova(enable_hooks=False)
        owner_memory = working_nova / "memories" / "USER.md"
        owner_memory.parent.mkdir()
        owner_memory.write_text("Keep my private preference.\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", "memories/USER.md"], cwd=working_nova, check=True
        )
        subprocess.run(
            ["git", "commit", "-q", "-m", "Remember owner preference"],
            cwd=working_nova,
            check=True,
        )
        remote = self.create_bare_remote("existing-private.git")
        subprocess.run(
            ["git", "remote", "add", "origin", str(remote)],
            cwd=working_nova,
            check=True,
        )
        commits_before = self.run_command(
            "git", "rev-list", "--all", "--count", cwd=working_nova
        ).stdout

        enabled = self.run_command(
            "sh", "bin/nova-safety", "enable", cwd=working_nova
        )

        self.assertEqual(enabled.returncode, 0, enabled.stderr)
        self.assertEqual(
            owner_memory.read_text(encoding="utf-8"),
            "Keep my private preference.\n",
        )
        self.assertEqual(
            self.run_command(
                "git", "rev-list", "--all", "--count", cwd=working_nova
            ).stdout,
            commits_before,
        )
        self.assertEqual(
            self.run_command(
                "git", "remote", "get-url", "origin", cwd=working_nova
            ).stdout.strip(),
            str(remote),
        )


if __name__ == "__main__":
    unittest.main()
