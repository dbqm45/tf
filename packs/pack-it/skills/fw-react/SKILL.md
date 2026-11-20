---
name: fw-react
description: Use for React 18–19.3 code — pure components, state, when not to use an effect, Actions and forms, React Compiler, tests.
metadata:
  review: "2027-01-03"
  catalog: "Use for React code (18–19.3) regardless of the framework — components and hooks, state structure, effects and their replacements (computing during render, key, useEffectEvent), Actions and forms (useActionState, useOptimistic, use), React Compiler instead of manual memo, Suspense and error boundaries, tests with Testing Library, the 18→19 upgrade — and when deciding where to place domain concepts in a React application. Not for Next.js routing, cache and Server Actions (fw-nextjs), TypeScript syntax (lang-typescript) or general frontend architecture (fe-architecture)."
  keywords: "formularz w React, React Hook Form, react-hook-form, walidacja formularza, zod, zodResolver, schemat wspólny z serwerem, formularz wielokrokowy, kreator, useFieldArray, błędy z API w formularzu, React, komponent Reacta, hook, useEffect, useState, useMemo, useCallback, memo, re-render, useActionState, useOptimistic, useEffectEvent, React Compiler, JSX, tsx, Vite, form in React, form validation, schema shared with the server, multi-step form, wizard, API errors in a form, React component"
---

# React

**First check the version** (`detect_stack.py` / `package.json`). The rules below describe React 19.x; in an older
project take the equivalents from the "Version-dependent" section. React recommends starting a new React application with a framework
(Next.js App Router, React Router v7, Expo); without a framework — Vite. Create React App is deprecated (February 2025).

## Rules
1. **A component is pure:** the same props, state and context → the same JSX. Do not modify props, state, context or
   objects created before render. Side effects go into event handlers, and an effect is the last resort.
2. **Minimal state:**
   - group values that change together;
   - do not keep contradictory state (two flags instead of one `status`);
   - do not copy props into state;
   - keep the ID of the selected item, not its copy;
   - flatten nested data;
   - lift shared state up to the nearest common parent.
3. **When not to use an effect** (react.dev, "You Might Not Need an Effect"):
   - a value that can be **computed during render** you compute in the component body, without state and an effect;
     an expensive computation is memoized by the compiler or `useMemo`;
   - resetting all state when the identity changes (e.g. `userId`) → a different **`key`** on the component;
   - a reaction to a user action (a submit, a purchase, a notification) → an event handler, not an effect on state;
   - an effect is for synchronizing with an external system (a connection, a subscription, a widget from outside React)
     and always has a cleanup.
4. **An effect reads the current value but must not react to it** → `useEffectEvent` (19.2+). A function from it does not go
   into the dependencies and does not trigger resynchronization. Do not disable linter rules (`eslint-disable`) — that hides the bug.
5. **Fetching data:**
   - in an application with a framework — the framework's mechanism (in Next.js Server Components, fw-nextjs);
   - outside it — a library with a cache (e.g. TanStack Query) or `use(promise)` with a promise created outside render;
   - manual fetching in an effect requires a cleanup that ignores a late response (a race) or aborts
     the request through `AbortController`.
6. **Mutations and forms (19):**
   - `<form action={fn}>` and Actions (asynchronous functions in `startTransition`);
   - `useActionState` gives the result and a pending flag;
   - `useFormStatus` gives the form state in a child component;
   - complex forms (validation as you type, a wizard, field lists) with React Hook Form and a schema shared with the server,
     API errors, accessibility: `references/forms.md`;
   - `useOptimistic` shows the result before the server responds.
   Return a business rejection as action state, not an exception.
7. **Memoization:** in new code enable **React Compiler** (`babel-plugin-react-compiler` 1.x, the plugin run
   first; in Next.js `reactCompiler: true`) and the compiler rules from the `recommended` preset
   in **`eslint-plugin-react-hooks`** 7+. Manual `memo`/`useMemo`/`useCallback` only where a measurement or
   value identity requires it. Opting out for one component: the `"use no memo"` directive.
8. **Rules of hooks:**
   - call hooks only at the top level of a component or a custom hook;
   - do not call them in a condition, a loop, after an early `return`, in a handler, in `try/catch`;
   - a custom hook starts with `use` and shares logic, not state.
9. **Lists:** a stable `key` from the data (an ID), never the index for lists that change order.
10. **Boundaries:**
    - `<Suspense>` around the parts that wait for data;
    - an error boundary (a class component or the `react-error-boundary` library) at the feature level;
    - `<Activity mode="hidden">` (19.2) hides part of the UI while keeping its state.
11. **Tests:** Testing Library (`@testing-library/react`) — queries by role and text, interactions through `user-event`;
    you import `act` from `react` (not from `react-dom/test-utils`). Test domain logic as pure functions, without render.
    Runner: tool-vitest or tool-jest.

Examples (effect → computation, reset through `key`, `useEffectEvent`, a form with `useActionState`, a race when
fetching) and equivalents for React 18: `references/patterns.md`.

## Domain concepts in React — where things live
| Concept (glossary) | Place in a React application |
|---|---|
| **value object** | pure TS in `domain/` (lang-typescript); in the UI a presentational component or a formatting function (e.g. `<Money>`), a form control for a field repeated in many forms |
| **entity** | a domain type in `domain/`; the component gets it in props and does not modify it |
| **variants** | a discriminated union and a `switch` on `kind` in the component (exhaustive, with `never`); separate components for strongly different variants |
| **operation result** | the action state from `useActionState` (`ok` / `rejected` with a reason); a 409/422 rejection as a message, not an exception |
| **aggregate** | usually **on the backend**; in the frontend only for offline work — a class or module in `domain/`, called from a reducer |
| **state machine** | `useReducer` with a union of states and events; the reducer as a pure function tested without render |
| **event** | UI events through callback props (`onReserve`); domain events from the server (SSE/WebSocket) through `useSyncExternalStore` or an effect with a subscription |
| **policy** | a pure function in `domain/`; a variant dependent on configuration through context (`createContext`) |
| **specification / rules** | pure functions in `domain/`, used in form validation and in buttons' `disabled` |
| **repository / port** | a data module (`api/`) mapping DTO ↔ domain types; in Next.js the data access layer on the server (fw-nextjs) |
| **read model** | data from the query library's cache or a Server Component; views only read |
| **module** | a feature directory (`features/<name>/`) with a public `index.ts`; `domain/` without imports from `react` |

## Version-dependent
| Version | Changes relevant to this skill |
|---|---|
| 18 | `createRoot`, automatic batching of updates, `useTransition`, `useDeferredValue`, `useId`, `useSyncExternalStore`; Suspense with streaming SSR. 18.3 warns about APIs removed in 19 |
| 19.0 | Actions (asynchronous `startTransition`), `useActionState`, `useOptimistic`, `use`, `useFormStatus`, `<form action>`; **`ref` as a regular prop** (no `forwardRef`); `<Context>` as a provider; document metadata and stylesheets in components; the `'use client'`/`'use server'` directives stable. **Removed:** `propTypes`, `defaultProps` in function components, legacy context, string refs, `ReactDOM.render`/`hydrate`, `react-dom/test-utils` (`act` from `react`); `useRef` requires an argument in the types |
| 19.1 | Owner Stacks (`captureOwnerStack`, dev only) |
| 19.2 | `<Activity>`, `useEffectEvent`, `cacheSignal` (RSC), performance tracks in DevTools, partial prerendering in `react-dom` |
| 19.3 | `<ViewTransition>` and `addTransitionType` stable, `<Fragment ref>` stable, `use(browser())` for browser-only subtrees, Trusted Types integration, a dev warning on conditional `use()` |

Upgrade 18 → 19: first 18.3 (warnings), then `npx codemod@latest react/19/migration-recipe` and
`npx types-react-codemod@latest preset-19 ./src`. You bump dependencies only at the human's request (core-stack-sync).

**RSC security:** the `react-server-dom-*` packages 19.0–19.2.0 had a critical RCE vulnerability (CVE-2025-55182, December
2025), and later releases fixed DoS and source code exposure. An application with Server Components must have the latest patch
of its line (19.0.x / 19.1.x / 19.2.x); report it to the human if the version is older.

## Checklist
- [ ] the React version checked; the APIs used are available in that version
- [ ] no state computable from props/state and no effects "on state change"
- [ ] every effect synchronizes with something external and has a cleanup
- [ ] the `eslint-plugin-react-hooks` lint without disables; the compiler enabled or consciously skipped
- [ ] `domain/` without imports from `react`; rejections as action state
- [ ] Form: one schema with the server, the server always validates, 422 errors at the fields, `aria-invalid`/`aria-describedby`, focus on the first error

## Sources
- react.dev/reference/react, react.dev/learn (including "You Might Not Need an Effect", "Keeping Components Pure",
  "Choosing the State Structure"), react.dev/versions — accessed 2026-10-03
- react.dev/blog: React 19 Upgrade Guide (2024-04-25), React 19.2 (2025-10-01), React Compiler v1.0 (2025-10-07),
  React 19.3 (2026-09-09), RSC security notices (2025-12-03, 2025-12-11)
- the npm registry: `react` 19.3.0 (2026-09-09), `babel-plugin-react-compiler` 1.0.0, `eslint-plugin-react-hooks` 7.1.1
