---
name: qa-spec-first-testing
description: Use when tests must check the requirement, not the implementation — an independent oracle, clean-room, ATDD, mutations.
metadata:
  review: "2027-10-09"
  catalog: "Use whenever writing tests — how to make a test check the REQUIREMENT instead of duplicating the implementation (an oracle independent of the code, TDD/ATDD, clean-room, a discrepancy protocol, characterization, mutation and property-based tests). Not for test-case selection techniques (qa-test-design), formal verification (qa-formal-methods) or tool syntax (tool-*)."
  keywords: "test ze specyfikacji pada, zmienić oczekiwaną wartość w teście, poprawić test pod kod, test czy kod, wyrocznia testu, zgłoszony błąd, testy do poprawki błędu, przykład ze zgłoszenia, próg nie działa, dokładnie na progu, jakie przypadki dodać do poprawki, a spec-based test fails, change the expected value in a test, fix the test to match the code, test or code, test oracle, reported bug, tests for a bug fix, example from the report, threshold does not work, exactly at the threshold, which cases to add for a fix"
---

# Tests from the specification, not from the implementation

## The problem
A test written by **reading the existing method** encodes its behavior — along with its bugs. Such a ("mirror") test
always passes and proves nothing: if the method computes a discount from `> 10` instead of `>= 10`, a test generated from the code
will check `11` and cement the bug.

## The rule: an independent oracle
**The expected result of a test comes from outside the production code**, always with a named source:
1. acceptance criteria (Given/When/Then) and business rules from `docs/project/03-requirements/`,
2. examples from the expert (Example Mapping, ddd-deep-modeling) — concrete numbers and dates,
3. values computed **by hand or by a method other than** the code (a table in the test, a spreadsheet, a reference model),
4. regulations, standards, API contracts (OpenAPI, public types),
5. properties and invariants ("the sum of installments = the amount", "never two reservations for the same interval").

**Never:** running the code and copying the result as "expected"; the same formula in the test as in production;
a mock returning what is then asserted.

## Workflows
### A new feature — test first (TDD / ATDD)
1. The tester writes **acceptance tests** (e2e/API) from the acceptance criteria — before the implementation.
2. The developer in a TDD cycle: a unit test **red for the right reason** → minimal code → green → refactor (eng-testing).
3. Every new test **must fail first** — a test that is green right away has proved nothing (check that it executes an assertion at all).

### A reported bug — from an example to a test
1. Write down the example: **input / expected / actual** (with a quote from the report as the source of the expected).
2. From the threshold derive points: at the threshold, just below and just above (99.99 · 100.00 · 100.01) and one counterexample for the rule
   (e.g. a promo code, a refund). A counterexample without a clear "Then" is a question for the business, not a test.
3. The rule in words you write last, from the examples. A single example lets through an implementation that "knows the answer"
   (`if total == 100`).
4. **A property test does not replace the example:** random generation over the full range almost never hits the threshold exactly,
   so the example from the report stays as an explicit case in the property test (e.g. `@example(100.00)` in Hypothesis,
   tool-pytest).
5. For thresholds and numeric rules optionally **a contract before the tests**: preconditions, postconditions and unspecified
   cases written by the agent and read by the human before the tests are created; the tests follow from the contract,
   not from the code that was read. It costs more tokens, so not as a default step (J. Wąsowski, "Failing Example as
   the Start of a Spec", 2026-10-28; the numbers from the studies cited there [unverified]).
6. Acceptance tests protected from change by the agent are enforced by CI, not by a prompt (core-git-workflow, "Pull request").

### Existing code without tests
Two different kinds of tests — never mix them:
- **Tests from the specification** (designed in clean-room, see below). A failure = a defect or a gap in the specification — **not a test fix**.
- **Characterization tests** — only as a safety net before refactoring; they cement the current behavior, not its
  correctness. Mark them (`describe('[characterization] …')`, the `@characterization` tag) and do not count them as proof that it works.
  When rewriting such tests to a higher level keep an **assertion register** (what the new assertion no longer distinguishes and why that is OK),
  and report a change that "while at it" fixes a bug as a hidden defect (eng-behavior-preserving-refactoring).

### Clean-room (separation of roles)
- **The test designer** (`*-qa-analyst`) sees the specification, contracts and existing tests, **does not see the implementation** —
  the `cleanroom_guard.py` hook enforces this. Produces test cases with expected results and their source.
- **The automation engineer** (`*-qa-automation`) may read the code to wire up tests (selectors, API), but **takes expected values
  only from the test cases** — not from the code.

### Clean-room beyond tests
The same rule applies when generating requirements for a model stress test (ddd-model-stress-test): an agent in the `blind` profile
reads only the business brief — requirements written with knowledge of the architecture fit it by construction.

## The discrepancy protocol (a test from the specification does not pass)
1. Check the test against the specification: did you read the requirement and the input data correctly?
2. The test matches the specification → **a defect report** (qa-exploratory-manual: the report format) with the case ID and a quote from the source.
   The test stays red or is marked as a known bug (`test.fails` / `test.fixme` with a link to the report) — **never
   change the expected value to make it "pass"**.
3. The specification is ambiguous → an open question to the product owner (core-project-record); the test marked as pending.
4. Change the expected value only with a new source (an updated criterion) — give the source in the commit.

## Do the tests catch bugs at all?
- **Mutation tests** (Stryker for JS/TS, PIT for Java) on domain logic: the tool introduces small bugs (`>=` → `>`,
  `+` → `-`). Measure the *mutation score* of critical modules, not line coverage: coverage shows code without a test, the mutation
  score — blind tests (an agent rarely leaves code uncovered, more often covered but undefended).
  A result of 0% or a suspicious 100% at the start = first check whether the tool activates mutants at all (tool-vitest).
  Scope: modules from the risk map or the current change, narrowed to a file or a line range — not the whole repo after every commit.
- **Property-based tests** (fast-check, jqwik) for calculations and invariants — the oracle is the property, not the code.
- **Boundary values** from qa-test-design — that is where "off by one" bugs most often hide.
- **Formal methods** (the Z3 solver, TLA+ or Alloy model checking) for concurrency, protocols and rules with a limit —
  the oracle is the tool, not random generation (qa-formal-methods).

### A mutant survived — a decision, not automation
For each one you ask: "would a real bug of this shape hurt the user or the business?"
1. **Yes — a real gap** → add an assertion of the behavior (not of an implementation detail). Typically: `>=` → `>` at a threshold,
   `||` → `&&` in error handling, a removed condition.
2. **An equivalent mutant** (the change does not alter observable behavior) → skip; no test will kill it.
3. **A real change, but the assertion would be brittle** (message wording, a header, cosmetics of the response) → skip knowingly,
   with a one-sentence justification in the report.

You do not chase 100% — killing cosmetic mutants produces mirror tests. Tests that kill no mutant
and duplicate another test (the same assertion, a different setup), merge into one parameterized test or delete.

### Deliberate breaking — does the assertion guard anything at all? (manual mutation)
When the test was written after the code, the agent worked unsupervised, or it guards a risk from the risk map:
1. Add the step's files to the index (`git add <files>`) so that restoring is exact.
2. In the production code invert or weaken exactly the protected behavior (narrow a filter, invert a branch, remove a write) —
   the change only in the working tree.
3. Run that test. It must be **red** (ideally only it) — that is a positive result.
4. Always restore: `git checkout -- <file>`, also when something went wrong; check `git diff` before the commit.
5. Green on broken code = the assertion guards nothing → strengthen the assertion; never weaken the code or skip the step.

In the report: what was broken, which test turned red, that the file was restored.

### Tests for an existing file without a full cycle (the runner is already there)
1. From the requirements and the stack (not from the code) list the file's behaviors that matter to the user and the business — before the tests. If the sources do not
   settle the expected result → questions, not guessing.
2. For each behavior a behavioral test and at least one edge case from the risk (null, empty, a dependency error,
   bad input). No near-identical copies — every test catches a different regression.
3. The report: | Test | What regression it catches | What change in the code would turn it red | The source of the expectation |. A row without
   column 2 or 3 → "uncertain" and a question to the human.

## Signs of a mirror test (reject in review)
the expected value computed with the same formula as in the code · assertions on calls to internal methods instead of on the result ·
the whole result as a snapshot accepted without review · the test name = the method name (`test calculate()`) instead of the behavior ·
no reference to a requirement · a test written after the code that was never red (→ deliberate breaking) ·
`toEqual(await f(x))` — a function's result compared with itself · only happy paths, zero edge cases
from the risk · a series of tests differing only in setup with the same assertion.

## Traceability
The test's name or tag contains the criterion/case ID: an acceptance test — the identifier of the story's scenario
(`US-02/AC-3`), a case from the test plan — its number (`TC-014`). We measure coverage by **requirements** (every criterion has a test),
not by line percentage.

## Sources
- The 10xDevs course, ed. 3 (2026), module 3, lesson 2 (unit tests with an agent, mutation tests) and module 5 (the "deliberate
  breaking" check in unsupervised work) — training material (accessed 2026-10-09).
- Stryker 10.0 `stryker run --help` — narrowing `--mutate` to a file or a line range (checked 2026-10-10).
Described in our own words.
