---
name: eng-testing
description: Use for a test strategy in any language — TDD, BDD, the test pyramid, test doubles, contract, mutation tests.
metadata:
  review: "2027-10-09"
  catalog: "Use when designing a test strategy and writing tests in any language — TDD (red-green-refactor), BDD and Example Mapping, the test pyramid/trophy, test doubles, contract, mutation and characterization tests. Not for the tools of a specific test framework (tool-*) or a tester's work (qa-*)."
  keywords: "jakość testów, pokrycie kodu, czy testy coś sprawdzają, mocki, dublery, testy mutacyjne, TDD, czy robić w TDD, kiedy TDD, faza w TDD, rusztowanie i konfiguracja w TDD, ile testów pisać, które przypadki testować, testy przed kodem, po co najpierw test, test od razu zielony, test nic nie sprawdza, testy psują się po zmianie nazwy, testy przywiązane do implementacji, testy raz przechodzą raz nie, testy trwają za długo, udawane serwisy, mocki czy prawdziwe serwisy, nikt nie ufa testom, kruche testy, testy sypią się przy zmianie kodu, testy łamią się przy refaktoryzacji, testy do nowej funkcji, wszystkie przypadki czy tylko ważne, ile przypadków testowych, zmiana nazwy funkcji psuje testy, testy sprawdzają wewnętrzne funkcje, sypie się wiele testów, aplikacja działa tak samo a testy czerwone, zmieniamy nazwę wewnętrznej funkcji, tests break on rename, tests coupled to implementation, test quality, code coverage, do the tests check anything, mocks, test doubles, mutation tests, should we do TDD, when TDD, a phase in TDD, scaffolding and configuration in TDD, how many tests to write, which cases to test, tests before code, why test first, test green right away, the test checks nothing, tests pass sometimes and fail sometimes, tests take too long, fake services, mocks or real services, nobody trusts the tests, brittle tests, tests fall apart when the code changes, tests break during refactoring, tests for a new feature, all cases or only the important ones, how many test cases, renaming a function breaks tests, tests check internal functions, many tests fail, the application works the same but the tests are red, we are renaming an internal function, using TDD, test first, red green refactor, add a rule with tests, discount rule test"
---

# Testing

## TDD — the cycle
Red → green → refactor; in the red step check that the smallest new test fails **for the right reason**. For a bugfix
first a test that reproduces the bug. Test **behaviour through the public API**, not the implementation.
Agent work: first agreed seams, then vertical slices one test at a time, refactoring as an explicit separate step,
anti-patterns (a test tied to the implementation, a tautological one, horizontal slicing) and **the gate before a phase** (when TDD, and when
an ordinary implementation; a budget of 2–5 tests per phase) — `references/tdd-with-agent.md`.

### TDD in the factory — mandatory for production code
- **Order, not a declaration:**
  1. you edit the test file;
  2. you run the tests — the new test **does not pass** for the right reason (a missing function, a wrong value, not a typo
     in the test);
  3. only now the production code.

  The `tdd_guard` hook blocks editing production code without this sequence, separately in the session and in every subagent.
- **A test green right away** proves nothing: fix it so that it checks the missing behaviour. Exception: a
  characterization test before refactoring code without tests; you mark it `[characterization]` (qa-spec-first-testing).
- **The next behaviour = the next test.** After a dozen or so code changes without a new test the hook requires a test again
  (`CLAUDE_TDD_MAX_EDITS`, default 12).
- **No cheating:**
  - you do not change the expectations in a test so that the code passes;
  - you do not write an implementation "for the test" (returning a constant, a condition on the test data);
  - you do not mark a test as skipped.

  If a test is wrong, you say so in the report and fix it explicitly, with a justification.
- **Key logic** (money, permissions, domain rules): acceptance tests are written by someone other than the author of the code
  (qa-analyst in a clean room). The author of the code gets them as a ready contract.
- **Outside the gate:** configuration, styles, templates, documentation, `.d.ts` types, generated files. A prototype or a spike
  is the human's decision (`CLAUDE_TDD=off`); `CLAUDE_TDD=ask` hands every block over to the human.
- **Report:** the command and a fragment of the red output, then the green output of the whole suite.

## BDD and examples
- Business rules as **Given / When / Then** scenarios in the domain language (the same examples as in modelling — ddd-deep-modeling).
- **Example Mapping** before implementation: story → rules → examples → questions. Too many questions = the story is not ready.

## Test proportions
- The most fast tests of domain logic; integration tests at the edges (a repository with a real database, an HTTP client,
  a queue); few E2E. Front end: a majority of component tests (the "test trophy").
- **A real database**, when a rule depends on constraints, cascades, uniqueness, real SQL — a mock would lie here.
  **A client stub**, when you need to trigger a failure in the middle of a sequence (the second of three operations fails), which a real database
  does not simulate easily — you test a non-atomic write with a stub for the partial-failure branches.
- You test the contract that **exists** (e.g. "partial failure → log + `ok: true`"), not a dreamed-of one (a rollback that does not
  exist); you report the lack of protection as an open product risk. A heavy integration gate can be "on demand".

## Test doubles
- Fake (a simple working implementation, e.g. an in-memory repository) > stub > mock. Mock only what you do not own
  (external systems), and do it through your own port, not an external library directly.

## Test quality and where the expected result comes from
- **The expected value comes from a requirement or an example, never from running the code.** A value copied from the code's
  output cements a bug instead of detecting it. Details, the clean room and the discrepancy protocol: qa-spec-first-testing.
- **A red test that agrees with the requirement is a defect in the code:** you do not change the expected value so that the test passes,
  but report or fix the code.
- **Line coverage is not enough:** the quality of tests of critical logic is measured by **mutation tests**, and calculations are strengthened by
  **property-based tests** (e.g. the sum of a split amount = the amount).
- Techniques for choosing cases: qa-test-design. Regression and flaky tests: qa-regression.

## Special techniques
- **Contract tests** (consumer-driven) between contexts/services instead of brittle E2E across many systems.
- **Characterization tests** before refactoring legacy — they lock in the current behaviour.

## Good tests
Name = behaviour (`rejects_block_when_resource_disabled`), one reason for failure per test, no `sleep` — the clock as
a dependency.

## Tests readable for the business
- **Builders in the domain language** instead of assembling objects by hand: `project("P1").requires(skill("JAVA-MID"), january).earns(10_000)`.
- **Domain assertions**: `assertThat(schedule).hasStage("Project").atLevel(2)` — the error speaks the domain language.
- **A module's test configuration**: the real facade assembled from fakes (an in-memory repository) — fast use case tests without a database.
- **Test your own assertions and builders** — a helper assertion that compares a value with itself always passes
  (check it once on a case that MUST fail).
- The test file naming convention must match the run pattern — a file with a different suffix silently does not run.
- Concurrency: for optimistic locking a test with N parallel attempts and an assertion on a consistent final state.

## Layers of an acceptance test
Scenario → DSL (domain verbs) → driver (translates into system calls) → system. The scenario and the DSL do not know the implementation,
so they survive refactoring; only the driver is replaced (domain / application / system level). The driver has no assertions.
The refactoring procedure with proof of behaviour: eng-behavior-preserving-refactoring.
