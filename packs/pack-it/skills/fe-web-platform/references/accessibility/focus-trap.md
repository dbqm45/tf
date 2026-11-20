# Focus Trap

> **Contents:** Metadata · TLDR · Notes (state as of 2026, corrections to the source) · Problem · Solution · Code examples · Advantages · Disadvantages / trade-offs · Related patterns · When to use / when NOT to use

Source: frontendpatterns.dev/focus-trap (Den Odell, updated 7 October 2025).

## Metadata

- **Category:** Accessibility
- **Level:** Beginner
- **Examples:** Vue, Native web (React also appears in the code examples)

## TLDR

"Trap keyboard focus inside modals and dialogs by cycling Tab through interactive elements and
preventing escape to background content."

## Notes (state as of 2026, corrections to the source)

- **The first choice in 2026: `<dialog>` with `showModal()`** — the browser itself makes the background inert (also for screen readers),
  handles Escape (`cancel`) and restores focus. A manual trap only for custom overlays.
- The `inert` attribute is enough on its own — it also hides from assistive technologies; adding `aria-hidden="true"`
  on the same container is redundant.
- The "focusable" selector from the examples omits, among others, `[contenteditable]`, `summary`, `audio[controls]` and does not
  exclude `disabled`/hidden ones — libraries (`focus-trap`, `tabbable`, Angular CDK `cdkTrapFocus`) do it correctly.
- `focus-trap-react` since v10: the child element must accept a ref; the `active`/`paused` option for nesting.

## Problem

Keyboard users, pressing Tab, can leave the modal and reach the background content — even though
visually the background is dimmed/obscured. Screen readers additionally "announce" this background content,
creating a mismatch between what is visible (only the modal) and what is actually accessible to
assistive technologies (the whole page).

## Solution

Intercept `Tab` and `Shift+Tab` to cycle focus between the first and the last
interactive element of the modal. The implementation requires:
- finding all the focusable elements inside the modal,
- tracking which is the first and which the last,
- listening for `Tab` to redirect focus at the boundaries,
- adding `aria-modal="true"`,
- considering the `inert` attribute for the background content,
- providing an obvious way out (`Escape`, a visible "Close" button).

## Code examples

### A basic implementation — React

```javascript
function Modal({ children, onClose }) {
  const modalRef = useRef();

  useEffect(() => {
    if (!modalRef.current) return;

    const focusableElements = modalRef.current.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    const trapFocus = (e) => {
      if (e.key === 'Tab') {
        if (e.shiftKey && document.activeElement === firstElement) {
          lastElement.focus();
          e.preventDefault();
        } else if (!e.shiftKey && document.activeElement === lastElement) {
          firstElement.focus();
          e.preventDefault();
        }
      }
      if (e.key === 'Escape') onClose();
    };

    modalRef.current.addEventListener('keydown', trapFocus);
    firstElement?.focus();

    return () => modalRef.current?.removeEventListener('keydown', trapFocus);
  }, [onClose]);

  return (
    <div ref={modalRef} role="dialog" aria-modal="true">
      {children}
    </div>
  );
}
```

### A basic implementation — Vue

```vue
<template>
  <div v-if="isOpen" ref="modalRef" role="dialog" aria-modal="true" @keydown="handleKeydown">
    <h2 ref="firstFocusable" tabindex="-1">Modal Title</h2>
    <slot />
    <button @click="$emit('close')">Close</button>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';

const props = defineProps(['isOpen']);
const emit = defineEmits(['close']);
const modalRef = ref(null);
const firstFocusable = ref(null);

const handleKeydown = (e) => {
  if (e.key === 'Escape') { emit('close'); return; }
  if (e.key !== 'Tab') return;

  const focusable = modalRef.value.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  const first = focusable[0], last = focusable[focusable.length - 1];

  if (e.shiftKey && document.activeElement === first) {
    last.focus(); e.preventDefault();
  } else if (!e.shiftKey && document.activeElement === last) {
    first.focus(); e.preventDefault();
  }
};

watch(() => props.isOpen, (isOpen) => { if (isOpen) firstFocusable.value?.focus(); });
</script>
```

### A basic implementation — Web Components

```javascript
class FocusTrapDialog extends HTMLElement {
  connectedCallback() {
    this.attachShadow({ mode: 'open' });
    this.render();
    this.setupFocusTrap();
  }

  setupFocusTrap() {
    const selector = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';

    this.addEventListener('keydown', (e) => {
      const focusable = this.shadowRoot.querySelectorAll(selector);
      const first = focusable[0], last = focusable[focusable.length - 1];

      if (e.key === 'Tab') {
        if (e.shiftKey && document.activeElement === first) {
          last.focus(); e.preventDefault();
        } else if (!e.shiftKey && document.activeElement === last) {
          first.focus(); e.preventDefault();
        }
      }
      if (e.key === 'Escape') this.close();
    });

    this.shadowRoot.querySelector(selector)?.focus();
  }

  close() { this.dispatchEvent(new CustomEvent('close')); }

  render() {
    this.shadowRoot.innerHTML = `
      <div role="dialog" aria-modal="true">
        <h2>Dialog Title</h2>
        <slot></slot>
        <button id="close-btn">Close</button>
      </div>
    `;
    this.shadowRoot.getElementById('close-btn').addEventListener('click', () => this.close());
  }
}

customElements.define('focus-trap-dialog', FocusTrapDialog);
```

### A focus trap with `inert` on the background

```javascript
function Modal({ isOpen, onClose, children }) {
  const previousFocusRef = useRef();

  useEffect(() => {
    const mainContent = document.querySelector('#root');
    if (isOpen) {
      previousFocusRef.current = document.activeElement;
      mainContent?.setAttribute('inert', '');
      mainContent?.setAttribute('aria-hidden', 'true');
    } else {
      mainContent?.removeAttribute('inert');
      mainContent?.removeAttribute('aria-hidden');
      previousFocusRef.current?.focus();
    }
    return () => {
      mainContent?.removeAttribute('inert');
      mainContent?.removeAttribute('aria-hidden');
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <FocusTrap>
      <div role="dialog" aria-modal="true">
        <h2>Modal Title</h2>
        {children}
        <button onClick={onClose}>Close</button>
      </div>
    </FocusTrap>
  );
}
```

### Using the `focus-trap-react` library

```javascript
import FocusTrap from 'focus-trap-react';

function Modal({ isOpen, onClose, children }) {
  if (!isOpen) return null;

  return (
    <FocusTrap focusTrapOptions={{
      initialFocus: '#modal-title',
      escapeDeactivates: true,
      returnFocusOnDeactivate: true
    }}>
      <div role="dialog" aria-modal="true">
        <h2 id="modal-title">Modal Title</h2>
        {children}
        <button onClick={onClose}>Close</button>
      </div>
    </FocusTrap>
  );
}
```

**A note from the source about nested modals:** "For nested modals like confirmation dialogs inside
settings panels, set `active={false}` on the parent trap when the child opens to transfer focus
control."

## Advantages

- Keyboard behaviour matches visual behaviour (what looks unavailable is also
  unavailable to Tab).
- Users cannot accidentally activate hidden background content.
- This is a WCAG requirement for modal dialogs, not an optional refinement.
- Users stay oriented in the modal's context, they do not "get lost" in the content under it.

## Disadvantages / trade-offs

- Tracking focusable elements is complex — disabled elements, `tabindex="-1"`, hidden
  elements and collapsed containers all need to be taken into account.
- Dynamic content breaks the trap when elements appear/disappear after it is set up.
- Nested modals require careful coordination (see the note about `active={false}` above).
- The virtual cursors of screen readers can sometimes "escape" the trap despite a correct implementation.
- The `inert` attribute now has full browser support and is the **preferred** way of blocking
  the background — simpler than managing `aria-hidden` + a focus trap by hand at the same time.
- Libraries (e.g. `focus-trap-react`) add weight to the bundle.
- Testing requires real assistive technology, not only unit tests.

## Related patterns

- [Focus Management](focus-management.md) — Accessibility
- [Keyboard Navigation](keyboard-navigation.md) — Accessibility
- [ARIA Roles and Attributes](aria-roles-and-attributes.md) — Accessibility
- [Focus Trap Pattern — W3C APG](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/)
- [focus-trap Library — GitHub](https://github.com/focus-trap/focus-trap)
- [Modal Dialog Accessibility — W3C](https://www.w3.org/WAI/ARIA/apg/patterns/dialogmodal/)

## When to use / when NOT to use

Use it **always** with modals/dialogs that block the rest of the page — it is a WCAG requirement, not
an option. If the target browsers support the `inert` attribute (today practically all modern ones)
— **prefer `inert` on the background container** over writing a focus trap from scratch by hand; it is a simpler,
native mechanism doing the same with a lower risk of error (less code to maintain = fewer
places for a bug, in line with KISS — eng-design-principles). Write your own trap by hand only when
you need behaviour that `inert` does not give (e.g. a subtly different blocking scope), or when
the support of the target browsers requires it.
