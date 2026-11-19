# Lazy Loading

> **Contents:** Metadata · TLDR · Notes (state in 2026, corrections to the source) · Problem · Solution · Code examples · Advantages · Disadvantages / tradeoffs · Related patterns · When to use / when NOT to use

Source: frontendpatterns.dev/lazy-loading.

## Metadata

- **Category:** Performance
- **Level:** Advanced
- **Framework examples:** React, Vue, Svelte, Native web
- **Last updated:** 30 November 2025
- **Author:** Den Odell

## TLDR

"Defer loading of images, components, and data until they're needed, reducing initial load time and
saving bandwidth."

## Notes (state in 2026, corrections to the source)

- **Do not lazy-load the LCP image (hero, above the fold)** — `loading="lazy"` on it worsens LCP. For the hero:
  `fetchpriority="high"` (and possibly `<link rel="preload" as="image">`). The example below has been corrected.
- Core Web Vitals = LCP, INP, CLS (FCP is an auxiliary metric) — fe-web-platform (`.claude/skills/fe-web-platform/references/core-web-vitals.md`).
- Angular: `@defer` in the template and `loadComponent` in routing (fw-angular). Iframes also support `loading="lazy"`.
- A custom Intersection Observer for `<img>` is unnecessary — native `loading="lazy"` has full support.
- The Svelte examples are Svelte 4 syntax (`export let`, `$:`, `on:click`, `<svelte:component>`); in Svelte 5: `$props()`,
  `$state`, `$derived`, `onclick`, you render a dynamic component directly (`<Comp />`).

## Problem

Pages load resources before they are really needed. An example from the source: a landing page downloads
JavaScript for the admin panel, analytics, settings and 47 images below the fold, although the user wants
only the hero section — the author estimates that 80% of the JS bundle is code the user never touches.
Parsing on mobile devices takes 2–3× longer; images below the fold use bandwidth and memory
needlessly.

## Solution

"Don't load resources until users actually need them." For JavaScript: a dynamic `import()` to
split the bundle — route components loaded on navigation, heavy features (chart libraries)
deferred. For images: the `loading="lazy"` attribute or an Intersection Observer. For third-party scripts:
`async`/`defer` or loading after user interaction. Combine it with preloading on hover to
cancel out the perceived delay on navigation.

## Code examples

### Component Lazy Loading — React

```javascript
import { lazy, Suspense } from 'react';

const AdminPanel = lazy(() => import('./AdminPanel'));

function App() {
  return (
    <div>
      <Header />
      <MainContent />
      <Suspense fallback={<Loading />}>
        <AdminPanel />
      </Suspense>
    </div>
  );
}
```

### Component Lazy Loading — Vue

```vue
<template>
  <Suspense>
    <AsyncAdminPanel />
    <template #fallback>
      <Loading />
    </template>
  </Suspense>
</template>

<script>
import { defineAsyncComponent } from 'vue';

export default {
  components: {
    AsyncAdminPanel: defineAsyncComponent(() =>
      import('./AdminPanel.vue')
    )
  }
};
</script>
```

### Component Lazy Loading — Svelte

```svelte
<script>
  let AdminPanel;

  async function loadAdminPanel() {
    const module = await import('./AdminPanel.svelte');
    AdminPanel = module.default;
  }
</script>

<button on:click={loadAdminPanel}>Load Admin Panel</button>

{#if AdminPanel}
  <svelte:component this={AdminPanel} />
{/if}
```

### Component Lazy Loading — Web Components

```javascript
class LazyComponent extends HTMLElement {
  async connectedCallback() {
    this.innerHTML = '<div class="loading">Loading...</div>';
    const { AdminPanel } = await import('./admin-panel.js');
    this.innerHTML = '';
    this.appendChild(new AdminPanel());
  }
}

customElements.define('lazy-component', LazyComponent);
```

### Route-Based Code Splitting

```javascript
import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

const Home = lazy(() => import('./pages/Home'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Admin = lazy(() => import('./pages/Admin'));

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/admin" element={<Admin />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
```

### Conditional Feature Loading

```javascript
function Dashboard({ user }) {
  const [AnalyticsPanel, setAnalyticsPanel] = useState(null);

  useEffect(() => {
    if (user.isPremium) {
      import('./AnalyticsPanel').then(m => setAnalyticsPanel(() => m.default));
    }
  }, [user.isPremium]);

  return (
    <div>
      <h1>Dashboard</h1>
      {AnalyticsPanel && <AnalyticsPanel />}
    </div>
  );
}
```

### Image Lazy Loading — the native attribute

```html
<!-- Hero (LCP): NOT lazy — load eagerly with high priority -->
<img src="hero.jpg" alt="Hero" fetchpriority="high" width="800" height="600" />
<!-- Below the fold: lazy, with dimensions to avoid CLS -->
<img src="image1.jpg" loading="lazy" alt="Image 1" width="400" height="300" />
<img src="image2.jpg" loading="lazy" alt="Image 2" width="400" height="300" />
```

### Image Lazy Loading — Intersection Observer

```javascript
const observer = new IntersectionObserver((entries, obs) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.src = entry.target.dataset.src;
      obs.unobserve(entry.target);
    }
  });
});

document.querySelectorAll('img[data-src]').forEach(img => observer.observe(img));
// HTML: <img data-src="actual.jpg" alt="Lazy image" />
```

### Preloading on Hover

```javascript
function ProductCard({ product }) {
  return (
    <div onMouseEnter={() => import('./ProductDetails')}>
      <h3>{product.name}</h3>
      <Link to={`/product/${product.id}`}>View Details</Link>
    </div>
  );
}
```

### Lazy Third-Party Scripts

```html
<script src="analytics.js" defer></script>
<script src="chat-widget.js" async></script>

<script>
  function loadAnalytics() {
    const script = document.createElement('script');
    script.src = 'https://analytics.example.com/script.js';
    document.head.appendChild(script);
  }

  document.addEventListener('click', loadAnalytics, { once: true });
</script>
```

## Advantages

- A drastically smaller initial bundle — the user downloads only what is needed at the start.
- Time to interactive drops; the difference between 50KB and 500KB decides whether a mobile user
  gives up.
- Users without premium/admin access do not download code they will not use.
- Images below the fold load on demand, saving bandwidth.
- Loading metrics (FCP, LCP) improve; with image dimensions, CLS too.
- Cache efficiency improves — a change to a rarely used feature does not invalidate the cache of popular
  paths.

## Disadvantages / tradeoffs

- The first navigation to a lazily loaded route shows a spinner — it may seem slower than
  a traditional SPA without splitting.
- Every lazy loading boundary requires a loading state and a fallback UI.
- Error handling gets more complicated — network errors require retry and error boundaries.
- Debugging across chunks is harder (separate source maps, broken stack traces).
- Lazy images cause layout shifts if you do not set an explicit `width`/`height`.
- Without preloading a click "feels" slow — combine it with a prefetch on hover.
- Incorrect split boundaries can accidentally duplicate shared dependencies — check the
  bundle analyzer.
- Modals/drawers that the user expects immediately do not work well with lazy loading.

## Related patterns

- [Code Splitting](../performance/code-splitting.md) — Performance.
- Lazy Loading — web.dev.
- `React.lazy` — the React documentation.
- Async Components — the Vue documentation.
- Dynamic Imports — the Svelte documentation.

## When to use / when NOT to use

Use it for route components, images below the fold and features used only by some
users. Do **not** apply it to elements the user expects immediately (a modal opened
from the main action, a key widget above the fold) — a spinner in such a place spoils the impression more
than you gain on the initial bundle; this is an example where the "Performance" foundation and the "Resilience" foundation
(do not surprise the user with a loading state in an expected place) can come into conflict — decide
in favour of what the user will actually perceive as faster, not what is smaller in the bundle
analyzer.
