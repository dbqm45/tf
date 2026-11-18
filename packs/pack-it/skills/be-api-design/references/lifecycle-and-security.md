# API lifecycle, security and tests

## 1. The contract first (design-first)
1. Resources from the domain language (the glossary, ddd-facilitation): nouns the expert recognizes, not table names.
   An API resource ≠ a table ≠ an aggregate — you model what the client needs.
2. The OpenAPI spec in a PR **before** the implementation; a review by the consumers.
3. Spec lint in CI (e.g. Spectral with the team's rules: names, error codes, pagination, descriptions, examples).
4. A mock from the spec (e.g. Prism) — the frontend and integrators start work in parallel.
5. Implementation and contract tests (section 4). The documentation generated from the spec, with examples and a description of errors.

## 2. Versioning and retirement
- **Additive evolution** as the principle: new optional fields, new endpoints, new values only where clients
  are prepared for them (an enum in a response — document that it may grow). Clients ignore unknown fields.
- A breaking change → a new major version. In the URL (`/v2/…`) for public APIs (visible, easy in routing and logs);
  a header or a media type only when the team and the clients can handle it. One strategy across the organization.
- **Retirement** announced in responses:
  - `Deprecation: @<unix-timestamp>` (RFC 9745) — since when it is deprecated;
  - `Sunset: <HTTP date>` (RFC 8594) — when it will stop responding (not earlier than the date from `Deprecation`);
  - `Link: <…>; rel="deprecation"` — the migration documentation.
  Plus monitoring who still uses the old version (logs per client), and contacting them before switching it off.
- **Inventory** (OWASP API9): a list of hosts, versions, environments and owners; no forgotten `/v1`, debug
  endpoints and test environments with real data.

## 3. Security — OWASP API Security Top 10 (2023)
| Risk | Control |
|---|---|
| API1 — object-level authorization (BOLA/IDOR) | every call with an identifier checks whether *this* user has the right to *this* object (be-auth-security); tests with two accounts |
| API2 — authentication | proven libraries, login attempt limits, short-lived tokens (be-auth-security) |
| API3 — property-level authorization | DTOs with an explicit list of fields on input and output; no mass assignment (`role`, `price` from the body ignored or rejected); no excess data in the response |
| API4 — unrestricted resource consumption | request limits, body size, `limit` in pagination, timeouts, GraphQL query cost limits, limits on sending SMS and emails |
| API5 — function-level authorization | admin endpoints separate, deny by default, tests "an ordinary user → an admin endpoint = 403" |
| API6 — unrestricted access to business flows | limits per flow (purchase, registration, booking), automation detection, not only a technical limit |
| API7 — SSRF | a URL from the user only through an allowlist and blocking internal addresses (be-auth-security, webhooks) |
| API8 — security misconfiguration | security headers, CORS with an allowlist, no stack traces, TLS everywhere, disabled methods and debug features |
| API9 — improper inventory management | section 2 |
| API10 — unsafe consumption of third-party APIs | responses of external APIs validated like user input, timeouts, no blindly following redirects |

## 4. API keys (for server–server, not for users in the browser)
- Generated from a CSPRNG, at least 128 bits of randomness; a **prefix** with the type and environment (e.g. `acme_live_…`,
  `acme_test_…`), so that secret scanners and people recognize the key (ops-secrets-identities).
- In the database only a **hash** (SHA-256 is enough for high-entropy keys) and the first few characters for identification;
  the full key shown once, at creation.
- Scopes and, where possible, a restriction to addresses or environments; an expiry date; an owner.
- Rotation with overlap: two active keys for the transition, then revoking the old one. Immediate
  revocation after a leak and a usage log per key.
- The key only in a header (`Authorization` or a dedicated one), **never in the URL** — it ends up in logs, history and the `Referer` header.

## 5. API tests
- **Contract**:
  - the provider checks that the responses match the OpenAPI spec (schema validation in integration tests);
  - with many internal consumers — consumer-driven contract tests (Pact), run in the provider's
    CI before a release.
- **Integration** over real HTTP with a test database: success, validation, 401/403/404, conflicts, idempotency,
  pagination (page boundaries).
- **Mocks**: from the spec (Prism) for parallel teams; in frontend tests MSW at the network level (tool-vitest).
- **Performance** (e.g. k6): a scenario from real traffic, a target from the SLO (p95, the error rate), a load test
  and a stress test before traffic grows (ops-sre-incidents).
- **Security**: BOLA tests with two accounts, input fuzzing from the spec, a DAST scan on staging.

## 6. Personal data and regulations
- Minimization: the API returns only the fields the client needs; special data (health, finance) behind a separate scope.
- Logs without request bodies with personal data, tokens and card numbers (masking). Retention per the policy.
- GDPR: the rights of access and erasure as API operations or a procedure; payment card data through the payment provider
  (tokenization), so as not to enter the full PCI DSS scope. The legal department confirms the legal details — the agent does not
  decide on compliance.

## Sources
- [OWASP API Security Top 10 — 2023](https://owasp.org/API-Security/editions/2023/en/0x11-t10/)
- [RFC 9745 — Deprecation header](https://www.rfc-editor.org/rfc/rfc9745.html), RFC 8594 — Sunset header
- [roadmap.sh — API Design](https://roadmap.sh/api-design) (lifecycle, versioning, API keys, testing, standards and compliance)
Described in our own words.
