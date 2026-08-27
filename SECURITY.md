# Security

## Supported versions

Security fixes are provided for the latest published Nova release.

## Security model

Nova is a set of local files, project-local hooks, and instructions used by a
native coding agent. It is not a sandbox or a separate security boundary.

- Nova inherits the filesystem, network, tool, and command permissions granted
  to Codex, Claude Code, or another coding agent.
- Nova's hooks execute local shell code when the supported agent invokes them.
  Review the folder and its hooks before granting trust.
- Skills are instructions that may cause an agent to use tools or modify files.
  Review skills according to the sensitivity of the work and the permissions
  available to the agent.
- Imported documents, webpages, repository content, and tool output may contain
  untrusted instructions. Nova tells agents to treat that content as evidence,
  but this is guidance rather than technical isolation.

The coding agent and any tools, plugins, or model providers it uses have their
own data handling and network behavior. Review those products separately under
your organization's policies.

## Local data and Git history

Memory, second-brain knowledge, skills, and configuration are ordinary local
files. Nova does not encrypt them or enforce a retention period. Protect the
device and any backups according to the sensitivity of that content.

The installer creates a local Git repository with no remote and restricts the
Nova root directory to its owner. Local commits make changes recoverable, but
they can also retain content after it is removed from the current file. Before
adding a remote, sharing a working Nova, or copying its Git history, review the
entire repository for private data and credentials.

The public Nova repository distributes empty starter memory and knowledge
files. A person's working Nova is a separate repository and must not be pushed
to the public Nova repository.

## Git safety guard

New Nova installations configure `core.hooksPath=.githooks` inside the working
repository. The pre-commit hook checks staged filenames and content before they
enter history. The pre-push hook scans all local Git history and requires the
destination URL to be approved as a private backup remote before the first
push. Changing that URL invalidates the approval.

Run the review explicitly with:

```sh
sh bin/nova-safety approve origin
```

When an authenticated GitHub CLI is available, the review verifies GitHub
visibility directly. Otherwise, it asks the owner to confirm that the remote is
private. That command may contact GitHub through GitHub CLI; automatic commit
and push hooks do not make network requests beyond Git's requested push.

The guard is defense in depth, not a security boundary:

- Git allows hooks to be bypassed with `--no-verify`.
- Pattern matching cannot recognize every credential or determine whether an
  ordinary note, image, PDF, or company document is confidential.
- Private-remote approval records the reviewed URL; non-GitHub visibility
  cannot be monitored continuously.
- Existing custom `core.hooksPath` settings are preserved instead of silently
  replaced, so their owner must integrate the Nova hooks manually.

The distributed `.gitignore` excludes common credential filenames and local
state, but ignore rules do not remove files that were already committed. Never
treat a passed scan as authorization to publish a working Nova publicly.

## Autonomous learning and review

Nova learns autonomously by default. When completed work produces a justified,
reusable improvement, the active coding agent may update a Nova-owned skill and
record the change in local Git. This is model-directed behavior, not a security
enforcement mechanism.

Organizations or owners that require human review before skill changes can set:

```yaml
skills:
  write_approval: true
```

Nova will then stage proposed skill changes for review instead of applying them
directly. This setting does not review external skills or restrict the native
agent's other file and tool permissions.

## Skills outside Nova

Native coding agents may expose user-level, global, project, plugin, managed,
or built-in skills alongside Nova's canonical library. Nova's root activation
does not audit, sandbox, hide, or disable those external sources. Review skills
before installing them and manage their trust through the runtime or source
that owns them.

Nova may use a relevant external skill, but its autonomous learning loop must
not modify or delete that source. External skill learning belongs with its
owner rather than in Nova's canonical library.

## Startup release check

When startup update checks are enabled, Nova sends a public unauthenticated
request to GitHub's Nova release endpoint at the configured interval. It does
not send memory, project context, prompts, tool output, or other Nova content.
Disable the check with `updates.check_on_startup: false` in `config.yaml`.

This is the only network request initiated by Nova's bundled hooks. It is
separate from network requests made by the coding agent or its tools.

## Installation and updates

The installer downloads a versioned archive and checksum from the same GitHub
release, rejects an unexpected archive path, and refuses to replace an existing
destination. The checksum detects corruption or a mismatched archive, but it is
not an independent publisher signature.

Nova never updates itself automatically. The bundled `update-nova` skill treats
an update as a reviewed merge and preserves owner-managed content. For managed
environments, review and pin the exact release before installation or update.

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
