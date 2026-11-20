# Debounce

> **Contents:** Metadata · TLDR · Notes (state in 2026, corrections to the source) · Problem · Solution · Code examples · Advantages · Disadvantages / tradeoffs · Related patterns · When to use / when NOT to use

Source: frontendpatterns.dev/debounce.

## Metadata

- **Category:** Performance
- **Level:** Intermediate
- **Framework examples:** React, Vue, Svelte, Native web
- **Last updated:** 19 December 2025
- **Author:** Den Odell

## TLDR

"Wait until the input settles before you react. Make API calls, validations or
expensive computations once, after typing stops, instead of on every keystroke."

## Notes (state in 2026, corrections to the source)

- Debounce does not remove races — when the query changes, **cancel the previous request** (`AbortController`) and encode
  the parameters (`encodeURIComponent`). The React example has been corrected.
- Ready-made equivalents: Angular `debounced()` on signals / `debounceTime` in RxJS (fw-angular); React 19
  `useDeferredValue` for an expensive render (this is not a network debounce, only render priority); Vue `watchDebounced`
  (VueUse).
- For `resize` a `ResizeObserver` on a specific element is often better than a debounce on `window`.
- The Web Components example inserted results through `innerHTML` (XSS) — use `textContent`/the DOM API.
- The Svelte examples are Svelte 4 syntax (`export let`, `$:`, `on:click`, `<svelte:component>`); in Svelte 5: `$props()`,
  `$state`, `$derived`, `onclick`, you render a dynamic component directly (`<Comp />`).

## Problem

Rapid events (e.g. typing into a search field) generate unnecessary API requests — typing
"javascript" sends seven separate requests, one per letter. This wastes bandwidth, overloads the server and
causes race conditions when responses come back in the wrong order. The same problem affects
`resize` handlers (60+ computations/s) and form validation (errors shown before the user has finished
typing).

## Solution

Debouncing delays the execution of a function until a quiet period without new events has passed — the
`clearTimeout(timeoutId); timeoutId = setTimeout(fn, delay);` pattern cancels the pending execution and schedules
a new one. Delay ranges: 150–200ms for a responsive autocomplete, 300–500ms for expensive API
calls.

**When debounce is the wrong choice:** when you need periodic updates during continuous
activity (e.g. a scroll-spy highlighting the active section) — a debounced handler gives no feedback
while scrolling. The solution in such a case: **throttle** (execution at regular
intervals, e.g. every 100ms), not debounce.

## Code examples

### React

```javascript
import { useState, useEffect } from 'react';

function useDebouncedValue(value, delay = 300) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timeoutId = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timeoutId);
  }, [value, delay]);

  return debouncedValue;
}

function SearchInput() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const debouncedQuery = useDebouncedValue(query, 300);

  useEffect(() => {
    if (!debouncedQuery) return;
    const controller = new AbortController();
    fetch(`/api/search?q=${encodeURIComponent(debouncedQuery)}`, { signal: controller.signal })
      .then(res => res.json())
      .then(setResults)
      .catch(err => { if (err.name !== 'AbortError') throw err; });
    return () => controller.abort(); // stale responses never land
  }, [debouncedQuery]);

  return (
    <div>
      <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search..." />
      <ul>{results.map(item => <li key={item.id}>{item.name}</li>)}</ul>
    </div>
  );
}
```

### Vue

```javascript
<script setup>
import { ref, onBeforeUnmount } from 'vue';

const query = ref('');
const results = ref([]);
let timeoutId = null;

function handleInput(event) {
  query.value = event.target.value;
  clearTimeout(timeoutId);
  timeoutId = setTimeout(async () => {
    const response = await fetch(`/api/search?q=${query.value}`);
    results.value = await response.json();
  }, 300);
}

onBeforeUnmount(() => clearTimeout(timeoutId));
</script>

<template>
  <div>
    <input :value="query" @input="handleInput" placeholder="Search..." />
    <ul><li v-for="item in results" :key="item.id">{{ item.name }}</li></ul>
  </div>
</template>
```

### Svelte

```javascript
<script>
  import { onDestroy } from 'svelte';

  let query = '';
  let results = [];
  let timeoutId;

  function handleInput(event) {
    query = event.target.value;
    clearTimeout(timeoutId);
    timeoutId = setTimeout(async () => {
      const response = await fetch(`/api/search?q=${query}`);
      results = await response.json();
    }, 300);
  }

  onDestroy(() => clearTimeout(timeoutId));
</script>

<div>
  <input value={query} on:input={handleInput} placeholder="Search..." />
  <ul>{#each results as item}<li>{item.name}</li>{/each}</ul>
</div>
```

### Web Components

```javascript
function debounce(fn, delay) {
  let timeoutId;
  return function(...args) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn.apply(this, args), delay);
  };
}

class SearchInput extends HTMLElement {
  connectedCallback() {
    this.innerHTML = `<input type="text" placeholder="Search..." /><ul class="results"></ul>`;
    const input = this.querySelector('input');
    const resultsList = this.querySelector('.results');

    const debouncedSearch = debounce(async (query) => {
      const response = await fetch(`/api/search?q=${query}`);
      const results = await response.json();
      resultsList.replaceChildren(...results.map(item => {
        const li = document.createElement('li');
        li.textContent = item.name;
        return li;
      }));
    }, 300);

    input.addEventListener('input', (e) => debouncedSearch(e.target.value));
  }
}

customElements.define('search-input', SearchInput);
```

### Debounce with Loading State

```javascript
function SearchInput() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const debouncedQuery = useDebouncedValue(query, 300);

  useEffect(() => {
    if (!debouncedQuery) return;
    setIsSearching(true);
    fetch(`/api/search?q=${debouncedQuery}`)
      .then(res => res.json())
      .then(data => { setResults(data); setIsSearching(false); });
  }, [debouncedQuery]);

  return (
    <div>
      <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search..." />
      {isSearching && <span>Searching...</span>}
      <ul>{results.map(item => <li key={item.id}>{item.name}</li>)}</ul>
    </div>
  );
}
```

### Debounced Window Resize Handler

```javascript
const debouncedResize = debounce(() => {
  recalculateLayout();
  updateResponsiveElements();
}, 150);

window.addEventListener('resize', debouncedResize);
window.removeEventListener('resize', debouncedResize); // cleanup
```

## Advantages

- A search field sends one request after typing stops, instead of one per letter.
- Expensive `resize` handlers run once after the gesture ends, not dozens of times per second.
- Race conditions with responses arriving out of order become rare.
- Form validation waits until the user pauses before it shows an error.
- Battery life on mobile devices improves.
- The implementation is a few lines around `setTimeout`/`clearTimeout` — no dependencies.

## Disadvantages / tradeoffs

- The delay is always present, regardless of how fast the operation is.
- Choosing the delay requires a balance between responsiveness and efficiency.
- Timer management is easy to break — forgetting `clearTimeout` on unmount causes a memory leak.
- Slow users (pauses longer than the delay) can trigger many requests despite the debounce.
- Without a "searching…" indicator, the delay can look like the UI not responding.
- Debounce is **not** a rate limiter — continuous typing without pauses will never trigger the function.

## Related patterns

- [Code Splitting](../performance/code-splitting.md) — Performance.
- [Lazy Loading](../performance/lazy-loading.md) — Performance.
- [Memoization](../performance/memoization.md) — Performance.
- Debouncing and Throttling Explained — CSS-Tricks.
- Debounce — the Lodash documentation.
- `setTimeout()` — MDN.

## When to use / when NOT to use

Use it for events where what counts is **the final result after activity stops** — a search field,
form validation, `resize`. Do **not** use it when feedback is needed **during** continuous
activity (scroll-spy) — there the correct pattern is throttle, not debounce; using the wrong one of these
two is a common, concrete mistake, not a subtle trade-off.
