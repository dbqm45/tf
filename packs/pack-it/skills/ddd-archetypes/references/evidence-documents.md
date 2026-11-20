# Evidence documents — versions, integrity, distribution, retention, legal hold

## When it applies
- Signal: someone must be able to show exactly which content existed, was agreed or was delivered at a moment — and
  until when it must be kept.
- Not this: a casual attachment (a profile picture, a note) — a file field is enough.

## Core shape
- **Logical document**: id, type, classification, a pointer to the business fact (contract, invoice, consent); it has
  no content of its own.
- **Version** (immutable): number, author, time, status, content hash. Every change creates a new version; the numbering
  scheme is a policy.
- **Rendition**: the same version in a format — editable source, PDF, an archival format such as PDF/A.
- **Record**: a version frozen as evidence, with context (case, fact, who, why). ISO 15489-1:2016 names the
  characteristics of a record — authenticity, reliability, integrity, usability — a good requirements checklist.
- **Integrity proof** on the version: a hash stored separately with its algorithm and date; optionally a seal, a
  timestamp or a signature. The assurance level — simple, advanced or qualified electronic signature / seal under
  Regulation (EU) No 910/2014 (eIDAS) — is a parameter per document type and risk; the legal effect is a question for a
  lawyer.
- **Distribution**: which version and rendition went to which party, through which channel, when, and whether it was
  acknowledged.
- **Retention rule**: classification → period → disposition (delete, transfer to an archive, review). Data, versioned
  with effective dates; each document stores the rule version it was classified under.
- **Legal hold**: its own entity (reason, scope, who placed it, period). While active, disposal is blocked even after
  the retention period ends; it is lifted explicitly.

## Rules
- The retention period starts at a business event (file closure, contract end, employment end, fiscal year end), never
  at file creation.
- Disposal always checks for active legal holds.
- After a format migration, recompute the integrity evidence or keep it together with the original.
- Superseding a version never erases distribution history.
- The document is evidence of a business fact, not the authoritative state holder; a mismatch between document and state
  is investigated, not silently corrected.
- Editing (drafts, comments, co-authoring) and the approval workflow (approvers, order, deadlines) are separate models.
  Approval runs on a specific version; editing content mid-approval creates another version and normally restarts the
  approval. Workflows spanning many documents are processes (work execution).
- Retention periods differ between public-sector archival schemes and private-sector tax, accounting and employment
  rules — have legal counsel confirm the periods.

## Decisions to settle
- Scanned paper: is the scan the original or a copy; is the paper kept?
- Confidentiality classes (enforced by authorisation).
- Anonymising content while keeping the record.
- Privacy consent vs retention obligations (which wins, and for which data).
- Which signature/seal level per document type.

## Belongs elsewhere
- The contract's terms and state → commitments; who may read a document → authorisation; long multi-document workflows
  → work execution.

## Traps
- Overwriting the PDF in storage when a typo is fixed.
- A `created_at + 10 years` deletion job.
- A deletion job that ignores litigation.
- "What did we email the customer?" answered by re-rendering today's template.

## Worked example
Requirement: HR stores signed employment contracts; must prove which version an employee signed and what was emailed,
keep files for a statutory period after employment ends, and stop deletion during a lawsuit.
- Logical document `EMP-CONTRACT/E-2231`, classification *employment-contract*, pointing to the employment of party E-2231.
- Versions: v1 (draft), v2 (sent for signature, SHA-256 `9f3a…` stored 2026-01-12), v3 (signed with a qualified
  electronic signature — level as a parameter for this type). Renditions of v3: DOCX source, PDF/A-2b.
- Distribution: v2 PDF emailed to the employee's private address 2026-01-12 10:04, acknowledged 10:31.
- Retention rule `HR-01 v4`: employment contracts → N years after **employment end** → delete (N to be confirmed by
  legal counsel for the jurisdiction); the document stores `HR-01 v4`.
- Lawsuit filed: legal hold `LH-17` (scope: all documents of E-2231, placed by Legal, 2027-03-01, open-ended) — the
  disposal job skips them until it is lifted.
