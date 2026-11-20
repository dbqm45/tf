# Waiting lists — more applicants than units

## When it applies
- Signal: when a unit frees up, someone must decide which waiting applicant gets it.
- Not this: background job queues (infrastructure), or work queues where every item will be served anyway and only the
  order matters.

## Core shape
- **List**: target resource (or pool), capacity, ordering rule — FIFO, or priority with a stable tie-break by arrival time.
- **Entry**: applicant id (party, booking), priority, arrival time, optionally units needed and a validity window.
- Operations: `join` (refused when full, or another stated overflow rule — a second list, evict the lowest-ranked),
  `takeNext` on release, `withdraw(id)`, size and contents, optionally the applicant's position.
- **Offer**: taking the next applicant creates a time-limited offer, not an immediate grant.
- Entry states: waiting → offered → accepted; offered → declined or timed out → the next applicant is offered; waiting →
  withdrawn or expired. Accepted, declined, timed out, withdrawn and expired are terminal.
- Underneath: a heap-based priority queue, hidden by the interface.

## Rules
- Working with resource holds: a release event triggers a policy that offers the unit to the next applicant **and places
  a hold for them for the offer's duration**. Acceptance turns it into a permanent hold; decline or timeout releases it and
  starts the next cycle. Without the hold, a walk-in booking races the offer.
- Priority is a parameter computed elsewhere (loyalty tier, medical urgency, sibling rule). Changing priority = remove
  and re-insert the entry, optionally keeping the original arrival time.
- Log every decision event (joined, offered, accepted, declined, timed out, withdrawn, expired) with the priority and
  arrival time used — this answers "why not me?".
- Offer duration is a parameter from a policy.

## Decisions to settle
- Overflow when the list is full: refuse, second list, evict lowest?
- An applicant needs more units than were freed — skip them, partial offer, wait?
- Parallel offers to several applicants (first to confirm wins)?
- Limits on declines; does a decliner rejoin at the back, keep their slot, or leave the list?
- Membership in several lists at once (and what happens to the others on acceptance)?

## Belongs elsewhere
- Holding the unit during the offer → resource holds.
- Computing priority → a policy.
- Notifying applicants → the application layer.

## Traps
- `ORDER BY created_at` as the whole design — no priority, no offer, no timeout, no audit.
- Granting the spot immediately to the next person who never answers.
- Unstable ordering among equal priorities (ties resolved by database whim).

## Worked example
Requirement: a summer camp has 40 spots per session; when full, families can join a waitlist of up to 25; siblings of
current campers go first; a cancellation gives the next family 48 hours to accept.
- List `Session-July-2`: capacity 25, ordering by priority (sibling = 1, other = 2), tie-break by arrival time.
- Overflow: the 26th family is refused with a message (decision U); alternative proposed: the August session's list.
- Cancellation → `HoldReleased(spot)` → policy calls `takeNext` → entry of family Kowalczyk (priority 1, joined
  2026-02-03 09:14) becomes *offered*, and the spot is held for them until +48 h.
- Accept within 48 h → hold becomes the camp booking. Timeout → hold released, entry *timed out*, next family offered.
- Dispute "we joined earlier": the log shows the other family had priority 1 (sibling), arrival time as tie-break.
