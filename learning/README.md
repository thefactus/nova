# Learning

This directory keeps continuous learning auditable.

- `proposal-schema.json` defines the portable proposal format.
- `review-schema.json` defines the structured output expected from any reviewing runtime.
- `config.json` holds the editable per-entry memory limit used by the reviewer.
- `proposals/` contains owner-reviewed changes to Nova's canonical skills.
- `feedback/` contains useful learning that belongs to a repository, company, external package, or another owner.

Proposal states are `pending`, `approved`, `rejected`, and `applied`. State
directories are created when they are first needed. Moving a proposal records
a decision; applying it remains a separate, visible change with its own
validation.

Use `skills/curate-skill-learning` to inspect and transition proposals one at a
time. The curator changes audit state only. It never edits a skill.

Counters, reviewer jobs, locks, and logs belong under `.runtime/`, not here.
