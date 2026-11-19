# HTTP in API practice: caching, negotiation, limits, collections, bulk operations

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
- **The Richardson maturity model** describes the steps towards REST:
  - level 0: one endpoint, everything through `POST` (an RPC style over HTTP);
  - level 1: separate resources with their own addresses;
  - level 2: HTTP methods and codes according to their semantics (`GET` without effects, `201`, `404`, `409`);
  - level 3: hypermedia, i.e. the response contains links to the possible next steps (section 7).

  Most good public APIs aim for level 2 and take only the cheap elements from level 3. The model is a tool
  for description, not a goal to "pass".
- **A command as a document:** a business operation that is not a field edit you expose as creating a resource
  describing the decision, e.g. `POST /complaints/{id}/approvals` with the body `{ "reason": …, "decidedBy": … }`.
  The response is `201` with `Location` (synchronously) or `202` with a processing status (asynchronously).
  - The command has an identity, an author, a time and a result, so it can be read, audited, retried idempotently
    (an `Idempotency-Key` or a client-assigned identifier) and rejected with a reason (`422`).
  - The resource name comes from the domain language (approval, revocation, correction), not from the table. A `PATCH` changing
    `status` to `approved` hides the business decision and bypasses its rules.
  - A withdrawal is another command (e.g. `POST /complaints/{id}/approval-revocations`), not a `DELETE` of history.
  - On the server side the command document goes to a command handler in the application layer (ddd-tactical-design).
- Some training materials call designing an API around command documents "level 4" of REST maturity.
  The Richardson model has levels 0–3, and "level 4" is an informal term.

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
- A command as a document and "level 4" based on the programme of the training "DDD — advanced modelling techniques
  and archetypes" (Bottega IT Minds, material from the human, 2026-10-21).
Described in our own words.
