# Output Encoding

> **Contents:** Metadata · TLDR · Notes (state in 2026, corrections to the source) · Problem · Solution · Code examples · Advantages · Disadvantages / tradeoffs · Related patterns · When to use / when NOT to use

Source: frontendpatterns.dev/output-encoding.

## Metadata

Category: Security. Level: Advanced. Frameworks: React, Vue, Svelte, Native Web. Author: Den Odell.
Last updated: 17 June 2026.

## TLDR

Output encoding ensures that user data renders as inert text by encoding it for
the exact context in which it lands — rely on the framework's auto-escape for typical cases,
treat every escape hatch as a deliberate decision backed by sanitization.

## Notes (state in 2026, corrections to the source)

- Angular: `{{ }}` interpolation and property bindings escape/sanitize automatically; the escape hatch is
  `bypassSecurityTrustHtml` — fw-angular.
- **URL bindings** (`href={authorUrl}`) do not protect against `javascript:` in all frameworks (React only
  warns) — validate the scheme (`new URL(u).protocol` ∈ `http:`/`https:`) before you bind a URL from a user.
- The `<script>` context with `JSON.stringify` is safe only after additionally escaping `<` (e.g. `\u003c`), because
  `</script>` in the data closes the block — it is better to pass data through `data-*` or a `<script type="application/json">`
  read through `textContent`.

## Problem

The application stores user input (e.g. a profile name) without encoding. When this
content reaches the DOM in an inappropriate context, it can be interpreted as executable code
instead of text — e.g. `<img src=x onerror="fetch(...)">` is parsed as an HTML element, and
the `onerror` handler runs automatically. Stored XSS fires repeatedly, for every
user viewing the page.

Different contexts carry different threats:
- in HTML content: `<` opens a tag,
- in attributes: `"` breaks the quotation,
- in inline scripts: `</script>` ends the block,
- in URLs: `&` and `#` change the structure of the query.

## Solution

Encode user data for the specific target context **before** rendering:

1. **HTML body context:** `<` → `&lt;`, `>` → `&gt;`, `&` → `&amp;`.
2. **Attribute context:** additionally encode quotes.
3. **JavaScript context:** use `JSON.stringify` instead of concatenation.
4. **URL context:** apply `encodeURIComponent`.

Modern frameworks (React, Vue, Svelte) encode text interpolations and attribute
bindings by default. "Escape hatches" (`dangerouslySetInnerHTML`, `v-html`, `{@html}`, `innerHTML`) bypass
encoding completely — use them only with trusted HTML, cleaned beforehand by
DOMPurify.

## Code examples

### React

```javascript
function Comment({ body, authorUrl }) {
  // Safe: React escapes interpolated text and attribute values by default.
  // A body of "<script>alert(1)</script>" renders as visible text.
  return (
    <article>
      <a href={authorUrl}>Author</a>
      <p>{body}</p>
    </article>
  );
}

// Unsafe: dangerouslySetInnerHTML skips all encoding.
// Only use with sanitized HTML from a trusted source.
function RichComment({ trustedHtml }) {
  return <p dangerouslySetInnerHTML={{ __html: trustedHtml }} />;
}
```

### Vue

```javascript
<script setup>
defineProps({ body: String, authorUrl: String, trustedHtml: String });
</script>

<template>
  <!-- Safe: mustache interpolation and :attr bindings auto-escape. -->
  <article>
    <a :href="authorUrl">Author</a>
    <p>{{ body }}</p>
  </article>

  <!-- Unsafe: v-html injects raw markup with no encoding.
       Only bind sanitized, trusted HTML here. -->
  <p v-html="trustedHtml" />
</template>
```

### Svelte

```javascript
<script>
  export let body;
  export let authorUrl;
  export let trustedHtml;
</script>

<!-- Safe: {value} and attribute bindings are escaped automatically. -->
<article>
  <a href={authorUrl}>Author</a>
  <p>{body}</p>
</article>

<!-- Unsafe: {@html} renders raw markup with no encoding.
     Only use with sanitized, trusted HTML. -->
<p>{@html trustedHtml}</p>
```

### Web Components (Native)

```javascript
class CommentCard extends HTMLElement {
  set data({ body, authorUrl, trustedHtml }) {
    const article = document.createElement('article');
    const link = document.createElement('a');

    // Safe: textContent treats input as text, never markup.
    const p = document.createElement('p');
    p.textContent = body;

    // Safe: assign attributes via the DOM API, not string concatenation.
    link.href = authorUrl;
    link.textContent = 'Author';

    article.append(link, p);
    this.replaceChildren(article);

    // Unsafe: innerHTML parses input as HTML and executes handlers.
    // this.innerHTML = trustedHtml; // only with sanitized input
  }
}

customElements.define('comment-card', CommentCard);
```

### A context-aware helper

```javascript
// Escape for HTML body and attribute contexts.
// Replace & first so later replacements aren't double-encoded.
function encodeHTML(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;');
}

// Build a safe link: escape the text for HTML, encode the query for URLs.
function searchLink(query) {
  const href = `/search?q=${encodeURIComponent(query)}`;
  return `<a href="${encodeHTML(href)}">${encodeHTML(query)}</a>`;
}

// JavaScript context: never concatenate raw input into code.
// JSON.stringify produces a safely quoted, escaped string literal.
function inlineScript(message) {
  return `<script>showToast(${JSON.stringify(message)})<\/script>`;
}
```

## Advantages

- Neutralizes XSS at the rendering boundary — user data is always treated as text.
- Works as the last line of defence, even when upstream validation fails.
- Auto-escape in frameworks makes the safe path the default.
- Context-specific encoding covers all surfaces (HTML content, attributes, inline scripts, URLs).
- Prevents stored XSS — a single unencoded record does not execute repeatedly for many
  visitors.
- Integrates with defense-in-depth layers such as CSP and a dedicated sanitizer.
- Built-in browser APIs (`textContent`, `encodeURIComponent`) work without dependencies.

## Disadvantages / tradeoffs

- Correctness depends on the context — encoding for HTML in a URL or script context does not protect.
- Double encoding duplicates data: `<` becomes `&amp;lt;` and is displayed literally.
- Hand-written HTML encoders can miss edge cases (unquoted attributes, `javascript:`
  URLs) — a library is safer.
- Escape hatches (`dangerouslySetInnerHTML`, `v-html`, `{@html}`, `innerHTML`) invisibly bypass
  encoding.
- HTML with real tags requires a dedicated sanitizer (DOMPurify), not encoding alone.
- Encoding does not replace input sanitization or CSP — relying on it alone leaves
  the system fragile.
- Reviewing large codebases for under-encoded fields is tedious.

## Related patterns

- Input Sanitization — Security (`input-sanitization.md`)
- Trusted Types — Security (`trusted-types.md`)
- Content Security Policy (CSP) — Security (`content-security-policy.md`)
- External: [Output Encoding / XSS Prevention — OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html),
  [Character encodings in HTML — Wikipedia](https://en.wikipedia.org/wiki/Character_encodings_in_HTML),
  [XSS — OWASP](https://owasp.org/www-community/attacks/xss/)

## When to use / when NOT to use

If you use React/Vue/Svelte through standard interpolation (`{body}`, `{{ body }}`) — **the framework's
auto-escape already does this for you**, you do not need to add anything. Deliberately check only the
places with an escape hatch (`dangerouslySetInnerHTML`, `v-html`, `{@html}`, `innerHTML`) — that is
the only place where this pattern requires your active attention, not every line of the render.
