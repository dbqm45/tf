# CSS Modules & Scoped Styles

> **Contents:** Metadata · TLDR · Notes (state in 2026, corrections to the source) · Problem · Solution · Code examples · Advantages · Disadvantages / tradeoffs · Related patterns · When to use / when NOT to use

Source: frontendpatterns.dev/css-modules-and-scoped-styles.

## Metadata

- **Category:** Styling
- **Level:** Beginner
- **Framework examples:** React, Vue, Svelte, Native web
- **Last updated:** 13 December 2025
- **Author:** Den Odell

## TLDR

"Scope styles to components by generating unique class names at build time, preventing conflicts
without runtime overhead."

## Notes (state in 2026, corrections to the source)

- Isolation mechanisms in frameworks: Angular — `ViewEncapsulation.Emulated` (the default, `_ngcontent-*` attributes),
  `ShadowDom`, `None`; `:host`, `::ng-deep` is deprecated (fw-angular). Vue `scoped`/`module`; Svelte — by default;
  Web Components — Shadow DOM + `::part()`.
- A native alternative without a build: **`@scope (.card) to (.card__content) { … }`** — Baseline since the end of 2025 (all
  major engines); together with `@layer` cascade layers (reset, tokens, components, utilities) it solves most
  collisions without generated names.
- The values in the examples (`blue`, `10px`, `#1a1a1a`) are an illustration — in the project, only tokens (SKILL.md).
- Theme: switch tokens on `:root`/`[data-theme]` and use `light-dark()` + `color-scheme`, instead of theme classes
  from a module.
- Svelte: the example is in Svelte 4 syntax (`export let`); in Svelte 5 `let { variant = 'primary' } = $props()`.
  Vue: the `$style` example is in the Options API — in `<script setup>` use `useCssModule()`.
- Types for CSS Modules: Vite/TS — `vite/client` gives a general type; exact keys are generated e.g. by `typed-css-modules`
  or a TS plugin (lang-typescript).

## Problem

The global CSS namespace creates conflicts between teams and libraries — two different people (or
a person and a component library) can name a class `.header`. The author describes a situation in which a change to
`.button` in one place broke a button's padding in a completely different area of the application. The BEM
convention (`.component-name__element-name--modifier`) mitigates the problem, but it requires the discipline of the whole
team and in practice gets long/verbose.

## Solution

Tools working at build time automatically transform readable class names into unique
identifiers — `.button` becomes `.Button_button__a1b2c3`. The style is imported as a JavaScript
module: `import styles from './Button.module.css'`. Vue does this with `data-v-*` attributes, Svelte
generates unique classes at compile time. "When you genuinely need global styles, use `:global()`
selectors."

## Code examples

### Basic Scoped Styles — React

```javascript
/* Button.module.css */
.button {
  padding: 10px;
  border-radius: 4px;
}

.primary { background: blue; }
.secondary { background: gray; }
.large { padding: 16px; font-size: 18px; }

import styles from './Button.module.css';

function Button({ variant = 'primary', size = 'normal', children }) {
  const className = [
    styles.button,
    styles[variant],
    size === 'large' && styles.large
  ].filter(Boolean).join(' ');

  return <button className={className}>{children}</button>;
}
```

### Basic Scoped Styles — Vue (Scoped)

```vue
<template>
  <button class="button primary">Click me</button>
</template>

<style scoped>
/* Vue adds data-v-xxx attribute to scope these rules */
.button { padding: 10px; }
.primary { background: blue; }

/* Deep selector affects child components */
.button :deep(.icon) { margin-right: 8px; }
</style>
```

### Basic Scoped Styles — Vue (CSS Modules)

```vue
<template>
  <button :class="$style.button">Click me</button>
</template>

<style module>
.button { background: blue; padding: 10px; }
</style>

<script>
export default {
  mounted() {
    console.log(this.$style.button); // "button_1a2b3c"
  }
}
</script>
```

### Basic Scoped Styles — Svelte

```svelte
<script>
  export let variant = 'primary';
</script>

<button class="button {variant}">Click me</button>

<style>
  /* Svelte scopes these automatically */
  .button { padding: 10px; border-radius: 4px; }
  .primary { background: blue; }
  .secondary { background: gray; }

  :global(body) { margin: 0; }
</style>
```

### Composition

```css
/* shared.module.css */
.baseButton { padding: 10px; border: none; border-radius: 4px; cursor: pointer; }

/* Button.module.css */
.button {
  composes: baseButton from './shared.module.css';
  background: blue;
}

.iconButton {
  composes: baseButton from './shared.module.css';
  background: transparent;
}
```

```javascript
import styles from './Button.module.css';

<button className={styles.button}>Primary</button>
<button className={styles.iconButton}>Icon</button>
```

### Global Styles

```css
/* App.module.css */
:global(.legacy-class) { color: red; }

.container { padding: 20px; }
.container :global(.legacy-component) { margin: 10px; }
```

### TypeScript Support

```typescript
// Button.module.css.d.ts (auto-generated or manual)
declare const styles: {
  readonly button: string;
  readonly primary: string;
};
export default styles;

import styles from './Button.module.css';

<button className={styles.button}>Click</button>
<button className={styles.nonexistent}>Error</button> // TS error
```

### Dynamic Classes with classnames

```javascript
import styles from './Button.module.css';
import classNames from 'classnames';

function Button({ variant, size, disabled, children }) {
  const buttonClass = classNames(styles.button, styles[variant], {
    [styles.large]: size === 'large',
    [styles.disabled]: disabled
  });
  return <button className={buttonClass}>{children}</button>;
}
```

### Theming with CSS Variables

```css
/* theme.module.css */
.light { --primary: blue; --bg: white; }
.dark { --primary: lightblue; --bg: #1a1a1a; }
```

```javascript
import theme from './theme.module.css';
import styles from './Button.module.css';

function App({ isDark }) {
  return (
    <div className={isDark ? theme.dark : theme.light}>
      <button className={styles.button}>Themed</button>
    </div>
  );
}
```

### Build Tool Configuration

```javascript
// webpack.config.js
module.exports = {
  module: {
    rules: [{
      test: /\.module\.css$/,
      use: ['style-loader', {
        loader: 'css-loader',
        options: { modules: { localIdentName: '[name]__[local]___[hash:base64:5]' } }
      }]
    }]
  }
};

// vite.config.js
export default {
  css: {
    modules: { localsConvention: 'camelCase', generateScopedName: '[name]__[local]___[hash:base64:5]' }
  }
};
```

## Advantages

- Name conflicts disappear completely — without a manual naming convention.
- Isolation enforced by tools, not by team discipline (as in BEM).
- Zero runtime cost — everything is resolved at build time.
- It is ordinary CSS syntax — no new language to learn.
- Safer refactoring thanks to explicit, imported dependencies.
- Dead code is easier to find — an unused CSS module is visible.
- `:global()` lets you deliberately step outside the isolation when needed (integration with third-party libraries).

## Disadvantages / tradeoffs

- DevTools shows generated, unreadable class names (`Button_button__a1b2c3`) — this makes
  debugging harder without source maps.
- Sharing styles between modules requires explicit composition (`composes`).
- Fully dynamic styles are hard — CSS Modules are static; you need CSS custom properties or
  inline style.
- Requires build tool configuration (Webpack, Vite, Parcel).
- CSS frameworks (Bootstrap, Material UI) assume global classes — `:global()` wrappers are needed.
- Concatenating many classes gets verbose — template literals or a helper (`classnames`) are needed.
- TypeScript support requires generated/manual type declarations for CSS modules.

## Related patterns

- CSS Modules — the GitHub repository.
- CSS Modules Specification — CSS-Tricks.
- Scoped CSS — the official Vue.js documentation.

## When to use / when NOT to use

Use it by default in every component project with a real risk of CSS name collisions (more than
one team/library in the same style base) — it is a low cost for full isolation without runtime
overhead. It is **not** the only way: for very small, single-person projects or for styles that are
global by nature (reset, design tokens, theme) a simpler, single global CSS stylesheet may be
enough — do not introduce build-time tooling only to "do it properly" if the
name collision problem does not occur in practice (YAGNI — eng-design-principles).
