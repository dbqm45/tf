---
name: eng-refactor-planning
description: Use when deciding what to refactor, in what order and how (too big a class, rewrite or not) — candidates, intent from history, right-sizing, reversible paths, ranking.
metadata:
  review: "2027-10-09"
  catalog: "Use when a debt report, a hotspot list or a 'this class is too big' complaint has to become a refactoring plan the human decides on — the problem list and CANDIDATE classification, current shape described with archetypes (Transaction Script, Table Module, Domain Model), intent from ADRs and git archaeology (deliberate constraint vs accidental complexity), right-sizing (stays / guard instead of a rebuild / rebuild), reversible paths (Strangler Fig, Branch by Abstraction, Mikado), a ranking of 2–3 options, verification of structural claims with ast-grep and rg, then a phased plan. Not for the debt audit alone (eng-tech-debt-audit), the proof of behaviour preservation during execution (eng-behavior-preserving-refactoring) or redesigning domain concepts (ddd-legacy-modernization)."
  keywords: "co refaktoryzować, od czego zacząć refaktoryzację, w jakiej kolejności refaktoryzować, plan refaktoryzacji, zrefaktoryzuj, zrefaktoryzuj serwis, zrefaktoryzuj klasę, klasa jest za duża, serwis jest za duży, za duży plik, za duży moduł, rozbić duży serwis, przepisać od nowa, przepisać moduł od zera, refaktoryzacja z raportu długu, ranking opcji refaktoryzacji, strangler fig, branch by abstraction, mikado, guard zamiast przebudowy, osłona zamiast przebudowy, świadome ograniczenie, przypadkowa złożoność, git log -L, git blame, archeologia gita, ile plików dotknie zmiana, zasięg zmiany, wymienić warstwę zapisu, bez długiej gałęzi, weryfikacja liczb w raporcie, ast-grep, what to refactor, refactoring plan, refactor this service, class too big, service too big, rewrite from scratch, refactoring order, strangler fig, branch by abstraction, mikado method, guard instead of a rebuild, deliberate constraint, accidental complexity, change reach, refactoring options ranking"
---

# Planning a refactoring — options for a human decision

"Refactor this" leaves three things unknown: the target shape, the history (is the odd part a quirk or a load-bearing decision?)
and the way back if it goes wrong. This skill turns findings into options with a ranking; the human picks one; only then is there a plan.

**Stages, each in its own session:** exploration (read-only, writes `research.md`) → the human reads it → decision and plan →
implementation. Exploration never changes code and never ends with "shall I go ahead?"; it ends with the report and the question
of which option to take. Every step states what is examined, what is deliberately not done, and who decides when.
A request to "plan and change it right away" gets the exploration report first.

## Procedure — exploration
1. **Problem list.** Write out every problem from the input (debt audit, hotspots, complaint), whatever its label. Findings from the
   input are evidence — do not re-derive them. Mark a problem **CANDIDATE** only when its fix changes code structure; a missing test or
   documentation gap is input to feasibility, not a candidate. If the real fix is a redesign of business concepts (two meanings of
   "customer", a rule split across contexts) → stop and refer to ddd-legacy-modernization.
2. **Three investigations per candidate**, as parallel read-only workers; every statement labelled **evidence / inference / unknown**
   with `file:line`:
   - **current shape** — where the logic lives, what responsibilities mix, which abstractions already exist; describe it on the
     archetype spectrum Transaction Script → Table Module → Domain Model with a service layer (e.g. "an overgrown transaction script");
   - **intent** — ADRs and design docs first, then git archaeology (`references/paths-and-verification.md` §2). Verdict:
     **deliberate constraint**, **accidental complexity** or unknown. The number of fix commits on the mechanism is evidence: zero fixes in
     years means it is stable. Essential complexity stays (it may be arranged better); accidental complexity is removed;
   - **feasibility** — the abstraction to use or create; change reach (from the input, else
     `python3 .claude/skills/eng-codebase-mapping/scripts/code_graph.py <repo> --impact <file>`, numbers confirmed with `rg`);
     existing guards and tests (check the CI config, not only the test directory); the first prerequisite step.
3. **Right-size each candidate:**

   | Finding | Decision |
   |---|---|
   | small module, simple logic | **stays as is** |
   | deliberate constraint (it is odd on purpose) | **guard instead of a rebuild**: a cheap deterministic check that fails on drift; the shape stays |
   | accidental complexity whose cost grows (hotspot = complexity × change frequency) | **rebuild** along a reversible path |

   Repay the highest "interest" first: the debt that slows down the changes happening now. A guard is a pure addition — one `test:` or
   `build:` commit that one revert undoes (a sentinel-value test, an ast-grep/linter rule in CI, a generator validation).
4. **Pick a reversible path** for each rebuild (details `references/paths-and-verification.md` §1):
   - **Strangler Fig** — new code at the edge (router, facade, queue), behaviour moved in slices, the system works at every moment;
     set a phase-out date for the old part;
   - **Branch by Abstraction** — an abstraction over the contact point, clients switched commit by commit, contract tests green for both
     implementations, mainline releasable, no long-lived branch;
   - **Mikado** — when everything depends on everything: try the goal in a time box, note each breakage as a prerequisite, **revert**,
     solve the leaves first, one commit each.
   A rewrite from scratch is listed as rejected: it throws away the knowledge stored in years of fixes.
5. **Ranking.** 2–3 strongest options, each: current → target shape, why here (cost of the debt vs cost of the change), reach,
   the reversible path in outline, the first prerequisite. Then **Considered and rejected**, one sentence of reason each.
6. **Verify structural claims** in a separate pass (`references/paths-and-verification.md` §3): every count or "X is called in N places"
   gets an `ast-grep` pattern; every zero is confirmed with `rg`; corrections are written in place as `5 (report: 4)`. The pass does
   **not** reorder the ranking or change intent verdicts — a discrepancy is logged "for a decision at the planning stage".
7. **Write** `docs/project/<step>/research.md` (template `references/paths-and-verification.md` §4) with front matter
   `status: exploration`, `last_updated`, `tags: [refactor-opportunities]`, `verified_at_commit`, and end with one question:
   "which option do we implement?".

## Procedure — decision and plan
- Run the conversation per core-plan-interview, starting with "which option do we implement?". New evidence found while planning is
  a separate question, not a silent change of the option.
- The plan is a narrow slice: one option, possibly plus a cheap guard. Characterization test first at a seam visible without editing
  the code (qa-spec-first-testing). Phases are separate reversible commits, cheapest and most self-contained first (the guard first),
  each with automatic and manual verification criteria.
- **The mechanism lands green, enforcement is enabled separately:** a new validation ships disabled (or warning-only), then is enabled
  per layer in its own commit, with a justified exception list.
- A section **What we are NOT doing** closes scope creep. Options of several weeks each become a campaign: phases with their own
  explore → plan → implement. A fresh-context reviewer reads the plan before implementation.
- Execution and the proof that behaviour stayed the same: eng-behavior-preserving-refactoring.

## Example
Input: debt audit of `billing/export` (7 findings): "`InvoiceExporter.py` is 2,400 lines", "batch insert writes values by position",
"`TaxedInvoiceSource` and `CachedInvoiceSource` decorators skip `list_corrections()`", "`InvoiceSource` has 31 methods", two missing
tests, one naming issue.

Exploration result (`docs/project/014-export-refactor/research.md`):
- CANDIDATES: positional batch insert, decorators missing overrides, the size of `InvoiceExporter.py`. Missing tests and naming → input
  to feasibility.
- Positional insert: `git log -L :write_batch:billing/export/writer.py` shows one commit from 2021 "batch insert, 9× faster on month-end"
  and **0 fix commits** since → **deliberate constraint** → **guard instead of a rebuild**: a sentinel-value test per column
  (`.claude/skills/eng-behavior-preserving-refactoring/references/examples.md`, example 4).
- Decorators: 3 incidents of corrections missing from exports, both decorators changed in 11 of the last 20 commits → accidental
  complexity, hotspot → **rank #1**: a generator validation "every decorator overrides every `InvoiceSource` method or lists the
  exception", shipped disabled, then enabled per layer.
- Splitting `InvoiceExporter.py` → **rejected**: 2 changes in 12 months, the size costs little now.
- Verification: "31 methods" → `ast-grep` on the protocol class gives `33 (report: 31)`; "`list_corrections` called in 4 places" →
  `5 (report: 4)`, the fifth in a generated client — ranking unchanged, noted "for a decision at the planning stage".
- Ends with: "Which option do we implement: #1 decorator validation, #2 the guard on the positional insert, or both in that order?"

## Checklist
- [ ] every input problem listed; CANDIDATES only for structural fixes; business-concept problems sent to ddd-legacy-modernization
- [ ] shape, intent (with `git log -L`/blame evidence) and feasibility per candidate, labelled evidence/inference/unknown with file:line
- [ ] right-sizing decision per candidate; guard considered before any rebuild
- [ ] 2–3 ranked options with a reversible path and first prerequisite; rejected options with reasons
- [ ] structural claims verified with ast-grep, zeros confirmed with rg, `N (report: M)` corrections, ranking untouched by verification
- [ ] no code changed; the report ends with the decision question

## Sources
- M. Fowler, *Patterns of Enterprise Application Architecture*, Addison-Wesley, 2002 — Transaction Script, Table Module, Domain Model.
- F. P. Brooks, "No Silver Bullet — Essence and Accident in Software Engineering", 1986 — essential vs accidental complexity.
- M. Fowler, "StranglerFigApplication" and "BranchByAbstraction", martinfowler.com/bliki (accessed 2026-10-10).
- O. Ellnestam, D. Brolund, *The Mikado Method*, Manning, 2014.
- M. Feathers, *Working Effectively with Legacy Code*, Prentice Hall, 2004 — seams, characterization tests.
- git documentation: `git-log` (`-L`), `git-blame` (`-w -C`), `gitattributes` (diff drivers), git-scm.com/docs (accessed 2026-10-10).
- ast-grep documentation, "Command Line Reference" and "Pattern Syntax" (ast-grep.github.io, accessed 2026-10-10); behaviour checked on
  ast-grep 0.50.0 (own run, 2026-10-10).
