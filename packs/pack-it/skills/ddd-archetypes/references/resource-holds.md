# Resource holds — exclusive use of a resource over time, no double booking

## When it applies
- Signal: for some interval (or for the present moment) a resource is either free or held by exactly one holder.
- Not this: "how many are left" in a divisible pool → value ledger; "who gets it next" → waiting list.
- Divisible or not? Can the buyer pick the exact unit (room 214, seat 14C, lens serial 88213)? Yes → each unit is its own
  resource. No (any of 30 identical parking spots) → a counted pool.

## Core shape
- **Model availability, not reasons.** Bookings, maintenance, relocation, breakdown, a checkout cart — all are clients
  that request a hold. Business services check one result: did the hold succeed?
- Minimal contract:
  - `hold(resource, holder, interval)` — fails on an interval already held or out of service;
  - `release(resource, holder, interval)` — only the current holder;
  - `takeOutOfService(resource, by, interval)` — always allowed, overrides other holds; only `by` may return it.
- Each call returns success or a refusal with the reason (`already-held-by`, `out-of-service`, `not-holder`).
- Taking out of service over existing holds either **rejects** or **pre-empts** them; on pre-emption emit an event listing
  the displaced holders so their processes (rebooking, refund) react.
- **Future-dates variant**: fine-grained time **slices** per resource (e.g. 15 min or 1 day) as small aggregates. A
  request over a longer interval loads only the affected slices and locks them together — conflicts occur only on real
  overlap. Coarser grains (one global calendar, one calendar per resource, a monthly bucket) cause false contention or
  month-edge bugs.
- **"Now only" variant**: one current hold per resource with an expiry — lifecycle registered → active → withdrawn, or
  held until T. A periodic sweeper releases expired holds and emits an event.

## Rules
- Intervals are half-open `[start, end)`; timestamps are time-zone aware and computed in UTC. Watch zero-based months in
  some languages (JavaScript `Date`) and DST transitions.
- Database-level guard: a range type with an exclusion constraint where the database has one (e.g. PostgreSQL `EXCLUDE
  USING gist` on `tstzrange`, be-database); otherwise snap intervals to slice boundaries and enforce `UNIQUE(resource,
  slice)`. Slice length trades precision against row count.
- Concurrency: version-check the whole slice group in one statement; affected rows must equal the number of slices,
  otherwise roll back. Test: N parallel attempts for the same interval → exactly one wins.
- Hold duration (cart 20 min, offer 48 h) is a parameter computed by a policy, not a constant in the model.
- Read model: merge adjacent slices with the same holder into periods for calendar views.

## Decisions to settle
- Buffers between holds (cleaning, travel, inspection)?
- Extending a hold?
- All-or-nothing holds over several resources (a kit of camera + lens + tripod)?
- Parent/child resources (a hall and its sections)?
- Pre-empt or reject when taking out of service?
- Audit of who held what.

## Belongs elsewhere
- The booking's commercial state (paid, cancelled, refunded) → the order or commitment.
- Whether a customer may book → authorisation.
- Which resource to choose → task selection; the order of stages → stage scheduling.

## Traps
- `reserved`, `under_maintenance` booleans plus hand-written overlap checks in each service.
- Separate models per reason (booking, maintenance) — every new reason multiplies cross-checks.
- Check-then-insert without a database guard — two customers get the same lens.
- Closed intervals `[9:00, 10:00]` making back-to-back bookings conflict.
- Optimistic UI showing "booked!" before the server confirmed.

## Worked example
Requirement: camera kits for rent; a cart holds a kit for 20 minutes during checkout; kits go out for sensor cleaning;
bookings weeks ahead; two people booked the same lens last week.
- Each lens and body is a resource (customers choose an exact kit). Slices of 1 hour; a 3-day booking locks 72 slices.
- Cart: `hold(KIT-12, cart-5531, [Mon 10:00, Thu 10:00))` with expiry 20 min (policy parameter); the sweeper releases it
  at expiry and emits `HoldExpired`; checkout converts it to a booking hold.
- Cleaning: `takeOutOfService(LENS-88213, maintenance, [Tue 08:00, Tue 14:00))`. Decision U: **pre-empt** only holds that
  start > 7 days ahead, otherwise reject — the `HoldsDisplaced` event lists affected bookings.
- Guard: `UNIQUE(resource_id, slice_start)`; the insert of 72 rows must affect 72 rows. Test: 20 parallel requests →
  1 success, 19 `already-held-by`.
- Paid / unpaid lives on the rental order, not on the hold.
