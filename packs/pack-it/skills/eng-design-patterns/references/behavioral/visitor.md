# Visitor

> **Contents:** Problem · Solution and participants · When to use · Costs · Relations · Idiomatic form in TS · Example (TS) · When NOT to use / pitfalls

Category: behavioral. The essence: new **operations** on a stable type hierarchy live in separate visitor
objects; the elements only "receive the guest" (`accept`) and direct it to the right method (double dispatch).

## Problem
A charging tariff or a price list is an expression: a constant, a price per kWh × energy, a sum, a product, a minimum. On the same tree
many operations are needed: computing the amount, a readable description for the customer, validation, export to a partner's format. Adding
every operation to every node class bloats the model and mixes responsibilities.

## Solution and participants
- **Visitor** — an interface with a method for each concrete element type.
- **Concrete visitor** — one operation for all types (computation, description).
- **Element** — `accept(visitor)`.
- **Concrete elements** — `accept` calls the visitor's method appropriate for its own type.

## When to use
- The type hierarchy is **stable**, and **operations** on it keep being added.
- Auxiliary operations (export, a report, validation) are not to clutter the element classes.
- A visitor can collect state while traversing the structure (e.g. tree statistics).

## Costs
A new element type requires changing **all** visitors; a visitor sees only the elements' public API;
the additional complexity of double dispatch.

## Relations
- It usually works on a **Composite** tree, often together with an **Iterator**.
- It is sometimes described as a more powerful **Command** — an operation on objects of many unrelated types.

## Idiomatic form in TS
**A discriminated union + a function with a `switch`** is "a visitor without `accept`": each operation is a function, and the compiler
enforces handling all the variants when a new one is added (lang-typescript). The classic Visitor — when the hierarchy is
open (classes from different modules) or the elements have their own logic.

## Example (TS)
```ts
interface TariffVisitor<R> {
  fixed(node: Fixed): R;
  perKwh(node: PerKwh): R;
  sum(node: Sum): R;
  min(node: Min): R;
}

interface TariffNode {
  accept<R>(visitor: TariffVisitor<R>): R;
}

class Fixed implements TariffNode {
  readonly cents: number;
  constructor(cents: number) {
    this.cents = cents;
  }
  accept<R>(v: TariffVisitor<R>): R {
    return v.fixed(this);
  }
}
class PerKwh implements TariffNode {
  readonly centsPerKwh: number;
  constructor(centsPerKwh: number) {
    this.centsPerKwh = centsPerKwh;
  }
  accept<R>(v: TariffVisitor<R>): R {
    return v.perKwh(this);
  }
}
class Sum implements TariffNode {
  readonly parts: readonly TariffNode[];
  constructor(...parts: TariffNode[]) {
    this.parts = parts;
  }
  accept<R>(v: TariffVisitor<R>): R {
    return v.sum(this);
  }
}
class Min implements TariffNode {
  readonly a: TariffNode;
  readonly b: TariffNode;
  constructor(a: TariffNode, b: TariffNode) {
    this.a = a;
    this.b = b;
  }
  accept<R>(v: TariffVisitor<R>): R {
    return v.min(this);
  }
}

/** Operation 1: the amount for a session. */
class Price implements TariffVisitor<number> {
  readonly #kwh: number;
  constructor(kwh: number) {
    this.#kwh = kwh;
  }
  fixed(n: Fixed): number {
    return n.cents;
  }
  perKwh(n: PerKwh): number {
    return Math.round(n.centsPerKwh * this.#kwh);
  }
  sum(n: Sum): number {
    return n.parts.reduce((total, p) => total + p.accept(this), 0);
  }
  min(n: Min): number {
    return Math.min(n.a.accept(this), n.b.accept(this));
  }
}

/** Operation 2: a description for the customer. */
class Describe implements TariffVisitor<string> {
  fixed(n: Fixed): string {
    return `${(n.cents / 100).toFixed(2)} PLN`;
  }
  perKwh(n: PerKwh): string {
    return `${(n.centsPerKwh / 100).toFixed(2)} PLN/kWh`;
  }
  sum(n: Sum): string {
    return n.parts.map((p) => p.accept(this)).join(' + ');
  }
  min(n: Min): string {
    return `min(${n.a.accept(this)}, ${n.b.accept(this)})`;
  }
}

const tariff = new Min(new Sum(new Fixed(200), new PerKwh(239)), new Fixed(15_000));
console.log(tariff.accept(new Describe()), '=', tariff.accept(new Price(40)) / 100, 'PLN for 40 kWh');
```
The union form (a closed set of nodes):
```ts
type Tariff =
  | { kind: 'fixed'; cents: number }
  | { kind: 'perKwh'; centsPerKwh: number }
  | { kind: 'sum'; parts: readonly Tariff[] }
  | { kind: 'min'; a: Tariff; b: Tariff };

function price(t: Tariff, kwh: number): number {
  switch (t.kind) {
    case 'fixed':
      return t.cents;
    case 'perKwh':
      return Math.round(t.centsPerKwh * kwh);
    case 'sum':
      return t.parts.reduce((s, p) => s + price(p, kwh), 0);
    case 'min':
      return Math.min(price(t.a, kwh), price(t.b, kwh));
  }
}
console.log(price({ kind: 'sum', parts: [{ kind: 'fixed', cents: 200 }, { kind: 'perKwh', centsPerKwh: 239 }] }, 40));
```

## When NOT to use / pitfalls
- **Element types are added often** — that is the opposite of the situation in which the pattern helps; every new type = a change
  to every visitor. Then ordinary polymorphism (a method in each class).
- Check in which dimension the code really grows (types or operations) before you choose.
- 2–3 types and one operation → a union + `switch`; a Visitor pays off with a combination of many types × many operations.
- A visitor reaching into the elements' internals through getters breaks encapsulation — expose only what the operations
  really need.
