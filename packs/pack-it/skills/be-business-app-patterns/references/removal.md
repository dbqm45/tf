# Deletion: soft delete, the trash and data erasure

## When soft delete
- Yes: restoring is needed (a trash), the record is the target of relations (invoices point to the customer), the audit or settlements
  require history.
- No: personal data on an erasure request, data without historical value (sessions, tokens, technical logs), tables
  in which the `deleted_at IS NULL` filter would be everywhere and easy to forget.

## Implementation pitfalls
- A default filter (a scope in the ORM, a view, an RLS policy) — otherwise deleted records come back in reports, search,
  export and counters.
- Uniqueness: a partial unique index `WHERE deleted_at IS NULL`, so that after deletion the same
  name or email can be used.
- Cascades: what happens to the children (mark them together, leave them, block the deletion) — an explicit decision.
- Files in the object store and data in search or the cache you delete or hide together with the record.

## The trash and irreversible deletion
- A deletion with a large effect: a permission (the owner), a confirmation by typing the name with the number of items
  that will disappear; for critical ones re-authentication or a second factor.
- A grace period (e.g. 30 days) with restoring, then permanent deletion by a background job; a notification to the people
  it concerns.

## A personal data erasure request (GDPR Art. 17)
- `deleted_at` is not enough: the data is still in the database. Permanent deletion or anonymization (irreversible, without
  a key to restore; pseudonymization is still personal data).
- It covers: the application tables, files, search, analytics, external systems and subcontractors, logs and the audit
  (pseudonymization), backups (they usually expire with the rotation; you document the deadline and do not restore deleted
  data when restoring).
- Exceptions (a legal obligation, e.g. accounting documents) — the data stays only in the required scope; the decision and the basis
  recorded. The legal assessment: arch-privacy-compliance.
