# Semantic HTML

> **Contents:** Metadata · TLDR · Notes (state as of 2026, corrections to the source) · Problem · Solution · Code examples · Advantages · Disadvantages / trade-offs · Related patterns · When to use / when NOT to use

Source: frontendpatterns.dev/semantic-html.

## Metadata

- **Category:** Fundamentals
- **Level:** Beginner
- **Examples:** Native web
- **Last updated:** October 2, 2025
- **Author:** Den Odell

## TLDR

"Use HTML elements for their intended purpose to get accessibility, keyboard support, and SEO benefits without extra code."

## Notes (state as of 2026, corrections to the source)

- Newer native elements replacing custom widgets: `<dialog>` (modal), the `popover` attribute (a menu, a tooltip without positioning
  JS — with CSS anchor positioning), `<details name="…">` (an exclusive accordion), `<search>` (the search
  landmark), `<output>`/`<meter>`/`<progress>` for results and indicators.
- In components a heading does not know its level — pass the level as an input (`level`) or design the sections so
  that the page sets the hierarchy.
- A `<button>` in a form has `type="submit"` by default — always set `type` explicitly.

## Problem

A page built only from `<div>` elements prevents screen reader users from navigating through landmarks. `<div>` elements styled as buttons do not work with the keyboard and are not announced by screen readers as interactive — they require recreating from scratch the functionality a native element has for free.

## Solution

Use HTML elements for their intended purpose: `<button>` for actions, `<a>` for links, `<nav>` for navigation, `<main>` for the main content, `<header>`/`<footer>` for header/footer sections, `<article>` for self-contained content, `<aside>` for supplementary content, `<h1>`–`<h6>` for the heading hierarchy, `<table>` for tabular data, `<form>` with an associated `<label>` for input fields.

## Code examples

### Semantic document structure

```html
<body>
  <header>
    <h1>Site Title</h1>
    <nav aria-label="Primary">
      <ul>
        <li><a href="/">Home</a></li>
        <li><a href="/about">About</a></li>
      </ul>
    </nav>
  </header>

  <main>
    <article>
      <header>
        <h2>Article Title</h2>
        <time datetime="2026-01-01">January 1, 2026</time>
      </header>
      <p>Introduction paragraph...</p>
      <h3>First Section</h3>
      <p>Section content...</p>
      <figure>
        <img src="chart.png" alt="Sales data visualization">
        <figcaption>Q4 2025 Sales Performance</figcaption>
      </figure>
      <aside>
        <h4>Related Information</h4>
        <p>Additional context...</p>
      </aside>
    </article>
  </main>

  <aside aria-label="Sidebar">
    <h2>Popular Posts</h2>
    <ul>
      <li><a href="/post-1">First Post</a></li>
    </ul>
  </aside>

  <footer>
    <p>&copy; 2026 Company Name</p>
    <nav aria-label="Footer">
      <a href="/privacy">Privacy</a>
      <a href="/terms">Terms</a>
    </nav>
  </footer>
</body>
```

### Semantic interactive elements

```html
<!-- Div button requires extensive ARIA and JavaScript -->
<div role="button" tabindex="0" onclick="handleClick()"
     onkeydown="handleKeyPress(event)">Submit</div>

<!-- Semantic button works automatically -->
<button type="submit">Submit</button>

<!-- Div link breaks keyboard nav and right-click -->
<div class="link" onclick="navigate('/page')">Go to page</div>

<!-- Semantic link has full browser features -->
<a href="/page">Go to page</a>
```

### Semantic form elements

```html
<form>
  <label for="username">Username</label>
  <input id="username" type="text" required>

  <fieldset>
    <legend>Shipping Address</legend>
    <label for="street">Street</label>
    <input id="street" type="text">
    <label for="city">City</label>
    <input id="city" type="text">
  </fieldset>

  <button type="submit">Submit</button>
  <button type="button">Cancel</button>
</form>
```

### Semantic data presentation

```html
<table>
  <caption>Monthly Sales Report</caption>
  <thead>
    <tr>
      <th scope="col">Month</th>
      <th scope="col">Revenue</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th scope="row">January</th>
      <td>$50,000</td>
    </tr>
  </tbody>
</table>

<details>
  <summary>Advanced Settings</summary>
  <p>Additional configuration options...</p>
</details>
```

## Advantages

- Screen readers automatically announce the meaning of elements without an extra `role`/`aria-*`.
- Better SEO thanks to a recognizable, semantic document structure.
- Default keyboard support (Tab, Enter, Space) without writing your own code.
- Compatibility with reader mode and the browser's text-to-speech features.
- Less code: one `<button>` instead of twenty lines of ARIA + keyboard handling for a `<div role="button">`.
- Self-documenting code — the document structure is visible from the element names alone.

## Disadvantages / trade-offs

- It requires learning many HTML elements and their correct use (not every developer finds them intuitive).
- The browser's default styles for semantic elements need resetting/overriding in CSS.
- Some elements have unintuitive usage rules (e.g. when `<article>` and when `<section>`).
- The heading hierarchy (`<h1>`–`<h6>`) must be sequential, which is sometimes inconvenient in a component architecture (a component does not always know at which hierarchy level it will end up).
- CSS frameworks/design systems sometimes assume a `<div>`-based structure, which makes it hard to "inject" semantics without rewriting the styles.
- Retrofitting (adding semantics to existing, already written code) is time-consuming.
- Semantic correctness is not visible in the browser — a mistake does not "look" wrong, even though it breaks accessibility.

## Related patterns

- [ARIA Roles and Attributes](aria-roles-and-attributes.md) — Accessibility.
- [Accessible Forms](accessible-forms.md) — Accessibility.
- Semantic HTML — MDN.
- HTML5 Semantic Elements — W3Schools.
- Accessibility and Semantics — web.dev.

## When to use / when NOT to use

Use semantic HTML **by default and always** — it is one of the foundations of frontend architecture ("Accessibility as a Foundation", fe-architecture `.claude/skills/fe-architecture/references/principles.md`), not an optional technique to consider on larger projects. The cost is zero or negative (less code than recreating the same thing with ARIA+JS on a `<div>`), and the gain (accessibility, SEO, keyboard) is immediate.

The only justified exception: building **your own complex widget** (e.g. a custom dropdown with unique behaviour) for which no native element exists — then a `<div>` + the full set of `role`/`aria-*`/keyboard handling is the right tool (see [ARIA Roles and Attributes](aria-roles-and-attributes.md)), but it is the last option, not the first.
