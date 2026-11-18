---
artifact: requirements
phase: requirements
status: accepted
version: 1
author: ewa
created: 2026-09-20
updated: 2026-09-22
inputs: []
---
# Requirements: order pricing

## TL;DR
Quantity discount when pricing an order line: thresholds of 10 and 50 units, amounts in grosze (gr, 1/100 PLN).

## H1 Quantity discount
As a wholesale customer I want a discount on a larger order, so that buying more pays off for me.

- **H1-AC1:** below 10 units — no discount.
- **H1-AC2:** from 10 units inclusive — a 5% discount on the line value.
- **H1-AC3:** from 50 units inclusive — a 10% discount (discounts do not add up).
- **H1-AC4:** the quantity must be an integer ≥ 1; otherwise the pricing is rejected (an error).
- **H1-AC5:** amounts in grosze; the result rounded to a whole grosz (half up).

Example from the sales department: 10 units × 19.99 PLN = 189.91 PLN (199.90 PLN − 5% = 189.905 → 189.91).

## Open questions
- [x] Do discounts add up? → No (sales, 2026-09-21).

## Handoff
- **For:** kasia
- **Task:** a test plan and automated tests for the pricing
- **Read:** H1
