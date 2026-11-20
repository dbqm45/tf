# Conventional Commits 1.0.0 — rules, reasons, FAQ and parsing

Contents: 1. The rules in our own words · 2. Why the format exists · 3. Common questions · 4. Parsing history ·
5. What the factory adds

Primary source: https://www.conventionalcommits.org/en/v1.0.0/ (licence CC BY 3.0, accessed 2026-11-20). Everything
below is a paraphrase with our own examples; read the original when wording matters. The spec uses RFC 2119 keywords;
here "required" and "allowed" stand in for them.

## 1. The rules in our own words
**Header**
1. A commit opens with a type: a noun such as `feat` or `fix`. After it may come a scope in parentheses and a `!`;
   then a colon and exactly one space are required. Shape: `type(scope)!: `.
2. `feat` is required when the commit adds a feature for users of the application or library.
3. `fix` is required when the commit repairs a bug.
4. A scope is optional. When present it is a noun for a part of the codebase, in parentheses straight after the type —
   e.g. `feat(checkout):`.
5. Straight after the colon and space comes the description: a brief summary of what the code change does.

**Body**
6. A longer body is allowed. It starts after exactly one blank line below the description.
7. The body has no fixed structure; it may hold several paragraphs separated by newlines.

**Footers**
8. After one blank line below the body (or below the description if there is no body) there may be any number of
   footers. Each is a token, a separator — either `: ` or ` #` — and a value. The idea comes from git trailers.
9. Tokens use hyphens where words would have spaces (`Reviewed-by`, `Signed-off-by`), so a footer cannot be confused
   with a body paragraph. The one token allowed to contain a space is `BREAKING CHANGE`.
10. A value can span several lines and contain spaces; a footer ends where the next token-plus-separator begins.

**Breaking changes**
11. An incompatible change has to be visible either in the header or in a footer.
12. Footer form: the token `BREAKING CHANGE` in capitals, a colon, a space, then what broke.
13. Header form: `!` directly before the colon. With `!` the footer becomes optional, and the description itself should
    convey the break.

**Openness and case**
14. Types beyond `feat` and `fix` are permitted (`docs`, `ci`, `perf`…).
15. Tools must accept any letter case for the parts of a commit, with one exception: `BREAKING CHANGE` has to be uppercase.
16. In a footer, `BREAKING-CHANGE` means the same as `BREAKING CHANGE`.

Example that exercises rules 1, 4, 6, 8 and 12:
```
feat(invoices): allow several billing addresses per customer

Large customers asked to invoice branches separately.

BREAKING CHANGE: Customer.billingAddress (object) is now Customer.billingAddresses (array).
Reviewed-by: Ola
Refs: INV-204
```

## 2. Why the format exists
The spec lists these benefits (paraphrased):
- changelogs can be generated from history;
- the next semantic version can be derived from commit types;
- teammates, users and other stakeholders see what kind of change happened;
- builds and releases can be triggered by commit type;
- a structured history is easier for newcomers to read and contribute to.

## 3. Common questions (the spec's FAQ, restated)
| Question | Answer in short |
|---|---|
| Early, fast-moving development — does it apply? | Yes; behave as if the product were already released, because someone (even your team) consumes it. |
| Upper or lower case types? | Either, as long as the project is consistent. This repository: lowercase (the hook enforces it). |
| A change fits two types? | Split it into two commits where possible — the format nudges towards smaller, focused commits. |
| Does it slow development? | It slows careless commits; over time it speeds up work across projects and contributors. |
| Does it restrict what types we may use? | It limits types with release meaning; you may add your own (`chore`, `ui`…) for other purposes. |
| How does it relate to SemVer? | `fix` → PATCH, `feat` → MINOR, any breaking marker → MAJOR, whatever the type. |
| How to version our own extension of the convention? | Use SemVer for the extension itself (e.g. a team's commitlint preset). |
| Wrong type used? | Before merge or release, edit history (interactive rebase). After release it depends on tooling; an unknown type just gets skipped by release tools. This repo's rule: see SKILL.md "Fixing a commit with the wrong type". |
| Must every contributor follow it? | No, if you squash-merge: maintainers can write clean messages when merging. |
| How are reverts written? | The spec deliberately leaves this open; tools and projects decide, typically with a `revert` type and a footer listing the reverted SHAs. |

Example of the squash case: a contributor's three commits `wip`, `fix typo`, `tests` become one commit with the PR
title `feat(export): add CSV export of bookings (#341)`.

## 4. Parsing history
- Header regex (groups: type, scope with parentheses, bang, description):
  `^(\w+)(\([^)]+\))?(!)?: (.+)$`
- A breaking change may be only in a footer — read the whole message: `git log -1 --format=%B <sha>`, not only `%s`.
- Quick views: `git log --format=%s v1.4.0..HEAD` (headers since a tag); `git log --grep='^feat' --format=%h %s`
  (approximate — `--grep` also matches body lines).
- Counting the bump by hand is error-prone; `python3 .claude/skills/core-semver/scripts/semver.py next` does it.

## 5. What the factory adds (not in the spec)
- Lowercase types, header ≤ 72 characters, no trailing period, imperative description — enforced by `commit_msg.py`.
- Trace footers `Change: <key>` and `Flag: <flag-key>`; required `Change:` on keyed branches.
- `revert:` type with `Refs: <sha>` for reverts.
- Scope taken from the architecture (Nx project, module, bounded context).
