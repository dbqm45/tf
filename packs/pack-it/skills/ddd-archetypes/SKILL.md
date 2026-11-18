---
name: ddd-archetypes
argument-hint: "[archetype] [requirements]"
description: Use for business archetypes — parties, bookings, money, product, accounting, pricing, agreements, resources.
metadata:
  review: "2027-10-17"
  catalog: "Use when you model, map requirements onto an archetype or analyse (also existing code) an area with a proven business archetype — parties and relationships, availability and bookings, quantities and money, product, accounting, pricing, configurator, waitlist, resource assignment, stage planning, locations and addresses, resources and services, procedures and activities, agreements and orders, documents and retention, production and batch traceability. Not for purely technical or novel domains with no pattern, nor for documentation in the repository (docs-tech-writing)."
  keywords: "program lojalnościowy, punkty lojalnościowe, saldo, wygasanie punktów, rezerwacja zasobu, dostępność terminu, cennik, rabat, kolejka oczekujących, przydział zasobów, strefy dostaw, adresy klientów, adres z dnia sprzedaży, kody pocztowe i gminy, umowa z aneksami, aneks zmienia cenę od daty, co obowiązywało w danym dniu, umowa ramowa i zamówienia, wersje dokumentu, podpisany dokument, okres przechowywania dokumentów, kategoria archiwalna, receptura, partia surowca, wycofanie partii, identyfikowalność, procedura i wykonanie, zlecenie pracy, checklista przeglądu, aktywa i serwis, katalog usług, lista rezerwowa, rezygnacja z miejsca, pierwszeństwo stałych klientów, limit miejsc, loyalty program, loyalty points, balance, points expiry, resource booking, slot availability, price list, discount, waiting queue, resource assignment, delivery zones, customer addresses, address as of the sale date, postal codes and municipalities, agreement with amendments, an amendment changes the price from a date, what was in force on a given day, framework agreement and orders, document versions, signed document, document retention period, archival category, recipe, raw material batch, batch recall, traceability, procedure and execution, work order, inspection checklist, assets and servicing, service catalog, waitlist, giving up a place, priority for regular customers, place limit"
---

# Business model archetypes

An archetype is a proven, generic model of a problem that recurs in many industries (refined, among others, by
ERP system engineers and in Fowler's analysis patterns). Instead of inventing a model from scratch, you recognize the archetype,
and you add the business specifics **with policies and configuration**. The effect: a system open to extension.

## An archetype is not a design pattern
GoF patterns are tactical, technical solutions in code, recognizable and applied the same way. An archetype works one level higher:
it is **a way of thinking about a business model**, applied strategically and tactically, with a flexible implementation.
Treat it as **a signpost, not a ready plan** — the details depend on the complexity of the business, the scale, the consistency boundaries
and regulations.

## When to reach for it
- **Strategically** — it speeds up drawing contexts: a pricing problem → Pricing, a value that changes over time →
  Accounting, users and roles → Party, resource availability → Availability (sometimes called Inventory). It helps separate
  the complexity of the core domain from repeatable operational patterns.
- **Tactically** — it suggests decisions about aggregates and known pitfalls, e.g.:
  - Accounting: instead of one big Account aggregate with a list of transactions — the **transaction** in the centre, and accounts are reference
    points for entries (a transaction usually concerns two accounts; it scales better and reflects reality);
  - Party: addresses in the party aggregate or separately? The deciding question is about **rules requiring immediate consistency**
    between the party and the addresses; at large scale more often separately.
- Best: custom software, modernization or refactoring of the architecture, new systems in classic
  domains (trade, finance, logistics, health, telecommunications, energy).

## When NOT to reach for it
- **Purely technical domains** (firmware, flight control) — no classic business archetypes.
- **Deploying a bought product** (ERP, CMS, BPMS) with no influence on the model.
- **Legacy maintained with patches**, without architectural consistency, when we do not plan modernization.

## Signals that an archetype fits
- The area lies on the **right side of Cynefin** (ordered, known in the industry) — ddd-strategic-analysis.
- The model gets flags and branches like "what if the customer is also a supplier?", "what if the car is in the service shop?".
- Several products/processes ask the same key question ("is the resource free?", "who is this party?") → model
  **the capability**, not the product.

## How to use it
1. Describe the problem in levels (from the simplest requirement to the hardest) — as in the reference materials.
2. Recognize the archetype and check which of its elements are needed. Do not implement the whole thing "just in case".
3. Express the business specifics with policies (e.g. who may grant a role, how many relationships are allowed, whether a resource may be disabled).
4. Place the archetype as a separate module/context with a small interface at the edge (ddd-context-mapping → a deep module).
5. Decide the model level:
   - **capability** — what we can do at all (e.g. a resource can be blocked in time),
   - **operations** — everyday actions (block, release),
   - **policies** — rules configuring the operations (who, when, how much),
   - **decision support** — analyses and recommendations based on operational data.

   Layers depend only on lower ones: a policy configures operations, but operations do not know policies by name. This is a version of
   Evans's responsibility layers (*Domain-Driven Design*, 2003, ch. 16 "Responsibility Layers"; Evans also has,
   for example, a commitment layer [unverified: layer names from secondary sources]). The knowledge and operations level:
   ddd-deep-modeling, `.claude/skills/ddd-deep-modeling/references/untangling.md`.

## Mapper — the common protocol (every archetype)
Every `references/<archetype>.md` file is a **procedure for mapping** requirements onto the archetype: fit test → questions → steps →
decision check → result. This protocol is common; the archetype files contain only what is specific. A direct call:
"map onto the Accounting archetype: <requirements>" or `/ddd-archetypes accounting <requirements>`.

0. **Requirements** — from the argument; if missing, from the current conversation / `docs/project/` (areas, requirements); only when there is nothing —
   one question about the description of the domain.
1. **Fit test** (a section of the archetype file) — **before** mapping. It does not fit → a short assessment "❌ does not fit" with reasons
   from the requirements and **stop**. If the signals clearly point to another archetype from the catalog — one sentence "check X"; nothing more.
   A borderline case → the deciding question from the file.
2. **Questions** — only about what the requirements do not settle: (A) the archetype's standard decisions, (B) **gaps**: capabilities
   of the archetype the requirements are silent about (think on your own, the list in the file is examples).
   - `AskUserQuestion`: up to 4 questions per call, decisions as **design options**, not assumptions; the last option is always
     **"It depends"**. "It depends" = **a variable policy**: the archetype takes a *parameter* (e.g. `valid_to`, `balance_policy`),
     and its value is computed by the rules layer above the archetype — do not model this logic in the archetype.
   - In a subagent (no conversation): do not guess — return the questions as hot spots, and in the model mark the decisions as (X).
3. **Concept mapping** — a table `domain concept → archetype element → justification` + an **"Unmapped concepts"** section
   (always present; "none" is also a result). An unmapped concept often points to another archetype or to the core.
4. **Archetype-specific steps** (from the file).
5. **Decision check (R/A/X)** — before the result, list every concrete decision contained in the model and its source:
   **(R)** from the requirements · **(A)** an answer to a question · **(X)** adopted silently. An (X) decision with small impact (technical) →
   an explicit assumption in "Notes"; an (X) changing business behaviour → **ask before handing over the model** (in a subagent: a hot spot).
6. **Result** in the format from the file → `docs/project/02-domain/archetypes/<archetype>-<area>.md` (the core-project-record header,
   `artifact: archetype-model`, TL;DR, Open questions, Handoff).

Common rules:
- **Authorization outside the archetype.** The archetype records what happened and guards structural invariants. "Is it allowed?" depending
  on *who*, *why* and *what else is going on* — the application/policy layer, which then calls the archetype. The exception:
  unconditional numeric limits ("balance never < 0") may be enforced by the archetype itself.
- **A variable policy comes from outside** as an operation parameter — the archetype executes it mechanically.
- **The minimum that answers the requirements** — do not implement the whole archetype "just in case"; missing elements are future extensions.
- Archetypes compose — when mapping reveals another archetype (e.g. Quantity in Product), note it and refer to its file.
- Cost: read only the file of the indicated archetype; delegate mapping of large materials to a subagent (`*-ddd-analyst`), and conduct the conversation in the main thread.

## Catalog
| Archetype | You recognize it by | The essence of the solution | Details |
|---|---|---|---|
| **Party** (parties and relationships) | user/customer/lead/partner/supplier, people and companies, departments, "on behalf of" | one party (person, organization, unit), many roles; relationships as separate entities with roles on both sides | `references/party.md` |
| **Availability** | double bookings, servicing/downtime, time blocks, "is it free?" | one contract block/release/disable; a time variant (segments) or a simple one (a block "now" with expiry) | `references/availability.md` |
| **Quantity / Money** | numbers with a unit or currency, rounding, splitting amounts | a value object: value + unit/currency, arithmetic only for compatible units, explicit rounding | `references/quantity-money.md` |
| **Product** | catalog, variants, serial numbers, batches, feature columns | type vs instance vs batch vs offer item; a tracking strategy; features as data with constraints | `references/product.md` |
| **Accounting** | balances, points, limits, settlements, reversals, "where does this balance come from?" | accounts, debit/credit entries, transactions balancing to zero, reversals instead of edits, posting rules | `references/accounting.md` |
| **Pricing** | price lists, interest, fees, promotions in `if`s | named calculators with a type, parameters and a description; a new rate = data, a new way of computing = a new type | `references/pricing.md` |
| **Configurator** | options with dependencies "not together / only together / one of" | declarative rules + a configuration process + a SAT solver checking possible completions | `references/configurator.md` |
| **Waitlist** | limited supply, a queue of candidates, priorities | a list with capacity, FIFO or priority; "resource released → next from the list" | `references/waitlist.md` |
| **General assignment** | assigning tasks to resources with different features | a multidimensional knapsack problem: maximum value while matching requirements to resources | `references/general-assignment.md` |
| **Planning / Parallelization** | stages with dependencies, "what can be done in parallel", critical path, penalties for delays | a graph of stages → topological sort into parallel levels; explicit and implicit dependencies (a shared resource); a schedule | `references/planning.md` |
| **Geographic Location** (locations, areas, addresses) | delivery zones, sales regions, the address "as of the invoice date", city/street columns | the location separated from the name, the area role and the address; a containment hierarchy; codes from registers as attributes | `references/geography.md` |
| **Resource / Service** (resources, assets, services) | machines, vehicles, customer equipment, "a service with a response time", service catalog | asset type vs instance with a life cycle; a customer-facing vs a technical service; the service offer and catalog | `references/resource-service.md` |
| **Activity / Process** (procedures, activities, work orders) | checklists, "how it should be" vs "what was done", working time, abandoned tasks | the procedure (template) vs the actual activity; the work order, party assignments, action states | `references/activity-process.md` |
| **Agreement** (agreements, terms, amendments, orders) | amendments from a date, a framework agreement and orders, "what was in force on day X" | request → quote → agreement with items and terms → orders; periods of validity and a second date range | `references/agreement.md` |
| **Document** (documents, versions, retention) | versions and signatures, "what exactly did we send", retention period, archive | the logical document vs an immutable version vs a copy in a format; integrity evidence; classification and retention | `references/document.md` |
| **Production / Supply** (product, production, procurement) | recipes, BOM, batches from suppliers, batch recall, "what was this made from" | the product structure and the routing; the production order and its execution; batches and traceability events | `references/production-supply.md` |

**The algorithm underneath** (ddd-algorithm-recognition): Availability → interval overlap (an interval tree / an exclusion
constraint in the database) · General assignment → multidimensional knapsack / assignment · Planning → topological sort, critical
path · Configurator → SAT/CSP · Waitlist → a priority queue · Pricing, Accounting → transformations (no algorithm).
The archetype gives **the model**, the algorithm — **the engine** enclosed behind the archetype's interface.

Archetypes combine: Product uses Quantity, Pricing returns Money, Waitlist works with Availability,
General assignment plans and Availability blocks, Accounting posts the financial effects.

The new archetypes combine with the existing ones: Agreement points to a price list (Pricing) and the parties (Party), and its effects
are posted by Accounting; Document is the carrier and evidence of an agreement; Production / Supply uses Product and Quantity, consumes
resources (Resource / Service) in activities (Activity / Process) planned by Planning; Geographic Location gives
Party its addresses, and Pricing — its zones. The last six archetypes are based on classic data model patterns
(Hay, Silverston, Fowler) and standards — sources with a verification date are at the end of each file.

## Archetypes in layers and technologies
This skill says **what** to model. The shape of the archetype in individual layers (domain, edge, integration, read, UI),
hard rules for the UI and signals in code of any language: `references/layers.md`. **How** to write it in a given language
and framework — the `lang-*` and `fw-*` skills (the "Domain concepts in …" section); combining per `core-skill-composition`.

Source of the archetypes from Party to General assignment: the "Archetypy Oprogramowania" (Software Archetypes) repository Software-Archetypes/archetypes (B. Słota, J. Pilimon, CC BY-NC-SA 4.0) — described here in our own words, without copying code.
Planning, the optimization/simulation section and the "in code" notes: based on an analysis of the sample SmartSchedule system from the Domain Drivers course (github.com/DomainDrivers/dd-typescript, a repo without a licence — only conclusions in our own words).
Sources of the six new archetypes (Geographic Location, Resource / Service, Activity / Process, Agreement, Document,
Production / Supply): D. C. Hay, L. Silverston, M. Fowler, J. Arlow and I. Neustadt, and the ISO, IEC, OMG, GS1
and TM Forum standards — verified by search on 2026-10-17, described in our own words; the list is in the "Sources" section of each file.
