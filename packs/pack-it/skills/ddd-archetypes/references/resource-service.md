# The Resource / Service archetype — mapper (resources, assets, services, service catalog)

> **Contents:** Fit test · Model (the essence) · Questions · Mapping steps · Decisions to check (R/A/X) · Result format · Patterns and pitfalls · Quality check · Example (shortened)

It turns requirements about **things and capabilities an organization has at its disposal or provides** (machines, equipment, vehicles,
technicians, licences, technical services) into a model: the resource type and instance, the asset life cycle, the service as a capability, the service
catalog and the assignment of a resource to work. The effect: a resource is neither "a product row" nor "a calendar", and a service is not
confused with a commercial offer. The common protocol: `SKILL.md` → "Mapper — the common protocol".

## Fit test
**The core question:** *are we modelling things and capabilities the organization has at its disposal or provides — regardless of
how it sells them?* Yes → it fits. If the key question is "what do we sell and for how much" → Product / Pricing.

| Signal in the requirements | Fits? |
|---|---|
| "a register of machines / vehicles / equipment", "the service history of a device" | ✅ an asset with a life cycle |
| "a service catalog", "service X available to customers of group Y" | ✅ a service and a service offering |
| "a service consists of technical services / sub-services" | ✅ a customer-facing vs a technical service |
| "a technician and a tool assigned to an order" | ✅ assigning a resource to work |
| "consumables (filters, parts)" | ✅ if it is a resource; a quantity balance → Quantity / Accounting |
| "a commercial offer, variants, bundles for sale" | ❌ → Product (and Pricing) |
| "is the room/technician free on Tuesday?" | ❌ → Availability |
| "whom to assign to minimize travel cost?" | ❌ → General assignment |
| "depreciation, book value" | ❌ → Accounting |
| "a penalty for exceeding the response time" | ❌ a term of the agreement → `agreement.md` |
| "inspection steps, execution, working time" | ❌ → `activity-process.md` |
| "a resource that gets booked" | ⚠️ borderline |

**Borderline cases:**
- *A booked resource* — the existence and the life cycle alone are Resource; the question "free on a date" and the block are Availability.
  Usually both archetypes at once, with a clear split: Resource says **what it is**, Availability **when it is available**.
- *Service = product?* — if the requirement concerns what the customer buys (a name, a price, variants), it is Product; if it concerns what
  the organization **can perform** and what it consists of — Service. One service is sometimes the basis of many products.
- *A customer's asset vs one's own asset* — a customer's lift that we service is an object of work for us, not our fixed
  asset; the model must distinguish the owner (Party) from the user and from the servicer.

## Model (the essence)
Below is the factory's modelling reasoning; the sources in the `## Sources` section confirm only the facts indicated there.

- **Resource type vs instance** — the type describes a class (a lift model, the "SEP electrician" qualification), the instance a specific item
  with a serial number, a location and a state. The type/instance convention is known from the pattern literature, but applying it to
  resources is our conclusion `[assumption]`.
- **A fixed asset with a life cycle** — purchase → operation → servicing → withdrawal. The asset's state is a state machine with a history
  of events (handover, repair, inspection), not one `status` field. According to ISO 55000:2024 an asset is an item or entity that has
  potential or actual value to an organization; **the book value** is computed by Accounting, it is not here.
- **A consumable vs a durable resource** — this is our conclusion, not a split attributed to the pattern authors. Durable: there is an instance,
  it comes back after use, it has a history. Consumable: the quantity and consumption count (→ Quantity / Accounting). The same type is sometimes one
  and sometimes the other depending on the context (a lent tool vs a disposable one) — decide per type.
- **A service as a capability** — a service is something the organization can deliver, not a thing to put on a shelf. In the TM
  Forum SID model a service visible to the customer (CustomerFacingService, it realizes a product) is distinguished from a technical service hidden
  from the customer (ResourceFacingService); an example from SID: VPN is a CFS, BGP is an RFS; there are also the CFSSpec and RFSSpec specifications.
  The conclusion: a customer-facing service consists of technical services, and these rely on resources.
- **Three concepts that must not be merged** (GB922, partly): the product specification (the design), the offering (the market presentation),
  the product in use (the instance at the customer). The details of the relationships between them are not confirmed here `[unverified]`; in the model
  keep three separate entities and ask which one a given requirement concerns.
- **The service offering and the service catalog** (ITIL 4, a paraphrase): a service offering is a formal description of one or more services for
  a defined group of consumers (it may include goods, access to resources, service actions); a service catalog is structured
  information about services and offerings, tailored to the consumer. The catalog is therefore **a view**, not a new sales entity.
- **Assigning a resource to work** — a separate entity connecting a resource (equipment, a person) with work, with a period and a role. In
  Silverston's data models there are fixed asset assignments and assignments of assets to parties; Fowler describes the Resource
  Allocation pattern. We do not attribute the consumable/durable split to either of them.
- **SLA** (e.g. a 4 h response time) is a term of the agreement (`agreement.md`); the service only **points to** what it concerns.

## Questions
**A — standard decisions:**
- What is the **type** and what is the **instance** (serial number, location, owner)? Which instances are our own and which the customer's?
- Which resources are **durable** and which **consumable**? Who keeps the quantities (Quantity)?
- What **life cycle stages** exist and who may change them (purchase, commissioning, servicing, withdrawal)?
- Is there a split **customer-facing service** vs **technical service**? What does a service consist of (sub-services, resources, qualifications)?
- Does the **service catalog** have different views for different consumer groups?
- Can a resource be assigned to work **in parallel** (one technician – two orders)?

**B — gaps** (examples):
- resource substitutability (a substitute instance) · resource hierarchy (part – whole) · location and moving ·
  qualifications required for operation · versions of the service specification · dependencies between services · withdrawing a service
  from the catalog with existing instances · assignment history (audit) · technicians' personal data (GDPR).

## Mapping steps
1. **Resource inventory** — a list of types and instances; the owner, the user, the servicer (Party).
2. **Durable vs consumable** — a decision per type; refer consumables to Quantity / Accounting.
3. **Life cycle** — states, transition events, who changes them; history as events.
4. **Services** — the customer-facing service, technical services, dependencies on resources and qualifications.
5. **Offering and catalog** — who the consumer of the offering is, what catalog views; the interface with Product (what is sold).
6. **Assignments** — resource ↔ work (role, period, exclusivity); the interface with Availability and `activity-process.md`.
7. **Boundaries** — SLA → `agreement.md`, depreciation → Accounting, optimal assignment → General assignment.

## Decisions to check (R/A/X)
Type vs instance · the asset owner (own/customer's) · durable vs consumable · life cycle states · customer-facing vs
technical service · service composition · catalog views · parallel assignment · substitutability · withdrawing a service with active instances.

## Result format
```markdown
# Resource / Service model: <area>
## Resources             — | Type | Instance (key) | Durable/consumable | Owner | Location |
## Asset life cycle      — | State | Event | Next state | Who changes it |
## Services              — | Service | Level (customer-facing / technical) | Consists of | Requires resources/qualifications |
## Offering and catalog  — | Service offering | Consumer | Services in the offering | Catalog view |
## Assignments           — | Resource | Work | Role | Period | Exclusivity |
## Concept mapping       — | Domain concept | Archetype element | Justification |
## Unmapped concepts
## Integrations          — | Event | From / to archetype | Reaction |
## Decisions (R/A/X)     — | Decision | Source |
## Notes                 — assumptions (X), variable policy parameters, [unverified]
```

## Patterns and pitfalls
- Merging the service with the product: a change of price or bundle should not touch the description of the capability. Three concepts – three entities.
- A `status` field instead of life cycle events loses the service history, which is usually a value in itself.
- A resource with a built-in calendar: availability is a separate archetype (Availability); Resource holds the identity and the state.
- A technician as "a user account" instead of a party and a resource: permissions (authorization outside the archetype) are not qualifications.
- An assignment as a `technician_id` field on the order makes many technicians, roles and change history impossible.
- An SLA written into the service – it is a term of the agreement and may differ between customers; insert it as a parameter from `agreement.md`.
- Value and depreciation in the asset object – these are accounting entries (Accounting), not resource attributes.

## Quality check
- [ ] every resource has a type, an instance and an owner; durable/consumable settled
- [ ] the life cycle has states, events and history
- [ ] the customer-facing and the technical service are separated (or consciously merged — the decision recorded)
- [ ] the offering, the specification and the instance are not merged; the catalog is a view
- [ ] assignments are a separate entity with a role and a period
- [ ] SLA, depreciation, availability and assignment referred to the appropriate archetypes
- [ ] the mapping table and "Unmapped concepts" present; no material (X)

## Example (shortened)
**Input:** `[example]` "A company servicing lifts. The lifts belong to customers, each has a factory number and an inspection history.
Technicians have qualifications and measuring tools. We sell the service "maintenance with a 4 h response time"."

```markdown
## Resources — | lift type | lift factory no. (inst.) | durable | customer (Party) | building address |
   | technician | person (Party) | durable | company | — | · | meter | instance | durable | company | warehouse |
## Life cycle — lift: in operation → in servicing → disabled → withdrawn (events with a date)
## Services — | maintenance | customer-facing | periodic inspection + breakdown response | "lifts" qualification |
## Offering — | maintenance 4 h | customers with a framework agreement | maintenance | B2B catalog view |
   response time 4 h → a parameter from `agreement.md`, not a service attribute
## Assignments — | technician + meter | order (activity-process) | performer | order period | no |
## Unmapped — the technician's free slot (→ Availability) · choosing the nearest technician (→ General assignment) ·
   the subscription price (→ Pricing) · the penalty for exceeding 4 h (→ Agreement)
## Decisions — the customer's lifts are not the company's assets (R) · technician = durable resource (X, small) · withdrawing the service
   with active agreements (X → ask)
```

## Sources
Accessed 2026-10-17.
- ISO 55000:2024 "Asset management — Vocabulary, overview and principles" (ed. 2, replaced the 2014 edition) — **a standard, primary**; we take the concept of an asset as an entity with value for the organization. We know the definition from secondary descriptions, so we paraphrase it.
- TM Forum, Information Framework (SID), Browsable SID R20.0 — **primary**; the distinction CustomerFacingService and ResourceFacingService, the CFSSpec and RFSSpec specifications, the VPN/BGP example.
- TM Forum GB922 Product (the newest found v24.5.0, approved 7.03.2025) — **primary, partly confirmed**; we take only three concepts: the product specification, the offering, the product in use; the relationships between them `[unverified]`.
- AXELOS, ITIL 4 — **primary (a paraphrase)**; the definitions of the service offering and the service catalog. We do not take the definitions of "service" and "SLA" from this family (not confirmed).
- L. Silverston, "The Data Model Resource Book", Vol. 1 Revised Edition, Wiley 2001, ISBN 978-0-471-38023-8 — **a book; table of contents confirmed at O'Reilly (secondary)**; the table of contents of the chapter on work requirements partly confirmed (among others Fixed Asset Assignments, Party Fixed Asset Assignments). Vol. 2 (Wiley 2001, ISBN 978-0-471-35348-5) is industry models, including professional services and telecommunications.
- M. Fowler, "Analysis Patterns: Reusable Object Models", Addison-Wesley 1997 (the author gives 1996), ISBN 0-201-89542-0 — **a book; table of contents confirmed at the publisher (InformIT)**; ch. 8 "Planning" contains the Resource Allocation pattern. The consumable/durable split was not confirmed in it.
- D. Hay, "Enterprise Model Patterns: Describing the World (UML Version)", Technics Publications, ISBN 978-1-935504-05-4 (year 2011, partly confirmed) — **a book; table of contents confirmed at the publisher**; ch. 6 "Assets". The content of the chapter (asset type vs asset) not confirmed; this is the type/instance convention `[assumption]`.

Described in our own words; the content of books and standards was not quoted.
