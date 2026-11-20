# Production traceability — bills of materials, production orders, lot genealogy, recalls

## When it applies
- Signal: goods are made from inputs or pass along a supply chain, and the origin of inputs — plus where and when things
  happened — must be answerable.
- Not this: pure buy-and-sell with no lot origin → product definitions + value ledger.

## Core shape
- **Bill of materials (BOM) / recipe**: a dated, versioned association between product definitions — parent → component,
  quantity with unit, optional tolerance (±%). Not a set of columns on the product.
- **Routing**: an ordered list of operations with work centre, time and materials; each operation is a work activity
  (work execution).
- Keep **capability**, **plan** and **actual production** apart, as IEC 62264 / ISA-95 does.
- **Production order**: freezes the BOM and routing versions valid on the order date; records consumed lots, produced
  lots, scrap and status.
- **Material requirements planning (MRP) output** — quantities and dates needed after on-hand stock — is accepted as data;
  the calculation runs behind an interface or in the ERP.
- **Discrete vs process** manufacturing: countable items, assembly, serials or lots — vs recipes, mixing, variable yield,
  co-products and waste, unit conversions. Decide which applies (sometimes both, per plant).
- **Lot as the trace unit**: input lot → output lot links form a **genealogy graph** with backward trace (what went in),
  forward trace (where it went), and as-of-date queries.
- **Traceability facts**: object, time, place, business reason. GS1 EPCIS 2.0 (GS1, 2022) offers a vocabulary of event
  types: object, aggregation (packing), transformation, association, transaction events.

## Rules
- You cannot consume more than a lot holds (a quantity invariant).
- Keep events, not only the current location — "where was it last Tuesday?" must be answerable.
- Suppliers are parties in a role; purchases are commitments.
- Minimum legal baseline in EU food law: Regulation (EC) No 178/2002, Article 18 — one step back, one step forward (know
  your direct supplier and direct customer). A full internal genealogy is an extension, built when recall precision
  requires it. Details by legal counsel.
- Quarantine release and recall decisions are policies; customer notification sits outside the model.

## Decisions to settle
- Substitute components; rework; mixed lots (a tank refilled before empty).
- Shelf life and quarantine status.
- Tracking unit: lot, serial, logistics unit (pallet with SSCC)?
- Identifier standards (GTIN, SSCC, GLN) — settle with a domain expert.
- Discrete, process, or both?

## Belongs elsewhere
- Stock quantities → value ledger; scheduling of production orders → stage scheduling; machine availability →
  resource holds; definitions and lots → product definitions.

## Traps
- `ingredients` text field on the product; BOM edited in place, so last month's orders show today's recipe.
- Only `current_warehouse` on a pallet.
- Treating a cream blend like discrete assembly — no yield, no co-products, no unit conversions.
- Genealogy reconstructed from invoices after a contamination alarm.

## Worked example
Requirement: a cosmetics maker blends creams from oil and emulsifier lots bought from suppliers, fills jars in daily
lots and ships to distributors; a contaminated emulsifier lot must lead to every affected jar lot and distributor.
- Process manufacturing: recipe `CREAM-HYD v3` = base oil 62% ±1, emulsifier `EMU-7` 8% ±0.5, water, actives; yield
  variable (95–98%).
- Production order `PO-0412` (2026-05-04) freezes recipe v3; consumed: oil lot `OL-88` 310 kg, emulsifier lot
  `EM-2219` 40 kg → bulk lot `BULK-0504` 492 kg (transformation event) → filled into jar lots `JAR-0504-A`, `-B`
  (transformation + aggregation into cartons).
- Shipments as transaction events: `JAR-0504-A` → distributor party *BeautyHub* (GLN), 2026-05-06.
- Recall of `EM-2219`: forward trace EM-2219 → BULK-0504 → JAR-0504-A/B → BeautyHub, Lumena. Backward trace from a
  complaint jar → its emulsifier and oil lots → supplier.
- One-step-back/one-step-forward is the legal minimum; the internal bulk → jar links are the extension that keeps the
  recall to two lots instead of a week's output. Notifying distributors happens outside the model.
