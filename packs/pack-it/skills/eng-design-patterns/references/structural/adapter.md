# Adapter

Category: structural. The essence: an object that **implements the interface our code expects** and translates the calls
into an API we cannot change.

## Problem
The domain expects a `PaymentGateway` port (async, amounts in grosze (cents), the result as a union). The payment provider gives an SDK
with callbacks, amounts as text in PLN and its own error codes. Calling the SDK directly from the logic
spreads its conventions across the whole code and makes changing the provider impossible.

## Solution and participants
- **Client interface (port)** — what our code wants.
- **Service (adaptee)** — the existing API: an external library, legacy, another context.
- **Adapter** — implements the port, holds a reference to the service, converts data and calls in both directions.
The service does not know about the adapter. A "class" adapter (multiple inheritance) does not exist in TS — we use composition.

## When to use
- Integrating an external or legacy library with an incompatible interface.
- Hexagonal architecture: an infrastructure adapter implements a port defined by the domain
  (ddd-tactical-design; in server code — be-*).
- Several services with a similar function and different signatures are to be used uniformly.
- An anti-corruption layer between contexts — the adapter is its building block (ddd-context-mapping).

## Costs
A new interface and class; sometimes it is simpler to change the service itself, if it is ours.

## Relations
- **Bridge** has a similar structure, but is planned up front; an Adapter patches an existing incompatibility.
- **Decorator** keeps the interface and allows stacking layers; an Adapter changes the interface.
- **Proxy** has the same interface as the object and controls access; an Adapter translates into a different one.
- **Facade** creates a new, simpler interface to a whole subsystem; an Adapter usually wraps one object.

## Idiomatic form in TS
When the port is a single function, the adapter is a function: `const charge: Charge = (id, cents) => sdk.pay(...)`.
Promisifying callbacks (`new Promise(...)`) is typical adapter work.

## Example (TS)
```ts
type Currency = 'PLN' | 'EUR';
type ChargeResult = { ok: true; reference: string } | { ok: false; reason: string };

/** A port defined on our side. */
interface PaymentGateway {
  charge(orderId: string, amountCents: number, currency: Currency): Promise<ChargeResult>;
}

/** An external SDK — we cannot change it. */
class LegacyPayClient {
  pay(
    request: { ref: string; amount: string; cur: string },
    done: (error: string | null, transactionId?: string) => void,
  ): void {
    setTimeout(() => done(null, `tx-${request.ref}`), 10);
  }
}

class LegacyPayAdapter implements PaymentGateway {
  readonly #client: LegacyPayClient;

  constructor(client: LegacyPayClient) {
    this.#client = client;
  }

  charge(orderId: string, amountCents: number, currency: Currency): Promise<ChargeResult> {
    const request = { ref: orderId, amount: (amountCents / 100).toFixed(2), cur: currency };
    return new Promise((resolve) => {
      this.#client.pay(request, (error, transactionId) => {
        if (error !== null || transactionId === undefined) {
          resolve({ ok: false, reason: error ?? 'missing transaction identifier' });
        } else {
          resolve({ ok: true, reference: transactionId });
        }
      });
    });
  }
}

const gateway: PaymentGateway = new LegacyPayAdapter(new LegacyPayClient());
gateway.charge('ORD-9', 12_345, 'PLN').then((result) => console.log(result));
```

## When NOT to use / pitfalls
- **Both sides are under your control** — unify the interface at the source instead of cementing a translating layer.
- **You are designing two independent dimensions of variation from scratch** — that is rather a Bridge.
- The translation is one line in one place → a mapping function, not a class with an interface.
- An adapter must not "leak": if SDK types or exceptions appear in the domain, the adapter does not fulfil its role.
