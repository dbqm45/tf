---
artifact: plan
phase: plan
status: proposed
version: 1
author: jan
created: 2026-09-27
updated: 2026-09-27
inputs: [docs/project/04-architecture/stack-decision.md, docs/project/04-architecture/adr/0001-modular-monolith.md, docs/project/04-architecture/adr/0002-booking-consistency-postgresql-exclusion-constraint.md, docs/project/04-architecture/adr/0004-m365-graph-outbox-integration.md, docs/project/03-requirements/requirements.md]
---
# Delivery plan: Room and desk booking (MVP)

## TL;DR
8 steps (vertical slices), each deployable. Step #1 (skeleton + CI) right after this plan is accepted.
The first slice with business value: #2 (H6 SSO) → #3 (H1 room booking, without M365). The M365 integration (#8) is
moved to the end and depends on IT's answer (S2/S3) — without it H1 works, only without an entry in the M365 calendar.
Bottleneck: 1 Java developer for the whole `booking`/`resources`/`identity` module — the back-end steps go sequentially.

## Steps (vertical slices, each deployable)
| # | Step | Stories | Executor (persona/role, tier) | "Done" criteria | Depends on |
|---|---|---|---|---|---|
| 1 | Skeleton: Spring Modulith modules (`identity`, `resources`, `booking`, `calendarsync` as empty ports), `ApplicationModules.verify()` in CI, Testcontainers, an Angular workspace + empty routing, a pipeline (GitHub Actions — to be confirmed with IT), deployment of an empty app to App Service dev. Includes spike S0 (availability of the services in the region) and S4 (MSAL Angular 22). | — (walking skeleton) | jan-backend (std) + the Angular front-end team (outside the jan team) | Pipeline green; `verify()` without violations; the app deploys and responds on `/actuator/health` in the target region | ADR-0001..0003 accepted (they are) |
| 2 | SSO sign-in with Entra ID, the `identity` module | H6 | jan-backend (std, skills be-auth-security) + front end (MSAL Angular) | An employee signs in with the company account; the back end verifies the token (resource server), the roles are available in the request context | Step 1 |
| 2a | Tactical design of the booking aggregate: `Allocation`/`Booking` (the Availability archetype), invariants, value objects (slot, status), the consistency boundary — before the implementation of step 3 | — | jan-ddd-analyst (deep, ddd-tactical-design + ddd-archetypes) | A short model recorded in `02-domain/` (aggregate, invariants, mapping to `allocation` from ADR-0002) | Step 1 |
| 3 | Booking a room for a time slot, **without** M365 synchronisation (modules `booking`+`resources`) — includes spike S1 (exclusion constraint + JPA + the 50 parallel test) | H1 (partly — without the M365 entry) | jan-backend (std) | The fitness function from ADR-0002 passes (50 parallel → 1 success, 49 × `RESOURCE_UNAVAILABLE`); the room booking UI works | Step 2, 2a |
| 4 | The resource availability calendar (a day/week view), a read model on `allocation` | H5 | jan-backend + front end | An employee sees the availability of rooms for a day/week | Step 3 |
| 5 | Booking a desk for a day — extending `resources` with the "desk" resource type (data + policy), without changes in `booking` | H2 | jan-backend | The modifiability test from ADR-0001 (a new resource type only through data/configuration) passes; a desk booking = the slot [00:00,24:00) in the office's time zone | Step 3 |
| 6 | Blocking a resource for maintenance (the facility role) | H3 | jan-backend | A blocked resource has the status `BLOCKED` in `allocation`, cannot be booked per the fitness function from step 3 | Step 3 |
| 7 | Automatic release of a booking without a check-in after 15 min | H4 | jan-backend | A background job runs an idempotent `UPDATE … RETURNING`; safe with >1 App Service instance | Step 3 |
| 8 | M365 integration: the `calendarsync` module, the outbox (Event Publication Registry), Microsoft Graph, application permissions — completes H1 ("an entry in M365") | H1 (completion) | jan-backend | A room booking creates/updates/cancels an event in the M365 calendar; a Graph failure does not block the booking (the synchronisation state visible in the UI) | Step 3; **IT's answers** (S2, S3) |

## Spikes
| ID | Question | When (step) | Criterion for dropping the choice |
|---|---|---|---|
| S0 | App Service Linux / PostgreSQL Flexible GP available in the target region? | Step 1 | Service missing → a fallback EU region (ADR-0003) |
| S1 | Exclusion constraint + JPA: mapping `23P01`, behaviour with 50 parallel requests | Step 3 | >1 success or p95 > 1 s → the `FOR UPDATE` variant (ADR-0002 option B) |
| S2 | Are the rooms already Exchange resource mailboxes? Two sources of truth? | Before step 8 | Bookings directly in Exchange cannot be blocked → a new version of ADR-0004, the user's decision |
| S3 | The M365 administrator's consent to `Calendars.ReadWrite` (RBAC for Applications) | Before step 8 | No consent → option C of ADR-0004 (an .ics invitation) |
| S4 | Compatibility of MSAL Angular 6.x with Angular 22 | Step 1 | Runtime/build errors → BFF (Spring `oauth2Login`, a session) |

## Schedule risks
- **Bus factor:** 1 Java developer handles steps 2, 2a→3, 5–8 sequentially — this is the critical path of the 3-month MVP; the front end (2 people TS/Angular) waits for the API contracts from steps 2–3. Mitigation: steps 4–7 have independent front-end parts that the front end can build on an API mock, when the contract (OpenAPI) from step 3 is agreed earlier.
- **Step 8 blocked by IT** (S2, S3) — if the answers are delayed, we deliver the MVP without M365 synchronisation (H1 partly met) and close step 8 after the answer, per ADR-0004.
- **The Azure region (S0)** unknown until confirmed — it can move step 1 by days if the region has to change.

## Open questions
- [ ] All questions from `stack-decision.md` stay open (the source of truth for rooms, the M365 consent, the region, check-in, the budget, repo/CI, TS skills on the back end) — step 8 does not start without answers to the first two.
- [ ] Who confirms "done" after each step (Product Owner) and at what rhythm (a Sprint Review every how often)? → user

## Handoff
- **For:** jan-backend (step #1), in parallel jan-ddd-analyst (step #2a, can start at once, independently of #1)
- **Task:** step #1 — the Spring Modulith module skeleton + CI with `ApplicationModules.verify()`; step #2a — tactical design of the `Allocation` aggregate
- **Read:** TL;DR, the rows of steps #1 and #2a, ADR-0001, ADR-0002
- **Do not:** do not start step 8 (M365) before IT's answer; do not build step 3 before #2a (the risk of a model without agreed invariants)
- **Done when:** step #1 deployed and green in CI, step #2a has its model recorded in `02-domain/`, both accepted by the user
