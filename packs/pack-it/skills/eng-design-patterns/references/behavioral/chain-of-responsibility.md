# Chain of Responsibility

> **Contents:** Problem · Solution and participants · When to use · Costs · Relations · Idiomatic form in TS · Example (TS) · When NOT to use / pitfalls

Category: behavioral. The essence: a request passes through a sequence of handlers; each one **handles it or passes it
on** (and can stop the flow). The sender does not know who finally handled it.

## Problem
An expense is approved by a person with the right limit: a team lead up to 1,000 PLN, a director up to 10,000 PLN, the board above that;
the "IT equipment" category always goes through the IT department. One function with nested `if`s grows with every change
in the company's structure, and the configuration differs between companies.

## Solution and participants
- **Handler** — the shared interface `handle(request)`.
- **Base handler (optional)** — holds a reference to the next link and by default passes the request on.
- **Concrete handlers** — decide: handle it or pass it on.
- **Client** — assembles the chain (the order matters) and can reconfigure it at runtime.

## When to use
- The order and the set of steps change (configuration, per customer, at runtime).
- It is not known up front which step will handle the request, and the first suitable one is to "take" it.
- Middleware, validators with early termination, propagation of UI events up the tree.

## Costs
A request can pass through without being handled — an explicit "nobody handled it" result is needed; debugging the path through many links.

## Relations
- **Decorator** has the same shape, but always delegates further; a chain link can interrupt.
- **Command** is sometimes the request travelling through the chain; **Composite** — a chain from a leaf to the root.
- **Command, Mediator, Observer** — other ways of connecting senders with receivers.

## Idiomatic form in TS
**An array of functions** and `for`/`find` with an early exit; the `(ctx, next) => …` middleware known from HTTP frameworks is this
pattern built in.

## Example (TS)
```ts
type Expense = { amountCents: number; category: string };
type Decision = { approvedBy: string } | { rejected: string };

abstract class Approver {
  #next: Approver | undefined;
  protected abstract readonly role: string;
  protected abstract canApprove(expense: Expense): boolean;

  /** Returns the next link, so that the chain can be assembled fluently. */
  then(next: Approver): Approver {
    this.#next = next;
    return next;
  }

  handle(expense: Expense): Decision {
    if (this.canApprove(expense)) return { approvedBy: this.role };
    return this.#next?.handle(expense) ?? { rejected: 'nobody in the chain can approve' };
  }
}

class ItDepartment extends Approver {
  protected readonly role = 'IT department';
  protected canApprove(e: Expense): boolean {
    return e.category === 'IT equipment' && e.amountCents <= 2_000_000;
  }
}
class TeamLead extends Approver {
  protected readonly role = 'team lead';
  protected canApprove(e: Expense): boolean {
    return e.category !== 'IT equipment' && e.amountCents <= 100_000;
  }
}
class Director extends Approver {
  protected readonly role = 'director';
  protected canApprove(e: Expense): boolean {
    return e.category !== 'IT equipment' && e.amountCents <= 1_000_000;
  }
}

const chain = new ItDepartment();
chain.then(new TeamLead()).then(new Director());

console.log(chain.handle({ amountCents: 50_000, category: 'training' }));
console.log(chain.handle({ amountCents: 5_000_000, category: 'training' }));
```
The functional form:
```ts
type Expense = { amountCents: number; category: string };
type Rule = (e: Expense) => string | undefined; // returns a role or undefined = "pass it on"

const rules: readonly Rule[] = [
  (e) => (e.amountCents <= 100_000 ? 'team lead' : undefined),
  (e) => (e.amountCents <= 1_000_000 ? 'director' : undefined),
];

function approve(e: Expense): string {
  for (const rule of rules) {
    const role = rule(e);
    if (role !== undefined) return role;
  }
  return 'board';
}
console.log(approve({ amountCents: 300_000, category: 'training' }));
```

## When NOT to use / pitfalls
- **A fixed, short sequence** — `a(); b(); c();` or an array of functions is more readable than objects with `setNext()`.
  A class chain makes sense with real reconfiguration at runtime.
- The framework already has middleware/interceptors — do not build a parallel infrastructure.
- Every request **must** go through all the steps (without interruption) → that is a pipeline/function composition, not a chain.
- Approval rules are business knowledge — it is often better to model them as policies/specifications in the domain
  (ddd-tactical-design), and leave the chain to the infrastructure.
