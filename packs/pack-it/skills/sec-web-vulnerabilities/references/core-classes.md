# Core classes — signals, bypasses, the correct defence, proof

> **Contents:** 1. Access control — IDOR/BOLA (CWE-639), BFLA (CWE-285) · 2. XSS (CWE-79) · 3. CSRF (CWE-352) · 4. Secrets and excess data on the client side (CWE-798,… · 5. Open redirect (CWE-601) · 6. Passwords · 7. SSRF (CWE-918) · 8. File upload (CWE-434) · 9. Injection — SQL (CWE-89), NoSQL (CWE-943), OS commands… · 10. XXE (CWE-611) · 11. Path traversal (CWE-22) · 12. Security headers · 13. JWT (CWE-347)

Every class has the same layout:
- **Signals** — what you look for in the code;
- **Bypasses** — how an attacker defeats a typical, incomplete defence;
- **Correctly** — a defence that works;
- **Proof** — a test that fails without the fix.

Common rule: every input is under the attacker's control until the server proves otherwise. The defence sits on the
server, is in one module and denies on error. Validation in the browser is only a convenience for the user.

## 1. Access control — IDOR/BOLA (CWE-639), BFLA (CWE-285)
**Signals:** `findById(req.params.id)`, `WHERE id = ?` without the owner column, an identifier from the body or a header
(`X-User-Id`, `tenantId` in JSON), endpoints for export, search, attachments and bulk operations. Also a child
resource checked without its parent (a comment without the post, a file without the project) and a role read from the client's token or
from the body.

**Bypasses:**
- changing the number in the URL, and with a UUID — an identifier from another place where it leaks (a list, an e-mail, a log);
- a method nobody secured (`PUT` next to a protected `GET`);
- an old API version (`/v1/` without the check, when `/v2/` has it);
- a parameter added to the body (`"ownerId": "…"`).

**Correctly:**
- an ownership filter in the query itself, with the user or tenant identifier taken from the session;
- one function in the style of `loadOwned(model, id, user)`, not a condition added in every controller;
- deny by default;
- a 404 response both for a non-existent object and for someone else's.

Unguessable identifiers make enumeration harder, but they are not access control. Losing membership in an organization
removes access immediately (session invalidation: be-auth-security).

**Proof:**
- user A's resource, a request with session B → 404;
- an administrator function with an ordinary user's session → 403/404;
- the same cases for every HTTP method on the path.

## 2. XSS (CWE-79)
**Three types — they differ in where the payload waits and who inserts it:**
| Type | Payload path | Where to look | Trap |
|---|---|---|---|
| stored | the attacker saves content, the victim displays it | comments, profiles, file names, messages, logs in the admin panel | it also reaches places outside the application: e-mails, PDFs, export to CSV/HTML, the administrator panel |
| reflected | the payload in the request (parameter, path, header) comes back in the response | search pages, error messages, redirects with a parameter | the victim clicks a crafted link; a 404 error page that repeats the path |
| DOM-based | a script in the browser takes a value from a source (`location`, `hash`, `postMessage`, `localStorage`) and inserts it into a sink | frontend code: `location.hash` → `innerHTML`, routers reading parameters | the server sees nothing (the `#` fragment is not sent), so server-side escaping and a WAF do not help; the defence is only in the client code |

**Signals — sinks:** `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `dangerouslySetInnerHTML`,
`v-html`, `[innerHTML]`, `bypassSecurityTrust*`, `|safe`, `{!! !!}`, `href`/`src` from data, and `eval` and `setTimeout`
with a string.

**Signals — sources outside a form:**
- the query string and the `#` fragment;
- the name of an uploaded file;
- headers shown in a panel (User-Agent in logs);
- data from an external API;
- WebSocket and `postMessage` messages;
- values from `localStorage`;
- Markdown content with HTML allowed;
- SVG files;
- e-mail and PDF templates generated from HTML;
- error messages that repeat the input.

**Bypasses:**
- a context other than assumed: a value inserted into an attribute without quotes or into an inline script;
- a `javascript:` link in the "website" field;
- a blacklist filter bypassed with letter case, encoding or another event (`onfocus`, `ontoggle`);
- a sanitizer run before further text processing (mutation XSS).

**Correctly:**
- the framework's escaping stays on; every sink from the list above goes through review;
- HTML from the user only through a sanitizer with an allowlist (e.g. DOMPurify), run **last**, right before
  insertion;
- a URL from data only with the `https:` scheme (possibly `mailto:`);
- a second line of defence: CSP with a nonce or hash, without `'unsafe-inline'` and `'unsafe-eval'` in `script-src`, with `object-src 'none'`
  and `base-uri 'none'` (module A4);
- `X-Content-Type-Options: nosniff`.

**Proof** (separately for each type, payloads for each context: `<img src=x onerror=alert(1)>`,
`" autofocus onfocus=alert(1) x="`, `javascript:alert(1)`):
- stored: a payload saved through the API, then the page displaying it in the application, in an e-mail and in the admin panel →
  text, no execution (e2e or a rendering test);
- reflected: a payload in a parameter and in the path (`/search?q=…`, `/doesnotexist/<payload>`) → a response with escaped
  text (an integration test of the HTML response);
- DOM: the page opened with the payload in `#` and in `postMessage` → no execution (e2e in a browser, e.g. Playwright,
  listening for `dialog`), because a server-side test will not detect it.

## 3. CSRF (CWE-352)
**Signals:**
- a session in a cookie and an endpoint that changes state without a token;
- a `GET` that changes something (`/unsubscribe?id=`, `/approve?id=`);
- token validation only when it came in the request;
- login, registration, password reset, e-mail change and the OAuth callback without protection — the attack also works before
  login: the victim gets logged in to the attacker's account.

**Bypasses:**
- JSON sent by a form as `text/plain`, and the server parses it without checking the type;
- a `SameSite=Lax` cookie with a state change via `GET`;
- an attacker's (or taken-over) subdomain sets the token cookie in the double submit variant;
- CORS with credentials and a reflected origin (module A4).

**Correctly:**
- a random token, bound to the session, in a header, always required — a missing token means rejection;
- a new token after login;
- session cookies `SameSite=Lax` or `Strict`, `Secure`, `HttpOnly`, with the `__Host-` prefix;
- the server checks `Origin` or `Sec-Fetch-Site`;
- state changes only with methods other than `GET`;
- the OAuth `state` bound to the session.

**Proof:** a state change with a valid cookie and without a token → 403; with `Origin: https://evil.example` → 403; `GET` on
a changing endpoint → 405.

## 4. Secrets and excess data on the client side (CWE-798, CWE-200)
**Signals:**
- public variables of build tools (`NEXT_PUBLIC_*`, `VITE_*`, `REACT_APP_*`, `PUBLIC_*`) with keys that allow
  writes or payments;
- importing a server module in a client component;
- source maps (`*.map`) deployed to production;
- hydration state (`__NEXT_DATA__`, `window.__INITIAL_STATE__`) with whole records;
- API responses returning the whole entity (password hash, reset token, full PESEL (national ID number), card number);
- stack traces and server versions in error responses;
- HTML comments and `data-*` attributes with internal addresses.

**Bypasses:** these are not bypasses, just reading: the attacker opens the JS bundle or the browser's developer tools.

**Correctly:**
- calls that need a secret only from the backend (route handler, server action, BFF);
- the secret in a secrets manager or in a server environment variable, in the repo only `.env.example` (ops-secrets-identities);
- responses through a DTO with an explicit list of fields;
- a key that is public by design (publishable key, maps key) restricted at the provider to a domain and scope;
- sensitive data masked in the UI (`***-***-123`);
- errors in production without technical details.

**Proof:** grep over the built bundle and source maps (`sk_live_`, `AKIA`, `-----BEGIN`, `secret`, variable names
from `.env.example`); a snapshot test of the API response without sensitive fields.

## 5. Open redirect (CWE-601)
**Signals:** `res.redirect(req.query.next)`, `window.location = params.get('returnUrl')`, `redirect_uri` checked
with `startsWith` or `includes`.

**Bypasses:**
| Input | What happens |
|---|---|
| `//evil.example` | a scheme-relative URL: the browser goes to a foreign host |
| `/\evil.example`, `\/evil.example` | browsers treat `\` like `/` |
| `https://app.example@evil.example` | the part before `@` is the user name, the host is `evil.example` |
| `https://app.example.evil.example` | `startsWith('https://app.example')` lets a foreign domain through |
| `https://app.example#@evil.example`, `?@` | different parsers understand the host differently |
| `%2f%2fevil.example`, `%252f%252f…` | validation before decoding, redirect after decoding (once or twice) |
| `%09`, `%0a`, `%00` in the address | characters removed by the browser or truncating the string |
| `javascript:…`, `data:text/html,…` | the redirect becomes XSS |
| `аpp.example` (Cyrillic "а") | an IDN homograph, looks like the trusted domain |

**Correctly (from the best):**
1. An indirect reference — `?to=settings` mapped to a fixed path.
2. Only a relative path: after decoding it starts with a single `/`, does not contain `//`, `\`, `@` or control
   characters.
3. A full URL only after parsing with the standard WHATWG parser, with an exact comparison of the host with an allowlist after
   conversion to Punycode and with the `https:` scheme.

**Proof:** a parameterized test in which every row of the table gives a redirect to the default page.

## 6. Passwords
Requirements per NIST SP 800-63B-4 (2025) [unverified]:
- a minimum length of 15 characters when the password is the only login factor, or 8 with MFA;
- a maximum of at least 64 characters;
- all characters allowed, also spaces and Unicode;
- no composition rules and no forced periodic change;
- a check against a list of breached passwords.

Storage: Argon2id, scrypt or bcrypt; never MD5, SHA-1 or a single SHA-256. Attempt limits, password reset
and MFA: be-auth-security.

## 7. SSRF (CWE-918)
**Signals:**
- the server fetches a URL from input: a webhook, a link preview, import from a URL, an avatar from an address, RSS, an integration with a customer's
  endpoint, a proxy;
- rendering HTML to PDF or an image — a headless browser fetches every `<img>` and `<iframe>` from the content;
- an XML parser with external entities (section 10).

**Bypasses:**
| Technique | Example |
|---|---|
| IPv4 notation other than dotted | `2130706433`, `0177.0.0.1`, `0x7f000001`, `127.1` |
| IPv6 | `[::1]`, `[::]`, `[::ffff:127.0.0.1]`, `[fe80::1%25eth0]` |
| a name resolving to an internal address | `127.0.0.1.nip.io`, a CNAME to `db.internal` |
| DNS rebinding | the check sees a public address, the connection — an internal one (short TTL) |
| a redirect | a public URL responds `302 Location: http://169.254.169.254/` |
| parser differences | `http://evil.example#@internal`, `http://internal\@evil.example` |
| another scheme | `file://`, `gopher://`, `dict://` in libraries that support them |

**Correctly:**
1. An allowlist of hosts, when the integration allows it.
2. Otherwise:
   - only `http`/`https` on allowed ports;
   - DNS resolution on the application side and rejection of private, loopback, link-local, `0.0.0.0/8`, IPv6 ULA
     and IPv4-mapped addresses;
   - **a connection to the same address that was checked** (IP pinning in the HTTP client, e.g. a custom `lookup`
     in a Node agent), to close DNS rebinding.
3. Redirects disabled or every hop checked anew.
4. A time and response size limit; the user does not get the raw response or error details (blind SSRF
   is also SSRF).
5. Fetching in a separate service or network without access to internal resources.
6. Cloud metadata blocked explicitly: `169.254.169.254`, `fd00:ec2::254`, `metadata.google.internal`; on AWS
   IMDSv2 with a hop limit of 1.

**Proof:**
- every row of the table → refusal **before** the connection is made (a test with a fake resolver and a local server
  checking that it did not get a request);
- a redirect to `169.254.169.254` → refusal.

## 8. File upload (CWE-434)
**Signals:**
- saving under a name from the user;
- the upload directory served by the same server that executes scripts;
- checking only the `Content-Type` from the request or only the extension;
- unpacking archives;
- processing images with an external program with the file name in the command.

**Bypasses:**
| Trick | Example | What stops it |
|---|---|---|
| two extensions | `invoice.pdf.php`, `photo.php.jpg` | one extension from an allowlist, a random name |
| null byte, space, trailing dot | `shell.php%00.png`, `shell.php.` | a random name assigned by the server |
| a fake MIME type | a script sent as `image/png` | checking the signature and parsing |
| polyglot | a file that is both a valid GIF and a script | re-encoding the image (e.g. rescaling) |
| SVG with JavaScript | `<svg onload=…>` | an SVG sanitizer, conversion to PNG or a ban |
| an office document with XML | DOCX/XLSX with an external entity | a parser without DTD (section 10) |
| an archive with `../` | Zip Slip | path canonicalization of every entry (section 11) |
| a decompression bomb | a small ZIP, gigabytes after unpacking | a limit on total size and number of entries |
| file name in a command | `a.jpg; curl …` | a call without a shell, a random name |
| the browser guessing the type | HTML served as an "image" | `nosniff`, `Content-Type` from the detected type |

Signatures to check: JPEG `FF D8 FF`, PNG `89 50 4E 47 0D 0A 1A 0A`, GIF `47 49 46 38`, PDF `25 50 44 46`,
ZIP and DOCX/XLSX/PPTX `50 4B 03 04`.

**Correctly:**
- an allowlist of types confirmed by the signature **and** by parsing with a library for the given format;
- size limits in the application and on the proxy;
- a random name;
- object storage or a directory outside the webroot, without execute permission;
- serving from a separate domain with `Content-Disposition: attachment`, `nosniff` and a correct `Content-Type`;
- image libraries up to date, in a separate process (ImageMagick with a restrictive resource policy (policy.xml));
- documents with macros rejected or scanned.

**Proof:** every row of the table as a file in the test directory → rejection or safe serving (download
instead of execution).

## 9. Injection — SQL (CWE-89), NoSQL (CWE-943), OS commands (CWE-78)
**Signals — SQL:**
- string concatenation and template literals in a query;
- "raw" ORM methods with interpolation (`$queryRawUnsafe`, `sequelize.literal`, `knex.raw` with `${}`, `extra()`
  in Django);
- `ORDER BY`, column and table names, sort direction from a parameter;
- `LIMIT` without casting to a number;
- `IN` lists built by hand;
- `LIKE` without escaping `%` and `_`.

**Signals — NoSQL:** an object from JSON goes straight into a filter (`{ email, password: req.body.password }`), the
`$where` and `$regex` operators from input.

**Signals — commands:** `exec`, `system`, `shell=True`, `child_process.exec` with a string, file names and URLs
in a command.

**Bypasses:**
- injection where parameterization does not work (sorting);
- second order: a value saved safely, later used in a concatenated report query;
- `{"password": {"$ne": null}}` instead of a string;
- injecting a command option (`--output=/etc/…`) without using shell characters.

**Correctly:**
- always parameterized queries;
- identifiers (columns, direction) only from an allowlist;
- NoSQL input cast to simple types or validated with a schema;
- commands through `execFile`/`spawn`/`subprocess.run([...])` with an argument list, with `--` before the arguments from
  the user;
- a database user with minimal privileges (be-database);
- database errors do not reach the response.

**Proof:** `' OR '1'='1`, `1) OR (1=1`, sorting `name; DROP TABLE x`, `{"$ne": null}`, file name `a; id` →
rejection or a result identical to that for ordinary input.

## 10. XXE (CWE-611)
**Signals:**
- explicit: SOAP and XML-RPC endpoints, XML import, RSS/Atom feeds, configuration in XML from the client;
- hidden: DOCX/XLSX/PPTX (ZIP with XML), SVG, SAML assertions, conversions of other formats to XML.

**Bypasses:**
- an external entity reading a file (`file:///etc/passwd`) or making a request (SSRF);
- parameter entities and an external DTD when the result is not visible (out-of-band exfiltration);
- exponentially nested entities ("billion laughs").

**Correctly:**
- DTD processing disabled entirely (no external entities, external DTDs and XInclude), an up-to-date parser;
- where possible — JSON instead of XML;
- settings per language:

| Language | Setting |
|---|---|
| Java | `DocumentBuilderFactory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true)` (the same for SAX and StAX) |
| Python | `defusedxml` instead of `xml.etree`/`lxml` for external data |
| .NET | `XmlReaderSettings { DtdProcessing = DtdProcessing.Prohibit, XmlResolver = null }` |
| PHP 8+ | libxml ≥ 2.9 does not load entities by default; do not pass `LIBXML_NOENT` or `LIBXML_DTDLOAD` |
| Node.js | a parser without DTD support; in libxmljs `noent: false`, `dtdload: false` |

**Proof:** a document with `<!DOCTYPE x [<!ENTITY e SYSTEM "file:///etc/passwd">]><x>&e;</x>` → a parsing error or
the entity not expanded.

## 11. Path traversal (CWE-22)
**Signals:** `path.join(UPLOADS, req.query.file)`, `open(base + name)`, `res.sendFile(name)`, a template name
from a parameter, unpacking an archive with entry names.

**Bypasses:**
- `../`, and also `..%2f`, `%2e%2e/`, `....//` (when the filter removes `../` once) and `..\` on Windows;
- an absolute path (`/etc/passwd`, `C:\…`), which `path.join` in some languages accepts as a new root
  (Python `os.path.join`);
- a symbolic link inside the directory that leads outside it.

**Correctly:**
- an indirect reference (identifier → a path from the database or a map);
- otherwise canonicalization (`realpath`) and a check that the result lies in the base directory, plus an allowlist of characters
  and extensions.
```python
def inside(base_dir: str, name: str) -> str:
    base = os.path.realpath(base_dir)
    target = os.path.realpath(os.path.join(base, name))
    if os.path.commonpath([base, target]) != base:
        raise PermissionError(name)
    return target
```

**Proof:** every bypass from the list and a symbolic link leading outside the directory → refusal.

## 12. Security headers
| Header | Value | Purpose |
|---|---|---|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` (`preload` after a conscious decision, because it is hard to withdraw) | HTTPS only |
| `Content-Security-Policy` | strict CSP with a nonce, `frame-ancestors 'none'`, `object-src 'none'`, `base-uri 'none'` | a second line against XSS, clickjacking |
| `X-Content-Type-Options` | `nosniff` | no type guessing |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | tokens in URLs do not leak to foreign sites |
| `Cache-Control` | `no-store` on pages and responses with user data | no copy in a cache (module A2) |
| `Cross-Origin-Opener-Policy` | `same-origin` | window isolation (module A4) |

You add `X-Frame-Options: DENY` only for very old browsers.

**Proof:** an integration test of the headers on a representative page with data and on an API response.

## 13. JWT (CWE-347)
| Error | Effect | Correctly |
|---|---|---|
| the algorithm from the token header, `alg: none` | a token without a signature passes | a list of algorithms in the verification configuration |
| RS256 → HS256 | the public key used as the HMAC secret | `algorithms: ['RS256']`, a separate key type |
| a short HMAC secret | offline dictionary cracking | ≥ 256 random bits |
| `kid` in a file path or in SQL | traversal or injection | `kid` only as a key into a map of trusted keys |
| `jku`/`x5u` from the token | the attacker points to their own key | keys from configuration or a trusted JWKS |
| no `exp`, `aud`, `iss` | the token lives forever or works in another service | verification of all three |
| `decode` instead of `verify` | no signature verification | only `verify` on the authorization path |

```javascript
jwt.verify(token, publicKey, { algorithms: ['RS256'], audience: 'api', issuer: 'https://id.example' })
```

Storage in the browser:
- an `HttpOnly; Secure; SameSite` cookie protects against reading through XSS, but requires CSRF protection (section 3);
- a token in the application's memory with a short lifetime is also a correct choice;
- `localStorage` is out when XSS is a real risk;
- token rotation and invalidation: be-auth-security.

**Proof:** a token with `alg: none`, signed with the public key as HMAC, expired, with a foreign `aud` or `iss`
→ 401.

## Sources
- MITRE CWE (cwe.mitre.org) — class identifiers.
- OWASP Cheat Sheet Series: XSS Prevention, CSRF Prevention, SSRF Prevention, File Upload, XXE Prevention,
  JSON Web Token (cheatsheetseries.owasp.org) [unverified, accessed 2026-11-07].
- NIST SP 800-63B-4 (2025) [unverified] — password requirements.
- WHATWG URL Standard (url.spec.whatwg.org) — address parsing in browsers.

Described in our own words.
