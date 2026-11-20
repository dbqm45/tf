# Sharing skills across repositories

When the same skills should serve several repositories or teams, pick the simplest channel that keeps one source of truth
and lets every consumer see which version it runs.

## Channels
| Channel | Fits | Watch out for |
|---|---|---|
| A factory pack (`packs/pack-*` or an external pack via `install.py --pack-dir <source>`) | Skills that belong with the factory's roles, hooks and gate | The pack must pass the same contract as built-in packs: id prefix, `requires.core`, the skill gate; foreign skills go through `skill_audit.py` on install |
| A Claude Code plugin marketplace (a repository with `.claude-plugin/marketplace.json`) | Skills used outside the factory, by people who install plugins themselves | Each consumer chooses when to update; private repositories need git access for every consumer |
| Copying the skill directory | A one-off, one repository | No update path; copies drift - avoid for anything maintained |

## What any installer must guarantee
These are the properties the factory's own installer (`core/factory/install.py`, `update.py`, `uninstall.py`) provides;
hold any other channel to the same bar:
- **Idempotent.** Running it again is an update, not a second copy.
- **Marked blocks.** Text it adds to files people also edit (instructions files, ignore files) sits between begin/end markers,
  so an update replaces only its own block. A begin marker without an end marker stops the run instead of guessing.
- **Manifest with hashes.** Every installed file is recorded with its hash, so an update can tell a factory file from one the
  project changed: a project file with the same name is left alone and reported, a locally edited factory file is
  overwritten and listed, and an obsolete factory file is removed only if its hash still matches.
- **Clean removal.** Uninstalling removes what was installed and nothing else.
- **No secrets in the package.** Credentials for private sources come from the consumer's own git or registry login.

## Versions
- Tag releases with SemVer (core-semver): renaming a skill, a cited section number, or an output line that a hook parses is a
  breaking change for consumers; new scenarios or wording fixes are a patch.
- Consumers pin a tag (`--pack-dir <url>#<tag>`; without a ref the installer takes the latest `vX.Y.Z` tag) and update on purpose.
- Every shared skill keeps its scenario file next to it, so consumers can run the gate after an update.

## Before building a channel
Ask whether one is needed: if two repositories share three skills, a pack in the factory is usually enough. A separate
marketplace or a private package registry adds hosting, access control and a release process that someone must own.

## Sources
- Claude Code docs, "Create and distribute a plugin marketplace", code.claude.com/docs/en/plugin-marketplaces - accessed 2026-11-20.
- Semantic Versioning 2.0.0, semver.org (paraphrased through core-semver).
- Factory installer behaviour: `core/factory/install.py` (docstring and marker constants), read 2026-11-20.
