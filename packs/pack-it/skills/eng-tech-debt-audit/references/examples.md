# Technical debt audit examples

## 1. A module audit with priorities and quick wins
**Situation:** "Do a debt audit of `apps/shop-api` (NestJS, about 18 thousand lines). We have a clean-up sprint and want
to know where to start".

**How:**
1. **Orientation:** README, `package.json`, ADRs, `git log --since=6.months --stat`; the 20 largest and the 20 most frequently
   changed files — the intersection: `order.service.ts`, `invoice.ts`. The architecture model in 2 paragraphs;
   the README describes a queue that does not exist in the code → a finding (documentation).
2. The plan (scope, modules, tools: `madge --circular`, `knip`, `tsc --noEmit`, `npm audit` — only those the project
   has) shown to the human before the assessment.
3. **Assessment in nine dimensions**; a dimension without findings = "nothing significant".
4. **Priority** = weight (4/3/2/1) × changes in 6 months ÷ effort (S=1, M=2, L=4).
5. Report `docs/project/07-review/2026-10-04-tech-debt.md`.

**Result** (a fragment of the table, sorted by priority):

| ID | Dimension | file:line | Weight | Effort | Changes | Priority | Description | Proposal |
|---|---|---|---|---|---|---|---|---|
| D2 | tests | `src/billing/invoice.ts:88` | high | M | 25 | 3×25÷2 = **37.5** | VAT calculation without tests, changed every week | characterization tests, then edge cases |
| D1 | architecture decay | `src/orders/order.service.ts:1` | high | L | 38 | 3×38÷4 = **28.5** | 1240 lines, 4 responsibilities | extract pricing and shipping into separate services |
| D3 | errors and observability | `src/payments/webhook.ts:42` | critical | S | 6 | 4×6÷1 = **24** | `catch {}` swallows a payment write error | log it and return 500, so that the provider retries |
| D4 | types and contracts | `src/api/client.ts:17` | medium | S | 12 | 2×12÷1 = **24** | the API response is cast `as any` | schema validation at the boundary |
| D5 | dependencies | `package.json:31` | low | S | 3 | 1×3÷1 = **3** | unused package `moment` (`knip`) | remove it |

**Quick wins** (S with a weight of at least medium): D3, D4.
**Looks bad, but is fine:** `src/shared/retry.ts` and `src/workers/retry.ts` are almost identical — deliberately,
the workers are deployed separately and must not depend on `shared` (ADR-007). Do not merge them.
**Questions for the team:** is the queue from the README planned or abandoned?

## 2. A repeat audit and `debt:` markers
**Situation:** "A quarter has passed since the `shop-api` audit. What has changed?"

**How:**
1. The same procedure, then a comparison with the report `2026-10-04-tech-debt.md`.
2. Every finding gets the status ROZWIĄZANE (resolved), NOWE (new) or ZMIENIONE (changed).
3. The collected markers `debt: <limitation>, <when to come back>`; a marker without a return condition is a separate finding.

**Result:**

| ID | Status | file:line | Change |
|---|---|---|---|
| D3 | ROZWIĄZANE | `src/payments/webhook.ts:42` | error logged, response 500 |
| D1 | ZMIENIONE | `src/orders/order.service.ts:1` | 1240 → 820 lines, weight high → medium |
| D6 | NOWE | `src/catalog/search.ts:15` | `// debt: no pagination` without a return condition — add "when the catalogue > 1000 items" |
| D7 | NOWE | `src/catalog/import.ts:60` | `// debt: synchronous import, come back when the import > 5 MB` — a correct marker, it goes into the table with a priority |
