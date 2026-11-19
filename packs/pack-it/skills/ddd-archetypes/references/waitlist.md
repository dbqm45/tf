# The Waitlist archetype — mapper (waiting list, capacity, priorities)

> **Contents:** Fit test · Model (the essence) · Questions · Mapping steps · Decisions to check (R/A/X) · Result format · Patterns and pitfalls · Quality check · Example (shortened)

It turns requirements in which **supply is limited and there are more candidates** (places on a course, tickets, appointments, a product
in pre-sale) into a waiting list model: capacity, queue type, priorities, an offer with a deadline and cancellations. The effect:
the decision "who gets the released resource" is **fair, predictable and explainable**, not buried in `ORDER BY data_wpisu`
(an entry-date column, which does not handle priorities, a limit or cancellations). The common protocol: `SKILL.md` → "Mapper — the common protocol".

## Fit test
**The core question:** *when a unit of the resource is released, must you choose **who of those waiting** gets it?*
Yes → it fits. If nobody is waiting and the question is "is it free?" → Availability.

| Signal in the requirements | Fits? |
|---|---|
| "a reserve list", "sign me up when a place frees up" | ✅ |
| "order of applications", "regular customers have priority" | ✅ |
| "at most 20 people on the reserve list" | ✅ list capacity |
| "you have 24 h to confirm, then the next person" | ✅ an offer with a deadline |
| "is the room free on Thursday?" | ❌ → Availability |
| "how many places are left?", a pool of tickets | ❌ → Accounting (a pool) / Availability |
| "whom to assign to match competences and maximize value?" | ❌ → General assignment |
| "a queue of jobs to process" (worker, broker) | ❌ a technique, not a business archetype |
| "tickets handled by SLA / urgency" | ⚠️ borderline |

**Borderline cases:**
- *A ticket queue (helpdesk)* — do those waiting **compete for a limited resource** and may not get it? Yes → Waitlist.
  Every ticket will be handled anyway, only the order of work matters → General assignment / a state machine.
- *A one-off allocation (a lottery, recruitment)* — a choice from the pool at once, not "on release" → a selection rule over the list
  (still Waitlist if the next one goes after an offer is rejected) or General assignment when the match matters.
- *Position in a queue vs a balance* — order, not value; loyalty points giving priority are computed by Accounting, the list
  gets a ready priority.

## Model (the essence)
- **Waiting list** — an identifier, **the resource/offer** it concerns, **capacity**, **queue type**:
  - **FIFO** — first come, first served;
  - **priority** — an element has a priority (a regular customer, medical urgency), the others get the default priority;
    with equal priority the entry time decides (stability = fairness).
- **Element (entry)** — the identifier of the one waiting (a party, a booking, an order), a priority, the entry time, optionally the number
  of units needed and the entry's validity window.
- **Operations:** add (refusal when capacity is exceeded) · **take the next one** (when the resource is released) · remove by
  identifier (cancellation) · preview of the content and size · (optionally) the position of the one waiting.
- **Offer** — "the next one from the list" does not get the resource immediately, but an offer with **a confirmation deadline**:

| Entry state | Transition |
|---|---|
| waiting | → offered (taken as the next one) · → cancelled · → expired (the entry window has passed) |
| offered | → accepted (resource assigned) · → rejected / deadline passed → the next one from the list |
| accepted / cancelled / expired | final states |

- **Cooperation with Availability:** the event "resource released" → the policy "take the next one and **block it for them** for the duration of the
  offer" → acceptance extends the block, rejection/expiry releases it → the next cycle.
- The algorithm underneath: **a priority queue** (a heap) enclosed behind the list's interface.

## Questions
**A — standard decisions:**
- Order: **FIFO or priorities**? Who assigns the priority and can it **change** while waiting?
- **Capacity:** how many people can wait? What when it is exceeded — refusal, a second list, pushing out the lowest priority?
- **Offer:** how much time to confirm? What if they do not confirm — the next one, or back to the list (at the end / to their place)?
- Can one person be on **many lists** at the same time (and what when they accept an offer from one)?

**B — gaps** (examples):
- 2 places released, and the first one wants 3 — wait or jump to a smaller request? · does the one waiting see their
  position? · entry validity (a list for a specific date expires with it) · a limit of offer rejections · a parallel offer to several people
  (whoever confirms first) · audit of the decision "why not me?" · anonymization of entries (GDPR) · notifications (channel, who sends them).

## Mapping steps
1. **Resource and list** — what the list concerns (a date, a course, a product); one list per resource or per group of resources.
2. **Those waiting** — who signs up (a party → Party, a booking); entry data; how many units.
3. **Queue type and priorities** — the source of the priority as **a parameter** from outside; the tie rule.
4. **Capacity** — the limit and the behaviour when it is exceeded.
5. **Offer cycle** — the trigger (an event from Availability), the confirmation deadline, the effects of rejection/expiry.
6. **Cancellations and entry expiry** — removal by identifier, the validity window, a periodic job.
7. **Fairness** — record the ordering rule so that every decision can be reproduced (events: entered, offered,
   accepted, rejected, expired).
8. **Integrations** — Availability (a block for the duration of the offer), Party (who the one waiting is), notifications.

## Decisions to check (R/A/X)
FIFO/priority · the source and variability of the priority · the tie rule · capacity and the behaviour when it is exceeded · the offer deadline ·
the fate after rejection (next / back to the list / removal) · many lists at once · partial matching of the number of units ·
visibility of the position · entry validity · blocking the resource for the duration of the offer.

## Result format
```markdown
# Waitlist model: <area>
## Lists              — | List | Resource | Capacity | Queue type | Tie rule |
## Concept mapping    — | Domain concept | Archetype element | Justification |
## Unmapped concepts
## Priorities         — | Category | Priority | Source (parameter) | Variable over time? |
## Offer cycle        — | State | Event | Next state | Deadline |
## Exceeded capacity / cancellations / expiry
## Integrations       — | Event | From / to archetype | Reaction |
## Decisions (R/A/X)  — | Decision | Source |
## Notes              — assumptions (X), edge cases, variable policy parameters
```

## Patterns and pitfalls
- The order in a query's `ORDER BY` = no priorities, no limit and no decision history; the list is a domain entity.
- **The priority is a parameter**, not the list's logic: "is the customer a regular one?" is computed by the policy layer (or Accounting/Party).
- "May this person sign up at all?" (age, permissions, an account block) — **authorization outside the archetype**; the list guards
  only capacity and order.
- An assignment without an offer with a deadline → the resource goes to someone who no longer wants it; without a block in Availability → a race with a booking
  "from the street".
- Changing the priority while waiting = removing and re-inserting (keeping the entry time, if so decided).
- Fairness is **a business rule** — record it explicitly and test it with examples (ties, cancellations during an offer).

## Quality check
- [ ] every list has a resource, a capacity, a queue type and a tie rule
- [ ] the priority has a source (a parameter) and a change rule
- [ ] the offer cycle has a deadline and the behaviour on rejection/expiry
- [ ] the behaviour when capacity is exceeded and on cancellation defined
- [ ] the cooperation with Availability (who blocks, when it releases) described
- [ ] the mapping table and "Unmapped concepts" present; no material (X)

## Example (shortened)
**Input:** "A language school: a group has 12 places. When the group is full, you can sign up for the reserve list (max 10 people).
Continuing students have priority. After someone leaves the group, the first person on the list gets an SMS."

```markdown
## Lists — | group_reserve | group (12 places in Availability) | 10 | priority | entry time |
## Mapping — leaving the group → "resource released" (Availability) · SMS → offer (notification outside the archetype) ·
   continuing student → priority 1, the others → 0
## Unmapped — the course fee (→ Accounting) · the language level (matching → General assignment?)
## Priorities — "continuing" is computed by the policy layer from the enrolment history (Party) → parameter `priority`
## Offer cycle — confirmation deadline: A "how much time?" — It depends (shorter just before the course starts) → parameter
   `offer_valid_to` computed by the policy; no answer → the next one, the entry removed (X → ask)
## Decisions — capacity 10 (R) · priority for continuing students (R) · overflow = refusal (X → ask)
```
