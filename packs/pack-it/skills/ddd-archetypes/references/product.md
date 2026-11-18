# The Product archetype — mapper (type, instance, batch, offer)

> **Contents:** Fit test · Model (the essence) · Questions · Mapping steps · Decisions to check (R/A/X) · Result format · Patterns and pitfalls · Quality check · Example (shortened)

It turns requirements about **what a company sells, issues, manufactures or services** into a model that separates the meanings
hiding under the one word "product": the definition ("iPhone 15 Pro 256 GB"), a specific item (the phone with serial number X),
a batch (milk from batch LOT-2024-001), a service performed on a date (8.5 h of consulting) and an offer item ("on promotion until the end
of the month"). The effect: a new assortment = new data, not new columns and subclasses.
The common protocol (questions, "It depends", the R/A/X check, recording): `SKILL.md` → "Mapper — the common protocol".

## Fit test
**The core question:** *does the business describe "things" (goods, services) by features and must it distinguish the definition from items, batches
or the offer?* Yes → it fits. One service with no variants and no tracking → a simple dictionary is enough.

| Signal in the requirements | Fits? |
|---|---|
| catalog, categories, product card, "withdraw from the offer" | ✅ |
| serial numbers, VIN, IMEI, a warranty per item | ✅ |
| batches, expiry dates, batch recall | ✅ |
| `color`, `size`, `year` columns added with a new assortment | ✅ features |
| variants (size × colour), sets, bundles | ✅ |
| a service with a date and a life cycle | ✅ a service as a product |
| "how many items do we have in stock?" | ❌ → Accounting (or Availability) |
| "how much does it cost for this customer?" | ❌ → Pricing |
| "option A excludes option B" | ❌ → Configurator |
| "is this instance free on a date?" | ❌ → Availability |
| a subscription service | ⚠️ borderline |

**Borderline cases:**
- *A subscription* — does it have a definition with features, and are its instances (periods) what is sold? → Product + Accounting/agreement.
  Only the state "active/inactive" → a state machine.
- *A variant* — does the variant have its own code (GTIN/SKU) and stock level? Yes → a separate ProductType in a family. No, chosen
  at order time → instance features / Configurator.
- *A bundle* — sold as a whole with its own price, but issued from components? → a bundle with items (type + quantity).

## Model (the essence)
- **ProductType** — *what something is*: an identifier (ISBN, GTIN, UUID…), a name, a description, **a preferred unit** (Quantity),
  **a tracking strategy**, feature definitions.
- **Tracking strategy** — "how do we tell items apart?":

| Strategy | Example | An instance requires |
|---|---|---|
| unique | a painting, a specific musician's guitar | an identifier of the only item |
| tracked individually | serial number, VIN, IMEI; also an agreement, a shipment | a serial number |
| tracked by batches | food, medicines (quality control, recalls) | a batch |
| individually and by batches | TVs: a number + a batch for service campaigns | both |
| identical / interchangeable | screws, flour in bulk | nothing — instances optional |

- **ProductInstance** — a specific instance: a serial number and/or a batch (per the strategy), optionally a quantity (3.2 kg, 8.5 h;
  by default 1 preferred unit) and **feature values**.
- **Features instead of columns** — the type defines **feature types** (name, mandatory/optional, constraint: a list of allowed
  values, a numeric/decimal range, a date range, a regular expression, no constraint); the instance gives values validated
  against the definition. A new feature = data. Type features (constant for all items) ≠ instance features (e.g. mileage).
- **Batch** — a batch: the type, the quantity in the batch (in the type's unit), the dates of production / sell by / use by / best before,
  the range of serial numbers, notes.
- **Family and variants** — a family groups types differing in the values of distinguishing features (size, colour); each variant
  with its own code is a ProductType.
- **Bundle (set)** — a type composed of `type + quantity` items; choosing components with "one of / not together" rules → Configurator.
- **CatalogEntry** — *that something is for sale*: a marketing name, a sales description, navigation categories, **the offer's validity
  period**, metadata (highlights, badges). The same type may have several entries (channels, names, periods). Withdrawing from the offer
  = closing the period, not deleting the type.
- **A service as a product** — a service instance is the execution of a process: scheduled → in progress → completed / cancelled.

## Questions
**A — standard decisions:**
- Does the business distinguish specific items? By what? Are batch recalls needed? (→ the tracking strategy per type)
- Which features are mandatory for the type and which optional? What constraints do they have?
- Can "the same product" be in the offer several times (different names, channels, periods)?
- What happens to instances when the type is withdrawn from the offer?

**B — gaps** (examples): can the tracking strategy change for a type over time? · versioning of the type definition (old
instances under the old definition)? · inheritance of features in categories? · substitute units (sold per kg, stocked in pcs)? ·
substitutes and successors of a product? · who approves a new product card (a workflow outside the archetype)?

## Mapping steps
1. **Untangle "product"** — for every use of the word in the requirements: a type, an instance, a batch, an offer item or a service execution?
2. **Types** — a list of ProductTypes with an identifier, a preferred unit (Quantity) and a tracking strategy.
3. **Features** — columns/attributes from the requirements → feature types with constraints; the split: a type feature vs an instance feature.
4. **Instances and batches** — what requires a number, what a batch; batch fields (dates, the range of numbers).
5. **Variants and bundles** — families, distinguishing features, bundle compositions; refer selection rules to the Configurator.
6. **Offer** — catalog entries, channels, validity periods, categories; price → Pricing.
7. **Services** — the life cycle of a service instance and the consumption unit (h, session).

## Decisions to check (R/A/X)
the tracking strategy per type · mandatory features and constraints · a type vs an instance feature · a variant as a type vs a feature ·
bundle compositions · multiple catalog entries · the fate of instances after withdrawal from the offer · the preferred unit ·
versioning of the definition · batch fields (which dates are mandatory).

## Result format
```markdown
# Product model: <area>
## Concept mapping    — | Domain concept | Archetype element | Justification |
## Unmapped concepts
## Product types      — | Type | Identifier | Unit | Tracking strategy | Family |
## Features           — | Type | Feature | Level (type/instance) | Mandatory | Constraint |
## Instances and batches — | Type | Requires (number/batch) | Quantity | Batch fields |
## Bundles            — | Bundle | Component | Quantity | Selection rule |
## Offer              — | Entry | Type | Channel | Valid from–to | Categories |
## Services           — | Service | Unit | Life cycle |
## Decisions (R/A/X)  — | Decision | Source |
## Notes              — assumptions (X), edge cases, variable policy parameters
```

## Patterns and pitfalls
- One `Product` class for everything = a bag of flags and `color`, `size`, `year` columns added with every assortment.
- Type ≠ offer: deleting the type on withdrawal from the offer destroys the history of sold instances.
- The price is not a product feature → Pricing; the stock level is not a type field → Accounting/Availability.
- Quantities of instances and batches are Quantity (`quantity-money.md`), not a "bare" number.
- **Outside the archetype:** who may add a product or publish an entry — authorization/workflow; the archetype validates only
  the structure (features vs definitions, number vs strategy).
- **Variable policies as parameters:** "medicines: sale until 30 days before the use-by date" → the batch gets a ready `sell_by`.
- **The distribution channel is a separate dimension:** the same product type is sometimes sold in channels (shop, online, wholesale,
  partner) with a different assortment, description, price and availability. The channel is neither a type feature nor an `onlineOnly` flag:
  a catalog entry connects the type with a channel and a period, and the price per channel is Pricing.
- **PIM is not Inventory:** PIM (product information: descriptions, photos, features, translations) answers "what
  we sell and how to describe it", Inventory answers "how much we have, where, and whether it can be promised" (Availability,
  Accounting). A different owner, rate of change and rules, so separate contexts connected by the type identifier.
- **An import staging area:** data from outside (a supplier feed, a file, an integration) first goes to a staging
  zone as raw records with a validation status and a match against existing types. They move to the catalog or the stock
  only after validation or a human decision. A faulty import then does not break the state or the history, and a rejected
  record has a reason.

## Quality check
- [ ] every use of the word "product" assigned to one concept (type/instance/batch/offer/service)
- [ ] every type has a tracking strategy and a preferred unit
- [ ] no feature columns: every feature has a definition with a constraint
- [ ] withdrawal from the offer closes the period, does not delete the type
- [ ] price and stock referred to the appropriate archetypes
- [ ] the mapping table and "Unmapped concepts" present; no material (X)

## Example (shortened)
**Input:** "A bike shop: bikes in sizes S/M/L and colours, each with a frame number. Parts (inner tubes, chains) are sold
per item, grease per ml. The "Start" bundle: a bike + a helmet + a lamp. Bike servicing by the hour. Some models are sold online only."

```markdown
## Product types
| Bike Trek FX2 M black | GTIN | pcs | individually (frame no.) | family Trek FX2 |
| Inner tube 28" | GTIN | pcs | interchangeable | — |
| Chain grease | GTIN | ml | by batches (expiry date) | — |
## Features
| Bike | frame size | type | yes | {S, M, L} |
| Bike | service mileage | instance | no | 0–100,000 km |
## Bundles — | Start | bike (any from the family) + helmet + lamp | 1+1+1 | bike choice → Configurator |
## Services — | Servicing | h | scheduled → in progress → completed / cancelled |
## Decisions
| variant (size × colour) as a separate type | R: its own GTIN |
| sales channels | A: "It depends" on the model → parameter `channels` on CatalogEntry |
| grease tracked by batches | X → asked → A: yes (recalls) |
## Unmapped concepts — prices and the bundle discount (→ Pricing), the stock level (→ Accounting)
```

## Sources
- J. Arlow, I. Neustadt, *Enterprise Patterns and MDA*, Addison-Wesley, ISBN 9780321112309 (year: the sources give 2003
  or 2004) — the Product and Inventory archetypes (according to the table of contents; the content of the chapters was not verified).
- The distribution channel, PIM vs Inventory and the import staging area are described in our own words based on the programme of the training
  "DDD — zaawansowane techniki modelowania i archetypy" (DDD — advanced modelling techniques and archetypes; Bottega IT Minds, material from a human, 2026-10-21);
  the rules are the factory's modelling conclusions.
