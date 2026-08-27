from __future__ import annotations

import io
import shutil
import subprocess
import tarfile
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

    def create_nova_from_tag(self, tag: str) -> Path:
        working_nova = self.temporary_path / f"nova-{tag}"
        archive = subprocess.run(
            ["git", "archive", "--format=tar", tag],
            cwd=ROOT,
            capture_output=True,
            check=True,
        ).stdout
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as release:
            release.extractall(working_nova, filter="data")
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
        subprocess.run(["git", "add", "--all"], cwd=working_nova, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", f"Install Nova {tag}"],
            cwd=working_nova,
            check=True,
        )
        return working_nova

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

    def test_pre_commit_detects_a_secret_after_a_nul_byte(self) -> None:
        working_nova = self.create_working_nova()
        fake_token = "ghp_" + ("N" * 36)
        (working_nova / "binary-note.bin").write_bytes(
            b"binary-prefix\0" + fake_token.encode() + b"\n"
        )
        subprocess.run(
            ["git", "add", "binary-note.bin"], cwd=working_nova, check=True
        )

        result = self.run_command(
            "git", "commit", "-m", "Save binary note", cwd=working_nova
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("GitHub token", result.stderr)
        self.assertNotIn(fake_token, result.stdout + result.stderr)

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

    def test_pre_commit_blocks_a_case_variant_sensitive_filename(self) -> None:
        working_nova = self.create_working_nova()
        credentials_file = working_nova / "CREDENTIALS.JSON"
        credentials_file.write_text("{}\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", "-f", "CREDENTIALS.JSON"],
            cwd=working_nova,
            check=True,
        )

        result = self.run_command(
            "git", "commit", "-m", "Save credentials", cwd=working_nova
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("blocked sensitive filename", result.stderr)

    def test_pre_commit_fails_closed_when_a_staged_blob_cannot_be_read(self) -> None:
        working_nova = self.create_working_nova()
        source = working_nova / "temporary-content"
        source.write_text("safe content\n", encoding="utf-8")
        object_id = self.run_command(
            "git", "hash-object", "-w", "temporary-content", cwd=working_nova
        ).stdout.strip()
        subprocess.run(
            [
                "git",
                "update-index",
                "--add",
                "--cacheinfo",
                "100644",
                object_id,
                "missing.md",
            ],
            cwd=working_nova,
            check=True,
        )
        source.unlink()
        object_path = working_nova / ".git" / "objects" / object_id[:2] / object_id[2:]
        object_path.unlink()

        result = self.run_command(
            "sh", "bin/nova-safety", "pre-commit", cwd=working_nova
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("could not read staged file", result.stderr)

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

    def test_pre_push_blocks_an_unapproved_deletion(self) -> None:
        working_nova = self.create_working_nova()
        remote = self.create_bare_remote("unapproved-deletion.git")
        subprocess.run(
            ["git", "remote", "add", "origin", str(remote)],
            cwd=working_nova,
            check=True,
        )
        seeded = self.run_command(
            "git", "push", "--no-verify", "origin", "main", cwd=working_nova
        )
        self.assertEqual(seeded.returncode, 0, seeded.stderr)

        result = self.run_command(
            "git", "push", "origin", ":main", cwd=working_nova
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("has not been approved", result.stderr)
        self.assertIn(
            "refs/heads/main",
            self.run_command("git", "show-ref", cwd=remote).stdout,
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

    def test_history_scan_detects_a_secret_after_a_nul_byte(self) -> None:
        working_nova = self.create_working_nova()
        fake_token = "ghp_" + ("B" * 36)
        (working_nova / "binary-history.bin").write_bytes(
            b"binary-prefix\0" + fake_token.encode() + b"\n"
        )
        subprocess.run(
            ["git", "add", "binary-history.bin"], cwd=working_nova, check=True
        )
        subprocess.run(
            ["git", "commit", "-q", "--no-verify", "-m", "Save binary history"],
            cwd=working_nova,
            check=True,
        )
        remote = self.create_bare_remote("binary-history.git")
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
        self.assertIn("GitHub token", result.stderr)
        self.assertNotIn(fake_token, result.stdout + result.stderr)

    def test_pre_push_blocks_a_secret_in_a_commit_pushed_by_raw_sha(self) -> None:
        working_nova = self.create_working_nova()
        remote = self.create_bare_remote("raw-sha.git")
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
        self.assertEqual(approval.returncode, 0, approval.stderr)

        fake_token = "ghp_" + ("R" * 36)
        (working_nova / "dangling.md").write_text(
            f"temporary token {fake_token}\n", encoding="utf-8"
        )
        subprocess.run(["git", "add", "dangling.md"], cwd=working_nova, check=True)
        subprocess.run(
            ["git", "commit", "-q", "--no-verify", "-m", "Create dangling secret"],
            cwd=working_nova,
            check=True,
        )
        secret_commit = self.run_command(
            "git", "rev-parse", "HEAD", cwd=working_nova
        ).stdout.strip()
        reset = self.run_command("git", "reset", "--hard", "HEAD^", cwd=working_nova)
        self.assertEqual(reset.returncode, 0, reset.stderr)

        result = self.run_command(
            "git",
            "push",
            "origin",
            f"{secret_commit}:refs/heads/leak",
            cwd=working_nova,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("GitHub token", result.stderr)
        self.assertNotIn(fake_token, result.stdout + result.stderr)
        self.assertEqual(self.run_command("git", "show-ref", cwd=remote).stdout, "")

    def test_history_scan_blocks_a_secret_introduced_only_by_a_merge(self) -> None:
        working_nova = self.create_working_nova()
        subprocess.run(
            ["git", "switch", "-q", "-c", "topic"], cwd=working_nova, check=True
        )
        (working_nova / "choice.md").write_text("topic\n", encoding="utf-8")
        subprocess.run(["git", "add", "choice.md"], cwd=working_nova, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "Add topic choice"],
            cwd=working_nova,
            check=True,
        )
        subprocess.run(["git", "switch", "-q", "main"], cwd=working_nova, check=True)
        (working_nova / "choice.md").write_text("main\n", encoding="utf-8")
        subprocess.run(["git", "add", "choice.md"], cwd=working_nova, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "Add main choice"],
            cwd=working_nova,
            check=True,
        )
        merge = self.run_command(
            "git", "merge", "--no-commit", "topic", cwd=working_nova
        )
        self.assertNotEqual(merge.returncode, 0)
        fake_token = "xoxb-" + ("M" * 24)
        (working_nova / "choice.md").write_text(
            f"resolved with {fake_token}\n", encoding="utf-8"
        )
        subprocess.run(["git", "add", "choice.md"], cwd=working_nova, check=True)
        subprocess.run(
            ["git", "commit", "-q", "--no-verify", "-m", "Resolve choices"],
            cwd=working_nova,
            check=True,
        )
        remote = self.create_bare_remote("merge.git")
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
        self.assertIn("Slack token", result.stderr)
        self.assertNotIn(fake_token, result.stdout + result.stderr)

    def test_history_scan_checks_filenames_in_a_tree_tag(self) -> None:
        working_nova = self.create_working_nova()
        (working_nova / ".Env").write_text("safe content\n", encoding="utf-8")
        subprocess.run(["git", "add", "-f", ".Env"], cwd=working_nova, check=True)
        tree_id = self.run_command(
            "git", "write-tree", cwd=working_nova
        ).stdout.strip()
        subprocess.run(
            ["git", "update-ref", "refs/tags/tree-backup", tree_id],
            cwd=working_nova,
            check=True,
        )
        remote = self.create_bare_remote("tree-tag.git")
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
        self.assertIn("blocked sensitive filename in Git history", result.stderr)

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

    def test_ssh_url_with_a_username_is_not_treated_as_embedded_credentials(
        self,
    ) -> None:
        working_nova = self.create_working_nova()
        subprocess.run(
            [
                "git",
                "remote",
                "add",
                "origin",
                "ssh://git@github.com/example/nova.git",
            ],
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

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Approved private backup remote", result.stdout)

    def test_approval_uses_the_effective_push_url(self) -> None:
        working_nova = self.create_working_nova()
        fetch_remote = self.create_bare_remote("fetch.git")
        push_remote = self.create_bare_remote("push.git")
        subprocess.run(
            ["git", "remote", "add", "origin", str(fetch_remote)],
            cwd=working_nova,
            check=True,
        )
        subprocess.run(
            ["git", "remote", "set-url", "--add", "--push", "origin", str(push_remote)],
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
            "git", "push", "origin", "main", cwd=working_nova
        )

        self.assertEqual(approval.returncode, 0, approval.stderr)
        self.assertIn(str(push_remote), approval.stdout)
        self.assertNotIn(str(fetch_remote), approval.stdout)
        self.assertEqual(pushed.returncode, 0, pushed.stderr)

    def test_adding_an_unapproved_pushurl_blocks_every_destination(self) -> None:
        working_nova = self.create_working_nova()
        first_remote = self.create_bare_remote("first-push.git")
        second_remote = self.create_bare_remote("second-push.git")
        subprocess.run(
            ["git", "remote", "add", "origin", str(first_remote)],
            cwd=working_nova,
            check=True,
        )
        subprocess.run(
            [
                "git",
                "remote",
                "set-url",
                "--add",
                "--push",
                "origin",
                str(first_remote),
            ],
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
            [
                "git",
                "remote",
                "set-url",
                "--add",
                "--push",
                "origin",
                str(second_remote),
            ],
            cwd=working_nova,
            check=True,
        )

        result = self.run_command(
            "git", "push", "origin", "main", cwd=working_nova
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("has not been approved", result.stderr)
        self.assertEqual(self.run_command("git", "show-ref", cwd=first_remote).stdout, "")
        self.assertEqual(self.run_command("git", "show-ref", cwd=second_remote).stdout, "")

    def test_copied_public_source_marker_does_not_bypass_remote_approval(self) -> None:
        working_nova = self.create_working_nova()
        (working_nova / ".nova-public-source").write_text(
            "Nova public source: https://github.com/thefactus/nova\n",
            encoding="utf-8",
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

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("has not been approved", result.stderr)

    def test_official_public_source_identity_bypasses_private_remote_approval(
        self,
    ) -> None:
        working_nova = self.create_working_nova()
        (working_nova / ".nova-public-source").write_text(
            "Nova public source: https://github.com/thefactus/nova\n",
            encoding="utf-8",
        )
        subprocess.run(
            ["git", "add", ".nova-public-source"], cwd=working_nova, check=True
        )
        subprocess.run(
            ["git", "commit", "-q", "-m", "Mark official public source"],
            cwd=working_nova,
            check=True,
        )
        official_url = "https://github.com/thefactus/nova.git"
        subprocess.run(
            ["git", "remote", "add", "origin", official_url],
            cwd=working_nova,
            check=True,
        )
        local_oid = self.run_command(
            "git", "rev-parse", "HEAD", cwd=working_nova
        ).stdout.strip()
        update = f"refs/heads/main {local_oid} refs/heads/main {'0' * 40}\n"

        result = self.run_command(
            "sh",
            "bin/nova-safety",
            "pre-push",
            "origin",
            official_url,
            cwd=working_nova,
            input_text=update,
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_official_public_source_can_delete_without_private_approval(self) -> None:
        working_nova = self.create_working_nova()
        (working_nova / ".nova-public-source").write_text(
            "Nova public source: https://github.com/thefactus/nova\n",
            encoding="utf-8",
        )
        subprocess.run(
            ["git", "add", ".nova-public-source"], cwd=working_nova, check=True
        )
        subprocess.run(
            ["git", "commit", "-q", "-m", "Mark official public source"],
            cwd=working_nova,
            check=True,
        )
        official_url = "https://github.com/thefactus/nova.git"
        subprocess.run(
            ["git", "remote", "add", "origin", official_url],
            cwd=working_nova,
            check=True,
        )
        old_oid = self.run_command(
            "git", "rev-parse", "HEAD", cwd=working_nova
        ).stdout.strip()
        update = f"(delete) {'0' * len(old_oid)} refs/heads/old {old_oid}\n"

        result = self.run_command(
            "sh",
            "bin/nova-safety",
            "pre-push",
            "origin",
            official_url,
            cwd=working_nova,
            input_text=update,
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_push_by_url_fails_with_actionable_guidance(self) -> None:
        working_nova = self.create_working_nova()
        remote = self.create_bare_remote("direct-url.git")

        result = self.run_command(
            "git", "push", str(remote), "main", cwd=working_nova
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("configure and approve a named remote", result.stderr)

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

    def test_version_016_can_receive_and_enable_the_new_safety_guard(self) -> None:
        working_nova = self.create_nova_from_tag("v0.1.6")
        owner_memory = working_nova / "memories" / "USER.md"
        owner_memory.write_text("Keep this owner preference.\n", encoding="utf-8")
        owner_skill = working_nova / "skills" / "owner-workflow" / "SKILL.md"
        owner_skill.parent.mkdir()
        owner_skill.write_text("# Owner workflow\n", encoding="utf-8")
        owner_config = "skills:\n  write_approval: true\n"
        (working_nova / "config.yaml").write_text(owner_config, encoding="utf-8")
        subprocess.run(
            ["git", "add", "memories/USER.md", "skills/owner-workflow", "config.yaml"],
            cwd=working_nova,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-q", "-m", "Adapt my Nova"],
            cwd=working_nova,
            check=True,
        )
        remote = self.create_bare_remote("existing-v016.git")
        subprocess.run(
            ["git", "remote", "add", "origin", str(remote)],
            cwd=working_nova,
            check=True,
        )

        shutil.copytree(ROOT / "bin", working_nova / "bin", dirs_exist_ok=True)
        shutil.copytree(
            ROOT / ".githooks", working_nova / ".githooks", dirs_exist_ok=True
        )
        enabled = self.run_command(
            "sh", "bin/nova-safety", "enable", cwd=working_nova
        )

        self.assertEqual(enabled.returncode, 0, enabled.stderr)
        self.assertEqual(
            self.run_command(
                "git", "config", "--get", "core.hooksPath", cwd=working_nova
            ).stdout.strip(),
            ".githooks",
        )
        self.assertEqual(
            owner_memory.read_text(encoding="utf-8"),
            "Keep this owner preference.\n",
        )
        self.assertEqual(owner_skill.read_text(encoding="utf-8"), "# Owner workflow\n")
        self.assertEqual(
            (working_nova / "config.yaml").read_text(encoding="utf-8"),
            owner_config,
        )
        self.assertEqual(
            self.run_command(
                "git", "remote", "get-url", "origin", cwd=working_nova
            ).stdout.strip(),
            str(remote),
        )
        self.assertFalse((working_nova / ".nova-public-source").exists())
        self.assertTrue((working_nova / "bin/nova-safety").stat().st_mode & 0o100)
        self.assertTrue((working_nova / ".githooks/pre-push").stat().st_mode & 0o100)


if __name__ == "__main__":
    unittest.main()
