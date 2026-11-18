# Component Lifecycle

> **Contents:** Metadata · TLDR · Notes (state in 2026, corrections to the source) · Problem · Solution · Code examples · Advantages · Disadvantages / tradeoffs · Related patterns · When to use / when NOT to use

Source: frontendpatterns.dev/component-lifecycle.

## Metadata

- **Category:** Components
- **Level:** Beginner
- **Examples:** React, Vue, Svelte, Native web
- **Last updated:** September 26, 2025
- **Author:** Den Odell

## TLDR

"Hook into mount, update, and unmount phases to fetch data, sync with external systems, and clean up resources without causing leaks or stale state."

## Notes (state in 2026, corrections to the source)

- The principle is agnostic: **every resource opened on mount has a symmetrical close**. Equivalents: React
  `useEffect` + cleanup; Vue `onMounted`/`onUnmounted` or `watch(..., { onCleanup })`/`onWatcherCleanup`; Svelte 5
  `$effect` returning a cleanup; Angular (fw-angular) `DestroyRef.onDestroy`, `takeUntilDestroyed()`, `effect(onCleanup => …)`;
  Web Components `connectedCallback`/`disconnectedCallback`.
- Many "manual" data-fetching effects are replaced today by data layers (TanStack Query, router loaders,
  Angular `httpResource`) — the effect remains for synchronizing with external systems (subscriptions, DOM, timers).
- React in StrictMode (dev) deliberately mounts an effect twice — a missing cleanup shows up immediately then.
- Encode parameters in queries: `` `/api/search?q=${encodeURIComponent(query)}` `` (corrected below).
- The Web Components example corrected from `innerHTML` to `textContent`.
- The Svelte examples are Svelte 4 syntax (`export let`, `$:`, `on:click`, `<slot>`); in Svelte 5: `$props()`, `$state`,
  `$derived`, `$effect`, `onclick` attributes, snippets instead of slots.

## Problem

Memory leaks in frontend applications: event listeners never removed, subscriptions not closed, timers running for components already removed. An example from the site: navigating through 50 pages of an application creates 500 "orphaned" event listeners, because every mount added a new one and no unmount removed it.

## Solution

Every opened resource needs closing, every listener — removal, every timer — clearing at the right moment of the component's lifecycle. On mount: set up listeners, start subscriptions, fetch data, initialize resources. On unmount: reverse all of it, symmetrically. Modern frameworks provide ready hooks for this: React `useEffect` with a cleanup function (return), Vue `onMounted`/`onUnmounted`, Svelte `onMount`/`onDestroy`.

## Code examples

### React — Basic Lifecycle with Cleanup

```javascript
import { useEffect, useState } from 'react';

function DataSubscriber({ userId }) {
  const [data, setData] = useState(null);

  useEffect(() => {
    const subscription = dataSource.subscribe(userId, setData);

    // Cleanup runs on unmount or before re-running effect
    return () => subscription.unsubscribe();
  }, [userId]);

  return <div>{data ? data.name : 'Loading...'}</div>;
}
```

### Vue

```javascript
<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue';

const props = defineProps(['userId']);
const data = ref(null);
let subscription = null;

onMounted(() => {
  subscription = dataSource.subscribe(props.userId, newData => {
    data.value = newData;
  });
});

onUnmounted(() => {
  if (subscription) subscription.unsubscribe();
});

watch(() => props.userId, (newId) => {
  if (subscription) subscription.unsubscribe();
  subscription = dataSource.subscribe(newId, newData => {
    data.value = newData;
  });
});
</script>
```

### Svelte

```javascript
<script>
  import { onMount } from 'svelte';

  export let userId;
  let subscription;
  let data;

  onMount(() => {
    subscription = dataSource.subscribe(userId, newData => {
      data = newData;
    });
    // Return cleanup function
    return () => subscription.unsubscribe();
  });

  // React to prop changes
  $: if (userId) {
    if (subscription) subscription.unsubscribe();
    subscription = dataSource.subscribe(userId, newData => {
      data = newData;
    });
  }
</script>
```

### Web Components

```javascript
class DataSubscriber extends HTMLElement {
  constructor() {
    super();
    this.subscription = null;
    this.attachShadow({ mode: 'open' });
  }

  connectedCallback() {
    const userId = this.getAttribute('user-id');
    this.subscription = dataSource.subscribe(userId, data => this.render(data));
  }

  disconnectedCallback() {
    if (this.subscription) this.subscription.unsubscribe();
  }

  static get observedAttributes() { return ['user-id']; }

  attributeChangedCallback(name, oldValue, newValue) {
    if (name === 'user-id' && oldValue !== newValue) {
      if (this.subscription) this.subscription.unsubscribe();
      this.subscription = dataSource.subscribe(newValue, data => this.render(data));
    }
  }

  render(data) {
    const div = document.createElement('div');
    div.textContent = data.name; // never interpolate data into innerHTML
    this.shadowRoot.replaceChildren(div);
  }
}

customElements.define('data-subscriber', DataSubscriber);
```

### Handling Multiple Lifecycle Concerns

```javascript
function UserProfile({ userId }) {
  const [user, setUser] = useState(null);

  useEffect(() => {
    const subscription = dataSource.subscribe(userId, setUser);
    const interval = setInterval(() => console.log('Polling'), 5000);
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      subscription.unsubscribe();
      clearInterval(interval);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [userId]);

  return <div>{user?.name}</div>;
}
```

### Preventing Race Conditions with Abort Controllers

```javascript
function SearchResults({ query }) {
  const [results, setResults] = useState([]);

  useEffect(() => {
    const controller = new AbortController();

    fetch(`/api/search?q=${encodeURIComponent(query)}`, { signal: controller.signal })
      .then(res => res.json())
      .then(setResults)
      .catch(err => {
        if (err.name !== 'AbortError') console.error(err);
      });

    return () => controller.abort();
  }, [query]);

  return <ul>{results.map(r => <li key={r.id}>{r.title}</li>)}</ul>;
}
```

### Conditional Effects

```javascript
function ConditionalEffect({ shouldSubscribe, userId }) {
  useEffect(() => {
    if (!shouldSubscribe) return;

    const subscription = dataSource.subscribe(userId, setData);
    return () => subscription.unsubscribe();
  }, [shouldSubscribe, userId]);

  return <div>{/* ... */}</div>;
}
```

## Advantages

- Memory leaks stop with proper cleanup — the application works without degradation during long navigation.
- Race conditions disappear when stale requests are aborted on a dependency change (see `AbortController`).
- Predictable behaviour — effects run at precisely defined points of the lifecycle.
- External resources (WebSocket, intervals, listeners) are managed symmetrically: opened on mount, closed on unmount.
- The reaction to a props change is explicit: a change of `userId` = unsubscribing from the old data and subscribing to the new.
- Easier debugging — effects centralized in lifecycle hooks, not scattered randomly across the component.

## Disadvantages / tradeoffs

- Forgetting the cleanup function is easy; the resulting memory leaks are subtle and hard to diagnose.
- Dependency arrays in React can be tricky — mistakes lead to closures with stale values or to infinite loops.
- A component with five or more effects becomes hard to understand and maintain.
- `useEffect` in React runs asynchronously, after the browser paints — for synchronous timing before paint you need the less common `useLayoutEffect`.
- The cleanup function must be synchronous — you cannot return a `Promise`; asynchronous cleanup requires a different approach.
- Frameworks differ in timing semantics (React: async after paint; Vue: sync) — you cannot transfer intuitions 1:1 between them.
- Testing lifecycle behaviour requires careful setup/teardown — an effect from one test can "leak" into another.

## Related patterns

- [Async Boundary](../resilience/async-boundary.md) — Resilience.
- `useEffect` — React docs.
- Lifecycle Hooks — Vue docs.
- Lifecycle — Svelte docs.
- Custom Elements Lifecycle — MDN.

## When to use / when NOT to use

Use deliberate lifecycle management whenever a component opens **any** external resource (subscription, timer, listener, network request) — this is not an optimization "for large applications", it is a basic condition for an SPA not to degrade over the course of navigation (in line with the "Resilience by Design" foundation, `../principles.md`).

Do not complicate it where there is no resource to close — a purely presentational component without effects does not need a `useEffect` "just in case"; that would be adding boilerplate without any real gain (YAGNI). If a component accumulates 5+ independent effects, consider splitting it into smaller, more specialized components/hooks, instead of coordinating everything in one place.
