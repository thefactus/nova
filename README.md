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

Install Nova. This creates a new `~/nova` folder, the recommended home for its
memory, skills, and configuration:

```sh
curl -fsSL https://github.com/thefactus/nova/releases/latest/download/install.sh | sh
```

Your Nova stays local and is not connected to GitHub.

### Open Nova

From the terminal, start your coding agent in the Nova folder:

```sh
cd ~/nova
codex  # or: claude
```

Prefer a desktop app? Open the Nova folder in the
[Codex desktop app](https://developers.openai.com/codex/app/). In
[Claude Desktop](https://code.claude.com/docs/en/desktop), open the Code tab and
choose the Nova folder as the project folder.

Nova applies to sessions started from that folder. It does not change either
agent globally. A durable preference or project decision saved by one agent
remains available when you open another agent from the same Nova.

On first launch, your coding agent may ask you to trust the Nova folder. It may
also ask you to review Nova's hooks, which apply only inside that folder.

Your Nova will grow to contain personal memory and context. Keep it local or
back it up in a private Git repository. Do not use the public Nova repository
as its remote. That repository distributes Nova itself, not your personal data.

## How Nova works

Nova is made of ordinary files you can inspect, edit, and version with Git.

- `AGENTS.md` tells each supported coding agent how to use Nova.
- `memories/` helps agents remember your preferences and important context.
- `second_brain/` holds detailed knowledge and project history.
- `skills/` holds reusable ways of doing recurring work.
- `learning/` holds proposed skill changes until you review them.

Codex reads `AGENTS.md` directly. Claude Code reaches the same instructions
through the one-line `CLAUDE.md` bridge. Project-local hooks remind both agents
to load the same files without changing how they work outside Nova.

Nova is active only when a coding agent starts from the Nova root. During normal
work, the agent can save durable learning to the appropriate readable file.

## Current scope

Nova `0.1.0` is tested with Codex and Claude Code on macOS and Linux. It includes
shared memory, second-brain knowledge, reusable skills, project-local hooks, and
learning that keeps skill changes under your review.

Other operating systems and coding agents have not been tested yet. A web
interface, automatic upgrades, and built-in secret scanning are not part of
this release.

## Updating Nova

Use the bundled `update-nova` skill when a new release is available. It guides
your coding agent through reviewing and applying the update while keeping your
memory, knowledge, skills, configuration, and local choices under your control.

## Why Nova

### Why not just use Hermes or OpenClaw?

Hermes and OpenClaw provide broader agent environments. Nova takes a smaller
approach. It gives Codex, Claude Code, and other native coding agents one
understandable home for shared context without asking you to replace the tools
you already use.

### Why not just use documents?

Documents preserve information, but they do not tell an agent how to use it.
Nova gives coding agents a shared structure for what to load, where to save
knowledge, how to reuse skills, and when to preserve learning.

### Is Nova just memory between sessions?

No. Nova is an AI assistant, and memory between sessions is only one part of it.
It also gives your coding agents deeper project knowledge, reusable skills,
shared instructions, local hooks, and a way to improve while keeping changes
reviewable.

## Security

Your Nova may contain personal or company information. Before sharing it,
review its files and Git history for private data, credentials, and tokens. See
[`SECURITY.md`](SECURITY.md) to report a vulnerability or respond to an exposed
credential.
