# Prototype

Category: creational. The essence: the object **itself knows how to copy itself**; the client clones it through an interface, without knowing
the concrete class or the private fields.

## Problem
The legal department maintains several configured contract templates (clauses, metadata, versions). A new contract is a copy
of a template with small changes. Copying "from the outside" does not see the private fields, requires knowing the concrete class
and easily ends with a shallow copy in which changing a clause in the contract breaks the template.

## Solution and participants
- **Prototype** — an interface with `clone()`.
- **Concrete prototype** — implements `clone()` inside the class (it has access to the `#private` fields) and itself decides what
  to copy deeply (collections, nested objects, back references).
- **Prototype registry (optional)** — a `name → ready prototype` map, returning clones.

## When to use
- The code gets objects through an interface and must copy them without knowing the class.
- Instead of many subclasses that differ only in configuration — a few configured instances to clone.
- Creating the object from scratch is expensive (computations, loading), and a copy of a ready one is cheap.

## Costs
Correctly cloning complex graphs (cycles, shared references, resources) can be hard; every new field in the class
requires remembering about `clone()`.

## Relations
- An alternative to Factory Method (it does not require creator subclasses); an Abstract Factory can clone prototypes.
- It helps copy Composite trees and stacks of Decorators; a history of Commands can store copies.
- A simple alternative to Memento, when the object can simply be cloned.

## Idiomatic form in TS
For data without methods and private state: `structuredClone(obj)` (a deep copy, handles cycles, `Map`, `Date`) or
spread `{ ...obj }` (shallow). Immutable objects do not need a copy at all — share them.

## Example (TS)
```ts
interface Cloneable<T> {
  clone(): T;
}

class ContractTemplate implements Cloneable<ContractTemplate> {
  #clauses: string[];
  #meta: Map<string, string>;

  constructor(clauses: readonly string[], meta: ReadonlyMap<string, string> = new Map()) {
    this.#clauses = [...clauses];
    this.#meta = new Map(meta);
  }

  withClause(text: string): this {
    this.#clauses.push(text);
    return this;
  }
  tag(key: string, value: string): this {
    this.#meta.set(key, value);
    return this;
  }

  /** A copy made inside the class: it sees the #private fields, copies the collections deeply. */
  clone(): ContractTemplate {
    return new ContractTemplate(this.#clauses, this.#meta);
  }

  render(): string {
    return this.#clauses.map((clause, i) => `§${i + 1}. ${clause}`).join('\n');
  }
}

const registry = new Map<string, ContractTemplate>([
  ['room-rental', new ContractTemplate(['Subject of the rental', 'Rent', 'Deposit']).tag('version', '3')],
  ['it-service', new ContractTemplate(['Scope of services', 'SLA', 'Confidentiality']).tag('version', '7')],
]);

function contractFrom(name: string): ContractTemplate {
  const prototype = registry.get(name);
  if (prototype === undefined) throw new Error(`unknown template: ${name}`);
  return prototype.clone();
}

const contract = contractFrom('room-rental').withClause('Contractual penalty');
console.log(contract.render());
console.log(contractFrom('room-rental').render()); // the template unchanged
```

## When NOT to use / pitfalls
- **Flat DTOs and configuration objects** — `structuredClone`/spread is enough; a `clone()` interface and a registry make
  sense with private state, deep class hierarchies or cyclic references.
- "Avoiding `new`" is not a reason. Check whether you really copy **without knowing the class**, or just copy data.
- Watch out for shallow copies of collections — an array shared between the prototype and the clone is a classic mistake.
- `structuredClone` loses the class prototype (methods) — for class instances use `clone()` from the class.
