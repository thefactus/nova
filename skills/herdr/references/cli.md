# Herdr CLI reference

Use this reference for command patterns, then confirm current syntax with the
installed binary. Do not run bare `herdr` for discovery because it may launch
or attach the interactive interface.

## Contents

- Discover capabilities
- Identify the caller
- Create a working pane
- Prompt and monitor agents
- Run ordinary commands
- Cleanup boundaries

## Discover capabilities

```sh
herdr --help
herdr agent
herdr pane
herdr workspace
herdr tab
```

Print only the relevant command group. Do not probe a potentially mutating
nested command by omitting its arguments.

Most control commands return JSON. Parse IDs from their responses instead of
predicting them.

## Identify the caller

```sh
test "${HERDR_ENV:-}" = 1
printf '%s\n' "$HERDR_WORKSPACE_ID" "$HERDR_TAB_ID" "$HERDR_PANE_ID"
herdr pane current --current
herdr pane layout --pane "$HERDR_PANE_ID"
herdr pane list --workspace "$HERDR_WORKSPACE_ID"
herdr agent list
```

Prefer `--current`, an explicit pane ID, or a unique agent name. Omitting a
target may use a pane focused by another client.

Workspace, tab, and pane IDs are opaque handles such as `w1`, `w1:t1`, and
`w1:p1`. Closed IDs are not reusable. After moving a pane, continue with the
new ID returned by the command or with the live agent name.

## Create a working pane

Inspect the layout first. Split a wide pane to the right and a narrow or tall
pane down. Preserve the working directory and owner focus:

```sh
herdr pane split --current --direction right --cwd "$PWD" --no-focus
```

Use `--direction down` when it produces a more usable layout. Read the new pane
ID from `.result.pane.pane_id`.

An agent needs an existing shell pane that is waiting at an interactive prompt.
Starting an agent does not create the pane:

```sh
herdr agent start reviewer --kind codex --pane <pane-id>
```

Inspect `herdr agent` for supported kinds and runtime-specific arguments. Pass
native arguments only after `--`.

## Prompt and monitor agents

```sh
herdr agent get reviewer
herdr agent prompt reviewer "Review the current diff." --wait --timeout 120000
herdr agent read reviewer --source recent-unwrapped --lines 120
herdr agent wait reviewer --until blocked --timeout 120000
```

For ordinary work, `agent prompt --wait` waits for the first settled state. Use
`--until` only when a specific state is required.

Interpret lifecycle state carefully:

- `working`: the agent is active;
- `blocked`: Herdr recognized an approval or question interface;
- `idle`: the agent is ready and its tab has been seen;
- `done`: background work settled before its tab was seen;
- `unknown`: Herdr cannot classify the agent confidently.

Neither `idle` nor `done` proves that an existing agent is free for unrelated
work. Inspect its recent output and assignment first.

If a prompt or wait stalls, read state and output before deciding whether to
send another prompt, a logical key, or no input. Use logical keys for interactive
controls:

```sh
herdr agent send-keys reviewer esc
herdr agent send-keys reviewer ctrl+c
```

## Run ordinary commands

Use pane commands for shells, tests, servers, and other non-agent processes:

```sh
herdr pane run <pane-id> "just test"
herdr pane wait-output <pane-id> --match "test result" --timeout 120000
herdr pane read <pane-id> --source recent-unwrapped --lines 120
```

Use `--regex` instead of `--match` only when pattern matching is required.
Prefer `recent-unwrapped` for logs and transcripts, `visible` for the rendered
viewport, and `detection` only when inspecting the text used for agent-state
detection.

If completed output cannot be recovered from an alternate screen, ask the
agent to write its complete result as Markdown in a safe temporary directory
and return the path. Use this as a fallback, not the initial workflow.

## Cleanup boundaries

- Use `--no-focus` for background work.
- Close only task-created panes unless the owner explicitly expands the scope.
- Never run `herdr server stop` from an active session as routine cleanup.
- CLI server errors normally use exit status 1; syntax errors use exit status 2.
