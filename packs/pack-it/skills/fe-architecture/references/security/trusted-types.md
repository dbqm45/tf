# Trusted Types

> **Contents:** Metadata · TLDR · Notes (state in 2026, corrections to the source) · Problem · Solution · Code examples · Advantages · Disadvantages / tradeoffs · Related patterns · When to use / when NOT to use

Source: frontendpatterns.dev/trusted-types.

## Metadata

Category: Security. Level: Advanced. Technology: Native web (Browser APIs). Author: Den Odell.
Last updated: 22 June 2026.

## TLDR

The browser's Trusted Types API enforces that dangerous DOM sinks (e.g. `innerHTML`) accept
only typed objects passed through an audited policy (`TrustedHTML` etc.), not raw
strings — it eliminates DOM-based XSS at the source.

## Notes (state in 2026, corrections to the source)

- Support: Chromium for a long time; in 2025–2026 the other engines are joining (Safari 26, Firefox) — check Baseline for
  your audience. Without support, enforcement is simply ignored — Trusted Types is an additional layer.
- The `Report-To` header is deprecated — use `Reporting-Endpoints` + `report-to` in the CSP.
- Angular supports Trusted Types natively (the `angular`, `angular#bundler` policies) — fw-angular. In React `dangerouslySetInnerHTML`
  accepts `TrustedHTML` from a policy.
- The `default` policy is a safety net for third-party libraries — log its uses so that you can gradually remove them.

## Problem

DOM-based XSS vulnerabilities arise when an untrusted string reaches a DOM "sink" that
interprets it as code. The classic example: `element.innerHTML = userInput`. Other dangerous
sinks: `outerHTML`, `document.write`, `insertAdjacentHTML`, `script.src`, `eval`, `iframe.srcdoc`.

Two problematic aspects:
1. Such bugs look innocent (ordinary assignments) and easily slip past code review.
2. Dangerous sinks are scattered across the whole codebase; sanitization is often forgotten and
   inconsistent between places.

## Solution

Trusted Types changes the browser's default behaviour — dangerous sinks stop accepting
plain strings and require special, typed objects: `TrustedHTML`, `TrustedScript`,
`TrustedScriptURL`. These objects can be created **only** through an audited policy, defined once
with `trustedTypes.createPolicy()`.

Enabling: the `Content-Security-Policy: require-trusted-types-for 'script'` header.

## Code examples

### Enabling enforcement

```
Content-Security-Policy: require-trusted-types-for 'script'
Content-Security-Policy: trusted-types sanitize default;
```

After enabling: `element.innerHTML = '<b>hi</b>'` throws a `TypeError`.

### Creating a policy (native web)

```javascript
import DOMPurify from 'dompurify';

const sanitizer = trustedTypes.createPolicy('sanitize', {
  createHTML: (input) => DOMPurify.sanitize(input),
});

// Returns TrustedHTML, not a string
const safe = sanitizer.createHTML(userInput);
element.innerHTML = safe; // Accepted: sanitized by the policy

// A plain string is rejected
element.innerHTML = userInput; // TypeError: requires TrustedHTML
```

### The default policy

```javascript
trustedTypes.createPolicy('default', {
  createHTML: (input) => DOMPurify.sanitize(input),
  createScriptURL: (input) => {
    const url = new URL(input, location.origin);
    if (url.origin !== location.origin) {
      throw new Error(`Untrusted script URL: ${input}`);
    }
    return url.href;
  },
});
```

### Report-only mode

```
Reporting-Endpoints: csp-endpoint="https://example.com/csp-reports"
Content-Security-Policy-Report-Only: require-trusted-types-for 'script'; report-to csp-endpoint
```

## Advantages

- Eliminates XSS vulnerabilities at the source by not allowing an unsanitized string to be passed to
  a protected sink.
- Centralizes sanitization in one audited policy, instead of scattered, inconsistent
  calls across the code.
- Moves catching the bug from production to a `TypeError` already during development.
- Layers with CSP and output encoding for defense-in-depth.
- Report-only mode lets you measure the real exposure on production data before enforcing.

## Disadvantages / tradeoffs

- Browser support was limited to Chromium for a long time; other engines are joining only in 2025–2026.
- Requires refactoring existing code — every dangerous assignment must go through
  a policy.
- Third-party libraries that write to `innerHTML` internally can break under enforcement.
- An overly permissive `default` policy is a threat in itself — it can open the hole it
  was meant to close.
- It protects only the protected sinks; it does not catch XSS through a `javascript:` URL in attributes or through
  style injection.
- Enforcement depends on correctly sent CSP headers — a configuration error silently turns off
  the protection.
- Creating policies adds operational complexity.
- Trusted Types guarantees only that the content passed through a policy — a faulty implementation of
  `createHTML` can still approve dangerous markup.

## Related patterns

- Content Security Policy (CSP) — Security (`content-security-policy.md`)
- Output Encoding — Security (`output-encoding.md`)
- Input Sanitization — Security (`input-sanitization.md`)
- External: [Trusted Types API — MDN](https://developer.mozilla.org/en-US/docs/Web/API/Trusted_Types_API),
  [The Trusted Types specification — GitHub](https://w3c.github.io/trusted-types/dist/spec/),
  [XSS Prevention with Trusted Types — web.dev](https://web.dev/trusted-types/)

## When to use / when NOT to use

Introduce Trusted Types in applications where DOM-based XSS is a real risk — a large codebase with
many places writing to `innerHTML`/similar sinks, especially from many teams at once, where
"in each place separately" sanitization has already drifted apart. Do **not** treat it as the first step
— it is a pattern that complements Input Sanitization and Output Encoding, not their replacement; if
the project does not yet have basic sanitization/encoding in order, Trusted Types will only add
`TypeError`s without real benefit until that foundation is ready. Check browser
support for the target audience before enforcing in production — for some users
(older Safari/Firefox) the protection simply will not work, so do not count on it as the only layer.
