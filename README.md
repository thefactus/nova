# Nova

> Same you, every coding agent.

Bring your memory, skills, and context to Codex, Claude Code, and more.

Nova is an AI assistant that works through the coding agents you already use.
Codex stays Codex. Claude Code stays Claude Code.

Nova adds a small, understandable layer of shared context without replacing
native behavior, burying coding agents in rules, or requiring a complex setup.
Each owner can evolve it for their own work.

Current version `0.1.5`. Published releases use a matching `v`-prefixed Git
tag, such as `v0.1.5`.

## Start using Nova

Nova currently supports macOS and Linux. You need Git, `curl`, a POSIX shell,
and either Codex or Claude Code.

Install Nova. This creates a new `~/nova` folder, the recommended home for its
memory, skills, and configuration:

```sh
curl -fsSL https://github.com/thefactus/nova/releases/latest/download/install.sh | sh
```

Prefer another location? Pass the destination after `sh -s --`:

```sh
curl -fsSL https://github.com/thefactus/nova/releases/latest/download/install.sh | sh -s -- "$HOME/ai/nova"
```

The destination must not already exist. Nova creates its parent directories
when needed.

Your Nova content stays local and is not linked to the public GitHub repository.
By default, startup makes a cached request to Nova's public GitHub release
endpoint to check for a newer version. It sends no Nova content and can be
disabled in `config.yaml`.

## Use Nova

**Open Nova → Work normally → Keep useful context → Continue later**

From the terminal, start your coding agent in the Nova folder:

```sh
cd ~/nova
codex  # or: claude
```

If you installed Nova somewhere else, use that directory instead.

Then ask it to work normally:

```text
Work on ~/workspace/acme-api. Add CSV export to reports.
```

That is it. There are no special Nova commands.

- **Your agents stay the same.** Keep using Codex, Claude Code, or another
  compatible coding agent.
- **The context is shared.** Agents started inside Nova can use the same
  preferences, skills, and second brain.
- **Memory is selective.** The agent keeps what seems useful later, not
  everything you say or do.
- **You remain in control.** Everything is stored in ordinary files you can
  inspect, edit, remove, and version.

<details>
<summary><strong>See what Nova may preserve</strong></summary>

- Personal preferences in `memories/USER.md`
- Project context in `second_brain/projects/`
- Repeatable workflows as autonomously improved skills, or reviewable changes
- Nothing when the task produces no durable learning

You can ask the agent to remember something, but you do not have to.

</details>

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
- `config.yaml` controls skill review, periodic learning, and update notices.
- `memories/` helps agents remember your preferences and important context.
- `second_brain/` holds detailed knowledge and project history.
- `skills/` holds reusable ways of doing recurring work.
- `learning/` holds staged skill changes when approval is enabled.
- `.runtime/skill-index.md` is a disposable index that helps agents find the
  right Nova skill without loading every skill file.
- `.runtime/update-check/` stores the disposable timestamp and public version
  from the most recent release check.

Codex reads `AGENTS.md` directly. Claude Code reaches the same instructions
through the one-line `CLAUDE.md` bridge. Project-local hooks remind both agents
to load the same files without changing how they work outside Nova.

Nova is active only when a coding agent starts from the Nova root. During normal
work, the agent can save durable learning to the appropriate readable file.

After a non-trivial task changes canonical Nova files, the agent keeps those
durable changes recoverable in a focused local Git commit. It commits only work
it can attribute to the current task, leaves unrelated or uncertain changes
untouched, and checks for sensitive or runtime data first. Nova never pushes,
tags, releases, or publishes without the owner's explicit authorization. This
policy does not change how the agent handles Git in external project
repositories.

### Skill learning

Nova creates and improves its canonical skills autonomously when completed work
reveals a durable, reusable procedure. Changes remain ordinary local files and
visible Git diffs. Speculative or one-off observations should not change a
skill, and deletion always requires explicit owner authorization.

At the end of non-trivial work, the agent actively reviews owner corrections,
missing or outdated skill steps, and repeated workflows that may deserve a new
skill. The agent should act on justified learning rather than merely classify
it, while leaving one-off or temporary observations in the current session.

Autonomous skill writes and periodic learning review are the defaults:

```yaml
skills:
  write_approval: false
learning:
  periodic_review:
    enabled: true
    turn_interval: 10
    action_interval: 15
updates:
  check_on_startup: true
  check_interval_hours: 24
```

Set `skills.write_approval` to `true` in `config.yaml` to stage every skill
creation or update under `learning/proposals/pending/`. Review staged changes
through the bundled `curate-skill-learning` skill. Switching the setting does
not apply proposals that were already pending.

The periodic review is a lightweight fallback for the end-of-task learning
loop. After either configured interval is reached, the next user prompt asks
the active agent to inspect recent completed work and apply only justified
durable learning. Nova stores only disposable counters and a due marker under
`.runtime/`. It does not start a background reviewer or retain prompts, tool
results, or transcripts. Set `learning.periodic_review.enabled` to `false` to
turn the fallback off.

### Other installed skills

Nova adds its canonical `skills/` library to the coding agent's normal
environment. It does not hide skills the runtime already exposes from user or
global directories, the active project, plugins, managed packages, or built-in
sources. Starting from Nova is therefore root-activated, but not skill-isolated.

When skills overlap, the agent should prefer the most specific procedure for
the task and its owner. Nova-owned skills take precedence for maintaining Nova
itself. Compatible skills may be combined; materially conflicting skills should
not be blended silently. Nova's autonomous learning changes only its own
canonical skills, never external sources.

### Update notices

At startup, Nova checks its public GitHub release endpoint at most once per
configured interval. If a newer semantic version exists, the agent mentions the
installed and available versions once in its first response. The check has a
short timeout, fails silently when offline, and never updates Nova automatically.

To silence update notices and disable the network check:

```yaml
updates:
  check_on_startup: false
```

## Current scope

Nova `0.1.5` is tested with Codex and Claude Code on macOS and Linux. It includes
shared memory, second-brain knowledge, reusable skills, project-local hooks, and
autonomous skill learning with optional write approval.

Other operating systems and coding agents have not been tested yet. A web
interface, automatic upgrades, and built-in secret scanning are not part of
this release.

## Updating Nova

Use the bundled `update-nova` skill when a new release is available. It guides
your coding agent through reviewing and applying the update while keeping your
memory, knowledge, skills, configuration, and local choices under your control.

## Why Nova

Nova is inspired by [Hermes Agent](https://github.com/NousResearch/hermes-agent)
and [OpenClaw](https://github.com/openclaw/openclaw). They showed how memory,
skills, and continuous learning can make an assistant more useful over time.

Both are broad, general-purpose agent environments. Nova takes a narrower idea
from them: give the coding agents you already use a shared memory, second brain,
reusable skills, and an autonomous learning loop with optional review.

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
shared instructions, local hooks, and a way to improve autonomously while
keeping review available when you want it.

## Security

Your Nova may contain personal or company information. Before sharing it,
review its files and Git history for private data, credentials, and tokens. See
[`SECURITY.md`](SECURITY.md) to report a vulnerability or respond to an exposed
credential.
