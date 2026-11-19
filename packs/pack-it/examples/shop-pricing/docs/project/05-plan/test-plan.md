---
artifact: test-plan
phase: plan
status: draft
version: 1
author: kasia
created: 2026-09-27
updated: 2026-09-27
inputs: [docs/project/03-requirements/requirements.md]
---
# Test plan: order line pricing — quantity discount (H1)

## TL;DR
14 test cases (clean-room, without looking at src/pricing.ts) covering H1-AC1..AC5: equivalence classes and
boundary values of the quantity (0, 1, 9, 10, 11, 49, 50, 51, non-integer, negative values), rounding .5 grosz up
with a 5% and a 10% discount (computed by hand), and the sales example (10 units × 1999 gr → 18991 gr). The highest risk:
an off-by-one error at the 10/50 thresholds and wrong rounding of half grosze — both classes covered by several cases.
3 open questions on the error mechanism (AC4) and the allowed unit price values — marked with proposals,
they do not block the automation. Test level: unit (pure calculation logic); good candidates for property-based
tests (fast-check) for the properties "a discount never increases the price", "the result is always ≥ 0" and mutation tests (Stryker) on
the threshold boundaries.

## Scope and risks
| Area / requirement | Impact | Likelihood | Risk | Techniques | Level |
|---|---|---|---|---|---|
| Thresholds of 10 and 50 units (AC2, AC3) | High (a wrong amount on the invoice) | Medium (a classic off-by-one error) | High | boundary values | unit |
| Rounding .5 gr (AC5) | High (a grosz drift at scale) | Medium (depends on the round implementation) | High | manual calculation + boundary values | unit |
| Quantity validation (AC4) | Medium (wrong input data) | High (many input sources) | High | equivalence classes | unit |
| Discounts do not add up (AC3) | Medium | Low | Medium | decision table (2 thresholds) | unit |

## Test cases
The expected result comes from the source — never from the code (qa-spec-first-testing).

| ID | Requirement | Technique | Preconditions | Steps / input | Expected result | Source of the result | Level | Auto/manual | Priority |
|---|---|---|---|---|---|---|---|---|---|
| TC-001 | H1-AC1 | boundary value (minimum valid) | — | qty=1, price=1999 gr | 1999 gr | AC1: below 10 units no discount; value = 1×1999 | unit | auto | H |
| TC-002 | H1-AC1 | boundary value (just below the 10 threshold) | — | qty=9, price=1999 gr | 17991 gr | AC1 + calculation: 9×1999=17991, no discount | unit | auto | H |
| TC-003 | H1-AC2, H1-AC5 | boundary value (the 10 threshold) + sales example | — | qty=10, price=1999 gr | 18991 gr | Example from the sales department in requirements.md: 10×19.99 PLN − 5% = 189.905 PLN → 189.91 PLN = 18991 gr | unit | auto | H |
| TC-004 | H1-AC2 | boundary value (just above the 10 threshold) | — | qty=11, price=1999 gr | 20890 gr | Calculation: 11×1999=21989; 21989×0.95=20889.55 → rounded to 20890 gr | unit | auto | H |
| TC-005 | H1-AC2 | boundary value (just below the 50 threshold) | — | qty=49, price=1999 gr | 93053 gr | Calculation: 49×1999=97951; 97951×0.95=93053.45 → rounded to 93053 gr (the discount is still 5%, not 10%) | unit | auto | H |
| TC-006 | H1-AC3 | boundary value (the 50 threshold) | — | qty=50, price=1999 gr | 89955 gr | Calculation: 50×1999=99950; 99950×0.90=89955 (exact, no rounding) | unit | auto | H |
| TC-007 | H1-AC3 | boundary value (just above the 50 threshold) | — | qty=51, price=1999 gr | 91754 gr | Calculation: 51×1999=101949; 101949×0.90=91754.1 → rounded to 91754 gr | unit | auto | H |
| TC-008 | H1-AC5 | half-grosz calculation (5% discount) | — | qty=10, price=11 gr | 105 gr | Calculation: value=110 gr; 110×0.95=104.5 gr → rounding up (AC5: "half up") = 105 gr | unit | auto | H |
| TC-009 | H1-AC5 | half-grosz calculation (10% discount) | — | qty=51, price=15 gr | 689 gr | Calculation: value=765 gr; 765×0.90=688.5 gr → rounding up = 689 gr | unit | auto | H |
| TC-010 | H1-AC4 | equivalence class (invalid: zero) | — | qty=0, price=1999 gr | Pricing rejected (validation error) | AC4: "the quantity must be an integer ≥ 1; otherwise the pricing is rejected" | unit | auto | H |
| TC-011 | H1-AC4 | equivalence class (invalid: negative) | — | qty=-1, price=1999 gr | Pricing rejected (validation error) | AC4 as above — a negative value is not ≥ 1 | unit | auto | H |
| TC-012 | H1-AC4 | equivalence class (invalid: non-integer) | — | qty=2.5, price=1999 gr | Pricing rejected (validation error) | AC4: "an integer" — 2.5 is not an integer | unit | auto | H |
| TC-013 | H1-AC4 | error guessing (a large non-integer close to the threshold) | — | qty=9.999999, price=1999 gr | Pricing rejected (validation error), not treated as qty=10 | AC4 — integer validation takes precedence over the quantity threshold | unit | auto | M |
| TC-014 | H1-AC3 | decision table (thresholds do not add up) | — | qty=100, price=1999 gr | 179910 gr | Calculation: 100×1999=199900; discounts do not add up (confirmed by sales 2026-09-21) → only 10%: 199900×0.90=179910 | unit | auto | M |

## Exploratory sessions and UAT
Not applicable — pure calculation logic without a UI; no manual sessions. If the automation reveals a discrepancy
in the error mechanism (see Open questions), a short session with the product owner is recommended, not an exploratory session.

## Entry and exit criteria
- Entry: `docs/project/03-requirements/requirements.md` in the version containing H1-AC1..AC5 and the answer to the question about adding up discounts (already ticked).
- Exit: all cases TC-001..TC-014 implemented in Vitest and green (or red with a reported defect per the discrepancy protocol of qa-spec-first-testing — never with a substituted expected value); a recommended addition of property-based tests (fast-check) for the invariants "result ≥ 0" and "result ≤ base value"; a mutation score (Stryker) for the pricing module ≥ 80% as a quality goal (to be confirmed with the team).

## Open questions
- [ ] TC-010/011/012 assume **[proposal]**: an invalid quantity causes the pricing to be rejected (an error/exception or a result with an error flag — the technical mechanism to be set by the automation engineer per the function's contract, it does not affect the business expectation "no valid amount"). Should zero and a negative value return the same kind of error, or different messages? → domain analyst / product owner.
- [ ] Can the unit price be 0 gr (a promotional/free product) or negative (a correction)? The requirements do not specify this — **[proposal]**: the unit price is an integer ≥ 0 gr; negative values rejected like in AC4. → sales department.
- [ ] Must the unit price be a whole number of grosze, or are fractions of a grosz allowed on input (e.g. from currency conversions), rounded before pricing? → domain analyst.

## Handoff
- **For:** kasia (for automation)
- **Task:** automate the tests per the plan in Vitest
- **Read:** the whole cases table
