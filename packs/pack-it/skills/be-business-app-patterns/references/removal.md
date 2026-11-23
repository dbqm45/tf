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
- `deleted_at` is not erasure: delete or anonymize irreversibly (pseudonymization is still personal data) — the
  application tables, files, search, analytics, external systems, logs; backups expire with the rotation (document the
  deadline, do not restore erased data).
- Exceptions (e.g. accounting documents) keep only the required scope, with the basis recorded; the legal assessment:
  arch-privacy-compliance.
