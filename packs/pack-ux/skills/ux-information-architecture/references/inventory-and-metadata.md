# Inventory, audit, metadata and taxonomy

## Content inventory
A spreadsheet or an export from the CMS, one line per page or asset:
`ID | address | title | type | hierarchy level | owner | author | publication and update date | language | traffic (12 mo.) | entry sources | metadata`.
Collect it automatically (XML sitemap, crawler, CMS API, analytics). By hand you only add the owner and the decision.
Without an owner a page is a candidate for removal or for being taken over.

## Content audit
Assess a sample or the whole by these criteria:
| Criterion | Question |
|---|---|
| currency | is the content consistent with the actual state and the date |
| accuracy | is it correct, not contradicting another page |
| usefulness | does anyone need it (traffic, the tasks from step 1) |
| understandability | plain language, one task per page |
| duplicates | is the same information elsewhere (merge) |
Decision: **keep / fix / merge / remove / add**. When removing: 301 redirects and updating internal links.
The audit result feeds both the cards for sorting (a representative sample of pages) and the migration plan.

## Cards for sorting from the inventory
Choose 30–60 pages/concepts representing all areas, including the frequently searched ones (from search queries).
Names in the users' language; a short description on the back.

## Metadata
- Minimum: title, description, content type, topic, audience (if different), update date, owner.
- Range of values: a **controlled vocabulary** (a list, not free text), synonyms and outdated forms mapped to the preferred name.
- Use: filters and facets in search and lists, related content, reports on the state of the content.
- Rule: every attribute has a user (a filter or a report). Do not collect metadata "just in case".

## Taxonomy and label glossary
Entry: `preferred name | definition | synonyms and user phrases | discouraged name | level | owner`.
Hierarchy and rules: one grouping principle per level; disjoint names; broader/narrower/related relations.
Facets (e.g. category, brand, price, use) instead of one tree when objects have several independent traits (a shop).
The glossary lives: an owner and a review date (every quarter or when the offer changes).
