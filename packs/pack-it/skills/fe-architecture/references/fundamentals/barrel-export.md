# Barrel Export

> **Contents:** Metadata · TLDR · Notes (state in 2026, corrections to the source) · Problem · Solution · Code examples · Advantages · Disadvantages / tradeoffs · Related patterns · When to use / when NOT to use

Source: frontendpatterns.dev/barrel-export ("Aggregate Module Exports").

## Metadata

- **Category:** Fundamentals
- **Level:** Beginner
- **Examples:** Native web
- **Last updated:** September 22, 2025
- **Author:** Den Odell

## TLDR

"Use index files to re-export modules from a single entry point, simplifying imports while being mindful of tree-shaking implications."

## Notes (state in 2026, corrections to the source)

- A barrel is the natural **public API of a module/slice** (FSD: the `index.ts` of every slice — fsd-screaming-architecture.md;
  the boundaries are enforced by a linter, e.g. `eslint-plugin-boundaries`, Nx `enforce-module-boundaries`).
- The cost in 2026: large barrels slow down the dev server/tests (loading the whole module graph) and hinder tree-shaking
  with side effects. Do not make a barrel of "everything" in `shared/`; import from submodules
  (`shared/ui/button`), mark packages `"sideEffects": false`.
- In TS with `verbatimModuleSyntax`/`isolatedModules` a re-export of types must be explicit: `export type { X }` or
  `export { type X }` (lang-typescript).

## Problem

Long import paths such as `import { Button } from './components/atoms/buttons/Button/Button.tsx'` expose the whole internal folder structure, which makes safe refactoring impossible (moving a file breaks every import). Without clear module boundaries, consumers import implementation details that were never meant to be shared publicly.

## Solution

Create an index file in the module's directory that re-exports the module's public API. Instead of a deep path — `import { Button } from './components'`. This lets you reorganize the inside of the folder without changing external imports and establishes an explicit boundary of what the module's public API is.

## Code examples

### A basic barrel

```javascript
// components/Button.js
export function Button(props) { /* ... */ }

// components/Input.js
export function Input(props) { /* ... */ }

// components/index.js - Barrel file
export { Button } from './Button';
export { Input } from './Input';

// Usage
import { Button, Input } from './components';
```

### A nested barrel pattern

```javascript
// components/forms/index.js
export { Input } from './Input';
export { TextArea } from './TextArea';

// components/buttons/index.js
export { PrimaryButton } from './PrimaryButton';

// components/index.js - Top-level barrel
export * from './forms';
export * from './buttons';

// Usage - Import from any level
import { Input } from './components/forms';
import { Input, PrimaryButton } from './components';
```

### Namespace import

```javascript
import * as Components from './components';

const button = <Components.Button label="Click me" />;
const { Button, Card } = Components;  // Can destructure
```

### Selective re-exporting (safer than `export *`)

```javascript
// utils/dateUtils.js
export function parseDate(str) { /* ... */ }
export function _internalHelper(date) { /* ... */ }  // Internal

// utils/index.js - Selective exports (prefer over export *)
export { parseDate, formatDate } from './dateUtils';
export { capitalize, truncate } from './stringUtils';
// Internal helpers stay hidden
```

### Re-exporting types in TypeScript

```typescript
// components/index.ts
export { Button, type ButtonProps } from './Button';
export { Input, type InputProps } from './Input';

// Usage
import { Button, type ButtonProps } from './components';
```

## Advantages

- Cleaner imports instead of long, deep paths.
- Easier refactoring — files inside the module can be moved freely without breaking external imports.
- An explicit public API of the module — the barrel decides what is exposed and what stays internal.
- A hierarchical organization focused on module boundaries, not on the physical location of files.

## Disadvantages / tradeoffs

- **Tree-shaking:** "Using `export *` can prevent bundlers from eliminating unused code" — a barrel with `export *` can be worse for bundle size than direct imports.
- The barrel file must be updated with every new export of the module — an extra step to remember.
- Harder to trace which file a given export actually comes from (one more layer of indirection).
- The risk of circular dependencies when two barrels export from each other.

## Related patterns

- ES6 Modules — MDN.
- Tree Shaking and Barrel Files — Webpack docs.
- Module Systems — javascript.info.

## When to use / when NOT to use

Use barrel exports for **public API boundaries** — e.g. the whole `components/` or `utils/` folder, so that the consumer imports from one stable place, not from a deep internal path.

Do not use `export *` thoughtlessly on large modules in a project with a size-sensitive bundle — prefer selective, named re-exports (`export { X, Y } from './file'`), which the bundler analyses more easily for tree-shaking. If the project has no real bundle size problem (e.g. a small internal script), the difference is negligible — do not optimize it upfront without a reason (YAGNI, see `../principles.md`).
