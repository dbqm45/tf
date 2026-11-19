# Examples — choosing the stack

## 1. The backend of a new application: a weighted matrix
**Situation.** "We are building an application for reporting and handling faults in 300 shops. Team: 4 people, they write
TypeScript every day, the frontend is already in Angular. The data must stay in the EU. Which backend?"

**How.**
1. **Drivers** from the requirements, with weights 1–5: QA-1 assigning a ticket without double assignment (5), QA-2 a new fault
   category in 1 module (4), constraint: a team of 4 and a start in 3 months (5).
2. **Mandatory filters**: hosting in the EU, a licence allowing commercial use, support within the project's horizon,
   active patches — an option that drops out gets no points.
3. **Candidates**: 2–3, including the "boring" one — what the team knows.
4. I delegate **facts** (versions, end-of-support dates, licences, compatibility with the frontend's TypeScript version) to `researcher`; they go into
   the matrix only with a source and a check date, never from memory.
5. **Matrix** by the skill's criteria; the result = the sum (a score of 1–5 × the weight).
6. **Conclusions from the domain**: ticket assignment is competition for a resource → a database with strong consistency and constraints (PostgreSQL).

**Result** (a fragment of `04-architecture/stack-decision.md`, status `proposed`):

| Criterion (weight) | A: TypeScript + Node.js ("boring") | B: Java + Spring | C: Go |
|---|---|---|---|
| fit to the drivers (5) | 4 | 5 | 4 |
| team skills (5) | 5 | 2 | 2 |
| ecosystem maturity (3) | 4 | 5 | 4 |
| operating cost and complexity (3) | 4 | 3 | 4 |
| friendliness for AI agents (4) | 5 (`lang-typescript`, types shared with the frontend) | 4 (`lang-java`) | 2 (no `lang-go` skill) |
| lock-in and exit cost (2) | 4 | 4 | 4 |
| security (3) | 3 | 4 | 4 |
| **Total** | **106** | 95 | 82 |

Decision: A + PostgreSQL, style: a modular monolith. Implementing personas: `stack: [lang-typescript, fw-angular, be-database]`.
Risk: the npm dependency chain → ops-supply-chain-security (lockfile, a cooldown for new versions). ADR-003, a row in decisions.md.

## 2. An old system: keep / improve / replace
**Situation.** "We have a 10-year-old wholesale order system. The team wants to rewrite everything from scratch on a new framework."

**How.**
1. An existing project → first `python3 .claude/hooks/detect_stack.py`; a recommendation per area, not a new stack.
2. For every area: does it block an (H,H) scenario? how much does the migration cost?
3. I plan the replacement with the strangler fig pattern, along context boundaries — new code next to the old, traffic switched piece by piece.
4. I reject the anti-pattern: a rewrite "because the framework is old", unrelated to the drivers.

**Result**:

| Area | Decision | Justification (driver) | Migration cost |
|---|---|---|---|
| relational database | **keep** | meets QA-2 (consistency of stock levels) | 0 |
| order backend | **improve** | characterization tests + extracting modules; no scenario that cannot be met | 6 weeks |
| pricing module | **replace** (strangler fig) | QA-4: changing a discount rule takes 3 weeks today | 3 months, context by context |
| customer panel frontend | **replace** | a framework without security patches — it drops out on a mandatory filter | 4 months |

A full rewrite: rejected — the cost of the whole without a gain in the drivers and without value for the user until the last day of the migration.

## 3. An algorithmic core: a solver and a spike with an abandonment criterion
**Situation.** "We plan routes for 25 service technicians a day with customers' time windows. Shall we write our own algorithm?"

**How.**
1. `02-domain/algorithms.md` (ddd-algorithm-recognition) recognized a routing problem with time windows — NP-hard.
2. The skill's rule: a solver or an optimization library **behind a domain interface**, not your own algorithm.
3. `researcher` checks the specific libraries, licences and versions — 2 candidates with sources go into the decision.
4. I turn the uncertainty (computation time at real scale) into a time-boxed spike, with an **abandonment criterion**.

**Result** (a "Risks and spikes" entry in stack-decision.md):
```markdown
### SPIKE-02: the technicians' route solver
Question: does candidate X build a plan for 25 technicians and 180 visits in < 60 s while respecting the time windows?
Time: 5 working days, 1 person.
Data: an anonymized day from March (180 visits), the dispatcher's manual plan as the reference point.
Success: < 60 s and total driving time ≤ the manual plan.
Abandonment criterion: > 60 s or a violated time window → candidate Y; both drop out → the manual plan + suggestions.
Domain interface (independent of the solver): RoutePlanning.plan(day, technicians, visits) -> DayPlan
```
