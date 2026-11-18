# Abstract Factory

Category: creational. The essence: one object creates **a whole family** of collaborating objects that must
fit together; the client knows only the interfaces.

## Problem
An invoicing system supports several countries. The tax rate, the document numbering and the date format must come from **the same**
jurisdiction — Polish numbering with German VAT is a legal mistake, not an aesthetic one. When the client picks
the elements itself (`new PolishNumbering()`, `new GermanTax()`), it is easy to mix them up, and every new country spreads `if (country)`
across the code.

## Solution and participants
- **Abstract products** — an interface for each element of the family (`TaxPolicy`, `InvoiceNumbering`).
- **Abstract factory** — an interface with a creating method for each product (`InvoicingKit`).
- **Concrete factories** — one per family (`PolishInvoicing`, `GermanInvoicing`); they return only the products of their own
  family.
- **Client** — gets the factory once (configuration, DI) and from then on does not know which family it works with.

## When to use
- The code works on products from different families, and the consistency of the family is a rule (jurisdiction, platform, UI theme).
- Families are really being added, or there are several of them from the start.
- A class accumulates many factory methods that obscure its main responsibility — a signal to extract them.

## Costs
Many interfaces and classes; adding **a new product type** requires changing the factory interface and all factories.

## Relations
- Usually a set of Factory Methods in one interface; the methods can also clone Prototypes.
- A Builder assembles one complex object in steps; an Abstract Factory hands over finished products immediately.
- With Bridge: the factory can create matching abstraction–implementation pairs.
- A Facade also hides complexity, but does not specialize in creation.

## Idiomatic form in TS
The factory can be an ordinary object satisfying the interface (`const polishKit = { taxPolicy, numbering } satisfies
InvoicingKit`), chosen from a `Record<Country, InvoicingKit>` map. Add classes when the factory has dependencies.

## Example (TS)
```ts
interface TaxPolicy {
  vatCents(netCents: number): number;
}
interface InvoiceNumbering {
  next(sequence: number, issuedAt: Date): string;
}

/** Abstract factory: a family of elements of one jurisdiction. */
interface InvoicingKit {
  taxPolicy(): TaxPolicy;
  numbering(): InvoiceNumbering;
}

class PolishInvoicing implements InvoicingKit {
  taxPolicy(): TaxPolicy {
    return { vatCents: (net) => Math.round(net * 0.23) };
  }
  numbering(): InvoiceNumbering {
    return {
      next: (seq, at) => `FV/${seq}/${String(at.getMonth() + 1).padStart(2, '0')}/${at.getFullYear()}`,
    };
  }
}

class GermanInvoicing implements InvoicingKit {
  taxPolicy(): TaxPolicy {
    return { vatCents: (net) => Math.round(net * 0.19) };
  }
  numbering(): InvoiceNumbering {
    return { next: (seq, at) => `RE-${at.getFullYear()}-${String(seq).padStart(6, '0')}` };
  }
}

// Client: does not know the concrete classes, cannot mix up the families.
// (In a real model the amounts are a Money value object — ddd-archetypes, quantity-money.)
function issueInvoice(kit: InvoicingKit, sequence: number, netCents: number) {
  const taxCents = kit.taxPolicy().vatCents(netCents);
  return {
    number: kit.numbering().next(sequence, new Date()),
    netCents,
    taxCents,
    grossCents: netCents + taxCents,
  };
}

const kits = { PL: new PolishInvoicing(), DE: new GermanInvoicing() } satisfies Record<string, InvoicingKit>;
console.log(issueInvoice(kits.PL, 42, 10_000));
console.log(issueInvoice(kits.DE, 42, 10_000));
```

## When NOT to use / pitfalls
- **You create one product, not a family** → that is a Factory Method or an ordinary function.
- **One family with no prospect of a second** — a structure "just in case" is the classic hammer from `critique-and-pitfalls.md` (point 3):
  the cost of interfaces without a gain.
- With 2–3 fixed families a function returning an object literal (`{ taxPolicy, numbering }`) is usually enough.
- New product **types** appear more often than new **families** — the pattern works opposite to the need (every
  new type changes all factories).
