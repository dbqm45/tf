# The Quantity / Money archetype — mapper (quantities, units, amounts, currencies)

> **Contents:** Fit test · Model (the essence) · Questions · Mapping steps · Decisions to check (R/A/X) · Result format · Patterns and pitfalls · Quality check · Example (shortened)

It turns requirements in which **numbers with a unit or a currency** appear — 3 kg, 8.5 h, 120 PLN, 2 pcs — into value
objects carrying the number together with its meaning. When the unit or the currency lives in a separate field (or only in the developer's head),
errors appear: kilograms added to litres, zlotys to euros, rounding on floating-point numbers, formatting
duplicated in many places. The effect: incorrect arithmetic **does not compile or throws an error**, and rounding and conversions
are explicit policies. The common protocol (questions, "It depends", the R/A/X check, recording): `SKILL.md` → "Mapper — the common protocol".

## Fit test
**The core question:** *does this number make sense without a unit or a currency?* No → Quantity/Money. Yes (a counter, a number, a percentage
without a reference, a rating) → an ordinary number.

| Signal in the requirements | Fits? |
|---|---|
| amounts, prices, balances, instalments, cost splitting | ✅ Money |
| kg, l, m², h, pcs — especially different in different items | ✅ Quantity |
| several currencies, exchange rates, currency conversion | ✅ Money + an exchange rate policy |
| "we round to the grosz / to 5 groszy / down" | ✅ a rounding policy |
| "split 100 PLN into 3 instalments" | ✅ splitting without losing groszy |
| an order number, a number of views, a rating 1–5 | ❌ an ordinary number / identifier |
| "where does this balance come from?", the history of value changes | ❌ → Accounting (uses Money) |
| "how much does it cost for this customer?" | ❌ → Pricing (returns Money) |
| percentage, VAT rate | ⚠️ borderline |

**Borderline cases:**
- *A percentage / rate* — is it a coefficient multiplied by Quantity/Money? → a separate value object `Rate` (no unit,
  with its own precision), not Money. A standalone reporting indicator → an ordinary number.
- *Time* — is it an **amount** of time (8.5 h to bill)? → Quantity. A moment or an interval in a calendar → date/time types (Availability).
- *Loyalty points* — Quantity with the unit `pts`; their history and balances → Accounting.

## Model (the essence)
- **Unit** — a value object: a symbol and a name (pcs, kg, l, m, m², m³, h, min), **a dimension** (mass, volume, length, time,
  items). The set of units is open — you can add your own (a pallet, a carton).
- **Quantity** — a decimal value + a unit. Addition and subtraction **only for the same unit** (otherwise an error);
  multiplication/division by a scalar; comparisons only in the same unit.
- **Conversion factor** — a separate, explicit policy (a conversion table), not hidden magic. Constant within a dimension (1 kg = 1000 g) vs
  dependent on the product (1 carton = 12 pcs, 1 l of milk ≈ 1.03 kg) — the latter belong to Product, not to Unit.
- **Money** — a specialized quantity: an amount + **a currency** (an ISO 4217 code and the number of places of the smallest unit: PLN 2, JPY 0,
  KWD 3). Operations: add, subtract, negate, absolute value, comparisons, min/max, multiply by a scalar, **division with a remainder**
  and **proportional allocation** without losing groszy, a zero and sign check.
- **Exchange rate** — a currency pair, a value, **the date/moment of validity**, a source and a kind (buy/sell/mid, e.g. the NBP table).
  Currency conversion = the operation `Money × ExchangeRate → Money`, always with the recorded rate.
- **Rounding policy** — a mode (HALF_UP, HALF_EVEN, down, to 5 groszy), a precision and **a moment** (per item vs per document),
  in one place, explicitly.
- Arithmetic always on exact types (decimal / an integer in the smallest unit); never float.
- **Where it appears:** the product's preferred unit and the quantity in a batch (Product), a price list returns Money (Pricing), account balances
  (Accounting), a service consumes hours.

## Questions
**A — standard decisions:**
- In what unit does the business think about this number? Can the unit differ between items?
- Do we convert units/currencies? Who sets the exchange rate/conversion factor and for what moment?
- What are the rounding rules and who defines them (the law, accounting, the agreement)?
- How do we split an amount into parts (instalments, cost splitting) so that the total matches?

**B — gaps** (examples): negative amounts allowed (corrections, refunds)? · intermediate precision higher than the final one (unit prices
with 4 places)? · who gets the "remainder" on a split (the first/last instalment, the largest part)? · amounts in many currencies at once
(a wallet, a reporting total)? · the display format per language/country (outside the model)? · VAT computed per item or on the total?

## Mapping steps
1. **An inventory of numbers** — every number from the requirements: does it have a unit/currency? If so → Quantity/Money; if not → justify it.
2. **Units** — a list of units with a dimension; a canonical unit for storage per dimension.
3. **Conversion factors** — constant (within a dimension) vs product-dependent (→ Product); direction and precision.
4. **Currencies** — the list, decimal places, the base/reporting currency.
5. **Exchange rates** — the source, the kind, the moment of validity (the transaction / invoice / payment date), recording the rate on the operation.
6. **Rounding** — for each place of computation: mode, precision, moment; who sets it.
7. **Splitting amounts** — the algorithm (equal with a remainder / proportional by weights / the largest remainder method) and who gets the remainder.

## Decisions to check (R/A/X)
the canonical unit per dimension · conversion factors (constant vs product) · currencies and their precision · the source, kind and date of the exchange rate ·
the mode, precision and moment of rounding · who gets the remainder of a split · whether negative amounts are allowed · intermediate precision ·
handling many currencies in one total.

## Result format
```markdown
# Quantity/Money model: <area>
## Concept mapping    — | Domain concept | Archetype element | Justification |
## Unmapped concepts
## Units              — | Unit | Dimension | Canonical? | Notes |
## Conversion factors — | From | To | Factor | Constant/product | Precision |
## Currencies and rates — | Currency | Places | Rate source | Kind | Moment of validity |
## Rounding           — | Place of computation | Mode | Precision | Moment | Who sets it |
## Splitting amounts  — | Operation | Algorithm | Remainder goes to |
## Decisions (R/A/X)  — | Decision | Source |
## Notes              — assumptions (X), edge cases, variable policy parameters
```

## Patterns and pitfalls
- `double` for money: 0.1 + 0.2 ≠ 0.3. Decimal or an integer in groszy.
- An amount without a currency in the field next to it (`amount`, `currency`) — someone will eventually add PLN to EUR.
- 100 PLN / 3 = 33.33 × 3 = 99.99 — the split must distribute the remainder (33.34 + 33.33 + 33.33).
- The "current" exchange rate instead of the rate from the event date — reports cannot be reproduced.
- Rounding scattered across the code → different totals on the invoice and in the ledger.
- Converting kg ↔ l requires the density — that is product knowledge, not unit knowledge.
- **Outside the archetype:** formatting and localization ("1 234,56 zł" in the Polish format) — the presentation layer; who may set an exchange rate manually —
  authorization.
- **Variable policies as parameters:** a rounding mode depending on the country or the agreement, the exchange rate source per counterparty → the operation
  gets a ready `rounding_policy` / `exchange_rate`.

## Quality check
- [ ] no amount or quantity is a "bare" number; no float
- [ ] operations on different units/currencies are forbidden or go through an explicit conversion factor/exchange rate
- [ ] every exchange rate has a source, a kind and a moment of validity
- [ ] every place of rounding has a mode, a precision and a moment
- [ ] every split of an amount sums to the whole
- [ ] the mapping table and "Unmapped concepts" present; no material (X)

## Example (shortened)
**Input:** "A wholesaler sells coffee per kg and in 250 g packs, to customers from PL and DE (PLN, EUR). An invoice in EUR is converted
to PLN for the ledger. The customer can split the payment into 3 instalments."

```markdown
## Units
| g | mass | yes | storage in grams |
| kg | mass | no | 1 kg = 1000 g (constant) |
| pack | items | no | 1 pack = 250 g of coffee (product → Product) |
## Currencies and rates
| PLN | 2 | NBP | mid | the business day before the invoice issue date |
| EUR | 2 | — | — | — |
## Rounding
| unit price | HALF_UP | 4 places | per item | accounting |
| VAT | HALF_UP | 0.01 | A: "It depends" (per item vs on the total) → parameter `VAT_rounding_moment` | law/accounting |
## Splitting amounts — | instalments | equal with a remainder | the first instalment (X → asked → A) |
## Decisions
| the rate from the day before the invoice | R |
| refunds as negative amounts | X → hot spot |
## Unmapped concepts — the price per kg per customer (→ Pricing), settling the instalments (→ Accounting)
```
