# Critique of patterns and the pitfalls of overuse

This part is as important as the catalog: its goal is **not to propose a pattern where simpler code is better**.

## 1. A pattern as a patch for a missing language feature
A well-known objection (among others Paul Graham, Peter Norvig): some patterns exist because the language they were written down for did not have
the right abstraction. In languages with functions as values, closures and modules, many patterns shrink to
a few lines:

| Pattern | A lighter form in TS/JS |
|---|---|
| Strategy | a function passed as a parameter (a function type) |
| Command | a closure `() => void` in an array/map; the command's data as a discriminated union |
| Factory Method | a factory function or a passed creating function |
| Singleton | an instance at the ES module level / a DI provider scope |
| Iterator | `Symbol.iterator`, generators, `for…of` |
| Observer | `EventTarget`, `EventEmitter`, RxJS, framework signals |
| Decorator | a higher-order function, middleware |
| State / Visitor | a discriminated union + an exhaustive `switch` |
| Prototype | `structuredClone`, spread, immutable objects |

This does not mean patterns are unnecessary — the **shape** of the implementation should use what the language gives instead of copying
the class structure from a textbook written for C++/Java before lambdas.

## 2. Mechanical application
Patterns describe common approaches, but they are not a dogma to be reproduced point by point. A signal in a review: **the pattern's
structure is visible, the problem** it was meant to solve is not — e.g. an `AbstractFactory` with one family that will never
get a second one. Simplify.

## 3. The hammer and the nails
Whoever has just learned patterns sees them everywhere. A control question: would a solution **without** a pattern (a function, a condition,
a few lines) be shorter and just as clear? If so — that is the answer. A pattern earns its complexity only
when the problem really occurs and recurs, not when it "might come in handy" (YAGNI, the rule of three —
eng-design-principles).

## 4. The cost of complexity
Every layer of indirection is a file and a jump that the reader must get through to understand one execution path.
Code harder to understand than the problem it solves is a regression, not an improvement.

## Checklist before proposing a pattern
1. Can I name a **concrete, recurring** problem in this code (not a hypothetical one)?
2. Does simpler code solve it equally well? If so — simpler code.
3. Does the language give a light form (the table above)? If so — that one, without the full class structure.
4. Is the number of new types/files proportional to the gain on future changes?
5. Does the pattern not duplicate a framework mechanism (DI, middleware, store, signals)?

When (2) or (3) gives "yes", leave the simple code and — if worthwhile — note in the PR which pattern would be the next step
when the problem actually grows.

## Signals of overuse in a review
- an interface with one implementation and no plan for a second one;
- class names with pattern words (`…Factory`, `…Strategy`, `…Visitor`) without the variation they would handle;
- a singleton as convenient global access;
- a stack of decorators/a chain for two fixed steps;
- `accept()`/Visitor for two types and one operation;
- a mediator with a `switch` on dozens of events (a new "god object").
