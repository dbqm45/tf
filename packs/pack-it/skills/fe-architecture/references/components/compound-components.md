# Compound Components

Source: the former `fe-architecture/references/patterns.md` (the repo's own pattern), extended with equivalents
in other frameworks.

## TLDR

Instead of one component with dozens of configuration props — a family of components that together form
a whole and share state implicitly (context / DI), and the user assembles them like native HTML (`<select>` + `<option>`).

## Problem

`<Tabs items={[...]} renderTab={...} renderPanel={...} tabClassName="..." showIcons />` — every new use
case adds a prop; the API grows combinatorially, and a layout (e.g. an icon between tabs) is impossible without
yet another prop.

## Solution

```tsx
<Tabs defaultValue="a">
  <Tabs.List>
    <Tabs.Trigger value="a">A</Tabs.Trigger>
    <Tabs.Trigger value="b">B</Tabs.Trigger>
  </Tabs.List>
  <Tabs.Panel value="a">…</Tabs.Panel>
  <Tabs.Panel value="b">…</Tabs.Panel>
</Tabs>
```

The state (the active tab) lives in the root and is shared with the parts internally:

| Framework | Sharing mechanism | Assembling the parts |
|---|---|---|
| React | `createContext` + `use(Context)` (React 19) / `useContext` | `children` |
| Vue | `provide` / `inject` | slots |
| Svelte 5 | `setContext` / `getContext` | snippets (`{@render children()}`) |
| Angular (fw-angular) | a service injected into the parent component (`providers`) or `inject(ParentComponent)` | content projection (`<ng-content select>`), `contentChildren()` |
| Web Components | events + finding an ancestor (`closest`) or the Context Protocol | `<slot>` |

## Rules

- A part used outside its parent should throw a readable error ("`Tabs.Trigger` must be inside `Tabs`").
- Support both controlled and uncontrolled mode (`value` + `onValueChange` vs `defaultValue`).
- Semantics and keyboard handling belong to the library of parts: the `tablist`/`tab`/`tabpanel` roles, roving tabindex, arrows
  (fe-web-platform, `.claude/skills/fe-web-platform/references/accessibility/keyboard-navigation.md`). Consider ready headless primitives
  (Radix, React Aria, Angular Aria/CDK, Ark UI) instead of writing from scratch.

## When to use / when NOT to

Use it when a component has **several parts configured by the user** (tabs, accordion, menu, select,
a dialog with a header/footer). Do not use it for a simple component with 2–3 props — a context and several exports are
overhead without gain (YAGNI — eng-design-principles).

## Related

- [Props and Attributes](props-and-attributes.md) — when there are too many props.
- [Presentational vs. Container](presentational-vs-container.md).
