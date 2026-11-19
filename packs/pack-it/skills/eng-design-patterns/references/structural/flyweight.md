# Flyweight

Category: structural. The essence: many small objects **share the immutable part of their state**, and get the unique part
from the outside — a memory optimization, not an organizational one.

## Problem
A stadium seat map has 60,000 seats. Each seat copies the data of its category (name, price, colour, description of the refund
rules), although there are five categories. In the client's browser and in the booking server's memory this is hundreds of megabytes
of repetition, and the GC constantly has work to do.

## Solution and participants
- **Intrinsic state** — shared and immutable (the seat category) → in the flyweight object.
- **Extrinsic state** — unique (row, number, occupancy) → in a light context or passed
  in method parameters.
- **Flyweight** — an immutable object with the intrinsic state.
- **Flyweight factory** — a pool; returns the existing flyweight for the same key instead of creating a new one.
- **Context** — the extrinsic state + a reference to the flyweight.

## When to use
All three conditions at once: very many similar objects, a **measured** memory problem, the state can be cleanly
split into shared and unique. Examples: glyphs in an editor, map tiles/markers, particles in graphics, tables
with millions of records in the browser.

## Costs
Complexity (two kinds of state, a factory); CPU for RAM — the extrinsic state has to be passed or computed; harder
to read and test.

## Relations
- **Composite** — the leaves of the tree can be flyweights.
- **Singleton** — one, often mutable instance; there are many flyweights and they are immutable.
- DDD value objects are immutable, so they **can** be shared like flyweights (interning) — but that is an optimization,
  not a reason for the modelling.

## Idiomatic form in TS
The pool is a `Map<key, Flyweight>`; immutability through `readonly` + `Object.freeze`. In JS the engine interns strings anyway —
a flyweight makes sense for compound objects.

## Example (TS)
```ts
/** Flyweight: the shared, immutable state of a seat category. */
class SeatCategory {
  readonly code: string;
  readonly priceCents: number;
  readonly color: string;

  constructor(code: string, priceCents: number, color: string) {
    this.code = code;
    this.priceCents = priceCents;
    this.color = color;
    Object.freeze(this);
  }

  label(row: number, seat: number): string {
    return `${this.code} row ${row}, seat ${seat}: ${(this.priceCents / 100).toFixed(2)} PLN`;
  }
}

/** A flyweight factory with a pool. */
class SeatCategories {
  readonly #pool = new Map<string, SeatCategory>();

  get(code: string, priceCents: number, color: string): SeatCategory {
    const key = `${code}|${priceCents}|${color}`;
    let category = this.#pool.get(key);
    if (category === undefined) {
      category = new SeatCategory(code, priceCents, color);
      this.#pool.set(key, category);
    }
    return category;
  }

  get size(): number {
    return this.#pool.size;
  }
}

/** Context: only the extrinsic state + a reference to the flyweight. */
type Seat = { row: number; seat: number; taken: boolean; category: SeatCategory };

const categories = new SeatCategories();
const seats: Seat[] = [];
for (let row = 1; row <= 200; row++) {
  for (let seat = 1; seat <= 300; seat++) {
    const category = row <= 20 ? categories.get('VIP', 45_000, 'gold') : categories.get('STD', 12_000, 'blue');
    seats.push({ row, seat, taken: false, category });
  }
}
console.log(seats.length, 'seats,', categories.size, 'category objects');
console.log(seats[0]?.category.label(1, 1));
```

## When NOT to use / pitfalls
- **There are few objects or memory is not a measured problem** — this is an optimization pattern; in typical application
  code the least often needed one in the catalog. First a profiler (fe-/be- performance: measure before optimizing).
- You cannot cleanly split the state into "always shared" and "unique" → this is not that problem.
- A flyweight must be immutable; a mutable flyweight changes the data of all contexts at once — a bug that is hard to find.
