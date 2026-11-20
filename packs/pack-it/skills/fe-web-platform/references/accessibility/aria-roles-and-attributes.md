# ARIA Roles and Attributes

> **Contents:** Metadata · TLDR · Notes (state as of 2026, corrections to the source) · Problem · Solution · Code examples · When ARIA is unnecessary · Advantages · Disadvantages / trade-offs · Related patterns · When to use / when NOT to use

Source: frontendpatterns.dev/aria-roles-and-attributes (Den Odell, updated 17 October 2025).

## Metadata

- **Category:** Accessibility
- **Level:** Beginner
- **Format:** Native web

## TLDR

"Add ARIA attributes only when native HTML falls short. Use roles to identify custom widgets,
states to communicate changes, and properties to describe relationships."

## Notes (state as of 2026, corrections to the source)

- **Combobox per ARIA 1.2**: `role="combobox"` is on the `<input>` itself (with `aria-expanded`, `aria-controls`,
  `aria-activedescendant`), not on a wrapping `<div>` — the wrapper pattern comes from the outdated ARIA 1.1.
  The example was corrected.
- `role="menu"` is for application menus (as in desktop programs) with arrow navigation; for a site's
  navigation menu use a button with `aria-expanded` + an ordinary list of links (the "disclosure" pattern).
- Hiding: the `hidden` attribute (or `display: none`) hides both from the eye and from the screen reader — do not combine
  `aria-hidden` + `style.display` by hand. New native mechanisms instead of ARIA: `<dialog>`, `popover` + `popovertarget`,
  `<details name>` (an exclusive accordion), `<search>`, customizable `<select>` (Chromium, `appearance: base-select`).
- Landmarks: the native `<header>`, `<nav>`, `<main>`, `<aside>`, `<footer>` instead of `role="banner"` etc. — roles only
  with legacy markup.
- Specification: WAI-ARIA 1.2 (a W3C recommendation), 1.3 in preparation.

## Problem

Custom components (dropdown, tab panels, combobox) built from `<div>` and CSS are
invisible to screen readers — there is no information about the widget type, its selection or state
changes. The basic problem: HTML does not have native elements for all the interactive UI patterns
that actually get built.

## Solution

ARIA attributes communicate what HTML does not express natively:
- **State** — `aria-expanded`, `aria-selected`, `aria-checked`.
- **Widget type** — `role="menu"`, `role="tab"` etc.
- **Relationships/descriptions** — `aria-label`, `aria-describedby`, `aria-controls`.

**The key rule:** ARIA is the last resort, not the first choice — native elements (`<button>`,
`<dialog>`, `<details>`) have built-in semantics and **do not need** additional roles.

## Code examples

### Dropdown menu

```html
<button
  aria-expanded="false"
  aria-controls="dropdown-menu"
  aria-haspopup="menu"
  aria-label="User settings"
>
  Settings
</button>

<ul id="dropdown-menu" role="menu" aria-hidden="true">
  <li role="menuitem">Profile</li>
  <li role="menuitem">Settings</li>
  <li role="separator"></li>
  <li role="menuitem">Logout</li>
</ul>
```

### A tabs interface with ARIA

```html
<div role="tablist" aria-label="Account settings">
  <button role="tab" aria-selected="true" aria-controls="profile-panel" id="profile-tab" tabindex="0">
    Profile
  </button>
  <button role="tab" aria-selected="false" aria-controls="security-panel" id="security-tab" tabindex="-1">
    Security
  </button>
</div>

<div role="tabpanel" id="profile-panel" aria-labelledby="profile-tab" tabindex="0">
  <!-- Profile content -->
</div>

<div role="tabpanel" id="security-panel" aria-labelledby="security-tab" tabindex="0" hidden>
  <!-- Security content -->
</div>
```

### A live region for dynamic updates

```html
<div role="status" aria-live="polite" aria-atomic="true" id="status-message">
  <!-- Updates announced without stealing focus -->
</div>

<script>
function updateStatus(message) {
  document.getElementById('status-message').textContent = message;
}
</script>
```

### Custom combobox

```html
<!-- ARIA 1.2: role="combobox" lives on the input itself -->
<label for="country" id="combo-label">Choose a country</label>
<input id="country" type="text" role="combobox" aria-expanded="false"
       aria-autocomplete="list" aria-controls="country-list" aria-activedescendant="" />
<ul role="listbox" id="country-list" aria-labelledby="combo-label" hidden>
  <li role="option" id="opt-1">United States</li>
  <li role="option" id="opt-2">Canada</li>
</ul>
```

### Dynamic state updates (JS)

```javascript
function toggleDropdown(button) {
  const menu = document.getElementById(button.getAttribute('aria-controls'));
  const isExpanded = button.getAttribute('aria-expanded') === 'true';

  button.setAttribute('aria-expanded', !isExpanded);
  menu.setAttribute('aria-hidden', isExpanded);
  menu.style.display = isExpanded ? 'none' : 'block';
}

function selectTab(tab) {
  const tablist = tab.closest('[role="tablist"]');

  tablist.querySelectorAll('[role="tab"]').forEach(t => {
    t.setAttribute('aria-selected', 'false');
    t.setAttribute('tabindex', '-1');
  });

  tab.setAttribute('aria-selected', 'true');
  tab.setAttribute('tabindex', '0');

  const panel = document.getElementById(tab.getAttribute('aria-controls'));
  document.querySelectorAll('[role="tabpanel"]').forEach(p => p.hidden = true);
  panel.hidden = false;
}
```

### Landmark roles

```html
<div role="banner"><!-- header --></div>
<div role="navigation" aria-label="Main"><!-- nav links --></div>
<div role="main"><!-- primary content --></div>
<div role="complementary"><!-- sidebar --></div>
<div role="contentinfo"><!-- footer --></div>
```

### Toggle button

```html
<button aria-pressed="false" aria-label="Enable dark mode" onclick="toggleDarkMode(this)">
  <span aria-hidden="true">🌙</span>
</button>

<script>
function toggleDarkMode(button) {
  const isPressed = button.getAttribute('aria-pressed') === 'true';
  button.setAttribute('aria-pressed', !isPressed);
  button.setAttribute('aria-label', isPressed ? 'Enable dark mode' : 'Disable dark mode');
}
</script>
```

## When ARIA is unnecessary

Native HTML elements (`<button>`, `<nav>`, `<dialog>`, `<select>`) already have the right semantics —
adding ARIA roles to them is redundant, and sometimes harmful (redundancy can confuse a screen reader).

## Advantages

- Custom widgets become usable for screen readers.
- State changes are announced automatically.
- Complex components (combobox, tree view, accordion) become accessible.
- Relationships between elements become unambiguous thanks to `aria-controls`/`aria-describedby`.

## Disadvantages / trade-offs

- **Incorrect ARIA makes accessibility worse** than its absence.
- The specification is complex, with strict parent-child relationship requirements (e.g. `role="tab"` must be
  a child of `role="tablist"`).
- It is easy to overdo — redundant roles on elements that already have native semantics.
- ARIA **does not add behaviour** — a role/attribute alone without the matching JS is a facade without function.
- Automated tests detect only syntax errors, not whether the use makes sense.
- `aria-hidden="true"` hides the element **and all its descendants** — it is easy to accidentally hide more than
  intended.
- Dynamic updates may not be announced without the appropriate live regions.

## Related patterns

- [Semantic HTML](semantic-html.md) — Fundamentals
- [Keyboard Navigation](keyboard-navigation.md) — Accessibility
- [Accessible Forms](accessible-forms.md) — Accessibility
- [ARIA in HTML — W3C](https://www.w3.org/TR/html-aria/)
- [WAI-ARIA Overview — MDN](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA)
- [ARIA Authoring Practices Guide — W3C](https://www.w3.org/WAI/ARIA/apg/)

## When to use / when NOT to use

Use ARIA **only when you are building a custom widget that native HTML does not express**
(a custom dropdown, a tab panel, a combobox). If you can use `<button>`, `<details>`, `<dialog>`,
`<select>` — use them and **do not add ARIA on top** — this is a classic case of YAGNI/KISS (eng-design-principles): the native element already solves the problem, adding roles "just in
case" only increases the risk of a mistake with zero benefit. Before you add an ARIA attribute, ask: "is there
a native HTML element that already does this?" — if so, ARIA is unnecessary here.
