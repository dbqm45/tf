# Code Splitting

> **Contents:** Metadata · TLDR · Notes (state in 2026, corrections to the source) · Problem · Solution · Code examples · Advantages · Disadvantages / tradeoffs · Related patterns · When to use / when NOT to use

Source: frontendpatterns.dev/code-splitting.

## Metadata

- **Category:** Performance
- **Level:** Advanced
- **Framework examples:** React, Vue, Svelte, Native web
- **Last updated:** 13 December 2025
- **Author:** Den Odell

## TLDR

"Split your bundle into chunks that load on demand, deferring code for routes and features until users actually need them."

## Notes (state in 2026, corrections to the source)

- **The Core Web Vitals are LCP, INP and CLS** (INP replaced FID in 2024; TTI is no longer a Lighthouse metric) — see
  fe-web-platform (`.claude/skills/fe-web-platform/references/core-web-vitals.md`). The list in "Advantages" has been corrected.
- Angular (fw-angular): `loadComponent`/`loadChildren` in routing and `@defer (on viewport | idle | interaction)` in
  templates — the declarative equivalent of `lazy()` + `Suspense`.
- Vite 8 builds with Rolldown: `build.rollupOptions.output.manualChunks` is deprecated in favour of Rolldown's chunk
  groups (`build.rolldownOptions.output.advancedChunks` / `codeSplitting`, depending on the version) — check
  the documentation of your version; before you split vendor code manually, measure (bundle analyzer).
- The `webpackPrefetch/Preload` magic comments work only in webpack/Rspack; in Vite prefetching is done through
  `<link rel="modulepreload">` or an import on hover/`requestIdleCallback`.
- Handle a failed chunk import after a deployment (old HTML → a deleted chunk) with an Error Boundary + a reload
  (e.g. the `vite:preloadError` event).
- The Svelte examples are Svelte 4 syntax (`export let`, `$:`, `on:click`, `<svelte:component>`); in Svelte 5: `$props()`,
  `$state`, `$derived`, `onclick`, you render a dynamic component directly (`<Comp />`).

## Problem

Applications send too much code at once. An example from the source: the home page takes 8
seconds to load, because it downloads the code of the admin panel, text editors and chart libraries that
the user will never use — a 2MB bundle, of which 100KB is really needed. The problem concerns
both the download time and the time the browser spends parsing JavaScript.

## Solution

A dynamic `import()` splits the code into logical parts — the bundler creates separate chunks loaded on
demand. The main split points: route boundaries, "heavy" components, feature
flags.

## Code examples

### Route-Based Splitting — React

```javascript
import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

const Dashboard = lazy(() => import('./pages/Dashboard'));
const Analytics = lazy(() => import('./pages/Analytics'));
const Settings = lazy(() => import('./pages/Settings'));

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<LoadingSpinner />}>
        <Routes>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
```

### Route-Based Splitting — Vue

```javascript
import { createRouter, createWebHistory } from 'vue-router';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/dashboard', component: () => import('./views/Dashboard.vue') },
    { path: '/analytics', component: () => import('./views/Analytics.vue') },
    { path: '/settings', component: () => import('./views/Settings.vue') }
  ]
});
```

### Route-Based Splitting — Svelte

```svelte
<script>
  let DashboardComponent;

  async function loadDashboard() {
    const module = await import('./Dashboard.svelte');
    DashboardComponent = module.default;
  }

  // $page comes from SvelteKit ($app/stores); in SvelteKit routing and per-route code splitting are built in
  $: if ($page.route.id === '/dashboard') loadDashboard();
</script>

{#if DashboardComponent}
  <svelte:component this={DashboardComponent} />
{:else}
  <LoadingSpinner />
{/if}
```

### Component-Level Splitting

```javascript
import { lazy, Suspense } from 'react';

const Chart = lazy(() => import('./components/Chart'));

function Dashboard({ showChart }) {
  return (
    <div>
      <h1>Dashboard</h1>
      {showChart && (
        <Suspense fallback={<ChartSkeleton />}>
          <Chart data={data} />
        </Suspense>
      )}
    </div>
  );
}
```

### Named Chunks and Prefetching (Webpack)

```javascript
const Dashboard = () => import(
  /* webpackChunkName: "dashboard" */
  /* webpackPrefetch: true */
  './pages/Dashboard'
);

const HeavyEditor = () => import(
  /* webpackChunkName: "editor" */
  /* webpackPreload: true */
  './components/RichTextEditor'
);
```

### Feature Flag Splitting

```javascript
async function loadFeature(featureName) {
  const features = {
    'advanced-analytics': './features/AdvancedAnalytics',
    'admin-panel': './features/AdminPanel'
  };

  if (features[featureName]) {
    const module = await import(features[featureName]);
    return module.default;
  }
  return null;
}
```

### Vendor Splitting Configuration — Webpack

```javascript
// webpack.config.js
module.exports = {
  optimization: {
    splitChunks: {
      cacheGroups: {
        vendor: { test: /[\\/]node_modules[\\/]/, name: 'vendor', chunks: 'all' },
        common: { minChunks: 2, name: 'common', chunks: 'all' }
      }
    }
  }
};
```

### Vendor Splitting Configuration — Vite

```javascript
// vite.config.js
export default {
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'charts': ['chart.js', 'd3']
        }
      }
    }
  }
};
```

### Error Handling and Preloading

```javascript
// Handle failed chunk loads gracefully
async function loadDashboard() {
  try {
    const module = await import('./pages/Dashboard');
    return module.default;
  } catch (error) {
    console.error('Failed to load dashboard:', error);
    return ErrorComponent;
  }
}

// Preload on hover to anticipate navigation
document.querySelector('#dashboard-link').addEventListener('mouseenter', () => {
  import('./pages/Dashboard');
});
```

## Advantages

- The initial bundle size shrinks drastically.
- Better time-to-interactive on all devices, especially mobile ones on slow connections.
- Unused features do not affect the size of other bundles.
- Vendor libraries are cached independently of the application code.
- Loading metrics improve (FCP, LCP; less main-thread work → better INP).

## Disadvantages / tradeoffs

- The first navigation to a given route "feels" slower than in a traditional SPA without splitting.
- Every split point requires its own loading UI.
- The build configuration becomes more complex.
- On HTTP/1.1 many small files hurt performance; HTTP/2 solves this.
- Difficult granularity: too many small chunks vs too few large ones.
- Dynamic imports return promises — failed network requests must be handled.
- A prefetching strategy requires a balance between wasted bandwidth and slow navigation.
- Shared dependencies can accidentally be duplicated without a correct bundler configuration.

## Related patterns

- [Lazy Loading](../performance/lazy-loading.md) — Performance.
- Code Splitting — web.dev.
- Dynamic `import()` — MDN.
- Webpack Code Splitting — the Webpack documentation.

## When to use / when NOT to use

Use it at real route boundaries and for features used by only some of the users
(the admin panel, a heavy editor, charts) — there the cost (a more complex build, loading UI) is
justified by a real gain in the initial bundle. Do **not** split code "just in case" for small,
always-used components — that is a pure example of breaking YAGNI from `../principles.md`:
the overhead (an extra request, its own loading state, the risk of a network error) exceeds the gain if the given
code always runs anyway. Check the bundle analyzer before you decide where the weight really is.
