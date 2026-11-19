# The Document archetype — mapper (documents, versions, workflow, retention)

> **Contents:** Fit test · Model (the essence) · Questions · Mapping steps · Decisions to check (R/A/X) · Result format · Patterns and pitfalls · Quality check · Example (shortened)

It turns requirements about **documents** (an agreement, a protocol, an invoice as a file, a consent, an attachment) into a model in which the logical
document, its immutable versions, copies in formats, distribution and disposition after the deadline are separate concepts.
The effect: you can prove what exactly was recorded or sent and when, and you know how long to keep it.
The common protocol (questions, "It depends", the R/A/X check, recording): `SKILL.md` → "Mapper — the common protocol".

## Fit test
**The core question:** *do you need to prove WHAT exactly was recorded, agreed or sent and when — and how long to keep it?*
Yes → it fits. The file is only an attachment with no evidential value and no retention deadline → a field in another aggregate is enough.

| Signal in the requirements | Fits? |
|---|---|
| "we must show which version of the agreement the customer signed" | ✅ |
| versions, numbering, "who changed it and when", approval | ✅ |
| a signature, a seal, a timestamp, a file hash as evidence | ✅ |
| keeping for N years, then deletion or transfer to an archive | ✅ |
| sent to a counterparty / customer; who received which version | ✅ |
| suspending deletion during a dispute or an inspection | ✅ |
| "what obligations follow from the agreement?" (parties, deadlines, terms) | ❌ → Agreement (`agreement.md`); the document is the carrier |
| "what is the amount on the invoice and how to post it?" | ❌ → Accounting; the document is not the source of truth for state |
| README, ADR, runbook in the repository | ❌ → docs-tech-writing |
| identity and read permissions | ❌ authorization (the application layer) |
| full-text search, OCR | ⚠️ borderline |

**Borderline cases:**
- *An ordinary attachment to a ticket* — if nobody asks about the version, integrity or a deadline, it is not this archetype.
- *The content of obligations vs the file* — the rules and deadlines of the agreement live in Agreement; Document guards which file is the evidence of which version.
- *Form data* — when "what the customer saw and approved" matters, freeze the version of the content as a document; the form itself
  is not a document.

## Model (the essence)
The breakdown below is the factory's modelling conclusion; the sources in the "Sources" section confirm only what is described there.
### Document, version, copy
- **Document** (an information resource) — a logical entity: an identifier, a type (agreement, protocol, consent), a classification, links
  to a business fact. It has no content; it points to versions. It also covers media other than text (a photo, a recording, an e-mail).
- **DocumentVersion** — **immutable** content: a number, an author, a creation time, a status (draft, approved, superseded),
  a content hash. A change = a new version, never an edit; the previous one stays available. Numbering is a policy (the next number,
  major.minor), not a date.
- **Rendition** (copy) — a specific file of the same version in some format: editable, PDF, PDF/A for long-term retention.
  The long-term format is a retention decision: an approved version gets an archival rendition.
- **Record** — a version frozen in the role of evidence: it does not change, it has a context (a case, a business fact, who and why).
  A record is trustworthy when its authenticity, reliability, integrity and usability can be demonstrated — these
  four characteristics are a good checklist of requirements (not a data schema).

### Integrity evidence
- **IntegrityEvidence** — a content hash stored separately from the file; optionally an electronic seal, a timestamp,
  a signature. The level (simple, advanced, qualified) and the provider are a **policy parameter** depending on the document type and
  the risk, not a constant in the archetype. The evidence belongs to the version, not to the document; after a format migration the evidence is recomputed or
  kept together with the original. The legal effects of the levels are assessed by a lawyer.

### Distribution and disposition
- **Distribution** — the fact of handing over a specific version (and rendition) to a specific party (→ Party): channel, time, acknowledgement.
  It lets you answer "who got which version". Revoking or superseding a version does not erase the distribution history.
- **Disposition** — what happens to the document after the deadline: deletion, transfer to an archive, appraisal. It follows from the retention rule
  applied to the document, not from a manual decision on the file.

### Retention
- **RetentionRule** — a classification (a document category) → a period and a disposition. The rule is data, versioned, with an effective
  date; the document records which rule was applied.
- **The deadline is counted from an event, not from creation** — usually from the closing of the case. An example from Polish public administration: classification
  according to JRWA (the uniform list of file categories), archival category A (permanently), B with a number of years or BE with a number of years (after the period an archival appraisal);
  the period is counted from 1 January of the year following the closing of the case. A bare "B" without a number is incorrect.
  For private companies the periods follow from other regulations (tax, accounting, employment) — to be confirmed by a lawyer.
- **LegalHold** (suspension of deletion) — a separate entity: a reason, a scope (documents, cases), who placed it, a period; while it lasts,
  disposition is blocked even though the deadline has passed. This is our own modelling conclusion, not an element of the standard; a hold is lifted explicitly.

### The link to a business fact
The document points to a fact (`agreement → Agreement`, `invoice → Accounting`, `consent → Party`), but **it is not the source of truth for state**.
The state of the obligation, the balances and the permissions are kept by the appropriate archetypes; the document is their evidence. A file–state discrepancy is
a signal to investigate, not to correct silently.

## Questions
**A — standard decisions:**
- Which document types do we cover, and which of them are records (evidence) and which drafts?
- Who freezes a version and when (approval, signature, sending)? After freezing, do we allow only new versions?
- What level of integrity evidence for which type (hash, seal, timestamp, signature)? Who is the provider?
- The long-term format (e.g. PDF/A) — for which types and when is the rendition created?
- What classification and retention period per type; from which event do we count the deadline?
- What does disposition do after the deadline (delete, archive, appraisal) and who approves it?

**B — gaps** (examples): suspending deletion during a dispute? · distribution to many recipients with acknowledgement? · confidentiality
and access classification (→ authorization)? · format migration after years vs signature validity? · a scanned paper document
(original vs copy)? · GDPR consents vs retention (→ Party)? · anonymizing the content while keeping the record?

## Mapping steps
1. **Document types** — nouns from the requirements (agreement, protocol, amendment) → a type and a classification; separate the document from the business fact.
2. **Versions** — when a new one is created, numbering, statuses, who approves.
3. **Renditions** — formats and the moment the archival format is created.
4. **Integrity evidence** — the level per type as a policy parameter.
5. **Distribution** — to whom, which version, through which channel, with or without acknowledgement.
6. **Retention** — the rule, the start event, the period, the disposition; rule versioning.
7. **LegalHold** — is it needed, who places and lifts it.
8. **The link to the fact** — which archetype the document refers to; the direction of the dependency.

## Decisions to check (R/A/X)
types and records · the moment of freezing · version numbering · the evidence level per type · the archival format · the retention start event ·
the period and disposition · legal hold · distribution and acknowledgement · format migration · the link to the business fact.

## Result format
```markdown
# Document model: <area>
## Concept mapping    — | Domain concept | Archetype element | Justification |
## Unmapped concepts
## Document types     — | Type | Classification | Record? | Business fact (archetype) |
## Versions and renditions — | Type | Numbering | Statuses | Moment of freezing | Formats |
## Integrity evidence — | Type | Hash | Seal/timestamp/signature (level) | Policy parameter |
## Distribution       — | Type | Recipient (Party) | Channel | Acknowledgement |
## Retention          — | Classification | Period | Start event | Disposition | Rule (version) |
## Holds (legal hold) — | Reason | Scope | Who places/lifts |
## Decisions (R/A/X)  — | Decision | Source |
## Notes              — assumptions (X), edge cases, variable policy parameters
```

## Patterns and pitfalls
- **Overwriting a file under the same name** — loses the evidence. Every change is a new version; an approved one is immutable.
- **The document as the source of truth for state** — "the amount from the PDF" instead of from Accounting, "the deadline from the agreement" instead of from Agreement. The document
  documents; the state comes from the appropriate archetype.
- **Retention counted from the file creation date** — the deadline runs from an event (closing of the case, the end of the financial year).
- **A hash together with the file in one field without the algorithm version** — record the algorithm and the date; algorithms age.
- **Deleting after the deadline without checking holds** — disposition always asks about active LegalHolds.
- **An editable format as the archive** — for long-term retention a separate rendition in a format intended for archiving.
- **Outside the archetype:** "who may see the agreement?" (authorization), "what follows from it?" (Agreement), "how to post it?"
  (Accounting). Technical documentation in the repository is docs-tech-writing.
- **Variable policies as parameters:** the signature level and the retention period depending on the type and the country → the archetype gets ready values.
- **Workflow is not editing:** editing (changing the content, drafts, comments, collaboration) and workflow
  (who approves, in what order, deadlines, escalations) are two models with different rules and events. The workflow
  operates on **a specific version**: changing the content during approval creates a new version and usually restarts the workflow
  (decision A). An "in approval" status in the document table mixes both models. A workflow of many documents is a process
  (`activity-process.md`), not a document field.

## Quality check
- [ ] document, version, rendition, distribution and disposition are separate concepts
- [ ] an approved version is immutable; a change is a new version
- [ ] integrity evidence belongs to the version; the level as a policy parameter
- [ ] retention with a classification, a start event, a period and a disposition; categories A/B/BE correct (B and BE with a number of years)
- [ ] legal hold settled (it exists or it is explicitly not needed)
- [ ] the document refers to the business fact, it is not the source of truth for state
- [ ] the mapping table and "Unmapped concepts" present; no material (X)

## Example (shortened)
**Input:** "A service company concludes agreements and draws up acceptance protocols with the signatures of both parties. Agreements have amendments. The customer
gets the signed version by e-mail. We keep documents for 10 years from the end of the agreement [example]. During a dispute nothing may be deleted."

```markdown
## Concept mapping
| agreement, protocol | Document (types) + classification | business fact: agreement → Agreement |
| amendment | a new DocumentVersion of the same Document or a separate linked Document | decision (A) |
| signed version | Record = a frozen DocumentVersion + IntegrityEvidence | immutable |
| e-mail to the customer | Distribution (version, recipient from Party, channel) | lets you demonstrate what was sent |
| 10 years | RetentionRule (start: end of the agreement) | [example] |
| dispute | LegalHold | blocks disposition |
## Integrity evidence — agreement: hash + signature (level: policy parameter, A); protocol: hash + timestamp
## Retention — agreement | 10 years [example] | end of the agreement | deletion after approval | rule v1
## Decisions
| retention 10 years from the end | R |
| amendment as a version or a separate document | A: a separate document linked to the agreement |
| signature level | A: "It depends" on the value of the agreement → parameter |
| archival format | X → hot spot (PDF/A?) |
## Unmapped concepts — the payment deadline from the agreement (→ Agreement), the invoice for the service (→ Accounting), the customer (→ Party)
```

## Sources
Accessed 2026-10-17.
- Hay, "Enterprise Model Patterns: Describing the World (UML Version)", Technics Publications, 2011 (ISBN 978-1-935504-05-4) —
  we take: the chapter "Documents and other Information Resources" covers information resources, their relationships, concepts, distribution
  and dispositions, as well as media (photos, recordings, e-mails). Rank: primary (the publisher's description).
- ISO 15489-1:2016, "Records management — Concepts and principles" — we take: the four characteristics of a trustworthy record (authenticity,
  reliability, integrity, usability) as a checklist. Rank: primary (iso.org).
- ISO 16175-1:2020 and ISO 16175-2:2020 — we take: only the indication of the current parts as further reading (we do not describe the content). Part 2 is sometimes described as a technical specification (TS) — do not cite it as a standard without that caveat;
  part 3 (2010) withdrawn. Rank: primary, partly verified.
- MoReq2010 (DLM Forum, 2011) — we take: only the indication as further reading; currency [unverified] (no successor found).
  Rank: primary.
- ISO 19005-4:2020 (PDF/A-4, based on ISO 32000-2) — we take: a format intended for long-term retention; earlier parts
  -1 (2005), -2 (2011), -3 (2012). Rank: primary (iso.org).
- Regulation (EU) 2024/1183 of 11.04.2024 amending eIDAS 910/2014 (in force since 20.05.2024) — we take: the context for the electronic
  seal, the timestamp and the signature levels (simple, advanced, qualified), without article numbers. Rank: secondary.
  Legal effects to be confirmed by a lawyer, not advice.
- Rozporządzenie Prezesa Rady Ministrów (the Regulation of the Prime Minister) of 18.01.2011 on the office instruction, JRWA and the archival instruction (Dz.U. 2011
  No. 14 item 67) — we take: the JRWA classification, categories A, B + years, BE + years, counting from 1 January of the year following
  the closing of the case. Rank: primary (ELI; status "in force", amendments [unverified]). It concerns public administration; for private
  companies — context to be confirmed by a lawyer.
- Workflow vs editing of a document — based on the programme of the training "DDD — zaawansowane techniki
  modelowania i archetypy" (DDD — advanced modelling techniques and archetypes; Bottega IT Minds, material from a human, 2026-10-21); described in our own words.

The breakdown into document, version, rendition, distribution and disposition in this form, integrity evidence as a policy parameter, and
LegalHold are the factory's modelling conclusions, not theses of the authors or the standards.
Described in our own words; the content of books and standards was not quoted.
