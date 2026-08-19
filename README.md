# Nova

> Same you, every coding agent.

Bring your memory, skills, and context to Codex, Claude Code, and more.

Nova carries what is yours without flattening what makes each agent distinct.
Codex stays Codex. Claude Code stays Claude Code.

Nova evolves with its owner and stays understandable as it grows.

## Continuous learning

Nova learns proactively when something is worth carrying forward. The user
does not need to explicitly ask every time.

- `memories/USER.md` holds durable preferences, communication style, expectations, and workflow habits. Its default limit is 1,375 characters.
- `memories/MEMORY.md` holds compact durable facts that remain useful across projects and sessions. Its default limit is 2,200 characters.
- `second_brain/` holds deeper knowledge, global agent working notes, and projects. Individual projects may also keep their own `agents-second-brain/`.

Memory stays compact. Entries are separated by `§`; stale or overlapping
entries are consolidated instead of allowing the files to grow forever. Both
memory files are tracked in Git as part of the owner's Nova. The owner can
adjust these recommendations as their Nova evolves.

Memory is compact startup context. Detailed or project-specific knowledge
belongs in the second brain. A memory entry may point to deeper knowledge
instead of duplicating it.

Nova is runtime-agnostic. Its memory, knowledge, skills, and learning rules are
canonical; Codex, Claude Code, and future agents can connect to the same sources
without one runtime becoming the primary one.

Nova's shared code validates compact memory entries and runtime-neutral learning
reviews without giving any runtime its own private copy.

Proposed skill changes remain pending until the owner reviews them through
Nova's bundled `curate-skill-learning` skill.

## Runtime integration

`AGENTS.md`, `memories/`, `second_brain/`, and `skills/` are Nova's canonical
sources. Codex reads `AGENTS.md` directly. Claude Code uses the one-line
`CLAUDE.md` bridge to import the same instructions.

Nova is active only for agents opened from the Nova root. It does not install
global hooks or inject its context into sessions started elsewhere.

Inside Nova, both runtimes call `hooks/nova_context.sh` through their native
project configuration. The small POSIX shell hook points the agent to Nova's
compact memory at session start and reinforces canonical skill routing and the
learning loop on each prompt. Basic startup does not require Python, Node, or a
generated skill index.

When Python is available, `python3 -m nova.skills` can validate skill metadata
and generate `.runtime/skill-index.json`. The optional index is disposable
adapter input, not a second source of truth.

## Public source and your Nova

This repository is Nova's public source. A person's working Nova is created
from a release as a separate local or private repository. It is not expected to
be a public GitHub fork, and onboarding should not add a public remote by
default.

Updates should keep the owner's memory, knowledge, skills, configuration, and
local intent under their control. Nova's bundled `update-nova` skill guides the
agent through understanding and applying those changes.

## Structure

- `memories/` keeps compact durable context.
- `second_brain/` keeps deeper knowledge and history.
- `skills/` keeps reusable procedures shared by every runtime.
- `learning/` keeps learning configuration, skill proposals, and ownership feedback reviewable.
- `nova/` contains shared learning and skill-discovery behavior.

Your working Nova can contain personal and company context. Keep it in a
private repository unless you intentionally want that context to be public.
