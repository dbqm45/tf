# TDD with an agent — vertical slices on agreed seams

A supplement to the cycle from SKILL.md for agent work. Vocabulary (module, interface, seam, adapter): eng-module-depth.

## The gate before a plan phase — TDD or not?
1. **Does the code of this phase already exist** (even partially)? Yes → this is not TDD. You do not add tests "after the fact" under
   the TDD label: either an ordinary implementation with a test and deliberate breaking (qa-spec-first-testing), or a
   characterization test before refactoring.
2. **Can you name the first red test in one sentence about an observable result?** ("returns 401 when the user
   has no access to the course", "resets the interval to 1 day for a rating of 0"). No → go back to the analysis, do not guess.

| Good for TDD | Weak for TDD |
|---|---|
| parsers, validators, transformations; rules with an input and an output; an API contract (status, body, authorisation); reducers and state machines; a bugfix (a reproducing test first); a regression guard for a risk | directory scaffolding, configuration of tools, CI and environment variables, documentation, UI cosmetics without assertions, thin glue (a test would copy the code), a spike looking for a contract |

- A mixed phase: TDD for the part with logic, the rest as an ordinary implementation — explicitly in the report.
- Budget: 2–5 tests per phase, chosen for regressions, not a test for a getter.
- You show RED by running **a single test file**; red for the right reason = an assertion or a missing module or
  function that you are about to write — not a syntax error, a wrong import or "No test files found" in the test itself.
- GREEN: other tests failed → you fix the code, not the tests.
- Commit only on a green full suite; a red state is a checkpoint for the human, not a commit boundary.
- One plan can mix modes per phase (environment → TDD of the contract → E2E of the path → recipes in the test strategy),
  with the progress state in one place.

## Before the first test is written
- **Name the seams** (the public interfaces through which you observe the behaviour) and **stop for confirmation**.
  You do not write a test in an unconfirmed seam. You will not test everything — agreeing the seams directs the effort to
  critical paths and complex logic, not to every edge case. Seams are usually set already in the specification
  (qa-spec-first-testing) or in the task brief.
- Names of tests and interfaces — in words from the domain glossary; respect the ADRs of the area.
- When the very shape of the interface is unclear — eng-module-depth first, then the tests.

## The loop
1. **One slice per cycle:** one seam, one test, a minimal implementation. The first cycle is a **tracer bullet** —
   one path from start to end, which proves that the whole connects.
2. Red → green; do not anticipate the next tests, do not add features "just in case".
3. The next test follows from what the previous cycle taught.
4. **Refactoring separately** — after green, as a separate step or commit, usually at review. In practice agents skip
   it in the loop, so write it explicitly into the plan or the review list, instead of assuming that "it will do itself".

## Three anti-patterns
| Anti-pattern | Signal | Prevention |
|---|---|---|
| **a test tied to the implementation** | the test fails after an internal function is renamed, although the behaviour did not change; mocks of your own modules, counting calls, checking through a database query instead of through the interface | test only through the interface; you check a saved object by reading it with a public method |
| **a tautological test** | the expected value computed the same way as in the code (`expect(sum(a, b)).toBe(a + b)`), a snapshot derived the same way | the expected value from the specification, a known literal or an example calculated by hand (`toBe(15)`) |
| **horizontal slicing** | first a batch of tests, then all the code | the tests check imagined behaviour and shape, not what the user needs → vertical slices |

## Mocks only at the system boundary
- You mock: external APIs (payments, e-mail), time, randomness; sometimes the file system and the database (a test database is better).
- You do not mock: your own classes and modules, internal collaborators — anything you have control over.
- **Inject** external dependencies (do not create the client inside a function).
- An SDK-style client of an external API — a separate function per operation (`getUser`, `createOrder`) instead of
  one generic `fetch(endpoint, options)`: the mock returns one shape, without conditions in the test configuration, with types.

## The loop in a larger flow
- Order: interview → specification (here you agree the seams) → tasks → TDD in each task → review.
- **The review checks the seams:** whether the tests were created only in the agreed seams, whether the names describe behaviour, whether there are mocks
  of your own modules. Refactoring is done at review, not in the loop.
- The agent does not see the other tasks: attach the specification (a link) to the task, not just the task description; cut the tasks so that each
  can be closed with one loop.
- An unclear choice of seam → ask the agent to compare 2–3 variants (what each lets you test, what it hides) before
  you confirm.
- Agents without supervision sometimes write code before the test. In the factory the order is enforced by the `tdd_guard` hook: production code
  only after editing a test and a red run. For key slices check in the report whether the red result
  was for the right reason.

## It works well when
The agent names the seams and waits before the first test file; the tests appear one at a time (fails → minimal code → next);
test names describe a user capability ("an order with a valid cart is confirmed"), not the internals
("calls paymentService.process"); renaming internals breaks no test; mocks are only at the boundary.
Slow E2E/browser tests you run at the end (write this in the project's `CLAUDE.md`).
Work without defined behaviour (configuration, glue, simple CRUD) — TDD has little value here; an integration test
of the path is enough.

## Sources
- 10xDevs course, ed. 3 (2026), module 3, lesson 2 (TDD with an agent, the gate before a phase) — training material (accessed 2026-10-09).
- [mattpocock/skills](https://github.com/mattpocock/skills) (MIT), the `tdd` skill (with files on good tests and mocking);
description: [aihero.dev](https://www.aihero.dev/skills-tdd). Described in our own words.
