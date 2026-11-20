# HTTP in API practice: caching, negotiation, limits, collections, bulk operations

> **Contents:** 1. HTTP caching · 2. Content negotiation · 3. Rate limits · 4. Collections: pagination, filtering, sorting, search · 5. Bulk and long operations · 6. Retries and idempotency · 7. HATEOAS in practice · 8. REST maturity levels and commands as documents

## 1. HTTP caching
- Every `GET` response has a consciously set `Cache-Control`:
  - public, rarely changing data: `public, max-age=…` (for a CDN `s-maxage`);
  - a specific user's data: `private` or `no-store`, never in a shared cache.
- **Validation**: an `ETag` (or `Last-Modified`) + a conditional `If-None-Match` request → `304 Not Modified` without a body.
  The same `ETag` serves optimistic version control on writes (`If-Match` → 412, SKILL.md).
- `Vary` lists the headers the response depends on (`Accept`, `Accept-Language`, `Authorization`, if applicable).
  Without it the cache gives one client a response prepared for another.
- A server-side cache (Redis, an application cache) is a separate decision with an explicit invalidation strategy and lifetime.

## 2. Content negotiation
- The client says what it accepts (`Accept`) and what it sends (`Content-Type`). No `Accept` → `application/json` by default.
- A type unsupported in `Accept` → `406`, an unsupported request `Content-Type` → `415`; the response lists the supported ones.
- Errors in `application/problem+json` (RFC 9457) regardless of the success type.
- Compression (`Accept-Encoding: gzip, br`) enabled for large JSON responses; do not compress secret data together
  with user-supplied data in the same response (BREACH-type attacks).

## 3. Rate limits
- **Where**: per API key or OAuth client (primarily), per user, per tenant, per IP (protection against abuse
  without login). Separate, stricter limits for expensive operations and business flows (login, password reset,
  purchase, sending an SMS — OWASP API6).
- **Algorithm**: token bucket (allows short bursts, the most common choice), sliding window (smoother), fixed window
  (the simplest, but a burst at the window boundary). A counter shared by all instances (e.g. Redis) or a limit in the API gateway.
- **Response**: `429 Too Many Requests` with `Retry-After`. Limit information: the `RateLimit-Policy`
  and `RateLimit` headers from the IETF draft (draft-ietf-httpapi-ratelimit-headers, version 11 of 05.2026 — not yet an RFC; the syntax
  may change) or the popular `X-RateLimit-Limit` / `-Remaining` / `-Reset`. Choose one convention
  and describe it in OpenAPI.
- **Quotas** (e.g. 10,000 requests a month on a plan) are something different from a rate limit — a separate counter and message.
- The client (ours too) respects `Retry-After` and retries with exponential backoff and random jitter.

## 4. Collections: pagination, filtering, sorting, search
- Offset only for small, rarely changing sets; otherwise a cursor (keyset) — **opaque**, with all
  the sort fields, and sorting ends with a unique field (`id`). The total count of results optional or approximate.
- Filters and sorting only from an allowlist; an unknown filter → `400`, not silently ignored; every filter and sort has
  an index or a limit (be-database).

## 5. Bulk and long operations
| Kind | Semantics | Response |
|---|---|---|
| **batch** | all or nothing (one transaction) | `200`/`201` or an error with a list of records to fix |
| **bulk** | each record separately, partial success allowed | `207 Multi-Status` with a result per record (status, errors, identifier) |
| long (seconds and more) | asynchronously | `202 Accepted` + the `Location` of a job resource (`styles-and-communication.md`) |
- A limit on the number of records and the request size; large imports as a stream of records (NDJSON or `application/json-seq`),
  so that one bad record does not invalidate the whole JSON document.
- A result per record lets the client retry only the failed ones — with the same idempotency key per record.

## 6. Retries and idempotency
- Safely retried: `GET`, `HEAD`, `PUT`, `DELETE` (idempotent by definition). `POST` and `PATCH` — only
  with an `Idempotency-Key`: the server remembers the result of the first execution for the key (e.g. 24 h) and returns it again;
  the same key with a different body → `422`.
- Retry transient errors (`408`, `429`, `502`, `503`, `504`, a dropped connection), do not retry `4xx` client
  errors. Exponential backoff with random jitter, a limit on attempts and a total time limit.

## 7. HATEOAS in practice
A full hypermedia-driven API rarely pays off. `next`/`prev` links in collections and links to related
resources are cheap and useful. A list of allowed actions in a resource (e.g. `"actions": ["cancel"]`) helps the frontend
show the right buttons without copying business rules.

## 8. REST maturity levels and commands as documents
**Richardson maturity model** — a way to describe how much of HTTP an API actually uses, not an exam to pass:
- **Level 0:** one endpoint, every call is `POST /api` with the operation name in the body. HTTP is only a transport
  (RPC over HTTP).
- **Level 1:** separate resources with their own URIs (`/orders/42`, `/customers/7`), still often with one verb.
- **Level 2:** HTTP methods and status codes with their proper meaning: safe `GET`, `201` with `Location` on create,
  `404`, `409` on conflict, `412` on a failed precondition. This is the reasonable baseline for most APIs.
- **Level 3:** hypermedia controls; responses carry links to related resources and to the next possible steps.
  Take the cheap parts (collection links, a list of allowed actions, section 7); a fully hypermedia-driven client is
  worth it only when clients really must discover the API at run time.
- The model has four levels, 0 to 3. Anything called "level 4" is an informal label, not part of the model.

**Business actions as resources.** An operation that is not an edit of a field (approve a complaint, cancel an order,
correct an invoice) and that carries its own data, author, time and outcome is exposed as *creating a resource that
records the decision*:
```http
POST /complaints/123/approvals
Idempotency-Key: 6f1c...
If-Match: "v7"

{ "reason": "defect confirmed by service", "decidedBy": "u-55" }
```
- Response: `201 Created` with `Location: /complaints/123/approvals/9` when the decision is taken synchronously, or
  `202 Accepted` with a status resource to poll when processing is asynchronous.
- The command has an identity, so it can be read back, audited and retried safely (`Idempotency-Key`, or an id chosen
  by the client and sent with `PUT`). A rule that refuses the decision answers `422` with a problem document
  (RFC 9457) saying why; a stale `If-Match` version answers `412`.
- Name the resource after the domain decision (approvals, cancellations, corrections). `PATCH { "status": "approved" }`
  hides the decision, loses who and why, and lets clients bypass the rules.
- Undoing a decision is another command, e.g. `POST /complaints/123/approval-revocations`, not `DELETE` on the
  approval: the history stays.
- On the server, each such resource maps to a command handler in the application layer (ddd-tactical-design);
  asynchronous variants and their status resources: `styles-and-communication.md`.

## Sources
- [MDN: HTTP caching](https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching), [MDN: Content negotiation](https://developer.mozilla.org/en-US/docs/Web/HTTP/Content_negotiation),
  [SoftwareMill: Content negotiation in practice](https://softwaremill.com/content-negotiation-in-practice/)
- [Tyk: API rate limiting](https://tyk.io/learning-center/api-rate-limiting/),
  [IETF draft: RateLimit header fields](https://datatracker.ietf.org/doc/draft-ietf-httpapi-ratelimit-headers/)
- [Nordic APIs: API pagination](https://nordicapis.com/everything-you-need-to-know-about-api-pagination/),
  [Tyk: bulk vs batch import](https://tyk.io/blog/api-design-guidance-bulk-and-batch-import/)
- [roadmap.sh — API Design](https://roadmap.sh/api-design)
- L. Richardson, "Justice Will Take Us Millions Of Intricate Moves", QCon 2008 (the talk that introduced
  the levels) and M. Fowler, "Richardson Maturity Model" (martinfowler.com/articles/richardsonMaturityModel.html,
  2010) [unverified: pages unavailable from this session, dates from secondary sources].
Described in our own words.
