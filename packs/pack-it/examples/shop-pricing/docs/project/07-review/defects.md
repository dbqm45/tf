---
artifact: review
phase: review
status: draft
version: 1
author: kasia
created: 2026-09-27
updated: 2026-09-27
inputs: [docs/project/05-plan/test-plan.md]
---
# Defect reports: order line pricing — quantity discount (H1)

## TL;DR
Automating the plan TC-001..TC-014 (src/pricing.spec.ts) found 2 defects in src/pricing.ts: (1) the 5%/10% discount threshold
computed as `quantity > 10` instead of `>= 10` (H1-AC2/AC3 say "from 10 units inclusive") — for qty=10 the code applies no
discount (TC-003, TC-008); (2) no integer validation of the quantity (H1-AC4) — `orderTotal` rejects only qty<1, it lets through
non-integer values such as 2.5 or 9.999999 (TC-012, TC-013). The tests for both groups are left as `it.fails` in the spec, with
the expected (correct) value from the specification — the expectations were not changed to fit the code.

## Handoff
To decide: the fix of `discountRate` (`>=` instead of `>`) and adding the `Number.isInteger(quantity)` validation in
`orderTotal` (with an unambiguous error mechanism — see the open question below). After the fix, change `it.fails` →
`it` in `src/pricing.spec.ts` (TC-003, TC-008, TC-012, TC-013).

## DEFECT-01: the discount threshold computed as `> 10` instead of `>= 10`
- **Affected tests:** TC-003, TC-008
- **Requirement:** H1-AC2 / H1-AC3 — the 5%/10% discount applies "from 10 units inclusive"
- **Expected result (TC-003):** qty=10, price=1999 gr → 18991 gr (5% discount)
- **Actual result:** `discountRate(10)` returns 0 (because `10 > 10` is false) → `orderTotal(1999, 10)` = 19990 gr
- **Expected result (TC-008):** qty=10, price=11 gr → 105 gr
- **Actual result:** no discount → 110 gr
- **Location:** `src/pricing.ts:5` (`if (quantity > 10) return 0.05;`)
- **Hypothesis:** a defect in the code (a classic off-by-one error at the threshold) — the requirement and the sales example in
  `docs/project/05-plan/test-plan.md` (TC-003) clearly point to an inclusive threshold.
- **Recommendation:** change the conditions to `quantity >= 10` (the 5% threshold) and `quantity >= 50` (the 10% threshold, already correct —
  but check the consistency after changing the order of the conditions).

## DEFECT-02: no integer validation of the quantity (H1-AC4)
- **Affected tests:** TC-012, TC-013
- **Requirement:** H1-AC4 — the quantity must be an integer ≥1, otherwise the pricing is rejected
- **Expected result (TC-012):** qty=2.5 → pricing rejected (validation error)
- **Actual result:** `orderTotal(1999, 2.5)` does not throw — only `quantity < 1` is checked
- **Expected result (TC-013):** qty=9.999999 → pricing rejected, NOT treated as qty=10
- **Actual result:** no integer validation; the value goes through `discountRate`/`orderTotal` without an error
- **Location:** `src/pricing.ts:10` (`if (quantity < 1) throw new RangeError(...)`)
- **Hypothesis:** a gap in the implementation against requirement AC4 (incomplete validation) — possibly also an ambiguity in
  the requirements about the error reporting mechanism (see the open question below).
- **Recommendation:** add the condition `!Number.isInteger(quantity)` to the input validation, reported by the same
  mechanism as `quantity < 1` (currently a `RangeError` exception).

## Open question
The test plan (TC-010..TC-013) defines the expected result as "pricing rejected (validation error)", but does not specify
the mechanism (an exception vs a result with an `ok:false` flag). The code currently uses an exception (`RangeError`) — the tests were adapted to
this mechanism (`toThrow()`). If a result with an error flag (Result) is required in the end, that is a separate change of the function's
contract, not just a validation fix — to be confirmed with the owner of the requirements before implementing the fix.
