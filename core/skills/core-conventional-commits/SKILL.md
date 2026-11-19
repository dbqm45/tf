---
name: core-conventional-commits
description: Use for a commit message and a PR title (Conventional Commits) — types, fixing a wrong type, BREAKING CHANGE, SemVer.
metadata:
  review: "2027-10-17"
  catalog: "Use when writing, reviewing and parsing commit messages and PR titles per Conventional Commits 1.0.0 — types, scope, !, BREAKING CHANGE, footers, revert, the SemVer bump, a changelog from history (nx release). Not for the branch and PR strategy (core-git-workflow) or the content of a hand-written CHANGELOG (the documentation skill, pack-docs)."
  keywords: "komunikat commita, commit message, wiadomość commita, opis commita, tytuł PR, BREAKING CHANGE, feat, fix, chore, commitlint, narzędzie do wydań, policzyło wersję, wersja z commitów, usunąłem pole z DTO, zmiana łamiąca w commicie, semantic-release, release-please, PR title, commit type, wrong commit type, breaking change in a commit, version from commits, removed a field from a DTO, zrób commit, zacommituj zmiany, make a commit, commit these changes"
---

# Conventional Commits 1.0.0

## Format
```
<type>[(<scope>)][!]: <description>

[body — why, not what; paragraphs separated by a blank line]

[footers: Token: value  or  Token #value]
```
- **Type** required; **scope** optional, in parentheses — a part of the code.
- **Description** right after `: `; in the imperative mood, **in the repository's commit language** (from `git log`; English in a new repo), no full stop, ≤ 72 characters.
- **Body** after one blank line; **footers** after another blank line. Footer tokens with hyphens instead of spaces
  (`Reviewed-by`, `Refs`); the exception: `BREAKING CHANGE`.
- Letter case does not matter to tools, **except** `BREAKING CHANGE` (always upper case; `BREAKING-CHANGE`
  is a synonym). Keep one convention in the repo (ours: the type in lower case).

## Types
| type | when | SemVer |
|---|---|---|
| `feat` | a new feature for the user (MUST) | MINOR |
| `fix` | a bug fix (MUST) | PATCH |
| `perf` | a performance improvement without a change of behaviour | PATCH* |
| `refactor` | a change of structure without a change of behaviour | — |
| `test` | only tests | — |
| `docs` | only documentation | — |
| `style` | formatting with no effect on meaning | — |
| `build` | the build system, dependencies | — |
| `ci` | CI configuration | — |
| `chore` | other maintenance work | — |
| `revert` | reverting commit(s) | depends on the reverted one |

\* depending on the configuration of the release tool. The spec requires only `feat` and `fix`; the other types are a convention
(`@commitlint/config-conventional`) — the list is open, stick to the one adopted in the repo.

## Scope
- A scope consistent with the architecture: in an Nx monorepo — **the Nx project name** (or the value of the `scope:` tag), outside Nx — a module
  or a DDD context. Never the author's name.
- Before the first commit in someone else's repo check `git log` — if the repo gave the scope a different meaning (e.g. a task
  key), stick to it.

## Breaking changes
- `!` before the colon: `feat(api)!: remove v1 endpoints` — the footer is then optional, and the description describes the change.
- or the footer: `BREAKING CHANGE: <co i jak migrować>`.
- Every breaking change means **MAJOR**, regardless of the type. Mark it in the early phase of a project too (spec FAQ).

## SemVer, changelog, nx release
| Commits since the last release | Bump |
|---|---|
| only `fix` (and possibly `perf`) | PATCH |
| at least one `feat` | MINOR |
| `!` or `BREAKING CHANGE` in any | MAJOR |

`nx release` computes the version and the changelog from history (also per project, by scope/paths); similarly
semantic-release, release-please. Validation: commitlint in the `commit-msg` hook. That is why the format is a **contract**, not aesthetics.
The number is computed by `python3 .claude/skills/core-semver/scripts/semver.py next`. The SemVer rules (the 0.y.z phase, pre-release
versions, the public API, deprecation) are described in core-semver.

## Practical rules
- One commit = one logical change; two types fit → two commits.
- References to tasks in a footer (`Refs: PROJ-123`), not in the description.

## The trace of a change in footers (`Change:`, `Flag:`)
When the work belongs to a change or a slice with a key (`CHG-12`, `TSK-57`, a Jira key), every commit has the footer
`Change: <klucz>` — through it release tracking tools link the commit to the slice, and the slice to the change. A commit of a slice
behind a flag also gets `Flag: <klucz-flagi>`:
```
feat(payments): retry failed payment

Change: TSK-57
Flag: payment-retry
```
- A key shaped like `[A-Z][A-Z0-9]+-[0-9]+`; several keys separated by commas (`Change: TSK-57, TSK-58`). You take the key
  from the change plan or from the human, you do not make it up.
- The `commit-msg` hook checks the header, the footers and — on a branch with a key in its name (`story/tsk-57-…`) — requires
  `Change:` with that key. Installation at the human's request (the git hooks directory is protected):
  `python3 .claude/skills/core-conventional-commits/scripts/commit_msg.py install`; it does not overwrite someone else's hook,
  it only gives the line to add. By hand: `commit_msg.py check <plik-wiadomości>`.
- With a squash merge the PR title = the final commit, so the PR title is in this format too; on a squash the maintainer can
  tidy up the contributors' messages.
- Revert: the spec does not define it — a project convention (ours: the `revert` type + `Refs: <sha>`).

## Fixing a wrong type
The spec suggests `git rebase -i` before the merge — **not available here** (no interactive mode). Instead:
- the last, **unpushed** commit and the user explicitly asks → `git commit --amend`;
- deeper in history or already published → do not rewrite history; tell the user (a corrective commit or a manual rebase);
- by default: the next change in a new, correctly classified commit.

## Examples
```
feat(booking): block resource for selected time slot
fix(pricing): round partner discount to minor units
feat!: send an email to the customer when a product is shipped
refactor(availability)!: replace isReserved flag with blockade state

BREAKING CHANGE: ResourceDto.isReserved removed; read blockade.state instead.
```
```
fix: prevent racing of requests

Introduce a request id and a reference to latest request. Dismiss
incoming responses other than from latest request.

Reviewed-by: Z
Refs: #123
```
```
revert: let us never again speak of the noodle incident

Refs: 676104e, a215868
```

## References index
- Read `references/specification-and-faq.md` when you need the literal wording of the 16 rules (MUST/SHOULD/MAY), the
  specification's FAQ or commit parsing (regex, `git log` commands).

## Checklist
- [ ] The type chosen from the table; one commit = one change.
- [ ] Scope = the Nx project / module name (or the repo's convention from `git log`).
- [ ] The description in the repo's commit language, imperative mood, no full stop, ≤ 72 characters.
- [ ] A breaking change marked with `!` or `BREAKING CHANGE:` with migration instructions.
- [ ] References to tasks in footers.

Source: conventionalcommits.org/en/v1.0.0 (CC BY 3.0) — content described in our own words, rule quotes in references.
