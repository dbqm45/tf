---
name: arch-tech-selection
description: Use when choosing or changing a stack — framework, database, hosting, tools — with knock-out filters, a weighted matrix, verified versions and a recorded decision.
metadata:
  review: "2027-05-20"
  catalog: "Use when choosing the technology stack for a new project (language, framework, database, hosting, tools) or deciding keep / improve / replace per area of an existing one — drivers and weights, knock-out filters (licence, data location, support horizon, security patches, team skills), the boring option, facts verified from primary sources with a date, a weighted matrix, conclusions from the domain model, agent friendliness and what to do when a chosen tool fails it, spikes with abandonment criteria, MVP hosting, the record in stack-decision.md. Not for quality attribute scenarios and the utility tree (arch-quality-attributes), communicating and recording architectural decisions in general (arch-architect-practice)."
  keywords: "wybór stacku, jaki stack, jaki framework, jaka baza danych, wybrać bazę, wybrać framework, porównanie frameworków, stack dla startupu, nowy projekt jaki język, hosting MVP, gdzie wdrożyć aplikację, platforma do wdrożenia, przepisać od zera, przepisanie aplikacji, migracja stacku, stary stack, AngularJS, Java 8, zostawić czy wymienić, strangler fig, macierz decyzyjna, macierz ważona, filtry obowiązkowe, nudna technologia, przyjazność dla agentów, framework bez typów, klient upiera się przy frameworku, zgodność wersji, kompatybilne wersje, czy wersje są zgodne, własny algorytm czy solver, planowanie tras, spike, kryterium porzucenia, decyzja o stacku, websockety hosting, serverless, tech stack, choose a framework, which database, pick a database, framework comparison, startup stack, MVP hosting, where to deploy, deployment platform, rewrite from scratch, stack migration, legacy stack, keep or replace, weighted decision matrix, knock-out criteria, boring technology, agent friendly stack, untyped framework, version compatibility, build vs solver, abandonment criterion, stack decision"
---

# Choosing a stack — a recorded decision, not a list of favourites

The result is a recommendation with reasons and facts checked today. A key input missing (the team's skills, where data
must live, the budget) → ask; do not assume.

**Inputs (read TL;DR and the indicated sections):** the brief, `03-requirements/requirements.md` (quality scenarios),
domain documents, optionally `02-domain/algorithms.md` and `02-domain/stress/*.md`. Existing project: run
`python3 .claude/hooks/detect_stack.py` first.
**Output:** `docs/project/04-architecture/stack-decision.md` with status `proposed` (template: core-project-record), an ADR
for each key decision, rows in `decisions.md`, a log entry. A human accepts.

## Procedure
1. **Drivers.** 3–5 quality scenarios rated (H,H) (arch-quality-attributes) plus constraints; give each a weight 1–5.
2. **Knock-out filters** — a candidate that fails one is rejected without scoring:
   - licence acceptable for the product;
   - hosting and compliance (e.g. personal data must stay in the EU);
   - a support horizon covering the product's life (LTS, end-of-life date);
   - security patches still being released;
   - the team can start with it now, or there is a real hiring plan.
3. **Candidates.** 2–3 per area, and always the **boring option**: what the team already knows or the default of the
   ecosystem. Every additional technology costs maintenance, hiring and skills.
4. **Facts from primary sources, with a date.** Versions, support dates, compatibility between components (a framework's
   major version usually pins a range of its language or compiler), licences — from release pages, official docs and
   registry queries (`npm view <pkg> version`, `pip index versions <pkg>`). Delegate the lookup to the `researcher` agent
   (it returns facts with sources); never answer a version or compatibility question from memory (core-grounding,
   core-source-research).
5. **Weighted matrix.** Criteria:
   - fit to the drivers;
   - team skills (time to learn before the first release);
   - ecosystem maturity;
   - cost and complexity of running it;
   - agent friendliness (section below);
   - lock-in and exit cost;
   - security (vulnerability history, patch speed, secure defaults).
   Total = Σ (score 1–5 × weight). The matrix supports the decision; a close result means "pick the boring one".
6. **Conclusions from the domain model** (ddd-deep-modeling, ddd-archetypes, ddd-algorithm-recognition):
   - generic subdomain → buy or SaaS behind an anti-corruption layer;
   - CRUD or supporting subdomain → the simplest framework, generators, even a BaaS;
   - complex core rules → a language with a strong type system (sum types, immutability) and easy domain tests;
   - competition for a scarce resource → a strongly consistent database with constraints (e.g. exclusion constraints on
     overlapping ranges — be-database);
   - integration between contexts → messages with an outbox (be-messaging-outbox); read-heavy → read models or a cache;
   - an algorithmic core (scheduling, routing — often NP-hard) → an optimisation library or solver behind a domain
     interface, plus a time-boxed spike; geography → a geo extension of the database; similarity → full-text or vector index.
7. **Architecture style:** a modular monolith unless the drivers justify something else.
8. **Risks and spikes.** Every serious uncertainty gets a time-boxed experiment with an **abandonment criterion** (what
   result makes us drop the option). Before recording, challenge the leading option — devil's advocate, pre-mortem,
   unknown unknowns (arch-architect-practice, `.claude/skills/arch-architect-practice/references/decision-resilience-test.md`).
   MVP hosting: `references/deployment-platform.md`.
9. **The agent team.** Which `lang-*`, `fw-*`, `tool-*` skills exist for the stack and which must be created
   (`python3 .tf/factory/build.py new-skill …`); a suggested `stack` field for implementing personas, e.g.
   `[fw-angular, lang-typescript]`.
10. **Starting point.** The official generator or a mature template: the command and version from a dated source, never an
    empty directory (eng-repo-readiness). Label the confidence: checked by us / listed but not tried / manual.

## Agent friendliness
An agent works well with a stack it can read, run and check without a human. Look at:
- **types** — typed data contracts (static types, schemas) so mistakes surface at compile or validation time;
- **conventions** — established places for routing, tests, configuration, so the agent finds and puts things where people expect;
- **popularity within the language family** — compare a framework with its siblings in the same language, not with the whole
  market; widely used tools have more examples and fewer surprises;
- **current, versioned documentation** in a machine-readable form (Markdown, `llms.txt`, a documentation server);
- fast tests, deterministic tools, low integration friction (one command, one variable, one documentation page for a
  service), and existing skills for the stack.

**When the human picks a candidate that does poorly here** (e.g. a client insists on an untyped framework with thin docs):
it is not in the recommendation by default. Name what it lacks, name the best alternative in the same language family, and
propose compensation — concrete rules for `CLAUDE.md` (where files go, which commands verify a change, which patterns are
forbidden), schema validation at boundaries, extra tests. Record `quality_override: yes` with the reason in
`stack-decision.md`. A quick question for the human: will you notice when the agent drifts from this stack's practice?
If not, recommend the boring option.

Team friction (slow builds, long feedback, many teams' standards) is diagnosed first as developer experience
(fe-engineering-levels); a tool change is a possible outcome, not the starting point.

## Existing project
- Detect the stack, then give a verdict **per area**: keep / improve / replace, each with the migration cost.
- Replace step by step along context boundaries (strangler fig), never in one switch.
- Reject "rewrite because it is old" when no driver gains: a full rewrite costs everything up front and delivers value only at the end.
- A component that fails a knock-out filter (e.g. a framework without security patches) must be replaced — plan it.
- Worked table: `references/examples.md` §2.

## Anti-patterns
Choosing for a CV or fashion; benchmarks unrelated to the drivers; microservices "just in case"; versions outside the
compatible range; ignoring team constraints; facts from memory.

## Example
**Situation:** "A team of 4 knows Python; B2B SaaS with EU customer data; pick a framework and a database."
**Result (excerpt of `stack-decision.md`):**
- Drivers: tenant isolation (H,H, weight 5), time to first release (weight 4), EU data residency (constraint).
- Filters: a US-only hosted database rejected (data location); a framework whose current major has no security support rejected.
- Candidates: Django + PostgreSQL (boring option), FastAPI + PostgreSQL, a Node framework (rejected on team skills).
- Facts: versions and support dates from the projects' release pages, checked 2026-11-20 by `researcher`.
- Matrix: Django 4.4, FastAPI 4.0 — Django wins on conventions and admin generators.
- Spike: row-level security for tenants in 2 days; abandonment criterion — policies cannot cover the reporting queries.
- Challenge: pre-mortem "a tenant saw another tenant's invoice" → isolation test in CI.
- Status `proposed`; the human accepts.
More cases (matrix, keep/improve/replace, solver spike): `references/examples.md`.

## Sources
- Facts about versions, support and licences come from each project's release pages and package registries, checked at
  decision time; the skill itself contains no version facts.
