# Singleton

Category: creational. The essence: the class makes sure that **one** instance exists and gives global access to it.
In practice this is the pattern we most often **advise against** — read the pitfalls section as the main part of the file.

## Problem
The pattern combines two independent needs (and therefore violates SRP):
1. **A guarantee of one instance** — two copies would break the program (e.g. one local flag registry, one connection pool
   in the process).
2. **A global access point** — like a global variable, but protected from being overwritten.
Solutions that meet only point 2 are often called a singleton — that blurs the concept.

## Solution and participants
A private constructor blocks `new` from the outside; a static field holds the instance; a static accessor creates it lazily
on first use and then returns the same one.

## When to use
- The program is entitled to have exactly one object of a given class and **two would really break it**.
- You need tighter control over something that would otherwise be a mutable global variable.

## Costs
- Hidden dependencies: the function signature does not show that it reaches for a singleton.
- Hard tests: you cannot easily substitute a replacement, state leaks between tests.
- It masks a bad division of responsibilities — everyone reaches for everything.
- In multi-threaded environments (other languages) it requires synchronization at creation.

## Relations
- A Facade is sometimes the only instance — but that is a decision of the application's composition, not of the class.
- A Flyweight also shares objects, but has **many** immutable instances; a singleton has one, often mutable.
- Concrete factories/builders are sometimes the only instances — usually one object injected through DI is enough.

## Idiomatic form in TS
**An ES module executes once** — an exported constant is shared by everyone who imports it. In applications
with a DI container "one instance" is the provider's scope (fw-*), not a trait of the class. The classic private constructor is
most often a transfer of an idiom from languages without modules.

## Example (TS)
The idiomatic variant — an instance at the module level, injected explicitly wherever possible:
```ts
// metrics.ts — the module executes once, `metrics` is shared
const counters = new Map<string, number>();

export const metrics = {
  inc(name: string, by = 1): void {
    counters.set(name, (counters.get(name) ?? 0) + by);
  },
  snapshot(): ReadonlyMap<string, number> {
    return new Map(counters);
  },
};
```
The classic variant (when you really need to enforce one instance in the class) — `#` fields are private also at runtime:
```ts
class FeatureFlags {
  static #instance: FeatureFlags | undefined;
  #enabled = new Set<string>();

  private constructor() {}

  static get instance(): FeatureFlags {
    return (FeatureFlags.#instance ??= new FeatureFlags());
  }

  enable(flag: string): void {
    this.#enabled.add(flag);
  }
  isOn(flag: string): boolean {
    return this.#enabled.has(flag);
  }
}

FeatureFlags.instance.enable('new-pricing');
console.log(FeatureFlags.instance === FeatureFlags.instance, FeatureFlags.instance.isOn('new-pricing'));
```

## When NOT to use / pitfalls
- Ask: do I need to **enforce** one instance (because two will break the program), or just **convenient** access? The second
  does not justify the pattern — an explicitly injected/imported object is testable.
- In TS/JS instead of a class with `getInstance()` use a module instance; in a framework with DI — the provider's scope. Do not duplicate
  the framework's mechanism with a manual singleton on a service class.
- Global **mutable** state is a source of flaky tests; if it really must exist, give it an interface and inject it, and
  keep the singleton only at the application's composition root.
- An ES module is "one" per module loader instance — with micro-frontends, workers or duplicated packages
  in `node_modules` you can get several copies.
