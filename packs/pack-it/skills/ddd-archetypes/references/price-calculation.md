# Price calculation — prices, fees, interest and penalties from changing rules

## When it applies
- Signal: the amount is computed from parameters that business staff should adjust without a code change.
- Not this: an amount that is merely copied or summed (an order total of fixed line prices is arithmetic).
- Typical requirements: tariffs, tiered rates, surcharges, minimum charges, late-payment interest, contractual penalties,
  commissions, promotions.

## Core shape
- **Calculation method** (a type): declares its **parameters** (fixed when configured, e.g. rate 0.12 EUR/kg) and its
  **inputs** (given per calculation, e.g. weight 340 kg). A missing parameter or input raises an explicit error — never a
  silent wrong price.
- **Configured calculator**: a named instance of a method with parameter values and a human-readable description
  ("Fuel surcharge 14% of freight").
- **Composition** into a tree from building blocks:
  - sum of components;
  - **banded (graduated)** — each band of the quantity priced at its own rate;
  - **threshold (volume)** — once the quantity reaches a band, all units get that band's rate;
  - percentage of another component (surcharge, discount, tax);
  - time-based: interest or per-period fee, annual rate converted with a stated day-count convention
    (actual/365, actual/360, 30/360);
  - minimum / maximum caps;
  - lowest or highest of alternatives.
- **Price list**: a set of calculators with an effective window and a version number. Any change creates a new version;
  older versions remain.
- **Rate set (scenario)**: a named, internally consistent set of input values valid at one instant — exchange rates,
  index values, energy prices, assumed cost increases. Each value is *sourced* (a feed and the field in it), *computed*
  from other values of the same set (a cross rate) or *entered* by a person. Calculations run against a chosen set:
  the official one, or a what-if ("diesel +15%"). Computed values are cached and invalidated when an input changes.
- **Price result**: money plus a **breakdown** — each component, the parameters used, the price list version.

## Rules
- Changing a rate = changing data. A genuinely new formula = a new method type. One class per promotion is an anti-pattern.
- Banded and threshold pricing differ at band edges — record which applies and put a numeric boundary example in the model.
- **Freezing**: a price quoted on an offer or order stores the amount and the price list version; later list changes do
  not reprice it.
- Past prices are reproducible from the stored version and inputs.
- Who gets which price list, and whether a discount may be granted, is decided by a policy and passed in as parameters
  (e.g. `customerSegment = contract`, `discountRate = 0.05`).
- Money and rounding per the quantity-and-money archetype; rounding point stated (per line or per total).

## Decisions to settle
- Discount stacking: cumulative (added up), sequential (each on the reduced price) or best-wins?
- Minimum price or minimum margin?
- Net vs gross; when is tax applied?
- When is currency converted (before or after caps)?
- Pro-rata when a price changes mid-period.
- Per-line vs total rounding.
- What-if replay: running a new price list against last quarter's orders before publishing it.

## Belongs elsewhere
- Posting the amount → value ledger.
- Whether an option is allowed → option constraints.
- Customer eligibility, approval rights for discounts → policy and authorisation.
- Subscription proration mechanics at a payment provider → be-billing-subscriptions.

## Traps
- `if (customer.isVip && month == 12) price *= 0.9` in a service or view.
- A float price recomputed differently on the client and the server.
- Repricing open quotes when the tariff changes.
- Not knowing whether "500 kg costs band-2 rate" means all 500 kg or only the part above 100 kg.

## Worked example
Requirement: freight per kg by weight band, fuel surcharge as a %, minimum charge per shipment, 5% off for contract
customers, quoted prices must not change after a tariff update.
- Tree: `max(min-charge 45.00 EUR, (freight + fuel) × (1 − discount))`, where `fuel = 14% × freight` and
  `discount` is a parameter from the customer policy (0.05 or 0).
- Freight bands: 0–100 kg at 0.40, 100–500 kg at 0.30, above 500 kg at 0.22 EUR/kg.
  - Banded, 340 kg: 100 × 0.40 + 240 × 0.30 = 112.00 EUR.
  - Threshold, 340 kg: 340 × 0.30 = 102.00 EUR. At exactly 100 kg: banded 40.00, threshold 40.00 or 30.00 depending on
    whether the band is `[100, 500)` — write the boundary down.
- Banded chosen (decision U). 340 kg contract customer: 112.00 + 15.68 = 127.68; × 0.95 = 121.296 → 121.30 (half-up on
  the total). Minimum 45.00 not reached.
- The quote stores `121.30 EUR, tariff 2026-v3, breakdown [freight 112.00, fuel 15.68, discount −6.38]`.
