# Places and zones — locations, names, hierarchies, addresses, coordinates

## When it applies
- Signal: some decision hinges on a position or on membership in an area (delivery possible? which tax jurisdiction?
  which sales rep? which tariff zone?).
- Not this: a free-text address used for no decision — a field on the party is enough.

## Core shape
- **Location** with its own technical id. Its **kind** (country, region, municipality, town, street, building,
  coordinate point) is reference data, not a subclass.
- **Names**: separate records with language, kind (official, colloquial, historical) and validity. One location has
  many names (exonyms: Warszawa / Warsaw / Varsovie). A name is never a key.
- **External codes**: attributes with a scheme and a validity period — ISO 3166-1 country and ISO 3166-2 subdivision
  codes (iso.org, accessed 2026-11-20), national territorial register codes (e.g. TERYT in Poland), postal codes.
  Never keys: registers renumber, merge and split units, and one postal code may cover several towns.
- **Containment**: "A lies within B" as a dated relationship. Several hierarchies side by side (administrative, postal,
  commercial). Decide whether membership comes from stored containment links or from geometry.
- **Zone**: a dated role an area plays for an owner (delivery zone, sales territory, tax jurisdiction), defined as a
  collection of areas (municipalities, postal codes) — this survives boundary changes better than a hand-drawn polygon.
  A zone is a usage role, not a location kind.
- **Address**: a structured value with a country-specific template (element order, required parts, postal code pattern)
  held as data; can link to coded locations and keep its printable text.

## Rules
- Responsibility split: the party model owns *which party uses which address for which purpose*; the location model
  knows *what the address means* and which areas enclose it.
- **Snapshot rule**: an invoice, order or contract stores a frozen copy of the address and name valid at the event, plus
  a dated reference. A later move never rewrites history.
- Geometry: GeoJSON (RFC 7946, IETF, August 2016) uses WGS 84 with **longitude, latitude** order. The EPSG:4326
  definition lists latitude first, and many tools follow it — swapped axes put a point elsewhere without any error.
  Pin the axis order in the interface contract and test against a known reference coordinate.
- Boundaries are versioned with source and date. Point-in-polygon runs behind an interface.
- Geocoding and map search are external integrations behind an anti-corruption layer; store the result and the
  register id, not just the response.
- Prices or limits that depend on a zone sit in price calculation or a policy, receiving the zone as an input.

## Decisions to settle
- Which countries and address templates are in scope?
- Postal-code validation by pattern or against a register?
- Zones built from municipalities or postal codes — and what about codes that span two municipalities?
- Who maintains zones and register imports, how often?
- Time zone per area (for cut-off times, delivery slots)?

## Belongs elsewhere
- Party ↔ address purpose and lifecycle → parties and relationships.
- Zone-dependent fees → price calculation.
- Delivery slots in time → resource holds.

## Traps
- `city`, `street`, `zip` columns on the customer table, overwritten on every move; old invoices change with them.
- A country enum with `if (country == "DE")` formatting.
- A postal code used as the key of a town.
- `[lat, lon]` stored where the library expects `[lon, lat]` — the warehouse ends up in the Indian Ocean.

## Worked example
Requirement: a shop delivers in Poland and Germany; delivery zones are sets of municipalities and postal codes;
customers move; the invoice must show the address valid on the sale date.
- Locations: `PL` (ISO 3166-1), `PL-14` (ISO 3166-2, Masovian), municipality with TERYT code, `DE`, `DE-BE`; containment
  links dated.
- Zone `Express-Warsaw` (owner: logistics) = {Warsaw municipality, postal codes 05-090, 05-500}, valid from 2026-04-01;
  code 05-500 spans two municipalities → modelled as an explicit postal-code member (decision U).
- Address templates: PL `street number, postal-code town`; DE `street number, PLZ Ort` — data, not code.
- Customer moves on 10 May: a new address version on the party's contact set; invoice of 2 May keeps its snapshot.
- Delivery fee: price calculation receives `zone = Express-Warsaw` as input.
