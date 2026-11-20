---
name: ddd-archetypes
description: Use when a business requirement is a recurring modelling problem — money, ledgers, pricing, parties, places, products, bookings, waitlists, contracts, documents.
argument-hint: "[area] [requirements]"
metadata:
  review: "2027-05-20"
  catalog: "Use when you design, review or refactor a business domain and a requirement is a well-known modelling problem with a reusable model (an archetype) — quantities and money with currencies and rounding, balances and ledgers (points, credits, leave days, stock), prices and fees from changing rules, parties with roles and relationships, locations, addresses and zones, product definitions vs items vs lots vs listings, option compatibility in configurators, exclusive holds and double booking, waiting lists, choosing and staffing tasks, dependent stages and the critical path, assets and services, procedure vs actual work, contracts with terms and amendments, quotes and orders, documents as evidence with retention and legal hold, bills of materials and lot traceability; also archetype smells such as float money, role flags and balance columns. Not for purely technical domains such as device control loops, configuring a bought package, the context map between modules (ddd-context-mapping), strategic subdomain classification (ddd-strategic-analysis), aggregate and value object design in general (ddd-tactical-design), design patterns and principles in code (eng-design-principles), subscription mechanics with a payment provider (be-billing-subscriptions) or repository documentation (docs-tech-writing)."
  keywords: "archetyp, archetypy biznesowe, jak zamodelować, typ pieniędzy, kwota i waluta, zaokrąglenia, raty, kurs walut, jednostki miary, saldo, saldo punktów, punkty lojalnościowe, program lojalnościowy, kredyty api, dni urlopu, księgowanie, księga, podwójny zapis, storno, korekta salda, wygasanie punktów, cennik, taryfa, rabat, prowizja, odsetki, kara umowna, progi cenowe, klient i dostawca, kontrahent, strona, role, relacje między firmami, spółka zależna, struktura organizacyjna, adres, adresy, strefa dostaw, kody pocztowe, gminy, współrzędne, produkt, katalog produktów, warianty, partia, numer seryjny, konfigurator, opcje wykluczające się, rezerwacja, podwójna rezerwacja, dostępność zasobu, blokada w koszyku, lista oczekujących, lista rezerwowa, obsada zleceń specjalistami, które zlecenia przyjąć, harmonogram etapów, ścieżka krytyczna, zależności etapów, zasoby i usługi, katalog usług, zlecenie pracy, karta pracy, ewidencja godzin, procedura, umowa, aneks, oferta, zamówienie, umowa ramowa, obowiązywało w dniu, dokument, wersja dokumentu, retencja, okres przechowywania, blokada prawna, receptura, BOM, zlecenie produkcyjne, genealogia partii, wycofanie produktu, śledzenie partii, archetype, business archetype, domain model pattern, how to model, money type, currency rounding, instalments, exchange rate, unit of measure, balance, loyalty points, api credits, ledger, double entry, reversal, expiry, pricing rules, tariff, discount, fee, interest, penalty, party role, customer and supplier, subsidiary, org hierarchy, address model, delivery zone, postal codes, product catalog, variants, lot, serial number, bundle, configurator, incompatible options, booking, double booking, availability, cart hold, waitlist, waiting list, staffing projects, which projects to accept, critical path, task dependencies, service catalog, work order, timesheet, contract, amendment, quote, order, framework agreement, as of date, document versions, retention, legal hold, bill of materials, production order, lot genealogy, recall, traceability"
---

# Business archetypes — recognise the recurring problem, reuse the model

Many business requirements are old problems in new clothes: a balance with history, a price from rules, a person in
several roles, a resource nobody may book twice. For each such problem a reusable model (an **archetype**) exists:
its entities, invariants, boundaries and known traps. The agent's job: recognise the archetype, adapt the minimum the
requirements need, and push everything business-specific (deadlines, priorities, rates, limits) into **policies** that
hand values in as **parameters** — the core model applies them mechanically.

An archetype is a thinking aid at the strategic and tactical level, not a code template. It fits best in well-understood
domains (commerce, finance, logistics, healthcare, telecom, energy). Warning signs that one is missing: a model growing
flags and "what if X is also Y" branches, or several products asking the same core question — then model that shared
capability once.

**Skip it** for purely technical domains (a device controller, a compiler, a cache), for configuring an off-the-shelf
product the team cannot reshape, for patch-only legacy without a modernisation plan, and for a single trivial CRUD screen.

## Router — which archetype
Answer the signal question; "yes" points to the reference file. Read only the files you need.

| Signal question in the requirements | Archetype | Reference |
|---|---|---|
| Is the number meaningless without a unit or currency? | quantity and money | `references/quantities-and-money.md` |
| "How much X does S have, and why?" — a number with a history | value ledger | `references/value-ledger.md` |
| Is the amount computed from rules business staff should change without code? | price calculation | `references/price-calculation.md` |
| Does one person or company appear in several roles or linked to others? | parties and relationships | `references/parties-and-relationships.md` |
| Does a decision hinge on a position or membership in an area? | places and zones | `references/places-and-zones.md` |
| Which "product" is meant — a type, a physical item, a lot, a listing, a service run? | product definitions | `references/product-definitions.md` |
| Does picking one option change which others are allowed? | option constraints | `references/option-constraints.md` |
| Is a resource, for an interval, either free or held by exactly one holder? | resource holds | `references/resource-holds.md` |
| When a unit frees up, must someone choose which applicant gets it? | waiting list | `references/waiting-lists.md` |
| Not everything fits, resources differ, tasks have different value? | task selection | `references/task-selection.md` |
| Do work items need others' output, so order and parallelism must be decided? | stage scheduling | `references/stage-scheduling.md` |
| Things or capabilities the organisation owns, operates or delivers? | assets and services | `references/assets-and-services.md` |
| Does "how it should be done" vs "what really happened" matter? | work execution | `references/work-execution.md` |
| Do parties commit to terms that hold for a time and change? | commitments | `references/commitments.md` |
| Must you prove which content existed or was sent, and keep it until a date? | evidence documents | `references/evidence-documents.md` |
| Made from inputs or passed along a supply chain, with origin questions? | production traceability | `references/production-traceability.md` |

Layers, module communication, UI rules and code smells across all archetypes: `references/across-layers.md`.
Every archetype file has the same sections: When it applies · Core shape · Rules · Decisions to settle ·
Belongs elsewhere · Traps · Worked example.

## Procedure
1. **Requirements.** Take them from the prompt, the conversation or project docs (the requirements
   and domain folders under docs/project). None anywhere → ask once for a domain description; do not invent rules.
2. **Fit test first.** Run the signal question of the candidate archetype. No fit → say so with the reason, name a
   better-fitting archetype in one line if one is obvious, and stop. Borderline → one deciding question.
3. **Ask only what is open.** From "Decisions to settle" pick the ones the requirements leave open, plus standard
   capabilities they do not mention. Offer them as design options, ≤4 questions per round; "it varies by case" is a valid
   answer and becomes a parameter supplied by a policy. Without a human (a sub-agent, CI): do not ask, list the open
   questions and mark the decisions **assumed**.
4. **Concept mapping.** A table *domain term → model element → why*, plus **Unmapped concepts** (none is a valid
   result). An unmapped term often points to another archetype or to the core domain.
5. **Archetype steps.** Apply "Core shape" and "Rules" of the file; keep only what the requirements need, list the rest
   as possible extensions.
6. **Provenance of decisions.** Mark each decision **R** (stated in requirements), **U** (answered by the user) or
   **A** (assumed). Low-impact technical assumptions go to notes; an assumption that changes business behaviour must be
   confirmed before handover.
7. **Write the model** to `docs/project/02-domain/archetypes/<archetype>-<area>.md` (or the project's domain folder).

### Result format
```
Archetype: <name> | Fit: yes|no|partial — <one-line reason>
## Summary            (3–5 lines: what is modelled, the key invariant)
## Concept mapping    | Domain term | Model element | Why |   + Unmapped concepts
## Model              entities, value objects, invariants, operations with their results
## Decisions          | Decision | Choice | R/U/A |
## Boundaries         what goes to policy, authorisation, other archetypes
## Open questions     + Next steps
```
Use the business's words in the model; archetype names stay in the design document, not in UI text.

## Rules that hold for every archetype
- **Policies outside, parameters in.** Anything that varies (expiry deadline, priority, rounding mode, limit, choice of
  price list, hold duration) is evaluated by a policy and passed to the operation as an argument.
- **Authorisation outside.** The model records what happened and enforces structural invariants, including unconditional
  numeric limits. "May this actor do it now, for this reason?" is answered by the application or policy layer before the call.
- **Levels of responsibility:** capability (what is possible) → operations (daily actions) → policies (rules that configure
  operations) → decision support (analytics, recommendations). Each level depends only on those below; an operation never
  names a policy.
- **One module per archetype** behind a small stable interface (a deep module, eng-module-depth). Algorithms (interval
  overlap, knapsack/MIP, topological sort and critical path, SAT/CSP, priority queue) stay hidden behind it; pricing and
  ledgers are plain transformations.
- **Operation results** are success, no-op (duplicate, nothing changed) or a refusal with a reason; publish events only
  for real changes.
- **History is appended, not overwritten**: reversals, new versions, dated validity, snapshots on documents.
- **Build the minimum**; the rest is a listed extension, not code.

## How archetypes compose
- Product definitions use quantities; price calculation returns money; the ledger posts the financial effects of
  contracts, prices and events.
- A waiting list reacts to release events from resource holds and places a hold during an offer.
- Task selection plans, resource holds commit; stage scheduling decides order, task selection decides who, holds decide when.
- Commitments reference parties and price lists; evidence documents prove them; the ledger posts their effects.
- Production traceability uses product definitions, quantities and resources in work that is scheduled.
- Places supply addresses to parties and zones (as inputs) to price calculation.

## Example
Input: "Our developer platform gives each workspace 10,000 API credits a month; customers can buy top-ups valid a year;
unused monthly credits vanish at month end; top-ups can be refunded. How do we model the balance?"

Output (shortened):
- `Archetype: value ledger | Fit: yes — "how many credits does workspace W have and why" is a number with a history.`
- Accounts per workspace and source: `monthly-grant` and `top-up` (unit: credit, policy: no negative balance), plus
  counter accounts `grant-pool`, `sold-credits`, `consumed`, `forfeited`.
- Monthly grant = transaction *grant-pool → monthly-grant 10,000*, validity [1st of month, 1st of next month).
  Top-up = *sold-credits → top-up 5,000*, validity 1 year, `source_event_id` of the payment unique.
- Usage draws down **earliest expiry first** (a parameter; other options FIFO, source priority); each usage event's id is
  unique → a replayed event is a no-op.
- Month end posts the remainder *monthly-grant → forfeited*, visible in analytics, not a silent filter.
- Refund = a reversing transaction referencing the purchase. Decision **U**: if 3,000 of 5,000 are already used, refund
  only the unused 2,000 (no cascade into past consumption).
- Each entry has `recorded_at` (now, immutable) and `effective_at` (may be backdated by a correction).
- Open: may admins grant goodwill credits (a new posting rule, configuration only)? Caps on accrual speed?
- Rejected: a `credits` column updated in place — no history, races, no answer to "why".

More worked examples sit at the end of each archetype file.

## Delegation
Language idioms (value objects in Java, TypeScript, …) → the language skills (lang-*); the project's framework → fw-*.
Strategic fit and subdomains → ddd-strategic-analysis; context maps → ddd-context-mapping; aggregates in general →
ddd-tactical-design; deeper modelling sessions → ddd-deep-modeling; recognising the algorithm behind a rule →
ddd-algorithm-recognition; database mechanics (exclusion constraints, outbox) → be-database, be-messaging-outbox.

## Sources
Standards and literature cited in the archetype files, each with its access or edition date there; summary:
- ISO 4217 currency codes and minor units; ISO 3166 country and subdivision codes (iso.org, accessed 2026-11-20).
- RFC 7946 GeoJSON (IETF, August 2016); EPSG:4326 axis order (EPSG registry, accessed 2026-11-20).
- ISO 15489-1:2016 records management; Regulation (EU) No 910/2014 (eIDAS); Regulation (EC) No 178/2002, Article 18.
- GS1 EPCIS 2.0 (GS1, 2022); IEC 62264 / ISA-95; OMG BPMN 2.0, CMMN 1.1, DMN.
- E. Evans, *Domain-Driven Design* (Addison-Wesley, 2003) — responsibility layers; M. Fowler, *Analysis Patterns*
  (Addison-Wesley, 1997) — quantity, accounts, party, time-bounded facts.
