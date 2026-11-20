# Quantities and money — numbers that carry a unit or a currency

## When it applies
- Signal: remove the unit or currency and the number means nothing ("12" — kilograms? euros? days?). Then it is a value
  object, not a primitive.
- Stays a plain number: counters, identifiers, ratings, a plain percentage shown to a user.
- Typical requirements: weights and volumes on products, prices in several currencies, instalments, tax lines,
  conversions between packaging units, reports in a reporting currency.

## Core shape
- **Unit**: symbol, name, **dimension** (mass, volume, length, duration, count, …). The unit set is extensible as data
  (a custom "crate of 24" or "pallet" unit), not an enum frozen in code.
- **Quantity** = exact decimal amount + unit. Record the amount and unit as given at capture; convert on read.
- **Compound unit**: base units with signed integer powers (kWh, m³/h, EUR/kg, km/h). Conversion reuses the base-unit
  factors raised to their powers.
- **Money** = exact decimal amount + ISO 4217 currency code. The currency knows its minor-unit digits: JPY 0, EUR 2,
  KWD/BHD 3 (ISO 4217 list, iso.org, accessed 2026-11-20). Store as a decimal type or an integer count of minor units.
- **Ratio** (interest rate, tax rate, discount percentage) is its own dimensionless type — not money, not a quantity.
- **Exchange rate**: currency pair, value, the instant it is valid for, source (e.g. a central bank table), kind
  (buy / sell / mid).
- **Rounding policy**: mode (half-up, half-even "banker's", down, to a cash increment such as 0.05), precision, and the
  **point of application** (per line or per document total). Defined once and passed in.
- A billable duration is a quantity in a time unit; a calendar instant is a date/time type, never a quantity.

## Rules
- Add, subtract and compare only within the same unit or currency; a mismatch is an error (or does not compile).
  Multiply and divide only by a scalar or a ratio.
- Operations on money: negate, abs, min/max, sign checks (`isNegative`, `isZero`), division that returns the remainder,
  and **allocation by weights** whose parts always sum back to the original — the leftover minor units go to a stated
  part (first, last, largest).
- Conversion inside one dimension (kg ↔ g, h ↔ min) is a fixed factor table on the units; a chain of factors reaches
  indirect targets, and tests cover round trips. Offset scales (°C ↔ °F) are not a factor — a conversion function.
- Calendar units (month, year) have no fixed length; never convert them by a constant — use dates.
- Conversion that depends on the product (box ↔ pieces, litres ↔ kg through density) is product data, never a unit rule.
- Currency conversion stores, on each converted amount, the rate used (pair, value, instant, source, kind) so a report
  can be reproduced. Past events use the rate valid at the event, never "today's rate".
- Intermediate precision may be higher than final (unit prices to 4 decimals, the line total rounded to the currency).
- No binary floating point for money anywhere: model, API, database, UI.
- Formatting and localisation (symbols, separators, "1 234,50 zł") belong to presentation; one formatter for the whole UI.

## Decisions to settle
- Are negative amounts allowed (refunds, corrections) or is direction a separate field?
- Which part receives the remainder of a split (first instalment, last, the largest line)?
- Can one document total several currencies, or one currency per document?
- Whose rules govern rounding: tax law, accounting policy, the contract? Line-level or total-level for tax?
- Which rate source and kind applies to each kind of conversion, and at which instant (order, invoice, payment)?

## Belongs elsewhere
- Which rate or discount applies to whom → price calculation (with a policy).
- Balances over time → value ledger.
- Product-specific conversions → product definitions.

## Traps
- `double price` plus a separate `currency` string, rounding scattered over services and views.
- Value and unit as two loose strings (`"12"`, `"kg"`).
- The unit in the field name (`weight_kg`, `duration_min`) — input in another unit is converted by hand or silently wrong.
- Splitting 100.00 into 3 × 33.33 and losing 0.01; the parts must sum to the total.
- Tax rounded per line in one place and per total in another — two different invoice totals.
- Treating a percentage as money ("10 EUR off" vs "10% off" typed the same).

## Worked example
Requirement: a yearly subscription paid in JPY, PLN and USD, reported in EUR, payable in 4 equal instalments.
- ¥100,000 / 4 → ¥25,000 × 4 (0 minor digits, no remainder). 1,000.00 PLN / 4 → 250.00 × 4.
  1,000.01 USD / 4 → 250.00 + 250.00 + 250.00 + 250.01 — the remainder goes to the **last** instalment (decision U).
- Each instalment converted to EUR stores `rate {USD/EUR, 0.9212, 2026-03-01T00:00Z, ECB reference, mid}` — numbers
  illustrative.
- Tax: 23% computed on the document total, half-up to 2 decimals (decision A, to confirm with accounting).
- The UI shows "approx. €230.30" for a preview; only the server-computed amount is ever charged.
