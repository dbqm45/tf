# Reversible paths, git archaeology, verification of claims, the report

> **Contents:** 1. Reversible paths · 2. Intent from history — git archaeology · 3. Verifying structural claims with ast-grep and rg · 4. The exploration report template (`research.md`)

## 1. Reversible paths
All three keep the main line releasable and allow stopping half-way with a working system.

### Strangler Fig
- **When:** a module or subsystem with a natural entry point (HTTP routes, a facade, a queue consumer) whose behaviour can move in slices.
- **Steps:** put a seam at the edge (router, facade, queue) → implement one slice in the new code → route that slice to it → compare
  old and new (a parallel run on copies of real input, or characterization tests) → next slice → delete the old part when its traffic is zero.
- **Risk:** two systems living side by side indefinitely. Set a phase-out date and track the remaining slices.

### Branch by Abstraction
- **When:** an internal dependency used from many places (a persistence layer, a client library) must be replaced without a long branch.
- **Steps:**
  1. Introduce an abstraction over the contact point; the old implementation goes behind it unchanged.
  2. Switch clients to the abstraction commit by commit.
  3. Build the new implementation beside the old one; the same contract tests run against both.
  4. Choose the implementation by flag or configuration, per client or per environment; switch gradually.
  5. Delete the old implementation and, if it adds nothing, the abstraction itself.
- Every commit is releasable; no branch lives longer than a day or two.

### Mikado
- **When:** the goal change breaks things in many places and the order of prerequisites is unknown.
- **Steps:**
  1. Write the goal as the root of a graph.
  2. Try it directly in a time box (e.g. 15 minutes).
  3. Each breakage becomes a prerequisite node under the goal.
  4. **Revert everything** (`git restore .` / `git reset --hard` to the start). If the working tree holds the human's uncommitted changes,
     ask first.
  5. Pick a leaf, try it the same way; when it works without new breakage, commit it and tick the node.
  6. Repeat towards the root.
- Keep the graph in the plan as Mermaid, leaves at the bottom:
  ```mermaid
  flowchart BT
    a["InvoiceSource split into Reader + Corrections ✓ 3f2a1c"] --> goal["Exporter depends on InvoiceReader only"]
    b["CachedInvoiceSource delegates list_corrections"] --> a
    c["TaxedInvoiceSource delegates list_corrections"] --> a
  ```

### Rejected by default: rewrite from scratch
A rewrite loses the knowledge stored in fixes and edge cases, stops delivery or runs two systems in parallel for months. List it under
"Considered and rejected" with that reason unless the human brings evidence that the old code is beyond rescue.

## 2. Intent from history — git archaeology
| Question | Command |
|---|---|
| how did this function evolve? | `git log -L :<function>:<file>` |
| how did these lines evolve? | `git log -L <from>,<to>:<file>` |
| who wrote each line, ignoring whitespace and following moved/copied code? | `git blame -w -C -C <file>` |
| how many fixes touched the file? | `git log --oneline --grep=fix -- <file>` (also try the team's words: `bug`, `hotfix`, ticket prefixes) |
| what did the review say? | `gh api repos/<o>/<r>/pulls/<no>` (and `/comments`) for the PR named in the commit |

- `git log -L :<function>:` finds function boundaries with a diff driver; without one it guesses from lines that look like headers.
  Add to `.gitattributes` (locally, without committing, if the repo has none): `*.go diff=golang`, `*.java diff=java`, `*.py diff=python`.
- Read the commit message and the linked PR or ticket of the commit that introduced the odd shape. "9× faster on month-end" or
  "required by the bank's file format" is a **deliberate constraint**; "quick fix, refactor later" is **accidental complexity**.
- Zero fix commits on a mechanism in years is evidence it is stable; many fixes in the same place is evidence of accidental complexity.
- No history (squashed import, a zip) → the verdict is **unknown**; say so, do not guess.

## 3. Verifying structural claims with ast-grep and rg
Run the `ast-grep` binary — on Linux `sg` is usually the group-switching command from the login package.

| Need | Command |
|---|---|
| find matches as data | `ast-grep run -p '<pattern>' -l <lang> --json=stream <dir>` (one JSON object per line; count lines) |
| see how ast-grep parsed the pattern | `ast-grep run -p '<pattern>' -l <lang> --debug-query=ast` — `ERROR` nodes mean the pattern is not valid code |
| match a fragment that is not valid alone | wrap it in valid context and pick the node with `--selector <node kind>` |
| list nodes of one kind | `-k <node kind>` |
| confirm a zero | `rg -n '<plain text>' <dir>` |

- **No matches → exit code 1.** It is a result, not a failure of your script; handle it explicitly.
- **The silent zero.** A pattern that does not parse as code in the target language matches nothing and reports nothing. Example in Java:
  `ast-grep run -p 'source.listCorrections($A)' -l java src/` may return 0 because a bare expression is not a valid Java compilation
  unit; wrap it — `-p 'class X { void m() { source.listCorrections($A); } }' --selector method_invocation` — and check with
  `--debug-query=ast`. Whatever the tool says, every zero gets an `rg` check.
- ast-grep skips comments and strings and separates `save(` from `save_batch(`; `rg` catches everything. The difference between the two
  counts is information (generated code, tests, docs), not noise — say where it comes from.
- Write corrections in place, keeping the trace: `33 (report: 31)`. Record the ast-grep version (`ast-grep --version`) and the commit.
- Do **not** reorder the ranking or change intent verdicts in this pass. A count that changes the picture is logged in "Verifying claims"
  as "for a decision at the planning stage".

Claims table:

| Claim | Verdict | Evidence | Method |
|---|---|---|---|
| `InvoiceSource` has 31 methods | refined: 33 (report: 31) | `billing/export/source.py:12-140` | ast-grep `def $M($$$)` in the class, rg `def ` |
| `list_corrections` called in 4 places | refined: 5 (report: 4) | `billing/export/client_gen.py:88` (generated) | ast-grep call pattern + rg |
| no direct SQL outside `writer.py` | confirmed: 0 | — | ast-grep `cursor.execute($$$)` → 0, rg `execute(` → only `writer.py` |

## 4. The exploration report template (`research.md`)
```markdown
---
status: exploration
last_updated: 2026-11-20
tags: [refactor-opportunities]
verified_at_commit: <sha>
---
# <module> — refactoring options

## Intent
What this exploration examines, what it deliberately does not do (no code changes, no plan), who decides and when.

## Problems and classification
| # | Problem (from input) | Source | CANDIDATE? | Why / why not |

## Candidates
Per candidate: current shape (archetype), intent (deliberate constraint / accidental complexity / unknown, with history evidence),
feasibility (abstraction, reach, guards and tests, first prerequisite), right-sizing decision. Labels evidence / inference / unknown, file:line.

## Refactoring options (ranking)
1. <option> — current → target; why here; reach; reversible path; first prerequisite.
2. …

## Considered and rejected
- <option> — one-sentence reason.

## Verifying claims (ast-grep)
Tool version, commit, the claims table, discrepancies "for a decision at the planning stage".

## Human's decisions
Which option do we implement? (filled in at the planning stage)
```
