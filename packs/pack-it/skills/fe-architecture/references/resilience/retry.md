# Retry

> **Contents:** Metadata · TLDR · Notes (state in 2026, corrections to the source) · Problem · Solution · Code examples · Advantages · Disadvantages / tradeoffs · Related patterns · When to use / when NOT to use

Source: frontendpatterns.dev/retry.

## Metadata

- **Category:** Resilience
- **Level:** Advanced
- **Examples:** React, Native web
- **Last updated:** 15 November 2025
- **Author:** Den Odell

## TLDR

"Re-attempt failed requests with exponential backoff to handle transient network issues without
showing errors for temporary problems."

## Notes (state in 2026, corrections to the source)

- **A bug in the source's example corrected:** the "non-retryable" error was thrown inside `try` and caught by its own
  `catch`, so 404/401 were retried too. Now non-retryable errors go out at once; `options` are passed to
  `fetch`; `onRetry` was added (used in the "User Feedback" example) and cancellation handling.
- Jitter: "full jitter" (`random(0, delay)`) is recommended — it spreads clients out better than ±25%.
- Retry only idempotent operations; `POST` — only with an idempotency key (`Idempotency-Key`), agreed with
  the backend (be-api-design).
- Data layers have retry built in (TanStack Query `retry`/`retryDelay`, RxJS `retry({ delay })` in Angular) —
  do not write your own if you already use them. A circuit breaker is usually a job for the backend/gateway, rarely for the browser.

## Problem

Transient failures (a momentary network problem, a server timeout, a deployment, a container restart)
look to the user exactly like permanent errors. A 2-second connection drop shows
the same error message as a request for a resource that does not exist. Mobile users suffer
particularly — constant packet loss and switching WiFi↔mobile mean that "every dropout
triggers an error dialog".

## Solution

Automatic retry logic: when a request fails with a **transient** error (5xx, timeout,
no network), try again before you show the error to the user — in most cases the second
attempt succeeds and the user never learns about the failure.

**The key technique — exponential backoff:** wait 1s before the first retry, 2s before the second, 4s
before the third. Add a random **jitter** to avoid the "thundering herd" (thousands of clients retrying
at the same time after the same server failure). Retry **only** truly transient errors —
`404` (the resource does not exist) and `401` (no authentication) will not be fixed by repetition — and set
a sensible limit on the maximum number of attempts.

## Code examples

### Exponential Backoff with Jitter

```javascript
class HttpError extends Error {
  constructor(status, retryable) {
    super(`HTTP ${status}`);
    this.status = status;
    this.retryable = retryable;
  }
}

async function fetchWithRetry(url, options = {}) {
  const {
    maxRetries = 3,
    baseDelay = 1000,
    maxDelay = 30000,
    retryableStatuses = [408, 429, 500, 502, 503, 504],
    onRetry,
    ...fetchOptions // method, headers, body, signal…
  } = options;

  for (let attempt = 0; ; attempt++) {
    let error;
    try {
      const response = await fetch(url, fetchOptions);
      if (response.ok) return await response.json();
      error = new HttpError(response.status, retryableStatuses.includes(response.status));
    } catch (e) {
      if (e.name === 'AbortError') throw e; // cancelled by the caller — never retry
      error = e;                            // network error (TypeError) — retryable
    }

    const retryable = error.retryable ?? true;
    if (!retryable || attempt >= maxRetries - 1) throw error;

    // Exponential backoff with full jitter
    const cap = Math.min(baseDelay * 2 ** attempt, maxDelay);
    onRetry?.(attempt + 1, error);
    await new Promise(resolve => setTimeout(resolve, Math.random() * cap));
  }
}
```

### React Hook with Retry

```javascript
function useDataWithRetry(url) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    let cancelled = false;

    async function fetchData() {
      setLoading(true);
      try {
        const result = await fetchWithRetry(url, { maxRetries: 3 });
        if (!cancelled) setData(result);
      } catch (err) {
        if (!cancelled) setError(err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchData();
    return () => { cancelled = true; };
  }, [url, retryCount]);

  return { data, loading, error, retry: () => setRetryCount(c => c + 1) };
}
```

### Retry with Circuit Breaker

```javascript
class CircuitBreaker {
  constructor(threshold = 5, timeout = 60000) {
    this.failureCount = 0;
    this.threshold = threshold;
    this.timeout = timeout;
    this.state = 'CLOSED'; // CLOSED, OPEN, HALF_OPEN
    this.nextAttempt = Date.now();
  }

  async execute(fn) {
    if (this.state === 'OPEN') {
      if (Date.now() < this.nextAttempt) throw new Error('Circuit breaker is OPEN');
      this.state = 'HALF_OPEN';
    }

    try {
      const result = await fn();
      this.failureCount = 0;
      this.state = 'CLOSED';
      return result;
    } catch (error) {
      this.failureCount++;
      if (this.failureCount >= this.threshold) {
        this.state = 'OPEN';
        this.nextAttempt = Date.now() + this.timeout;
      }
      throw error;
    }
  }
}
```

### Retry-After Header Support

```javascript
async function fetchWithRetryAfter(url, maxRetries = 3) {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const response = await fetch(url);
      if (response.ok) return await response.json();

      if (response.status === 429 && attempt < maxRetries - 1) {
        const retryAfter = response.headers.get('Retry-After');
        if (retryAfter) {
          // Retry-After can be seconds or HTTP date
          const delay = Number.isNaN(Number(retryAfter))
            ? Math.max(0, new Date(retryAfter) - Date.now())
            : Number(retryAfter) * 1000;
          await new Promise(resolve => setTimeout(resolve, delay));
          continue;
        }
      }

      if (response.status >= 500) throw new Error(`Server error: ${response.status}`);
      throw new Error(`Client error: ${response.status}`);
    } catch (error) {
      if (attempt === maxRetries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
    }
  }
}
```

### User Feedback During Retry

```javascript
function DataLoader({ url }) {
  const [attempt, setAttempt] = useState(0);
  const [data, setData] = useState(null);

  useEffect(() => {
    fetchWithRetry(url, {
      maxRetries: 3,
      onRetry: (attemptNum) => setAttempt(attemptNum),
    }).then(setData);
  }, [url]);

  if (!data) {
    return (
      <div>
        Loading...
        {attempt > 0 && <p>Connection issue, retrying (attempt {attempt})...</p>}
      </div>
    );
  }
  return <div>{data.content}</div>;
}
```

## Advantages

- Network interruptions stay invisible to the user.
- Mobile users do not see constant, repeated error messages.
- The application survives server deployments and infrastructure changes without a failure visible to the client.
- Rate limiting becomes manageable thanks to the `Retry-After` header.
- Read operations (GET) become practically "bulletproof" — safe to retry by nature.
- Much less friction for the user — no need to click "Try Again" manually.

## Disadvantages / tradeoffs

- The error message is delayed — the user waits through **all** the attempts before learning about
  a real, permanent problem.
- Without jitter a "thundering herd" problem arises — thousands of clients overwhelm the server at the same
  moment after a shared failure.
- Tuning the parameters is hard: too aggressive retrying wastes resources, too conservative forces
  the user to wait too long.
- Retry logic can **mask** real infrastructure problems that should be
  noticed and fixed, not just patiently worked around.
- The delays grow fast (1s, 2s, 4s, 8s, 16s) — after a few attempts the user may conclude that
  the application has frozen.
- **Never thoughtlessly retry non-idempotent operations** — retrying a `POST` can create
  a duplicate resource (e.g. two orders from one click of "Buy").
- A circuit breaker adds real implementation complexity.
- Data transfer costs grow on metered mobile connections.

## Related patterns

- [Error Handling](./error-handling.md) — Resilience
- [Retry Pattern (Microsoft)](https://docs.microsoft.com/en-us/azure/architecture/patterns/retry)
- [Exponential Backoff (Wikipedia)](https://en.wikipedia.org/wiki/Exponential_backoff)

## When to use / when NOT to use

Use it for **idempotent** operations (GET, and carefully designed PUT/DELETE) exposed to
transient network errors — this is safe by default and highly cost-effective. Do **not** automatically retry
`POST`/resource-creating operations if the server does not guarantee idempotency (e.g. through
an `Idempotency-Key`) — the risk of a duplicate is worse than a one-off, visible error. Do not build a Circuit
Breaker "just in case" for an application with little traffic — it is an overhead justified at real
scale and with a real risk of overloading the backend, not a default addition to every `fetch()`.
