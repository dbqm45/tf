# Proxy

Category: structural. The essence: an object with **the same interface** as the service stands in front of it and controls access:
lazy creation, permissions, cache, remoteness, audit. The client cannot tell it apart from the real service.

## Problem
A document store connects to an expensive resource (initializing a cloud client, fetching keys) and contains confidential
data. Some screens never read documents, and access is to depend on permissions. Adding checks and lazy
initialization at every place of use duplicates logic; changing the store class is impossible (a library).

## Solution and participants
- **Service interface** — the shared contract.
- **Service** — the real logic (slow, expensive, sensitive or remote).
- **Proxy** — holds (or creates) the service, performs auxiliary work before/after delegating, often manages its
  life cycle.

| Variant | What for |
|---|---|
| virtual (lazy) | deferring an expensive initialization until first use |
| protection | checking permissions before the call |
| remote | hiding the network (an RPC/HTTP client stub generated from the contract) |
| caching | remembering the results of repeated requests |
| logging/audit | recording who used it and when |
| smart reference | a usage counter, releasing the resource when nobody holds it |

## When to use
When access to an existing service requires supervision, and the client is to remain unaware — and this supervision recurs
in many places.

## Costs
Additional indirection and a class; possible latency; the flow is harder to trace.

## Relations
- **Decorator** — the same shape; the motivation decides: a Decorator **adds** behaviour and the client composes the layers,
  a Proxy **controls access** to what the service already does, and usually manages its life cycle itself.
- **Adapter** changes the interface; **Facade** gives a different, simpler interface to many objects.

## Idiomatic form in TS
Lazy initialization: `this.#real ??= create()`. Cache: `Map`. The built-in `Proxy` object (`new Proxy(target, handler)`)
intercepts operations at the language level — it is one of the possible implementation techniques (e.g. in reactive libraries),
not a synonym for the pattern; in application code an explicit class is more readable and better typed.

## Example (TS)
```ts
interface DocumentStore {
  read(documentId: string): Promise<string>;
}

class CloudDocumentStore implements DocumentStore {
  constructor() {
    console.log('expensive initialization of the cloud client');
  }
  async read(documentId: string): Promise<string> {
    return `content of ${documentId}`;
  }
}

/** A protection + virtual proxy: checks permissions and creates the service only on first use. */
class GuardedLazyStore implements DocumentStore {
  #real: DocumentStore | undefined;
  readonly #create: () => DocumentStore;
  readonly #canRead: (documentId: string) => boolean;

  constructor(create: () => DocumentStore, canRead: (documentId: string) => boolean) {
    this.#create = create;
    this.#canRead = canRead;
  }

  async read(documentId: string): Promise<string> {
    if (!this.#canRead(documentId)) throw new Error(`no access to ${documentId}`);
    this.#real ??= this.#create();
    return this.#real.read(documentId);
  }
}

const store: DocumentStore = new GuardedLazyStore(
  () => new CloudDocumentStore(),
  (id) => !id.startsWith('HR-'),
);
store.read('CONTRACT-1').then(console.log);
store.read('HR-7').catch((e: unknown) => console.warn(String(e)));
```

## When NOT to use / pitfalls
- **The motivation is new business behaviour** → that is a Decorator (or a change to the service), not a Proxy.
- One check in one place → an ordinary `if` before the call.
- Laziness and caching are often handled by `??=` and `Map` without a separate class — a Proxy makes sense when the supervision is
  reused many times and the client is not to see it.
- Authorization hidden in a proxy does not replace authorization at the system boundary (be-auth-security) — it is an additional
  layer.
