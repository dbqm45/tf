# Identity and references — names, identifiers from many issuers, duplicates and equivalences

## When it applies
- Signal: the same real thing is known under several numbers or names (an internal id, a supplier's code, a GS1 GTIN,
  a tax number, a legacy id), records get duplicated, or partners disagree about whether two things are "the same".
- Typical requirements: importing supplier catalogues, integrating an acquired company's systems, master data
  management, "merge these two customers", cross-references between trading partners' codes.
- Not this: login identities and sessions → be-auth-security; one internal surrogate key and nothing else → plain id.

## Core shape
- **Thing**: the object itself (a party, a product, an asset, a location) with an internal technical id that never leaves
  the system's meaning and is never reused.
- **Label (name)**: an informal string — display names, aliases, abbreviations. 0..n per thing, one may be preferred.
  The same label may belong to many things; it is never a key.
- **Identifier**: *scheme + value → one thing*.
  - **Scheme** (configuration): who issues the values (us, a supplier, GS1, a tax authority, a legacy system), the format
    and check digit, whether one thing may hold several values in it, whether values may ever be reused.
  - Unique per *(scheme, value)*; the same value in two schemes is unrelated and harmless.
  - Immutable once assigned and never deleted; a retired value stays recorded so old documents still resolve.
- **Merge** of duplicates (two records turn out to be one thing), three strategies:
  - **absorb**: move data and references to the survivor, delete the other — simplest, irreversible, breaks identifier
    immutability unless every reference is found;
  - **retire and forward**: mark one record *merged into* the survivor, keep it read-only, resolve its identifiers to
    the survivor — keeps the history of what was recorded on each;
  - **shared core**: both records stay as facets linked to a new core object — easiest to undo, every reader must
    consult all facets.
- **Equivalence**: a set of things that some parties treat as interchangeable, plus the parties that endorse it
  (a customer accepts part B as a substitute for part A). The things stay distinct; the equivalence is not universal.

## Rules
- Resolve incoming references through the identifier table *(scheme, value)*, never through labels and never by
  guessing on names.
- Validate an identifier's format when it is recorded, per its scheme; a check-digit error is a refusal, not a warning.
- Do not encode changing properties (region, category, size) into an identifier you issue; give a separate descriptive
  code if people need one.
- Choose the merge strategy by certainty and reversibility: high certainty and no audit need → absorb; history matters
  → retire and forward; the match may prove wrong → shared core.
- A merge is an event with who, when and why; references to the retired record keep working (forwarding), so external
  systems never get a dangling id.
- An equivalence is used only on behalf of a party that endorses it ("show substitutes" for customer X uses X's
  equivalences, not everyone's).
- A coding system of a partner (their product codes, their classification) is a scheme mapped onto your things; data
  can be exchanged at the partner's granularity without adopting their model.

## Decisions to settle
- Which schemes exist, who owns each, and which one is shown first?
- Duplicate detection: which fields are a strong match, which are only a hint for a human?
- Who may merge and un-merge (authorisation), and is un-merge required?
- What happens on merge to conflicting values (two different VAT numbers, two addresses)?
- Retention of retired records and identifiers.

## Belongs elsewhere
- Party roles and relationships → parties and relationships (this archetype only resolves *which* party).
- Product definitions vs items → product definitions; locations and addresses → places and zones.
- Matching algorithms (fuzzy matching, record linkage) → an implementation detail behind the merge-candidate list.

## Traps
- Loose columns `legacy_id`, `crm_id`, `sap_id`, `supplier_code` on the entity — every new partner is a migration and
  uniqueness per issuer is unchecked.
- A natural key (tax number, email, EAN) as the primary key — it changes, is missing for some kinds, or is reused.
- Merging by `UPDATE … SET customer_id = :survivor` across tables and deleting the duplicate — invoices sent with the old
  number no longer resolve, and the merge cannot be undone.
- Treating a substitute part as "the same product" for everyone — one customer's acceptance becomes a global rule.
- Matching by name ("ACME Ltd" vs "Acme Limited") and silently linking the wrong company.

## Worked example
Requirement: an industrial parts distributor acquires a competitor; both catalogues and both customer bases must be
combined; suppliers send price files with their own part codes; some fleet customers accept aftermarket substitutes.
- Schemes: `our-sku` (we issue, never reused), `gtin` (GS1, check digit validated), `supplier:<party-id>` (one per
  supplier), `legacy-acq` (the acquired company's numbers, read-only, values never reissued).
- Part *hydraulic seal 40 mm*: `our-sku P-118204`, `gtin 05901234123457`, `supplier:S-17 HS-40N`, `legacy-acq 7731-B`.
  A supplier price file line "HS-40N" resolves via *(supplier:S-17, HS-40N)*; a name match is never used.
- Customer duplicates found after the migration (same VAT number, different addresses): **retire and forward** —
  `C-9033` merged into `C-1210` on 2026-05-02 by the master-data team; invoices printed with `C-9033` still resolve.
  A suspected but unconfirmed match → **shared core**, so it can be split again.
- Equivalence *P-118204 ≈ P-560771 (aftermarket)* endorsed by customers `C-1210` and `C-4410` only; the "substitutes"
  list for any other customer does not show it.
