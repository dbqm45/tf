# Bulk operations

## Before starting
- The scope as a filter ("all matching: status = new, 50,213 records"), not a list of IDs sent from the browser.
- A preview: the number of records and a sample; a confirmation with the number; a limit (above a threshold an additional confirmation or
  a role).
- The permission checked per record (the same rules as for a single change) — records without the permission skipped
  and reported.

## Execution
- A background job (a queue), in batches (e.g. 500), each batch in a separate transaction; progress visible in the UI.
- Idempotency: an operation identifier, a record of the processed records; resuming after a failure does not change them a second
  time.
- Partial errors do not stop the whole: a report "changed / skipped / errors with a reason" to download.
- Locks and load: batches outside peak hours or with a rate limit, so as not to block the database.

## After execution
- One audit entry for the operation (who, the filter, the numbers) plus entries per record, if the audit is per object.
- Undo: recording the previous values lets you reverse the operation within a time window; for irreversible ones (sending
  emails, payments) a clear warning before the start.
- A completion notification (UI, email) — the user does not wait on an open page.
