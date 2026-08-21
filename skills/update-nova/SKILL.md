---
name: update-nova
description: Guide updates to a working Nova while preserving the owner's memory, knowledge, skills, configuration, and local intent. Use when the owner asks to update, upgrade, sync, or bring changes from a Nova release into their working Nova.
---

# Update Nova

Bring released Nova changes into a working Nova without replacing the Nova the
owner has evolved. Treat an update as a reviewed merge, not a fresh install.

## Prepare

1. Confirm that the target is a working Nova and read its `VERSION` and Git
   state.
2. Identify the requested release and obtain its verified release artifact in
   a temporary directory. Do not run the installer over an existing Nova or
   add the public source repository as its remote.
3. Make the current state recoverable before editing. Prefer an existing clean
   commit, a local checkpoint commit, or a clearly identified backup.

## Preserve ownership

- Never replace `memories/`, `second_brain/`, `config.yaml`, owner-created or
  adapted skills, or other owner-managed configuration automatically.
- Treat any locally modified distributed file as a merge, not an overwrite.
- Treat `.runtime/` as disposable state rather than owner knowledge.
- Ask before a conflict would remove content, change local intent, require
  credentials, or publish anything.

## Apply the update

1. Compare the current Nova with the target release. When a prior release is
   available, use it as the baseline to distinguish upstream changes from local
   changes.
2. Summarize meaningful release changes, local changes, and conflicts before
   editing.
3. Apply the smallest coherent set of changes. Add new distributed files when
   safe, merge locally adapted files, and leave unresolved conflicts visible.
4. Update `VERSION` only after the corresponding release changes are applied.
5. Run the checks supplied by the release and inspect the final Git diff. At a
   minimum, confirm that startup instructions, hooks, and runtime bridges still
   point to valid local files.
6. Report the previous and resulting versions, what changed, what remained
   local, validation performed, and anything still requiring a decision.

If the target release cannot be verified, the current state is not recoverable,
or file ownership is unclear, stop before modifying the working Nova and ask
the owner how to proceed.
