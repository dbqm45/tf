# The Production / Supply archetype — mapper (product structure, production, procurement, traceability)

> **Contents:** Fit test · Model (the essence) · Questions · Mapping steps · Decisions to check (R/A/X) · Result format · Patterns and pitfalls · Quality check · Example (shortened)

It turns requirements about **manufacturing products** or **the flow of goods through a supply chain** into a model with the product
structure, the routing, the order and the batch trace. The effect: you know what something was made from, where and when, and where it went. The common protocol (questions, "It depends", the R/A/X check, recording):
`SKILL.md` → "Mapper — the common protocol".

## Fit test
**The core question:** *are products made from materials (or do goods pass through a supply chain), and do you need to know
from what, where and when?* Yes → it fits. If the company only buys and sells, knowing nothing about the origin of batches —
Product with Accounting is enough.

| Signal in the requirements | Fits? |
|---|---|
| "recipe", "bill of materials", "the product consists of…" | ✅ |
| "production order", "routing", "process stages" | ✅ |
| "what to order to carry out the production plan" (material requirements) | ✅ |
| "from which raw material batch was this product batch made?", "recall the batch" | ✅ traceability |
| catalog, variants, product types, serial numbers | ❌ → Product (`product.md`) |
| "the order of stages and the critical path" | ❌ → Planning |
| "is the machine free on Wednesday?" | ❌ → Availability |
| "which order on which machine to maximize value" | ❌ → General assignment |
| "stock level and inventory valuation" | ❌ → Accounting |
| "assembly at the customer's site as a service" | ⚠️ borderline |

**Borderline cases:**
- *A service vs a product* — if nothing is created materially, and the work over time is what counts → activity-process (operations)
  and resource-service; Production / Supply fits when a product batch with a trace of materials is created.
- *Distribution alone* — only traceability fits (batches, events); the structure and the routing are unnecessary.
- *A machine* — the asset is resource-service, capacity over time → Availability; here only the place where a segment is executed.

## Model (the essence)
### Product structure and process
- **Product structure (BOM)** — general manufacturing knowledge: a product consists of components in defined quantities.
  Our modelling conclusion: the BOM is **an association between products** (product → component, quantity → Quantity, period
  of validity, version); the product stays in Product, the BOM is not its field.
- **Routing / process segments** — the order of steps with a place, a time and materials; a step as an activity →
  activity-process.
- **Product definition, production capability, schedule and production execution** — the ISA-95 / IEC 62264 models
  (secondary, see "Sources"): "what we can do", "what was planned", "what was done". We take only **the separation of
  plan / execution**.
- **Production order** — the product, the quantity, the structure and the routing **in the version as of the order date**, a status, consumption
  and the result (batches, rejects). Versions of the structure with an effective date as in `agreement.md`, not an overwrite.

### Procurement
- **Material requirements planning (MRP)** — material requirements over time follow from the product plan and the structures, after
  taking stock into account (the demand-driven approach: Ptak & Smith 2011). The archetype **accepts the result** (requirements, dates)
  as data; the computation is an algorithm behind an interface. The supplier is a party in a role (Party), the purchase — Agreement.

### Discrete vs process
Our own conclusion, supported by the fact that Hay has separate chapters "Material requirements planning" and "Process manufacturing":
- **discrete** — countable items, assembly; key: the structure, serial numbers or batches;
- **process** — recipes, mixing, **co-products and waste**, a variable yield; key: a recipe with a tolerance,
  the batch as the trace unit, quantity conversions (Quantity).

### Traceability
- **Batch / lot** — the tracking unit (Product); input → output links form an origin graph.
- **Events** — we record facts (what, when, where, why). The
  GS1 EPCIS 2.0 standard (with CBV 2.0, 2022) distinguishes event kinds: ObjectEvent (an observation of an object), AggregationEvent
  (packing into a collective package), TransformationEvent (inputs → outputs), AssociationEvent (an association, new
  in 2.0), TransactionEvent (a link to a transaction); the descriptions in parentheses are a shorthand by the factory's authors, the normative definitions
  were not read. For the model this is **a dictionary of kinds of facts**, not necessarily an exchange format.
- **GS1 Global Traceability Standard 2.0 (2017)** — a framework for the traceability process in a supply chain.
- **The "one step back, one step forward" requirement** in food (Regulation (EC) 178/2002, art. 18; confirmed
  partly, indirectly) — context to be confirmed by a lawyer: an operator knows from whom it took and to whom it handed over.
  The minimal trace = this requirement; a full batch graph is an extension.
- **GS1 identifiers** (e.g. GTIN, SSCC, GLN) — [unverified] in this file; settle with an expert whether the company uses them.

## Questions
**A — standard decisions:**
- **Discrete or process** production (recipes, co-products, tolerances)?
- What is the **tracking unit**: a batch, an item (serial number), a collective package?
- How deep **back and forward** must we reach: one step or a full origin graph?
- Does the product structure **have versions**, and does the order freeze the version as of the order date?
- Who computes the material requirements (our system, the ERP, manually), and does the archetype only accept the result?

**B — gaps** (examples): component substitutes · co-products and waste · mixed batches · rework · shelf
life · quarantine · batch recall and notifying recipients (outside the archetype).

## Mapping steps
1. **Kind of production** — discrete, process, supply chain only.
2. **Products and components** — products from Product; the structure as an association with a quantity (Quantity) and a period.
3. **Routing** — segments, places, materials per step.
4. **Plan vs execution** — the order, consumption, the result, rejects.
5. **Material requirements** — the source of the MRP result; dates; the link to purchasing (Party, Agreement).
6. **Batches and the origin graph** — the tracking unit, input → output links.
7. **Events** — kinds of facts and their fields.
8. **Queries** — "back", "forward", "as of a day".

## Decisions to check (R/A/X)
discrete vs process · the tracking unit · the trace depth · versions of the structure and the routing · substitutes and
co-products · the source of material requirements · batch status · kinds of events.

## Result format
```markdown
# Production / Supply model: <area>
## Concept mapping    — | Domain concept | Archetype element | Justification |
## Unmapped concepts
## Structures and routings — | Product (→ Product) | Component | Quantity | Period/version | Segment and place |
## Orders             — | Order | Product | Structure version | Plan vs execution | Status |
## Batches and origin — | Batch | Type | Input batches | Shelf life | Status |
## Events and queries — | Kind of fact / question (back, forward, as of a day) | Data | Depth |
## Integrations       — | Event | From / to archetype | Reaction |
## Decisions (R/A/X)  — | Decision | Source |
## Notes              — assumptions (X), edge cases, variable policy parameters
```

## Patterns and pitfalls
- **The structure as columns in the product** (`component1`, `component2`) — no versions and no depth.
- **The current location instead of events** — no answer to "where was it on Thursday".
- **Batch = product** — the catalog mixed with the trace; keep the boundary with Product.
- **Plan and execution in one record** — the fact overwrites the plan.
- **Quantities without units** break consumption and yield → Quantity.
- **Authorization outside the archetype**: who releases a batch from quarantine or manages a recall is settled by the policy
  layer; the archetype records the fact and guards invariants (e.g. you will not consume more than there is in the batch).
- Without a trace requirement, do not build an origin graph; a batch and a supplier are enough.

## Quality check
- [ ] the kind of production (discrete/process) indicated; the tracking unit named
- [ ] the product structure is an association with a quantity (Quantity) and a period, not product fields
- [ ] plan and execution separated; the order freezes the structure version; the trace depth matches the requirement
- [ ] the boundaries indicated (Product, Planning, Availability, General assignment, Accounting, Quantity)
- [ ] GS1 identifiers [unverified] or omitted; the legal requirement only as context
- [ ] the mapping table and "Unmapped concepts" present; no material (X)

## Example (shortened)
**Input:** "A bakery: bread is made from flour, water, yeast and salt according to a recipe. We buy flour from several suppliers,
each delivery has a batch number. We issue bread to shops in daily batches. When a supplier reports a defect in a flour batch,
we must indicate which bread batches and which shops they went to." [example]

```markdown
## Concept mapping
| bread recipe | product structure (an association product → component, quantity with a tolerance) | process production |
| flour batch | input batch (supplier = Party) | tracking unit |
| the day's baking | production order → bread batch | input batches consumed in the order |
| issue to a shop | a flow event (moving a batch) | forward trace |
## Queries — back: from which flour batches was batch P made · forward: which shops did the batches from flour
   batch M go to (depth: full graph, because of the recall) (A: "It depends" on the requirement → parameter `trace_depth`)
## Decisions — recipe with versions (X → ask) · notifying the shops outside the archetype (R)
## Unmapped concepts — ordering flour from the supplier (→ Agreement / Party) · the oven as a resource (→ Availability,
   resource-service) · units (kg, sack) (→ Quantity)
```

## Sources
Accessed 2026-10-17.
- **IEC 62264-1:2013 "Enterprise-control system integration — Part 1: Models and terminology"** (ed. 2, replaced
  the 2003 edition) — a primary standard; part 1 defines level 3 (MOM) and the interface of levels 3–4. Currency in 2026
  uncertain (EVS: withdrawal of 62264-2:2013 from 2026-05-04, a newer edition possible).
- **The ISA-95 models** (personnel, equipment, material, process segment, production capability, product definition,
  schedule, production execution) — secondary, partly confirmed; levels 0–4 and B2MML not verified.
- **"Orlicky's Material Requirements Planning", 3rd ed., Ptak & Smith, McGraw-Hill 2011** — primary for MRP in the
  demand-driven approach. Concepts cited as originating from Orlicky in 1975 were not verified.
- **Hay, "Data Model Patterns: Conventions of Thought", Dorset House 1996** — only the chapter titles "Material
  requirements planning" and "Process manufacturing" (a library catalog); the content of the sections was not verified.
- **Silverston, "The Data Model Resource Book, Vol. 2, Revised Edition", Wiley 2001, ISBN 978-0-471-35348-5** —
  ch. 2 "Manufacturing"; the sections (BOM, MRP) were not verified (the sources contradict each other).
- **GS1 EPCIS 2.0 and CBV 2.0** (ratified June 2022, ref.gs1.org; EPCIS/CBV Implementation Guideline 2.0 —
  March 2023) — primary; the event kinds partly confirmed.
- **GS1 Global Traceability Standard, Release 2.0, August 2017** — primary; the framework for the traceability process.
- **Regulation (EC) No 178/2002, art. 18** — the "one step back, one step forward" requirement; confirmed
  partly, indirectly through recital 3 of implementing regulation 931/2011 (EUR-Lex). Only legal context,
  to be confirmed by a lawyer, not advice.

The rest (the BOM as an association of products, discrete vs process, the origin graph, pitfalls) are our modelling conclusions,
not attributed to the authors. Described in our own words; the content of books and standards was not quoted.
