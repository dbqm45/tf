# Data quality, data governance and compliance

## Quality dimensions
| Dimension | Question | Example test |
|---|---|---|
| completeness | are all records and fields present | row count vs the source, the share of missing values |
| accuracy | do the values correspond to reality | reconciling the sum with the source system, ranges |
| consistency | do the same facts agree between tables | foreign keys, the sum of details = the header total |
| timeliness | is the data fresh | the time of the last update vs the SLA |
| validity | does it fit the format and rules | patterns (NIP (Polish tax ID), email), allowed values |
| uniqueness | are there no duplicates | uniqueness of the business key |
- Tests on every pipeline run (dbt tests, Great Expectations, Soda or your own queries), with a threshold:
  a warning or a halt of publication.
- Every dataset has an **owner** and **consumers**; you handle a quality incident like a service incident (ops-sre-incidents):
  detection, a message to consumers, a fix, a backfill, a root cause analysis.
- Data observability: freshness, volume, distributions, schema and lineage in one view; anomalies of volume
  and distribution catch errors for which there is no test.

## Metadata, catalog and lineage
- **Data catalog**: what exists, a description, an owner, a classification (public, internal, confidential, personal), freshness,
  example queries. Without a catalog people build their own copies of the same data.
- **Lineage**: from which sources and transformations a column or table arose — to assess the impact of a change,
  look for the cause of an error and answer GDPR requests. Generated automatically (dbt, the OpenLineage standard), not
  drawn by hand.
- **A "metadata first" architecture**: pipelines, permissions and quality driven by declarations (schema, owner,
  classification, quality rules), not hard-coded.

## Data organisation
| Concept | What it is |
|---|---|
| **data lake** | file storage in raw form, various formats; cheap, but without governance it becomes a "swamp" |
| **warehouse** and **data mart** | models for analytics; a data mart — a slice for one department |
| **lakehouse** | a lake with a table format (Iceberg, Delta, Hudi) — transactions and a schema as in a warehouse |
| **data hub** | a data exchange point between systems with access control |
| **data fabric** | an integration and metadata layer connecting distributed sources, often with automation |
| **data mesh** | organisationally: domains are responsible for their data as **products** (an owner, a contract, quality, documentation), a self-service platform, shared federated rules. Requires mature teams; corresponds to DDD context boundaries (ddd-strategic-analysis, proc-team-topologies) |
You choose by the organisation's scale, not by fashion: a small team usually needs one warehouse with dbt.

## Data protection
- **Classification** of columns (personal, special-category, financial data) in the catalog, permissions by classification (column-
  and row-level access in the warehouse).
- **Masking** (dynamic — depending on permissions — or static in copies), **pseudonymisation**
  and **tokenisation** (a value replaced by a token, the mapping in a separate, protected store — e.g. card numbers through a
  payment provider), irreversible **anonymisation** for test and open data. Pseudonymisation and tokenisation
  are still personal data within the meaning of the GDPR.
- Encryption in transit and at rest, keys in a KMS (ops-secrets-identities, `cryptography-and-pki.md`).
- Minimisation and retention: you keep data only as long as the purpose requires; deletion also covers copies,
  snapshots and the warehouse.

## Law (the legal department decides, the agent prepares the facts)
- **GDPR**: the legal basis and purpose of processing, the right of access, rectification and erasure (lineage shows where
  a person's data is), transfers outside the EEA, the record of processing activities, an impact assessment for risky processing.
- **The AI Act** (EU): transparency obligations (Art. 50 — informing about contact with AI, labelling synthetic content)
  apply from 2.08.2026; the Digital Omnibus package moved the obligations for high-risk systems from Annex III
  to 2.12.2027, and from Annex I to 2.08.2028 — check whether the changes have entered into force and what they say on the decision date.
  For data: documentation of the sources and quality of training data, counteracting bias.
- Other jurisdictions by market (e.g. in the USA the federal electronic communications law — ECPA — and state
  privacy laws).

## Sources
- DAMA-DMBOK (quality dimensions); Z. Dehghani, *Data Mesh* (2022); OpenLineage; the dbt documentation
- [Jones Walker — EU AI Act Digital Omnibus](https://www.joneswalker.com/en/insights/blogs/ai-law-blog/yes-august-2-still-matters-the-eu-approved-a-high-risk-ai-delay-but-most-trans.html?id=102nbon)
- [roadmap.sh — Data Engineer](https://roadmap.sh/data-engineer) (data quality, lineage, metadata management, data lake,
  mart, hub, fabric, mesh, masking, obfuscation, tokenization, GDPR, EU AI Act, ECPA)
Described in our own words.
