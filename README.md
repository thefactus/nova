# Nova

> Same you, every coding agent.

Bring your memory, skills, and context to Codex, Claude Code, and more.

Nova is an AI assistant that works through the coding agents you already use.
Nova carries what is yours without flattening what makes each agent distinct.
Codex stays Codex. Claude Code stays Claude Code.

Nova evolves with its owner and stays understandable as it grows.

Current version `0.1.0`. Published releases use a matching `v`-prefixed Git
tag, such as `v0.1.0`.

## Start using Nova

Nova currently supports macOS and Linux. You need Git, `curl`, a POSIX shell,
and either Codex or Claude Code.

Install the latest release at `~/nova`:

```sh
curl -fsSL https://github.com/thefactus/nova/releases/latest/download/install.sh | sh
```

Pass a different destination when needed:

```sh
curl -fsSL https://github.com/thefactus/nova/releases/latest/download/install.sh | sh -s -- /path/to/nova
```

The installer verifies the release, creates a new Git repository on `main`,
and makes the first commit. It does not configure a remote. Start `codex` or
`claude` from the new Nova root.

Verify the local repository:

```sh
cd ~/nova
git branch --show-current
git log -1 --pretty=%s
git remote
```

The first two commands should print `main` and `Start my Nova`. The last command
should print nothing.

On first launch, the coding agent may ask whether you trust the folder. Review
it, then accept to enable Nova's project configuration and hooks. They apply
only inside that Nova.

Keep your working Nova local or connect it to a private repository. The public
Nova repository should not be its remote.

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

The active coding agent classifies learning and updates Nova's readable files
directly. There is no background reviewer or separate Nova runtime.

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
learning loop on each prompt. Basic startup requires only POSIX shell.

Agents discover skills directly from their canonical frontmatter.

## Current scope

Nova `0.1.0` supports Codex and Claude Code on macOS and Linux. Memory,
second-brain knowledge, skills, project-local hooks, and agent-native learning
are available today.

Windows, additional coding agents, a web interface, automatic upgrades, and
deterministic secret scanning are not included yet.

## Public source and your Nova

This repository is Nova's public source. A person's working Nova is created
from a release as a separate local or private repository. It is not expected to
be a public GitHub fork, and onboarding should not add a public remote by
default.

Updates should keep the owner's memory, knowledge, skills, configuration, and
local intent under their control. Nova's bundled `update-nova` skill guides the
agent through understanding and applying those changes.

## Why Nova

### Why not just use Hermes or OpenClaw?

Use a complete agent harness when that is what you want. Nova is for people who
want to keep using Codex, Claude Code, and other native coding agents while
sharing one understandable environment across them.

### Why not just use documents?

Documents preserve information. Nova also tells each coding agent what to load,
where new knowledge belongs, how skills are shared, and when durable learning
should be saved.

### Is Nova just memory between sessions?

No. Nova is an AI assistant. Memory between sessions is one of its capabilities,
along with deeper project knowledge, skills, shared agent instructions,
project-local hooks, and continuous learning.

## Structure

- `memories/` keeps compact durable context.
- `second_brain/` keeps deeper knowledge and history.
- `skills/` keeps reusable procedures shared by every runtime.
- `learning/` keeps skill proposals and ownership feedback reviewable.

Your working Nova can contain personal and company context. Keep it in a
private repository unless you intentionally want that context to be public.

Security reporting and credential guidance are in [`SECURITY.md`](SECURITY.md).
