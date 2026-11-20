# Memento

> **Contents:** Problem · Solution and participants · When to use · Costs · Relations · Idiomatic form in TS · Example (TS) · When NOT to use / pitfalls

Category: behavioral. The essence: the object itself takes **a snapshot of its state** and itself restores from it; someone else
stores the snapshots, but does not see their content.

## Problem
A sales offer editor has private state (line items, negotiation discounts, internal notes) and needs "undo"
and "restore the version from before the negotiation". Copying the state from the outside requires making the fields public — anyone could
change them, and every refactoring of the class would break the code that makes the copies.

## Solution and participants
- **Originator** — creates a snapshot and restores itself from it; only it knows its content.
- **Memento** — an immutable snapshot; on the outside it exposes at most metadata (time, label).
- **Caretaker** — the history of snapshots (a stack, a limit); it decides when, but does not look inside.

## When to use
- Undo/redo, drafts, restore points — without breaking encapsulation.
- Rolling back changes to an in-memory object after a failed multi-step operation.

## Costs
Memory with frequent snapshots of large objects; the caretaker must remove stale ones; in JS immutability and privacy are
real only with `#fields`, `Object.freeze` and opaque types.

## Relations
- **Command** + Memento — the command saves a snapshot before executing, to be able to undo.
- **Prototype** — a simpler alternative when the object can simply be cloned.
- **Iterator** — a snapshot of the iteration position.
- Event sourcing (decider — ddd-tactical-design) rebuilds the state from events — a different mechanism of "going back in time".

## Idiomatic form in TS
When the state is **immutable** (a new object on every change — the reducer/store style), the history is simply
an array of previous states. An opaque memento type: a type brand + a `WeakMap` with the actual state in the originator's module.

## Example (TS)
```ts
declare const snapshotBrand: unique symbol;
/** An opaque memento: only the metadata is visible from the outside. */
type OfferSnapshot = { readonly takenAt: Date; readonly label: string; readonly [snapshotBrand]: true };

type OfferState = { title: string; lines: { sku: string; qty: number; discount: number }[] };

// The content of the snapshots is available only in this module (at the originator).
const contents = new WeakMap<OfferSnapshot, OfferState>();

class OfferDraft {
  #state: OfferState = { title: '', lines: [] };

  rename(title: string): void {
    this.#state.title = title;
  }
  addLine(sku: string, qty: number, discount = 0): void {
    this.#state.lines.push({ sku, qty, discount });
  }
  summary(): string {
    return `${this.#state.title}: ${this.#state.lines.map((l) => `${l.qty}×${l.sku}`).join(', ')}`;
  }

  save(label: string): OfferSnapshot {
    const snapshot = Object.freeze({ takenAt: new Date(), label }) as OfferSnapshot;
    contents.set(snapshot, structuredClone(this.#state));
    return snapshot;
  }
  restore(snapshot: OfferSnapshot): void {
    const state = contents.get(snapshot);
    if (state === undefined) throw new Error('foreign snapshot');
    this.#state = structuredClone(state);
  }
}

/** Caretaker: stores the snapshots with a limit, does not know their content. */
class DraftHistory {
  readonly #stack: OfferSnapshot[] = [];
  readonly #limit: number;
  constructor(limit = 20) {
    this.#limit = limit;
  }
  push(snapshot: OfferSnapshot): void {
    this.#stack.push(snapshot);
    if (this.#stack.length > this.#limit) this.#stack.shift();
  }
  pop(): OfferSnapshot | undefined {
    return this.#stack.pop();
  }
}

const draft = new OfferDraft();
const history = new DraftHistory();
draft.rename('Offer for ACME');
draft.addLine('ROOM-A', 2);
history.push(draft.save('before negotiation'));
draft.addLine('CATERING', 30, 0.15);
const previous = history.pop();
if (previous !== undefined) draft.restore(previous);
console.log(draft.summary(), '| restored:', previous?.label);
```

## When NOT to use / pitfalls
- **The state is already immutable** — an array of previous states gives undo without Memento/Caretaker classes.
- **Flat DTOs without private state** — `structuredClone` on a change is enough; the full pattern makes sense when the
  originator's state is private and should not be visible to the caretaker.
- Set the history limit right away (the last N) — an unbounded history of large objects is a real memory cost.
- A snapshot does not cover the outside world (saved records, sent messages) — compensation is needed there.
