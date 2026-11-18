---
name: arch-architect-practice
description: Use for an architect's work beyond technology — decisions (devil's advocate), communication, estimation, ATAM, arc42/C4/ADR.
metadata:
  review: "2027-10-09"
  catalog: "Use for an architect's work beyond technology alone — architecture levels, making and communicating decisions, estimation, architecture review (ATAM), simplification, documentation (arc42, C4, ADR), coaching, enterprise frameworks (TOGAF, ITIL). Not for quality attributes (arch-quality-attributes) or stack selection (arch-tech-selection)."
  keywords: "decyzja architektoniczna, zakomunikować decyzję, utrwalić decyzję, wracamy do tej samej dyskusji, ADR, rekord decyzji, przegląd architektury, ATAM, arc42, C4, interesariusze architektury, szacowanie architekta, architectural decision, communicate a decision, record a decision, we keep coming back to the same discussion, decision record, architecture review, architecture stakeholders, architect estimation, devil's advocate, pre-mortem"
---

# The architect's practice

The architect is responsible for decisions that are expensive to change, and for the team understanding and applying them. You write code
as much as needed for the decisions to be grounded in reality (a prototype, a skeleton, a review).

## Architecture levels
| Level | Scope | Typical questions | Result |
|---|---|---|---|
| **application** | the inside of one system: modules, layers, patterns | how to split the code, where the module boundaries are, how to test | the module structure, ADRs, fitness functions (eng-*, ddd-tactical-design) |
| **solution** | several systems for one business need | how the systems integrate, data flow, technologies | the solution architecture, a context map, contracts (ddd-context-mapping, be-api-design) |
| **enterprise** | the whole organization: business capabilities, the system portfolio | which systems to develop, retire, merge; standards | capability and application maps, principles, a roadmap (`references/corporate-frameworks.md`) |
A task always names the level — otherwise a conversation about "architecture" mixes the inside of a module with the company strategy.

## Expectations of an architect (after Richards and Ford)
Makes architectural decisions (and leads to them, instead of dictating technologies); continuously analyses the architecture
and its drift; follows trends and assesses them critically; keeps compliance with the decisions (automatically, fitness functions);
knows many technologies superficially and a few deeply; knows the business domain; has interpersonal skills; understands
the organization and its politics (without this the best decision will not be implemented).

## Decisions
1. **Is it an architectural decision?** It concerns the structure, quality attributes, dependencies, interfaces or construction
   techniques and is costly to reverse. Leave reversible details to the team.
2. **Factors**: quality attribute scenarios, constraints (budget, deadline, skills, regulations), existing
   decisions (ADRs) and data, not opinions. No facts → a researcher or a spike, not a guess.
3. **Options**: at least two real ones plus "change nothing"; for each the trade-offs explicitly (what we gain, what we
   lose). There is no best solution, there is the least bad one for these factors.
4. **Reversibility**: in a tie choose the one easier to change; postpone expensive decisions to the last responsible
   moment, but prepare what is needed to make them.
5. **Record**: an ADR with the context, options and consequences (docs-tech-writing); a human accepts it (core-project-record).
6. **Communication**: you explain the decision to three audiences — the team (what to do differently and why), the business (cost,
   risk, deadline, in its language), operations (what changes in maintenance). The justification "why" matters more
   than "what".
7. **A decision resilience test (against sycophancy).** A model adjusts its assessment to what the human already believes.
   Before you record a recommendation, run the leader through three lenses — yourself, in the same session:
   - **devil's advocate:** 3–5 concrete weaknesses, hidden costs and failure modes of *this* option in *this* project
     (names, limits, numbers — not categories);
   - **pre-mortem:** "3–6 months have passed, the decision turned out a failure" — a short narrative about the wrong assumptions;
   - **unknown unknowns:** 3–5 classes of risk outside the assessment (compliance, backups, exit from the provider, beta
     status, dependence on other teams).
   The result of each lens: I accept the risk / I record it as a known limitation (in the risk register with the source —
   which lens revealed it) / I change the choice. Ask "why is X a bad choice for Y", not "does X fit Y".
   When across many decisions the test never changes anything, it has become a ritual. Details and an example:
   `references/decision-resilience-test.md`.
Anti-patterns: a decision postponed forever while waiting for full information; "ivory tower architecture" without contact
with the code; the same discussion every month, because the decision was not recorded.

## Simplification and balance
- Questions for every proposal: why is it better than the alternatives, can it be simpler, what is the cost of building,
  maintenance and operations, does this edge case justify the cost?
- Complexity is not proof of competence. A technology chosen because it is new, not because it solves the problem,
  is debt (eng-design-principles: the minimalism ladder, YAGNI).
- Balance: speed vs quality, innovation vs stability — a conscious decision with recorded debt
  (eng-tech-debt-audit), not silent consent.

## Estimation and assessment
- **Estimation**: ranges (optimistic / most likely / pessimistic), breaking down into parts,
  comparison with similar completed tasks, explicit assumptions and unknowns; you turn the biggest unknowns into a spike.
  Flow-based forecasting: proc-agile.
- **Architecture assessment (a lightweight ATAM-style review)**: (1) business goals and quality scenarios with priorities,
  (2) a presentation of the architecture and decisions, (3) for every important scenario: which decisions support it, where the
  **sensitivity points** are (one decision strongly affects an attribute), the **trade-offs** (a decision improves one attribute
  at the cost of another) and the **risks**, (4) a report with risks and recommendations. Periodically and before a large change; continuous
  checking through fitness functions (arch-quality-attributes).

## Architecture documentation
- An **ADR** for decisions (docs-tech-writing) — the most important document, because it records the "why".
- The **C4 model** for views: context (the system and its surroundings), containers (applications and data stores), components (if
  needed); the code level is usually unnecessary. A diagram as code in the repo (docs-tech-writing, `diagrams-and-presentations.md`).
- **arc42** as the architecture document template (goals, constraints, context, solution strategy, views, cross-cutting
  concepts, decisions, quality requirements, risks, glossary) — you fill in only the sections someone will read.
- The documentation lives in the repo and is updated with the code; what can be generated (dependency graphs —
  eng-codebase-mapping, the API reference), you generate.
- **The model as the source, diagrams as views:** the C4 elements and relations described once in a text model in the repo (e.g.
  Structurizr DSL, LikeC4 or an export from a tool), and views for different audiences generated from it instead of separately
  drawn diagrams. A change in a PR modifies the model, CI renders the views. **Drift control in CI:** the relations from the model
  compared with the actual dependencies (the import graph, calls between services, IaC); a relation in the code without
  a counterpart in the model and vice versa is a finding for review. An ADR points to the model elements it concerns. The agent
  reads the model, not the diagram images. Check the tool versions before choosing (core-grounding).

## Advice and coaching
- Review designs and PRs for architectural decisions, not style (that is what linters are for).
- Questions instead of ready answers where the team is to learn something; a ready answer where time
  or risk counts.
- The architect's knowledge scales through standards in code (generators, templates, boundary rules), reference
  examples and workshops, not through being the bottleneck of every decision (fe-engineering-levels, proc-team-topologies).

## Checklist
- [ ] the architecture level named; an architectural decision distinguished from a detail
- [ ] ≥ 2 options with trade-offs, factors from data, reversibility assessed
- [ ] the leader passed the resilience test (devil's advocate, pre-mortem, unknown unknowns); each lens's result recorded
- [ ] an ADR and a message for the team, the business and operations
- [ ] an estimate in ranges with assumptions; a spike for the biggest unknown
- [ ] C4 views and documents in the repo, updated with the code

## Sources
- M. Richards, N. Ford, *Fundamentals of Software Architecture* (2nd ed. 2025) — expectations of an architect,
  decisions; N. Ford et al., *Building Evolutionary Architectures* — fitness functions
- SEI (R. Kazman et al.) — ATAM; S. Brown — [C4 model](https://c4model.com/); [arc42](https://arc42.org/)
- InfoQ, [Driving Architectural Simplicity](https://www.infoq.com/articles/driving-architectural-simplicity/);
  [roadmap.sh — Software Architect](https://roadmap.sh/software-architect)
- The 10xDevs course, ed. 3 (2026), module 1, lesson 5 (countering model sycophancy in decisions) — training
  material (accessed 2026-10-09).
Described in our own words.
