# Subresource Integrity

> **Contents:** Metadata · TLDR · Notes (state in 2026, corrections to the source) · Problem · Solution · Code examples · Advantages · Disadvantages / tradeoffs · Related patterns · When to use / when NOT to use

Source: frontendpatterns.dev/subresource-integrity.

## Metadata

Category: Security. Level: Advanced. Framework: Native web. Author: Den Odell. Last updated:
21 June 2026.

## TLDR

The `integrity` attribute on `<script>`/`<link>` cryptographically verifies that a resource from a CDN has not been
tampered with — the browser blocks execution if the hash does not match.

## Notes (state in 2026, corrections to the source)

- **Corrections:** the CSP directive `require-sri-for` never made it into browsers (removed from the specification) — do not
  rely on it. A fallback through `document.write` is deprecated (blocked/warned about, it breaks CSP) —
  inject the `<script>` through the DOM (`document.createElement('script')`).
- SRI makes sense mainly for resources from **other people's** origins; your own bundled assets with a hash in the file name
  are already protected by the deployment process. Import maps support an `integrity` field for ES modules.
- The example URLs (`react@18.2.0` UMD) are an illustration — modern applications bundle dependencies instead of loading them from a CDN.

## Problem

Loading scripts from a CDN means permanent trust in the provider. Without a verification mechanism
any file executed in the browser can contain malicious code as a result of a CDN compromise, a
man-in-the-middle attack, a configuration mistake or insider actions. A tampered script can
read passwords straight from form fields, steal session tokens, inject a cryptocurrency miner or
silently redirect users.

## Solution

Subresource Integrity (SRI) uses a cryptographic checksum in the `integrity` attribute
of `<script>` and `<link>` tags. The browser compares the hash of the downloaded resource with the expected value —
a mismatch blocks execution. It requires `crossorigin="anonymous"` for correct CORS handling.

## Code examples

### Adding integrity to a script from a CDN

```html
<!-- An external script, pinned to an exact version -->
<script
  src="https://cdn.example.com/react@18.2.0/react.min.js"
  integrity="sha384-oqVuAfXRKap7fdgcCY5uykM6+R9GqQ8K/uxy9rx7HNQlGYl1kPzQho1wx4JwY8wC"
  crossorigin="anonymous"
></script>

<!-- An external stylesheet -->
<link
  rel="stylesheet"
  href="https://cdn.example.com/bootstrap@5.3.0/bootstrap.min.css"
  integrity="sha384-9ndCyUaIbzAi2FUVXJi0CjmCapSmO7SnpJef0486qhLnuZ2cdeRhO02iuK6FUUVM"
  crossorigin="anonymous"
/>
```

### Generating the hash

```bash
# Hash of a local file
cat react.min.js | openssl dgst -sha384 -binary | openssl base64 -A
# -> oqVuAfXRKap7fdgcCY5uykM6+R9GqQ8K/uxy9rx7HNQlGYl1kPzQho1wx4JwY8wC

# Hash directly from the CDN
curl -s https://cdn.example.com/react@18.2.0/react.min.js \
  | openssl dgst -sha384 -binary | openssl base64 -A
```

### Automating SRI in the build — Vite/Rollup

```javascript
// vite.config.js
import { defineConfig } from 'vite';
import sri from 'vite-plugin-sri';

export default defineConfig({
  plugins: [
    sri({ algorithm: 'sha384' }),
  ],
});
```

For webpack — analogously `webpack-subresource-integrity`.

### A fallback for blocked resources

```html
<script
  src="https://cdn.example.com/jquery@3.7.1/jquery.min.js"
  integrity="sha384-1H217gwSVyLSIfaLxHbE7dRb3v4mYCKbpQvzx0cegeju1MVsGrX5xXxAvs/HgeFs"
  crossorigin="anonymous"
></script>
<script>
  // If SRI blocks it or the CDN is unavailable, window.jQuery will be undefined
  if (!window.jQuery) {
    const s = document.createElement('script');
    s.src = '/vendor/jquery-3.7.1.min.js'; // self-hosted fallback
    document.head.append(s);
  }
</script>
```

For stylesheets — listening for the `error` event:

```javascript
const link = document.querySelector('link[data-cdn]');
link.addEventListener('error', () => {
  link.href = '/vendor/bootstrap-5.3.0.min.css';
});
```

## Advantages

- Cryptographic verification of every resource before execution.
- Automatic blocking of compromised CDNs and tampering in transit.
- Forces pinning of exact versions, eliminating unexpected updates under the same URL.
- Declarative protection — one attribute, no extra network requests.
- Automation for your own resources already in the build step.
- Composes with self-hosted fallbacks.

## Disadvantages / tradeoffs

- Every change to a file requires regenerating the hash — it makes routine CDN updates harder.
- Impossible to use with mutable URLs (e.g. "latest") — the file changes, the hash never
  matches.
- The need to track and synchronize every hash with dependency version bumps.
- Requires correct CORS handling by the CDN — without the right headers verification is impossible.
- All or nothing — a blocked critical resource breaks the page without a fallback if
  you do not prepare one.
- Not suitable for rapidly rotating resources (analytics, ads).
- Updating a library becomes a deliberate, manual step, not a passive download.
- Errors fail silently from the user's perspective — monitoring is needed to notice them.
- It protects the resource's integrity, not its availability or privacy.

## Related patterns

- Content Security Policy (CSP) — Security (`content-security-policy.md`)
- Trusted Types — Security (`trusted-types.md`)
- External: [Subresource Integrity — MDN](https://developer.mozilla.org/en-US/docs/Web/Security/Subresource_Integrity),
  [SRI Hash Generator](https://www.srihash.org/), [CDN Security — web.dev](https://web.dev/codelab-sri/)

## When to use / when NOT to use

Add `integrity` **always** when you load a script/style from an external CDN under a specific, pinned
version (`react@18.2.0`, not `react@latest`) — the cost is one-off (generating the hash), and the
protection is real. Do **not** apply SRI to resources that by nature must change without your
control (analytics tags, ad networks, "latest" CDN links) — there the hash will drift
anyway, and the only sensible defence is CSP + isolation (see `content-security-policy.md`), not
SRI.
