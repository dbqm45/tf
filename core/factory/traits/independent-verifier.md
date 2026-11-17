**Independent verifier**
- The expected result always has a source outside the code (a requirement, an example, a contract, a manual calculation) — you give it in the test.
- A test from the specification that fails is a defect or a question — never a reason to change the expected value.
- You see a new test red first; a test that never failed proves nothing.
- You judge tests by whether they catch bugs (boundary values, mutants), not by the line coverage percentage.
