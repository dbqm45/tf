# TDD with an agent — the gate, seams, slices, anti-patterns


## 1. The gate before a plan phase
Before starting a phase, answer two questions:
1. **Does the code of this phase already exist, even partly?** Yes → this is not TDD. Do ordinary implementation (with a deliberate
   break to see the existing test go red) or characterization tests before refactoring. Never write tests after the fact and label them TDD.
2. **Can the first red test be stated in one sentence about an observable result?** — e.g. "applying an expired coupon returns
   `COUPON_EXPIRED` and leaves the total unchanged", "reserving more items than in stock is rejected and the stock stays 3". No → the
   phase is not understood yet; go back to analysis.

| Good for TDD | Weak for TDD |
|---|---|
| parsers, validators, transformations | scaffolding, directory layout |
| rule logic, calculations, rounding | tool, CI and environment configuration |
| API contract (status, body, authorization) | documentation |
| reducers, state machines | cosmetic UI changes |
| bug fixes, regression guards | thin glue code, spikes |

- **A mixed phase** (e.g. "ESLint config and a CSV price parser"): TDD for the logic part (the parser), the rest ordinary
  (configuration is outside the `tdd_guard` gate anyway). Say in the report which parts went which way.
- Budget **2–5 tests per phase**, chosen for regression value — not every edge case.
- A plan may mix modes per phase — environment → TDD of the contract → an E2E path → recipes — with progress tracked in one place.

## 2. Red and green in practice
- Show RED by running **one test file**. Red must be an assertion failure or a missing symbol — not a syntax error, a bad import or
  "No test files found".
- In GREEN, if other tests fail, fix the code, not those tests.
- **Commit only on a green full suite.** A red state is a checkpoint, not a commit.

## 3. Seams before the first test
- Name the **seams** — the public interfaces where behaviour will be observed (a facade method, an HTTP endpoint, a component's props
  and rendered output) — and **stop for confirmation**. No tests outside the confirmed seams.
- Agree seams that cover the critical paths, not every edge. Use the domain glossary's words and respect the ADRs.
- The interface shape is unclear → design it first (eng-module-depth); ask the agent to compare 2–3 seam variants with their trade-offs.

## 4. The loop: vertical slices
- One cycle = one seam, one test, the minimal code to pass it.
- The **first cycle is a tracer bullet**: a thin end-to-end path that proves the wiring (request → logic → storage → response).
- Do not anticipate later tests; the next test follows what the last one taught.
- **Refactoring is its own explicit step** — put it in the plan or the review list; agents skip it otherwise.

## 5. Anti-patterns
| Anti-pattern | Signal | Instead |
|---|---|---|
| implementation-coupled test | fails on an internal rename; mocks of your own modules; counting calls; asserting through a DB query instead of the interface | test through the seam's interface |
| tautological test | the expected value is computed the same way the code computes it | a literal from the spec or a hand calculation |
| horizontal slicing | all tests first, then all code (e.g. 40 tests, then the implementation) | vertical slices, one test at a time |

## 6. Mocks only at the system boundary
- Mock external APIs, time, randomness, sometimes the file system or database (a test database is usually better).
- Never mock your own classes or collaborators. Inject external dependencies.
- Prefer per-operation client functions (`getCustomer(id)`, `createShipment(order)`) to one generic `request(endpoint, options)`: each
  mock then returns one typed shape and cannot drift.

## 7. From spec to tasks
- Order: interview → spec (with agreed seams) → tasks → TDD per task → review.
- Attach the spec link to every task — the agent working on one task does not see the others.
- Slice tasks so that each one closes with a single loop.
- Run slow E2E tests at the end, not in every loop; note that in the project's `CLAUDE.md`.
- Review checks the seams: tests only at agreed seams, names describe behaviour, no mocks of own modules; refactoring happens at review.
- Agents sometimes write code before the test — `tdd_guard` blocks it; for key slices also check that the red reason was the right one.

## 8. When it works, when it adds little
Works well when the agent names the seams and waits, tests appear one at a time, test names describe what a user can do, an internal
rename breaks nothing, and mocks sit only at the boundary. Adds little for configuration, glue and simple CRUD — an integration test of
the path is enough there.

## Sources
- M. Pocock, `tdd` skill in the `mattpocock/skills` repository (github.com/mattpocock/skills, MIT licence) and his articles on aihero.dev
  — seams, vertical slices, tracer bullets, the mocking boundary [unverified: exact article title and date].
- The `tdd_guard` hook of this factory (`.claude/hooks/tdd_guard.py`) — the enforced order and modes.
