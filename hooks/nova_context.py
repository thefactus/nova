#!/usr/bin/env python3
"""Inject Nova's canonical context into supported runtime lifecycle events."""

from __future__ import annotations

import json
import sys
from pathlib import Path


NOVA_HOME = Path(__file__).resolve().parents[1]
SKILL_INDEX_PATH = NOVA_HOME / ".runtime" / "skill-index.json"

sys.path.insert(0, str(NOVA_HOME))

from nova.skills import write_skill_index  # noqa: E402


START_CONTEXT = f"""Nova operating check:
- Read memories/USER.md and memories/MEMORY.md before substantive work.
- Skill metadata index: {SKILL_INDEX_PATH}. Use it to find applicable skills, then load only their canonical SKILL.md files.
- Use second_brain only when deeper project history or decisions are needed.
- Keep durable knowledge in canonical Nova files."""

PROMPT_CONTEXT = f"""Nova skill-routing check:
1. Use {SKILL_INDEX_PATH} to identify relevant skills; do not scan every SKILL.md.
2. Load every clearly relevant SKILL.md before substantive work.
3. If no skill applies, proceed normally. Do not force a weak match.
4. After non-trivial work, classify durable learning as none, memory, project knowledge, skill improvement, or new-skill proposal."""


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, TypeError):
        return 0

    event = payload.get("hook_event_name")
    if event == "SessionStart":
        try:
            write_skill_index(NOVA_HOME)
        except OSError:
            pass
        context = START_CONTEXT
    elif event == "UserPromptSubmit":
        context = PROMPT_CONTEXT
    else:
        return 0

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": event,
                    "additionalContext": context,
                }
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
