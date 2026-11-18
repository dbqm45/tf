# The Availability archetype — mapper (resource availability over time, blocks)

> **Contents:** Fit test · Model (the essence) · Preventing interval overlap · In code — what to watch out for · Questions · Mapping steps · Decisions to check (R/A/X) · Result format · Patterns and pitfalls · Quality check · Example (shortened)

It turns requirements like "is the resource free?" into one contract: **block / release / disable** a resource in a time interval
by an owner. A booking, servicing, relocation or a breakdown are only **clients** of the contract — the model does not know the reasons
for unavailability. The effect: a new reason for unavailability does not change existing methods. The common protocol (questions, "It depends", the R/A/X check, recording): `SKILL.md` → "Mapper — the common protocol".

## Fit test
**The core question:** *is the resource at a given time (or now) free or held by exactly one owner?*
Yes → it fits. The question "how many units are left?" → a value (Accounting); "who gets the next one?" → Waitlist.

| Signal in the requirements | Fits? |
|---|---|
| "must not be booked twice", double bookings | ✅ |
| servicing / downtime / relocation / a breakdown disables the resource | ✅ |
| "is the room/car/workstation free on date X?" | ✅ |
| a block "now" with a deadline ("we hold it for 15 minutes") | ✅ the simple variant |
| `reserved`, `inMaintenance` flags in the resource entity | ✅ a signal for refactoring |
| "a room for 10 people, 7 taken", a pool of tickets | ⚠️ borderline |
| "who gets the released place?" | ❌ → Waitlist |
| "whom to assign to match competences / maximize value?" | ❌ → General assignment |
| "what can be done in parallel?", critical path | ❌ → Planning |
| "booking: placed → paid → cancelled" | ❌ a state machine of the agreement (which *uses* Availability) |

**Borderline cases:**
- *Availability vs Accounting* — is the unit **indivisible** (a binary slot free/taken)? Yes → Availability.
  A numeric capacity consumed partially ("7 of 10") → Accounting (a pool). The deciding question: *does the customer choose a specific seat
  (12A)?* Yes → N slot resources in Availability; no → a pool in Accounting.
- *Future dates or only "now"?* Bookings in the future → the time variant (segments); "free now / taken until T"
  (a scooter, a licence, a workstation) → the simple variant.
- *Choosing a resource by features* ("someone with SEP electrical qualifications") — the choice is General assignment, the occupation itself — Availability.

## Model (the essence)
**Problem levels:** (1) exclusive access — no double booking (a car, a seat, a room); (2) unavailability for other
reasons — servicing, relocation, a breakdown; (3) transitions with rules — do not send a car with an active booking to servicing, do not
withdraw a car that is in servicing or has bookings, do not book a car that is in servicing or withdrawn.

| Evolution of solutions | What breaks |
|---|---|
| Flags in the entity (`reserved`, `inMaintenance`, `inRelocation`) | mixes unrelated matters with the resource data; loses *who* and *for when* |
| Separate Booking / Servicing / Relocation models, checking in services | each new reason multiplies the conditions in all methods (13, then 21 checks); the "free in time?" logic is scattered, no single source of truth, an explosion of combination tests |
| **A stable abstraction of availability over time** | the client only asks "are you available?" (information hiding); the reasons merely use the contract |

- **The contract (the module edge):** `block(resource, interval, owner)`, `release(…)`, `disable(…)`. The business service has
  one condition: "did the block succeed?".
- **The `ResourceAvailability` segment** — a small aggregate: the resource, optionally a parent resource (grouping), the interval, the block, the version.
- **A dynamic aggregate** — an operation on a longer interval assembles a group of segments and blocks them together in one transaction.
- **Block states:** free · blocked by an owner · disabled by an owner (e.g. servicing).

| Operation | Transition rule |
|---|---|
| disable | always; only the one who disabled it may enable it again |
| block | only free; not blocked by another; disabled — nobody (including the one who disabled it) |
| release | only the current owner of the block |

**Evolution of the implementation** (the contract does not change):

| Variant | Problem |
|---|---|
| One calendar for all resources | loads everything; conflicts between unrelated resources; performance drops with the number of resources |
| A calendar per resource | conflicts on concurrent operations on the same resource for **different** dates |
| A calendar per resource per period (week/month) | trouble at period boundaries; good only with natural business boundaries |
| **Per resource per small time segment** ✔ | loads only the segments from the request; a conflict only on real overlap |

**The simple variant (no calendar)** — only "is it free **now**"; one block per resource:

| Block state | Meaning |
|---|---|
| none | free |
| servicing | the initial state after registration — the resource must be activated |
| withdrawal | the resource is withdrawn |
| owner | blocked by someone until a defined moment |

Operations: *register* (start in servicing) → *activate* (only from servicing); *withdraw* (only free or in servicing);
*block for a time* (only free); *extend indefinitely* and *unblock* (only the current owner). **Expiry:** a block has
a deadline; a periodic job releases the expired ones and publishes "block expired". Each operation returns a success event or
a rejection with a reason ("resource blocked", "no block for this owner") — easy to handle at the edge and in the UI.

## Preventing interval overlap
- **PostgreSQL:** a time range type + an exclusion constraint (a GiST index) on (resource, interval) —
  the database itself rejects overlapping intervals; conflict queries use the overlap operator.
- **Other databases — normalization and segmentation:** extend the interval to segment boundaries (10:05–11:30 with 30' → 10:00–11:30),
  split it into segments, uniqueness of (resource, start, end). Requests overlapping by even 5 minutes compete for the same record.
- Segment length = a compromise between precision and the number of records.
- **The calendar read model:** operationally fine-grained segments, the user wants periods ("1–3 January free, 3–7 taken by X").
  Merge adjacent segments of the same owner (window functions in SQL) → a map owner → intervals; "no owner" =
  free. The front end builds day/month views and filters from it.

## In code — what to watch out for
- Write a group of segments with version control in one statement (`UPDATE … WHERE version = expected`): **the number of changed
  rows = the number of segments**; fewer = a conflict, roll back the whole thing.
- `disable` takes blocks away from others → a "resource taken over" event with the list of previous owners, so that their processes (a project,
  a booking) can react.
- Half-open intervals `[from, to)`; time with a zone (`timestamptz`), computed in UTC; months in some languages start at 0 —
  test boundary dates.
- A concurrency test: N parallel attempts to block a segment → exactly one succeeds (or ≥ 1 ends with a conflict),
  a consistent final state.

## Questions
**A — standard decisions:**
- What are the reasons for unavailability and who is their **owner**? Which are a block and which a disable?
- Do we book **future dates** or only "now"? (time / simple variant)
- How long are typical blocks and how often do they overlap? (segment length, conflicts)
- Do resources form groups/hierarchies (a room in a building, a fleet)? (parent resource)
- Disabling with existing blocks: does it **take** them away (a "taken over" event) or is it rejected?

**B — gaps** (examples):
- expired blocks (an unpaid booking) — expiry, who sets the deadline? · a buffer between blocks (cleaning,
  travel)? · extending a block? · history/audit of blocks? · a calendar view? · what after a release — notify Waitlist? · blocking several resources at once (a room + a projector) — all or nothing?

## Mapping steps
1. **Resources** — what we block; identification; the parent resource.
2. **Reasons for unavailability** → owner + operation (`block` / `disable`); no reason enters the model as a flag.
3. **Variant** — time (segments) or simple (a block "now" with a deadline).
4. **Time** — granularity, segment length, interval normalization, `[from, to)`, the zone.
5. **Transition rules** — an operation → condition table; defer rules depending on *who/why* to the policy layer.
6. **Expiry and extension** — the deadline as an operation parameter; a periodic job; an "expired" event.
7. **Overlap** — an exclusion constraint or segment uniqueness; group version control.
8. **Events** — success/rejection with a reason, "resource taken over", "block expired" and who consumes them.
9. **Read model** — consolidated periods.

## Decisions to check (R/A/X)
variant (time/simple) · segment length · parent resource · disabling vs existing blocks · who may enable ·
the expiry deadline and who sets it · extension · buffer · atomicity of blocking many resources · the time zone and interval
boundaries · the database mechanism · event consumers.

## Result format
```markdown
# Availability model: <area>
## Resources          — | Resource | Identification | Parent resource | Variant |
## Concept mapping    — | Domain concept | Archetype element | Justification |
## Unmapped concepts
## Reasons for unavailability — | Reason | Owner | Operation | Expires? |
## Time               — granularity, segment, normalization, zone
## Transition rules   — | Operation | Condition | Rejection (reason) |
## Expiry             — | Block | Deadline (parameter) | What after expiry |
## Events             — | Event | When | Consumers |
## Overlap            — mechanism (constraint / segments), version control
## Read model         — calendar views
## Decisions (R/A/X)  — | Decision | Source |
## Notes              — assumptions (X), edge cases, variable policy parameters
```

## Patterns and pitfalls
- Model **availability**, not the reasons — a reason is only the owner of a block.
- "May customer X book room Y?" (a booking limit, a subscription, a role) — **authorization outside the archetype**; the archetype
  guards only the invariant "one owner at a time".
- A variable policy ("a VIP has 48 h to pay, the rest 2 h") → the archetype gets a ready expiry deadline.
- The state of the agreement/booking (paid, cancelled) lives outside the archetype; Availability knows only the block.

## Quality check
- [ ] every reason for unavailability has an owner and an operation; no flags in the resource entity
- [ ] the transition rules table covers block/release/disable (or the simple variant's operations)
- [ ] time granularity, `[from, to)` and the zone defined; the anti-overlap mechanism chosen
- [ ] expiry: the deadline as a parameter, a periodic job, an event
- [ ] the mapping and "Unmapped concepts" present; no material (X)

## Example (shortened)
**Input:** "A coworking space rents rooms by the hour. A room can be disabled for cleaning or renovation. A booking not paid
on time is lost."

```markdown
## Resources — | room | number | floor (parent) | time, segment 15' |
## Mapping — booking → block (owner: booking id) · cleaning/renovation → disable (owner: facilities) ·
   "is lost" → block expiry
## Unmapped — payment (→ Accounting/agreement) · the hourly price (→ Pricing)
## Rules — renovation takes blocks away (A) → "resource taken over" → the booking notifies the customer
## Expiry — payment deadline: A "how much time?" — It depends → parameter `block_valid_to` computed by the payment policy
## Decisions — segment 15' (X → technical, in Notes) · a 15' buffer for cleaning after each booking (X → ask)
```
