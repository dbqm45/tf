---
name: arch-architect-practice
description: Use when making, recording or communicating an architectural decision, challenging it, running an architecture review, estimating or documenting architecture.
metadata:
  review: "2027-11-20"
  catalog: "Use when an architect's work goes beyond picking technology — naming the architecture level (application, solution, enterprise), deciding with options and trade-offs, reversibility, recording an ADR and telling the team, the business and operations, challenging a recommendation before it is recorded (devil's advocate, pre-mortem, unknown unknowns), simplification, estimates as ranges, a lightweight ATAM-style review (sensitivity points, trade-off points, risks), C4 and arc42 documentation kept as a text model with drift checks in CI, coaching teams, and translating team artefacts into enterprise frameworks (TOGAF, ArchiMate, ITIL, PRINCE2, BABOK). Not for quality attribute scenarios and architecture styles (arch-quality-attributes), choosing a stack, database or platform (arch-tech-selection)."
  keywords: "decyzja architektoniczna, podjąć decyzję architektoniczną, zapisać decyzję, ADR, rekord decyzji, zakomunikować decyzję, zespół wraca do tej samej dyskusji, ciągle wracamy do tematu, wydzielić serwis, odwracalność decyzji, opcje i kompromisy, przegląd architektury, lekki przegląd architektury, ATAM, punkty wrażliwości, punkty kompromisu, raport z przeglądu, test odporności decyzji, przytakiwanie, model się zgadza, wszyscy się zgadzają, adwokat diabła, pre-mortem, nieznane niewiadome, sprawdzić rekomendację, rejestr ryzyk, rola architekta, poziomy architektury, architektura rozwiązania, architektura korporacyjna, uprościć architekturę, nadmierna złożoność, estymacja architekta, oszacować migrację, diagramy C4, diagramy nieaktualne, dokumentacja architektury rozjeżdża się z kodem, Structurizr, LikeC4, diagram jako kod, arc42, TOGAF, ArchiMate, ITIL, PRINCE2, BABOK, artefakty dla banku, coaching zespołu, architectural decision, record a decision, communicate a decision, decision keeps coming back, reversibility, architecture review, lightweight review, sensitivity point, trade-off point, stress-test a decision, sycophancy, devil's advocate, pre-mortem, unknown unknowns, risk register, architect role, solution architecture, enterprise architecture, simplify architecture, estimate migration, C4 diagrams stale, architecture as code, docs drift from code, enterprise framework artefacts"
---

# Architect practice — decide, challenge, record, explain

Picking technology is one decision among many. This skill covers the rest of the architect's job: what level a question
lives on, how a decision is made and made to stick, how it is attacked before it is written down, and how architecture
is reviewed, estimated and documented.

## 1. Name the level first
| Level | Scope | Typical output |
|---|---|---|
| Application | inside one system: modules, layers, boundaries, testability | ADRs, fitness functions, module rules |
| Solution | several systems serving one business need: integration, data flow, contracts | solution document, context map (ddd-context-mapping), API contracts (be-api-design) |
| Enterprise | capabilities, portfolio, standards, roadmap | capability and application maps, principles, roadmap |

State the level in the first sentence of any answer. A conversation that mixes a module's internals with the company's
platform strategy produces decisions nobody owns.

## 2. Expectations of an architect
- Guides decisions and the people who make them; does not hand down technology by decree.
- Keeps checking whether the system still matches the decisions (drift) and automates that check where possible
  (fitness functions — arch-quality-attributes).
- Broad, shallow knowledge of many technologies and deep knowledge of a few; follows trends without chasing them.
- Knows the business domain well enough to judge trade-offs in its terms.
- Works with people and with the organisation's politics: a correct decision that nobody adopts has no effect.
- Writes code only as far as it grounds decisions: spikes, a walking skeleton, reviews.

## 3. Making a decision
1. **Is it architectural?** It touches structure, a quality attribute, dependencies, interfaces or construction technique
   **and** it is expensive to undo. A cheap-to-reverse detail stays with the team.
2. **Inputs:** quality attribute scenarios (arch-quality-attributes), constraints (budget, date, skills, regulation),
   earlier ADRs, measurements. A missing fact becomes a spike or a research task (core-grounding) — never a guess.
3. **Options:** at least two real options plus "change nothing". For each: what we gain, what we give up, cost to build,
   run and leave. There is no best option, only the least bad one for these forces.
4. **Reversibility:** on a tie take the option that is easier to change. Postpone a costly, irreversible choice to the
   last responsible moment, and use the time to collect what the choice needs.
5. **Challenge** the leading option (section 4) before writing it down.
6. **Record** an ADR (format: docs-tech-writing): context, options, decision, consequences, the date to revisit.
   A human accepts it (core-project-record).
7. **Communicate** to three audiences, each in its own language:
   - the team — what changes in the code and why;
   - the business — cost, risk, date;
   - operations — what changes in deploying, monitoring, backup and on-call.
   The "why" matters more than the "what"; it is what stops the next re-argument.

Anti-patterns: waiting for complete information; an architect who no longer reads the code; the same debate every month
because the previous one left no record (the fix: point at the ADR and reopen it only on new facts).

## 4. Challenge the recommendation before recording it
Agreement is cheap. People in a meeting and language models alike drift towards confirming the option already on the
table, and "does X fit Y?" almost always gets a yes. Ask the opposite question: **"why is X a bad choice for Y?"**

Do it before an ADR or a stack/platform recommendation is recorded, whenever everyone agrees at once, and before handing
over research-based advice. Three angles, applied to the leading option in the same session:
- **Devil's advocate** — the strongest concrete case against it: named limits, numbers, hidden costs, failure modes.
- **Pre-mortem** — imagine it is six months later and the choice failed; tell the story backwards to the cause.
- **Unknown unknowns** — risk classes the assessment never looked at, each turned into a question someone can answer.

Every finding ends in one of three outcomes: accepted, written down as a known limitation in the risk register, or the
choice changes. The procedure, the register format and a worked example: `references/decision-resilience-test.md`.

## 5. Simplify and balance
For every proposal ask: why is it better than the alternatives, could it be simpler, what does it cost to build, maintain
and operate, does the edge case justify that cost? Complexity is not a sign of skill; technology adopted for novelty is
debt (eng-design-principles). Trade speed against quality and innovation against stability on purpose, and record the debt
you take on (eng-tech-debt-audit).

## 6. Estimating
- Give ranges (optimistic / likely / pessimistic), never one number.
- Decompose; compare with finished work of a similar kind; list assumptions and unknowns next to the number.
- The largest unknown becomes a time-boxed spike before the estimate is committed.
- Forecasting a team's throughput from history belongs to proc-agile; whole-project plans to proc-project-planning.

## 7. Lightweight architecture review (ATAM-style)
1. Business goals and the prioritised quality scenarios (arch-quality-attributes).
2. The architecture as it is and the decisions behind it.
3. For each important scenario: the decisions that support it, **sensitivity points** (one decision strongly moves one
   attribute), **trade-off points** (a decision improves one attribute at another's expense), **risks** and non-risks.
4. Report: scenarios walked, risks grouped into themes, recommendations with owners.
Run it periodically and before large changes; continuous checks between reviews are fitness functions.

## 8. Documentation
- **ADR** is the most valuable document: it keeps the "why".
- **C4** views: context, containers, components; the code level is rarely worth drawing.
- **arc42** as a template (goals, constraints, context, solution strategy, building blocks, runtime, deployment,
  cross-cutting concepts, decisions, quality, risks, glossary) — fill only the sections someone reads.
- Docs live in the repository and change in the same PR as the code; generate what can be generated (dependency graphs,
  API reference).
- **One text model as the source of truth.** Describe elements and relations once in a model in the repo (Structurizr DSL,
  LikeC4 or an export from the team's tool) and generate the views for each audience. A PR changes the model; CI renders the
  views. A drift check in CI compares the model's relations with real dependencies (import graph, service calls, IaC):
  a dependency in code missing from the model, or a modelled one with no code behind it, is a review finding. ADRs point
  at model elements; an agent reads the model text, not pictures. Check current tool versions before choosing (core-grounding).

## 9. Coaching
- Review designs and PRs for architectural decisions, not style (that is the linter's job).
- Ask questions where the team should learn; give the answer when time or risk dominates.
- Scale through standards in code (generators, templates, boundary rules), reference implementations and workshops,
  not by becoming the bottleneck for every decision.

## 10. Enterprise frameworks
The organisation may expect TOGAF, ArchiMate, ITIL, PRINCE2 or BABOK artefacts. Do not implement a framework; find out
what is really required (often a template and a review board) and map existing team artefacts onto it — ADR → decision
register, threat model → risk assessment, postmortem → problem record — instead of writing parallel documents.
Framework overview and mappings: `references/corporate-frameworks.md`.

## Example
**Situation:** "Every month the team argues again whether to split billing out of the monolith."
**Result:**
- Level: solution (billing talks to invoicing and the payment provider).
- Options: (A) change nothing; (B) a billing module with enforced boundaries inside the monolith; (C) a separate service.
  B keeps one deployment and gains a clear seam; C gains independent releases and loses a transaction, adds a network hop
  and a second on-call rota.
- Reversibility: B can become C later; C back to B is costly → B now, C when releases of billing block other work
  more than twice a quarter (the revisit trigger in the ADR).
- Challenge: pre-mortem "B failed because the boundary leaked" → a boundary test in CI from day one.
- ADR-014 accepted; team note (module rules), business note (no date impact), operations note (no change to deploys).

## Output
For a decision: level, options with trade-offs, the challenge findings and their outcome, the ADR draft and three short
audience notes. For a review: the report from section 7. Missing context (the decision, options or constraints) → ask
for it; do not invent a decision to record.

## Sources
- R. Kazman, M. Klein, P. Clements, "ATAM: Method for Architecture Evaluation", CMU/SEI-2000-TR-004 (Software Engineering
  Institute, 2000).
- G. Klein, "Performing a Project Premortem", Harvard Business Review, September 2007.
- M. Richards, N. Ford, *Fundamentals of Software Architecture*, O'Reilly, 2020 (expectations of an architect).
- N. Ford, R. Parsons, P. Kua, P. Sadalage, *Building Evolutionary Architectures*, 2nd ed., O'Reilly, 2023 (fitness functions).
- InfoQ, "Driving Architectural Simplicity" [unverified: author and date].
- roadmap.sh, "Software Architect" roadmap (accessed 2026-11-20).
- C4 model, c4model.com; arc42, arc42.org; Structurizr DSL, docs.structurizr.com; LikeC4, likec4.dev (accessed 2026-11-20).
