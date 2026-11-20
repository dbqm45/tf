---
name: eng-design-patterns
description: Use when a GoF pattern tempts you in a project or review — diagnosis symptom → pattern, when not, lighter forms.
disable-model-invocation: true
metadata:
  status: "inactive"  # measurement 2026-11-16: docs/inactive-skills.md
  review: "2027-10-17"
  catalog: "Use when you design or refactor code and consider a GoF pattern, or assess its use in a review — the \"symptom → pattern\" diagnosis, when NOT to use one, the classification, 22 patterns (factories, builder, adapter, decorator, proxy, observer, state, strategy, visitor…) with lighter forms in TS. Not for the SOLID/KISS principles (eng-design-principles) or DDD building blocks (ddd-tactical-design)."
  keywords: "role object, obiekt roli, ta sama osoba w wielu rolach, klient i dostawca, extension object, obiekt rozszerzenia, flagi isCustomer, klasa Person z polami null, każda rola ma inne dane, the same person in many roles, customer and supplier, isCustomer flags, Person class with null fields, each role has different data"
---

# Design patterns (GoF)

A pattern is an answer to **a recognized, recurring problem** — not a goal in itself. Start by naming the problem
in the code; if you cannot name it (variation that recurs, painful coupling, an explosion of subclasses), you do not
need a pattern. Simpler code wins a tie (`references/critique-and-pitfalls.md`).

## How to work
1. **Name the problem, not the pattern**: what requires edits in many places? which `switch` keeps growing? what is hard to test?
2. **Narrow it down by category**: creating objects → creational; static shape and composition → structural; flow over time
   → behavioral (`references/basics.md`).
3. **Pick a candidate** from the table below and read its file — especially "When NOT to use".
4. **Choose the lightest form** the language offers (a function, a closure, a union, a generator, a module) before you reach for
   a textbook class hierarchy.
5. **In a review** propose a pattern only for an identified, recurring problem; in the comment give the problem, the cost
   and a simpler alternative (comment format — eng-design-principles).

## Symptom → candidate
| Symptom in the code | Candidate | Check the lighter one first |
|---|---|---|
| `new` of a concrete class inside logic, a `switch` on type at creation | Factory Method | a factory function |
| elements must come from one "family" (country, platform, theme) | Abstract Factory | a `Record<Family, Kit>` map |
| a constructor with many options, an object assembled conditionally, validation of the whole | Builder | an options object with defaults |
| copying an object without knowing its class, with private state | Prototype | `structuredClone`, immutability |
| "there must be one instance" | Singleton (carefully) | an ES module, a DI scope |
| a third-party API does not fit our port | Adapter | a mapping function |
| classes = the product of two traits (`CsvRevenue`, `PdfRevenue`…) | Bridge | composition of one dimension |
| an element and a group of elements, a tree of arbitrary depth | Composite | a union + recursion |
| retry/cache/log/metrics in various combinations | Decorator | a higher-order function, middleware |
| the caller coordinates 4 modules in a fixed order | Facade | a use case function |
| tens of thousands of objects repeat the same data (measured) | Flyweight | — |
| lazy initialization, permissions, a cache in front of an existing service | Proxy | `??=`, `Map`, `if` |
| "handle it or pass it on", a variable set of steps | Chain of Responsibility | an array of functions |
| actions for a queue, a log, undo | Command | a closure in a map |
| traversing a paginated API/a tree without exposing the structure | Iterator | a generator, `Symbol.iterator` |
| UI components know each other "everyone with everyone" | Mediator | a state container/store |
| undo/versions with private state | Memento | a history of immutable states |
| many recipients of a change, a set that varies at runtime | Observer | `EventTarget`, RxJS, signals |
| the same `switch (status)` in many methods | State | a discriminated union + `switch` |
| a `switch` choosing a variant of an algorithm/rule | Strategy | a function as a parameter |
| several classes with an almost identical process | Template Method | a skeleton function + a steps object |
| new operations on a stable set of node types | Visitor | a union + a function with a `switch` |
| the same entity is a customer, a supplier, an employee; `isX` flags and role data in one class | Role Object (outside GoF) | a separate role object or aggregate pointing to the core |
| interfaces needed only by some clients, added by other modules | Extension Object (outside GoF) | a map of extensions by key |

Pairs that are easy to confuse (the motivation decides, not the shape): Decorator/Proxy, Strategy/State, Adapter/Bridge/Facade,
Chain/Decorator, Mediator/Facade — the "Relations" sections in the pattern files.

## When NOT to reach for a pattern
- There is one variant and no concrete second one on the horizon (YAGNI).
- A simple condition or function is shorter and just as clear.
- A framework mechanism already does it (DI, middleware, interceptors, a store, signals) — do not duplicate it.
- The pattern's structure is visible, but the problem it was meant to solve is not there.
- `@decorator` in TS is a language mechanism, not the Decorator pattern.

## Boundaries with neighbouring skills
- **eng-design-principles** — *why* (SOLID, KISS, composition > inheritance, resolving conflicts);
  this skill — *what shape* in the code.
- **eng-clean-code** — code smells and safe refactoring steps; make the move to a pattern in small steps
  (eng-behavior-preserving-refactoring).
- **ddd-tactical-design** — a policy (= a Strategy named in the business language), a specification (= a Composite of conditions),
  an aggregate factory, a state machine, events; there you decide about the model, here about the technique.
- **ddd-archetypes** — archetypes are the level of the business model, not GoF patterns.
- **fe-architecture** — UI patterns (compound components, loading states, error boundaries).
- **lang-typescript** — the idioms with which you implement the lighter forms (unions, generators, `satisfies`, `#fields`, `using`).

## Materials (read only the file you need)
- `references/basics.md` — when you need to explain what a pattern is, how it differs from an algorithm/a library,
  the classification and the "patterns in the repository" map.
- `references/critique-and-pitfalls.md` — before proposing a pattern in a review/refactoring; the table of lighter forms in TS,
  signals of overuse.
- `references/catalog.md` — when you choose between several candidates: 22 patterns with "one sentence" and "when NOT".
- `references/beyond-gof.md` — Role Object and Extension Object from the PLoP catalogs.
- `references/creational/{factory-method,abstract-factory,builder,prototype,singleton}.md`
- `references/structural/{adapter,bridge,composite,decorator,facade,flyweight,proxy}.md`
- `references/behavioral/{chain-of-responsibility,command,iterator,mediator,memento,observer,state,strategy,template-method,visitor}.md`
  — the full description of a pattern: the problem, the participants, when to use it, the costs, the relations, the idiomatic form in TS, an example,
  the pitfalls. The examples (30 blocks) compile in TS 6.0.3 and 7.0.2 (`strict`, `noUncheckedIndexedAccess`,
  `exactOptionalPropertyTypes`, `erasableSyntaxOnly`) and run in Node 22 through type stripping — without `enum`
  and parameter properties.

## Checklist
- [ ] The problem is named concretely and occurs at least a second time (not "for the future")
- [ ] A lighter form in the language / a framework mechanism has been checked
- [ ] "When NOT to use" of the chosen pattern has been read
- [ ] The number of new types is proportional to the gain; names from the domain, not from the pattern's name
- [ ] Business rules stayed in the domain (policies, specifications), not in the technical layer

Sources: the GoF catalog (Gamma, Helm, Johnson, Vlissides, 1994) and refactoring.guru — descriptions rewritten in our own
words, code examples written from scratch.
