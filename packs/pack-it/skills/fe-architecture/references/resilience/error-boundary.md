# Error Boundary

> **Contents:** Metadata · TLDR · Notes (state in 2026, corrections to the source) · Problem · Solution · Code examples · Advantages · Disadvantages / tradeoffs · Related patterns · When to use / when NOT to use

Source: frontendpatterns.dev/error-boundary.

## Metadata

- **Category:** Resilience
- **Level:** Advanced
- **Examples:** React, Vue, Svelte, Native web
- **Last updated:** 29 October 2025
- **Author:** Den Odell

## TLDR

"Catch render errors in a boundary component that displays a fallback UI instead of crashing the
entire application."

## Notes (state in 2026, corrections to the source)

- Equivalents: React — still a class component (or `react-error-boundary`); in React 19 additionally
  `createRoot(el, { onCaughtError, onUncaughtError })` for reporting. Vue `onErrorCaptured`/`app.config.errorHandler`.
  Svelte 5 — `<svelte:boundary onerror>` with a `failed` snippet (the Svelte example below catches only the global `error`
  and is not a real boundary). Angular (fw-angular) — a global `ErrorHandler`, locally `@defer … @error` and
  the `error` status in `resource`.
- `react-error-boundary` provides `useErrorBoundary().showBoundary(err)` — this is how an error is passed from asynchronous
  code to the boundary (resilience/error-handling.md).
- The Svelte examples are Svelte 4 syntax; in Svelte 5: `$props()`, `$state`, `onclick`, `<svelte:boundary>` (a boundary for errors
  and — with `await` in components — for loading).

## Problem

Unhandled JavaScript errors (a bug in the code, badly formatted data from the API, an exception from a library)
propagate through the component tree up to the root, where the whole application crashes — the user
sees a black/empty screen instead of anything useful. The author: "I've seen users lose entire forms
because an unrelated chart component failed to render."

## Solution

An Error Boundary works like a try/catch block for a component tree — it wraps part of the interface in
a component that catches the rendering errors of its children and shows a fallback UI. The recommended
layered strategy: one boundary at the root level as a safety net, plus separate,
more detailed boundaries around risky, isolated features.

**An important limitation:** error boundaries catch **only** errors from rendering, lifecycle methods and
constructors — they do **not** cover event handlers (`onClick` etc.), asynchronous code or
rejected Promises. Those require a traditional try/catch (see `error-handling.md`).

## Code examples

### Basic Error Boundary — React

```javascript
class ErrorBoundary extends React.Component {
  state = { hasError: false, error: null };

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught:', error, errorInfo);
  }

  resetError = () => this.setState({ hasError: false, error: null });

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary">
          <h1>Something went wrong</h1>
          <button onClick={this.resetError}>Try again</button>
        </div>
      );
    }
    return this.props.children;
  }
}

function App() {
  return (
    <ErrorBoundary>
      <Dashboard />
    </ErrorBoundary>
  );
}
```

### Basic Error Boundary — Vue

```vue
<script setup>
import { ref, onErrorCaptured } from 'vue';

const hasError = ref(false);
const error = ref(null);

onErrorCaptured((err) => {
  hasError.value = true;
  error.value = err;
  return false; // Prevent propagation
});

const reset = () => {
  hasError.value = false;
  error.value = null;
};
</script>

<template>
  <div v-if="hasError" class="error-boundary">
    <h1>Something went wrong</h1>
    <button @click="reset">Try again</button>
  </div>
  <slot v-else />
</template>
```

### Basic Error Boundary — Svelte

```svelte
<script>
  import { onMount } from 'svelte';

  let hasError = false;
  let errorMessage = '';

  onMount(() => {
    const handleError = (event) => {
      if (event.error) {
        hasError = true;
        errorMessage = event.error.message;
        event.preventDefault();
      }
    };
    window.addEventListener('error', handleError);
    return () => window.removeEventListener('error', handleError);
  });

  const reset = () => { hasError = false; errorMessage = ''; };
</script>

{#if hasError}
  <div class="error-boundary">
    <h1>Something went wrong</h1>
    <button on:click={reset}>Try again</button>
  </div>
{:else}
  <slot />
{/if}
```

### Basic Error Boundary — Web Components

```javascript
class ErrorBoundary extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this.hasError = false;
  }

  connectedCallback() {
    this.render();
    this.addEventListener('error', (event) => {
      this.hasError = true;
      this.errorMessage = event.error?.message || 'Unknown error';
      this.render();
      event.stopPropagation();
    }, true);
  }

  reset() {
    this.hasError = false;
    this.render();
  }

  render() {
    if (this.hasError) {
      this.shadowRoot.innerHTML = `
        <div class="error-boundary">
          <h1>Something went wrong</h1>
          <button id="reset">Try again</button>
        </div>
      `;
      this.shadowRoot.getElementById('reset').onclick = () => this.reset();
    } else {
      this.shadowRoot.innerHTML = '<slot></slot>';
    }
  }
}

customElements.define('error-boundary', ErrorBoundary);
```

### Granular Boundaries

```javascript
function Dashboard() {
  return (
    <ErrorBoundary fallback={<PageError />}>
      <ErrorBoundary fallback={<WidgetError />}>
        <SalesChart />
      </ErrorBoundary>
      <ErrorBoundary fallback={<WidgetError />}>
        <RecentActivity />
      </ErrorBoundary>
      <ErrorBoundary fallback={<WidgetError />}>
        <UserList />
      </ErrorBoundary>
    </ErrorBoundary>
  );
}
```

### Custom Fallback UI

```javascript
<ErrorBoundary
  fallback={(error, reset) => (
    <div>
      <h2>Widget failed to load</h2>
      <p>{error.message}</p>
      <button onClick={reset}>Retry</button>
    </div>
  )}
>
  <ComplexWidget />
</ErrorBoundary>
```

### Using react-error-boundary

```javascript
import { ErrorBoundary } from 'react-error-boundary';

function ErrorFallback({ error, resetErrorBoundary }) {
  return (
    <div role="alert">
      <p>Something went wrong:</p>
      <pre>{error.message}</pre>
      <button onClick={resetErrorBoundary}>Try again</button>
    </div>
  );
}

<ErrorBoundary FallbackComponent={ErrorFallback} onError={logErrorToService}>
  <Dashboard />
</ErrorBoundary>
```

## Advantages

- The application remains partly functional — the user still has the navigation and the undamaged
  components.
- The user sees a useful message instead of an empty screen.
- The failure is contained in a specific, limited part of the interface.
- Automatic error logging when integrated with monitoring (e.g. Sentry).
- "Try again" buttons allow recovery without refreshing the whole page.
- The message can be split: friendly for the user, a detailed stack trace for the developer.

## Disadvantages / tradeoffs

- They catch only rendering/lifecycle errors — event handlers, async code and Promise
  rejections require an ordinary try/catch separately.
- In React they require a class component (the `react-error-boundary` library lets you avoid this).
- A generic "something went wrong" can **mask** the error instead of helping to fix it — detailed
  logging on the dev side is needed.
- Placement is hard: too few boundaries → combined failures; too many → fallback UI everywhere.
- A reset without fixing the cause of the error can immediately lead to the same error repeating.
- During development it is sometimes worth **turning off** error boundaries, so that errors are visible during
  testing, not silently caught.

## Related patterns

- [Error Handling](./error-handling.md) — Resilience
- [Async Boundary](./async-boundary.md) — Resilience
- [Loading State](./loading-state.md) — Resilience
- [Error Boundaries (React)](https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary)
- [onErrorCaptured Hook (Vue)](https://vuejs.org/api/composition-api-lifecycle.html#onerrorcaptured)
- [Error Handling (Svelte)](https://svelte.dev/docs/svelte#onerror)
- [react-error-boundary Library](https://github.com/bvaughn/react-error-boundary)

## When to use / when NOT to use

Use it **always**, at least at the application root level — this is the minimal, cheap safety
net. Add granular boundaries around specific, risky widgets (charts,
third-party integrations), where the failure of one element should not take the rest of the page down with it.
Do **not** try to catch network/async errors with it — that is the job of `error-handling.md`/`retry.md`;
an Error Boundary solves a different problem (a rendering crash), not a failed fetch.
