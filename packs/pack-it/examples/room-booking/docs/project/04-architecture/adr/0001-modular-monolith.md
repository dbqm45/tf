---
artifact: adr
phase: architecture
status: accepted
version: 1
author: tomasz-solution-architect
created: 2026-09-27
updated: 2026-09-27
inputs: [docs/project/03-requirements/requirements.md, docs/project/04-architecture/stack-decision.md]
---
# 0001. Architecture style: a modular monolith (Spring Modulith)

## Context
One team (2 × TS/Angular, 1 × Java), MVP in 3 months, a low operations budget. Scenarios (H,H)/(H,M):
booking consistency (50 simultaneous attempts → 1 success), modifiability (a new resource type ≤ 2 days), 99.5% availability during 7:00–19:00.
No scenario requires independent scaling or deployment of a part of the system.

## Decision
One Spring Boot application (one deployment unit, one database) divided into modules with a small interface at the edge:
`identity` (Entra ID, roles), `resources` (the catalogue of resources and types, policies), `booking` (the Availability archetype: bookings,
maintenance blocks, no-show release), `calendarsync` (an ACL to Microsoft Graph). The modules communicate through the module's public API
and application events; `ApplicationModules.verify()` checks the boundaries in CI. The Angular front end is built separately,
served by the same application **[proposal]**.

## Options considered
- Modular monolith — pros: the simplest deployment and observability, an ACID transaction covers the booking and the outbox, the team knows Spring; cons: a shared deployment of the front end and the back end, the boundary discipline needs tests.
- Microservices (e.g. booking / resources / calendarsync) — pros: independent deployments; cons: eventual consistency between services makes the "0 double bookings" guarantee harder, the network, the platform and the monitoring are beyond what 1 back-end developer can do in 3 months.
- Serverless (Azure Functions) — pros: cost at low traffic; cons: the same transactions and database constraints as in the monolith, but more parts, cold starts at the 9:00 peak, weaker Spring support.

## Consequences
- We gain: one transaction for the booking + the event (outbox), one pipeline, a low cost.
- We lose: independent scaling of the modules (not needed with 300 users).
- Modifiability: a new resource type touches only the `resources` module (data + policy); `booking` operates on (resource, slot).
- Extracting a service (e.g. `calendarsync`) is possible later along the module boundary, when a concrete scenario demands it — a reversible decision.
- To do: the module skeleton + the `verify()` test in the first iteration.
