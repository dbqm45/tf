# Memoization

> **Contents:** Metadata · TLDR · Notes (state in 2026, corrections to the source) · Problem · Solution · Code examples · Advantages · Disadvantages / tradeoffs · Related patterns · When to use / when NOT to use

Source: frontendpatterns.dev/memoization.

## Metadata

- **Category:** Performance
- **Level:** Advanced
- **Framework examples:** React, Vue, Svelte, Native web
- **Last updated:** 29 November 2025
- **Author:** Den Odell

## TLDR

"Cache expensive computation results so repeated calls with identical inputs return instantly
instead of recalculating."

## Notes (state in 2026, corrections to the source)

- **React Compiler** (stable, React 19) inserts memoization automatically — manual `useMemo`/`useCallback`/`React.memo`
  remain for cases the compiler does not cover, and for libraries that require stable references.
- Equivalents: Vue `computed`, Svelte 5 `$derived`, Angular `computed()` (memoized, lazily recomputed — fw-angular).
- `memoize` with a `JSON.stringify(args)` key is expensive for large arrays and does not limit memory — for object
  data use a `WeakMap` by reference or an LRU (example below).
- The Svelte examples are Svelte 4 syntax (`export let`, `$:`, `on:click`, `<svelte:component>`); in Svelte 5: `$props()`,
  `$state`, `$derived`, `onclick`, you render a dynamic component directly (`<Comp />`).

## Problem

Components filtering large data sets (e.g. 10,000 products) recompute the result on every
render of the parent, even though the data has not changed — the author observed a simple `sort` that ran
47 times during a single user interaction. A separate variant of the same problem: inline callbacks
create a new function reference on every render, triggering unnecessary re-renders
of memoized child components.

## Solution

"Cache the results of expensive computations so that when inputs haven't changed, you return the
cached value instead of recalculating." In React: `useMemo` for values, `useCallback` for functions.
Vue caches computed properties automatically. Svelte does it through reactive statements (`$:`).
The author explicitly warns: "avoid memoizing everything — the overhead of memoization can exceed
the cost of recomputing cheap operations".

## Code examples

### Basic Memoization — React

```javascript
function ProductList({ products, category, sortBy }) {
  // Only recomputes when products or category change
  const filteredProducts = useMemo(() => {
    return products.filter(p => p.category === category);
  }, [products, category]);

  // Chain memoizations for multi-step transformations
  const sortedProducts = useMemo(() => {
    return [...filteredProducts].sort((a, b) =>
      a[sortBy] > b[sortBy] ? 1 : -1
    );
  }, [filteredProducts, sortBy]);

  return (
    <ul>
      {sortedProducts.map(p => <li key={p.id}>{p.name}</li>)}
    </ul>
  );
}
```

### Basic Memoization — Vue

```vue
<script setup>
import { computed } from 'vue';

const props = defineProps(['products', 'category']);

// computed() automatically memoizes
const filteredProducts = computed(() => {
  return props.products.filter(p => p.category === props.category);
});

const sortedProducts = computed(() => {
  return [...filteredProducts.value].sort((a, b) => a.name.localeCompare(b.name));
});
</script>

<template>
  <ul>
    <li v-for="product in sortedProducts" :key="product.id">
      {{ product.name }}
    </li>
  </ul>
</template>
```

### Basic Memoization — Svelte

```svelte
<script>
  export let products;
  export let category;
  export let sortBy;

  // Reactive statements are automatically memoized
  $: filteredProducts = products.filter(p => p.category === category);
  $: sortedProducts = [...filteredProducts].sort((a, b) =>
    a[sortBy] > b[sortBy] ? 1 : -1
  );
</script>

<ul>
  {#each sortedProducts as product (product.id)}
    <li>{product.name}</li>
  {/each}
</ul>
```

### Basic Memoization — Vanilla JS

```javascript
function memoize(fn) {
  const cache = new Map();

  return function(...args) {
    const key = JSON.stringify(args);
    if (cache.has(key)) return cache.get(key);

    const result = fn(...args);
    cache.set(key, result);
    return result;
  };
}

// Wrap expensive function
const filterProducts = memoize((products, category) => {
  return products.filter(p => p.category === category);
});

filterProducts(products, 'electronics'); // Computes and caches
filterProducts(products, 'electronics'); // Returns cached result
```

### Callback Memoization

```javascript
function TodoList({ todos, onToggle }) {
  // Stable reference prevents child re-renders
  const handleToggle = useCallback((id) => {
    onToggle(id);
  }, [onToggle]);

  return (
    <ul>
      {todos.map(todo => (
        <TodoItem key={todo.id} todo={todo} onToggle={handleToggle} />
      ))}
    </ul>
  );
}

// React.memo skips re-render if props unchanged
const TodoItem = React.memo(({ todo, onToggle }) => (
  <li onClick={() => onToggle(todo.id)}>{todo.text}</li>
));
```

### Component Memoization

```javascript
// Wrap component to prevent re-renders when props unchanged
const ExpensiveComponent = React.memo(({ data }) => {
  const processedData = data.map(item => ({
    ...item,
    computed: expensiveCalculation(item)
  }));

  return processedData.map(item => <div key={item.id}>{item.computed}</div>);
});

// Custom comparison for complex props
const CustomCompare = React.memo(
  ({ data, config }) => { /* ... */ },
  (prev, next) => prev.data.length === next.data.length && prev.config.id === next.config.id
);
```

### LRU Cache for Limited Memory

```javascript
class LRUCache {
  constructor(maxSize = 100) {
    this.cache = new Map();
    this.maxSize = maxSize;
  }

  get(key) {
    if (!this.cache.has(key)) return undefined;
    const value = this.cache.get(key);
    this.cache.delete(key);
    this.cache.set(key, value); // Move to end (most recent)
    return value;
  }

  set(key, value) {
    if (this.cache.has(key)) this.cache.delete(key);
    this.cache.set(key, value);
    if (this.cache.size > this.maxSize) {
      this.cache.delete(this.cache.keys().next().value); // Evict oldest
    }
  }
}
```

### Selector Pattern

```javascript
import { createSelector } from 'reselect';

const getProducts = state => state.products;
const getCategory = state => state.category;

// Memoized selector - only recomputes when inputs change
const getFilteredProducts = createSelector(
  [getProducts, getCategory],
  (products, category) => products.filter(p => p.category === category)
);

// Chained selectors
const getSortedProducts = createSelector(
  [getFilteredProducts, state => state.sortBy],
  (filtered, sortBy) => [...filtered].sort((a, b) => a[sortBy] > b[sortBy] ? 1 : -1)
);
```

### Fibonacci with Memoization

```javascript
// Exponential time -> linear time
const fibonacci = (() => {
  const cache = {};
  return function fib(n) {
    if (n in cache) return cache[n];
    if (n <= 1) return n;
    return cache[n] = fib(n - 1) + fib(n - 2);
  };
})();

fibonacci(50); // Instant with memoization
```

## Advantages

- Expensive operations run only when the data really changes.
- The visible delay in search fields and scroll interactions disappears.
- Stable callback references prevent cascading re-renders.
- Complex derived state becomes practical to maintain.
- Lower CPU usage, better behaviour on mobile devices.

## Disadvantages / tradeoffs

- Memoization trades memory for CPU time — it is not free.
- For cheap operations the overhead of memoization itself can worsen performance.
- Dependency arrays in React (`useMemo`/`useCallback`) are easy to get wrong.
- Shallow comparison has limitations — it does not detect changes nested in an object.
- Debugging memoized code is harder — breakpoints hit only sometimes.
- Custom comparison functions in `React.memo` are error-prone.
- It is easy to over-memoize "just in case".
- Only pure functions (without side effects) should be memoized.

## Related patterns

- [Pure Component](../components/pure-component.md) — Components.
- Memoization — Wikipedia.
- `React.memo` and `useMemo` — the React documentation.
- Computed Properties — the Vue documentation.
- Reactive Statements — the Svelte documentation.

## When to use / when NOT to use

Use it for computationally heavy operations called often with the same arguments — but
**measure/profile first** to confirm a real performance problem before you add memoization.
This is a literal illustration of YAGNI from `../principles.md`: memoization "just in case" for cheap
operations is pure overhead without gain — it adds complexity (dependency arrays, the risk of a wrong
comparison) in a place where the performance problem never existed.
