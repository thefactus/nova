# Learning

This directory keeps continuous learning auditable.

- `proposal-schema.json` defines the portable proposal format.
- `proposals/` contains staged changes when skill write approval is enabled.
- `feedback/` contains useful learning that belongs to a repository, company, external package, or another owner.

Proposal states are `pending`, `approved`, `rejected`, and `applied`. State
directories are created when they are first needed. Moving a proposal records
a decision; applying it remains a separate, visible change with its own
validation.

With the default `skills.write_approval: false`, the active coding agent applies
justified creations and improvements directly to Nova's canonical skills. When
the setting is `true`, the agent stages those writes here instead. Use
`skills/curate-skill-learning` to inspect and transition them one at a time.
Curating a proposal changes its audit state only; applying the approved change
remains a separate, visible edit.

Pending proposals remain pending when the setting changes. They are never
applied retroactively without review.
