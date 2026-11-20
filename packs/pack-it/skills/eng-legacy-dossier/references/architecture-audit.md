# Architecture audit — Inventory → Assessment → Recommendations

> **Contents:** 1. Principle · 2. Stages and results · 3. Assessment criteria · 4. Finding (`ARCH-NNN`) · 5. Categories · 6. Recommendation (`REC-NNN`) and decision rungs · 7. Priorities and roadmap · 8. Target principles · 9. File templates · 10. Indicative schedule · 11. When the audit is finished

## 1. Principle
You do not start from the question "what to rebuild?", but from "how does the current architecture work, what problems does it actually
cause, and will a change bring a measurable benefit?". A solution that does not match a popular pattern is not a problem until
you show an effect (cost of changes, bugs, blocked development) or a risk.

## 2. Stages and results
| Stage | Action | Result (dossier file) |
|---|---|---|
| 1. Scope | applications, shared libraries and their consumers, whether build/tests/CI, the team's existing standards | `assessment.md` § Scope and method, § Assessment criteria |
| 2. Inventory (as-is) | structure, projects, dependencies, solutions — no assessments | `README.md` + `modules/*.md` |
| 3. Assessment | current vs expected state, evidence, categories, strengths | `assessment.md` § Findings, Strengths |
| 4. Recommendations | a decision at the lowest effective rung, target principles | `recommendations.md` § Recommendations, Target principles |
| 5. Priorities | P1–P3, effort, risk, order, phases | `recommendations.md` § Roadmap, Success criteria |

You record findings as you go (with evidence and a question for verification), not at the end.

## 3. Assessment criteria
You set the checklist of areas in stage 1 (for Nx + Angular: `nx-angular.md` § 1). You assess each area with questions:
- **Clarity** — can the structure be understood without a long analysis of the code?
- **Consistency** — were similar problems solved in a similar way?
- **Coupling** — does a change in one place force changes in others?
- **Cohesion** — does what belongs to one responsibility lie together?
- **Testability** — can the essential logic be tested independently of the view?
- **Enforceability** — are the rules enforced by a tool (lint, dependency rules) or only by people's memory?
- **Maintainability** and **Complexity** — does the benefit justify the complexity?

Coupling measured with evidence in the code (degree of connascence) — ddd-connascence-analysis.

## 4. Finding (`ARCH-NNN`)
```markdown
### ARCH-004 — A shared library imports an application's implementation
Area: library boundaries
Category: confirmed problem
Current state: libs/shared/ui imports OrdersFacade from apps/shop
Expected state: shared libraries do not depend on applications
Gap: a change in the application can break all consumers of shared/ui
Evidence: libs/shared/ui/src/lib/order-badge.component.ts:3
Impact: coupling; shared/ui cannot be used in a second application
```
- **Evidence** is `file:line` (several separated by commas). Save the output of a command (e.g. the dependency graph) in the dossier
  (`evidence/graph.json`) and point to `evidence/graph.json:1` — `dossier_check.py` checks that the file and the line exist.
- **Fact vs interpretation:** "there is an import" is a fact (Evidence); "it does harm" is an interpretation (Impact) — it must follow
  from the evidence or go to "To investigate".

## 5. Categories
| Category | Meaning | Evidence |
|---|---|---|
| `confirmed problem` | a demonstrated effect, e.g. a cycle that blocks independent changes | required; requires a recommendation |
| `risk` | may surface, e.g. no control of dependencies | recommended |
| `inconsistency` | similar things solved differently | required (both places) |
| `improvement` | can be done more simply, without a critical problem | recommended |
| `preference` | a different style, without a demonstrated effect | — ; does not justify a structural refactoring |

## 6. Recommendation (`REC-NNN`) and decision rungs
```markdown
### REC-002 — Enforce the dependency direction with an Nx rule
Addresses: ARCH-004, ARCH-007
Decision: configuration
Priority: P1
Effort: 0.5 day
Risk: lint will block existing imports — first a list of exceptions
Verification: a sample forbidden import is reported by lint, allowed ones pass
```
Rungs (choose the lowest one that solves the actual problem): **`no change`** (with a reason) → **`documentation`** →
**`configuration`** (lint, rules, tags) → **`incremental refactoring`** → **`structural refactoring`** (a change
in the division of responsibilities) → **`redesign`**. The recommendation also describes the current solution, the problem,
the justification and the expected benefit — in the text below the fields.

## 7. Priorities and roadmap
| Priority | Criterion | Action |
|---|---|---|
| P1 | a significant impact on stability, safety of changes or development | plan without delay |
| P2 | raises the maintenance cost or the risk of further changes | the next iterations |
| P3 | readability or consistency without an urgent need | along with other work |

Besides the impact, take into account the effort, the regression risk, the reach (how many projects), the dependencies between tasks and the possibility
of rolling out in stages. Roadmap phases (an example, the order follows from the findings): **A. Foundations** (boundaries, dependency
rules, cycles, lint) → **B. The most important problems** → **C. Unification** (patterns, documentation of standards,
tests) → **D. Further improvements**. Each task: scope, priority, effort, dependencies, risks, completion
condition — ready to move into the task system. The refactoring execution plan: eng-refactor-planning;
execution with frozen behaviour: eng-behavior-preserving-refactoring.

## 8. Target principles
Only as much standard as helps this application. Separate: **mandatory** (enforced by a tool where possible),
**recommended** (exceptions with a justification), **context-dependent** (a decision in the given case). Typical areas:
the division into libraries, names and locations, tags, allowed dependency directions, public API, organization of features
and UI, API access, state management, test requirements, documenting exceptions. Decisions on principles — an ADR
(docs-tech-writing).

## 9. File templates
`assessment.md`:
```markdown
<!-- legacy-dossier:assessment -->
# Architecture Assessment — <system>
## Summary
## Scope and method
## Assessment criteria
## Findings
### ARCH-001 — …
## Strengths
## To investigate
```
`recommendations.md`:
```markdown
<!-- legacy-dossier:recommendations -->
# Architecture Recommendations & Roadmap — <system>
## Target principles
## Recommendations
### REC-001 — …
## Roadmap
## Success criteria
```

## 10. Indicative schedule
One application with significant libraries — a starting point of about 6–9 days of human work (an assumption from the audit plan,
not a measurement): scope and workspace → libraries and dependencies → Angular, routing, state, API, tests → assessment → recommendations
→ priorities → consultations. With an agent, stages 1–2 are faster (tools + the script), but the assessment and the consultations with the team
are not. A large repo: by layers or domains — first the structure and the flows, in depth where the questions are.

## 11. When the audit is finished
- you know the structure of the application and the key libraries, you can explain the most important dependencies and data flows;
- the most important findings have evidence, and the strengths are described;
- every significant recommendation has a justification, a priority and a way of verification;
- `dossier_check.py` → `legacy-dossier-check: OK`; the team knows the results and can plan work from them.
