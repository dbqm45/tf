---
name: qa-spec-first-testing
description: Use when tests must check the requirement, not the implementation — an independent oracle, clean-room roles, failing spec tests, bug examples, mutants.
metadata:
  review: "2027-10-09"
  catalog: "Use when tests must check the requirement, not the implementation: where expected values come from (an independent oracle, never the code), acceptance tests before code, the clean-room split between test designer and automation engineer, what to do when a spec-based test fails, tests derived from a bug report around a threshold, characterization tests before a refactor, mutation and property tests, a manual mutation check of a test written after the code, traceability by criterion id. Not for choosing test techniques and boundary values (qa-test-design), runner syntax (tool-vitest, tool-pytest), formal models of protocols (qa-formal-methods) or exploratory sessions (qa-exploratory-manual)."
  keywords: "test ze specyfikacji pada, zmienić oczekiwaną wartość w teście, poprawić test pod kod, test czy kod, wyrocznia testu, zgłoszony błąd, testy do poprawki błędu, przykład ze zgłoszenia, próg nie działa, dokładnie na progu, jakie przypadki dodać do poprawki, a spec-based test fails, change the expected value in a test, fix the test to match the code, test or code, test oracle, reported bug, tests for a bug fix, example from the report, threshold does not work, exactly at the threshold, which cases to add for a fix, generate unit tests from the code, AI-generated tests, expected values, tests from implementation, oracle problem"
---

# Spec-first testing — the test checks the requirement

A test whose expected value was read off the code is a **mirror test**: it duplicates the implementation, freezes its current
behaviour together with its bugs (an off-by-one at a threshold included) and passes forever. Generating unit tests "from the code
alone" produces exactly that. The expected value has to come from somewhere else.

## 1. The oracle — where expected values come from
Every expected value names its source (a comment, the case id or the test name). Allowed sources:
- acceptance criteria and business rules in `docs/project/03-requirements/`;
- concrete examples given by a domain expert or quoted from a bug report;
- values computed by hand or by a **different method** (a table, a spreadsheet, a simple reference model);
- regulations, standards, API contracts;
- properties and invariants (sum of parts = whole, idempotence, round-trip).

Not allowed: copying the program's output into the assertion, reusing the production formula in the test, asserting the value
a mock was told to return. No source → an open question to the requirement owner (core-project-record), not a guess.

## 2. Clean-room roles
- `*-qa-analyst` designs cases from specs, contracts and existing tests; **never sees the implementation** (a hook blocks reading
  source files for agents with that name).
- `*-qa-automation` turns cases into code; may read production code **only for wiring** (imports, constructors, selectors);
  expected values come only from the cases.
- The same blindness applies when stress-testing requirements: the blind profile in ddd-model-stress-test sees only the business brief.
- For a new feature: acceptance tests first, from the criteria, before the code exists; developer TDD inside (eng-testing).
  **Every new test must be seen failing** — red for the right reason. A test green at birth proves nothing.
- Acceptance tests are protected by repository rules in CI (core-git-workflow, "Pull request" section), not by a sentence in a prompt.

## 3. When a spec-based test fails
1. Re-read the test against the source. Is the test faithful to the spec?
2. **Test is right** → the code is wrong. **Do not change the expected value.** File a defect (qa-exploratory-manual format)
   with the case id and a quote of the source; keep the test red, or mark it as a known defect with a link:
   `test.fails` / `it.fails` (Vitest), `test.fail()` / `test.fixme` (Playwright), `@pytest.mark.xfail(strict=True)`.
3. **Spec ambiguous** (e.g. rounding not stated) → open question to the owner, mark the test pending/skip with the question's id. Do not pick a side.
4. The expected value changes only when a **new source** appears — and the commit message cites it.

## 4. Tests from a reported bug
1. Record the triple **input / expected / actual**, with the report quoted as the source of "expected".
2. Derive points **at, just below and just above** the threshold, plus one counterexample from the other side of the rule.
3. State the general rule last. A single example lets a hard-coded `if (total == 100)` pass.
4. Property tests rarely hit an exact threshold by chance — keep the report's example as an **explicit case**
   (Hypothesis `@example(...)`, fast-check `examples`), next to the property.
5. Optional, for numeric/threshold rules: before tests, the agent writes a short contract (preconditions, postconditions,
   cases the spec leaves unspecified) and the human reads it. It catches gaps early but costs tokens — not the default.

## 5. Existing code without tests
Two kinds of tests, never mixed in one file or one claim:
- **Spec tests** — from requirements; a failure is a defect or a spec gap, never "fix the test".
- **Characterization tests** — record what the code does today, as a safety net for a refactor (eng-behavior-preserving-refactoring).
  Label them with the word `characterization`: `describe('[characterization] invoice totals', …)`, tag `@characterization`.
  They are not proof of correctness and do not count as coverage of a requirement. (The TDD hook accepts a green-at-birth test only with that label.)
- Moving characterization tests to a higher level: keep a **register of assertions** — what the new tests no longer distinguish and
  why that is acceptable. A behaviour "fixed while refactoring" is a hidden defect: report it, do not slip it in.

## 6. Do the tests catch anything?
**Mutation testing** (Stryker, PIT, mutmut) on domain logic; use the score on critical modules instead of line coverage.
- 0% or a suspicious 100% first means the tool is not activating mutants — check the runner configuration before reading results.
- Narrow the scope to risky modules or the current change.
- Each surviving mutant is a decision:
  - a real gap → add an assertion on **behaviour**;
  - an **equivalent** mutant (no observable difference) → skip;
  - a real difference, but the assertion would be brittle or cosmetic (log text, an internal call order) → skip, with a one-line reason.
  Ask: "would a real bug like this hurt a user or the business?" Do not chase 100%. Merge or delete duplicate tests that kill nothing.

**Property-based tests** (fast-check, Hypothesis, jqwik) for calculations and invariants; boundary values come from qa-test-design;
concurrency and protocol rules go to qa-formal-methods.

**Manual mutation check** — for a test written after the code, or without supervision, that was never seen red:
1. Stage (`git add`) or commit your work first, so the break is the only unstaged change.
2. In the working tree only, weaken or invert exactly the behaviour the test protects (`>=` → `>`, drop the discount line).
3. Run that test — it must go red.
4. Restore with `git checkout -- <file>`; `git diff` must be empty.
5. Green on broken code → strengthen the assertion. Report what you broke and which test went red.

## 7. Adding tests to an existing file (runner already set up)
1. List the behaviours from requirements and the stack's conventions — **not from the code**. Unknown expectation → a question.
2. Per behaviour: one behavioural test plus one edge case chosen from risk.
3. Report in a table:

| Test | Regression it would catch | Change that turns it red | Source of the expected value |
|---|---|---|---|

A row with an empty column is marked **uncertain**.

## 8. Mirror-test smells (reject in review)
The same formula as the code · assertions on internal calls instead of results · snapshots nobody reviewed · test named after the
method (`testCalculate`) instead of the rule · no link to a requirement · never seen red · result compared with itself ·
happy path only · "variants" that differ only in setup and assert the same thing.

## 9. Traceability
The test name or tag carries the criterion or case id: `test('US-02/AC-3: a valid discount code lowers the total', …)`,
`TC-014`. Coverage is counted **by requirement**: every criterion AC-n has at least one test, every test points to a criterion.

## Example
Report: "An order of exactly 100.00 does not get free shipping; it should from 100." Existing suite uses Hypothesis.

```python
# Source: BUG-231 "free shipping from 100.00" (quote). input 100.00 / expected 0.00 / actual 9.99
@pytest.mark.parametrize("total, shipping", [
    (Decimal("99.99"), Decimal("9.99")),   # just below
    (Decimal("100.00"), Decimal("0.00")),  # at — the reported case
    (Decimal("100.01"), Decimal("0.00")),  # just above
    (Decimal("10.00"), Decimal("9.99")),   # counterexample far below
])
def test_BUG231_free_shipping_threshold(total, shipping): ...

@given(st.decimals(min_value=100, max_value=10_000, places=2))
@example(Decimal("100.00"))               # explicit — random draws rarely hit it
def test_free_shipping_from_100(total): assert shipping_for(total) == 0
```
Rule stated last: shipping is free for totals ≥ 100.00.

## Sources
- B. Meyer, *Object-Oriented Software Construction*, 2nd ed. (1997) — design by contract: preconditions, postconditions, invariants.
- J. Wąsowski, "Failing Example as the Start of a Spec" (blog, 2026) — a failing example from a report as the seed of a contract
  before tests [unverified: exact date and figures].
- Stryker Mutator docs (stryker-mutator.io, "Mutant states and metrics") and PIT docs (pitest.org) — survived, killed and
  equivalent mutants; check the CLI with `npx stryker run --help` (accessed 2026-10-09).
- Hypothesis docs, `@example` decorator (hypothesis.readthedocs.io); fast-check docs, `examples` parameter (fast-check.dev).
