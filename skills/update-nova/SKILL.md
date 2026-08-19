---
name: update-nova
description: Guide updates to a working Nova while preserving the owner's memory, knowledge, skills, configuration, and local intent. Use when the owner asks to update, upgrade, sync, or bring changes from a Nova release into their working Nova.
---

# Update Nova

Help the owner understand and apply an update while keeping their Nova under
their control.

## Approach

1. Inspect the working Nova, its Git state, and the source of the proposed
   changes. Notice files the owner created or adapted.
2. Explain the meaningful changes and choices before editing. Ask when a
   conflict would materially change the owner's content or intent.
3. Apply the smallest coherent update. Prefer a recoverable approach when the
   change would be difficult to undo.
4. Verify the result and summarize what changed, what stayed local, and what
   remains unresolved.

Keep owner-managed memory, second-brain knowledge, skills, and configuration in
the owner's hands throughout the update.
