# Catalog of 22 patterns — a "when yes / when no" summary

The full description is in the pattern's file (the problem, the solution, the costs, the relations, the idiomatic form in TS, an example checked
by the compiler, the pitfalls).

## Creational
| Pattern | In one sentence | When NOT (summary) | File |
|---|---|---|---|
| Factory Method | a subclass replaces the created product, the base logic stays | one variant; a factory function is enough | `creational/factory-method.md` |
| Abstract Factory | consistent families of objects without knowing the classes | one family "just in case"; types are added more often than families | `creational/abstract-factory.md` |
| Builder | a complex object in steps, validation at `build()` | a few options — an options object is enough | `creational/builder.md` |
| Prototype | the object clones itself, also with private state | a flat DTO — `structuredClone`/spread | `creational/prototype.md` |
| Singleton | one instance + global access | almost always: an ES module or a DI scope instead of a class | `creational/singleton.md` |

## Structural
| Pattern | In one sentence | When NOT (summary) | File |
|---|---|---|---|
| Adapter | translates a third-party API into our port | both sides are ours — unify at the source | `structural/adapter.md` |
| Bridge | two independent dimensions of variation as two hierarchies | only one dimension grows | `structural/bridge.md` |
| Composite | an element and a group under one interface, recursively | the data is not a tree | `structural/composite.md` |
| Decorator | layers of behaviour composed at runtime, the same interface | 1–2 fixed additions; do not confuse with a TS `@decorator` | `structural/decorator.md` |
| Facade | a simple interface to a complex subsystem | the subsystem is already simple; a god facade | `structural/facade.md` |
| Flyweight | sharing the immutable state of thousands of objects | no measured memory problem | `structural/flyweight.md` |
| Proxy | access control (laziness, permissions, cache) behind the same interface | the motivation is new behaviour (Decorator) or an `if`/`??=` is enough | `structural/proxy.md` |

Decorator and Proxy look the same in the code — the motivation decides.

## Behavioral
| Pattern | In one sentence | When NOT (summary) | File |
|---|---|---|---|
| Chain of Responsibility | handle it or pass it on; it can be interrupted | a fixed, short sequence; the framework has middleware | `behavioral/chain-of-responsibility.md` |
| Command | an action as an object: a queue, a log, undo | no undo/serialization — a closure is enough | `behavioral/command.md` |
| Iterator | traversal without exposing the structure | the iteration protocol and generators are in the language | `behavioral/iterator.md` |
| Mediator | components talk through an intermediary | 2–3 objects with one relation; the framework's store | `behavioral/mediator.md` |
| Memento | a snapshot of the state without breaking encapsulation | immutable state — the history is an array of states | `behavioral/memento.md` |
| Observer | subscribers learn about a change | one known recipient — a callback | `behavioral/observer.md` |
| State | state-dependent behaviour in state objects | the states differ in data — a union + `switch` | `behavioral/state.md` |
| Strategy | an interchangeable variant of an algorithm/policy | it is usually just a function; one variant | `behavioral/strategy.md` |
| Template Method | a fixed skeleton, overridden steps | differences scattered or variable at runtime — Strategy | `behavioral/template-method.md` |
| Visitor | new operations on a stable type hierarchy | types are added often; few types and operations | `behavioral/visitor.md` |

Command, Iterator and Strategy most often have a lighter form in TS than the class one — `critique-and-pitfalls.md`, point 1.
