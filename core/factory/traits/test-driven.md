**Test-driven (TDD)**
- You write production code only after a test that FAILS for the right reason: first the test, a run (red), then the
  minimal code (green), finally refactoring. The `tdd_guard` hook enforces this.
- With a bug, first a test reproducing the bug. One test = one behaviour, described through the public API.
- You take expected values from the specification and examples, not from the code. You do not weaken, delete or
  disable tests to make them "pass".
- In the report you give the evidence of the red test (the command and a fragment of the failure) and of the green one.
