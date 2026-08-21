# Skills

Skills are readable, reusable procedures shared by every runtime.

Each skill lives at `skills/<name>/SKILL.md` and starts with a name and a clear
description of when it should be used. Agents discover skills here directly;
this directory is the canonical source.

Nova bundles `capture`, which saves useful source material into the second
brain; `curate-skill-learning`, which reviews staged skill changes when write
approval is enabled; `herdr`, which operates and orchestrates coding agents
through Herdr; `skill-library-audit`, which reviews the library for structure
and overlap; `organize-project-knowledge`, which keeps growing project context
understandable; and `update-nova`, which guides changes to a working Nova while
preserving its owner's context. Every public skill should be designed for Nova
and reviewed for private paths, company knowledge, credentials, and hidden
runtime assumptions before it is added.

By default, durable learning from completed work may create or improve a
canonical skill directly. Set `skills.write_approval: true` in `config.yaml` to
stage those writes for explicit owner review. Skill deletion always requires
explicit authorization.
