# State

> **Contents:** Problem · Solution and participants · When to use · Costs · Relations · Idiomatic form in TS · Example (TS) · When NOT to use / pitfalls

Category: behavioral. The essence: each state of an object is a separate object with **its own behaviour**; the context delegates
to the current state, and the states themselves decide on the transitions.

## Problem
A reservation goes through "pending → confirmed → checked in / cancelled". The methods `confirm()`, `cancel()`,
`checkIn()` contain the same `switch (status)` with a growing number of branches; the cancellation fee depends on the state
and the time. Adding a "no-show" state requires editing every method, and it is easy to miss one branch.

## Solution and participants
- **Context** — holds the current state, delegates operations to it, exposes the transition (`transitionTo()`).
- **State interface** — the state-dependent operations.
- **Concrete states** — the behaviour in a given state and the decision about the next one; they can have their own data (e.g. the time
  of confirmation).

## When to use
- The same state fields drive branching in many methods of one class.
- The states have **different, non-trivial behaviour** (not only different data) or their own dependencies.
- The number of states grows or the states are to be extended independently.

## Costs
Many small classes; with a few simple states — an overgrown form; transitions scattered across the state classes are harder
to see in one place than in a transition table.

## Relations
- **Strategy** has the same shape, but strategies do not know each other and the client chooses them; states change by themselves.
- **A state machine** in the domain model (ddd-tactical-design) — explicit transitions instead of scattered `if (status == …)`;
  this file is one of the techniques for implementing it.
- **Bridge/Adapter** — also composition + delegation, different problems.

## Idiomatic form in TS
**A discriminated union + an exhaustive `switch`** (or a transition map) is the first choice when the states differ
mainly in data and allowed transitions — the compiler enforces completeness (lang-typescript). State classes — when
each state has its own, extensive logic.

## Example (TS)
State classes:
```ts
interface ReservationState {
  readonly name: string;
  confirm(reservation: Reservation): void;
  /** Returns the cancellation fee in grosze (cents). */
  cancel(reservation: Reservation, now: Date): number;
}

class Pending implements ReservationState {
  readonly name = 'pending';
  confirm(r: Reservation): void {
    r.transitionTo(new Confirmed(new Date()));
  }
  cancel(r: Reservation): number {
    r.transitionTo(new Cancelled());
    return 0;
  }
}

class Confirmed implements ReservationState {
  readonly name = 'confirmed';
  readonly #confirmedAt: Date;
  constructor(confirmedAt: Date) {
    this.#confirmedAt = confirmedAt;
  }
  confirm(): void {
    throw new Error('reservation already confirmed');
  }
  cancel(r: Reservation, now: Date): number {
    const hours = (now.getTime() - this.#confirmedAt.getTime()) / 3_600_000;
    r.transitionTo(new Cancelled());
    return hours <= 24 ? 0 : 5_000;
  }
}

class Cancelled implements ReservationState {
  readonly name = 'cancelled';
  confirm(): void {
    throw new Error('cannot confirm a cancelled reservation');
  }
  cancel(): number {
    return 0;
  }
}

class Reservation {
  #state: ReservationState = new Pending();

  get status(): string {
    return this.#state.name;
  }
  /** Called only by the states; in larger code hide it from clients (a separate interface). */
  transitionTo(next: ReservationState): void {
    this.#state = next;
  }
  confirm(): void {
    this.#state.confirm(this);
  }
  cancel(now = new Date()): number {
    return this.#state.cancel(this, now);
  }
}

const reservation = new Reservation();
reservation.confirm();
console.log(reservation.status, reservation.cancel(), reservation.status);
```
The union form — often more readable in TS:
```ts
type OrderState =
  | { kind: 'pending' }
  | { kind: 'shipped'; trackingId: string }
  | { kind: 'delivered'; deliveredAt: Date };

function advance(state: OrderState, trackingId: string): OrderState {
  switch (state.kind) {
    case 'pending':
      return { kind: 'shipped', trackingId };
    case 'shipped':
      return { kind: 'delivered', deliveredAt: new Date() };
    case 'delivered':
      return state; // the final state
  }
}
console.log(advance({ kind: 'pending' }, 'PL123'));
```

## When NOT to use / pitfalls
- **2–3 fixed states** — an `if`/`switch` without a pattern is often the most readable.
- The states differ only in data → a discriminated union; state classes when the behaviour is really different.
- A public `transitionTo()` lets clients bypass the rules — limit access (an interface for the states, a module).
- Persistent state: when saving to the database, map the state to a value (name + data) and back — state classes are not the persistence
  model.
