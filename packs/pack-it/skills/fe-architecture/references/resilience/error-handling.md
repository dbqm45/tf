# Error Handling

> **Contents:** Metadata · TLDR · Notes (state in 2026, corrections to the source) · Problem · Solution · Code examples · Advantages · Disadvantages / tradeoffs · Related patterns · When to use / when NOT to use

Source: frontendpatterns.dev/error-handling.

## Metadata

- **Category:** Resilience
- **Level:** Advanced
- **Examples:** React, Vue, Native web
- **Last updated:** 29 October 2025
- **Author:** Den Odell

## TLDR

"Handle errors at appropriate layers: catch at API boundaries, transform for display, and show
users actionable messages with recovery options."

## Notes (state in 2026, corrections to the source)

- **Throwing an error in `.catch()` inside `useEffect` does NOT reach the Error Boundary** (it is a rejected promise outside
  the render). Pass it explicitly: `showBoundary(err)` from `react-error-boundary` or through state
  (`setState(() => { throw err; })`). The "Error Boundary Integration" example has been corrected.
- "Try again" should retry the operation, not reload the page (`window.location.reload()` loses state) — corrected.
- Timeout: `AbortSignal.timeout(ms)` and combining it with a cancellation signal `AbortSignal.any([signal, AbortSignal.timeout(ms)])`
  instead of a manual `setTimeout` (it gives a `TimeoutError`, distinguishable from `AbortError`).
- A `TypeError` from `fetch` = a network/CORS error, but a `TypeError` from your own code too — classify only errors from the
  `fetch` call itself, not from the whole block.
- Model the result as a discriminated union (`idle | loading | error | success`), not three independent flags
  (lang-typescript). In Angular the status is given by `resource`/`httpResource` (fw-angular).
- Retry with backoff — the canonical version is in resilience/retry.md (a shortcut here); 409/422 are normal business outcomes,
  show them next to the fields (fe-web-platform).

## Problem

A lack of consistent error handling leads to: infinite loading states (the error never
ends `loading`), silent failures (an error occurs, nothing happens on the screen), no error logging
on the dev side, and an inconsistent approach between different components of the same
application.

## Solution

Key principles: every asynchronous operation requires **explicit** error handling; errors must be
**classified** (404 vs timeout vs 401) and treated differently depending on the type; messages for
the user must be **understandable to a human**, not a raw error from the devtools; where possible,
apply graceful degradation (data from the cache) instead of a complete failure.

## Code examples

### Basic Error Handling

```javascript
async function fetchUser(id) {
  try {
    const response = await fetch(`/api/users/${id}`);
    if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch user:', error);
    throw error;
  }
}
```

### Error Classification and Recovery

```javascript
class APIError extends Error {
  constructor(message, status, code) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

async function fetchUser(id) {
  try {
    const response = await fetch(`/api/users/${id}`);
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new APIError(errorData.message || 'Request failed', response.status, errorData.code);
    }
    return await response.json();
  } catch (error) {
    if (error instanceof TypeError) {
      throw new APIError('Network error - check your connection', 0, 'NETWORK_ERROR');
    }
    if (error instanceof APIError) throw error;
    throw new APIError('Unexpected error occurred', 500, 'UNKNOWN_ERROR');
  }
}
```

### Component with Error State — React

```javascript
function UserProfile({ userId }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [attempt, setAttempt] = useState(0); // bump to retry

  useEffect(() => {
    async function loadUser() {
      try {
        setLoading(true);
        setError(null);
        setUser(await fetchUser(userId));
      } catch (err) {
        setError(err);
        window.Sentry?.captureException(err, { tags: { userId } });
      } finally {
        setLoading(false);
      }
    }
    loadUser();
  }, [userId, attempt]);

  if (loading) return <Spinner />;
  if (error) return <ErrorDisplay error={error} onRetry={() => setAttempt(a => a + 1)} />;
  return <div>{user.name}</div>;
}
```

### Component with Error State — Vue

```vue
<script setup>
import { ref, onMounted } from 'vue';

const user = ref(null);
const loading = ref(true);
const error = ref(null);

async function loadUser(userId) {
  try {
    loading.value = true;
    error.value = null;
    const response = await fetch(`/api/users/${userId}`);
    if (!response.ok) throw new Error('Failed to fetch user');
    user.value = await response.json();
  } catch (err) {
    error.value = err.message;
  } finally {
    loading.value = false;
  }
}

onMounted(() => loadUser(props.userId));
</script>

<template>
  <div v-if="loading">Loading...</div>
  <div v-else-if="error">
    <p>{{ error }}</p>
    <button @click="loadUser(props.userId)">Try again</button>
  </div>
  <div v-else>{{ user.name }}</div>
</template>
```

### Centralized Error Handler

```javascript
class ErrorHandler {
  constructor(options = {}) {
    this.logger = options.logger || console;
    this.onError = options.onError;
  }

  handle(error, context = {}) {
    this.logger.error('Error:', { message: error.message, ...context });
    window.Sentry?.captureException(error, { contexts: context });
    this.onError?.(error, context);
    return this.getUserMessage(error);
  }

  getUserMessage(error) {
    if (error instanceof APIError) {
      const messages = {
        404: "The requested resource wasn't found",
        401: 'Please log in to continue',
        403: "You don't have permission to access this",
        500: 'Server error - please try again later',
      };
      return messages[error.status] || error.message || 'Something went wrong';
    }
    if (error.code === 'NETWORK_ERROR') return 'Network connection failed';
    return 'An unexpected error occurred';
  }
}
```

### Retry Logic with Exponential Backoff

```javascript
async function fetchWithRetry(url, options = {}, maxRetries = 3) {
  let lastError;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const response = await fetch(url, options);
      if (!response.ok) {
        if (response.status >= 400 && response.status < 500) {
          throw new APIError('Request failed', response.status);
        }
        lastError = new APIError('Request failed', response.status);
      } else {
        return await response.json();
      }
    } catch (error) {
      lastError = error;
      if (attempt === maxRetries - 1) throw error;
    }

    await new Promise(r => setTimeout(r, Math.pow(2, attempt) * 1000));
  }
  throw lastError;
}
```

### Error Boundary Integration

```javascript
import { ErrorBoundary, useErrorBoundary } from 'react-error-boundary';

function DataComponent() {
  const [data, setData] = useState(null);
  const { showBoundary } = useErrorBoundary();

  useEffect(() => {
    // Throwing inside .catch() would NOT reach the boundary — hand the error over explicitly
    fetchData().then(setData).catch(showBoundary);
  }, [showBoundary]);

  return <div>{data?.value}</div>;
}

function App() {
  return (
    <ErrorBoundary fallback={<ErrorMessage />}>
      <DataComponent />
    </ErrorBoundary>
  );
}
```

### Global Error Handler

```javascript
window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled rejection:', event.reason);
  window.Sentry?.captureException(event.reason);
  showToast('An unexpected error occurred', 'error');
  event.preventDefault();
});

window.addEventListener('error', (event) => {
  console.error('Global error:', event.error);
  window.Sentry?.captureException(event.error);
});
```

### Timeout Handling

```javascript
async function fetchWithTimeout(url, { timeout = 5000, signal } = {}) {
  // Combine the caller's cancel signal with a timeout (both are native)
  const combined = signal
    ? AbortSignal.any([signal, AbortSignal.timeout(timeout)])
    : AbortSignal.timeout(timeout);
  try {
    const response = await fetch(url, { signal: combined });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } catch (error) {
    if (error.name === 'TimeoutError') throw new Error('Request timeout', { cause: error });
    throw error; // AbortError = cancelled by caller, not a failure to show
  }
}
```

### Graceful Degradation

```javascript
async function fetchUserWithFallback(userId) {
  try {
    return await fetchUser(userId);
  } catch (error) {
    console.warn('Fetch failed, using cache:', error);
    const cached = getCachedUser(userId);
    return cached ? { ...cached, stale: true } : { id: userId, name: 'User', stale: true };
  }
}
```

## Advantages

- The user sees what happened instead of waiting for an infinite load.
- Transient errors become recoverable thanks to retry buttons.
- Production debugging is possible thanks to logging with context.
- Partial functionality beats complete failure.
- Different types of errors get appropriate, tailored treatment.
- The user does not lose the form data they entered, thanks to preserving state on error.

## Disadvantages / tradeoffs

- try/catch blocks add boilerplate in every place where we connect to something.
- An empty `catch (e) {}` hides the error instead of handling it — that is an anti-pattern, not "error handling".
- Every type of error requires a thought-through, separate approach — it cannot be generalized 100%.
- Centralized handlers can oversimplify the nuances of a specific case.
- In React handling **asynchronous** errors is not obvious — an Error Boundary does not catch them.
- Error messages must serve two audiences at once: the user (friendly language) and the developer
  (details for debugging) — these can conflict.
- Overly aggressive logging can flood monitoring tools with noise.
- A fallback from the cache can mislead the user if you do not state explicitly that the data is stale
  (`stale: true` in the example above is not just a technical flag — it should be reflected in the UI).

## Related patterns

- [Error Boundary](./error-boundary.md) — Resilience
- [Loading State](./loading-state.md) — Resilience
- [Retry](./retry.md) — Resilience
- [Error Handling (MDN)](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Control_flow_and_error_handling#exception_handling_statements)
- [try...catch Statement (MDN)](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/try...catch)
- [Promise Error Handling (MDN)](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Using_promises#error_handling)

## When to use / when NOT to use

This is not an optional pattern "to be added later" — every asynchronous operation in production
code **must** have explicit error handling (see the "Resilience by Design" foundation in
`../principles.md`). The only decision is the **level** of handling: a simple try/catch + a message
is enough for unimportant operations; error classification + a central handler + Sentry make sense when
errors in a given place really affect the user's trust (payments, loss of form
data). Do not build the `ErrorHandler` class from the example for one rarely called
`fetch()` — that is form over substance (YAGNI).
