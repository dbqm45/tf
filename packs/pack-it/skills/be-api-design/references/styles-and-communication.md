# API styles and ways of communicating

By default REST/JSON over HTTP. You choose another style when a specific scenario requires it, and you record the decision in an ADR.

## 1. Choosing the style
| Style | When | Cost and pitfalls |
|---|---|---|
| **REST / JSON** | public and cross-team APIs, CRUD with actions, HTTP caching | too much or too little data for a screen → a BFF or fields chosen by a parameter |
| **GraphQL** | many different clients assemble data from many sources, the frontend needs flexible queries | N+1 in resolvers (DataLoader), query depth and cost limits (DoS protection — OWASP API4), per-field authorization (API3), errors returned in a 200 response, harder HTTP caching; in production only persisted queries or an allowlist |
| **gRPC** | service–service communication, low latency, streams, a contract in Protobuf | the browser only through gRPC-Web or Connect; always set a deadline (otherwise hanging calls), gRPC status codes instead of HTTP, schema compatibility through field numbers (do not remove, do not change numbers) |
| **SOAP** | integration with existing systems that require it (banking, public administration) | XML, WSDL, WS-Security; you do not choose it for new APIs |
| **Webhooks** | notifying external systems about events (a payment, a status change) | delivery, retries, signatures, ordering — section 3 |
| **SSE** (`text/event-stream`) | a server → browser stream: progress, notifications, AI model responses token by token | one-way; reconnection with `Last-Event-ID`; proxies and timeouts must let long connections through |
| **WebSocket** | two-way and with low latency: chat, live collaboration, games | stateful connections (scaling, sticky sessions or a broker), your own message protocol, authentication at the handshake and token expiry during the session |
| **Response streaming** (NDJSON / JSON Lines, `application/json-seq` from RFC 7464) | a large result that the client processes on the fly (an export, logs) | a separate endpoint or a type in `Accept`, so that a client expecting JSON does not get several objects |
| **Polling** | rare changes, a client without a public address, simplicity | a delay of up to the interval length, the cost of empty queries; set a sensible interval and an `ETag` (304 instead of a full response) |

## 2. Synchronous or asynchronous
- An operation longer than a few seconds (an import, a report, AI generation) → **`202 Accepted`** with a `Location` header
  pointing to a status resource (`/jobs/{id}`: `pending | running | succeeded | failed`, the result or a link to the result). The client
  polls with `Retry-After` or gets a webhook or SSE on completion.
- Submitting a job is idempotent (`Idempotency-Key`), and cancellation is a separate action (`POST /jobs/{id}/cancel`).
- Between your own services, instead of a chain of synchronous calls — events through a broker (be-messaging-outbox).

## 3. Webhooks — the design on the sender's side
- **Signature**: HMAC-SHA256 of the body and a timestamp in a header (e.g. `Webhook-Signature`, `Webhook-Timestamp`);
  the receiver verifies the signature in constant time and rejects messages older than a few minutes (replay protection).
  A secret per subscription, with rotation (two valid secrets for a transition period).
- **At-least-once delivery**: retries with exponential backoff and random jitter for many hours, then
  a dead letter queue and a deliveries view for the customer (manual retry). Every event has an `id` — the receiver
  rejects duplicates.
- **Ordering is not guaranteed** — the event carries a version or a timestamp; a "thin" event (only the `id` and the type,
  the receiver fetches the current state through the API) avoids the stale data problem.
- The receiver responds quickly with `2xx` and processes asynchronously; a timeout on the sender's side (e.g. 10 s).
- **The client gives the URL → an SSRF risk** (OWASP API7): only `https`, blocking private addresses and cloud metadata,
  resolving DNS on every send.
- Events described in the documentation like a contract (e.g. AsyncAPI or JSON schemas), versioned like an API.

## 4. The API gateway and BFF
- **An API gateway**: cross-cutting concerns — routing, TLS termination, authentication, rate limits, logs
  and metrics, sometimes caching. **No business logic** — a rule in the gateway is a rule hidden from the domain tests.
  The gateway is a point every request passes through, so it must be highly available (several instances in different
  zones), scaled with traffic and covered by its own SLOs and alerts. Its failure takes down all services at once.
  Central authentication in the gateway does not exempt the services from authorization: a service checks the permissions to a specific
  resource and does not blindly trust traffic from the internal network (be-auth-security, OWASP API1).
- **Backend for Frontend**: a separate API fitted to one kind of client (web, mobile, the public API — by
  experience, not device). It assembles data from many services and shapes it for the screen. It is usually maintained by the team
  of that frontend. It does not copy business rules — it calls the services that have them.
- **A BFF as a token guard** (token handler): the browser gets an `HttpOnly; Secure; SameSite` cookie, and the OAuth tokens
  stay on the server side (be-auth-security, `tokens-sessions-oauth.md`).
- One client or clients with similar needs → a BFF is unnecessary; a well-designed API is enough.

## Sources
- [gRPC Core Concepts](https://grpc.io/docs/what-is-grpc/core-concepts/), [MDN: Using server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)
- [Hookdeck: When to use webhooks, WebSocket, pub/sub and polling](https://hookdeck.com/webhooks/guides/when-to-use-webhooks)
- [APIs You Won't Hate: Streaming data with REST APIs](https://apisyouwonthate.com/blog/streaming-data-with-rest-apis/)
- [bff-patterns.com](https://bff-patterns.com/); S. Newman, "Backends For Frontends"
- [roadmap.sh — API Design](https://roadmap.sh/api-design)
Described in our own words.
