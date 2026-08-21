# Security

## Supported versions

Security fixes are provided for the latest published Nova release.

## Skills outside Nova

Native coding agents may expose user-level, global, project, plugin, managed,
or built-in skills alongside Nova's canonical library. Nova's root activation
does not audit, sandbox, hide, or disable those external sources. Review skills
before installing them and manage their trust through the runtime or source
that owns them.

Nova may use a relevant external skill, but its autonomous learning loop must
not modify or delete that source. External skill learning belongs with its
owner rather than in Nova's canonical library.

## Report a vulnerability

Do not open a public issue with vulnerability details. Use GitHub's private
vulnerability reporting for this repository:

https://github.com/thefactus/nova/security/advisories/new

Include the affected Nova version, impact, and the smallest safe reproduction.
Use fake values in examples and never include credentials or private user data.

If private reporting is unavailable, open a minimal public issue asking for a
private contact channel without including vulnerability details.

## Exposed credentials

Treat a real credential committed to Git as compromised, even in a private
repository. Rotate or revoke it first. Removing the current file or rewriting
Git history does not invalidate a credential that may already have been copied.

After rotation, remove the credential from current files and coordinate any
history cleanup with everyone who may have clones, forks, or release artifacts.
