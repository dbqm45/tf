# Async Boundary

> **Contents:** Metadata · TLDR · Notes (state in 2026, corrections to the source) · Problem · Solution · Code examples · Advantages · Disadvantages / tradeoffs · Related patterns · When to use / when NOT to use

Source: frontendpatterns.dev/async-boundary.

## Metadata

- **Category:** Resilience
- **Level:** Advanced
- **Examples:** React, Vue, Svelte, Native web
- **Last updated:** 15 November 2025
- **Author:** Den Odell

## TLDR

"Wrap async operations in boundaries that handle loading and error states, keeping child components
focused on rendering data instead of managing request lifecycle."

## Notes (state in 2026, corrections to the source)

- **`use(fetchUser(userId))` without a cache is a bug**: every render creates a new promise, so Suspense suspends
  forever. The promise must come from a cache/data layer (TanStack Query `useSuspenseQuery`, a router
  loader, an RSC framework) or be created higher up and passed down. The example has been corrected.
- Boundary equivalents: React `<Suspense>`; Vue `<Suspense>` (still experimental); Svelte `{#await}` /
  `<svelte:boundary>`; Angular (fw-angular) `@defer` with `@placeholder`/`@loading`/`@error` and `resource`/
  `httpResource` with a status.
- Instead of a manual "delayed fallback" in React use transitions (`startTransition`) — during navigation the already visible
  content stays, instead of flashing a fallback.
- The Svelte examples are Svelte 4 syntax; in Svelte 5: `$props()`, `$state`, `onclick`, `<svelte:boundary>` (a boundary for errors
  and — with `await` in components — for loading).

## Problem

Without coordination, independent components on one screen (e.g. a dashboard) show unsynchronized
loading states — "one widget shows a skeleton, another shows a spinner, a third just sits there
empty" — which looks sloppy (jank). Alternatively, one global spinner blocks the whole page,
not letting the user read content that is already ready.

## Solution

Wrap related components in a boundary that coordinates their loading states: "think of it like a stage
curtain: you don't reveal the set piece by piece, you wait until everything's ready and show it all
at once". Nesting boundaries enables progressive loading — critical content appears
first, less important content follows later.

## Code examples

### React — Basic Async Boundary

```javascript
import { Suspense } from 'react';

function App() {
  return (
    <Suspense fallback={<Spinner />}>
      <UserProfile userId={userId} />
    </Suspense>
  );
}

function UserProfile({ userId }) {
  // React 19+ use(): the promise MUST be cached (same promise across renders),
  // e.g. from a data layer — a fresh fetch() per render suspends forever.
  const user = use(getUserCached(userId));
  return (
    <div>
      <h1>{user.name}</h1>
      <p>{user.bio}</p>
    </div>
  );
}
```

### Vue — Basic Async Boundary

```vue
<template>
  <Suspense>
    <template #default>
      <UserProfile :userId="userId" />
    </template>
    <template #fallback>
      <Spinner />
    </template>
  </Suspense>
</template>

<script setup>
import { defineAsyncComponent } from 'vue';
const props = defineProps(['userId']);
const UserProfile = defineAsyncComponent(() => import('./UserProfile.vue'));
</script>
```

### Svelte — Basic Async Boundary

```svelte
<script>
  export let userId;
  let userPromise = fetch(`/api/users/${userId}`).then(r => r.json());
</script>

{#await userPromise}
  <Spinner />
{:then user}
  <div class="profile">
    <h1>{user.name}</h1>
    <p>{user.bio}</p>
  </div>
{:catch error}
  <ErrorMessage message={error.message} />
{/await}
```

### Web Components — Basic Async Boundary

```javascript
class AsyncBoundary extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
  }

  async connectedCallback() {
    this.shadowRoot.innerHTML = '<slot name="fallback"></slot>';
    try {
      const userId = this.getAttribute('user-id');
      const { UserProfile } = await import('./user-profile.js');
      const el = document.createElement('user-profile');
      el.setAttribute('user-id', userId);
      this.shadowRoot.innerHTML = '';
      this.shadowRoot.appendChild(el);
    } catch (error) {
      this.shadowRoot.innerHTML = '<slot name="error"></slot>';
    }
  }
}
customElements.define('async-boundary', AsyncBoundary);
```

### Nested Boundaries for Progressive Loading

```javascript
function Dashboard() {
  return (
    <div className="dashboard">
      <Suspense fallback={<MainContentSkeleton />}>
        <MainContent />
      </Suspense>
      <Suspense fallback={<SidebarSkeleton />}>
        <Sidebar />
      </Suspense>
      <Suspense fallback={<ActivitySkeleton />}>
        <ActivityFeed />
      </Suspense>
    </div>
  );
}
```

### Multiple Async Dependencies

```javascript
// All three must load before the boundary resolves
function ProductPage({ productId }) {
  return (
    <Suspense fallback={<PageSkeleton />}>
      <ProductDetails productId={productId} />
      <ProductReviews productId={productId} />
      <RelatedProducts productId={productId} />
    </Suspense>
  );
}
```

### Streaming with Server Components

```javascript
// Next.js App Router - static content renders immediately, async streams in
export default function Page() {
  return (
    <div>
      <Header />
      <Suspense fallback={<ProductGridSkeleton />}>
        <ProductGrid />
      </Suspense>
      <Footer />
    </div>
  );
}
```

### Delayed Fallback

```javascript
// Avoid spinner flash for fast loads by delaying 200ms
function PageWithTimeout() {
  const [showFallback, setShowFallback] = useState(false);
  useEffect(() => {
    const timer = setTimeout(() => setShowFallback(true), 200);
    return () => clearTimeout(timer);
  }, []);

  return (
    <Suspense fallback={showFallback ? <Spinner /> : null}>
      <SlowComponent />
    </Suspense>
  );
}
```

## Advantages

- The UI loads in coherent chunks instead of flickering — "entire sections appear together, which feels
  polished".
- Loading states are predictable; the user knows what is loading.
- Child components do not manage their own loading state — this responsibility lives at the boundary.
- Progressive loading (the most important content first) becomes a natural effect of nesting
  boundaries, not extra logic.

## Disadvantages / tradeoffs

- Requires framework support (React Suspense, Vue Suspense, Svelte `{#await}`) — it cannot be
  done purely by hand without platform support.
- One slow child blocks the **whole** boundary — if one of three widgets waits long, all
  three wait.
- Placing boundaries is hard: too few → coarse, infrequent loading; too many → spinners
  everywhere.
- Not every data fetch works with boundaries — `useEffect` + `fetch` does not trigger Suspense
  by itself, it requires integration.
- No built-in timeout — a child that never resolves waits forever.
- Error handling requires extra work — combining it with an Error Boundary (see
  `../resilience/error-boundary.md`).

## Related patterns

- [Error Boundary](../resilience/error-boundary.md) — Resilience
- [Loading State](../resilience/loading-state.md) — Resilience
- [Lazy Loading](../performance/lazy-loading.md) — Performance
- [Suspense (React)](https://react.dev/reference/react/Suspense)
- [Suspense (Vue)](https://vuejs.org/guide/built-ins/suspense.html)
- [Await Blocks (Svelte)](https://svelte.dev/docs/logic-blocks#await)
- [Streaming and Suspense (Next.js)](https://nextjs.org/docs/app/building-your-application/routing/loading-ui-and-streaming)

## When to use / when NOT to use

Use it when you have **several independent asynchronous operations rendering in the same
area of the screen** and you want them to appear as a coherent group, not a flickering, unsynchronized
set of spinners. This is not a pattern to introduce "everywhere there is a `fetch()`" — if you have
one self-contained component with its own loading state, a simpler local `loading`/`error` (see
`loading-state.md`) does the job without the overhead of Suspense/the framework. Reach for it specifically when
the problem is **coordinating many** loading states at once, not a single `fetch`.
