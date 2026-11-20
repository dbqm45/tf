# Template Method

Category: behavioral. The essence: the base class fixes **the unchanging skeleton of the algorithm**, and subclasses override selected
steps (required, optional and hook points).

## Problem
A monthly statement for an individual and a business customer: both collect operations, add fees, sum up,
format and send. They differ in the source of the operations, the fees and the format. Two copies of the whole process diverge
with every change (e.g. a new audit step added only in one of them).

## Solution and participants
- **Base class** — the template method (the order of the steps) and the steps:
  - **abstract** — each subclass must provide them,
  - **with a default implementation** — a subclass may override them,
  - **hook points (hooks)** — empty, for optional extension at a specific place.
- **Concrete classes** — implement the steps; they do not change the template method itself.

## When to use
- Several classes have an almost identical algorithm differing in a few, well-isolated steps.
- You want to allow extending only selected steps of the process, and protect the order and the shared steps (audit, validation).
- Frameworks: a component/request life cycle with hooks.

## Costs
Inheritance binds the variants statically; a fixed skeleton limits clients that need a different order; a growing
number of hooks makes understanding harder; a risk of breaking LSP when a subclass violates the skeleton's assumptions.

## Relations
- **Strategy** — the same through composition (dynamically); often better in TS.
- **Factory Method** is a special case: the "create an object" step.
- eng-design-principles: composition over inheritance — Template Method is a deliberate exception with a stable skeleton.

## Idiomatic form in TS
TS has no `final` — the skeleton is protected by convention and review (or by not using inheritance). An alternative without classes:
**a skeleton function taking a steps object** (`runStatement(steps, account)`), where the optional steps have default
values.

## Example (TS)
```ts
type Entry = { date: Date; amountCents: number; description: string };

abstract class StatementJob {
  /** The template method — do not override (convention: TS has no `final`). */
  run(accountId: string, month: string): string {
    const entries = this.collect(accountId, month);
    const all = [...entries, ...this.fees(entries)];
    const totalCents = all.reduce((sum, e) => sum + e.amountCents, 0);
    this.beforeRender(accountId, totalCents);
    return this.render(accountId, month, all, totalCents);
  }

  /** A required step. */
  protected abstract collect(accountId: string, month: string): Entry[];
  /** A required step. */
  protected abstract render(accountId: string, month: string, entries: readonly Entry[], totalCents: number): string;
  /** A step with a default implementation. */
  protected fees(_entries: readonly Entry[]): Entry[] {
    return [];
  }
  /** A hook point. */
  protected beforeRender(_accountId: string, _totalCents: number): void {}
}

class RetailStatement extends StatementJob {
  protected collect(_accountId: string, month: string): Entry[] {
    return [{ date: new Date(`${month}-05`), amountCents: -12_000, description: 'Court booking' }];
  }
  protected render(accountId: string, month: string, entries: readonly Entry[], total: number): string {
    return `${accountId} ${month}: ${entries.length} operations, balance ${(total / 100).toFixed(2)} PLN`;
  }
}

class BusinessStatement extends StatementJob {
  protected collect(_accountId: string, month: string): Entry[] {
    return [
      { date: new Date(`${month}-02`), amountCents: -250_000, description: 'Conference room' },
      { date: new Date(`${month}-20`), amountCents: -80_000, description: 'Catering' },
    ];
  }
  protected override fees(entries: readonly Entry[]): Entry[] {
    return entries.length > 1 ? [{ date: new Date(), amountCents: -2_000, description: 'Statement fee' }] : [];
  }
  protected override beforeRender(accountId: string, totalCents: number): void {
    if (totalCents < -300_000) console.log(`audit: high balance on ${accountId}`);
  }
  protected render(accountId: string, month: string, entries: readonly Entry[], total: number): string {
    const lines = entries.map((e) => `  ${e.description}: ${(e.amountCents / 100).toFixed(2)}`);
    return [`Statement ${accountId} for ${month}`, ...lines, `Total: ${(total / 100).toFixed(2)} PLN`].join('\n');
  }
}

for (const job of [new RetailStatement(), new BusinessStatement()]) console.log(job.run('ACC-1', '2026-09'));
```

## When NOT to use / pitfalls
- The differences between the variants are in many places and cannot be isolated into a few steps — a shared base forces you to
  read two classes at once to understand one path. Choose composition (Strategy).
- The steps are to change at runtime, not only when choosing the class → Strategy.
- Watch LSP: a subclass overriding a step must not break the skeleton's assumptions (e.g. the expected order of side
  effects) — such bugs are hard to notice, because `run()` looks the same for every subclass.
- A deep hierarchy (a template within a template) is a signal to move to composition.
