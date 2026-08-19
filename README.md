# Nova

> Same you, every coding agent.

Bring your memory, skills, and context to Codex, Claude Code, and more.

Nova is an AI assistant that works through the coding agents you already use.
Codex stays Codex. Claude Code stays Claude Code.

Nova adds a small, understandable layer of shared context without replacing
native behavior, burying coding agents in rules, or requiring a complex setup.
Each owner can evolve it for their own work.

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

## How Nova works

Nova uses ordinary files that its owner can inspect and change.

- `AGENTS.md` gives every supported coding agent the same small operating
  direction.
- `memories/` keeps compact preferences and durable context between sessions.
- `second_brain/` keeps deeper knowledge and project history.
- `skills/` keeps reusable procedures shared across coding agents.
- `learning/` keeps proposed skill changes reviewable.

Codex reads `AGENTS.md` directly. Claude Code imports it through the one-line
`CLAUDE.md` bridge. Small project-local hooks point both agents to the same
files without changing their native identity or installing Nova globally.

Nova is active only when a coding agent starts from the Nova root. During normal
work, the agent can save durable learning to the appropriate readable file.
Changes to bundled skills remain pending until the owner reviews them.

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

## Security

A working Nova can contain personal and company context. Keep it in a private
repository unless you intentionally want that context to be public. Security
reporting and credential guidance are in [`SECURITY.md`](SECURITY.md).
