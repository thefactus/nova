---
name: skill-library-audit
description: Inventory and review a Nova skill library for structural problems, unclear triggers, overlap, stale assumptions, and cleanup opportunities. Use when the owner wants to understand, organize, simplify, consolidate, archive, or remove skills without making unreviewed changes.
---

# Skill Library Audit

Review the library as a system before changing individual skills. Keep the
audit evidence-based, compact, and read-only until the owner approves a change.

## Inventory

1. Resolve the Nova root from this skill's location under
   `skills/skill-library-audit/SKILL.md`.
2. Inventory immediate directories under `skills/` that contain `SKILL.md`.
3. Read each file's frontmatter first. Record the folder name, declared name,
   description, optional agent metadata, and bundled resources.
4. Check observable structural issues:
   - missing or malformed frontmatter;
   - folder and declared-name mismatch;
   - duplicate names;
   - descriptions that do not explain when the skill should trigger;
   - referenced resources that do not exist;
   - personal paths, private organization context, hidden runtime assumptions,
     or likely sensitive data.
5. Use a compatible skill validator when one is available. Do not introduce a
   runtime dependency merely to complete the audit.

Do not treat missing usage evidence as proof that a skill is unused. Mark
usage, provenance, or ownership as unknown when Nova cannot establish it.

## Review overlap

Group skills by purpose from their names and descriptions. Select one small,
coherent comparison batch at a time, then read every selected `SKILL.md`
completely.

Compare:

- triggering conditions;
- scope and expected output;
- unique procedures or knowledge;
- bundled resources and dependencies;
- assumptions about tools, paths, people, or organizations.

Distinguish genuine duplication from skills that share a topic but serve
different workflows.

## Report

Lead with the library count and the most important finding. Then show:

1. verified structural problems;
2. possible overlaps worth reviewing;
3. skills whose purpose or ownership is unclear;
4. a small recommended review batch;
5. open questions that require the owner's context.

Separate evidence from recommendations. Avoid a file-by-file inventory when a
short grouped summary is enough.

## Apply approved cleanup

Before changing an existing skill:

1. Obtain the owner's explicit approval for the exact skill or batch.
2. Explain what will remain, what will change, and how the previous version can
   be recovered.
3. Modify only the approved scope. Never remove or merge skills automatically.
4. Validate every affected skill and run Nova's relevant repository checks.
5. Report the resulting inventory and any unresolved overlap.
