# Focus Management

> **Contents:** Metadata · TLDR · Notes (state as of 2026, corrections to the source) · Problem · Solution · Code examples · Advantages · Disadvantages / trade-offs · Related patterns · When to use / when NOT to use

Source: frontendpatterns.dev/focus-management (Den Odell, updated 2 October 2025).

## Metadata

- **Category:** Accessibility
- **Level:** Beginner
- **Examples:** React, Vue

## TLDR

"Move focus programmatically after route changes, modal opens, and dynamic content updates so
keyboard users always know where they are."

## Notes (state as of 2026, corrections to the source)

- **The native `<dialog>` + `showModal()`** moves focus into the dialog by itself (or to the element with `autofocus`), blocks the background
  (the top layer, the rest of the page is inert), closes with Escape and restores focus after closing — prefer it to
  the manual management from the examples (focus-trap.md).
- After SPA navigation: focus on the `<h1>` of the new view (`tabindex="-1"`) + an update of `document.title`; routers
  sometimes do this themselves (Angular/React Router do not — it has to be added).
- The "removing from a list" example uses `setTimeout(…, 0)` — in React 19 it is clearer: `flushSync` or an effect after
  the list update; in Angular `afterNextRender`.
- Take the skip link and focus outline colours from tokens (fe-css); a focus indicator with contrast ≥ 3:1 (1.4.11),
  not hidden by sticky headers (2.4.11, WCAG 2.2) — wcag-levels.md.
- The "Focus trap inside a dialog" example has a full version in focus-trap.md.

## Problem

- Opening a modal does not move focus — the user stays on the button under the overlay.
- Navigating to a new page (SPA) leaves focus on the clicked link — you have to go through 30+
  elements to reach the new content.
- Removing an element from a list loses focus or jumps to the browser's address bar.
- Expanding an accordion leaves focus on the trigger, not on the newly shown content.

## Solution

The basic rule: **move focus programmatically** when the interface changes in a way that affects
the user's next interaction.

**Key practices:**
- Opening a modal → move focus into it.
- Closing a modal → restore focus to the element that opened it.
- SPA navigation → direct focus to the heading of the new page.
- Removing an element from a list → move focus to the next element (or the previous one, if the removed one was
  the last).
- Important notifications → consider moving focus (or a live region — see `live-regions.md`).

**The technical approach:** `element.focus()` for programmatic moving; `tabindex="-1"` on
elements that should be focusable programmatically but not with Tab (headings, containers);
remembering the previously focused element before opening an overlay.

## Code examples

### Focus management in a modal — Web Components

```javascript
class Modal extends HTMLElement {
  constructor() {
    super();
    this.previouslyFocusedElement = null;
  }

  set open(value) {
    this._open = value;
    if (value) {
      this.previouslyFocusedElement = document.activeElement;
      this.render();
      this.querySelector('[role="dialog"]')?.focus();
    } else {
      this.previouslyFocusedElement?.focus();
      this.previouslyFocusedElement = null;
    }
  }

  render() {
    if (this._open) {
      this.innerHTML = `
        <div role="dialog" aria-modal="true" tabindex="-1">
          <h2>Modal Title</h2>
          <button class="close">Close</button>
        </div>
      `;
      this.querySelector('.close').addEventListener('click', () => {
        this.open = false;
      });
    }
  }
}
customElements.define('modal-dialog', Modal);
```

### Focus management in a modal — React

```javascript
import { useEffect, useRef } from 'react';

function Modal({ isOpen, onClose, children }) {
  const dialogRef = useRef(null);
  const previousFocusRef = useRef(null);

  useEffect(() => {
    if (isOpen) {
      previousFocusRef.current = document.activeElement;
      dialogRef.current?.focus();
    } else {
      previousFocusRef.current?.focus();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div role="dialog" aria-modal="true" ref={dialogRef} tabIndex={-1}>
      {children}
      <button onClick={onClose}>Close</button>
    </div>
  );
}
```

### Focus management in a modal — Vue

```vue
<script setup>
import { ref, watch, nextTick } from 'vue';

const isModalOpen = ref(false);
const modalRef = ref(null);
let previouslyFocusedElement = null;

const openModal = () => {
  previouslyFocusedElement = document.activeElement;
  isModalOpen.value = true;
};

const closeModal = () => {
  isModalOpen.value = false;
  previouslyFocusedElement?.focus();
};

watch(isModalOpen, async (isOpen) => {
  if (isOpen) {
    await nextTick();
    modalRef.value?.focus();
  }
});
</script>

<template>
  <button @click="openModal">Open Modal</button>
  <div v-if="isModalOpen" ref="modalRef" role="dialog" tabindex="-1">
    <button @click="closeModal">Close</button>
  </div>
</template>
```

### Focus after a route change (React Router)

```javascript
import { useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';

function App() {
  const location = useLocation();
  const mainContentRef = useRef(null);

  useEffect(() => {
    mainContentRef.current?.focus();
  }, [location.pathname]);

  return (
    <main>
      <h1 ref={mainContentRef} tabIndex={-1}>
        {getPageTitle(location.pathname)}
      </h1>
      <Routes>{/* routes */}</Routes>
    </main>
  );
}
```

### Skip link

```html
<a href="#main-content" class="skip-link">Skip to main content</a>
<nav><!-- Navigation --></nav>
<main id="main-content" tabindex="-1"><!-- Content --></main>

<style>
  .skip-link {
    position: absolute;
    top: -40px;
    left: 0;
    padding: 8px;
    background: #000;
    color: white;
  }
  .skip-link:focus { top: 0; }
</style>
```

### Focus after removing an element from a list

```javascript
function TodoList({ items, onDelete }) {
  const itemRefs = useRef({});

  const handleDelete = (id, index) => {
    onDelete(id);
    const nextIndex = index < items.length - 1 ? index : index - 1;
    const nextItem = items[nextIndex];
    if (nextItem) {
      setTimeout(() => itemRefs.current[nextItem.id]?.focus(), 0);
    }
  };

  return (
    <ul>
      {items.map((item, index) => (
        <li key={item.id} ref={el => itemRefs.current[item.id] = el} tabIndex={-1}>
          {item.text}
          <button onClick={() => handleDelete(item.id, index)}>Delete</button>
        </li>
      ))}
    </ul>
  );
}
```

### Focus trap inside a dialog

```javascript
function Dialog({ children }) {
  const dialogRef = useRef(null);

  useEffect(() => {
    const handleTab = (e) => {
      if (e.key !== 'Tab') return;

      const focusable = dialogRef.current.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      const first = focusable[0];
      const last = focusable[focusable.length - 1];

      if (e.shiftKey && document.activeElement === first) {
        last.focus();
        e.preventDefault();
      } else if (!e.shiftKey && document.activeElement === last) {
        first.focus();
        e.preventDefault();
      }
    };

    document.addEventListener('keydown', handleTab);
    return () => document.removeEventListener('keydown', handleTab);
  }, []);

  return <div role="dialog" ref={dialogRef}>{children}</div>;
}
```

### Styling a visible focus

```css
*:focus-visible {
  outline: 2px solid #0066cc;
  outline-offset: 2px;
}
```

## Advantages

- Keyboard users stay oriented — a logical move of focus.
- Conformance with WCAG 2.4.3 (Focus Order) — this is not an optional requirement.
- Screen readers announce the content when focus moves to it.
- Modals become really usable for keyboard users.
- Consistent patterns build "muscle memory" in users who use many similar
  applications.

## Disadvantages / trade-offs

- **Incorrect focus placement is worse than none** — it disorients more than
  leaving the default behaviour.
- Determining the "correct" focus target requires careful thought for each case.
- Asynchronous DOM updates complicate the process — the element you want to move focus to
  may not exist yet at the moment `.focus()` is called.
- `tabindex="-1"` on headings/containers confuses developers unfamiliar with this pattern.
- Different screen readers (NVDA, JAWS, VoiceOver) announce focus changes in subtly different ways.
- Focus indicators require balance — too subtle ones fail users with low vision.
- The browser's back/forward navigation **should not** move focus if the content has not
  changed.
- Too aggressive focus management (moving it too often/without need) is irritating.

## Related patterns

- [Keyboard Navigation](keyboard-navigation.md) — Accessibility
- [Focus Trap](focus-trap.md) — Accessibility
- [Accessible Forms](accessible-forms.md) — Accessibility
- [Focus Management — MDN](https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement/focus)
- [Managing Focus — WAI-ARIA — W3C](https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/)
- [Accessible Focus Indicators — W3C](https://www.w3.org/WAI/WCAG21/Understanding/focus-visible.html)

## When to use / when NOT to use

Apply it **always** when your UI has modals, SPA routing, lists with element removal or dynamically
shown content (accordions) — this is not an optional "extra", it is a WCAG 2.4.3 requirement. Beware of
overdoing it: do not move focus on **every** DOM change (e.g. on the browser's back/forward navigation
without a real content change) — excessive, unjustified moving of focus is in itself
an accessibility defect (see "Disadvantages" above), not only a lack of focus management.
