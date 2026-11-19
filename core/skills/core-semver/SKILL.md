---
name: core-semver
description: Use for a version number (SemVer) — public API, a major/minor/patch bump, 0.y.z, pre-release versions.
metadata:
  review: "2027-10-09"
  catalog: "Use when you assign or check the version number of anything you release (a library, package, API, CLI, application, image, IaC module, the factory itself) — declaring the public API, which changes need major/minor/patch, the 0.y.z phase and the 1.0.0 release, pre-release versions and metadata, version order, deprecation, a release without changing a published version; the semver.py script computes the version without guessing. Not for the commit message format (core-conventional-commits) or the deployment strategy (the release skill, pack-it)."
  keywords: "semver, wersjonowanie, numer wersji, podbić wersję, major, minor, patch, wersja 1.0.0, 0.x, beta, rc, alpha, wydanie, release, tag v1.2.3, zmiana niezgodna wstecz, breaking change, przestarzałe, deprecated, następne wydanie, kolejność wersji, od jakiej wersji zacząć, version number, next version, version order, which version to start from"
---

# Semantic versioning (SemVer 2.0.0)

A version number is a promise to the user. MAJOR.MINOR.PATCH says whether an update can break something:
- **MAJOR** — a backward-incompatible change;
- **MINOR** — a new backward-compatible feature;
- **PATCH** — a backward-compatible fix.

**A script computes** the number, not the model's memory:
`python3 .claude/skills/core-semver/scripts/semver.py bump|next|compare|valid|check-changelog`.

## 1. Public API first
Without a declared public API compatibility cannot be judged (rule 1). Write it down in the README or in a
`PUBLIC_API.md` file before you assign 1.0.0. What usually belongs to it depends on the product type (details:
`references/public-api.md`):

| Product | Public API |
|---|---|
| library | exported functions, classes, types, exceptions, the minimal runtime version (Node, Java) |
| HTTP API | paths, methods, request and response fields, status codes, error format, authentication |
| CLI | commands, flags, exit codes, output format read by scripts |
| application or service | configuration (variables, keys), integration contracts, events, a data schema someone reads |
| IaC module, container image | input and output variables, ports, mount points, environment variables |

Internal details (private functions, code layout, log contents) are not part of the public API.

## 2. Which bump
| Change in the public API | Bump |
|---|---|
| removal, renaming, a change of type or meaning, a new **required** input field, narrowing the accepted values, a change of default behaviour, raising the minimal runtime version | **MAJOR** (minor and patch → 0) |
| a new feature, an optional parameter, a new field in the response, marking an element deprecated, a significant internal improvement | **MINOR** (patch → 0) |
| a bug fix without a contract change, a backward-compatible security patch, a dependency update without an API change | **PATCH** |
| only documentation, tests, CI, refactoring without a behaviour change | no release, or PATCH if you release |

- Several changes in one release: the **most serious** decides.
- A fix of a bug someone relies on (it changes the observable behaviour of the contract) is MAJOR, unless the
  behaviour was explicitly described as a bug.
- With Conventional Commits: `python3 …/semver.py next` computes the bump from the last `vX.Y.Z` tag (`!` and
  `BREAKING CHANGE` → major, `feat` → minor, `fix`/`perf` → patch). Check the result against the table above,
  because a commit can be mislabelled.

## 3. The 0.y.z phase and the 1.0.0 release
- A new project starts at **0.1.0**. In the 0.y.z phase anything may change (rule 4).
  - The factory's convention: an incompatible change → minor, the rest → patch. That is how `semver.py next` computes it.
- You release **1.0.0** when the product runs in production, someone relies on it, or you care about backward
  compatibility (FAQ). From 1.0.0 the public API is a commitment. Releasing 1.0.0 is the human's decision; the agent
  proposes it.

## 4. Pre-release versions and metadata
- Pre-release: `1.4.0-alpha.1`, `1.4.0-beta.2`, `1.4.0-rc.1`. They have lower precedence than `1.4.0`.
  - Number with a number after the dot (`rc.2`, not `rc2`), because `rc.10 > rc.9`, while `rc10 < rc9` (lexical
    comparison).
  - The next one: `semver.py bump 1.4.0-rc.1 pre` → `1.4.0-rc.2`; the release: `bump … release` → `1.4.0`.
- Build metadata: `1.4.0+sha.5114f85`. It **does not affect** the order; do not use it to tell releases apart.
- Check the order with the script (`semver.py sort …`). An example from the specification:
  1.0.0-alpha < 1.0.0-alpha.1 < 1.0.0-alpha.beta < 1.0.0-beta < 1.0.0-beta.2 < 1.0.0-beta.11 < 1.0.0-rc.1 < 1.0.0.

## 5. Release
1. Establish the last released version: the `vX.Y.Z` tag, the version file (`package.json`, `pom.xml`, `VERSION`),
   the CHANGELOG.
2. Classify the changes (section 2), compute the number with the script.
3. Update **every** place with the number at once: the version file, the CHANGELOG (newest entry on top, sections:
   Added, Changed, Deprecated, Removed, Fixed, Breaking), the installation docs.
4. `semver.py check-changelog CHANGELOG.md --version-file <plik>` — format, order and agreement with the version file.
5. The tag `v1.2.3` (the `v` prefix is a tag convention; the version itself is `1.2.3`). Creating the tag,
   `git push`, publishing the package or image only **after the human's consent**.

Rules:
- **A commit can be wrong about the intent, the diff cannot.** Before an automatic release check whether the files
  that go into the artifact changed since the last tag: `git diff --name-only v1.2.3..HEAD -- <ścieżki artefaktu>`
  (`npm pack --dry-run` shows the list of files in an npm package). No changes = no release, even with `feat:`; a
  change of files with only `chore:`/`docs:` = a warning for the human, not a silent skip.
- **You never change a released version** (rule 3): you do not move the tag and do not publish again under the same
  number. A new version fixes a bug in a release.
- **An accidental incompatible change in a minor:** release a new minor that restores compatibility. Describe the
  faulty version in the CHANGELOG and inform the users (FAQ).
- **Deprecation:** first a minor with a "deprecated" marker, a description of the replacement and documentation.
  Removal only in the next major, after at least one minor with the warning.
- Monorepo: each package has its own version (`nx release`).
- The API version number in the URL (`/v1/`) is a separate decision (the API design skill, pack-it: be-api-design).
  A change `/v1` → `/v2` usually goes with a major of the package or service.
- You do not raise the project's **dependency** versions without the human's request (core-stack-sync). This skill
  is about the version number of what you release.

## Checklist
- [ ] public API written down (README or PUBLIC_API.md)
- [ ] the most serious change classified; the number computed with `semver.py`, not from memory
- [ ] 0.y.z until the first stable version; 1.0.0 with the human's consent
- [ ] all version files and the CHANGELOG agree (`semver.py check-changelog`)
- [ ] no released version was changed; tag and publication with the human's consent

## Sources
- Semantic Versioning 2.0.0, semver.org (CC BY 3.0 licence; accessed 2026-10-03): rules 1–11, FAQ, the official
  regular expression (in `scripts/semver.py`).
- Conventional Commits 1.0.0 (mapping types to the bump — core-conventional-commits).
- The 10xDevs course, ed. 3 (2026), module 5, lesson 4 (versioning without manual bumping) — training material
  (accessed 2026-10-09).

Described in our own words.
