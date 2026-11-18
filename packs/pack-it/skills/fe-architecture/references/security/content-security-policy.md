# Content Security Policy (CSP)

> **Contents:** Metadata · TLDR · Notes (state in 2026, corrections to the source) · Problem · Solution · Code examples · Advantages · Disadvantages / tradeoffs · Related patterns · When to use / when NOT to use

Source: frontendpatterns.dev/content-security-policy.

## Metadata

Category: Security. Level: Advanced. Examples: Native web. Author: Den Odell. Last updated:
16 June 2026.

## TLDR

CSP is a browser-enforced allowlist, delivered as an HTTP header, that defines where
scripts, styles and other resources may come from.

## Notes (state in 2026, corrections to the source)

- A policy based on a **domain allowlist** is weak (bypasses through JSONP/gadgets on allowed CDNs). What is recommended
  is a **strict CSP**: `script-src 'nonce-{random}' 'strict-dynamic'; object-src 'none'; base-uri 'none'`
  (+ `'unsafe-inline' https:` as a fallback ignored by new browsers). Treat the allowlist as a transitional
  stage.
- `report-uri` is deprecated — use `report-to` + the `Reporting-Endpoints` header (the older `Report-To` is also
  deprecated); keep `report-uri` only as a fallback.
- Frameworks: Angular supports nonces (`ngCspNonce` / `CSP_NONCE`) and Trusted Types (fw-angular); Next.js — nonces through
  middleware; statically hosted SPAs — hashes (`'sha256-…'`) instead of nonces.
- The CSP is set by the server/CDN — it is a decision shared with the backend (be-auth-security).

## Problem

Web applications are exposed to XSS despite input sanitization and output encoding — the threat
comes both from internal code and from trusted sources (CDNs, analytics providers, ad
networks). Inline scripts make the situation worse: when legitimate inline code is normal on the page,
the browser has no way of telling `<script>onClick()</script>` apart from one injected by
an attacker — they are identical in form.

## Solution

CSP is an HTTP response header that defines a whitelist of sources for scripts, styles and resources.
The browser natively enforces these rules, blocking sources outside the list. Key elements:

- the "deny by default" principle with `default-src 'self'`,
- specialized directives: `script-src`, `style-src`, `img-src`, `connect-src`,
- a ban on `'unsafe-inline'` and `'unsafe-eval'`,
- **nonces** (random per-request values) to authorize specific inline scripts,
- **report-only mode** for testing the policy before enforcing it.

## Code examples

### Starter Policy (a native HTTP header)

```
Content-Security-Policy: default-src 'self'; script-src 'self' https://cdn.example.com; style-src 'self'; img-src 'self' data: https:; connect-src 'self' https://api.example.com; font-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'
```

`object-src 'none'` disables plugins; `base-uri 'self'` prevents hijacking of relative URLs;
`frame-ancestors 'none'` protects against clickjacking.

### Express + Helmet (Node.js middleware)

```javascript
import express from "express";
import helmet from "helmet";

const app = express();

app.use(
  helmet.contentSecurityPolicy({
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'", "https://cdn.example.com"],
      styleSrc: ["'self'"],
      imgSrc: ["'self'", "data:", "https:"],
      connectSrc: ["'self'", "https://api.example.com"],
      objectSrc: ["'none'"],
      baseUri: ["'self'"],
      frameAncestors: ["'none'"],
    },
  })
);
```

### Nonce-based Inline Scripts (Node.js)

```javascript
import crypto from "node:crypto";

app.use((req, res, next) => {
  res.locals.nonce = crypto.randomBytes(16).toString("base64");
  res.setHeader(
    "Content-Security-Policy",
    `default-src 'self'; script-src 'self' 'nonce-${res.locals.nonce}'`
  );
  next();
});
```

```html
<!-- Template markup (e.g. EJS, Handlebars) -->
<script nonce="r4nd0mPerRequestValue==">
  window.__APP_CONFIG__ = { theme: "dark" };
</script>
```

The nonce must be **random and unique per request** — reusing a static value invalidates the protection.

### Violation Reporting

```
Reporting-Endpoints: csp-endpoint="https://example.com/csp-reports"
Content-Security-Policy: default-src 'self'; script-src 'self'; report-to csp-endpoint; report-uri /csp-reports
```

Report-only deployment (testing without affecting functionality):

```
Content-Security-Policy-Report-Only: default-src 'self'; script-src 'self'; report-to csp-endpoint
```

## Advantages

- Injected scripts are blocked at the browser level, even when input sanitization and
  output encoding miss something.
- Protection against compromised CDNs/third-party providers.
- Nonces/hashes let you control inline scripts without `'unsafe-inline'`.
- Violation reports give visibility into attacks and configuration errors.
- Enforcement at the header level — independent of the application code.
- Report-only mode for validating the policy without affecting functionality.

## Disadvantages / tradeoffs

- Authoring complexity — configuring a strict policy requires iterative tuning.
- Existing inline scripts and event handlers must be refactored.
- Third-party libraries (analytics, tag managers, ad networks) often require liberal
  permissions.
- Nonce-based policies require server-side → template synchronization (extra coupling).
- CSP mitigates, it does not prevent attacks — it does not replace output encoding and input validation.
- Browser support and directive behaviour differ — fallbacks are required.
- Broad policies with `https:` wildcards give a false sense of security.
- Reporting endpoints can generate noise from browser extensions.

## Related patterns

- Subresource Integrity — Security (`../security/subresource-integrity.md`)
- Trusted Types — Security (`../security/trusted-types.md`)
- CSRF Protection — Security (`../security/csrf-protection.md`)
- Output Encoding — Security (`../security/output-encoding.md`)
- External: [CSP — MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP),
  [CSP Quick Reference](https://content-security-policy.com/),
  [CSP Best Practices — web.dev](https://web.dev/strict-csp/)

## When to use / when NOT to use

Use it when you want **a last line of defence against XSS at the browser level**, independent of whether
sanitization/encoding in the application code worked correctly — especially if the application
loads scripts from CDNs/analytics/ads that are outside your control. **Start with report-only**
to measure the real cost (how much existing code a strict policy will break) before you turn on
enforcement — introducing a strict CSP "straight into production" without this step is a common cause
of a broken application. If the application is small, static, without user content and without third-party
resources — the cost of maintaining a restrictive policy may exceed the real risk (see YAGNI in
`../principles.md`); then solid Output Encoding + Input Sanitization may be enough
as the first layer.
