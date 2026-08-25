from __future__ import annotations

import hashlib
import io
import os
import stat
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "install.sh"
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()


class InstallerTest(unittest.TestCase):
    def create_fake_release(self, directory: Path, *, valid_checksum: bool = True) -> Path:
        release_directory = directory / f"v{VERSION}"
        release_directory.mkdir(parents=True)
        archive_name = f"nova-v{VERSION}.tar.gz"
        archive_path = release_directory / archive_name

        with tarfile.open(archive_path, "w:gz") as archive:
            files = {
                "VERSION": f"{VERSION}\n",
                "AGENTS.md": "# Nova\n",
                "memories/USER.md": "",
            }
            for relative_path, content in files.items():
                data = content.encode()
                info = tarfile.TarInfo(f"nova-v{VERSION}/{relative_path}")
                info.size = len(data)
                info.mode = 0o644
                archive.addfile(info, io.BytesIO(data))

        checksum = hashlib.sha256(archive_path.read_bytes()).hexdigest()
        if not valid_checksum:
            checksum = "0" * 64
        (release_directory / f"{archive_name}.sha256").write_text(
            f"{checksum}  {archive_name}\n",
            encoding="utf-8",
        )
        return release_directory

    def run_installer(
        self, release_root: Path, destination: Path | None, home: Path
    ) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment.update(
            {
                "GIT_CONFIG_NOSYSTEM": "1",
                "HOME": str(home),
                "NOVA_RELEASE_BASE_URL": release_root.as_uri(),
            }
        )
        for name in (
            "GIT_AUTHOR_NAME",
            "GIT_AUTHOR_EMAIL",
            "GIT_COMMITTER_NAME",
            "GIT_COMMITTER_EMAIL",
        ):
            environment.pop(name, None)

        command = ["/bin/sh", str(INSTALLER)]
        if destination is not None:
            command.append(str(destination))

        return subprocess.run(
            command,
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_installs_release_as_a_new_local_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            release_root = temporary_path / "releases"
            self.create_fake_release(release_root)
            home = temporary_path / "home"
            destination = home / "nova"

            result = self.run_installer(release_root, None, home)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                (destination / "VERSION").read_text(encoding="utf-8"),
                f"{VERSION}\n",
            )
            self.assertEqual(
                subprocess.run(
                    ["git", "-C", str(destination), "branch", "--show-current"],
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip(),
                "main",
            )
            self.assertEqual(
                subprocess.run(
                    ["git", "-C", str(destination), "log", "-1", "--pretty=%s"],
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip(),
                "Start my Nova",
            )
            self.assertEqual(
                subprocess.run(
                    ["git", "-C", str(destination), "remote"],
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout,
                "",
            )
            self.assertEqual(
                subprocess.run(
                    ["git", "-C", str(destination), "status", "--short"],
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout,
                "",
            )
            self.assertEqual(
                stat.S_IMODE(destination.stat().st_mode) & 0o077,
                0,
            )

    def test_refuses_to_replace_an_existing_destination(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            release_root = temporary_path / "releases"
            self.create_fake_release(release_root)
            destination = temporary_path / "owner-nova"
            destination.mkdir()
            sentinel = destination / "keep.txt"
            sentinel.write_text("keep\n", encoding="utf-8")

            result = self.run_installer(
                release_root, destination, temporary_path / "home"
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("destination already exists", result.stderr)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep\n")

    def test_installs_at_an_explicit_destination(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            release_root = temporary_path / "releases"
            self.create_fake_release(release_root)
            home = temporary_path / "home"
            destination = temporary_path / "custom path" / "owner's nova"

            result = self.run_installer(release_root, destination, home)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                (destination / "VERSION").read_text(encoding="utf-8"),
                f"{VERSION}\n",
            )
            self.assertTrue((destination / ".git").is_dir())
            self.assertFalse((home / "nova").exists())
            self.assertIn(f"ready at {destination}", result.stdout)
            cd_command = next(
                line.strip()
                for line in result.stdout.splitlines()
                if line.strip().startswith("cd ")
            )
            changed_directory = subprocess.run(
                ["/bin/sh", "-c", f"{cd_command}\npwd"],
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(changed_directory.stdout.strip(), str(destination))
            self.assertIn(
                "Start your coding agent from that directory.", result.stdout
            )

    def test_rejects_a_release_with_the_wrong_checksum(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            release_root = temporary_path / "releases"
            self.create_fake_release(release_root, valid_checksum=False)
            destination = temporary_path / "owner-nova"

            result = self.run_installer(
                release_root, destination, temporary_path / "home"
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("checksum does not match", result.stderr)
            self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
