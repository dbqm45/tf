---
name: core-conventional-commits
description: Use when writing, reviewing or parsing a commit message or PR title — Conventional Commits, breaking changes, Change/Flag footers, version bump, commit-msg hook.
metadata:
  review: "2027-11-20"
  catalog: "Use when you write, review or classify a commit message or a PR title — Conventional Commits 1.0.0 (type, scope, `!`, body, footers), marking a breaking change, the factory's trace footers `Change:` and `Flag:`, the bump a set of commits implies (PATCH/MINOR/MAJOR), fixing a commit with the wrong type, revert commits, squash-merge PR titles, parsing history, and the commit-msg hook commit_msg.py. Not for the branch and PR strategy (core-git-workflow) or the content of a hand-written CHANGELOG (docs skill, pack-docs)."
  keywords: "commit message, komunikat commita, wiadomość commita, opis commita, zrób commit, zacommituj zmiany, zacommituj, napisz commit, jak nazwać commit, tytuł PR, tytuł pull requesta, conventional commits, konwencja commitów, typ commita, feat, fix, chore, refactor, scope commita, zakres commita, BREAKING CHANGE, zmiana niezgodna w commicie, wykrzyknik w commicie, stopka commita, trailer, Change:, Flag:, klucz zmiany w commicie, Refs:, zły typ commita, poprawić typ commita, amend, revert commit, squash merge tytuł, hook commit-msg, commitlint, semantic-release, release-please, nx release, jaki bump z commitów, make a commit, commit this, commit the changes, write a commit message, commit message format, PR title, commit type, commit scope, breaking change footer, wrong commit type, fix commit type, revert commit, squash merge title, commit-msg hook, commit footer, trailer, parse commit history"
---

# Commit messages — Conventional Commits plus the factory's trace footers

Format of every commit (and of the PR title under squash merge):
```
<type>(<scope>)!: <description>

<body: why, not what>

<Footer-Token>: <value>
```
Scope and `!` are optional, body and footers too. The precise rules, the reasons behind the format, the FAQ and
parsing recipes: `references/specification-and-faq.md`.

## Writing a message
1. **Read the repository first:** `git log --format=%s -20` — the language of descriptions, the scopes in use, the
   types the team uses. Follow them (a Polish history stays Polish; scope = ticket key if that is the local habit).
   A new repository: English.
2. **One commit = one logical change.** A bug fix and a new feature in the same work → two commits (`fix`, then `feat`),
   never one commit with a mixed type.
3. **Type** (lowercase in this repo; the list is open, only `feat` and `fix` are required by the spec):
   | Type | When | Bump |
   |---|---|---|
   | `feat` | new capability for users | MINOR |
   | `fix` | bug fix | PATCH |
   | `perf` | faster, same behaviour | PATCH in most release-tool configs — check yours |
   | `refactor`, `test`, `docs`, `style`, `build`, `ci`, `chore` | no user-visible change | none |
   | `revert` | undoes earlier commits (project convention, see below) | depends on what it undoes |
   The extra types follow `@commitlint/config-conventional`; they are convention, not part of the spec.
4. **Scope** names a part of the architecture: the Nx project name (or its `scope:` tag) in an Nx monorepo, a module or
   bounded context elsewhere. Never a person's name.
5. **Description:** imperative mood ("add", "remove", not "added"), lowercase start, no trailing period, header
   ≤ 72 characters (a ` (#123)` PR suffix does not count).
6. **Body** after one blank line: why the change was needed and what it affects.
7. **Footers** after one blank line, `Token: value`, tokens hyphenated (`Reviewed-by`, `Refs`). Task links go to
   `Refs: PROJ-123`, not into the description.
8. **Breaking change** — any incompatible change of the public API, whatever its type, also in early development:
   - `!` before the colon (`feat(api)!: …`), and/or
   - footer `BREAKING CHANGE: <what changed and how to migrate>` — exactly uppercase; `BREAKING-CHANGE:` is equivalent.
   With `!` alone the description must make the break clear; add the footer whenever users need migration steps.

## Trace footers (factory convention)
- Work that belongs to a change or slice with a key (`CHG-12`, `TSK-57`, a Jira key): **every** commit carries
  `Change: TSK-57` (several keys comma-separated: `Change: CHG-12, TSK-57`).
- A slice behind a feature flag also carries `Flag: payment-retry` (one key, no spaces).
- Keys come from the change plan or from the human — never invent one.
- `Change:` and `Flag:` are part of the factory's public API (release tracing reads them).

## The commit-msg hook
- Check by hand: `python3 .claude/skills/core-conventional-commits/scripts/commit_msg.py check <message-file>`
  (exit 0 ok, 1 rejected, 2 bad call).
- Install: `… commit_msg.py install` — **only when the human asks** (the hooks directory is protected). It writes
  `commit-msg` into git's hooks directory (respects `core.hooksPath`) and never overwrites a foreign hook: it prints the
  line to add instead.
- It enforces: header shape with a lowercase type, any scope, non-empty description ≤ 72 characters with no trailing
  period; a blank line after the header; `BREAKING CHANGE:`/`BREAKING-CHANGE:` uppercase with a description;
  `Change:` keys shaped like `TSK-57`; `Flag:` a single token. On a branch whose name contains a key
  (`story/tsk-57-retry`) the message must contain `Change: TSK-57`. Git's own messages (`Merge …`, `Revert "…"`,
  `fixup!`, `squash!`, `amend!`) pass unchecked; `#` comment lines and everything below the scissors line are ignored.

## Version bump from commits
| Commits since the last release | Bump |
|---|---|
| only `fix` (and `perf`, if configured) | PATCH |
| at least one `feat` | MINOR |
| at least one `!` or `BREAKING CHANGE` | MAJOR |
Release tools (`nx release`, semantic-release, release-please) compute version and changelog from this; commitlint in
the commit-msg hook keeps the input clean. Compute the number itself with
`python3 .claude/skills/core-semver/scripts/semver.py next`; 0.y.z, pre-releases, public API and deprecation are in core-semver.

## Fixing a commit with the wrong type
- Interactive rebase is not available in this agent environment.
- Last commit, **not pushed**, and the human explicitly asks → `git commit --amend` with the corrected header.
- Older or already pushed/published → do not rewrite history. Tell the human: a corrective commit, or a manual rebase
  on their side before merge. Default: put the next change in a new, correctly typed commit.

## Squash merge, reverts
- Squash merge: the PR title becomes the final commit, so it follows the same format; maintainers may tidy
  contributors' titles before merging.
- Reverts: the spec leaves them open. Here: `revert: <what is undone>` with `Refs: <sha>` (several SHAs comma-separated).
  Git's generated `Revert "…"` passes the hook unchanged.

## Example
Removed `isReserved` from `ResourceDto` in the booking module, replaced by `blockade.state`:
```
refactor(booking)!: replace isReserved with blockade.state

Reservation state now lives in one place, so the two flags can no longer disagree.

BREAKING CHANGE: ResourceDto.isReserved is removed; read blockade.state === "reserved" instead.
Refs: BOOK-88
Change: TSK-57
```
`!` and the footer → MAJOR. Imperative description, header of 58 characters. If the same work also fixed an unrelated bug, that
goes in a separate `fix(booking): …` commit.

More shapes:
- `feat(search): add fuzzy matching for hotel names` → MINOR
- `fix(payments): round amounts half-even before conversion` + `Refs: PAY-12` → PATCH
- `perf(reports): stream rows instead of loading the whole table`
- `chore(deps)!: drop Node 18 support` (bang only, the description says what breaks)
- `revert: restore the old retry policy` + `Refs: 9f2c1ab, 4e77d03`

## Checklist
- [ ] `git log` read: language, scopes, types follow the repository
- [ ] one logical change per commit; type and scope fit
- [ ] description imperative, ≤ 72 characters, no period; body says why
- [ ] breaking change marked (`!` and/or uppercase `BREAKING CHANGE:` with migration)
- [ ] `Change:` (and `Flag:`) footers when the work has a key; `check` passes
- [ ] no rewriting of pushed history; amend only unpushed and on request

## Sources
- Conventional Commits 1.0.0 — https://www.conventionalcommits.org/en/v1.0.0/ (accessed 2026-11-20). Restated in our own words.
- `@commitlint/config-conventional` type list — https://github.com/conventional-changelog/commitlint (accessed 2026-11-20).
- Git trailers — https://git-scm.com/docs/git-interpret-trailers (accessed 2026-11-20).
