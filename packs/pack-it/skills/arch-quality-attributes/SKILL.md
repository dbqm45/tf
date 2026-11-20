---
name: arch-quality-attributes
description: Use for quality attributes — scenarios, trade-offs, fitness functions, choosing an architecture style.
metadata:
  review: "2027-10-17"
  catalog: "Use when establishing architectural drivers — quality attribute scenarios (performance, availability, security, modifiability…), constraints, prioritization (the utility tree), trade-offs, fitness functions and choosing an architecture style (modular monolith, microservices, events). Not for choosing specific technologies (arch-tech-selection)."
  keywords: "wymagania niefunkcjonalne, wymagania jakościowe, system ma być szybki, wysoka dostępność, mierzalne wymaganie, scenariusz jakości, cel czasu odpowiedzi, drzewo użyteczności, kompromisy architektoniczne, wybór stylu architektury, monolit czy mikrousługi, non-functional requirements, quality requirements, fast and available, high availability, measurable requirement, quality attribute scenario, response time target, utility tree, architecture trade-offs, choose an architecture style, monolith or microservices"
---

# Quality attributes and architecture styles

The architecture is determined by **drivers**: the most important quality attributes, constraints and key functions.
Without them, choosing a technology is a matter of taste.

## A quality attribute scenario (recorded in requirements.md)
`source → stimulus → (environment) → artifact → response → measure`, e.g.
"100 users book a room at the same time at peak → the system accepts the requests → p95 < 300 ms, 0 double bookings".
A scenario without a measure is not a scenario ("the system must be fast").

Attributes to review (ISO 25010, abbreviated): performance, availability/reliability, security, modifiability,
testability, scalability, usability and accessibility (a11y), interoperability, portability, maintenance cost, regulatory compliance.
Record an availability or performance scenario straight away as an SLI and an SLO (the ratio of good events, a threshold, a time window), and commitments
to customers as an SLA looser than the SLO — ops-sre-incidents, `.claude/skills/ops-sre-incidents/references/sli-slo-sla.md`.

## Priorities — the utility tree
Every scenario: **(importance for the business, technical difficulty)** on an H/M/L scale. The architecture is shaped by the **(H,H)** scenarios —
3–5 of them. The rest are requirements to meet with "ordinary" means.

## Trade-offs
Name them explicitly in an ADR: e.g. immediate consistency ↔ availability, performance ↔ modifiability (cache, denormalization),
security ↔ usability. A **sensitivity point** = a decision an attribute depends on; a **trade-off point** = a decision
affecting several attributes in opposite directions.

## Architecture styles — the simplest by default
| Style | When | Cost |
|---|---|---|
| **Modular monolith** (default) | one team or a few, contexts as modules with boundaries (ddd-context-mapping) | low; boundaries guarded by architecture tests |
| Microservices | independent deployment/scaling of contexts, many autonomous teams (proc-team-topologies), different reliability requirements | high: the network, eventual consistency, observability, a platform |
| Event-driven architecture | integrating many contexts, asynchronous reactions, audit | the complexity of tracing flows |
| Serverless / BaaS | irregular traffic, a small team, generic subdomains | provider dependency, limits |
A fuller catalogue (layers, client–server, SOA, peer-to-peer, microkernel, blackboard, publish–subscribe, pipes
and filters, MVC/MVVM) with signals of a bad choice: `references/style-catalog.md`.
Data architecture (ACID, CAP and PACELC, eventual consistency, kinds of NoSQL databases, OLTP vs OLAP, warehouses, ETL/ELT,
CDC, batch and stream processing): `references/data-architecture.md`.
A glossary of cloud patterns (44 patterns with a map to the factory's skills) and choosing a runtime platform (PaaS, functions,
containers, Kubernetes, machines): `references/cloud-patterns.md`.
Move from a monolith to services only when a specific (H,H) scenario requires it — split along context boundaries.

## Fitness functions
Turn the key attributes into automated tests in CI: a module boundary lint, a performance budget (p95 in a load test),
a frontend bundle size budget, a dependency scan, a restore-after-failure test. An architecture nobody checks drifts.
Modifiability can be measured: a change impact report for a business metric (ddd-model-stress-test — how many requirements change 0–1 modules)
and a coupling profile of critical boundaries (ddd-connascence-analysis — the dynamic band does not grow between releases).

## Result
The "Quality attributes" section in `03-requirements/requirements.md`, "Decision drivers" in `04-architecture/stack-decision.md`,
the style and trade-offs in an ADR (core-project-record).

## Example
**Situation:** "The room booking system must be fast and reliable — write down the quality requirements."
**Result** (scenarios with a measure and a priority):

| ID | Scenario | Priority |
|---|---|---|
| QA-1 | 100 employees book at the 8:45–9:15 peak → the API accepts the requests → p95 < 300 ms | (H,H) |
| QA-2 | 2 people book the same slot in the same second → 0 double bookings | (H,H) |
| QA-3 | a user opens the calendar → an SLO of 99.5% successful requests in a 30-day window | (H,M) |

Style: a modular monolith. Fitness functions: a load test with a p95 threshold for QA-1, a concurrency test (50 attempts → 1 success) for QA-2.
More examples: `references/examples.md`.
