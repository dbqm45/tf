---
name: be-api-design
description: Use for designing an HTTP API — resources, codes, errors, pagination, versions, idempotency, OpenAPI, webhooks.
metadata:
  review: "2027-10-17"
  catalog: "Use when designing and implementing HTTP/REST endpoints — paths, methods, status codes, pagination, errors, versioning, idempotency, OpenAPI, HTTP caching, rate limits, webhooks, GraphQL/gRPC/SSE, OWASP API Top 10. Not for the database schema (be-database) or login mechanisms (be-auth-security)."
  keywords: "obsługa błędów API, format błędów, RFC 7807, RFC 9457, problem details, application/problem+json, eksport do CSV, eksport do Excela, eksport w tle, timeout przy eksporcie, CSV injection, wstrzykiwanie formuł, ponowienie żądania, Idempotency-Key, timeout klienta, podwójne wykonanie, endpoint POST, odpowiedź przy ponowieniu, metody HTTP GET PUT PATCH DELETE, kod statusu odpowiedzi, API error handling, error format, export to CSV, export to Excel, background export, export timeout, formula injection, request retry, client timeout, double execution, response on retry, HTTP methods, response status code, REST API design, pagination, API versioning"
---

# API design

## Resources and methods
- At most 2 levels of path nesting (`/users/{id}/orders`).
- Actions that do not fit CRUD: `POST /orders/{id}/cancel`. When an action has its own data, author, result or history
  (approval, revocation, correction), model it as a **command document resource**: `POST /complaints/{id}/approvals`
  creates an approval with an identifier that can be read, audited and withdrawn by another command
  (`http-in-practice.md`, section 8).

## Status codes that are easy to confuse
- `201` with `Location` after creation; `404` also when we do not want to reveal that the resource exists.
- `409` — a state conflict (a duplicate, a version); `422` — a correct format, but a business rule rejects it.
- `429` with `Retry-After`; `5xx` only for an error on our side, never for a client error.

## Error format (RFC 9457 Problem Details)
```json
{ "type": "https://example.com/errors/validation", "title": "Validation failed",
  "status": 400, "detail": "email is invalid", "errors": [{"field": "email", "code": "invalid"}] }
```
Never return a stack trace or database messages.

## Collections
A cursor for large sets, a hard `limit` on the server side, filters and sorting from an allowlist of fields
(`references/http-in-practice.md` §4).
Export (CSV, XLSX) of large sets in the background, with the same filters and permissions, an expiring link, columns
from an allowlist and protection against formula injection: `references/data-export.md`.

## Idempotency and consistency
- A `POST` with a financial or external effect accepts the `Idempotency-Key` header.
- Optimistic version control: `ETag` + `If-Match` → 412 on a conflict.

## Versioning and compatibility
- Adding fields is safe; removing/changing a type = a breaking change → a new version or a deprecation period with the `Deprecation` header.
- You number a service or SDK release by SemVer (core-semver): an incompatible contract change → MAJOR, a new field or
  endpoint → MINOR. The `/v1` prefix in the URL is a separate decision; changing it usually goes with a MAJOR.

## Validation
Every input validated with a schema at the boundary (body, query, params). Unknown fields rejected or ignored — consistently.

## References index
- `styles-and-communication.md` — REST, GraphQL, gRPC, SOAP, webhooks (signatures, retries, SSRF), SSE, WebSocket,
  streaming, asynchronous operations (`202`), the API gateway and BFF.
- `http-in-practice.md` — HTTP caching (`Cache-Control`, `ETag`/304, `Vary`), content negotiation (406/415), rate limits
  (algorithms, 429, RateLimit headers), cursor pagination, filters and sorting, batch vs bulk (207), retries, HATEOAS,
  the Richardson maturity model and commands as documents.
- `data-export.md` — CSV/XLSX export: synchronously or in the background (`202`, a job resource), the same filters and permissions, a consistent snapshot, a signed link and file retention, columns and personal data, formula injection, tests.
- The security checklist before a release: be-auth-security, `.claude/skills/be-auth-security/references/api-security-checklist.md`.
- `backend-performance-checklist.md` — a performance checklist (cache patterns and invalidation, timeouts and retries, keep-alive, asynchrony, scaling, profiling, asynchronous logging).
- `lifecycle-and-security.md` — design-first (lint, mock), versioning and retirement (`Deprecation`, `Sunset`),
  OWASP API Top 10 (2023), API keys, contract and performance tests, personal data.

## Checklist
- [ ] the OpenAPI spec updated
- [ ] tests: success, validation, 401/403, 404
- [ ] authorization checked per resource (see be-auth-security)
- [ ] `Cache-Control` set consciously; request and size limits; no excess fields in the response (OWASP API3)
- [ ] a breaking change → a new version or `Deprecation`/`Sunset` with a migration plan
