# System types — which archetypes a known kind of system is built from

A named system type ("we are building a WMS", "a booking platform", "billing") is not one archetype but a familiar
combination of several. Use the table to know which archetype files to open first and which decision usually decides
the design; then run the signal question of each candidate as usual — a row is a starting point, not a verdict.

Archetype names below are the reference files of this skill. "Core" = almost always present; "often" = present when
the requirements mention it.

| System type | Core archetypes | Often | The decision that usually shapes it |
|---|---|---|---|
| Online shop | product definitions, price calculation, quantities and money | value ledger (stock, vouchers), places and zones (delivery), commitments (order vs sale), identity (supplier codes) | Is stock a ledger of movements or a number per item? |
| Marketplace | parties and relationships, product definitions, commitments | price calculation (commission), value ledger (payouts, escrow), evidence documents | Is the operator a party to the sale or only an intermediary? |
| Booking / reservations | resource holds, assets and services | waiting lists, price calculation (tariffs), commitments (cancellation terms), parties | What exactly is held — a unit, a seat, a time slot, a pooled count? |
| Warehouse (WMS) | value ledger (holdings per item × location, movements), product definitions (lots, serials), places and zones (bins, zones) | work execution (picking and counting tasks), resource holds (dock slots), production traceability | Is a movement booked when planned, when picked or when confirmed? |
| Transport / fleet (TMS) | places and zones, assets and services, work execution | task selection (who drives what), stage scheduling (multi-leg), resource holds (vehicles), observations (telemetry) | Are routes planned centrally or adjusted by drivers in the field? |
| Point of sale | price calculation, quantities and money, value ledger (cash drawer) | product definitions, evidence documents (receipts, fiscal rules) | Must the terminal work offline, and how are conflicts merged later? |
| Billing / subscriptions | price calculation, value ledger, commitments | quantities and money (usage units), evidence documents (invoices) | Is usage rated as it happens or in a batch at period end? |
| Loyalty / credits / vouchers | value ledger | price calculation (earning rules), parties | Which origin of value is drawn down first, and does it expire? |
| Accounting / finance core | value ledger, quantities and money | commitments, evidence documents, identity (counterparty numbers) | Which events post automatically, through which posting rules? |
| CRM | parties and relationships, commitments (quotes, contracts) | identity (duplicates, external ids), places and zones, work execution (activities) | When do two records count as the same customer, and who merges them? |
| HR, leave and time | parties (positions), value ledger (leave days), work execution (time entries) | commitments (employment terms), price calculation (payroll rates) | Is a correction a reversal of the past or a change from today? |
| Field service / maintenance (CMMS) | assets and services, work execution | observations and measurements (inspections, readings), resource holds (technicians), task selection | Is the outcome of a visit recorded separately from its completion? |
| Manufacturing (MES) | production traceability, work execution, product definitions | value ledger (material stock), stage scheduling, observations (quality checks) | How deep must lot genealogy go for a recall? |
| Lab / quality (LIMS) | observations and measurements | work execution (sampling rounds), evidence documents (certificates), product definitions (lots) | Which results are tentative and who accepts them? |
| Insurance / policy administration | commitments (terms, amendments, bitemporal), parties | price calculation (premiums), value ledger, evidence documents | Are backdated amendments allowed, and what did we know when? |
| Case management | work execution (case work, not a fixed flow), parties | evidence documents, commitments (deadlines from rules) | Which steps are mandatory, and which are the case worker's judgement? |
| Document / records management | evidence documents | identity and references, parties | What is the retention trigger, and who can place a legal hold? |
| Master data management | identity and references | parties, product definitions, places and zones | Which merge strategy, and must a merge be reversible? |
| Learning platform (LMS) | parties (learners, groups), product definitions (courses), work execution (attempts) | observations (assessment results), commitments (enrolments), waiting lists | Is a course a definition with many runs, or each run its own item? |
| Event ticketing | resource holds (seats), price calculation | waiting lists, product definitions (ticket types), commitments (refund terms) | Seat-level holds or counted capacity per section? |
| IoT / telemetry platform | observations and measurements, assets and services | places and zones, work execution (alarms → work) | Which readings are kept raw, and which only as derived figures? |

## When the table does not help
- Technical systems (a compiler, a gateway, a rendering engine, a scheduler library) are not compositions of business
  archetypes — use the architecture and engineering skills (arch-*, eng-*) instead.
- A content management system is mostly evidence documents plus publishing workflow; the rest is technology.
- A system type the business invented ("our platform") — split it into the questions of the router table in SKILL.md
  rather than forcing the nearest row.

## Worked example
Input: "We are building a WMS for a regional distributor: receiving, put-away, picking, cycle counts, lot recalls."
- Open first: value ledger (holdings per item × bin, movements as balanced transactions), product definitions
  (lots), places and zones (bins and zones). Then work execution for picking and counting tasks, production
  traceability for the recall question.
- Deciding question to the business: is stock reduced when a pick is planned, when it is picked, or when the shipment
  is confirmed? The answer fixes which holdings exist (available, allocated, picked) and which movements post when.
- Not from the table: the decision itself, the bin naming scheme, the recall depth — those come from the requirements.
