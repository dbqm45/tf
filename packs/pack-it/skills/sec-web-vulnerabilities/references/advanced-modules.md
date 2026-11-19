# Advanced modules — chosen by the application's features

Every module: when to turn it on, what to look for in the code, how an attacker exploits it, the defence and the test. Proofs only
locally or in tests.

## A1. Business logic and races
**Turn on when:** money, credits, coupons, limits (votes, invitations, attempts), order states, refunds.

| Problem | In the code | Defence | Test |
|---|---|---|---|
| a "check, then write" race (CWE-362, TOCTOU) | `if (!coupon.used) { …; coupon.used = true }`, a balance read and written separately | one atomic conditional write: `UPDATE coupons SET used = true WHERE id = ? AND used = false` and a check of the number of changed rows; or `SELECT … FOR UPDATE` in a transaction; a uniqueness constraint (e.g. `UNIQUE(user_id, coupon_id)`) | N parallel requests (`Promise.all`, a thread pool) → exactly one succeeds |
| repeating a payment request | no idempotency key | `Idempotency-Key` saved with the result in the same transaction (be-api-design) | two identical requests → one charge |
| a state jump | `status` from the body, no state machine | allowed transitions in one place, the transition as a condition in `UPDATE … WHERE status = 'paid'` | `shipped` → `created` → 409 |
| negative and boundary values | quantity, amount, discount from the client | range validation on the server, the price from the server, not from the form | quantity −1, 0, 10⁹; price changed in the request → rejection or the price from the database |
| a limit bypassed in parallel | a counter read before the write | an atomic increment with a condition or a limiter with an atomic counter | N requests at once → at most the limit succeed |
| rounding | many small operations rounded down in the customer's favour | amounts in grosze (minor units, integers), rounding once, in one place | 1000 operations of 0.004 → the sum matches the rule |

You confirm a race only with a parallel test; a single request in a test will not show it.

## A2. The HTTP layer (CDN, proxy, cache)
**Turn on when:** a CDN, reverse proxy, load balancer, response cache, several servers in a chain.

| Problem | Mechanism | Defence | Test |
|---|---|---|---|
| request smuggling (CWE-444) | the front and the backend compute the body length differently (`Content-Length` vs `Transfer-Encoding`, HTTP/2 → HTTP/1.1) | HTTP/2 to the backend or normalization at the front, rejecting requests with both headers and an ambiguous `Transfer-Encoding`, an up-to-date proxy | a local proxy chain + backend, a request with both headers → 400 |
| web cache poisoning | a header outside the cache key (`X-Forwarded-Host`, `X-Original-URL`) changes the response | ignore unexpected headers or add them to the key (`Vary`), the host from configuration | a request with `X-Forwarded-Host: evil.example` → a response without that host, the cache does not store it |
| web cache deception | the address /account/profile.css reaches a dynamic page, and the CDN caches by extension | cache only for static paths from an allowlist, `Cache-Control: no-store, private` on pages with data, strict routing (404 for unknown suffixes) | the address /account/x.css with a session → `no-store`, no `HIT` for another session |
| Host header poisoning | a link in the reset e-mail built from the request's `Host` | the base address from configuration, an allowlist of hosts | a reset with `Host: evil.example` → a link with the domain from configuration |
| response splitting (CRLF, CWE-113) | input in a response header | libraries rejecting `\r\n`, no concatenation of headers | a value with `%0d%0a` → rejection |

## A3. Parsers and serialization
**Turn on when:** deep merging of objects from JSON, templates with user content, custom formats, deserialization,
regular expressions on input, comparing names/e-mails.

| Problem | In the code | Defence | Test |
|---|---|---|---|
| prototype pollution (CWE-1321) | `merge(target, req.body)`, `lodash.set` with a key from the user | reject `__proto__`, `constructor`, `prototype`; `Object.create(null)` or `Map`; schema validation with `additionalProperties: false` | `{"__proto__": {"isAdmin": true}}` → `({}).isAdmin === undefined` |
| SSTI (CWE-1336) | a template built from input (`render_template_string(user)`, `new Function`, `eval`) | input only as data for the template, never as the template; a sandbox is not a defence | `{{7*7}}`, `${7*7}`, `<%= 7*7 %>` → displayed literally |
| deserialization (CWE-502) | `pickle`, `ObjectInputStream`, `BinaryFormatter`, YAML with type tags | only data formats with a schema (be-auth-security) | a payload with a gadget in the test → rejection before deserialization |
| ReDoS (CWE-1333) | expressions with nested quantifiers (`(a+)+`, `(\w+\s?)*$`) on input | a linear engine (RE2, `re2`), an input length limit, simple expressions | 50,000 `a` characters + `!` → a response < 100 ms |
| Unicode normalization | comparing e-mails/logins before normalization; `ﬀ`, `İ`, full-width characters | NFKC + case folding before comparison and before a unique write; the same normalization everywhere | registering `Admin` and `Ａｄｍｉｎ` → a conflict |
| HTTP parameter pollution (HPP) | `?role=user&role=admin` read differently by the layers | one parsing library, rejecting repeated critical parameters | a repeated parameter → 400 |

## A4. The browser
**Turn on when:** CORS with credentials, `postMessage`, WebSocket, embedding in an iframe, a custom CSP, sensitive data
in GET responses.

| Problem | In the code | Defence | Test |
|---|---|---|---|
| CORS reflecting `Origin` (CWE-942) | `Access-Control-Allow-Origin: <origin from the request>` + `Allow-Credentials: true`, matching `endsWith('example.com')`, `null` allowed | an exact allowlist of origins, no `null`, no suffix patterns | `Origin: https://example.com.evil.example` and `null` → no CORS headers |
| `postMessage` | `addEventListener('message', e => …)` without checking `e.origin`; `postMessage(data, '*')` | check `event.origin` exactly, the target origin instead of `*`, data as data, not HTML | a message from a foreign origin → ignored |
| WebSocket without an Origin check (CSWSH, CWE-1385) | cookie authentication at the handshake | check `Origin` at the handshake or a token in the first message; authorization per message | a handshake with a foreign `Origin` → rejected |
| CSP bypasses | `'unsafe-inline'`, a CDN allowlist with JSONP or libraries with gadgets, no `base-uri`, `object-src` | strict CSP with a nonce and `strict-dynamic`, `base-uri 'none'`, `object-src 'none'` | a payload with `<base href>` and a script from an allowed CDN → blocked (CSP report) |
| DOM clobbering | `window.config || {}`, references to globals that `<form id=config>` can overwrite | explicit module variables, a sanitizer with clobbering protection | HTML with `id=config` → no effect on the logic |
| clickjacking | no `frame-ancestors` | `frame-ancestors 'none'` or a list | the page in an iframe from a foreign domain → blocked |
| XS-Leaks | a response dependent on the user's state, differing in time, size, number of frames | `Cross-Origin-Opener-Policy`, `Cross-Origin-Resource-Policy: same-origin`, `SameSite` cookies, `Sec-Fetch-*` on the server side (fetch metadata) | a request with `Sec-Fetch-Site: cross-site` to a sensitive GET → refusal |

## A5. APIs
**Turn on when:** automatic field binding, GraphQL, a public API, many clients.

| Problem | In the code | Defence | Test |
|---|---|---|---|
| mass assignment (CWE-915) | `User.update(req.body)`, `Object.assign(user, body)`, `@ModelAttribute` without a list of fields | a DTO/schema with an allowlist of fields for each operation (`pick(body, ['name','email'])`) | `{"role":"admin","tenantId":"other"}` → fields ignored or 400 |
| excess data in the response | serializing the whole entity | a response DTO | a snapshot without `passwordHash`, `resetToken` |
| GraphQL: introspection in production | the default configuration | disabled or only for authenticated tools | a `__schema` query without permissions → an error |
| GraphQL: depth, cost, batching, aliases | no limits; aliases bypass the login attempt limit | limits on depth, cost and the number of operations/aliases in a request; authorization in resolvers, not only at the gateway | a query with 100 login aliases → rejection |
| no limits | expensive endpoints, export, search | limits per user and per IP, pagination with a maximum (be-api-design) | N+1 requests over the limit → 429 |
| BFLA in an API | admin methods on the same path (`DELETE /users/{id}`) | authorization per action in one module | `DELETE` with an ordinary user's session → 403 |

## A6. The application's surroundings
**Turn on when:** own domains and subdomains, file buckets, preview environments, internal services reachable
from the application.

| Problem | Mechanism | Defence | Test or control |
|---|---|---|---|
| subdomain takeover | a CNAME record points to a deleted service (a static site, a cloud application), the attacker creates it | a DNS inventory, deleting records together with the resource, periodic scanning for dangling records | the CNAME list → every target exists and belongs to you |
| DNS rebinding against local services | a development server or panel on `localhost` without a `Host` check | a `Host` allowlist, authentication also locally | a request with `Host: evil.example` to a local service → 403 |
| a public bucket | a "public" ACL, signed URLs with a long lifetime | blocking public access at the account level, short signed URLs, a separate bucket for public content (sec-cloud-security) | anonymous listing and reading → refusal |
| preview and debug environments | `/debug`, `/actuator`, `/_next/` with source maps, Swagger with real data | disabled in production or behind authentication, previews without production data | a scan of a list of known paths on the test environment → 404 |
| cookies for the parent domain | `Domain=.example.com` → every subdomain reads and sets them | cookies without `Domain` (host only), the `__Host-` prefix | the session's `Set-Cookie` header has `__Host-` and no `Domain` |

## Sources
- PortSwigger Web Security Academy (portswigger.net/web-security) [unverified, accessed 2026-11-07] — request
  smuggling, web cache poisoning and deception, prototype pollution, SSTI, race conditions, DOM clobbering.
- OWASP API Security Top 10 2023 (owasp.org) [unverified] — BOLA, BFLA, mass assignment, limits.
- MITRE CWE (cwe.mitre.org) — class identifiers.
- W3C Fetch Metadata Request Headers, Cross-Origin-Opener-Policy (MDN) [unverified] — defence against XS-Leaks.

Described in our own words.
