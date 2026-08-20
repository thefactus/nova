---
name: herdr
description: Operate Herdr and coordinate coding agents across its workspaces, tabs, and panes. Use only when the owner explicitly mentions Herdr or asks to use it for agent orchestration, parallel work, review, collaborative brainstorming, pane control, or workspace inspection. Do not invoke Herdr merely because another terminal or agent might be useful. Requires a Herdr-managed session.
---

# Herdr

Use Herdr as a visible coordination surface while remaining responsible for the
overall result. Read [CLI reference](references/cli.md) before issuing control
commands.

## Establish the session

1. Verify that `HERDR_ENV=1`. If not, explain that the current agent is not
   running inside Herdr and stop before controlling another session.
2. Treat the installed `herdr` binary and its help output as the authority for
   supported commands and arguments.
3. Inspect the caller's workspace, tab, pane, layout, and live agents before
   creating or prompting anything.
4. Default to the current workspace, current tab, and current working directory.
   Create a different topology only when the owner requests it or the task
   clearly requires isolation.

## Coordinate agents

Use additional agents for bounded work that benefits from a distinct runtime,
perspective, or independent execution. Keep trivial or tightly coupled work in
the coordinating agent.

For each participant:

1. Choose a stable role-based name and inspect existing agents before deciding
   whether one is available. An idle agent may still belong to another task.
2. Create a pane without stealing focus and start the runtime requested by the
   owner. Do not silently substitute a different agent kind.
3. Give a self-contained assignment with the objective, relevant location,
   constraints, permission to edit or not, expected evidence, and desired
   output. Do not leak an expected answer into an independent evaluation.
4. Wait with a bounded timeout. If the agent is blocked, unknown, or stalled,
   inspect its state and recent output before sending input.
5. Integrate the contribution into the main task. Verify important claims and
   resolve conflicts instead of concatenating agent responses.

Keep the owner informed during longer coordination. One slow or blocked
participant must not freeze all useful progress.

## Run parallel work

Parallelize only tasks that can proceed independently without editing the same
files or depending on one another's unfinished conclusions. Assign clear file
or decision boundaries before starting.

When agents share a repository:

- inspect the working tree before and after their work;
- treat all existing changes as owner work;
- avoid concurrent edits to the same file;
- ask agents to report exact files, checks, and unresolved risks;
- run an integrated verification after combining results.

## Brainstorm collaboratively

A brainstorm is a conversation, not parallel idea collection. The coordinating
agent participates as a contributor and later synthesizes the result.

1. Choose a small set of complementary participants. When they may be reused,
   name them by stable role or runtime rather than the current topic.
2. Create a shared Markdown conversation artifact in a safe temporary
   directory unless the owner wants it preserved with the project.
3. Open with the problem, constraints, and the coordinating agent's first
   perspective.
4. Prompt one participant at a time to read the complete artifact and respond
   to the actual discussion. Ask it to challenge, combine, or extend previous
   points, not restart from an empty slate.
5. Append each returned contribution to the artifact, then add the
   coordinating agent's reactions and changed view before the next round.
6. Use a small bounded number of rounds. A useful default is one exploratory
   round and one convergence round, adjusted to the question.
7. If a participant stalls, inspect it, try one focused recovery when useful,
   and continue with the available conversation rather than waiting forever.
8. Synthesize the strongest direction, important disagreements, tradeoffs, and
   remaining decisions. Do not present a raw transcript as the conclusion.

Keep brainstorm agents alive when the owner wants to reuse them. Otherwise,
close only panes created for the task and only after their useful output is
captured.

## Preserve ownership and safety

- Do not prompt, interrupt, rename, move, or close an existing agent until its
  assignment is understood.
- Do not close panes, tabs, workspaces, or sessions that this task did not
  create unless the owner explicitly requests it.
- Keep background work from changing the owner's focus unless requested.
- Parse returned identifiers and state instead of guessing from layout order.
- Never stop the Herdr server or kill its main process as routine cleanup.
- Report blocked approvals or questions to the owner when answering them would
  require authority or context the coordinating agent does not have.
