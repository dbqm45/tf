---
name: eng-legacy-dossier
description: Use for describing the architecture of legacy code before a refactor — as-is, rules, an assessment with evidence, a roadmap.
metadata:
  review: "2027-10-17"
  catalog: "Use when you need to describe and explain existing (legacy) code before fixes and a refactor — a system dossier: module cards with responsibility, inputs and outputs, business rules extracted from the code with file:line evidence and a confidence, data and integrations, key flows, a code ↔ business glossary, questions for people, module state and refactoring candidates; an architecture audit mode (e.g. Angular in an Nx monorepo): Architecture Inventory (as-is), Assessment (findings with evidence, categories, strengths) and Recommendations & Roadmap (a decision from \"no change\" to a redesign, priority, verification); a script checks the dossier's completeness and evidence. Not for a bare map of structure and entry points (eng-codebase-mapping), a debt assessment (eng-tech-debt-audit), choosing a refactoring (eng-refactor-planning) or analysing binaries without sources."
  keywords: "legacy, stary system, stary kod, kod zastany, opisz system, opisz kod, dokumentacja legacy, brak dokumentacji, nikt nie wie jak działa, wytłumacz moduły, co robi ten moduł, reguły biznesowe w kodzie, przejmujemy system, onboarding do systemu, teczka systemu, przed refaktorem, przed poprawkami, posegregować kod, zrozumieć system, audyt architektury, ocena architektury, stan obecny, as-is, architecture inventory, assessment, rekomendacje zmian, roadmapa, granice bibliotek, monorepo, old system, old code, inherited code, describe the system, describe the code, legacy documentation, no documentation, nobody knows how it works, explain the modules, what does this module do, business rules in the code, taking over a system, system onboarding, system dossier, before a refactor, before fixes, sort out the code, understand the system, architecture audit, architecture assessment, current state, change recommendations, roadmap, library boundaries"
---

# Legacy system dossier — describe, sort out, explain

Goal: a document after which a person who does not know the system knows **what** each part does, **why** (business rules)
and **where** it is in the code — and the team has a ready input for fixes and a refactor. The dossier describes the current state;
it changes nothing in the code. Every claim about behaviour has `file:line` evidence or the confidence `to verify`
(core-grounding) — a description "from general memory" is worse than no description, because it misleads during a refactor.

## Procedure
0. **Scope and map.** Agree the system or directory with the human and record the HEAD commit. If there is no
   `docs/project/04-architecture/codebase-map.md`, first make the map per **eng-codebase-mapping** (inventory,
   layers, entry points, risk zones) — the dossier uses it and does not repeat it.
1. **Split into modules** from the map (layers, module legend). A module = a part with one business responsibility,
   not a directory. Order of description: the core and the risk zones first, the periphery at the end or as one line in the index.
2. **Module card** `modules/<module>.md` per `references/template.md`:
   - **Purpose** — 1–2 sentences in business language, without class names;
   - **Responsibilities, Inputs and outputs** (endpoints, events, files, scheduled jobs), **Data** (tables,
     entities: who writes, who reads), **Dependencies** (to and from the module) — from the graph, not from memory: for Python and TS/JS
     `python3 .claude/skills/eng-codebase-mapping/scripts/code_graph.py <repo> --focus <module path>` (outgoing
     and incoming imports with their kind); the graph skips DI, queues, registries and calls by name — those go to Questions;
   - **Business rules** — a table `ID | Rule | Evidence | Confidence`. You write a rule as a sentence for the business
     ("An invoice is overdue after 30 days"), not as a description of the code. Confidence: `test` (there is a test that
     guards it), `code` (it follows directly from the code), `to verify` (inferred, contradictory or without evidence — it also goes to
     Questions). Where to look for rules: `references/template.md` § Where to get rules from;
   - **Pitfalls** — surprising behaviour: side effects, global state, magic constants, dependence on order,
     the same rule in several places (often different);
   - **Tests** — what is covered, what is missing for the rules in the table;
   - **State** in the header: `green` (understood, tested), `yellow` (works, but risky to change),
     `red` (not understood or without tests for critical rules) — always with a reason.
3. **Flows (3–5 key ones)** in the index: step by step through the modules with files, a sequence diagram (Mermaid).
   Going deeper into one flow: `.claude/skills/eng-codebase-mapping/references/flow-analysis.md`.
4. **Glossary** code ↔ business: the name in the code, the business concept, a note on the mismatch (`Doc` = an invoice, but also
   a correction). Model mismatches and invariants are deepened by **ddd-legacy-modernization**.
5. **State and refactoring candidates** — a table of modules with their state and a list of candidates (what, why, evidence). The dossier
   ends at the candidates: the weight and effort assessment is done by **eng-tech-debt-audit**, the choice and plan by **eng-refactor-planning**,
   the execution with frozen behaviour by **eng-behavior-preserving-refactoring**.
6. **Check** — **run** `python3 .claude/skills/eng-legacy-dossier/scripts/dossier_check.py
   docs/project/04-architecture/legacy-dossier` (from the repository directory). First line: `legacy-dossier-check: OK`
   or `ERRORS` with a list: missing sections and cards, repeated IDs, evidence pointing to a non-existent file or line.
   You fix the errors before handing over; the number of `to verify` rules goes into the TL;DR.

Result: `docs/project/04-architecture/legacy-dossier/README.md` (the index) + `modules/*.md`; TL;DR and Handoff per
core-project-record. A large system: first the index and the core cards, the rest in later sessions (a checkpoint).

## Mode: architecture audit (Inventory → Assessment → Recommendations)
When the goal is an **assessment** of the architecture and a plan of changes, not just a description — e.g. Angular in an Nx monorepo after several teams.
The order is strict: first the current state with evidence, the assessment only after that, the recommendations at the end.
1. **Scope and criteria** — which applications and libraries (you assess shared ones together with their consumers), whether also
   the build, tests, CI; a checklist of areas with a question for each. Recorded in `assessment.md` § Scope and method, Assessment criteria.
2. **Architecture Inventory (as-is)** = the index and cards from the procedure above; a module is an application or a library.
   No assessments. Nx and Angular: `references/nx-angular.md` (commands, library inventory, dependencies, routing, state, API).
3. **Assessment** (`assessment.md`) — findings `ARCH-NNN`: current state / expected state / gap, evidence, impact and
   **category** (`Category`): `confirmed problem` · `risk` · `inconsistency` · `improvement` · `preference`. You separate a fact (there is an import)
   from an interpretation (it does harm — needs a justification). A separate **Strengths** section — what to keep.
4. **Recommendations & Roadmap** (`recommendations.md`) — `REC-NNN` for the findings: a decision at the lowest rung
   that solves the problem (`no change` → `documentation` → `configuration` → `incremental refactoring` → `structural refactoring` →
   `redesign`), priority P1–P3, effort, risk, the way of verification; target principles (mandatory /
   recommended / context-dependent); a roadmap in phases; success criteria.
5. **Check** — the same `dossier_check.py`: it guards the evidence of confirmed problems, a recommendation for each
   of them, and blocks a structural refactoring justified by preference alone.

Templates, criteria (clarity, consistency, coupling, cohesion, testability, enforceability) and the schedule:
`references/architecture-audit.md`. A deep debt assessment at repo scale — eng-tech-debt-audit; choosing a refactoring
variant — eng-refactor-planning.

## Rules
- **The reader does not know the system.** First "what and why", then "how"; short sentences, file names in `code`.
- **A fact or a question.** You do not guess the author's intent; you describe a code ↔ test ↔ comment contradiction and ask.
- **No judging of people** and no "this is badly written" — you describe the behaviour and the risk of change.
- **Cost:** the broad scan is done by tools (eng-codebase-mapping). Cards of independent modules can be delegated
  in parallel to read-only executors, with a brief: the file scope, the template, the check command (core-cost-control §0).
- **A dossier is not a refactor.** You do not fix code "along the way" — candidates go to section 5.

## Example
Input: "Describe the invoice module in the old system (Java), before changing the rounding."
Result (a fragment of `modules/invoices.md`):

```markdown
<!-- legacy-dossier:module -->
# Module: invoices
State: yellow — amounts are rounded in two places, with different methods

## Business rules
| ID | Rule | Evidence | Confidence |
|---|---|---|---|
| R-FAK-01 | The gross amount is rounded to 2 places "half up" | src/billing/Invoice.java:142 | test |
| R-FAK-02 | The PDF shows the amount rounded "banker's" style — it may differ by 1 grosz | src/pdf/PdfExporter.java:57 | code |
| R-FAK-03 | An invoice is overdue after 30 days (calendar days?) | — | to verify |

## Pitfalls
- The same amount is computed in `Invoice.total()` and `PdfExporter.render()` (R-FAK-01 vs R-FAK-02).
```

In the index: the candidate "one place for rounding" with evidence of both lines → eng-tech-debt-audit; the question
"calendar or working days?" → Open questions.

## Checklist
- [ ] scope and HEAD commit recorded; the map (eng-codebase-mapping) exists or was made first
- [ ] every module in the index has a card; "Purpose" in business language; State with a reason
- [ ] every rule: a sentence for the business, `file:line` evidence or `to verify` + a question
- [ ] 3–5 flows, a glossary with mismatches, refactoring candidates with evidence (no changes in the code)
- [ ] `dossier_check.py` → `legacy-dossier-check: OK`; the number of `to verify` rules in the TL;DR

## Additional materials
- `references/template.md` — the template of the index and of a module card, where to get business rules from; read it when writing the dossier.
- `references/architecture-audit.md` — the audit mode: stages, templates of a finding and a recommendation, categories, priorities.
- `references/nx-angular.md` — inventory and analysis of an Nx monorepo with Angular; read it when auditing such a repo.

## Sources
- Feathers, *Working Effectively with Legacy Code* (2004) — characterization tests as evidence of the current behaviour.
- Evans, *Domain-Driven Design* (2003) — the ubiquitous language; the code ↔ business glossary.
