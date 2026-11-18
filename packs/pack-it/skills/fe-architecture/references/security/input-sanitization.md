# Input Sanitization

> **Contents:** Metadata · TLDR · Notes (state in 2026, corrections to the source) · Problem · Solution · Code examples · Advantages · Disadvantages / tradeoffs · Related patterns · When to use / when NOT to use

Source: frontendpatterns.dev/input-sanitization.

## Metadata

Category: Security. Level: Advanced. Examples: React, Vue, Svelte, Native web. Author: Den Odell.
Last updated: 16 June 2026.

## TLDR

Clean and validate untrusted user data at the boundary, before you render or process it —
using an allow-list and a proven sanitizer, so that malicious markup becomes harmless text
instead of executable code.

## Notes (state in 2026, corrections to the source)

- The **Sanitizer API** (`element.setHTML(input)`, `Sanitizer`) is arriving in browsers in 2025–2026 — when it is available to
  your users, it replaces the library; until then DOMPurify (keep the version up to date).
- Angular sanitizes `[innerHTML]` automatically (`DomSanitizer`); `bypassSecurityTrust*` is an escape hatch that requires
  review — fw-angular.
- Client-side format validation is UX, not security — server validation decides (be-auth-security).
  SQL injection is a backend problem (parameterized queries), mentioned here only for completeness.
- The Svelte examples are in Svelte 4 syntax (`export let`, `$:`); in Svelte 5 `$props()`/`$derived`.

## Problem

User input, e.g. a `<script>` in a profile name, can execute malicious code when it is
rendered through `innerHTML`. Attack vectors go beyond `<script>` — they include `onerror` handlers
on images, `javascript:` URLs in links, SVG elements and SQL injection patterns. The basic
problem: untrusted data passed to interpreters (HTML parsers, SQL engines) executes without
validation.

## Solution

Use allow-lists, not deny-lists. For plain text — `textContent` instead of parsing HTML.
For rich text that is really needed — proven, maintained libraries such as DOMPurify, not
a hand-written regex. Sanitize at the input boundaries, validate against schemas,
parameterize database queries and add a Content Security Policy as defense-in-depth.

## Code examples

### Sanitizing rich text before rendering — React

```javascript
import DOMPurify from 'dompurify';

function Comment({ html }) {
  // Sanitize untrusted HTML, then opt in to raw rendering.
  const clean = DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'ul', 'ol', 'li'],
    ALLOWED_ATTR: ['href']
  });

  return <div dangerouslySetInnerHTML={{ __html: clean }} />;
}
```

### Sanitizing rich text before rendering — Vue

```javascript
<script setup>
import { computed } from 'vue';
import DOMPurify from 'dompurify';

const props = defineProps({ html: String });

// Sanitize before binding with v-html, never bind raw input.
const clean = computed(() =>
  DOMPurify.sanitize(props.html, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'ul', 'ol', 'li'],
    ALLOWED_ATTR: ['href']
  })
);
</script>

<template>
  <div v-html="clean" />
</template>
```

### Sanitizing rich text before rendering — Svelte

```javascript
<script>
  import DOMPurify from 'dompurify';

  export let html = '';

  // {@html} renders raw markup, so sanitize first.
  $: clean = DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'ul', 'ol', 'li'],
    ALLOWED_ATTR: ['href']
  });
</script>

<div>{@html clean}</div>
```

### Sanitizing rich text before rendering — Web Components

```javascript
import DOMPurify from 'dompurify';

class UserComment extends HTMLElement {
  set html(value) {
    // Sanitize untrusted markup before assigning to innerHTML.
    this.innerHTML = DOMPurify.sanitize(value, {
      ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'ul', 'ol', 'li'],
      ALLOWED_ATTR: ['href']
    });
  }
}

customElements.define('user-comment', UserComment);
```

### Escaping HTML without a library

```javascript
function escapeHTML(input) {
  const el = document.createElement('div');
  // textContent treats input as literal text, escaping < > & " automatically.
  el.textContent = input;
  return el.innerHTML;
}

escapeHTML('<img src=x onerror=alert(1)>');
// => "&lt;img src=x onerror=alert(1)&gt;"  (inert text, never executes)
```

### Validating formats with an allow-list

```javascript
const RULES = {
  username: /^[a-zA-Z0-9_-]{3,20}$/,
  email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/
};

function validate(field, value) {
  const pattern = RULES[field];
  if (!pattern || !pattern.test(value)) {
    throw new Error(`Invalid ${field}`);
  }
  return value;
}

validate('username', 'jane_doe-42');         // ok
validate('username', '<script>alert(1)</script>'); // throws: Invalid username
```

## Advantages

- Neutralizes stored and reflected XSS by turning malicious markup into inert text before
  HTML parsing.
- Allow-lists stay resistant to new attack patterns, because you define the allowed content.
- Maintained sanitizers cover unusual vectors (SVG, mutation XSS, `javascript:` URLs)
  that home-made filters miss.
- Format validation stops bad data early, preventing security problems and
  display errors.
- Parameterized queries eliminate SQL injection while keeping the code readable.
- Combines naturally with output encoding and a strict CSP for layered protection.
- A single sanitization point lets you treat the data as trusted further down the flow.

## Disadvantages / tradeoffs

- Overly aggressive sanitization removes legitimate content, frustrating users.
- Allow-lists require maintenance; a forgotten tag causes support tickets.
- Sanitizing rich text is hard; home-made regexes often contain bypasses.
- Even good sanitizers get security patches; pinning an old version creates a risk.
- Sanitization is not the same as encoding — cleaned data still needs context-specific encoding
  on output (see `output-encoding.md`).
- Client-side-only sanitization is insufficient; server-side validation remains
  necessary.
- A visible modification of the input after a form is submitted confuses users unaware of
  sanitization.
- Reusing sanitized data in another context (queries, shell commands) requires
  a fresh assessment — sanitization is contextual, not universal.
- Processing large documents adds a measurable parsing overhead.

## Related patterns

- Output Encoding — Security (`output-encoding.md`)
- Trusted Types — Security (`trusted-types.md`)
- External: [Input Validation Cheat Sheet — OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html),
  [XSS Prevention — OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html),
  [DOMPurify — GitHub](https://github.com/cure53/DOMPurify)

## When to use / when NOT to use

Sanitize **every** user input that will reach an HTML render, a database query or
another interpreter — this is not optional for any user-generated
content. For plain text (a name, a comment without formatting) `textContent`/
format validation is enough — **do not reach for DOMPurify** if you do not actually need to render HTML;
it is an unnecessary cost (bundle + parsing overhead) for a case that simpler
escaping solves (the YAGNI principle, `../principles.md`). DOMPurify/full rich text sanitization is
justified only when you really need to accept limited HTML from the user (a WYSIWYG editor,
comments with formatting).
