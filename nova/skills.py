"""Portable discovery for Nova's canonical skill library."""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence


SKILL_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_DESCRIPTION_CHARS = 1_024


class InvalidSkill(ValueError):
    """Raised when a canonical skill cannot be indexed safely."""


@dataclass(frozen=True)
class SkillMetadata:
    name: str
    description: str
    path: str


def discover_skills(root: Path | str) -> tuple[SkillMetadata, ...]:
    """Read and validate metadata for every canonical Nova skill."""

    root_path = Path(root).resolve()
    result = []
    names = set()

    for skill_path in sorted((root_path / "skills").glob("*/SKILL.md")):
        fields = _frontmatter(skill_path)
        name = fields.get("name", "")
        description = fields.get("description", "")

        if not SKILL_NAME.fullmatch(name):
            raise InvalidSkill(f"Invalid skill name in {skill_path}")
        if name != skill_path.parent.name:
            raise InvalidSkill(
                f"Skill name {name!r} does not match directory {skill_path.parent.name!r}"
            )
        if name in names:
            raise InvalidSkill(f"Duplicate skill name: {name}")
        if not description or len(description) > MAX_DESCRIPTION_CHARS:
            raise InvalidSkill(
                f"Skill description for {name!r} must contain 1 to "
                f"{MAX_DESCRIPTION_CHARS} characters"
            )

        result.append(
            SkillMetadata(
                name=name,
                description=description,
                path=str(skill_path.resolve()),
            )
        )
        names.add(name)

    return tuple(result)


def write_skill_index(
    root: Path | str,
    output: Path | str | None = None,
) -> Path:
    """Atomically write the disposable runtime skill index."""

    root_path = Path(root).resolve()
    output_path = (
        Path(output).resolve()
        if output is not None
        else root_path / ".runtime" / "skill-index.json"
    )
    content = json.dumps(
        [asdict(skill) for skill in discover_skills(root_path)],
        ensure_ascii=False,
        indent=2,
    ) + "\n"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=output_path.parent,
        prefix=f".{output_path.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, output_path)
    finally:
        temporary_path.unlink(missing_ok=True)
    return output_path


def _frontmatter(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise InvalidSkill(f"Missing YAML frontmatter in {path}")

    fields = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        match = re.match(r"^(name|description):\s*(.*)$", line)
        if match:
            fields[match.group(1)] = _scalar(match.group(2), path)
    else:
        raise InvalidSkill(f"Unclosed YAML frontmatter in {path}")

    return fields


def _scalar(value: str, path: Path) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"\"", "'"}:
        value = value[1:-1]
    if not value or value in {">", "|"}:
        raise InvalidSkill(f"name and description must be single-line values in {path}")
    return value.strip()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build Nova's runtime skill index")
    parser.add_argument(
        "--root",
        default=os.environ.get("NOVA_HOME", "."),
        help="Nova root. Defaults to NOVA_HOME or the current directory.",
    )
    parser.add_argument("--output", help="Optional index destination")
    arguments = parser.parse_args(argv)
    path = write_skill_index(arguments.root, arguments.output)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
