#!/usr/bin/env python3
"""Inspect and transition Nova skill-learning proposals safely."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


STATES = ("pending", "approved", "rejected", "applied")
TRANSITIONS = {
    "pending": {"approved", "rejected"},
    "approved": {"pending", "applied"},
    "rejected": {"pending"},
    "applied": set(),
}


def default_root() -> Path:
    configured = os.environ.get("NOVA_HOME")
    return Path(configured).resolve() if configured else Path(__file__).resolve().parents[3]


def proposals_root(root: Path) -> Path:
    return root / "learning" / "proposals"


def validate_id(proposal_id: str) -> str:
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
    if (
        not proposal_id
        or proposal_id in {".", ".."}
        or proposal_id.endswith(".json")
        or any(character not in allowed for character in proposal_id)
    ):
        raise ValueError("proposal id may contain only letters, digits, '-', '_', and '.'")
    return proposal_id


def load_document(path: Path) -> dict:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid proposal {path.name}: {error}") from error
    if not isinstance(document, dict) or document.get("id") != path.stem:
        raise ValueError(f"invalid proposal identity in {path.name}")
    if document.get("status") not in STATES:
        raise ValueError(f"invalid proposal status in {path.name}")
    if not isinstance(document.get("history"), list):
        raise ValueError(f"invalid proposal history in {path.name}")
    return document


def atomic_write(path: Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.stem}.",
        suffix=".tmp",
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(document, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def find_proposal(root: Path, proposal_id: str) -> tuple[str, Path, dict]:
    proposal_id = validate_id(proposal_id)
    matches = []
    for state in STATES:
        path = proposals_root(root) / state / f"{proposal_id}.json"
        if path.is_file():
            matches.append((state, path, load_document(path)))
    if not matches:
        raise ValueError(f"proposal not found: {proposal_id}")
    if len(matches) != 1:
        raise ValueError(f"proposal exists in multiple states: {proposal_id}")
    return matches[0]


def list_proposals(root: Path, state: str) -> list[dict]:
    directory = proposals_root(root) / state
    if not directory.exists():
        return []
    documents = []
    for path in sorted(directory.glob("*.json")):
        document = load_document(path)
        if document["status"] != state:
            raise ValueError(f"proposal {path.stem} is stored under the wrong state")
        documents.append(document)
    return documents


def find_skill(root: Path, target: str) -> Path | None:
    for path in sorted((root / "skills").glob("*/SKILL.md")):
        if path.parent.name == target:
            return path
        lines = path.read_text(encoding="utf-8").splitlines()
        if lines and lines[0] == "---":
            for line in lines[1:]:
                if line == "---":
                    break
                if line.startswith("name:") and line.removeprefix("name:").strip().strip("\"'") == target:
                    return path
    return None


def transition(root: Path, proposal_id: str, destination: str, note: str) -> Path:
    note = note.strip()
    if not note:
        raise ValueError("a transition note is required")
    source_state, source_path, document = find_proposal(root, proposal_id)
    if document["status"] != source_state:
        raise ValueError(f"proposal status does not match its {source_state} directory")
    if destination not in TRANSITIONS[source_state]:
        raise ValueError(f"cannot transition {source_state} -> {destination}")
    if destination == "applied" and find_skill(
        root, str(document.get("target_skill") or "")
    ) is None:
        raise ValueError("target skill does not exist; apply and validate it first")

    timestamp = datetime.now(timezone.utc).isoformat()
    document["status"] = destination
    document["history"].append(
        {
            "status": destination,
            "at": timestamp,
            "note": note,
        }
    )
    destination_path = proposals_root(root) / destination / source_path.name
    if destination_path.exists():
        raise ValueError(f"proposal already exists in {destination}")
    atomic_write(destination_path, document)
    source_path.unlink()
    return destination_path


def audit(root: Path) -> int:
    seen = set()
    count = 0
    for state in STATES:
        for document in list_proposals(root, state):
            proposal_id = document["id"]
            if proposal_id in seen:
                raise ValueError(f"proposal exists in multiple states: {proposal_id}")
            seen.add(proposal_id)
            count += 1
            if state == "applied" and find_skill(
                root, str(document.get("target_skill") or "")
            ) is None:
                raise ValueError(f"applied proposal target is missing: {proposal_id}")
    return count


def render(document: dict) -> str:
    return "\n".join(
        [
            f"id: {document.get('id', '')}",
            f"status: {document.get('status', '')}",
            f"action: {document.get('action', '')}",
            f"target: {document.get('target_skill', '')}",
            f"ownership: {document.get('target_ownership', '')}",
            f"created: {document.get('created_at', '')}",
            "",
            "source summary:",
            str(document.get("source_summary") or ""),
            "",
            "change summary:",
            str(document.get("change_summary") or ""),
            "",
            "rationale:",
            str(document.get("rationale") or ""),
            "",
            "proposed content:",
            str(document.get("proposed_content") or ""),
        ]
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, help="Nova root, defaults to NOVA_HOME")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("status")
    subparsers.add_parser("audit")

    listing = subparsers.add_parser("list")
    listing.add_argument("--status", choices=STATES, default="pending")

    showing = subparsers.add_parser("show")
    showing.add_argument("proposal_id")
    showing.add_argument("--json", action="store_true")

    for command in ("approve", "reject", "reopen", "mark-applied"):
        action = subparsers.add_parser(command)
        action.add_argument("proposal_id")
        action.add_argument("--note", required=True)
    return parser


def main(argv: list[str] | None = None, root: Path | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = (root or args.root or default_root()).resolve()
    try:
        if args.command == "status":
            for state in STATES:
                print(f"{state}: {len(list_proposals(root, state))}")
            return 0
        if args.command == "audit":
            print(f"ok: {audit(root)} proposals")
            return 0
        if args.command == "list":
            documents = list_proposals(root, args.status)
            if not documents:
                print(f"no {args.status} proposals")
                return 0
            for document in documents:
                print(
                    f"{document['id']}  {document.get('action', ''):6s}  "
                    f"{document.get('target_skill', '')}  "
                    f"{document.get('change_summary', '')}"
                )
            return 0
        if args.command == "show":
            _, _, document = find_proposal(root, args.proposal_id)
            if args.json:
                print(json.dumps(document, ensure_ascii=False, indent=2))
            else:
                print(render(document))
            return 0

        destination = {
            "approve": "approved",
            "reject": "rejected",
            "reopen": "pending",
            "mark-applied": "applied",
        }[args.command]
        path = transition(root, args.proposal_id, destination, args.note)
        print(f"{args.proposal_id}: {destination} ({path.relative_to(root)})")
        return 0
    except ValueError as error:
        print(f"curator: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
