# Pure Component

> **Contents:** Metadata · TLDR · Notes (state in 2026, corrections to the source) · Problem · Solution · Code examples · Advantages · Disadvantages / tradeoffs · Related patterns · When to use / when NOT to use

Source: frontendpatterns.dev/pure-component.

## Metadata

- **Category:** Components
- **Level:** Beginner
- **Examples:** React, Vue, Svelte, Native web
- **Last updated:** September 26, 2025
- **Author:** Den Odell

## TLDR

"Build components that produce the same output for the same inputs with no side effects, enabling memoization and predictable testing."

## Notes (state in 2026, corrections to the source)

- **React Compiler** (stable since 2025, React 19) automatically memoizes components and values — in projects with
  the compiler, manual `React.memo`/`useCallback` are usually unnecessary; render purity is then a **condition** for
  correct compilation. Equivalents of pure computations: Vue `computed`, Svelte 5 `$derived`, Angular `computed()`
  + `OnPush`/zoneless (fw-angular).
- "Fetch in `useEffect`" is the minimum; a data layer/loader is better (resilience/async-boundary.md).
- The Web Components example corrected from `innerHTML` to `textContent`.
- The Vue examples are in the Options API (`data`, `mounted`) — in new code the Composition API (`<script setup>`).
- The Svelte examples are Svelte 4 syntax (`export let`, `$:`, `on:click`, `<slot>`); in Svelte 5: `$props()`, `$state`,
  `$derived`, `$effect`, `onclick` attributes, snippets instead of slots.

## Problem

Components rendering different results for identical props (reading the current time during render, reading global state, analytics calls during rendering). This makes memoization impossible, causes flaky tests and race conditions.

## Solution

Build pure component functions: identical props → identical output, zero side effects during render. Move side effects (fetch, subscriptions, analytics) to `useEffect` (or the framework's equivalent), not into the body of the render function.

## Code examples

### React

```javascript
const Greeting = React.memo(function Greeting({ name, title }) {
  return (
    <div>
      <h1>Hello, {name}!</h1>
      {title && <p>{title}</p>}
    </div>
  );
});
```

### Vue

```html
<template>
  <div>
    <h1>Hello, {{ name }}!</h1>
    <p>{{ greeting }}</p>
  </div>
</template>

<script>
export default {
  props: ['name'],
  computed: {
    greeting() {
      return `Welcome, ${this.name}!`;
    }
  }
};
</script>
```

### Svelte

```svelte
<script>
  export let firstName;
  export let lastName;

  $: fullName = `${firstName} ${lastName}`;
</script>

<div>
  <h1>{fullName}</h1>
</div>
```

### Web Components

```javascript
class PureGreeting extends HTMLElement {
  static get observedAttributes() { return ['name']; }

  attributeChangedCallback(name, oldValue, newValue) {
    if (newValue !== oldValue) this.render();
  }

  render() {
    const h1 = document.createElement('h1');
    h1.textContent = `Hello, ${this.getAttribute('name')}!`;
    this.replaceChildren(h1);
  }
}
customElements.define('pure-greeting', PureGreeting);
```

### Pure vs impure

**Impure (avoid) — reads external state during render:**

```javascript
function ImpureTimestamp({ prefix }) {
  const time = new Date().toLocaleTimeString();
  return <div>{prefix}: {time}</div>;
}
```

**Pure (prefer) — the time is a prop, the output is predictable:**

```javascript
function PureTimestamp({ prefix, time }) {
  return <div>{prefix}: {time}</div>;
}
```

### Non-mutating (immutable) updates

```javascript
const UserDisplay = React.memo(({ user }) => <div>{user.name}</div>);

// Mutation — the same reference, no re-render
user.name = 'Bob';
<UserDisplay user={user} />

// Immutable — a new reference, a re-render happens
const updated = { ...user, name: 'Bob' };
<UserDisplay user={updated} />
```

### Testing memoization

```javascript
test('memoized component skips re-render with same props', () => {
  const renderSpy = jest.fn();
  const MemoizedGreeting = React.memo(({ name }) => {
    renderSpy();
    return <div>{name}</div>;
  });

  const { rerender } = render(<MemoizedGreeting name="Alice" />);
  expect(renderSpy).toHaveBeenCalledTimes(1);

  rerender(<MemoizedGreeting name="Alice" />);
  expect(renderSpy).toHaveBeenCalledTimes(1); // Skipped

  rerender(<MemoizedGreeting name="Bob" />);
  expect(renderSpy).toHaveBeenCalledTimes(2); // Rendered
});
```

### Side effects in Effects, not in render

**Avoid — a synchronous fetch during render causes duplicated calls:**

```javascript
function BadProfile({ userId }) {
  const user = fetchUserSync(userId);
  return <div>{user.name}</div>;
}
```

**Prefer — fetch in `useEffect`, the render stays pure:**

```javascript
function GoodProfile({ userId }) {
  const [user, setUser] = useState(null);
  useEffect(() => { 
    fetchUser(userId).then(setUser); 
  }, [userId]);
  return user ? <div>{user.name}</div> : <div>Loading...</div>;
}
```

### Stable callback references

```javascript
function TodoList({ todos }) {
  const handleToggle = useCallback((id) => toggleTodo(id), []);

  return todos.map(todo => (
    <TodoItem key={todo.id} todo={todo} onToggle={handleToggle} />
  ));
}

const TodoItem = React.memo(({ todo, onToggle }) => (
  <li onClick={() => onToggle(todo.id)}>{todo.text}</li>
));
```

## Advantages

- Predictable behaviour — identical props always give identical output.
- Memoization really works — `React.memo` (and its equivalents) effectively skip unnecessary re-renders.
- Simple testing — only props on the input and an assertion on the output, without mocking effects.
- Better reusability — a component without external dependencies works everywhere.
- Timing bugs disappear — effects moved to `useEffect` give control over the moment of execution.
- Safe for concurrent rendering — React can render many times without duplicating side effects.

## Disadvantages / tradeoffs

- Side effects must leave the render body — fetch, subscriptions, analytics always go to `useEffect`/its equivalent.
- Memoization has its cost (comparison overhead) — for rapidly changing props the cost can exceed the benefit.
- Shallow comparison has limits — a change of `user.name` without changing the reference of the `user` object will not trigger a re-render.
- Callbacks passed as props need `useCallback` — inline functions create a new reference on every render, invalidating the child's memoization.
- Not everything can be pure — imperative APIs (e.g. focus, scroll) by nature have a side effect.
- Profile before optimizing — `React.memo` everywhere "just in case" adds unnecessary comparison overhead.

## Related patterns

- [Memoization](../performance/memoization.md) — Performance.
- `React.memo` — React docs.
- Computed Properties — Vue docs.
- Reactive Declarations — Svelte docs.
- Pure Functions — Wikipedia.

## When to use / when NOT to use

Keep components pure **by default** — this is not an optional optimization, it is the condition for memoization/concurrent rendering to make sense at all, and for tests to be deterministic.

Do not wrap every component in `React.memo` "just in case" without a measured performance problem — the cost of comparing props can be greater than the cost of the re-render itself for simple components; this is classic premature optimization (see YAGNI in `../principles.md`). First measure, then memoize where it really hurts.
