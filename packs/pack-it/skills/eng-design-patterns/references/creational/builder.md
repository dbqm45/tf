# Builder

> **Contents:** Problem · Solution and participants · When to use · Costs · Relations · Idiomatic form in TS · Example (TS) · When NOT to use / pitfalls

Category: creational. The essence: a complex object is created **step by step**; you receive the complete and validated product
only at the end.

## Problem
Booking search criteria have a time range (required), a list of resource types, a minimum capacity, sorting,
sometimes availability filters. A constructor with eight parameters (some optional) is unreadable and it is easy to swap
their order; different screens assemble the criteria conditionally, in several places in the code.

## Solution and participants
- **Builder** — an object with step methods (`between()`, `ofType()`…) and a `build()` method that validates and hands over
  an immutable product.
- **Product** — the result; it is not available in an incomplete state.
- **Director (optional)** — encodes repeatable sequences of steps ("last minute search"); in TS usually an ordinary
  function taking the builder.
- Different builders can build different representations from the same steps (e.g. a query and its description for the UI).

## When to use
- Many optional elements assembled **conditionally, over time or recursively** (also trees — Composite).
- Several repeatable "recipes" for the same product (a candidate for a director).
- The product's invariant can be checked only when all the parts are known (validation in `build()`).
- **Test data builders** — default valid values + overriding only what matters in the test (eng-testing).

## Costs
An extra class (and possibly a director); duplication of the field list between the product and the builder.

## Relations
- Factory Method → Abstract Factory → Builder: more and more flexibility and complexity.
- An Abstract Factory hands over the product immediately; a Builder lets you perform steps before receiving it.
- It builds Composite trees well.

## Idiomatic form in TS
First an **options object** with named fields and default values (`create({ from, to, sort = 'price' })`).
Chained methods return `this` — builder subclasses then keep the correct type (lang-typescript).

## Example (TS)
```ts
type SortOrder = 'price' | 'distance';

type BookingSearch = Readonly<{
  from: Date;
  to: Date;
  resourceTypes: readonly string[];
  minCapacity?: number;
  sort: SortOrder;
}>;

class BookingSearchBuilder {
  #from: Date | undefined;
  #to: Date | undefined;
  #types: string[] = [];
  #minCapacity: number | undefined;
  #sort: SortOrder = 'price';

  between(from: Date, to: Date): this {
    this.#from = from;
    this.#to = to;
    return this;
  }
  ofType(type: string): this {
    this.#types.push(type);
    return this;
  }
  forAtLeast(people: number): this {
    this.#minCapacity = people;
    return this;
  }
  sortedBy(sort: SortOrder): this {
    this.#sort = sort;
    return this;
  }

  build(): BookingSearch {
    if (this.#from === undefined || this.#to === undefined) throw new Error('missing time range');
    if (this.#to <= this.#from) throw new RangeError('the end must be after the start');
    return {
      from: this.#from,
      to: this.#to,
      resourceTypes: [...this.#types],
      sort: this.#sort,
      ...(this.#minCapacity !== undefined ? { minCapacity: this.#minCapacity } : {}),
    };
  }
}

/** A "director" as a function: a repeatable recipe for a search. */
function lastMinute(builder: BookingSearchBuilder, now: Date): BookingSearch {
  const in48h = new Date(now.getTime() + 48 * 3_600_000);
  return builder.between(now, in48h).sortedBy('distance').build();
}

const custom = new BookingSearchBuilder()
  .between(new Date('2026-10-01'), new Date('2026-10-03'))
  .ofType('room')
  .forAtLeast(12)
  .build();
console.log(custom, lastMinute(new BookingSearchBuilder(), new Date()));
```

## When NOT to use / pitfalls
- **2–3 optional parameters** — an options object (`{ url: string; method?: string }`) is shorter and more readable than
  a class with chained methods.
- The signal that a Builder pays off: several repeatable build sequences or steps deferred in time, conditional,
  recursive. One call with the complete data → an ordinary function (`critique-and-pitfalls.md`).
- A builder without validation in `build()` is just a long-winded constructor — all the value lies in the guarantee of a complete
  product.
