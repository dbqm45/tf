---
artifact: decisions
phase: meta
status: accepted
version: 1
author: system
created: 2026-09-27
updated: 2026-09-27
inputs: []
---
# Decision register

| ID | Date | Decision | Rationale (1 sentence) | Status | Author | Details |
|---|---|---|---|---|---|---|
| D-001 | 2026-09-27 | Style: a modular monolith (Spring Modulith), one deployment unit | 1 team, MVP in 3 months, no scenario requires independent scaling; one ACID transaction for the booking and the outbox | accepted | tomasz | [ADR-0001](04-architecture/adr/0001-modular-monolith.md) |
| D-002 | 2026-09-27 | Stack: Java 25 + Spring Boot 4.1, Angular 22 + MSAL Angular, PostgreSQL 18 | the team's skills and the fewest technologies; versions supported within the MVP horizon | accepted | tomasz | [stack-decision](04-architecture/stack-decision.md) |
| D-003 | 2026-09-27 | Booking consistency: an exclusion constraint (resource, slot) in PostgreSQL, bookings and blocks in one table | the "0 double bookings" guarantee in the database, regardless of the code path | accepted | tomasz | [ADR-0002](04-architecture/adr/0002-booking-consistency-postgresql-exclusion-constraint.md) |
| D-004 | 2026-09-27 | Hosting: App Service Linux + PostgreSQL Flexible GP, one EU region (Poland Central after verification in S0) | the simplest operations; 99.5% during 7:00–19:00 without multi-region HA | accepted | tomasz | [ADR-0003](04-architecture/adr/0003-hosting-app-service-region-ue.md) |
| D-005 | 2026-09-27 | M365: Graph with application permissions (RBAC for Applications), outbox, one-way sync | the booking does not depend on Graph's availability; conditional — waiting for IT's answer | accepted | tomasz | [ADR-0004](04-architecture/adr/0004-m365-graph-outbox-integration.md) |
