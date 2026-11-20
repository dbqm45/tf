# TypeScript / Node code security

> **Contents:** The input boundary: `unknown` → validation → type · Backend (Node) · Frontend · The dependency chain (npm) · Checklist (TS-specific) · Tools

Scope: security pitfalls **specific to TS/JS and the npm ecosystem**. General principles (auth, passwords, sessions,
per-resource authorisation, headers, CORS, event logging, secret rotation) — be-auth-security; XSS, CSP, storage
in the browser — fe-web-platform; the client/server boundary and the front end's data layer — fe-architecture.
Examples checked in tsc 6.0.3/7.0.2 and run in Node 22.

**Thesis:** types are not a defence. They disappear at runtime, so they will not stop SQL injection, XSS, prototype pollution,
an attack on dependencies or a secret leak. `as`, `!` and `any` on external data are a security signal,
not just a style one.

## The input boundary: `unknown` → validation → type
- Data from a request, an API response, a queue, a file, `process.env`, `localStorage`, a URL is `unknown` until it
  passes a schema validator (Zod, Valibot, ArkType, class-validator…). Take the type from the validator (`z.infer`).
- `JSON.parse(x) as Dto` and `res.json() as Promise<Dto>` are casts, not validation.
- Configuration: validate `process.env` with a schema **at startup** — the application does not start with a missing/bad variable.
  Locally `node --env-file=.env` (Node ≥ 20.6) instead of extra packages; `.env` in `.gitignore`.

## Backend (Node)

### SQL injection — also through an ORM
```ts
const q = `SELECT * FROM users ORDER BY ${sortColumn} ${order}`;          // ❌ values from the request in SQL
```
Values — only as parameters (`$1`, `?`, a query builder's tagged template). Elements that cannot be
parameterised (the sort column, the direction) must not pass through — map them from a closed list:
```ts
const SORTABLE = ["name", "createdAt"] as const;
type SortColumn = (typeof SORTABLE)[number];
function parseSort(col: unknown, dir: unknown): { col: SortColumn; dir: "ASC" | "DESC" } {
  if (typeof col !== "string" || !(SORTABLE as readonly string[]).includes(col)) throw new RangeError("bad sort");
  return { col: col as SortColumn, dir: dir === "DESC" ? "DESC" : "ASC" };
}
```
Watch out for the "raw" ORM methods (`query`, `$queryRawUnsafe`, `.raw()`) — interpolation in them is injection.

### NoSQL injection (MongoDB)
```ts
await User.findOne({ username: req.body.username, password: req.body.password }); // ❌ body: {"$ne": null}
```
Validate the fields as primitives (`z.string()`) before they reach the query; do not let `$…` operators from the input through
(a schema, possibly `sanitizeFilter`/`mongo-sanitize` as a second layer).

### Prototype pollution
```ts
deepMerge(defaults, req.body); // ❌ {"__proto__": {"isAdmin": true}} changes Object.prototype
```
- A schema that rejects unknown keys (`z.strictObject`) instead of merging the whole input.
- Your own merge/set-by-path: skip `__proto__`, `constructor`, `prototype`; maps from the input as a `Map` or
  `Object.create(null)`; check keys with `Object.hasOwn`.
- `node --disable-proto=delete` removes the `__proto__` accessor in the whole process.

### JWT
```ts
jwt.verify(token, key);                                        // ❌ without a list of algorithms
jwt.verify(token, key, { algorithms: ["RS256"], issuer, audience }); // ✅
```
`decode()` does not verify the signature — never as authentication. Lifetime, refresh, verified claims —
be-auth-security. In new code consider the `jose` library (Web Crypto, it enforces the algorithm at the key).

### Constant-time comparison of secrets
```ts
if (provided === expected) { /* ❌ the time depends on the number of matching characters */ }

import { createHash, timingSafeEqual } from "node:crypto";
function safeEqual(a: string, b: string): boolean {
  // timingSafeEqual throws for buffers of different length — compare fixed-length hashes
  const ha = createHash("sha256").update(a).digest();
  const hb = createHash("sha256").update(b).digest();
  return timingSafeEqual(ha, hb);
}
```

### Templates (SSTI) and code execution
- User input never as a *template* (Nunjucks, EJS, Pug, Handlebars) — only as *data* for the template.
- No `eval`, `new Function`, `vm` as a "sandbox" (`vm` is not a security boundary),
  `child_process.exec` with interpolation — `execFile`/`spawn` with an argument array.

### Unsafe deserialisation
Libraries that recreate functions/classes from data (e.g. `node-serialize`, YAML with custom types) execute
code from the payload. External data: `JSON.parse` + schema validation.

### SSRF — parse the URL, do not compare strings
```ts
new URL("http://127.0.0.1@evil.com").hostname; // "evil.com" — `includes("127.0.0.1")` would let it through
new URL("http://0x7f.0.0.1/").hostname;        // "127.0.0.1"
```
Parse with `new URL()`, require `https:`, reject `username`/`password`, match the host against an allowlist; with
arbitrary hosts resolve DNS, reject private/link-local/metadata ranges and connect to **that** address
(DNS rebinding). The allowlist policy — be-auth-security.

### GraphQL
Introspection disabled in production; resolver arguments validated like a REST body; query depth/complexity
limits.

## Frontend

### XSS through URLs and HTML
```tsx
<a href={userUrl}>…</a>                       // ❌ `javascript:alert(1)` runs on click
<a href={safeHref(userUrl)}>…</a>              // ✅ only http(s)/mailto after `new URL()`
<a href={`/search?q=${encodeURIComponent(q)}`}>…</a> // URL segments always encoded
```
`dangerouslySetInnerHTML` / `[innerHTML]` / `v-html` only after DOMPurify; do not bypass the framework's sanitizer
(`bypassSecurityTrust…` in Angular). CSP, Trusted Types, `textContent` — fe-web-platform.

### Secrets in the client bundle
TypeScript does not know where the code will run — importing a module with a secret into shared code puts it in the bundle.
Only variables with the framework's public prefix (`NEXT_PUBLIC_`, `VITE_`, …) reach the client; mark server
modules (`import "server-only"` in Next.js, a separate directory/project with an import rule). Everything that
is in the bundle is public.

### CSRF
Mutations through session cookies: `SameSite=Lax/Strict`, `Origin` verification, a CSRF token for forms —
details in be-auth-security.

## The dependency chain (npm)
- `npm ci` with a lockfile in CI; review of the lockfile diff in the PR; `npm audit` / Snyk / Socket in the pipeline.
- Install scripts are execution of someone else's code: `--ignore-scripts` (or a script allowlist in the package
  manager), especially in CI with secrets. Example: `event-stream` (2018) — malicious code added by a new maintainer.
- **Dependency confusion:** private scopes assigned to the private registry in `.npmrc`
  (`@company:registry=…`), reserving the scope names on the public npm.
- Typosquatting: check the name and the publisher before `npm i`; prefer packages with provenance; fewer dependencies =
  a smaller attack surface; updates with a review, not "always the latest".
- A cooldown for new versions: `min-release-age=3` in `.npmrc` (npm ≥ 11.10, in days), `minimumReleaseAge` in pnpm (minutes).
  The axios case (March 2026): malicious versions with a new dependency and `postinstall` were available for about 3 hours.
  The full set of rules and the post-incident procedure — ops-supply-chain-security.

## Checklist (TS-specific)
- [ ] no `as`/`!`/`any` on external data — schema validation, the type from the validator
- [ ] `process.env` validated at startup; no secrets in code shared with the client
- [ ] parameterised queries; column names/directions from a closed list
- [ ] no blind merge of input (prototype pollution); unknown keys rejected
- [ ] `jwt.verify` with `algorithms`; no `decode()` as auth
- [ ] secrets compared in constant time (`timingSafeEqual` on hashes)
- [ ] user URLs parsed with `new URL()` (SSRF, `javascript:`)
- [ ] no `eval`/`new Function`/`exec` with interpolation; deserialisation only with `JSON.parse`
- [ ] `npm ci`, dependency audit, control of install scripts, scopes in `.npmrc`
- [ ] lint: `eslint-plugin-security` / the `no-unsafe-*` rules from typescript-eslint

## Tools
| Tool | What for |
|---|---|
| Zod / Valibot / ArkType / class-validator | validation of input, configuration, API responses |
| DOMPurify | HTML sanitisation before insertion into the DOM |
| Helmet | HTTP headers in Express (the list of headers — be-auth-security) |
| `jose` / `jsonwebtoken` | JWT with an explicit algorithm |
| `node:crypto` `timingSafeEqual` | constant-time comparison |
| npm audit / Snyk / Socket | dependency scanning |
| eslint-plugin-security, typescript-eslint `no-unsafe-*` | static pattern detection |

Source of inspiration: the article "TypeScript Application Security from A to Z" (dev.to, devsdaddy) — the content described
in our own words, corrected and extended.
