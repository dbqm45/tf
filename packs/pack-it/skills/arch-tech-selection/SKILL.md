---
name: arch-tech-selection
description: Use for choosing or assessing a stack (language, framework, database, hosting) — criteria, candidates, a matrix, risks.
metadata:
  review: "2027-10-09"
  catalog: "Use when you must recommend a stack (languages, frameworks, database, hosting, tools) for a new project or assess and evolve the stack of an existing one — drivers, mandatory filters, 2–3 candidates, verifying facts from sources, an assessment matrix, risks and spikes, mapping onto skills and personas. Not for establishing quality attributes (arch-quality-attributes)."
  keywords: "przepisać od zera, co zostawić a co wymienić, wybrać framework, który framework wybrać, czy wybrać, porównanie frameworków, modernizacja starego systemu, legacy, migracja stacku, nowy stack, wybór technologii, rewrite from scratch, what to keep and what to replace, choose a framework, which framework to choose, framework comparison, modernizing an old system, stack migration, new stack, technology choice, stack decision, pick a framework and a database, choose a stack, startup stack, regret the choice later, team knows Python"
---

# Choosing a technology stack

A recommendation is **a decision with a justification and verified facts**, recorded in `docs/project/04-architecture/stack-decision.md`
(template: core-project-record). Not a list of favourite technologies.

## Input (read the TL;DR + the indicated sections)
The brief (goals, constraints, team), the requirements (quality attribute scenarios), the domain (subdomains, archetypes, problem classes).
A key input missing (e.g. the team's skills, the hosting location) → a question to the user, not an assumption.
**An existing project:** first `python3 .claude/hooks/detect_stack.py` — the recommendation is *keep / improve / replace* per area,
with the migration cost (strangler fig, along context boundaries), not a new stack from scratch.

Supplementary input (if it exists): `02-domain/algorithms.md`, `02-domain/stress/*.md`.

## Procedure
1. **Drivers** — 3–5 (H,H) scenarios + constraints (arch-quality-attributes), with weights 1–5.
2. **Mandatory filters** (they reject an option without scoring): the licence, hosting and compliance (e.g. data in the EU), support within the project's
   horizon (LTS / end of support), security (active patches), the team's ability to start (or a real hiring plan).
3. **Candidates** — 2–3 per area, always with the **"boring"** option: what the team knows, or the most common choice in the ecosystem.
   Fewer technologies = cheaper: every extra language/framework is a cost of maintenance, recruitment and skills.
4. **Fact verification** — current versions, support dates, compatibility between elements (e.g. Angular 22 requires TS 6.0.x),
   licences: only from **primary sources** (release pages, the package registry: `npm view <package> version`), with a check date.
   Cheaply: delegate to the `researcher` agent (it returns facts with sources). **Never from memory.**
5. **Assessment** — a weighted matrix:
   | Criterion | Question |
   |---|---|
   | fit to the drivers | does it meet the (H,H) scenarios without extraordinary measures? |
   | team skills | how much learning before the first release? |
   | ecosystem maturity | stable releases, libraries, community, documentation |
   | operating cost and complexity | how many elements to maintain and monitor? |
   | **friendliness for AI agents** | **four gates**: **types** (explicit data contracts in the code) · **conventions** (established places for routing, tests, configuration) · **popularity assessed within the language family** (Django among Python frameworks, not against React) · **current, versioned documentation** (preferably in markdown: `llms.txt`, `.md` versions, available through a live documentation server); plus fast tests, deterministic tools, services integrated in one step (one command, one environment variable, one documentation page) and **existing `lang-*`/`fw-*`/`tool-*` skills** |
   | lock-in and exit cost | what if the provider/framework has to be changed? |
   | security | vulnerability history, patch speed, secure defaults |
6. **Conclusions from the domain** (ddd-deep-modeling, ddd-archetypes):
   - a generic subdomain → buy / SaaS / a ready component (through an ACL);
   - CRUD and supporting → the simplest framework, generators, even BaaS;
   - a core with complex rules → a language with a strong type system (sum types, immutability), easy domain tests;
   - competition for resources → a database with strong consistency and constraints (e.g. PostgreSQL with exclusion of overlapping ranges);
   - integration between contexts → messages + an outbox (be-messaging-outbox); read-dominated → read models / cache;
   - **an algorithmic core** (`02-domain/algorithms.md`, ddd-algorithm-recognition): an NP-hard problem → a solver/optimization
     library behind a domain interface + a spike with an abandonment criterion, not your own algorithm; a spatial problem →
     a geo extension in the database; similarity → a full-text/vector index. The `researcher` checks the specific libraries and versions.
7. **Architecture style** — by default a modular monolith (arch-quality-attributes); another one only with a justification in the drivers.
8. **Risks and spikes** — for every uncertainty: a time-boxed experiment and an **abandonment criterion** for the choice.
   Run the leader through the decision resilience test (devil's advocate, pre-mortem, unknown unknowns —
   arch-architect-practice) before you record the recommendation. MVP hosting: `references/deployment-platform.md`.
9. **Mapping onto the agent team** — the needed skills: available / to be created (`python3 .tf/factory/build.py new-skill …`),
   the suggested `stack` of the implementing personas (e.g. `[fw-angular, lang-typescript]`).
9a. **A start from the official generator and failed gates.**
   - Say what the project will start with: the official generator or a mature template (the command and version from a source with a date),
     never an empty directory. Confidence: checked by us / registered, untested / manual. eng-repo-readiness sets up
     the skeleton.
   - A candidate that failed the friendliness gate does not go into the recommendation "by default". When the human chooses it:
     name the failed gates, give the best alternative from the same family, describe the compensation (concrete rules for
     CLAUDE.md) and record `quality_override: yes` with a justification in stack-decision.
   - The human's self-check (5 questions): types? an official starter? recognizable conventions? current documentation?
     **will I recognize that the agent is doing something against the practice of this stack?** Two "no" answers → recommend the "boring" option.
10. **Record** — stack-decision.md (`proposed`), an ADR for key decisions, rows in decisions.md, an entry in the log; a human accepts it.

When the problem is team friction (a slow build, long feedback, standards for many teams), not the technology choice
itself — first a DevEx diagnosis and the migration cost in fe-engineering-levels; buying or changing a tool is the result of
that diagnosis.

## Anti-patterns
A choice for the CV or fashion; benchmarks unrelated to the drivers; microservices "just in case"; versions outside the compatibility range;
a recommendation without the team's skills and constraints; facts (versions, licences, EOL) from memory.

## Example
**Situation:** "The backend of a fault reporting app; 4 people write TypeScript, the frontend is in Angular, data in the EU."
**Result** (all candidates passed the mandatory filters; facts from `researcher` with a source and a date):

| Criterion (weight) | A: TypeScript + Node.js ("boring") | B: Java + Spring | C: Go |
|---|---|---|---|
| team skills (5) | 5 | 2 | 2 |
| friendliness for AI agents (4) | 5 | 4 | 2 (no `lang-go` skill) |
| **Weighted total (7 criteria)** | **106** | 95 | 82 |

Decision `proposed`: A + PostgreSQL (competition for ticket assignment), a modular monolith; an ADR, a human accepts it.
More examples: `references/examples.md`.

## Sources
- The 10xDevs course, ed. 3 (2026), lesson 4.1 (stack), module 1, lessons 2 and 5 (agent friendliness criteria, the deployment
  platform, the resilience test), module 2, lesson 4 (service visibility for agents) — training material
  (accessed 2026-10-09); described in our own words.
