# Keyboard Navigation

> **Contents:** Metadata · TLDR · Notes (state as of 2026, corrections to the source) · Problem · Solution · Code examples · Advantages · Disadvantages / trade-offs · Related patterns · When to use / when NOT to use

Source: frontendpatterns.dev/keyboard-navigation (Den Odell).

## Metadata

- **Category:** Accessibility
- **Level:** Beginner
- **Examples:** Native web

## TLDR

"Make all interactive elements reachable and operable via keyboard using logical tab order, arrow
key patterns, and standard shortcuts."

## Notes (state as of 2026, corrections to the source)

- **Do not reset `*:focus { outline: none; }`** — browsers themselves show the ring only for `:focus-visible`;
  a global reset of `:focus` takes away programmatic focus (e.g. headings after navigation). A `:focus-visible`
  style is enough. The CSS was corrected.
- The dropdown example is a sketch — a full listbox/combobox requires `aria-activedescendant` with option IDs, Home/End,
  type-ahead. Before you write your own: the native `<select>` (stylable in Chromium through `appearance: base-select`)
  or a headless library (Radix, React Aria, Angular Aria/CDK `ListKeyManager`).
- Shortcuts: `e.key` depends on the layout and Shift (`'s'` vs `'S'`) — compare `e.key.toLowerCase()` or `e.code` for
  the key position; do not intercept shortcuts in text fields without need. Expose the shortcuts (`aria-keyshortcuts`,
  a "?" help).

## Problem

Custom UI components built from `<div>` and CSS often fail at keyboard
accessibility: elements are not focusable by default, standard key interactions
(Enter, arrows) do not work, users get "trapped" in modals with no way out via
the keyboard. Hover-dependent menus completely exclude keyboard users, and custom
implementations often break established interaction conventions.

## Solution

Interactive elements must be reachable with Tab and operable with the keyboard alone. Semantic
HTML elements (`<button>`, `<a>`, `<input>`) give this automatically. For custom widgets —
apply the WAI-ARIA patterns: arrows navigate lists, Enter/Space activate elements, Escape closes
overlays. Use `tabindex="0"` for focusability, add `keydown` handlers, keep visible
focus indicators (`:focus-visible`) and always provide keyboard alternatives for mouse-dependent
features.

## Code examples

### A dropdown with keyboard navigation

```javascript
function Dropdown({ items, onSelect }) {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);

  const handleKeyDown = (e) => {
    if (!isOpen && (e.key === ' ' || e.key === 'Enter')) {
      setIsOpen(true);
      e.preventDefault();
      return;
    }
    if (isOpen) {
      if (e.key === 'ArrowDown') {
        setSelectedIndex((prev) => Math.min(prev + 1, items.length - 1));
      } else if (e.key === 'ArrowUp') {
        setSelectedIndex((prev) => Math.max(prev - 1, 0));
      } else if (e.key === 'Enter' || e.key === ' ') {
        onSelect(items[selectedIndex]);
        setIsOpen(false);
      } else if (e.key === 'Escape') {
        setIsOpen(false);
      }
      e.preventDefault();
    }
  };

  return (
    <div
      role="combobox"
      aria-expanded={isOpen}
      aria-haspopup="listbox"
      tabIndex={0}
      onKeyDown={handleKeyDown}
    >
      <div className="dropdown-trigger">{items[selectedIndex].label}</div>
      {isOpen && (
        <ul role="listbox">
          {items.map((item, index) => (
            <li key={item.id} role="option" aria-selected={index === selectedIndex}>
              {item.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

### A tab panel with roving tabindex

```javascript
function TabPanel({ tabs }) {
  const [activeTab, setActiveTab] = useState(0);

  const handleKeyDown = (e) => {
    if (e.key === 'ArrowRight') setActiveTab((activeTab + 1) % tabs.length);
    else if (e.key === 'ArrowLeft') setActiveTab((activeTab - 1 + tabs.length) % tabs.length);
    else if (e.key === 'Home') setActiveTab(0);
    else if (e.key === 'End') setActiveTab(tabs.length - 1);
    else return;
    e.preventDefault();
  };

  return (
    <div>
      <div role="tablist">
        {tabs.map((tab, index) => (
          <button
            key={tab.id}
            role="tab"
            aria-selected={activeTab === index}
            tabIndex={activeTab === index ? 0 : -1}
            onClick={() => setActiveTab(index)}
            onKeyDown={handleKeyDown}
          >
            {tab.label}
          </button>
        ))}
      </div>
      {tabs.map((tab, index) => (
        <div key={tab.id} role="tabpanel" hidden={activeTab !== index} tabIndex={0}>
          {tab.content}
        </div>
      ))}
    </div>
  );
}
```

### A modal with keyboard handling (Escape)

```javascript
function Modal({ isOpen, onClose, children }) {
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      tabIndex={-1}
    >
      <h2>Modal Title</h2>
      <div>{children}</div>
      <button onClick={onClose}>Close</button>
    </div>
  );
}
```

### Keyboard shortcuts

```javascript
function Editor() {
  const handleKeyDown = (e) => {
    const mod = e.ctrlKey || e.metaKey;
    if (mod && e.key === 's') { handleSave(); e.preventDefault(); }
    if (mod && e.key === 'z' && !e.shiftKey) { handleUndo(); e.preventDefault(); }
    if (mod && e.key === 'z' && e.shiftKey) { handleRedo(); e.preventDefault(); }
  };

  return (
    <div onKeyDown={handleKeyDown}>
      <textarea placeholder="Press Ctrl+S to save" />
    </div>
  );
}
```

### Skip links

```javascript
function Layout({ children }) {
  return (
    <>
      <a href="#main-content" className="skip-link">Skip to main content</a>
      <nav>{/* Navigation links */}</nav>
      <main id="main-content" tabIndex={-1}>{children}</main>
    </>
  );
}
```

### Focus indicators

```css
/* No global *:focus { outline: none } — browsers already limit the ring to :focus-visible */
:focus-visible { outline: 2px solid var(--focus-ring); outline-offset: 2px; }

@media (prefers-contrast: high) {
  *:focus-visible { outline: 3px solid currentColor; }
}
```

## Advantages

- Assistive technologies depend on the keyboard interface — working keyboard navigation
  also ensures compatibility with screen readers.
- Advanced users operate faster with the keyboard than with the mouse.
- "WCAG Level A requires keyboard operability, making this a legal requirement in many
  jurisdictions."
- Motor disabilities, RSI and temporary injuries prevent many people from using a mouse.
- Keeping keyboard focus eliminates switching between mouse and keyboard, especially when
  entering data.

## Disadvantages / trade-offs

- Custom widgets require an extensive implementation — semantic HTML gives keyboard
  support automatically, styled `<div>` elements require manual handlers.
- WAI-ARIA patterns are complex — a correct listbox needs Home, End, PageUp, PageDown, "type-ahead"
  search and handling of the selection mode.
- Custom keyboard shortcuts can clash with the browser's default shortcuts; `preventDefault()`
  removes native functionality.
- Intercepting arrows can disorient users who expect scrolling — it requires
  careful management of event propagation.
- Maintaining roving tabindex gets hard with dynamic lists (managing `tabindex="0"`
  vs `-1`).
- Keyboard shortcuts are invisible without documentation/hints — the user does not know they exist.
- International keyboards (AZERTY, Dvorak) have keys placed differently from QWERTY, which makes
  some shortcuts awkward or unavailable.
- The visibility of the focus indicator is sometimes a source of design tension — accessibility-compliant indicators
  often go beyond the designer's visual preferences.
- Testing keyboard navigation requires manual interaction — automated scanners do not assess
  the quality of the actual user experience.

## Related patterns

- [Focus Management](focus-management.md) — Accessibility
- [Focus Trap](focus-trap.md) — Accessibility
- [ARIA Roles and Attributes](aria-roles-and-attributes.md) — Accessibility
- [Keyboard Navigation — MDN](https://developer.mozilla.org/en-US/docs/Web/Accessibility/Keyboard-navigable_JavaScript_widgets)
- [Keyboard Accessibility — W3C](https://www.w3.org/WAI/WCAG21/Understanding/keyboard.html)
- [WAI-ARIA Keyboard Patterns — W3C](https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/)

## When to use / when NOT to use

Always, whenever you build **any** interactive element — this is not an optional enhancement, WCAG
Level A requires keyboard operability and it is a legal requirement in many jurisdictions. By default reach
for native elements (`<button>`, `<a>`, `<select>`) — they give this for free, without writing a single
`keydown` handler. Write your own keyboard logic (arrows, roving tabindex) only for widgets that
native HTML does not support (a custom combobox, a tab panel) — do not recreate by hand behaviour that
`<select>`/`<button>` already have built in.
