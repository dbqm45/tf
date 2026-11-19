# API security checklist — before a release and in review

> **Contents:** Authentication · JWT · Access and transport · Authorization and OAuth · Input · Processing · Output · CI/CD · Monitoring

Based on the roadmap.sh list "API Security Best Practices" and its source (shieldfy/API-Security-Checklist, MIT),
with corrections where the list simplifies. The OWASP API Top 10 risks and controls: be-api-design,
`lifecycle-and-security.md`. Tick only what you checked (a test, a configuration, a scan) — not what "should be".

## Authentication
- [ ] A standard instead of your own mechanism: OAuth 2 / OIDC through an IdP or the framework's sessions (SKILL.md). A note on the list:
  "JWT instead of Basic Auth" is a shorthand. JWT is a token format, not a login protocol, and is not by itself
  more secure. Basic Auth drops out because it sends a fixed password with every request.
- [ ] Login protection: a growing delay and a limit per account **and** per IP, a CAPTCHA or another challenge after suspicious
  activity. A hard account lockout after N attempts lets an attacker lock other people's accounts — apply it carefully
  and for a time.
- [ ] Sensitive data encrypted in transit (TLS) and at rest (database or field encryption); keys in a key manager
  (KMS, an HSM for high-stakes signatures), not in the code (ops-secrets-identities).

## JWT
- [ ] **The algorithm fixed on the server side** (an allowlist, e.g. only `RS256` or `EdDSA`), never taken from the token header;
  `alg: none` and an RS→HS swap rejected. Verification of `iss`, `aud`, `exp`, `nbf` (SKILL.md).
- [ ] Between services an asymmetric signature: the services verify with a public key from JWKS, chosen by the `kid` from a list
  of known keys, with a cache and rotation. HS256 only within one service, with a secret of ≥ 256 bits from a CSPRNG.
- [ ] A short access token lifetime (≤ 15 min) and a rotated refresh token (`tokens-sessions-oauth.md`).
- [ ] Nothing confidential in the token body — it is base64, not encryption. A small payload (an identifier, scopes), because the token
  travels in every request and in proxy headers.

## Access and transport
- [ ] Rate limits per key/user and per IP, separately for login and expensive operations (be-api-design, `http-in-practice.md`).
- [ ] TLS 1.2+ (1.3 preferred) with modern ciphers; certificates monitored (ops-observability).
- [ ] `Strict-Transport-Security: max-age=31536000; includeSubDomains` on API domains (the preload list only consciously —
  it is hard to get off it).
- [ ] No directory listing and no static files from the API server; debug mode, admin consoles
  and test documentation turned off in production (OWASP API8, API9).
- [ ] A private API reachable only from a private network or an allowlist, **and still with authentication** — the network is an extra
  layer, not the only one.
- [ ] Between services: mTLS or workload identity tokens; every request validated also from internal services
  (zero trust — an attacker who gets into the network does not get everything).

## Authorization and OAuth
- [ ] `redirect_uri` compared exactly with the registered list; Authorization Code + PKCE, without `response_type=token`
  (implicit); `state` (or PKCE) against CSRF in login; a minimal scope by default and scope validation per client
  (SKILL.md, OAuth/OIDC).
- [ ] Every endpoint behind authentication, unless it is explicitly public — a test that goes through all routes
  and checks 401 without a token.
- [ ] The current user's resources through `/me/...` instead of `/users/{id}/...` — fewer opportunities for BOLA. Unpredictable
  identifiers (UUID v4, or v7 when the order in the index matters) make guessing harder, but **do not replace**
  checking permissions to the object.

## Input
- [ ] The right HTTP method; another one → `405` with an `Allow` header.
- [ ] Supported formats in `Accept` (otherwise `406`) and in the request `Content-Type` (otherwise `415`).
- [ ] Schema validation and size limits (SKILL.md: input and output); parameterized SQL, no interpolation
  in system commands.
- [ ] **XML**: DTDs and external entities disabled (XXE). In Java e.g.
  `DocumentBuilderFactory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true)`.
- [ ] **XML/YAML with aliases**: an expansion limit (protection against "billion laughs"). SnakeYAML — `LoaderOptions` with an alias
  limit; the `yaml` package in JS — `maxAliasCount`; parsers only in safe mode (without creating arbitrary types).
- [ ] Secrets never in the URL (logs, history, `Referer`) — only the `Authorization` header or a dedicated one.
- [ ] Files: uploading directly to an object store through a short-lived signed URL, with a size and type limit,
  a malware scan and serving from a separate domain (otherwise an HTML/SVG file executes in your origin).

## Processing
- [ ] Heavy operations in the background (a queue, workers) and a fast `202` response (be-api-design) — long requests block
  the thread pool and make DoS easier.
- [ ] GraphQL: introspection disabled in production, depth and cost limits, a query allowlist.
- [ ] High-stakes operations (a transfer, a permission change, webhooks) with a request signature: HTTP Message Signatures
  (RFC 9421) or an HMAC with a time and an identifier (replay protection).
- [ ] A hardened runtime: a container without root, a read-only file system, without unneeded tools
  (ops-docker). The list's item on a "non-executable stack" is provided today by the system and the compiler, not the API code.

## Output
- [ ] API responses with headers: `X-Content-Type-Options: nosniff`, `Content-Security-Policy: default-src 'none';
  frame-ancestors 'none'` (for JSON), `X-Frame-Options: DENY` for older browsers, `Cache-Control: no-store`
  for private data.
- [ ] A `Content-Type` matching the content (`application/json; charset=utf-8`), never guessed.
- [ ] Removed headers that reveal the stack (`X-Powered-By` — in Express `app.disable('x-powered-by')`, `Server` with a version).
- [ ] Generic errors for the client (RFC 9457 without a stack trace and SQL content), details only in the logs with a correlation
  identifier given in the response.
- [ ] No passwords, tokens, secrets and excess fields in responses (OWASP API3); correct status codes.

## CI/CD
- [ ] Unit and integration tests cover authorization (a matrix: `authorization-models.md`) and validation.
- [ ] A review without self-approval (branch protection, CODEOWNERS); changes from an AI agent through the same process
  (ops-ci-cd).
- [ ] SAST and a secret scan in every PR; DAST on staging; a dependency and image scan (SCA) with a remediation policy
  (ops-supply-chain-security).
- [ ] A rehearsed deployment rollback (ops-release-engineering).

## Monitoring
- [ ] Centralized logs, with security events (logins, authorization denials, permission changes, key
  usage) and without sensitive data (passwords, cards, tokens, PINs — masking before writing).
- [ ] Alerts on anomalies: a spike of 401/403/429, unusual hours, volume or endpoint sequences, many objects
  from one account (a BOLA and scraping signal).
- [ ] A WAF or IDS/IPS in front of a public API as an extra layer — not instead of validation and authorization in the code.

## Sources
- [roadmap.sh — API Security Best Practices](https://roadmap.sh/api-security-best-practices) (in the roadmap data the "Input"
  group duplicates items of the "Access Control" group; the missing items taken from the list's source).
- [shieldfy/API-Security-Checklist](https://github.com/shieldfy/API-Security-Checklist) (MIT, as of 07.2026).
- OWASP Cheat Sheets: XML External Entity Prevention, Authentication, REST Security, JSON Web Token;
  RFC 9421 (HTTP Message Signatures), RFC 6797 (HSTS).
Described in our own words, with corrections.
