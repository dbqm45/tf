# Props and Attributes

> **Contents:** Metadata · TLDR · Notes (state in 2026, corrections to the source) · Problem · Solution · Code examples · Advantages · Disadvantages / tradeoffs · Related patterns · When to use / when NOT to use

Source: frontendpatterns.dev/props-and-attributes.

## Metadata

- **Category:** Components
- **Level:** Beginner
- **Examples:** React, Vue, Svelte, Native web
- **Last updated:** September 26, 2025
- **Author:** Den Odell

## TLDR

"Pass data into components through props to create flexible, reusable building blocks configured from the outside."

## Notes (state in 2026, corrections to the source)

- Equivalents of the input API: React props; Vue `defineProps`/`defineEmits`; Svelte 5 `$props()`; Angular (fw-angular)
  `input()`/`input.required()`/`output()`/`model()`; Web Components — attributes (strings) + JS properties.
- When boolean variants multiply, instead of more flags use a union (`variant: 'primary' | 'danger'`) or
  composition (children/slots/compound components — components/compound-components.md).
- The Web Components example corrected: `label` from an attribute went into `innerHTML` (XSS) — now `textContent`.
- The Svelte examples are Svelte 4 syntax (`export let`, `$:`, `on:click`, `<slot>`); in Svelte 5: `$props()`, `$state`,
  `$derived`, `$effect`, `onclick` attributes, snippets instead of slots.

## Problem

Without props, many almost identical duplicates of components appear (`SubmitButton.tsx`, `CancelButton.tsx` etc.) with values hard-coded inside. Testing becomes hard, because you cannot supply different data from the outside — you have to edit the component itself.

## Solution

Pass data in from the outside through props, instead of hard-coding it into the component. Props can be strings, numbers, objects, arrays, functions (callbacks). Set sensible default values and use TypeScript, so that the component's contract is explicit and statically checked.

## Code examples

### React — Basic Props

```javascript
function Button({ label, onClick, disabled = false, variant = 'primary', size = 'medium', icon = null }) {
  return (
    <button
      className={`btn btn-${variant} btn-${size}`}
      onClick={onClick}
      disabled={disabled}
    >
      {icon && <span className="btn-icon">{icon}</span>}
      {label}
    </button>
  );
}

<Button label="Submit" onClick={handleSubmit} />
<Button label="Cancel" onClick={handleCancel} variant="secondary" />
<Button label="Delete" onClick={handleDelete} variant="danger" disabled={loading} />
```

### Vue

```vue
<script setup>
const props = defineProps({
  label: { type: String, required: true },
  disabled: { type: Boolean, default: false },
  variant: { type: String, default: 'primary' },
  size: { type: String, default: 'medium' }
});
const emit = defineEmits(['click']);
</script>

<template>
  <button
    :class="`btn btn-${variant} btn-${size}`"
    :disabled="disabled"
    @click="emit('click')"
  >
    {{ label }}
  </button>
</template>
```

### Svelte

```svelte
<script>
  export let label;
  export let disabled = false;
  export let variant = 'primary';
  export let size = 'medium';
</script>

<button class={`btn btn-${variant} btn-${size}`} {disabled} on:click>
  {label}
</button>
```

### Web Components

```javascript
class Button extends HTMLElement {
  static get observedAttributes() { return ['label', 'disabled', 'variant']; }

  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._onClick = null;
  }

  connectedCallback() {
    this.render();
    this.shadowRoot.querySelector('button').addEventListener('click', () => {
      if (this._onClick) this._onClick();
      this.dispatchEvent(new CustomEvent('button-click'));
    });
  }

  attributeChangedCallback(name, oldValue, newValue) {
    if (oldValue !== newValue) this.render();
  }

  set onClick(handler) { this._onClick = handler; }

  render() {
    const label = this.getAttribute('label') || 'Button';
    const disabled = this.hasAttribute('disabled');
    const variant = this.getAttribute('variant') || 'primary';
    const button = document.createElement('button');
    button.className = `btn btn-${variant}`;
    button.disabled = disabled;
    button.textContent = label; // attribute values are untrusted text
    this.shadowRoot.replaceChildren(button);
  }
}
customElements.define('custom-button', Button);
```

### Props spreading

```javascript
function Card({ title, children, className, ...rest }) {
  return (
    <div className={`card ${className || ''}`} {...rest}>
      <h2>{title}</h2>
      <div className="card-content">{children}</div>
    </div>
  );
}

<Card title="User Profile" className="profile-card" data-testid="profile-card">
  <UserDetails />
</Card>
```

### TypeScript props

```typescript
interface ButtonProps {
  label: string;
  onClick: () => void;
  disabled?: boolean;
  variant?: 'primary' | 'secondary' | 'danger';
}

function Button({ label, onClick, disabled = false, variant = 'primary' }: ButtonProps) {
  return (
    <button className={`btn btn-${variant}`} onClick={onClick} disabled={disabled}>
      {label}
    </button>
  );
}
```

### Props with children

```javascript
function Card({ title, footer, children }) {
  return (
    <div className="card">
      {title && <div className="card-header"><h3>{title}</h3></div>}
      <div className="card-body">{children}</div>
      {footer && <div className="card-footer">{footer}</div>}
    </div>
  );
}

<Card title="User Profile" footer={<Button label="Save" />}>
  <UserForm />
</Card>
```

## Advantages

- One component, an unlimited number of configurations/uses.
- Testing becomes simple — you supply different props, you check different outputs.
- Components can be reused in different projects without modification.
- Compatibility with tools like Storybook (every combination of props = a separate "story").
- TypeScript catches prop type errors at compile time, not at runtime.
- The configuration logic is centralized in one place (the props definition), not scattered across copies of the component.

## Disadvantages / tradeoffs

- "Props explosion" — over time a component may require many, many properties.
- Conditional rendering logic depending on combinations of props accumulates.
- Prop drilling — passing data through many layers of intermediate components that do not use it themselves.
- Default values can mask errors (a missing, required prop goes unnoticed).
- Boolean props (`disabled`, `active`, `loading`...) in large numbers are hard to read in the component call.
- Spreading props (`{...rest}`) loses precise typing of what is actually passed.
- Web Components attributes natively support only strings — complex data (objects, functions) requires JS properties (`set onClick`), not HTML attributes.
- A large number of props/combinations means an exponential number of scenarios to test.

## Related patterns

- [ARIA Roles and Attributes](fe-web-platform/references/accessibility/aria-roles-and-attributes.md) — Accessibility.
- [Semantic HTML](fe-web-platform/references/accessibility/semantic-html.md) — Fundamentals.
- HTML Attributes — MDN.
- Passing Props — React docs.
- Props — Vue docs.
- Props — Svelte docs.

## When to use / when NOT to use

Use props for every value that can differ between uses of the component — this is literally the foundation of component architecture (see "Component-Driven Architecture" in `../principles.md`), not an optional technique.

When the number of props starts to grow endlessly (10+, many boolean flags combined with each other) — that is a signal that the component does too much at once; consider splitting it into smaller components (see [Single Responsibility](../fundamentals/single-responsibility.md)) or grouping related props into one configuration object, instead of adding yet another flat prop.
