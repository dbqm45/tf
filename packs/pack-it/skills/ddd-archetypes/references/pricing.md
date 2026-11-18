# The Pricing archetype — mapper (calculators, price lists, validity, frozen price)

> **Contents:** Fit test · Model (the essence) · Questions · Mapping steps · Decisions to check (R/A/X) · Result format · Patterns and pitfalls · Quality check · Example (shortened)

It turns requirements in which **a price or an amount follows from rules** (the customer, the quantity, the date, the agreement, a promotion, the time value
of money) into a model of named calculators. A price is rarely a product field; scattered across `if`s in services, it makes every
promotion a code change and a regression risk, and the business does not know how it was computed. The effect: a new rate = data, a new way of computing =
a new type, every price can be **explained and reproduced**. The common protocol: `SKILL.md` → "Mapper — the common protocol".

## Fit test
**The core question:** *is the amount produced by a computation on parameters (rates, thresholds, time) that the business wants to change
without a developer?* Yes → it fits. The amount is only copied from a document or summed from history → not Pricing.

| Signal in the requirements | Fits? |
|---|---|
| price list, rate, tariff, discount, promotion, "cheaper from 10 pcs" | ✅ |
| interest, a fee per day/month, a % commission, a contractual penalty | ✅ |
| "the price depends on the customer / agreement / season / channel" | ✅ |
| "show the customer how the price was computed" | ✅ |
| "how many points does the customer have?", balance, settlements | ❌ → Accounting |
| "which variant / which options may be chosen together?" | ❌ → Configurator (the option price → Pricing next to it) |
| "an amount in a currency, rounding, splitting into instalments" on its own | ❌ → Quantity/Money |
| "price = a product field, changed manually once a year" | ⚠️ borderline |

**Borderline cases:**
- *Price as a catalog attribute* — is there **any rule** (quantity, customer, period)? No → a Product attribute with history;
  yes → Pricing.
- *A commission/tax as the effect of an event* — Pricing computes the amount (a calculator), and posting it is an Accounting posting rule.
- *Pricing a configuration* — whether options are allowed is the Configurator; the price of the chosen options is Pricing calculators.

## Model (the essence)
| Element | Essence |
|---|---|
| **Calculator type** | a way of computing; it declares parameters **at creation** (an amount, an annual rate) and **at calculation** (a base, a number of days, a time unit). A missing parameter = a readable error, not a silently wrong price |
| **Calculator (instance)** | a name + a type + parameter values + a readable **description** ("a fixed amount of 20 PLN", "6% per year accrued per day/week/month/year"). It returns **Money** |
| **Calculator registry** | the business/configuration creates named instances ("interest-6", "fixed-fee-20"); pricing = choosing by name + parameters |
| **Composition** | a calculator composed of others — the table below |
| **Price list** | a set of calculators with **a validity period** (`valid_from`, `valid_to`) and **a version**; a change = a new version, the old one stays for reproduction |
| **Quote (result)** | Money + **a breakdown** (which calculator, what parameters, what price list version) — explainability and audit |
| **Offer price** | a quote **frozen** on an offer/order: a copy of the amount + a reference to the version; a later price list change does not touch it |

**Calculator composition**
| Kind | Action | Example |
|---|---|---|
| sum | adds the results of the components | base price + a delivery fee |
| step (tiered) | a fixed price per range, increases in steps | 1–10 pcs at 5 PLN, 11–50 at 4 PLN (each range separately) |
| threshold | after crossing a threshold **the whole** quantity at the new rate | ≥ 100 pcs → everything at 3 PLN |
| percentage | % of a base (another calculator) | a 10% discount, a 2% commission |
| daily / interest | rate × time; the annual rate converted per day/month | 6% per year × 45 days of delay |
| min / max | limits a component's result | a 2% commission, no less than 5 PLN |

Rounding and scale **explicit**: high precision internally, the result to the grosz (cent), the rounding rule in one place
(Money from `quantity-money.md`).

## Questions
**A — standard decisions:**
- What does the price depend on? What is a **fixed parameter** of the calculator, and what is **transaction data**?
- Who changes the price rules and how often? (configuration vs code)
- Must the customer see **how** the price was computed? (description, breakdown)
- From when is the price in force and **how long is the offer valid**?
- Is the price on the order **frozen**, or recomputed on fulfilment/invoice?
- Thresholds: **step** (each range separately) or **threshold** (the whole quantity at the threshold rate)?

**B — gaps** (examples):
- the order of applying discounts (from the base price or cascading)? combining promotions (they add up / the best one wins)?
- a minimum price / minimum margin? · currencies and exchange rates (when to convert)? · net/gross and VAT (Pricing or separately)?
- a price list change during a billing period (pro rata)? · reproducing a price from a year ago (a complaint, an audit)?
- rounding per item or on the total? · a "what if" simulation of a new price list on historical orders?

## Mapping steps
1. **Amounts** — list every amount from the requirements (price, fee, interest, discount, commission); for each: currency, precision, rounding.
2. **Calculator types** — the ways of computing; for each the creation and calculation parameters. Do not multiply types: a new rate is an instance.
3. **Instances** — named calculators with a description readable for the business.
4. **Compositions** — a tree of calculators for each final amount (sum, step, threshold, percentage, daily, min/max).
5. **Price lists** — grouping instances, the validity period, versioning, the price list selection rule (customer, channel, date).
6. **The moment of pricing and freezing** — when the price is computed (offer, order, invoice) and where it is frozen.
7. **Breakdown** — what goes into the explanation of the price (customer, audit, support).
8. **Boundaries** — what Pricing does not do: who may grant a discount (authorization), posting the amount (Accounting), whether options are allowed
   (Configurator).

## Decisions to check (R/A/X)
calculator types and their parameters · step vs threshold · the order and combining of discounts · rounding (per item / on the total,
mode) · the currency and the moment of conversion · the validity of the price list and the offer · versioning · freezing the price on the order · converting
the annual rate (365/360, actual days) · net/gross · minimum price · who changes the configuration.

## Result format
```markdown
# Pricing model: <area>
## Amounts            — | Amount | Currency | Precision | Rounding |
## Concept mapping    — | Domain concept | Archetype element | Justification |
## Unmapped concepts
## Calculator types   — | Type | Creation parameters | Calculation parameters | Result |
## Calculators        — | Name | Type | Parameters | Description for the business |
## Compositions       — a tree per final amount
## Price lists        — | Price list | Calculators | Valid from | Valid to | Version | Selection rule |
## Moment of pricing and freezing
## Price breakdown    — explanation fields
## Decisions (R/A/X)  — | Decision | Source |
## Notes              — assumptions (X), variable policy parameters, boundaries with other archetypes
```

## Patterns and pitfalls
- **A new rate = data, a new way of computing = a new type.** A calculator type for every promotion is an `if` in disguise.
- A price stored only as a result with no reference to the calculator and the version — it can be neither explained nor reproduced.
- Recomputing orders after a price list change — a classic mistake; the offer price is **frozen**.
- A price list edited in place loses history — **version** it, a validity period instead of overwriting.
- Confusing step with threshold gives different amounts at a range boundary — record it explicitly and add a numeric example.
- `double` for money — no; Money with an explicit scale and rounding.
- **Outside the archetype:** "may a sales rep give a 15% discount?" is authorization (the application layer), Pricing computes the given discount.
  Variable policies ("a VIP customer has a different price list") → the rules layer chooses the price list/calculator and supplies it as **a parameter**.

## Quality check
- [ ] every amount from the requirements has a calculator (or a composition) and a description readable for the business
- [ ] every type has a list of creation and calculation parameters; a missing parameter → an error
- [ ] rounding, currency and precision defined in one place
- [ ] price lists have a validity period and a version; it is known when the price is frozen
- [ ] step/threshold settled with a numeric example at a range boundary
- [ ] the mapping table and "Unmapped concepts" present; no material (X)

## Example (shortened)
**Input:** "A bike rental: 15 PLN per hour, from 4 hours 50 PLN per day. For each day of delay a penalty of 30 PLN.
Regular customers have a 10% discount. The price from the booking is in force even when we change the price list."

```markdown
## Calculator types
| rate_per_unit | rate, unit | number of units | Money |
| flat_fee | amount, period | — | Money |
| percentage | rate | base (Money) | Money |
## Calculators
| rental-hour-15 | rate_per_unit | 15 PLN/h | "15 PLN for each hour" |
| rental-day-50 | flat_fee | 50 PLN/day | "the whole day 50 PLN" (min chooses it from 4 h: 4×15=60 > 50) |
| penalty-delay-30 | rate_per_unit | 30 PLN/day | "30 PLN per day of delay" |
| discount-regular-10 | percentage | −10% | "10% for regular customers" |
## Compositions — rental = min(rental-hour-15, rental-day-50) → percentage(discount) if applicable; the penalty separately (no discount? → X)
## Moment of pricing — booking; the price frozen with a reference to the price list version (R)
## Decisions
| discount also on the penalty? | X → asked: "It depends" → parameter `discount_covers_penalties` from the loyalty policy (A) |
| who is a "regular customer" | outside the archetype — a rule supplies `discount` as a parameter (A) |
| rounding up to a full hour | X → hot spot |
```
