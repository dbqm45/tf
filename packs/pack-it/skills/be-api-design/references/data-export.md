# Data export (CSV, XLSX) from an API

An export looks like a small feature ("download CSV"), but with large sets it becomes a background job, a channel
for data leaks and an attack vector against the recipient's spreadsheet.

## 1. Synchronously or in the background
- **Synchronously** only for small sets with a hard limit (e.g. up to 10 thousand rows): a streamed response
  (`Content-Disposition: attachment`), without building the whole file in memory.
- **In the background** above the limit:
  - `POST /exports` with a filter and a format responds `202 Accepted` with a job resource (`Location: /exports/{id}`);
  - the job resource has a status (`queued` / `running` / `done` / `failed`), progress and a result;
  - on completion a notification (in the app, an email, a webhook) instead of polling every second.
- The export request has an idempotency key. Clicking again does not start a second job (`SKILL.md`,
  "Idempotency").
- A limit on the number of concurrent exports per user and per organization. Large exports go in a separate queue, so that
  they do not block ordinary jobs.

## 2. The same filters and permissions as the list
- The export accepts **the same filter** as the list endpoint (`GET /customers?...`) and goes through the same
  authorization, always on the server side. Records the user does not see on the list do not get into the file.
- The export permission is separate from the browsing permission. Downloading the whole customer database is a different
  operation from viewing one record.
- A consistent snapshot: the job reads in one read-only transaction or relative to a fixed moment
  (`as_of = the request time`) and a cursor over a unique key. Otherwise records changed in the meantime get into the file
  twice or not at all.

## 3. The file and its lifecycle
- The file in an object store, downloaded through a **signed link with a short validity** (e.g. 15 min to 24 h),
  issued only after checking again that the downloader is the requester or has the permission.
- The file expires and is deleted automatically (e.g. after 7 days). This is part of the data retention policy.
- Large files: compression or splitting into parts, and the date and the filter in the name
  (`customers_status-active_2026-11-10.csv`).

## 4. Personal data and columns
- You export only the columns needed for the purpose. The list of columns is explicit (an allowlist), without "all the
  entity's fields". Sensitive fields (PESEL, IBAN, notes) only behind a separate permission or masked. Data classes:
  arch-privacy-compliance (pack-it).
- You record every export in the audit log: who, when, which filter, how many rows, which columns. A file with personal
  data is a frequent source of leaks (be-business-app-patterns, pack-it).

## 5. Formula injection into CSV (CSV injection)
- A cell starting with `=`, `+`, `-`, `@`, a tab or a carriage return can be executed as a formula
  after the file is opened in a spreadsheet. Example: the company name `=HYPERLINK("http://…")` entered by a customer.
- You neutralize user-supplied values on export: prefix them with an apostrophe (`'`) when they start
  with one of these characters, and always quote the field with double quotes doubled inside.
  [unverified at the source 2026-11-10: OWASP "CSV Injection" — the page unavailable from this environment]
- You format numbers and dates from the database explicitly (the decimal separator, ISO 8601) and state the encoding (UTF-8 with a BOM,
  if the recipient is Excel).

## 6. Tests
- An export with a filter contains exactly the same records as the list with that filter for the same user.
- A user without the permission will not request an export and will not download someone else's file, even knowing its identifier.
- The value `=1+1` in the data goes into the file as text.
- The link expires, and the file disappears after the retention period.
- A retried request with the same idempotency key returns the same job.
