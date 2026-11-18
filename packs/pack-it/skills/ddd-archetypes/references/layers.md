# Archetypes in the layers of a system (independent of technology)

An archetype is a business model. In each layer it takes a different shape — the same knowledge, different responsibilities.
The idioms of a specific language and framework come from the `lang-*` and `fw-*` skills (the "Domain concepts in …" section).

## What lives where
| Layer | The archetype's role | Concepts from the glossary |
|---|---|---|
| **Domain (server)** | the source of truth for rules and invariants | aggregate, value object, state machine, policy, event, repository |
| **Module edge (API, facade)** | a small, stable contract of the archetype (e.g. block/release/disable), DTO ↔ domain translation | operation result, module, integration event |
| **Integration** | the archetype's Published Language between contexts | events (notification / state transfer), a read model on the receiver's side |
| **Read** | consolidated views (calendar, entry history, catalog) | read model |
| **UI** | reflecting the shape and states; hints, not decisions | value object (formatting, input), variants, read model, request state machine |

## Hard rules for the UI (in every framework)
1. **Prices, discounts, interest and totals to pay are computed by the server.** The UI shows the price and its description; a local calculation only as
   a preview marked "approximate" and never sent as the amount to pay.
2. **Resources people compete for are not booked optimistically.** A `pending` state → the result from the server; a conflict is
   a normal result. Optimistic UI only for operations without competition.
3. **Amounts never on a floating-point type** in calculations; one formatter.
4. **Rules come as data** (feature constraints, configurator rules, availability) — the UI does not invent them.
5. In the UI **the language of the business** ("Customer", "Appointment"), not archetype names ("Party", "Blockade").

## Signals in code (any language)
| Signal | Likely archetype |
|---|---|
| an amount as `float/double/number` + a separate currency field, rounding in many places | Money / Quantity |
| the value and the unit as separate texts, the unit appended on display | Quantity |
| `isCompany`, `isCustomer`, person and company fields in one structure, separate User/Customer/Lead classes for the same party | Party |
| `isReserved`, `inMaintenance` flags, manual checking of date overlap in many places | Availability |
| hard-coded feature columns/fields, a separate form or class per product type | Product |
| chains of `if`s enabling/disabling options | Configurator |
| discounts, interest, fees in the `if`s of services or views | Pricing |
| a `balance` field updated directly, a "correction" overwriting the amount | Accounting |
| the order of those waiting computed ad hoc | Waitlist |
| manual matching of resources to tasks | General assignment |

## Should the archetype be applied in a given layer?
Yes, when: the concept appears in many places of the layer and must be consistent; there are rules giving immediate feedback;
errors are costly; the other side (e.g. the backend) already models the archetype and the contract returns its shape.
No, when: it is one simple CRUD screen/endpoint, the other side does not know the concept (analysis first), or
an "archetype framework" would be created for one case.

## How archetype modules talk to each other
| Way | When | Risk |
|---|---|---|
| **a synchronous facade** (e.g. assignment calls "block" in availability) | an immediate "did it succeed?" answer is needed | the temptation of one transaction across two modules — a conscious compromise, record it in an ADR; eventually a saga/outbox |
| **private vs published events** | private inside the module; published = the Published Language at the edge | publishing internal events ties the receivers to the sender's model |
| **an ACL as a pure translating function** | data from a legacy / external system | the translation must not leak further than the module's input type |
| **a saga / process manager** | reacting to events from several modules (e.g. monitoring project risk) | the process state must be stored; the steps explicit |
Guard the import boundaries between modules with a linter rule or an architecture test (the equivalent of ArchUnit tests) — not only by convention.
Avoid dependency cycles between modules (A → B → A); move shared types to a shared kernel.
