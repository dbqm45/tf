# Iterator

Category: behavioral. The essence: a uniform way of traversing the elements of a collection **without exposing its
internal structure**; each iterator has its own position.

## Problem
Report code traverses orders from an API paginated with a cursor, a tree of organizational units and
an in-memory array. The logic "fetch the next page, check the cursor, descend to the children" mixes with the report's logic
and is repeated at every place of use; changing the API from an offset to a cursor breaks all the clients.

## Solution and participants
- **Iterator** — gives the next element and information about the end; stores its own iteration state.
- **Collection** — creates iterators (possibly of several kinds: depth-first, breadth-first, in reverse).
- **Client** — knows only the iteration protocol.

## When to use
- You want to hide the representation of the collection (a list, a tree, a graph, a paginated API) so that you can change it.
- You need several ways of traversal or several independent, simultaneous positions.
- The data is large or infinite — lazy iteration instead of loading everything.

## Costs
Unnecessary with simple collections; sometimes slower than specialized access.

## Relations
- Traversing **Composite** trees; **Visitor** performs an operation on the visited elements.
- A collection can create an iterator with a **Factory Method**; a **Memento** can save the iteration position.

## Idiomatic form in TS
The protocol is **built into the language**: `Symbol.iterator`/`Symbol.asyncIterator`, `for…of`/`for await…of`, spread,
`function*`/`async function*` generators, and since ES2025 the iterator helper methods (`Iterator.prototype.map`,
`filter`, `take` — check the target/lib in lang-typescript). A manual class with `current()/next()/valid()` is the form for
languages without the protocol.

## Example (TS)
A paginated API as a lazy stream of elements:
```ts
type Page<T> = { items: readonly T[]; next?: string };

async function* allItems<T>(fetchPage: (cursor?: string) => Promise<Page<T>>): AsyncGenerator<T> {
  let cursor: string | undefined;
  do {
    const page = await fetchPage(cursor);
    yield* page.items;
    cursor = page.next;
  } while (cursor !== undefined);
}

// A fake API: 3 pages of 2 elements each.
const fakeApi = async (cursor?: string): Promise<Page<number>> => {
  const n = Number(cursor ?? '0');
  return n < 2 ? { items: [n * 2, n * 2 + 1], next: String(n + 1) } : { items: [n * 2, n * 2 + 1] };
};

for await (const orderId of allItems(fakeApi)) {
  if (orderId > 3) break; // the client stops — the next pages are not fetched
  console.log('order', orderId);
}
```
A tree collection with its own traversal order:
```ts
class OrgUnit implements Iterable<OrgUnit> {
  readonly name: string;
  readonly #children: OrgUnit[] = [];

  constructor(name: string) {
    this.name = name;
  }
  add(...units: OrgUnit[]): this {
    this.#children.push(...units);
    return this;
  }
  /** Depth-first traversal (pre-order). */
  *[Symbol.iterator](): Generator<OrgUnit> {
    yield this;
    for (const child of this.#children) yield* child;
  }
}

const company = new OrgUnit('Board').add(
  new OrgUnit('Sales').add(new OrgUnit('North Region')),
  new OrgUnit('IT'),
);
console.log([...company].map((u) => u.name).join(' → '));
```

## When NOT to use / pitfalls
- An array, `Map`, `Set`, `string` are already iterable — do not add anything.
- Do not write an iterator class when a generator does the same in a few lines.
- A custom iterator class makes sense with many **simultaneously live, independent positions** with additional operations
  (e.g. going back, remembering the position).
- Modifying the collection during iteration — define the behaviour (copy, forbid or document), otherwise the bugs are
  non-deterministic.
