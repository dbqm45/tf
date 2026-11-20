---
name: eng-testing
description: Use when deciding how to test or writing tests — TDD order (tdd_guard), which cases, mocks vs fakes, tests that break on refactoring or pass at once, test quality.
metadata:
  review: "2027-10-09"
  catalog: "Use for test strategy and writing tests in any language — TDD in this factory (red before production code, enforced by the tdd_guard hook), the gate before a plan phase, seams and vertical slices, BDD and Example Mapping, proportions (pyramid, trophy), test doubles (fake behind your own port, mock only what you don't own, stub for partial failure), test quality (expected value from the requirement, mutation and property-based tests), business-readable tests, acceptance-test layers. Not for the tools of a specific test framework (tool-*) or a tester's work (qa-*)."
  keywords: "jak testować, strategia testów, ile testów pisać, jakie przypadki testować, TDD, kiedy TDD, czy robić TDD, faza w TDD, test najpierw, test przed kodem, czerwony test, test od razu zielony, test przechodzi od razu, test nic nie sprawdza, czemu pisać testy przed kodem, mocki czy prawdziwe serwisy, mock czy fake, dublery testowe, zaślepki, atrapy, testy łamią się przy refaktoryzacji, zmiana nazwy funkcji psuje testy, zmieniamy nazwę wewnętrznej funkcji i sypią się testy, sypie się kilkadziesiąt testów, testy sypią się po zmianie w kodzie, aplikacja działa a testy padają, testy pękają przy każdym refaktorze, testy związane z implementacją, jakość testów, pokrycie a jakość, 90% pokrycia a błędy, testy mutacyjne, testy oparte na właściwościach, skąd wartości oczekiwane, testy niestabilne, testy raz przechodzą raz nie, nikt nie ufa testom, testy czytelne dla biznesu, testy akceptacyjne, BDD, given when then, example mapping, piramida testów, testy integracyjne z bazą, częściowa awaria, agent pisze testy po kodzie, agent napisał wszystkie testy naraz, tdd_guard, warstwy testów akceptacyjnych, scenariusz DSL sterownik, testy akceptacyjne przeżywają refaktoryzację, częściowa awaria, druga z trzech operacji pada, zapis nieatomowy w teście, stub klienta do awarii, test przeszedł bez zmiany kodu, test zielony zanim napisałem kod, po refaktoryzacji pada kilkanaście testów, testy do przepisania po refaktorze, testy przypadków użycia bez bazy, buildery testowe, asercje domenowe, test własnego helpera, test optymistycznej blokady, testy kontraktowe, wstrzyknąć zegar, sleep w testach, nazwy testów, test się nie uruchamia, wartości brzegowe w TDD, rabat w TDD, faza mieszana TDD, szwy testowe, pionowe plastry, horyzontalne cięcie testów, how to test, acceptance test layers, partial failure test, test green without code change, tests break after refactoring,  test strategy, how many tests, which cases to test, when to use TDD, test first, red test, test passes immediately, mocks vs fakes, test doubles, tests break on refactoring, renaming breaks tests, test quality, coverage is not quality, mutation testing, property-based testing, flaky tests, business-readable tests, acceptance tests, example mapping, test pyramid"
---

# Testing — strategy and writing tests

## TDD in this factory
Cycle: **red → green → refactor**. In red, the smallest new test fails *for the right reason*. A bug fix starts with a test that
reproduces the bug. Tests exercise behaviour through the public API, not the implementation.

**For production code the order is mandatory** — the `tdd_guard` hook enforces it:
1. edit the test file;
2. run the tests (`npm test`, `npm test -- <file>`, `pytest <file>`…) — the new test **does not pass**, and for the right reason
   (a missing function, a wrong value — not a typo, a bad import or "No test files found");
3. only then change production code; then the whole suite green.
- A test that is **green at once proves nothing.** Rewrite it so it checks the missing behaviour. Exception: a characterization test
  before refactoring untested code, marked `[characterization]` (qa-spec-first-testing).
- The next behaviour = the next test. `tdd_guard` asks for a new test again after `CLAUDE_TDD_MAX_EDITS` (default 12) production edits
  without one. It tracks the main session and every subagent separately.
- **No cheating:** do not change an expectation to make a test pass; do not hard-code the implementation for the test (returning a
  constant, branching on test data); do not skip tests — weakening (skip, xfail, `@Disabled`, `xit`, fewer assertions) is detected
  (`CLAUDE_TDD_WEAKEN`, warn by default). A test that is wrong: say so in the report and fix it explicitly, with the reason.
- Modes (`CLAUDE_TDD`): `strict` (default, blocks), `ask` (the human decides every block), `off` — a spike or prototype, **the human's
  decision**, never the agent's. Exempt by default: configuration, styles, templates, docs, `.d.ts`, generated files; more via
  `CLAUDE_TDD_EXEMPT`.
- Report: the command, a fragment of the red output, then the green output of the whole suite.
- Before a plan phase decide whether it is TDD at all (the gate), name the seams, work in vertical slices: `references/tdd-with-agent.md`.

## Behaviour and examples (BDD)
- Business rules as Given / When / Then in the domain's language — the same examples as in modelling (ddd-deep-modeling).
- **Example Mapping** before implementation: story → rules → examples per rule → questions. Many open questions = the story is not ready.

## Proportions
- Many fast tests of domain logic; integration tests at the edges (a repository on a real database, an HTTP client, a queue); few E2E.
  Front end: mostly component tests (the trophy shape).
- **A real database** when the rules depend on constraints, cascades, uniqueness or real SQL behaviour.
- **A stub of the client** when you must make one step of a sequence fail (the second of three writes) to test the partial-failure
  branch of a non-atomic operation. Test the contract that exists (e.g. "partial failure → logged, `ok: true`"), not a rollback you wish
  existed; report the missing protection as an open product risk.
- A heavy integration gate may run on demand rather than on every save.

## Test doubles
- **Fake** (a working simple implementation, e.g. an in-memory repository) > **stub** (canned answers) > **mock** (verified interactions).
- Mock only what you **don't own** (a payment provider, a mail service, the clock, randomness), and through **your own port** — an
  interface in your code that the adapter implements. Never mock your own classes or collaborators.
- Assert on results and state, not on interactions; call counting couples the test to the implementation.

## Test quality
- **The expected value comes from the requirement or a worked example, never from running the code** — that cements the bug.
- A red test that agrees with the requirement means **a defect in the code**: report it or fix the code; do not change the expectation.
- Line coverage is not quality. For critical logic measure **mutation testing** (Stryker, PIT, mutmut); for calculations add
  **property-based tests** (fast-check, Hypothesis, jqwik) — e.g. "the split amounts always sum to the total".
- Choosing cases (boundaries, equivalence classes, risk): qa-test-design. Regression suites and flaky-test quarantine: qa-regression.
- Flaky by design: time (inject a clock), order and shared state (isolate, reset), parallelism, network — fix the cause, don't retry.

## Good tests
- The name says the behaviour: `rejects_booking_when_room_is_closed`. One reason to fail. No `sleep` — inject the clock.
- The file name matches the runner's pattern — a wrong suffix means the test silently never runs.
- Test your own test helpers: a custom assertion that compares a value with itself always passes — make it fail once.
- Concurrency: an optimistic-locking test fires N parallel attempts and asserts a consistent final state (one winner, the rest rejected).

## Tests readable for the business
- Builders in domain language, domain assertions whose failure message speaks the domain, a module test configuration that wires the
  **real facade from fakes** (fast use-case tests without a database):
  ```java
  var quote = insurance.quote(driver().aged(19).withLicenceYears(1), car("Fiat 500"));
  assertThat(quote).isRejectedBecause(DRIVER_TOO_YOUNG);
  ```
- Consumer-driven contract tests between services instead of brittle cross-system E2E.
- Characterization tests before refactoring legacy code (qa-spec-first-testing).

## Acceptance-test layers
Scenario → DSL (domain verbs) → driver (translates to calls of the system, no assertions) → system. Scenario and DSL survive a
refactoring; only the driver changes (domain, application or system level). Proving equivalence this way:
eng-behavior-preserving-refactoring. Key logic (money, permissions, domain rules) gets acceptance tests written by someone other than
the code's author — `qa-analyst` in a clean room (qa-spec-first-testing).

## Example
Input: "Add a rule: 10% discount when the cart total exceeds 200 PLN. Use TDD."
Result:
1. From the requirement: "exceeds" → 200.00 gets no discount. Examples: 199.99 → 199.99; 200.00 → 200.00; 200.01 → 180.01 (rounded
   half-up to grosze, agreed with the human); 500.00 → 450.00.
2. First test `no_discount_at_exactly_200` — passes at once (no rule yet means no discount), so it proves nothing about the new rule;
   start instead with `discount_above_200`: `total(cart(200.01)) == 180.01` → `npm test -- cart.test.ts` → red: expected 180.01,
   received 200.01.
3. Minimal code: `if (sum > 200) return round(sum * 0.9)`. Green. Then the boundary test `no_discount_at_exactly_200` as a guard
   and `500.00 → 450.00`; whole suite green. Report: command, red fragment, green suite.
