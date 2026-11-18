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
# 0002. Booking consistency: PostgreSQL + an exclusion constraint on (resource, slot)

## Context
Scenario (H,H): 50 people book the same room at the same time at 9:00 → exactly 1 success, the rest a clear refusal,
0 double bookings. Rooms are booked for any slot (H1), desks for a day (H2), facility blocks a resource for
maintenance (H3), the system releases no-show bookings (H4). Each of these cases occupies a resource in time (the Availability archetype).

## Decision
Azure Database for PostgreSQL Flexible Server 18. One allocation table (bookings **and** maintenance blocks) with the column
`period tstzrange` (bounds `[)`, so adjacent slots do not collide) and the constraint:

```sql
CREATE EXTENSION IF NOT EXISTS btree_gist;  -- add it to the azure.extensions parameter first
ALTER TABLE allocation ADD CONSTRAINT allocation_no_overlap
  EXCLUDE USING gist (resource_id WITH =, period WITH &&)
  WHERE (status IN ('BOOKED', 'CHECKED_IN', 'BLOCKED'));
```

The application does a preliminary availability check (for a nice message), but **the guarantee is the constraint in the database**:
the SQLSTATE `23P01` error is mapped to the operation result "rejected: resource taken" (HTTP 409, code `RESOURCE_UNAVAILABLE`).
A release (cancellation, no-show) = a status change outside the `WHERE` predicate, so the slot returns to the pool at once.
No-show: a job runs every minute one idempotent `UPDATE … SET status = 'RELEASED' … RETURNING id` — safe also with several instances.

## Options considered
- Exclusion constraint (chosen) — pros: a guarantee independent of the code path (also future imports, jobs, new resource types), any slots, maintenance blocks in the same mechanism; cons: specific to PostgreSQL, needs `btree_gist`, JPA does not express the range type directly (mapping through a native type / a Hibernate custom type — spike S1).
- `SELECT … FOR UPDATE` on the resource row + an overlap check + insert — pros: portable, simple; cons: correctness depends on **every** write path taking the lock; it serialises all bookings of a resource. The fallback option if S1 turns out badly.
- Optimistic locking (`@Version` on the resource/day) — cons: with 50 simultaneous attempts 49 conflicts and retries, more handling code.
- A unique index on (resource, slot) with a fixed slot grid (e.g. 15 min) — pros: the simplest database mechanism; cons: many rows per booking, a rigid granularity, multi-day maintenance blocks = hundreds of rows.
- `SERIALIZABLE` for the booking transaction — correct, but serialisation errors and retries at the peak; no advantage over the constraint.

## Consequences
- The consistency sensitivity point lies in the database schema — changes to the `allocation` migrations need a review.
- Fitness function in CI: a Testcontainers test (PostgreSQL 18) with 50 parallel requests → exactly 1 success.
- Lock-in to PostgreSQL (accepted; Azure Flexible Server is a managed service).
- A desk for a day = the slot [00:00, 24:00) in the office's time zone — an explicit decision about the time zone is needed (we store `timestamptz`, UTC).
