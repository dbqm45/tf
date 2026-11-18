# SameSite Cookie

> **Contents:** Metadata · TLDR · Notes (state in 2026, corrections to the source) · Problem · Solution · Code examples · Advantages · Disadvantages / tradeoffs · Related patterns · When to use / when NOT to use

Source: frontendpatterns.dev/samesite-cookie.

## Metadata

Category: Security. Level: Advanced. Framework: Native web. Author: Den Odell. Last updated:
18 June 2026.

## TLDR

The `SameSite` attribute on a cookie controls when the browser attaches it to cross-site requests — it is
one of the main browser-enforced defences against CSRF.

## Notes (state in 2026, corrections to the source)

- **Correction:** `SameSite=Lax` as the default value for cookies without the attribute is **Chromium** behaviour; Firefox and
  Safari have not adopted it (Safari has its own ITP) — always set the attribute explicitly.
- "Same-site" ≠ "same-origin": `a.example.com` and `b.example.com` are the same site — a taken-over subdomain bypasses SameSite.
  Hence the `__Host-` prefix for the session cookie.
- Third-party cookies (`SameSite=None`) are restricted by browsers in 2026 (Safari/Firefox block them,
  Chrome — user control); for embeds consider CHIPS (`Partitioned`) or the Storage Access API.

## Problem

Browsers automatically attach cookies to every request directed at the server's domain,
regardless of the request's origin. This enables CSRF attacks — a malicious site sends disguised
requests that exploit an authenticated user's session, without their knowledge.

## Solution

The `SameSite` attribute determines when the browser attaches the cookie to cross-site requests. Three values:

- **`Strict`** — never sends the cookie on cross-site requests (maximum protection, but it can
  worsen UX for incoming links — the user lands logged out).
- **`Lax`** — sends it on same-site requests and GET navigations from other sites, but blocks cross-site POSTs and
  AJAX requests (the recommended default in modern browsers).
- **`None`** — sends it on all cross-site requests (requires the `Secure` attribute; intended
  only for justified cases, e.g. embeds, SSO).

## Code examples

### Setting via the Set-Cookie header

```
# Strict: never sent cross-site — best for sensitive session cookies
Set-Cookie: sessionId=abc123; SameSite=Strict; Secure; HttpOnly; Path=/

# Lax: sent on GET navigations — the default for most sessions
Set-Cookie: sessionId=abc123; SameSite=Lax; Secure; HttpOnly; Path=/

# None: sent on all cross-site requests — REQUIRES Secure
Set-Cookie: widgetPrefs=xyz789; SameSite=None; Secure; Path=/
```

### Setting from an Express server

```javascript
// Strict session cookie for a first-party application
res.cookie('sessionId', 'abc123', {
  sameSite: 'strict', // never sent on cross-site requests
  secure: true,       // HTTPS only
  httpOnly: true,     // not accessible to JavaScript (limits XSS theft)
  maxAge: 1000 * 60 * 60 * 24, // 1 day
});

// Lax as the safer default when incoming links must keep the user logged in
res.cookie('sessionId', 'abc123', {
  sameSite: 'lax',
  secure: true,
  httpOnly: true,
});

// None required for justified cross-site cookies (embeds, SSO)
// The browser rejects SameSite=None without the Secure attribute
res.cookie('widgetPrefs', 'xyz789', {
  sameSite: 'none',
  secure: true, // mandatory with sameSite: 'none'
});
```

## Advantages

- Blocks the CSRF mechanism by preventing cookies from being attached to requests from other sites.
- Browser-enforced — the protection works automatically, without application code.
- In Chromium `Lax` is the default when the attribute is not set (other engines — no; set it explicitly).
- A one-line configuration on the `Set-Cookie` header.
- Combines with `Secure` and `HttpOnly` for multi-layered protection.
- `Strict` practically eliminates CSRF for cookies that do not need to be sent cross-site.

## Disadvantages / tradeoffs

- `Strict` worsens UX for links from e-mail/a search engine (the user has to log in again).
- `None` restores cross-site exposure and forces `Secure` (HTTPS only).
- `SameSite` alone is not complete CSRF protection — for state-changing operations also keep
  tokens (see `csrf-protection.md`).
- Older browsers handle `SameSite` inconsistently.
- Subdomains are treated as same-site — no isolation between your own subdomains.
- A missing `Secure` with `SameSite=None` makes the browser silently reject the cookie.
- Different cookies in the same application usually need different values (session: `Strict`/`Lax`,
  an embeddable widget: `None`).

## Related patterns

- CSRF Protection — Security (`csrf-protection.md`)
- Secure Token Storage — Security (`secure-token-storage.md`)
- Content Security Policy (CSP) — Security (`content-security-policy.md`)
- External: [SameSite Cookie Attribute — MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie/SameSite),
  [CSRF Protection — OWASP](https://owasp.org/www-community/SameSite),
  [Cookie Security — web.dev](https://web.dev/samesite-cookies-explained/)

## When to use / when NOT to use

Set `SameSite` on **every** cookie you create — there is no sensible case for
leaving it at the browser's default without a conscious decision. By default choose `Strict`
for the session cookies of the same application; `Lax` if you must support navigation from external
links (e-mail, search engine) without losing the session; `None` + `Secure` only when you have
**a specific, named cross-site reason** (an embeddable widget, SSO) — not "because it might come in handy".
Treat it as a complement to `csrf-protection.md`, not a replacement — `SameSite` alone does not protect against
all variants of CSRF (see Disadvantages).
