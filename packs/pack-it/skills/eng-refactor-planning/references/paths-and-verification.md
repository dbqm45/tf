# Refactoring paths, intent archaeology and verifying numbers

## 1. Intent archaeology
| Question | Command | Notes |
|---|---|---|
| who gave the function its current shape and why | `git log -L :<function>:<file>` | the history of the function alone with diffs; for accurate function detection set the diff driver in `.gitattributes` (e.g. `*.go diff=golang`, `*.java diff=java`, `*.py diff=python`) |
| the history of a line range | `git log -L <from>,<to>:<file>` | when the function is not recognized |
| where the lines come from (with moves) | `git blame -w -C -C <file>` | `-w` ignores whitespace, `-C` tracks code moved from other files |
| whether the mechanism broke | `git log --oneline --grep='fix' -- <file>` + reading the descriptions | 0 fixes over years is evidence of a stable decision |
| a description of the decision outside the commit | the PR number from the commit description → `gh api repos/<o>/<r>/pulls/<no>` | read the "why", not only the "what" |

You write the verdict with evidence: `deliberate constraint — commit 27d536b (2020-03): batch INSERT for import
speed; 0 column-order fixes in the file history`. Without evidence: `unknown` + a question to the team (who remembers).

## 2. Strangler Fig
1. Choose an entry seam (a router, a facade, a queue) through which traffic goes to the old code.
2. The new implementation first handles a small, well-tested slice of behaviour; the seam routes only that
   slice there.
3. Compare the results (a parallel run or characterization tests), move further slices.
4. When the old code gets no traffic — remove it in a separate commit.
Fits: replacing a subsystem, an entry point, an integration. Risk: two systems live for a long time → a phase-out date in the plan.

## 3. Branch by Abstraction
1. Introduce an abstraction (an interface, a port) over the place where clients use the old code; the old implementation behind it.
2. Switch the clients to the abstraction — commit after commit, behaviour unchanged.
3. Build the new implementation next to it; the contract tests of the abstraction pass for both.
4. Switch over (a flag or configuration, preferably per client or per environment).
5. Remove the old implementation and — if it is no longer needed — the abstraction itself.
The main branch is releasable the whole time; instead of a long-lived branch you have a series of small PRs.

## 4. Mikado
1. Write down the goal as the root of the graph (e.g. "saving through `PostRepository` instead of direct queries").
2. Try to do the goal directly, with a time limit (e.g. 15 min). Write down every compilation or test error as a prerequisite node.
3. **Revert everything** (`git restore .` / `git reset --hard` on the working branch — with consent, when there are uncommitted changes by the human).
4. Choose a leaf (a prerequisite without its own prerequisites), do it, commit it, check the tests.
5. Go back to step 2 for the parent. You finish when the root can be done without errors.
You keep the graph in the project step (Mermaid `flowchart BT`), you tick off the nodes along with the commits.

## 5. A guard instead of a rebuild
The deliberate constraint stays, but you turn the risk "it is easy to forget about this" into "this cannot be broken":
- a test that fails on drift (e.g. two column arrays must have the same order → a test with sentinel
  values, `.claude/skills/eng-behavior-preserving-refactoring/references/examples.md`);
- a linter or ast-grep rule in CI (a pattern forbidden outside one file);
- validation in the code generator (e.g. a decorator must override all the interface methods or explicitly list them
  in a list of exceptions).
A guard is a pure addition: one `test:` or `build:` commit, reversible with a revert.

## 6. Verifying claims with ast-grep
| Claim | Pattern (checked on ast-grep 0.50.0) | Confirming a zero |
|---|---|---|
| "`save` called in 4 places" (TS) | `ast-grep run -p '$S.save($$$A)' -l ts --json=stream src \| wc -l` | `rg -n '\.save\(' src` |
| "`SaveMultiple` called in 4 places" (Go) | `ast-grep run -p 'func _() { $S.SaveMultiple($$$A) }' --selector call_expression -l go .` | `rg -n 'SaveMultiple\('` |
| "the interface has 54 methods" (Go) | `ast-grep run -k method_elem -l go <file>` (one line per interface method) | `rg -c` on the signatures in the file |
| "layer X does not override `Delete`" (Go) | `ast-grep run -p 'func ($R $T) Delete($$$A) $$$RET' -l go <layer-directory>` | `rg -n 'func \(.*\) Delete\(' <directory>` |
- **The silent-zero trap:** the pattern must be valid code in the given language. In Go the bare expression
  `$S.SaveMultiple($$$A)` does not parse at the file level and returns 0 matches without an error — it needs context
  (`func _() { … }`) and `--selector`. You check a suspicious zero with `--debug-query=ast` (`ERROR` nodes = a bad pattern)
  and always with `rg`.
- ast-grep skips comments and string literals and distinguishes `Save(` from `SaveMultiple(`; `rg` catches everything — the difference
  between the results is information (occurrences in comments, tests, generated code).
- No matches ends `ast-grep` with code 1 — in scripts do not treat it as a failure.
- Record the result with the tool version and the commit on which the count was made.

## 7. The exploration report template (`docs/project/<step>/research.md`)
```markdown
---
status: exploration
last_updated: <date>
tags: [refactor-opportunities]
verified_at_commit: <sha or "—">
---
# Refactoring options: <area>
**Intent:** what we are examining · what we are NOT doing (changes, decisions) · who decides and when
## List of problems and classification
| # | Problem (source) | CANDIDATE / input | Justification |
## Candidates
### K1: <name>
- Current shape (evidence/inference/unknown, file:line) · archetype thesis
- Intent: deliberate constraint / accidental complexity / unknown — evidence
- Feasibility: abstraction, reach, guards and tests (CI), prerequisite
## Refactoring options (ranking)
1. … current → target · why · reach · path · prerequisite
## Considered and rejected
## Verifying claims (ast-grep)
| Claim | Verdict | Evidence | Method |
## The human's decisions (filled in by the planning stage)
```
