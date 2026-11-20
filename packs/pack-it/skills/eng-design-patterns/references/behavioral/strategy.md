# Strategy

Category: behavioral. The essence: interchangeable variants of an algorithm or a rule behind **a shared interface**; the context
delegates, and the choice of the variant belongs to the client or the configuration.

## Problem
A cart computes a discount: none, a volume discount, a loyalty discount depending on seniority, a seasonal promotion. All the variants
in one method with a `switch (promoType)` mean that every new promotion changes the cart's code, the tests cover the whole thing
at once, and two people editing promotions conflict in the same file.

## Solution and participants
- **Strategy** — the variant's interface (in TS most often a function type).
- **Concrete strategies** — the variants of the algorithm.
- **Context** — holds the strategy and delegates; it does not choose it itself.
- **Client** — picks the strategy (configuration, DI, a selection rule).

## When to use
- Several variants of the same task, interchangeable at runtime or per configuration.
- You want to remove a big condition choosing the algorithm and test the variants separately.
- The variants change independently of the code that uses them.
- **A policy** in DDD (discounting, charging penalties, allocation) is a strategy named in the business language
  (ddd-tactical-design); in the price-calculation archetype the price variants are policies (ddd-archetypes).

## Costs
The client must know the differences between the variants in order to choose; with 2 rarely changed variants — overkill.

## Relations
- **State** — the same shape, but states know each other and change by themselves; strategies are independent.
- **Template Method** — interchangeable steps through inheritance (statically); Strategy — through composition (dynamically).
- **Command** parameterizes with an *action*; Strategy with a *way* of execution. **Decorator** changes the shell, Strategy the inside.

## Idiomatic form in TS
A strategy is usually a **function** with a named type. A strategy class — when the variant has its own dependencies (a repository,
an HTTP client) or state injected in the constructor.

## Example (TS)
```ts
type CartLine = { sku: string; unitCents: number; qty: number };
type Cart = { lines: readonly CartLine[]; customerSince: Date };

/** Strategy (a discount policy): returns the discount in grosze (cents). */
type DiscountPolicy = (cart: Cart, today: Date) => number;

const subtotal = (cart: Cart): number => cart.lines.reduce((sum, l) => sum + l.unitCents * l.qty, 0);

const noDiscount: DiscountPolicy = () => 0;

const volumeDiscount =
  (thresholdCents: number, rate: number): DiscountPolicy =>
  (cart) =>
    subtotal(cart) >= thresholdCents ? Math.round(subtotal(cart) * rate) : 0;

const loyaltyDiscount: DiscountPolicy = (cart, today) => {
  const years = (today.getTime() - cart.customerSince.getTime()) / (365 * 86_400_000);
  return Math.round(subtotal(cart) * Math.min(0.1, 0.02 * Math.floor(years)));
};

/** A combination of strategies: the best discount for the customer. */
const bestOf =
  (...policies: DiscountPolicy[]): DiscountPolicy =>
  (cart, today) =>
    Math.max(0, ...policies.map((p) => p(cart, today)));

class Checkout {
  #policy: DiscountPolicy;
  constructor(policy: DiscountPolicy = noDiscount) {
    this.#policy = policy;
  }
  usePolicy(policy: DiscountPolicy): void {
    this.#policy = policy;
  }
  totalCents(cart: Cart, today = new Date()): number {
    const gross = subtotal(cart);
    return gross - Math.min(gross, this.#policy(cart, today));
  }
}

const cart: Cart = { lines: [{ sku: 'COFFEE', unitCents: 4_900, qty: 12 }], customerSince: new Date('2021-03-01') };
const checkout = new Checkout(bestOf(volumeDiscount(50_000, 0.05), loyaltyDiscount));
console.log(checkout.totalCents(cart, new Date('2026-09-27')));
```

## When NOT to use / pitfalls
- In TS/JS do not build an `interface Strategy` + classes for variants that are pure functions — a function type gives the same
  interchangeability without new files and `new` (`critique-and-pitfalls.md`, point 1).
- One algorithm without a real second variant — do not introduce an interface "for the future".
- If the strategies start to know each other and switch to one another, it is in reality a **State**.
- Choosing the strategy is also a rule — do not scatter it across the code; one place (a factory, configuration, a selection policy).
