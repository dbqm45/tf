---
name: core-semver
description: Use when picking the next version number of something you release — bump kind, 0.y.z vs 1.0.0, pre-releases, deprecation, computed by semver.py.
metadata:
  review: "2027-11-20"
  catalog: "Use when you assign or verify the version of anything the team releases (a library, an HTTP API, a CLI, an application or service, an IaC module, a container image, the factory itself) — what counts as public API, which change is major/minor/patch, the 0.y.z phase and the move to 1.0.0, pre-release labels and their ordering, build metadata, deprecation before removal, a release whose artifact did not change, a mistaken release, the changelog and version file in step, and the semver.py script that computes and checks the number. Not for the format of commit messages (core-conventional-commits), the deployment strategy of a release (the release skill, pack-it) or raising the project's own dependency versions (core-stack-sync)."
  keywords: "jaka wersja, następna wersja, numer wersji, podbić wersję, podbicie wersji, major minor patch, wersjonowanie semantyczne, semver, SemVer 2.0.0, wersja 1.0.0, kiedy 1.0.0, od jakiej wersji zacząć, wersja 0.1.0, faza 0.y.z, wersja przedpremierowa, pre-release, rc, beta, alpha, kolejność wersji, metadane builda, zmiana niezgodna wstecz, breaking change, przestarzała funkcja, deprecated, wycofanie funkcji, usunięcie funkcji, publiczne API, PUBLIC_API, tag wersji, tag v1.2.3, changelog a wersja, plik VERSION, wydanie bez zmian, paczka się nie zmieniła, automat wydań podbija wersję, semantic-release wersja, błędne wydanie, cofnąć wydanie, wersja obrazu, wersja modułu terraform, next version, version number, bump the version, which version, start at 0.1.0, when to release 1.0.0, prerelease ordering, build metadata, backward compatible, backward incompatible, deprecate then remove, public API, release tag, changelog version mismatch, release without changes, semver.py"
---

# Version numbers — classify the change, let the script compute

A version number is a promise about compatibility **relative to a declared public API**. You classify what
changed in that API, take the most severe change, and compute the number with the script — never by hand.

Script (run it, do not read it): `python3 .claude/skills/core-semver/scripts/semver.py`
| Call | What it gives |
|---|---|
| `valid 1.0.0-rc.1+b.5` | exit 0 = valid, 1 = invalid with the reason |
| `compare A B` / `sort V…` | precedence (-1/0/1) or an ascending list; build metadata ignored |
| `bump 2.4.1 major\|minor\|patch` | 3.0.0 / 2.5.0 / 2.4.2 |
| `bump 1.2.3 pre --id rc` → `bump 1.2.4-rc.1 pre` → `bump 1.2.4-rc.2 release` | 1.2.4-rc.1 → 1.2.4-rc.2 → 1.2.4 |
| `next [--since vX.Y.Z] [--path P] [--current V]` | bump suggested from commits since the last `vX.Y.Z` tag: `!` or `BREAKING CHANGE` → major, `feat` → minor, `fix`/`perf` → patch; in 0.y.z a breaking change → minor and everything else → patch. No tag → exit 2, pass `--current` |
| `check-changelog CHANGELOG.md [--version-file VERSION] [--strict-from V]` | `## [X.Y.Z]` headings valid, newest first, no repeats, newest = version file; from `--strict-from` the sections must fit the bump (Breaking/Removed → major, Added/Deprecated → at least minor). Exit 1 on problems |

## Procedure
1. **Public API written down.** README or `PUBLIC_API.md` lists what users may rely on. Without it a number means
   nothing — write the list first. What counts per product type: `references/public-api.md`.
2. **Last released version.** The newest `vX.Y.Z` tag, the version file and the top changelog entry. If they disagree,
   stop and reconcile them before computing anything.
3. **Did the artifact change?** Commit types describe intent and can be wrong; the shipped content cannot. Compare the
   files that go into the package since the tag: `git diff --name-only v1.4.0..HEAD -- src/ package.json` or
   `npm pack --dry-run` (image: the Dockerfile and its inputs; module: its `.tf` files).
   - nothing shipped changed → **no release**, even with `feat:` commits (CI, tests, docs only);
   - shipped files changed but only `chore:`/`docs:` commits → warn the human, the classification is probably wrong.
4. **Classify each change** (table below) and take the most severe one. Incompatible means: some existing correct use
   stops working, or silently behaves differently, without the user changing anything.
5. **Compute** with `bump` (or `next` as a cross-check against the commits) — the higher of your classification and
   `next` wins; explain a difference.
6. **Update every place that carries the number together:** version file(s), the changelog (new entry on top),
   install snippets in docs. Run `check-changelog` with `--version-file`.
7. **Tag** `vX.Y.Z` (the tag carries `v`, the version itself does not), push and publish — **only after the human
   agrees**. Never move a tag, never republish an existing number.

## Which part to raise
| Change in the public API | Bump |
|---|---|
| Incompatible: removed/renamed element, new required input, stricter validation, changed error type or status, removal of something deprecated | **major** (minor and patch reset to 0) |
| New compatible functionality: new export, optional parameter, new endpoint or field; **marking something deprecated** | **minor** (patch reset to 0) |
| Compatible bug fix, compatible security fix, dependency update with no API change | **patch** |
| Refactor, tests, CI, docs with no behaviour change | no release (or patch if you ship anyway) |

- **Deprecation then removal:** mark in a minor (warning, replacement, docs), keep it through at least one minor,
  remove in the next major. "Deprecated" alone never forces a major; the removal always does.
- **A fix people depend on:** if the "wrong" behaviour was documented or widely relied on, changing it is incompatible
  — judge against the declared API, not against intent.
- **Mistaken release** (an incompatible change shipped as minor/patch): do not rewrite it. Release a new version that
  restores compatibility, and note in the changelog which version was faulty. The incompatible change waits for a major.

## The 0.y.z phase and 1.0.0
- A new project starts at **0.1.0**. While the major is 0 the API may change at any time and users are warned.
- Factory convention in 0.y.z (also what `next` does): incompatible → minor, everything else → patch.
- Move to **1.0.0** when the thing runs in production, other people or systems depend on it, or you already care about
  backward compatibility. 1.0.0 is the human's decision: you propose it with reasons, they decide.
- From 1.0.0 onwards the table above applies strictly.

## Pre-releases and build metadata
- A pre-release appends `-label`: `2.0.0-beta.1`. It ranks **below** `2.0.0` and signals "not stable yet".
- Identifiers are compared one by one, left to right: numbers numerically, text in ASCII order, a number below text,
  and a longer list wins when all earlier parts are equal. So `alpha` < `alpha.1` < `beta` < `beta.2` < `beta.11` < `rc.1` < release.
- Always separate the counter with a dot: `rc.9` < `rc.10` numerically, but `rc10` sorts **before** `rc9` (text comparison).
- Flow: `bump X pre --id rc` repeatedly, then `bump … release`. Never publish two different builds under one pre-release label.
- Build metadata after `+` (`2.0.0+sha.5f3c1e`) is ignored for ordering: `2.0.0+a` and `2.0.0+b` are the same version.
  Never use it to tell releases apart.

## Edge cases
- **Monorepo:** each published package has its own version and tags (`pkg@1.2.0` or per-path `next --path`).
- **URL version** (`/v1/…`) of an HTTP API is a separate decision (be-api-design); `/v2` normally comes with a major.
- **Container images:** the full `1.4.2` tag is immutable; moving tags (`1`, `1.4`, `latest`) only move forward
  within compatible versions.
- **Our dependencies:** this skill is about what we release; raising the project's dependencies is core-stack-sync.
- **Commit format** for automatic bumps: core-conventional-commits.

## Example
Library at **2.4.1**. Since `v2.4.1`: an optional `timeout` parameter added to `fetch()`, and `legacyFetch()` —
deprecated in 2.3.0 — removed.
1. `git diff --name-only v2.4.1..HEAD -- src/` lists two source files → the artifact changed.
2. Optional parameter → minor; removal of a deprecated function → major. The most severe wins: **major**.
3. `python3 .claude/skills/core-semver/scripts/semver.py bump 2.4.1 major` → `3.0.0` (not 2.5.0: the earlier
   deprecation was the minor; the removal is the major).
4. CHANGELOG: `## [3.0.0]` with `### Removed — legacyFetch() (use fetch())` and `### Added — fetch(timeout)`; VERSION = 3.0.0;
   `check-changelog CHANGELOG.md --version-file VERSION` passes.
5. "Ready to tag `v3.0.0` and publish — shall I?" Tag only after a yes.

Ordering check: `sort 2.0.0-rc.10 2.0.0-rc.9 2.0.0 2.0.0-beta 2.0.0+sha.abc` →
`2.0.0-beta < 2.0.0-rc.9 < 2.0.0-rc.10 < 2.0.0 = 2.0.0+sha.abc`.

## Checklist
- [ ] public API written down (README or `PUBLIC_API.md`; the factory's own: `.tf/factory/PUBLIC_API.md`)
- [ ] the artifact really changed; the most severe change classified; the number computed by `semver.py`
- [ ] 0.y.z until the first stable API; 1.0.0 proposed, decided by the human
- [ ] version file(s) and changelog agree (`check-changelog` passes)
- [ ] no released version altered; tag, push and publication only after the human's consent

## Sources
- Semantic Versioning 2.0.0 and its FAQ — https://semver.org/spec/v2.0.0.html (accessed 2026-11-20). Rules restated
  in our own words; no specification text is quoted.
- Conventional Commits 1.0.0, mapping of commit types to bumps — https://www.conventionalcommits.org/en/v1.0.0/ (accessed 2026-11-20).
- `npm pack --dry-run` lists the files a package would contain — npm CLI docs, https://docs.npmjs.com/cli/commands/npm-pack (accessed 2026-11-20).
