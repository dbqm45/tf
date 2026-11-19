# Problem classes — recognition in detail

## The volatility test (the most important discriminator)
Can the data checked during the decision be changed at the same moment by **another request** (including the same person in a second tab)?
Yes → atomicity is needed → competition for resources. No → CRUD / a calculation with validation.

## Signals
| Class | Strong signals | Weak (check with the volatility test) | Approach |
|---|---|---|---|
| CRUD | descriptive fields; a write does not change what others can do; nothing in the system's state blocks the operation | "only the admin edits" | simply: a data layer, validation; no domain layers |
| Transformation | a deterministic result from the input; "calculate, price"; we do not store decisions affecting others | "many rules" | pure functions, policies, VO; ddd-algorithm-recognition |
| Presentation | read-only; the view combines data from many places; a calendar, a report, a dashboard | "a screen with editing" (that is usually several classes) | a projection/read model, BFF, a materialized view, a cache refreshed by events |
| Integration | "notify", "send to", "depends on system X"; partial failures; order matters | "synchronizes" | Published Language, ACL, saga/choreography, outbox (be-messaging-outbox) |
| Competition for resources | "cannot happen twice", limits, reservations, locks, state-dependent operations | "only one owner" | an aggregate with optimistic locking; no transactions across many aggregates; the Availability archetype |

## Signals from UI mock-ups
One screen is usually several classes. Look at the **buttons and states**, not at the fields: descriptive fields → CRUD; a button that changes what others
can do (reserve, approve, assign) → competition for resources; greyed-out actions dependent on the state → domain rules
(`canX()` computed by the domain, not by the UI); a summary/calendar → presentation.

## Pitfalls
- **Hidden CRUD:** descriptive fields and a status on one form — separate them: editing the description (CRUD) ↔ changing the state (domain). The domain
  exposes `canEdit()`, and editing the description can send a "X changed" signal to the domain, if it cares.
- **A limit enforced elsewhere** (an external system, a bank) — do not model it with an aggregate on your side.
- **Calculating a limit is a transformation, enforcing a limit is competition for resources** — separate them.
- Keep presentation data (descriptions, photos) outside the competition-for-resources aggregate.
- **A calendar is a projection**, not an aggregate. Tags and categories are usually labels, not entities.
- The projection test: "if we delete it and rebuild it from other data, do we lose anything?" No → presentation.
- An integration failure state named by the business ("payment rejected") is a domain event, not error handling.

## Deciding questions (in order)
1. Does the operation change what others can do? 2. The volatility test. 3. For CRUD — Behaving/Becoming (does the status hide a life cycle?).
4. For presentation — where is the source of truth? 5. For competition — what is the resource, what invariant, what lock granularity?
6. For integration — what if the other side does not respond; does the order matter?

## Classification result
The class + **confidence** (high: ≥ 3 consistent strong signals; medium: 1–2 confirmed by answers; low: needs further questions) +
**the deduction path** (a table: question → answer or "inferred" → conclusion) + quotes + "what NOT to do".
For a complex area: a **component → class** table (source of truth, read model, integration boundary, shared aggregate).
After the class "competition for resources", the next step: the design of the consistency boundary (ddd-tactical-design).
