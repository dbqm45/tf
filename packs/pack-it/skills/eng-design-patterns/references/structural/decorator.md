# Decorator

> **Contents:** Problem · Solution and participants · When to use · Costs · Relations · Idiomatic form in TS · Example (TS) · When NOT to use / pitfalls

Category: structural. The essence: an object wraps another object **with the same interface** and adds behaviour
before/after delegating; the layers can be composed at runtime in any combinations.

## Problem
Fetching exchange rates requires: retrying on network errors, caching, logging, metrics — in various
combinations depending on the environment. Subclasses (`CachedRetryingLoggingRates`…) multiply combinatorially, and flags
in one class turn it into a bag of conditions.

## Solution and participants
- **Component** — the shared interface (`RateProvider`).
- **Concrete component** — the basic behaviour (`HttpRateProvider`).
- **Decorators** — implement the same interface, hold the wrapped component (of the interface type, not the class!)
  and add logic before/after the call.
- **Client/application composition** — assembles the stack of layers.

## When to use
- Responsibilities added at runtime, without changing the class and without an explosion of subclasses.
- Inheritance impossible or impractical (a class from a library, a closed hierarchy).
- The behaviour naturally falls into cross-cutting layers: retry, cache, logging, metrics, authorization, compression.

## Costs
The order of the layers changes the result (cache before or after retry?); it is hard to remove a layer from the middle of the stack; debugging through
many levels of indirection; the code assembling the stack can be unreadable.

## Relations
- **Adapter** changes the interface; a Decorator keeps it and allows stacking layers.
- **Proxy** has the same shape, a different motivation: control over access and the object's life cycle, usually one layer.
- **Chain of Responsibility** can interrupt the flow; a decorator always delegates further.
- **Composite** has many children; a decorator has one. **Strategy** changes the inside, a Decorator the shell.

## Idiomatic form in TS
For a single function the decorator is a **higher-order function**: `withRetry(fetchRate, 3)` returns a function with the
same signature. HTTP framework middleware and client interceptors are this pattern in its framework version.

**A note on terminology:** the `@decorator` syntax (ECMAScript decorators in TS 5+, legacy `experimentalDecorators`)
is **a language mechanism** acting on classes/methods at the moment they are defined — not the same as the pattern. It can
serve to implement it (a method decorator wrapping the call), but the presence of `@something` does not mean the pattern:
check whether there is wrapping through composition with a shared interface (lang-typescript).

## Example (TS)
```ts
interface RateProvider {
  rate(from: string, to: string): Promise<number>;
}

class HttpRateProvider implements RateProvider {
  async rate(from: string, to: string): Promise<number> {
    if (from === to) return 1;
    return 4.27; // an HTTP call would be here
  }
}

class RetryingRates implements RateProvider {
  readonly #inner: RateProvider;
  readonly #attempts: number;
  constructor(inner: RateProvider, attempts = 3) {
    this.#inner = inner;
    this.#attempts = attempts;
  }
  async rate(from: string, to: string): Promise<number> {
    let lastError: unknown;
    for (let i = 0; i < this.#attempts; i++) {
      try {
        return await this.#inner.rate(from, to);
      } catch (error) {
        lastError = error;
      }
    }
    throw lastError;
  }
}

class CachedRates implements RateProvider {
  readonly #inner: RateProvider;
  readonly #cache = new Map<string, number>();
  constructor(inner: RateProvider) {
    this.#inner = inner;
  }
  async rate(from: string, to: string): Promise<number> {
    const key = `${from}/${to}`;
    const hit = this.#cache.get(key);
    if (hit !== undefined) return hit;
    const value = await this.#inner.rate(from, to);
    this.#cache.set(key, value);
    return value;
  }
}

// Composition: the cache on the outside — a hit does not trigger retrying.
const rates: RateProvider = new CachedRates(new RetryingRates(new HttpRateProvider()));
rates.rate('EUR', 'PLN').then((r) => console.log('EUR/PLN', r));
```
The functional form:
```ts
type Fetch<A extends unknown[], R> = (...args: A) => Promise<R>;

function withRetry<A extends unknown[], R>(fn: Fetch<A, R>, attempts = 3): Fetch<A, R> {
  return async (...args) => {
    let lastError: unknown;
    for (let i = 0; i < attempts; i++) {
      try {
        return await fn(...args);
      } catch (error) {
        lastError = error;
      }
    }
    throw lastError;
  };
}

const fetchRate = withRetry(async (from: string, to: string) => (from === to ? 1 : 4.27));
fetchRate('EUR', 'PLN').then(console.log);
```

## When NOT to use / pitfalls
- **This is not the `@decorator` from TS** — the most common mistake in this language (the note above).
- Few (1–2), non-growing additions — a parameter or a configuration option is simpler than a stack of classes.
- You often need to **remove** a specific layer from the middle — consider function composition with an explicit list of steps.
- A decorator that changes the meaning of the result (and not only the shell) hides business logic in the infrastructure — rules
  belong to the domain (ddd-tactical-design).
