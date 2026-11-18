# Example: tests from requirements (persona Kasia)

Input: the accepted requirements `docs/project/03-requirements/requirements.md` and the code `src/pricing.ts` with **two deliberate
bugs** (the threshold `> 10` instead of "from 10 units inclusive", no validation of a non-integer quantity) and a "mirror" test
that passed despite the bugs.

Command: `claude --agent kasia -p "Prepare tests for the order pricing (src/pricing.ts) according to the requirements in docs/project."`
(without any hint about the bugs).

What the agents did (Sonnet, cost $0.95, ~6 min):
1. `kasia-qa-analyst` (clean-room, no access to the code) → `docs/project/05-plan/test-plan.md`: 14 cases with
   boundary values and the expected result computed by hand from the requirements.
2. `kasia-qa-automation` → `src/pricing.spec.ts` (Vitest + fast-check): 12 green, 4 `it.fails` documenting the defects.
3. `docs/project/07-review/defects.md` — both bugs found and reported; **the code and the expected values untouched**.

Run: `npm i && npm test` (Vitest 5, Node ≥ 22.12).
