# Product definitions — type vs item vs lot vs listing vs service run

## When it applies
- Signal: the word "product" in the requirements means different things in different sentences. Classify each
  occurrence: **definition** (the type), **item** (a physical piece), **lot** (a batch), **listing** (a catalog entry),
  or **service run** (one execution of a sold service).
- Typical requirements: catalogs, variants, serial numbers, expiry dates, bundles, sales channels, supplier feeds.

## Core shape
- **Definition**: identifier (GTIN, ISBN, SKU or internal), name, default unit of measure, feature definitions, and a
  **tracking mode**.
- **Tracking modes**: one of a kind; serialised (serial number, VIN, IMEI); lot-tracked (food, pharma, anything
  recallable); serial and lot; fungible / untracked. The mode decides what an item record must carry.
- **Item**: serial and/or lot as the mode requires, an optional amount (defaults to one default unit), feature values.
- **Feature definition** (data, not columns): name, mandatory/optional, constraint — enumeration, integer or decimal
  range, date range, pattern (regex) or none. Type-level features are fixed for the definition; item-level features
  (mileage, colour of this piece) vary per item.
- **Lot**: amount in the definition's unit, manufacture date, sell-by, expiry and best-before dates, optional serial
  range, notes.
- **Bundle**: a definition composed of (definition, quantity) components.
- **Listing**: marketing name, copy, categories, validity window, badges, **sales channel** — separate from the
  definition; one definition has many listings.
- **Service run**: a service sold as a product has an execution lifecycle (planned → running → done, or cancelled) and a
  consumption unit (hours, sessions).

## Rules
- A variant with its own code and stock is its own definition, grouped into a family by distinguishing features.
  Otherwise it is an item feature or a configurable choice.
- Choices inside a bundle are option constraints, not bundle structure.
- Withdrawing a product ends its listing's validity; the definition is never deleted — sold items keep their history.
- The sales channel is a dimension of the listing, not a boolean per channel. Price per channel → price calculation.
- Product information (descriptions, media, translations) and inventory (how many, where, can we promise it) are separate
  contexts with different owners and change rates, linked by the definition id.
- Inbound supplier feeds land in a staging area with validation status and match results before reaching the catalog or
  stock; rejected records keep a reason.
- Prices are not product attributes (→ price calculation); on-hand counts are not either (→ value ledger or an
  availability view). Quantities use the quantity archetype.

## Decisions to settle
- Can the tracking mode change over time (a product becomes lot-tracked after a regulation)?
- Are definitions versioned?
- Substitutes and successors (a discontinued model replaced by a new one)?
- Alternative units: sold by weight, stocked by count?

## Belongs elsewhere
- Compatibility of options → option constraints.
- Prices → price calculation; stock → value ledger.
- Lot genealogy and recalls → production traceability.

## Traps
- Columns `screen_size`, `ram_gb`, `sleeve_length` on one product table; one form per product type.
- `active = false` on the definition to hide it from the shop — history and reorders break.
- `price` and `stock` columns on the product.
- One "product" table mixing the catalog card and the serial-numbered piece in the warehouse.

## Worked example
Requirement: a bike shop sells frames (serial numbers), tyres (by count), lubricant (lot with expiry), a "commuter kit"
and a fitting service, online and in two stores.
- Definitions: `FRAME-AL54` (serialised; type feature `material = aluminium`, item feature `colour`), `TYRE-700x32`
  (fungible, unit piece), `LUBE-100` (lot-tracked, unit ml, lots with expiry date).
- Bundle `KIT-COMMUTER` = {lights × 1, lock × 1, mudguard set × 1}; the choice of lock model is an option constraint.
- Service `FIT-60` sold per session; each sale creates a service run planned → done.
- Listings: `FRAME-AL54` listed online ("Urban 54 — light and stiff") and in store A only; withdrawing from store A ends
  that listing, the online one stays.
