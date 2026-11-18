# Facade

> **Contents:** Problem · Solution and participants · When to use · Costs · Relations · Idiomatic form in TS · Example (TS) · When NOT to use / pitfalls

Category: structural. The essence: one **simple interface** to a complex subsystem; the client calls one operation instead of
coordinating many classes in the right order.

## Problem
Placing an order requires: reserving stock levels, computing the price, charging the payment, withdrawing the reservation
on a payment error and sending a confirmation. When every controller, job and test repeats this choreography, a change of
the order or adding a step has to be applied in many places, and the calling code knows the details of four modules.

## Solution and participants
- **Facade** — exposes a limited, convenient set of operations (`placeOrder()`); it knows whom to direct the requests to and in what
  order.
- **Subsystem** — classes that do not know about the facade and can be used directly by those who need more.
- **Additional facades** — when one grows, split it per area.

## When to use
- You need a simple entry to a complex library or module — for 80% of the use cases.
- You want to layer the system: every layer/module exposes a facade, the rest is internal (the module's public `index.ts`
  — fe-architecture; a deep module — ddd-context-mapping).
- In DDD a thin **application service** implementing a use case plays the role of a facade over the domain and the infrastructure
  (ddd-tactical-design) — without business rules inside.

## Costs
A facade easily becomes a "god object" coupled with the whole application; a change in it touches many clients at once.

## Relations
- **Adapter** fits the existing interface of one object; a Facade defines a new one for many.
- **Mediator** also centralizes collaboration, but the components know about it; the subsystem does not know about the facade.
- **Proxy** has an interface identical to the object's; a Facade — a different, simplified one.
- **Abstract Factory** can replace a facade when only the creation of the subsystem's objects needs to be hidden.

## Idiomatic form in TS
Often a **module function** (`export async function placeOrder(deps, cmd)`) with the dependencies passed
explicitly is enough; a class — when the facade has state or many operations sharing dependencies.

## Example (TS)
```ts
type Line = { sku: string; qty: number };
type OrderResult = { ok: true; orderId: string } | { ok: false; reason: string };

class Inventory {
  reserve(lines: readonly Line[]): string {
    return `res-${lines.length}`;
  }
  release(reservationId: string): void {
    console.log('released', reservationId);
  }
}
class Pricing {
  totalCents(lines: readonly Line[]): number {
    return lines.reduce((sum, l) => sum + l.qty * 1_999, 0);
  }
}
class Payments {
  async charge(customerId: string, cents: number): Promise<boolean> {
    return cents < 100_000 && customerId !== '';
  }
}
class Mailer {
  send(customerId: string, text: string): void {
    console.log(`→ ${customerId}: ${text}`);
  }
}

/** Facade: one use case instead of a choreography in every caller. */
class Checkout {
  readonly #inventory: Inventory;
  readonly #pricing: Pricing;
  readonly #payments: Payments;
  readonly #mailer: Mailer;

  constructor(inventory: Inventory, pricing: Pricing, payments: Payments, mailer: Mailer) {
    this.#inventory = inventory;
    this.#pricing = pricing;
    this.#payments = payments;
    this.#mailer = mailer;
  }

  async placeOrder(customerId: string, lines: readonly Line[]): Promise<OrderResult> {
    const reservation = this.#inventory.reserve(lines);
    const total = this.#pricing.totalCents(lines);
    if (!(await this.#payments.charge(customerId, total))) {
      this.#inventory.release(reservation);
      return { ok: false, reason: 'payment rejected' };
    }
    const orderId = `ORD-${reservation}`;
    this.#mailer.send(customerId, `Order ${orderId} accepted`);
    return { ok: true, orderId };
  }
}

const checkout = new Checkout(new Inventory(), new Pricing(), new Payments(), new Mailer());
checkout.placeOrder('C-1', [{ sku: 'COFFEE', qty: 2 }]).then(console.log);
```

## When NOT to use / pitfalls
- **The subsystem already has a simple interface** — a facade over a facade is an unnecessary layer.
- The facade starts to know and coordinate everything in the application → split it per area.
- A facade is not the place for business rules (discounts, limits) — those go to the domain; the facade only orchestrates.
- Do not close the subsystem off completely: advanced clients may need direct access.
