# Skills

Skills are readable, reusable procedures shared by every runtime.

Each skill lives at `skills/<name>/SKILL.md` and starts with a name and a clear
description of when it should be used. Agents discover skills here directly;
this directory is the canonical source.

Nova bundles `curate-skill-learning`, which keeps proposed skill changes under
explicit owner control, and `update-nova`, which guides changes to a working
Nova while preserving its owner's context. Every public skill should be
designed for Nova and reviewed for private paths, company knowledge,
credentials, and hidden runtime assumptions before it is added.

Learning may propose a new skill or an improvement here. It never changes an
existing skill without the owner's approval.
