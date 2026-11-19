# Composite

> **Contents:** Problem · Solution and participants · When to use · Costs · Relations · Idiomatic form in TS · Example (TS) · When NOT to use / pitfalls

Category: structural. The essence: a single element and a group of elements have **the same interface**, so the client
processes the whole tree recursively, without distinguishing leaves from containers.

## Problem
A price list contains products and bundles; a bundle can contain products and other bundles, each with its own discount. Code computing
the price that checks "is this a bundle?" and descends manually is duplicated for every operation (price, weight, list
of SKUs) and breaks at the next level of nesting.

## Solution and participants
- **Component** — the shared interface of operations meaningful for a leaf and a container (`priceCents()`).
- **Leaf** — does the work itself (`Item`).
- **Composite** — holds children of the Component type, delegates the work to them and aggregates the result, adding its own contribution (the bundle discount).
- **Client** — works only through the component interface.

## When to use
- The model is naturally a part–whole tree: bundles, an organizational structure, a menu, rules composed of rules.
- The operations make sense at every level and are to work for any depth.
- Business **specifications** combined with and/or/not are a composite (ddd-tactical-design) — the modelling details are there.

## Costs
A shared interface for very different elements is hard to find; the interface is tempted to become too general; `add()` methods
on a leaf make no sense (keep them only in the composite).

## Relations
- **Decorator** has one wrapped child and adds behaviour; a Composite aggregates many children.
- **Iterator** traverses the tree; **Visitor** performs new operations on it; **Builder** assembles it in steps.
- **Flyweight** — leaves can be shared when there are very many of them; **Prototype** clones whole subtrees.
- **Chain of Responsibility** — a request can go from a leaf up to its ancestors.

## Idiomatic form in TS
The tree as a **discriminated union** + a recursive function (`switch (node.kind)`) — good when the set of node types is
closed. Classes with an interface — when the node types are to be open to extension.

## Example (TS)
```ts
interface PriceComponent {
  readonly name: string;
  priceCents(): number;
}

class Item implements PriceComponent {
  readonly name: string;
  readonly #priceCents: number;
  constructor(name: string, priceCents: number) {
    this.name = name;
    this.#priceCents = priceCents;
  }
  priceCents(): number {
    return this.#priceCents;
  }
}

class Bundle implements PriceComponent {
  readonly name: string;
  readonly #discount: number;
  readonly #children: PriceComponent[] = [];

  constructor(name: string, discount = 0) {
    if (discount < 0 || discount >= 1) throw new RangeError('discount in the range [0, 1)');
    this.name = name;
    this.#discount = discount;
  }

  add(...components: PriceComponent[]): this {
    this.#children.push(...components);
    return this;
  }

  priceCents(): number {
    const sum = this.#children.reduce((total, child) => total + child.priceCents(), 0);
    return Math.round(sum * (1 - this.#discount));
  }
}

const conference = new Bundle('Conference bundle', 0.1).add(
  new Item('Room for a day', 250_000),
  new Bundle('Catering', 0.05).add(new Item('Lunch', 60_000), new Item('Coffee break', 20_000)),
);
console.log(conference.name, conference.priceCents());
```
The union variant (a closed set of nodes):
```ts
type PriceNode =
  | { kind: 'item'; name: string; priceCents: number }
  | { kind: 'bundle'; name: string; discount: number; children: readonly PriceNode[] };

function price(node: PriceNode): number {
  switch (node.kind) {
    case 'item':
      return node.priceCents;
    case 'bundle':
      return Math.round(node.children.reduce((s, c) => s + price(c), 0) * (1 - node.discount));
  }
}
```

## When NOT to use / pitfalls
- **The data is not a tree** — a flat list + `map`/`reduce` is enough.
- The operation makes sense only for leaves or only for containers → these are two different types; empty `add()`/`remove()` on a leaf
  signal that the division is artificial.
- Unbounded recursion: with data from the user, guard against cycles and depth.
- DDD aggregates: do not build a huge tree in one aggregate "because composite" — consistency boundaries matter more
  (ddd-tactical-design).
