# Skill proposals

Skill changes move through four directories.

- `pending/` contains unreviewed proposals.
- `approved/` contains proposals the owner accepted but that have not been applied.
- `rejected/` preserves declined proposals and their reason.
- `applied/` preserves the audit history of completed changes.

When `skills.write_approval` is `true`, the active coding agent creates these
state directories only when needed. The curator moves one proposal at a time
after an explicit owner decision. Existing pending proposals remain reviewable
even when write approval is later disabled.
