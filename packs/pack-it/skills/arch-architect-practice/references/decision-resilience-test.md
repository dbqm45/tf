# The decision resilience test

Why: language models (and people) lean towards confirming what has already been said. The question "does X
fit Y?" almost always gets "yes". The test forces a search for reasons why the decision will fail —
before it is recorded in an ADR or `stack-decision.md`.

## When
- before recording an architectural decision or a stack/platform choice (arch-tech-selection, step 8);
- when everyone (people and the model) agrees from the first minute;
- when a recommendation came from source research (core-source-research) — before it is handed over.

## Three lenses
| Lens | The command to yourself | A good result | A weak result |
|---|---|---|---|
| devil's advocate | "Give 3–5 reasons why X is a bad choice for this project" | "a limit of 100 connections on the basic plan with 3 instances and a pool of 50" | "it may be expensive" |
| pre-mortem | "6 months have passed, the decision turned out a failure. What went wrong?" | a narrative with a concrete chain: assumption → event → consequence | a list of generalities |
| unknown unknowns | "Which classes of risk did the assessment not cover?" | compliance, backups, exit from the provider, beta, dependence on another team — each with a control question | "something can always happen" |

## Result and record
For every risk: **I accept** / **a known limitation** (the risk register) / **I change the choice**. A table in the ADR or
`stack-decision.md`:

| Risk | Source (lens / research) | Likelihood | Impact | Action |
|---|---|---|---|---|
| no database backup on the basic plan | pre-mortem | medium | high | a nightly backup to storage, a restore test |

## Additions without a procedure
- **Three alternatives in a table** (implementation cost, maintenance cost, learning curve, the key limitation) instead of
  assessing one option in a vacuum.
- **Role rotation:** look at the decision through the eyes of the frontend, security, operations, costs. When one role reacts
  badly, give a real alternative, not just a reservation.
- A sign that the test has become a ritual: in recent decisions nothing was changed or recorded as a limitation.

## Example
**Decision:** a managed PostgreSQL at the application platform provider. **Devil's advocate:** a connection limit on the starter
plan, no read replicas, exit requires a dump and downtime. **Pre-mortem:** after a marketing campaign the connection pool
is exhausted, reporting queries block writes, a migration to another database under pressure. **Unknown
unknowns:** the data region of the backups, the rules for deleting data after cancellation, the beta status of
database branching. **Result:** the choice stays; two known limitations (the connection pool → a pooler from day one;
reports → a separate read model later), one action (check the backup region before the start).
