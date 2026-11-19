---
name: sec-web-vulnerabilities
description: Use when writing or auditing web application code for vulnerabilities — IDOR, XSS, CSRF, SSRF, upload, injection, filter bypasses, advanced modules.
metadata:
  review: "2027-05-07"
  catalog: "Use when you write, review or audit the code of a web application or API (also one written quickly with AI help) and need to think like a bug hunter: where a given vulnerability class hides, how an attacker bypasses a typical filter, which defence is effective and which test proves it. Core classes: access control (IDOR/BOLA, BFLA), XSS, CSRF, client-side secrets, open redirect, SSRF, file upload, SQL/NoSQL/command injection, XXE, path traversal, security headers, JWT errors. Advanced modules to choose from: business logic and races, the HTTP layer (smuggling, cache poisoning and cache deception, the Host header), parsers and serialization (prototype pollution, SSTI, deserialization, ReDoS, Unicode normalization), the browser (CORS, postMessage, WebSocket, CSP bypasses, XS-Leaks), APIs (mass assignment, GraphQL, limits), the application's surroundings (subdomain takeover, DNS rebinding, public buckets). A report with a verdict, CWE, file:line, proof and a test. Not for designing sessions, tokens and OAuth (be-auth-security), an AppSec programme, scanners and SLAs (sec-appsec-devsecops), finding variants of a found bug (sec-variant-analysis), writing Semgrep rules (tool-semgrep), a threat model (arch-threat-modeling) or LLM applications (sec-llm-security)."
  keywords: "czy ten kod jest bezpieczny, podatności w aplikacji webowej, vibe coding bezpieczeństwo, kod od AI bezpieczny, audyt bezpieczeństwa aplikacji, przegląd bezpieczeństwa kodu, jak atakujący to obejdzie, obejście filtra, bug bounty, łowca błędów, idor, bola, cudze dane po zmianie id, xss, stored xss, reflected xss, dom xss, location.hash w innerhtml, csrf, ssrf, podgląd linku, pobieranie url od użytkownika, upload plików, wgrywanie plików, sql injection, nosql injection, command injection, xxe, path traversal, open redirect, klucz api w frontendzie, nagłówki bezpieczeństwa, csp, jwt alg none, wyścig, race condition, kupon użyty kilka razy, podwójne naliczenie, request smuggling, cache poisoning, web cache deception, prototype pollution, ssti, mass assignment, graphql introspekcja, cors, postmessage, websocket origin, przejęcie subdomeny, cdn, cache na cdn, pamięć podręczna, użytkownik widzi cudzą stronę, cudze dane konta pod tym samym adresem, strona ustawień w cache, is this code secure, web application vulnerabilities, vibe coding security, is AI-generated code secure, application security audit, code security review, how will an attacker bypass this, filter bypass, bug hunter, someone else's data after changing the id, location.hash in innerhtml, link preview, fetching a url from the user, file upload, uploading files, api key in the frontend, security headers, race, coupon used several times, double charge, graphql introspection, subdomain takeover, cache on cdn, user sees someone else's page, someone else's account data at the same address, settings page in cache"
---

# Web application vulnerabilities — writing and auditing through an attacker's eyes

Goal: the web application code contains no known vulnerability classes, and every defence has a test that shows it works.
You think like a bug hunter: at every input you ask "what if the attacker controls this" and "how would I bypass this
control". You work only on code that is yours or that you have permission for; proof of a vulnerability is a test
in the repository or a request to a local instance, never an attack on someone else's or a production system (core-agent-security).

## Modes
| Mode | When | What you do |
|---|---|---|
| **writing** | a new feature, endpoint, form | before the code: the "input → class → defence → test" table (below); you write the defence right away, the test before the implementation (TDD) |
| **review** | a diff, a PR | only the classes the diff touches (map below); a finding without proof from the diff is a question, not a bug |
| **core audit** | an application, a module, before a release | all classes from `references/core-classes.md` in order, with bypasses |
| **advanced audit** | on request or when the application has money, many tenants, cache/CDN, its own parsers | the core audit + selected modules from `references/advanced-modules.md` |

You choose the advanced modules by the application's features, not all at once:
- **A1 logic and races** — money, coupons, limits, order states, invitations;
- **A2 the HTTP layer** — CDN, reverse proxy, cache, several servers in a chain;
- **A3 parsers and serialization** — merging objects from JSON, templates with user content, custom formats, regular
  expressions on input;
- **A4 the browser** — CORS with credentials, `postMessage`, WebSocket, embedding in an iframe, CSP;
- **A5 APIs** — automatic field binding, GraphQL, a public API with limits;
- **A6 the surroundings** — own domains and subdomains, file buckets, internal services reachable from the application.

## Map: what in the code → which class
| In the code you see | Check |
|---|---|
| an identifier from the URL, body or a header used for a read/write | access control per object (IDOR, CWE-639) and per function (BFLA, CWE-285) |
| HTML from data, `innerHTML`, `dangerouslySetInnerHTML`, `v-html`, a template without escaping | XSS (CWE-79): stored, reflected, DOM; the output context |
| a state change via the session cookie | CSRF (CWE-352), `SameSite`, token, method |
| a URL from the user fetched by the server (webhook, preview, import, PDF from HTML) | SSRF (CWE-918) |
| a `next`, `returnUrl`, `redirect` parameter | open redirect (CWE-601) |
| a file from the user | upload (CWE-434), path traversal (CWE-22), XXE in SVG/DOCX (CWE-611) |
| concatenating SQL, NoSQL filters, shell commands, paths | injection (CWE-89, CWE-943, CWE-78), CWE-22 |
| a key, token, internal URL in the frontend code or in a `NEXT_PUBLIC_*`/`VITE_*` variable | a secret in the client (CWE-798, CWE-200) |
| JWT verification | `alg`, key, `aud`/`iss`/`exp` (CWE-347) — session details in be-auth-security |
| "check, then write" on a shared resource | race (CWE-362) — module A1 |
| `Object.assign(model, req.body)`, `Model.update(req.body)` | mass assignment (CWE-915) — module A5 |

## Audit procedure
1. **Scope and the input map:** routes, server actions, webhook handlers, queues, scheduled jobs, upload. For each:
   who can call it (anonymous, user, admin, another tenant), what data it accepts, what it changes.
2. **Core classes** per `references/core-classes.md`: for each, first find the places (grep by the patterns from the
   file), then check the defence and its bypasses. Do not stop at the first finding in a class.
3. **Advanced modules** — only the selected ones (above), per `references/advanced-modules.md`.
4. **Proof:** for every finding a test that fails without the fix (a request from another user, parallel
   requests, a bypass payload). Without proof a finding has the severity "to be confirmed".
5. **Fix at the source:** one shared function (e.g. `loadOwned(model, id, user)`), not patches in every endpoint.
   The same bug in many places → sec-variant-analysis; a rule blocking new occurrences → tool-semgrep.
6. **Report** in the format below.

## Report format
The first line — also for a single finding or an entry in someone else's report:
`Werdykt: BLOKUJE | DO POPRAWY | BEZ USTALEŃ` (verdict: blocks / to fix / no findings; BLOKUJE for critical or high severity with proof). Then a table; every finding has a CWE number (e.g. CWE-639 for IDOR), also in the audit plan for every
class, so that reports can be compared and linked with scanner rules:

| ID | Class (CWE) | Location (file:line) | Proof | Severity | Fix | Test |
|---|---|---|---|---|---|---|

Severity: critical (remote, without login, someone else's data or code), high (after login, someone else's data or money),
medium (requires victim interaction or a rare condition), low (hardening). At the end: the scope (what was checked,
which advanced modules, what not) — no findings in an unchecked part is not a verdict.

## Example
Input: "Endpoint `GET /api/invoices/:id` with `requireLogin`, returns `Invoice.findById(req.params.id)`".

Result:
```
Werdykt: BLOKUJE
| W1 | IDOR (CWE-639) | src/routes/invoices.ts:14 | user B fetches invoice A by changing the id (test) | high |
  query with the owner: Invoice.findOne({ _id: id, tenantId: user.tenantId }), none → 404 |
  test: invoice A, session B → 404; session A → 200 |
Scope: routes /api/invoices/*; other routes with :id — to be checked with the same pattern (sec-variant-analysis).
```
A 404 response instead of 403 does not reveal that the object exists. `requireLogin` alone checks identity, not the right to
the object.

## Writing a new feature — the table before the code
| Input | Class | Defence | Test |
|---|---|---|---|
| `invoiceId` from the URL | IDOR | the query always with `tenantId`/`ownerId` from the session | a foreign user → 404 |
| `returnUrl` | open redirect | only a relative path from an allowlist, without `//` and `\` | `//evil.example`, `/\evil.example` → the home page |
| webhook URL | SSRF | an allowlist of schemes and ports, DNS resolution and blocking of private ranges on every connection, no redirects | `http://169.254.169.254/`, a name resolving to `10.0.0.1` → refusal |

## Checklist
- [ ] every input has a class, a defence and a test; the defences in one module, not scattered
- [ ] server-side access control per object and per function, deny by default
- [ ] in an audit: all core classes and the selected advanced modules, the scope recorded
- [ ] a report with the verdict in the first line, CWE, file:line, proof and a test
- [ ] proofs only locally or in tests; no attacks on systems without permission

## Sources
- OWASP Web Security Testing Guide v4.2 (owasp.org, stable version, [unverified] accessed 2026-11-07) — test classes.
- OWASP ASVS 5.0.0 (owasp.org, May 2025, [unverified] accessed 2026-11-07) — verification requirements.
- MITRE CWE (cwe.mitre.org) — the class identifiers used in the tables.
- PortSwigger Web Security Academy (portswigger.net/web-security, [unverified] accessed 2026-11-07) — bypass
  techniques and advanced classes (smuggling, cache, prototype pollution, races).

Described in our own words.
