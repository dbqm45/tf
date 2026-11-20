# Assets and services — what the organisation owns, operates and delivers

## When it applies
- Signal: things and capabilities the organisation has, operates or delivers, independent of the commercial offer —
  vehicles, machines, rooms, licences, technicians' capabilities, IT services.
- Not this: the catalog entry a customer buys (→ product definitions) or the act of performing work (→ work execution).

## Core shape
- **Asset class** (model "Compressor K-40") vs **individual asset** (serial number, location, condition).
- Three separate party links per asset: **owner**, **user** (operator), **maintainer**. A customer's equipment that we
  service is a *work object* for us, not our asset.
- **Lifecycle with an event history**: acquired → commissioned → in operation ↔ in service/repair → retired; each event
  dated with actor and reason — not one status column.
- **Durable resources** (returned after use, have history) vs **consumables** (quantity consumed, handled by quantities
  and the value ledger). The same class may be either in different contexts — decide per class.
- **Services as capabilities**: a customer-facing service is realised by internal / resource-facing services, which run
  on resources. This matches the customer-facing vs resource-facing service split of the TM Forum information framework
  (SID) [unverified: exact entity names in the current SID release].
- Keep apart: **product specification** (what can be sold), **market offering** (how it is offered: price, terms,
  channel), **product instance in use** (what this customer has now).
- **Service offering**: services described for a defined consumer group. **Service catalog**: a consumer-specific view
  over services and offerings — not an extra sellable thing.
- **Resource assignment**: its own entity — resource, work item, role, period, exclusivity. Not a `technician_id`
  column on the order.

## Rules
- Service-level commitments (response time, availability, penalties) are terms of a commitment and may differ per
  customer; the service only refers to them.
- Book value and depreciation are value-ledger entries.
- Availability over time is resource holds; optimal assignment is task selection.
- Qualifications ("certified for gas installations") are facts about a party, not permissions.

## Decisions to settle
- Substitutes (another compressor of the same class)?
- Part–whole hierarchies (a line made of machines, a machine of modules)?
- Location moves and their history?
- Qualifications needed to operate or service a class?
- Versioning of service specifications; dependencies between services.
- Retiring a service that still has active instances.
- Audit, and personal data of technicians.

## Belongs elsewhere
- Prices of service offerings → price calculation; SLA terms → commitments; the work done → work execution.

## Traps
- An `assets` table with `status`, `owner`, `location` overwritten in place — no history of who had it when.
- The customer's device stored as our asset and depreciated.
- A service catalog modelled as a second product catalog with its own prices.
- `assigned_technician` column — no period, no role, no second technician.

## Worked example
Requirement: an HVAC company owns service vans and tools, maintains customers' heat pumps, sells "Premium Care"
(24 h response) and "Basic Care" (72 h).
- Our assets: van `VAN-07` (class Transit L2, owner = company, user = technician T. Nowak, maintainer = fleet
  partner); its lifecycle events: acquired 2024-05, in service 2026-02-10 – 02-12.
- Customer's heat pump `HP-SN-5512`: a work object (owner = customer party), not our asset.
- Customer-facing service *Heat pump care* realised by resource-facing *Diagnostics*, *Refrigerant handling* (needs a
  certified technician) — running on vans, tools and people.
- Offerings *Premium Care* and *Basic Care* differ by the response-time term (commitments); the customer portal shows a
  service catalog view with only the offering the customer has.
- A visit creates a resource assignment (T. Nowak, visit V-331, role *lead technician*, 2026-05-04 09:00–11:00, exclusive).
