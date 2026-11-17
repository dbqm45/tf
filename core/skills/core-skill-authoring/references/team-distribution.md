# Distributing your own skills and rules in a team


Skills, rules, commands and agent configuration templates are code executed with every change: they need versions,
change review and controlled distribution. Copying between repositories makes versions drift apart after a few weeks.
This factory's installer (`.tf/factory/install.py`, `.tf/factory/update.py`) implements the properties described below — a working
pattern to compare with.

## 1. Requirements — the measure of every solution
- one source of truth (a repository with the artifacts);
- a version per SemVer (core-semver), a breaking change = a new major version;
- control over who reads and who publishes;
- installation, update and **a clean uninstallation**;
- delivery to every AI tool in the team — only the target directories differ (e.g. `.claude/skills/`,
  another tool's rules directory).

## 2. Choosing the channel — the recipient decides
| Recipient | Channel | Start cost | Maintenance cost |
|---|---|---|---|
| a team on one git platform | a repo with tags or a package in that platform's registry | small | a read token for recipients outside the organisation |
| an organisation with its own cloud and registry management | an artifact registry in the cloud, configuration as code, login through OIDC | an account + infrastructure code | permissions, rotation |
| recipients on different stacks, access granted over time | your own API + CLI | a full product | the API, authentication, the client |
| one AI tool across the whole team | that tool's plugin marketplace | zero | dependence on the vendor's channel |
Anti-pattern: an "impressive" channel instead of one fitted to the recipient.

## 3. The installer — mandatory properties
- **Idempotent:** a second run gives the same result.
- **Blocks with markers** in files edited by people (`CLAUDE.md`, `AGENTS.md`): you replace only the middle of
  the begin/end block. One marker without the other = a damaged block → abort with a message. Reject content that itself contains
  markers — otherwise the next installation will delete someone else's text.
- **A manifest** in the recipient's repo: the package, the version, the tool, a list of files with hashes. Uninstallation removes exactly the files
  from the manifest, does not depend on `node_modules` or the package manager's scripts; a damaged manifest → it removes nothing.
- **A locally changed file** is overwritten like a dependency in `node_modules`: changes are made at the source and a new version
  is released; the recipient's configuration (e.g. `.tf/config/config.yaml`) stays, and new keys are added.
- **Copying** works everywhere (also with a one-off run from a cache that disappears); links only with
  a permanent dependency.
- **Dependencies between skills** declared in the header; choosing a subset goes through dependency resolution.
- An error of a post-install step does not break the installation of the project's dependencies — a warning instead of a failure.
- A new version of a foreign skill goes through the audit before being written (`.tf/factory/skill_audit.py`, core-agent-security §4a).

## 4. A private package — authentication and releases
- The recipient's repo commits only the mapping of the package scope to the registry, **never** a token.
- Publishing from CI with write permission to the registry and a short-lived job token (pack-it: ops-ci-cd).
- Reading: within the same organisation the CI job token is often enough; outside it (another repo, a foreign CI, build platforms)
  a token with read rights from an environment variable is needed, locally a login to the registry. The details depend on
  the registry and the token type — check its documentation [unverified in this session].
- Registries usually reject republishing the same version → the version is computed by an automaton (`semver.py`).
- A release only when since the last tag **the files that go into the package changed** (the diff), regardless of the commit type.

## 5. Your own API + CLI as a security boundary
- A package signature (e.g. Ed25519, the public key built into the client): first the content hash agreement, then the signature.
- A list of allowed API hosts built into the client — the address cannot be switched with an environment variable.
- A short-lived token with permissions re-checked on refresh.
- The API–client contract generated from an OpenAPI specification: a change breaking the client shows up at compile time.

## 6. Before you build
The first version: one source repo, one test package, a manual installation in one project. Release automation
and further channels you add only when someone really fetches new versions.

## 7. Example
A team of 8 people, all repos in one organisation on a git platform, two AI tools. The choice: an `ai-toolkit` repo
with SemVer tags and a package in the platform's registry; the installer copies skills to `.claude/skills/` and rules to the directory
of the second tool, adds a block between markers in `CLAUDE.md` and `AGENTS.md`, writes the manifest. CI publishes
only when the package's files change. Rejected: your own API + CLI (one recipient, no need to grant access over time).

The 10xDevs course, ed. 3 (2026), module 5, lesson 4 — training material (accessed 2026-10-09). Described in our own words.
