# The Geographic Location archetype — mapper (locations, areas, addresses)

> **Contents:** Fit test · Model (the essence) · Questions · Mapping steps · Decisions to check (R/A/X) · Result format · Patterns and pitfalls · Quality check · Example (shortened)

It turns requirements about **place** (a country, a municipality, a delivery zone, an address, coordinates) into a model in which the location is
a separate entity, and the name, the area role, the address and the geometry are separate pieces of information that change at different rates.
The effect: the same area has many names and languages, it is sometimes a delivery zone and a tax jurisdiction at once, and an invoice remembers the address
as of the sale date.
The common protocol (questions, "It depends", the R/A/X check, recording): `SKILL.md` → "Mapper — the common protocol".

## Fit test
**The core question:** *does the answer depend on WHERE something is or which area it belongs to?*
Yes → it fits. The address is only text entered by the customer and is not used for decisions anywhere → a field in Party is enough.

| Signal in the requirements | Fits? |
|---|---|
| "we deliver to selected municipalities / postal codes", delivery zones | ✅ |
| country → voivodeship → county → municipality; "everything in this region" | ✅ |
| the same area under several names or in several languages (Gdańsk / Danzig) | ✅ |
| an address per the country's template (PL, DE), code validation | ✅ |
| an invoice, order or agreement with the address "as of the event date" | ✅ |
| a sales area, a tax jurisdiction, a service zone | ✅ |
| "who the recipient is, what phone and e-mail they have" | ❌ → Party (contact mechanisms) |
| "is there a free slot at this pickup point?" | ❌ → Availability |
| "how much does delivery to zone 2 cost?" | ❌ → Pricing (the zone is only a parameter) |
| "what courier route through 40 addresses?" | ❌ → General assignment (a routing algorithm) |
| map display, address search as an external service | ⚠️ borderline |

**Borderline cases:**
- *An external service (a geocoder, maps)* — the model stores the result and the identifier from the register; the search itself is
  an integration (ACL), not the archetype.
- *The address as a text field* — if nobody filters, validates or computes a zone, do not build a hierarchy "just in case".
- *A warehouse / pickup point* — the location yes, the stock level and free slots no (Product, Availability).

## Model (the essence)
The breakdown below is the factory's modelling conclusion; the sources in the "Sources" section confirm only what is described there.
### Location and name
- **GeographicLocation** — a point or an area on Earth with its own technical identifier (generated in the application).
  The type (country, administrative unit, locality, street, point) is a feature from a dictionary, not a separate class.
- **GeographicName** — a separate entity: the name, the language, the kind (official, colloquial, historical), the validity period. A location
  has 1..n names; a name is not a key and does not identify the area.
- **ExternalIdentifier** — an identifier from an external register: a scheme (e.g. ISO 3166-1, ISO 3166-2, TERC, SIMC, ULIC,
  postal code) + a value + a validity period. It is **an attribute from a register**, not a model key: registers change codes,
  merge and split units. One location may have many identifiers (one per scheme).

### Hierarchy and containment
- **Area containment** — the relationship "area A lies in B" as a separate record with a period (country → voivodeship → county →
  municipality; in DE other levels). Not a `parentId` in the location: there are sometimes several structures (administrative, postal, commercial),
  and boundaries change. Coverage is sometimes computed from containment or from geometry — the choice is a decision (A).
- **Sets of areas** — a zone is a set of areas (municipalities, postal codes) with a period, not a separate hand-drawn geometry;
  then a change to a municipality's boundary does not break the zone.

### Area role
- **AreaRole** — "this area plays role X for Y": a shop's delivery zone, a sales rep's sales area, a tax
  jurisdiction. A separate entity with a period and a role owner. The role is information about **use**; a rate, a limit or a price
  depending on the zone belong to Pricing or the rules layer, which get the zone as a parameter.

### Address
- **Address** — a description of a location according to **the country's template** (the order and the required elements differ: PL, DE, GB). The template
  is data (element, requiredness, postal code format), not an `if` in code. The address points to a location (e.g. TERC +
  SIMC + ULIC in PL) and has text fields for printing; one without the other is sometimes insufficient.
- **A party's address** — the contact mechanism belongs to Party (billing address, delivery address, uses). The boundary:
  Party knows *who* is reachable at which address; Geographic Location knows *what this address is* and *which areas
  it lies in*.
- **Frozen vs current address** — a document (order, invoice, agreement) holds **a copy** of the address from the moment of the event
  (a snapshot: text + a reference to the location with a date). A change of the customer's address does not rewrite history. The party's current
  address is a separate, changing state. The same applies to names: an invoice remembers the name as of the sale date.

### Geometry
- **Geometry** — a separate entity or a reference (a point, a polygon) in an agreed coordinate system, with a period and a source.
  Stored in GeoJSON with WGS 84 in decimal degrees; coordinates in the order **longitude, latitude**.
  **The axis pitfall:** the EPSG:4326 designation in many tools and databases assumes the order latitude, longitude — swapping
  the axes gives a point elsewhere in the world with no validation error. Fix the order in the contract and test on a known point.
- Containment computed from geometry (point in polygon) is a spatial algorithm behind an interface; the model stores
  the result and the date of the boundary version.

## Questions
**A — standard decisions:**
- Which countries and address templates do we support now (PL, DE), and which will be added? Is the postal code validated by format or by register?
- Is a delivery zone a set of municipalities, a set of postal codes, or a drawn polygon? What on a conflict (a code crosses municipalities)?
- Hierarchy from containment (records) or from geometry? How many levels are really needed?
- Does a document freeze the address in full (a copy), or a copy + a reference to the location with a date?
- Which external identifiers do we record and who updates them from the register (periodic import)?

**B — gaps** (examples): a change of municipality boundaries vs existing zones? · names in several languages on documents? · an address without
a street (a village)? · pickup points and parcel lockers as locations? · the area's time zone? · a zone disabled for holidays
(→ Availability)? · GDPR: a natural person's address vs retention (→ Party, `document.md`)?

## Mapping steps
1. **Locations** — every "place" from the requirements → a location type; separate names from identifiers.
2. **Names** — languages, kinds, periods; which name goes on the document.
3. **External identifiers** — scheme, value, register source, update frequency.
4. **Hierarchy** — containment relationships with a period; levels per country.
5. **Area roles** — delivery zone, sales area, jurisdiction; the role owner and period.
6. **Address** — a template per country (data), validations, the link to the location.
7. **The boundary with Party and documents** — the current address in Party; a copy in the document (the freezing event).
8. **Geometry** — is it needed, the coordinate system, the axis order, boundary versioning.

## Decisions to check (R/A/X)
countries and address templates · the source of the hierarchy (records vs geometry) · a zone as a set of areas vs a polygon · freezing
the address on a document · external identifiers and their updates · multilingual names · axis order · boundary versioning ·
code validation · who maintains the zones.

## Result format
```markdown
# Geographic Location model: <area>
## Concept mapping    — | Domain concept | Archetype element | Justification |
## Unmapped concepts
## Locations and names — | Location type | Names (language, kind) | External identifiers (scheme) | Notes |
## Hierarchy          — | Containment relationship | Levels | Period | Source (records/geometry) |
## Area roles         — | Role | Areas (set) | Role owner | Period | Parameter for Pricing/rules |
## Addresses          — | Country | Template (elements, requiredness) | Validation | Link to the location |
## Freezing on documents — | Document | What we copy | Freezing event |
## Geometry           — | System | Axis order | Versioning | Where computed |
## Decisions (R/A/X)  — | Decision | Source |
## Notes              — assumptions (X), edge cases, variable policy parameters
```

## Patterns and pitfalls
- **A postal code or a city name as a key** — codes and names change, one code covers several localities.
  A technical key, the code as an external identifier.
- **One `address` field in the order pointing to the customer's current address** — after a move, a historical invoice
  shows the new address. Freeze it at the moment of the event.
- **`if (country == "DE")` in address validation** — the template as data.
- **A zone as a hand-drawn polygon** next to municipality boundaries — they drift apart after boundary changes; a set of areas is more robust.
- **Mixing the role and the area** — "zone 2" is not a kind of location, only an area's role in the delivery context.
- **The coordinate axis** — the longitude/latitude order swapped; a contract and a test on a control point.
- **Outside the archetype:** "does the pickup point have a free slot?" (Availability), "how much for delivery?" (Pricing), "in what order
  to drive?" (General assignment). Authorization ("who may change a zone") lies in the application layer.
- **Variable policies as parameters:** delivery coverage depending on the season → the archetype gets a ready set of areas.

## Quality check
- [ ] the name, the external identifier and the technical key are three different things
- [ ] the hierarchy with a period, not a `parentId`; a zone as a set of areas (or a justified polygon)
- [ ] address templates as data; countries listed
- [ ] documents freeze the address; the current address only in Party
- [ ] the axis order and the coordinate system explicit (if there is geometry)
- [ ] the mapping table and "Unmapped concepts" present; no material (X)

## Example (shortened)
**Input:** "An online shop delivers in Poland and Germany. In PL the delivery zones are sets of municipalities, in DE sets of postal
codes. The invoice must show the buyer's address as of the sale date. Gdańsk is sometimes entered as Danzig."

```markdown
## Concept mapping
| municipality, country | GeographicLocation (type: administrative unit) | the TERC identifier as an attribute |
| Gdańsk / Danzig | GeographicName (pl, de, official / colloquial) | one location, two names |
| delivery zone | AreaRole over a set of areas | period of validity |
| buyer's address | Address per the country's template | PL and DE: two templates (R) |
## Area roles
| DELIVERY_PL_1 | set of municipalities | Shop | from–to | parameter `zone` for Pricing |
| DELIVERY_DE_1 | set of postal codes | Shop | from–to | parameter `zone` |
## Freezing on documents — invoice | a copy of the buyer's address + a reference to the location | issuing (R)
## Decisions
| the PL zone as a set of municipalities | R |
| DE postal code: format or register | A: format to start with |
| a change of municipality boundaries vs zones | X → hot spot |
## Unmapped concepts — the delivery price (→ Pricing), the buyer and their phone (→ Party), the courier and the route (→ General assignment)
```

## Sources
Accessed 2026-10-17.
- Hay, "Enterprise Model Patterns: Describing the World (UML Version)", Technics Publications, 2011 (ISBN 978-1-935504-05-4) —
  we take: the chapter "Geographic Locations" covers the location, geographic names and roles; the chapter on people and organizations
  is separate. Rank: primary (the publisher's table of contents). We do not attribute the hierarchy of areas to this book.
- Silverston, Agnew, Vol. 3, "Universal Patterns for Data Modeling", Wiley, January 2009 — we take:
  the Geographic Boundary pattern linked to the postal address and the chapters on roles, hierarchies, contact mechanisms. Rank:
  secondary for the content of the pattern (the O'Reilly description).
- ISO 3166-1:2020 (country codes) and ISO 3166-2:2020 (subdivision codes) — we take: identifiers from a register as attributes.
  Rank: primary (iso.org).
- ISO 19160-1:2015, "Addressing — Part 1: Conceptual model" — we take: the address as a description of a location. Rank: primary (iso.org).
- ISO 19112:2019 — we take: spatial references through geographic identifiers, the conceptual schema of a gazetteer. Rank: primary.
- UPU S42 (International postal address components and templates) — we take: address templates per country as data. Rank:
  primary, but only partly verified; currency of the edition [unverified] (the newest found S42-8, 2017).
- RFC 7946, GeoJSON (August 2016) — we take: WGS 84, decimal degrees, the longitude–latitude order. Rank: primary.
- EPSG:4326 (WGS 84, the latitude–longitude axis per epsg.io) — we take: the difference in axis order as a pitfall. Rank: secondary.
- GUS, TERYT (eTERYT) (the Polish official register of territorial division): TERC, SIMC, ULIC — we take: the identifiers of units, localities and streets; an address coded TERC + SIMC +
  ULIC. Rank: primary.
- PRG and PRNG (GUGiK) and EMUiA (municipalities, geoportal.gov.pl) — we take: the registers of boundaries, names and addresses as import sources. Rank:
  primary, partly verified.
- The INSPIRE Directive 2007/2/EC (14.03.2007), Annex I — we take: geographic names, administrative units, addresses and coordinate
  systems as standardized data themes. Rank: secondary (a copy on legislation.gov.uk). Regulations only as context to be
  confirmed by a lawyer, not advice.

The breakdown into the name, the area role, the address and the geometry, and freezing the address on a document, are the factory's modelling conclusions, not theses of the authors.
Described in our own words; the content of books and standards was not quoted.
