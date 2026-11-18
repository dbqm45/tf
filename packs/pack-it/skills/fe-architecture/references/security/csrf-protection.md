# CSRF Protection

> **Contents:** Metadata · TLDR · Notes (state in 2026, corrections to the source) · Problem · Solution · Code examples · Advantages · Disadvantages / tradeoffs · Related patterns · When to use / when NOT to use

Source: frontendpatterns.dev/csrf-protection.

## Metadata

Category: Security. Level: Advanced. Frameworks: React, Vue, Svelte, Native Web. Author: Den Odell.
Last updated: 16 June 2026.

## TLDR

Enforce an unguessable, random per-session token on every state-changing request, validated on
the server before any work is done — add `SameSite` cookies as a second layer.

## Notes (state in 2026, corrections to the source)

- An additional, cheap layer in 2026: **Fetch Metadata** — the server rejects state-changing requests with
  `Sec-Fetch-Site: cross-site` (and checks `Origin`). Supported in all major browsers.
- A session cookie with the `__Host-` prefix (it enforces `Secure`, `Path=/`, no `Domain`) makes overwriting from a subdomain harder —
  important for double-submit.
- Do not assume that `SameSite=Lax` is the default — that is Chromium behaviour, not that of all browsers
  (samesite-cookie.md).
- Many frameworks have this built in: Angular's `HttpClient` automatically sends back the token from the `XSRF-TOKEN` cookie in
  the `X-XSRF-TOKEN` header (`withXsrfConfiguration`) — fw-angular. The server side — be-auth-security.
- The Svelte example: `<script context="module">` is Svelte 4; in Svelte 5 `<script module>`.

## Problem

CSRF attacks exploit the automatic attachment of cookies by browsers. When a logged-in
user visits a malicious site, it can send a state-changing request on their behalf
(a transfer, a password change). The server receives a correctly authenticated request, because the cookies are
attached, but the user never issued such a command. The attacker never sees the response and
does not read any data — they only need the victim to load the page while an active
session exists in the browser.

## Solution

Three complementary mechanisms:

1. **Synchronizer Token Pattern** — a token stored on the server side, passed to the client
   (a meta tag or an endpoint), sent back in the `X-CSRF-Token` header on every POST/PUT/PATCH/DELETE request.
2. **Double-Submit Cookie Pattern** — the server sets the token in a JS-readable cookie, the client
   copies the value into a header; an attacker can send the cookie, but cannot read its
   contents from another domain.
3. **The `SameSite` layer** — `SameSite=Lax`/`Strict` on the session cookie as additional protection,
   preventing it from being attached to cross-site requests (see `samesite-cookie.md`).

## Code examples

### Client-side token attachment — React

```javascript
import { useCallback } from 'react';

function getCsrfToken() {
  return document.querySelector('meta[name="csrf-token"]')?.content ?? '';
}

const UNSAFE_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);

export function useCsrfFetch() {
  return useCallback((url, options = {}) => {
    const method = (options.method ?? 'GET').toUpperCase();
    const headers = new Headers(options.headers);

    if (UNSAFE_METHODS.has(method)) {
      headers.set('X-CSRF-Token', getCsrfToken());
    }

    return fetch(url, { ...options, headers, credentials: 'same-origin' });
  }, []);
}

function TransferButton() {
  const csrfFetch = useCsrfFetch();

  const handleTransfer = () =>
    csrfFetch('/api/transfer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount: 100 }),
    });

  return <button onClick={handleTransfer}>Transfer $100</button>;
}
```

### Client-side token attachment — Vue

```vue
<script setup>
function getCsrfToken() {
  return document.querySelector('meta[name="csrf-token"]')?.content ?? '';
}

const UNSAFE_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);

function csrfFetch(url, options = {}) {
  const method = (options.method ?? 'GET').toUpperCase();
  const headers = new Headers(options.headers);

  if (UNSAFE_METHODS.has(method)) {
    headers.set('X-CSRF-Token', getCsrfToken());
  }

  return fetch(url, { ...options, headers, credentials: 'same-origin' });
}

function handleTransfer() {
  return csrfFetch('/api/transfer', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ amount: 100 }),
  });
}
</script>

<template>
  <button @click="handleTransfer">Transfer $100</button>
</template>
```

### Client-side token attachment — Svelte

```svelte
<script context="module">
  function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]')?.content ?? '';
  }

  const UNSAFE_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);

  export function csrfFetch(url, options = {}) {
    const method = (options.method ?? 'GET').toUpperCase();
    const headers = new Headers(options.headers);

    if (UNSAFE_METHODS.has(method)) {
      headers.set('X-CSRF-Token', getCsrfToken());
    }

    return fetch(url, { ...options, headers, credentials: 'same-origin' });
  }
</script>

<script>
  function handleTransfer() {
    return csrfFetch('/api/transfer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount: 100 }),
    });
  }
</script>

<button on:click={handleTransfer}>Transfer $100</button>
```

### Client-side token attachment — Web Components

```javascript
function getCsrfToken() {
  return document.querySelector('meta[name="csrf-token"]')?.content ?? '';
}

const UNSAFE_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);

export function csrfFetch(url, options = {}) {
  const method = (options.method ?? 'GET').toUpperCase();
  const headers = new Headers(options.headers);

  if (UNSAFE_METHODS.has(method)) {
    headers.set('X-CSRF-Token', getCsrfToken());
  }

  return fetch(url, { ...options, headers, credentials: 'same-origin' });
}

class TransferButton extends HTMLElement {
  connectedCallback() {
    this.innerHTML = `<button>Transfer $100</button>`;
    this.querySelector('button').addEventListener('click', () =>
      csrfFetch('/api/transfer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount: 100 }),
      })
    );
  }
}

customElements.define('transfer-button', TransferButton);
```

### Reading the token from a cookie (Double-Submit Pattern)

```javascript
function getCookie(name) {
  return document.cookie
    .split('; ')
    .find((row) => row.startsWith(`${name}=`))
    ?.split('=')[1] ?? '';
}

function csrfFetch(url, options = {}) {
  const headers = new Headers(options.headers);
  headers.set('X-CSRF-Token', getCookie('csrf_token'));
  return fetch(url, { ...options, headers, credentials: 'same-origin' });
}
```

### Server-side issuing and validation (Express)

```javascript
import crypto from 'node:crypto';
import express from 'express';
import cookieParser from 'cookie-parser';

const app = express();
app.use(cookieParser());
app.use(express.json());

const UNSAFE_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);

// Issue a token cookie if one isn't already present.
app.use((req, res, next) => {
  if (!req.cookies.csrf_token) {
    const token = crypto.randomBytes(32).toString('hex');
    res.cookie('csrf_token', token, {
      sameSite: 'lax',
      secure: true,
      // Readable by JS so the client can echo it back in the header.
      httpOnly: false,
    });
    req.cookies.csrf_token = token;
  }
  next();
});

// Reject unsafe requests whose header doesn't match the cookie.
app.use((req, res, next) => {
  if (!UNSAFE_METHODS.has(req.method)) return next();

  const cookieToken = req.cookies.csrf_token;
  const headerToken = req.get('X-CSRF-Token');

  const valid =
    cookieToken &&
    headerToken &&
    cookieToken.length === headerToken.length &&
    crypto.timingSafeEqual(Buffer.from(cookieToken), Buffer.from(headerToken));

  if (!valid) {
    return res.status(403).json({ error: 'Invalid CSRF token' });
  }
  next();
});

app.post('/api/transfer', (req, res) => {
  // Reaching here means the CSRF check passed.
  res.json({ status: 'ok', amount: req.body.amount });
});

app.listen(3000);
```

Note: `crypto.timingSafeEqual` instead of `===` prevents information leaks based on the comparison
time — see also be-auth-security (the section on timing
attacks). For the synchronizer token pattern store it in `req.session.csrfToken`.

## Advantages

- Requests from third-party sites are rejected, because the attacker does not have a valid token.
- Protection of specific dangerous operations (transfers, password change, account deletion).
- The same-origin policy does the heavy lifting — the token must be unguessable, not encrypted.
- Natural combination with `SameSite` cookies for a layered defence.
- The client side is a thin wrapper around `fetch`, written once and used everywhere.
- The double-submit variant does not require a server-side session store — easier to scale.
- Validation failures are visible and loud (HTTP 403) — configuration errors are easy to catch.

## Disadvantages / tradeoffs

- Every state-changing request carries the token baggage; forgotten headers cause silent errors.
- The server must generate, store and securely compare tokens — this adds cryptography concerns.
- Legitimate cross-origin clients break by design under this pattern — native applications/APIs
  require a different scheme (e.g. bearer tokens).
- SPAs must keep the token fresh after login/logout; requests can fail mid-session.
- Double-submit requires a JS-readable cookie — a potential trap when applied to
  sensitive cookies.
- `SameSite` cookies are not a full defence; older browsers ignore the attribute, `Lax` allows
  some navigations.
- Caching and CDNs get complicated — a page cached with one user's token should never
  reach another.
- A naive string comparison leaks timing information — validation requires a constant-time
  comparison (`crypto.timingSafeEqual`).

## Related patterns

- SameSite Cookie — Security (`samesite-cookie.md`)
- Secure Token Storage — Security (`secure-token-storage.md`)
- Content Security Policy (CSP) — Security (`content-security-policy.md`)
- See also be-auth-security — the CSRF section covers the same topic
  from the perspective of a Node.js/Express backend, this file — from the frontend perspective.
- External: [Cross-Site Request Forgery — OWASP](https://owasp.org/www-community/attacks/csrf),
  [CSRF Prevention Cheat Sheet — OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html),
  [SameSite Cookies — MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie/SameSite)

## When to use / when NOT to use

Use it **always** when the application has state-changing requests (POST/PUT/PATCH/DELETE) executed on
behalf of a logged-in user through a cookie-based session — this is not an optional add-on,
it is the fundamental protection for this authentication model. If the application uses **only** bearer
tokens in the `Authorization` header (not cookies) for API authentication, CSRF in its classic form does not
apply (the browser does not attach headers automatically the way it does cookies) — in that
case focus on `secure-token-storage.md` instead of adding an unnecessary layer of CSRF tokens.
