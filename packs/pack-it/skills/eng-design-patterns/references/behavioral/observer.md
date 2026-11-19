# Observer

Category: behavioral. The essence: an object with state (**the publisher**) maintains a list of subscribers and notifies only
them when the state changes; subscribers join and leave at runtime.

## Problem
A product's stock level changes often. The interested parties are: the cart view, a "few items left" alert, a "notify me
when available" list, metrics. Polling in a loop wastes resources and delays reactions, and calling all recipients
directly from the stock level class binds it to every new recipient.

## Solution and participants
- **Publisher** — `subscribe()`/`unsubscribe()` and notification on a change.
- **Subscriber** — an interface (in TS usually a function type) called with the new value or event.
- **Client** — connects publishers with subscribers and is responsible for unsubscribing.

## When to use
- A change in one object is to trigger reactions in others, and the set of recipients is not known up front or changes.
- Recipients observe only temporarily or conditionally.
- UI events hooked up to your own code without modifying the components.

## Costs
The order of notifications is undefined (do not build logic on it); memory leaks and update cascades come easily;
the flow is harder to trace than a direct call.

## Relations
- **Mediator** is sometimes built on subscriptions.
- **Chain** passes a request sequentially to one handler; Observer broadcasts to all.
- **Domain events** (ddd-tactical-design) are an Observer at the model level; between processes — a broker and an outbox
  (be-messaging-outbox), because an in-memory notification is lost on a failure.

## Idiomatic form in TS
Almost never from scratch: `EventTarget`/`CustomEvent` (the browser and Node), `EventEmitter` (Node), RxJS
`Observable`/`Subject`, framework signals (fw-*). `subscribe()` returning **an unsubscribe function** is an idiom that
makes cleaning up easier.

## Example (TS)
```ts
type Listener<T> = (value: T) => void;

class Observable<T> {
  readonly #listeners = new Set<Listener<T>>();

  /** Returns an unsubscribe function — easy to call when the subscriber is destroyed. */
  subscribe(listener: Listener<T>): () => void {
    this.#listeners.add(listener);
    return () => {
      this.#listeners.delete(listener);
    };
  }

  protected emit(value: T): void {
    for (const listener of [...this.#listeners]) listener(value);
  }
}

type StockChange = { sku: string; available: number };

class StockLevels extends Observable<StockChange> {
  readonly #levels = new Map<string, number>();

  set(sku: string, available: number): void {
    if (this.#levels.get(sku) === available) return; // no change — no notification
    this.#levels.set(sku, available);
    this.emit({ sku, available });
  }
}

const stock = new StockLevels();
const stopLowStockAlert = stock.subscribe(({ sku, available }) => {
  if (available < 5) console.log(`few items left: ${sku} (${available})`);
});
stock.subscribe(({ sku, available }) => {
  if (available > 0) console.log(`notify those waiting for ${sku}`);
});

stock.set('COFFEE-1KG', 3);
stopLowStockAlert();
stock.set('COFFEE-1KG', 2); // the alert is already unsubscribed
```

## When NOT to use / pitfalls
- **One recipient known up front** — an ordinary callback is enough.
- Check the platform's and the framework's mechanisms before you write your own `Subject`.
- **Memory leaks**: for every `subscribe()` point out where unsubscribing happens (destroying the component,
  `AbortSignal`, `using`/`Symbol.dispose` — lang-typescript).
- Do not assume the order of subscribers; an exception in one subscriber should not block the others
  (consider error isolation).
- An in-memory observer is not a reliable integration between modules — for that, events with an outbox.
