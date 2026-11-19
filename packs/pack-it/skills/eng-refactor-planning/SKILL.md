---
name: eng-refactor-planning
description: Use when you must choose from the debt what to refactor — a ranking of options checked in the code, Strangler, Mikado, a plan.
metadata:
  review: "2027-10-09"
  catalog: "Use when from a list of debt, risks or hotspots you must choose what to refactor, into what target shape and by which reversible path — classifying candidates, three perspectives (the current shape in the archetypes Transaction Script / Table Module / Domain Model, the intent from git history and ADRs, feasibility), right-sizing (stays / a guard instead of a rebuild / a rebuild), Strangler Fig, Branch by Abstraction, Mikado, a ranking of 2–3 options with the rejected ones, verifying the numbers with ast-grep with zeros confirmed by rg, the human's decision and a plan of phases. Not for the debt audit alone (eng-tech-debt-audit), the proof of behaviour preservation during execution (eng-behavior-preserving-refactoring) or redesigning domain concepts (ddd-legacy-modernization)."
  keywords: "co refaktoryzować, plan refaktoryzacji, plan refaktoru, opcje refaktoryzacji, ranking refaktoryzacji, refactor opportunities, od czego zacząć refaktor, zrefaktoruj moduł, przepisać od zera, strangler fig, branch by abstraction, mikado, odwracalna ścieżka, docelowy kształt modułu, świadome ograniczenie, przypadkowa złożoność, guard zamiast przebudowy, archeologia gita, git log -L, what to refactor, refactoring plan, refactor plan, refactoring options, refactoring ranking, where to start a refactor, refactor the module, rewrite from scratch, reversible path, target shape of the module, deliberate constraint, accidental complexity, guard instead of a rebuild, git archaeology"
---

# From debt to a refactoring plan

"Refactor this module" is an assignment without a goal (what shape at the end?), without history (what is a quirk, and what is
a load-bearing decision?) and without a way back (you will not verify 40 files at once piece by piece). So you assign the agent **options
with a ranking**, and the refactor starts with the human's decision. Input: a debt report (eng-tech-debt-audit), a flow
analysis (`.claude/skills/eng-codebase-mapping/references/flow-analysis.md`) or a list of hotspots.

## Stages (each in a separate session, the intent written at the top of the step — core-project-record)
**exploration → the human's reading → decision and plan → implementation.** Exploration only reads and ends with a report.
It does not change code and does not end with the question "do you approve?", because that forces a decision without reading. The intent
of the step: what we are examining, what we are not doing at this stage (changes, decisions), who decides and when.

## 1. The list of problems and classification (at the start of the report, for the human to audit)
- Write out **every** problem from the input, regardless of its label (debt, risk, hotspot, finding). You treat the findings of the input
  as collected evidence — you do not derive them anew.
- **CANDIDATE** = the fix changes the structure of the code. The rest (a missing test, a gap in the documentation) is not a candidate, but
  remains as input to the assessment of feasibility and cost.
- Is the real fix a redesign of business concepts, not of the structure? → stop at this candidate
  and refer to ddd-legacy-modernization.

## 2. Three perspectives on a candidate (three executors in parallel, read-only)
Every claim with the label evidence / inference / unknown and `file:line`. Missing data = `unknown`, not a guess.
- **a) The current shape:** where the logic lives, how responsibilities mix, which abstractions already exist. A thesis
  in the language of archetypes: **Transaction Script** (a procedure per request) · **Table Module** (one instance per table)
  · **Domain Model + Service Layer** (data and behaviour together, a thin layer of operations). It is a spectrum, not a ranking —
  e.g. "an overgrown Transaction Script: 180 lines of validation, counters and transactions in one function; the logic
  needs a model behind a service layer".
- **b) Intent (history):** first ADRs and design documents, then git archaeology —
  `git log -L :<function>:<file>`, `git blame -w -C <file>`, commit and PR descriptions. Verdict: **deliberate constraint**
  (a load-bearing decision) / **accidental complexity** / `unknown`. The number of fix commits for a mechanism is also
  evidence (e.g. 0 fixes over 6 years). Essential complexity (from the nature of the problem) stays — at most it can be better
  arranged; you remove the accidental one.
- **c) Feasibility:** an existing or a new abstraction, the reach of the change from the input report (missing → `python3
  .claude/skills/eng-codebase-mapping/scripts/code_graph.py <repo> --impact <file>`: the files at the 1st and 2nd step and the tests;
  confirm the numbers with `rg`), existing guards
  and tests (check the CI configuration, not only the test directory), the first prerequisite step.

## 3. Right-sizing
| Verdict | Move |
|---|---|
| a small module, simple logic | **stays** a Transaction Script |
| a deliberate constraint | **a guard instead of a rebuild**: a cheap, deterministic test, a linter rule or validation in the generator; the shape unchanged, reversible with one revert |
| accidental complexity whose cost grows (a hotspot: complexity × change frequency) | **a rebuild** by a reversible path (§4) |
Without this filter you get patterns everywhere and value nowhere. The order of repayment: first the debt with the highest
"interest", that is the one that slows down current changes.

## 4. Reversible paths
- **Strangler Fig:** new code grows at the edges of the old one, you move behaviour piece by piece, you phase out the old; at every
  moment the whole works. For replacing a subsystem or an entry point.
- **Branch by Abstraction:** an abstraction over the contact point → the old implementation behind it → the new one next to it → switching
  (a flag, configuration) → removing the old one. The main branch is releasable the whole time; no long-lived branch.
- **Mikado:** try the target change, write down what broke (a graph of prerequisites), **revert**, solve from the leaves to the
  root; every leaf is a small, separately reversible commit. The answer to "everything depends on everything".
- **Rewriting from scratch — no:** it loses the knowledge embedded in the fixes; cheap code generation does not change that.
Details of the steps, the characterization test and graph examples: `references/paths-and-verification.md`.

## 5. The exploration report — the section "Refactoring options (ranking)"
- **The 2–3 strongest options**, each: current → target shape · why this place (the cost of the debt vs the cost of the change)
  · reach · a sketch of the reversible path · the first prerequisite.
- **Considered and rejected** — each with a one-sentence reason (e.g. "deliberate constraint → guard").
- **Verifying the structural claims** on which the ranking stands ("54 methods", "4 calls", "overrides A,
  but not B"), in a separate run:
  1. every claim → a pattern `ast-grep run -p '<pattern>' -l <language> --json=stream` (the `ast-grep` binary;
     `sg` on Linux is usually the change-group command, not ast-grep);
  2. **confirm every zero from ast-grep with a plain `rg -n '<text>'`** — a zero may mean a bad pattern (e.g. in Go
     a bare call without the function context does not parse and gives 0 matches without an error);
  3. corrections in place with a trace: "5 (report: 4)"; a table claim → verdict (confirmed / refined /
     refuted) → evidence `file:line` → method;
  4. you **do not change** the ranking or the intent verdicts while doing this — you add the discrepancy "for a decision at the
     planning stage".

## 6. Decision and plan
- A conversation per core-plan-interview; **the first question: "which option do we implement?"** — accepting the ranking is an explicit
  decision. New evidence found during planning (e.g. a gap turned out to be a live bug) is a separate question, not a silent
  addition to the plan.
- A narrow slice: one option + possibly a cheap guard. The plan has these properties:
  - a characterization test before touching uncovered code, in a place where the behaviour is visible without editing
    the protected code (eng-behavior-preserving-refactoring);
  - phases = separate reversible commits, from the cheapest and most self-contained one (the guard first);
  - every phase with criteria for automatic and manual verification;
  - **the mechanism lands green, you enable enforcement in a separate commit** (e.g. validation disabled by default,
    then enabled per layer, with a list of exceptions with a justification);
  - a section "What we are NOT doing".
- Several options worth weeks of implementation → a campaign of phases (each with its own step: exploration → plan →
  implementation), not one big plan. A fresh context reviews the plan before implementation.

## Example
**Input:** a debt report for the message-saving module — 4 candidates. **Exploration result:**
- The audit's favourite "positional arrays of 18 columns in two functions" → `git log -L` shows a commit from 2020:
  a deliberate replacement of reflective saving with a batch INSERT for import speed; 0 column-order fixes in the history →
  **deliberate constraint → guard**: a test with sentinel values, one `test:` commit, the code untouched.
- Ranking #1: hand-written decorating layers over the `Store` interface — methods that are not overridden pass silently lower (the batch
  save bypasses search indexing) → completeness validation in the layer generator, disabled by default,
  enabled per layer. Verification: "the interface has 54 methods" → confirmed (ast-grep); "4 calls to
  `SaveMultiple`" → 5 (report: 4), the fifth in a test — added "for a decision at the planning stage".
- Rejected: "splitting `post.go` (3957 lines)" — accidental complexity, but the file rarely changes; it waits.
- The plan (after the human's decision): phase 1 the array guard, phase 2 validation in the generator (disabled), phase 3 enabling it
  for two layers; "What we are not doing": splitting `post.go`, changing the shape of the batch save.

## Checklist
- [ ] the list of problems and the CANDIDATE / input classification at the start of the report
- [ ] every candidate: the shape in archetypes, the intent verdict with evidence (ADR / commit / PR) or `unknown`
- [ ] right-sizing applied; deliberate constraints got a guard, not a rebuild
- [ ] a ranking of 2–3 options + the rejected ones with a reason; numbers verified with ast-grep, zeros confirmed with `rg`
- [ ] the human made the decision; the plan: characterization, phase commits, verification, enforcement separately, "what we are not doing"

## Sources
- The 10xDevs course, ed. 3 (2026), module 4, lesson 4 (refactoring with an agent) and its prompts (exploring options,
  verification with ast-grep) — training material (accessed 2026-10-09); described in our own words.
- M. Fowler, *Patterns of Enterprise Application Architecture* (2002) — logic archetypes; F. Brooks, "No Silver
  Bullet" (1986) — essential and accidental complexity; M. Fowler, [Strangler Fig Application](https://martinfowler.com/bliki/StranglerFigApplication.html)
  and [Branch By Abstraction](https://martinfowler.com/bliki/BranchByAbstraction.html); O. Ellnestam, D. Brolund,
  *The Mikado Method* (Manning, 2014); M. Feathers, *Working Effectively with Legacy Code* (2004) — seams and characterization
  tests (attributions after the lesson, accessed 2026-10-09).
- ast-grep 0.50.0 (`ast-grep run --help`, checked 2026-10-10): `-p`, `-l`, `-r`, `-i`, `-U`, `--json`; no
  matches → exit code 1; `/usr/bin/sg` in Ubuntu comes from the `login` package (change group) — checked 2026-10-10.
