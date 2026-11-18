# Basics: what a pattern is and how the categories lead to the problem

## Definition
A design pattern is **a named, proven shape of a solution to a recurring design problem**. It is not
ready-made code or a library — it is a description of roles, relations and trade-offs that you express anew in every project, in its
vocabulary and conventions.

A pattern description (also in the files of this skill) consists of: **the problem** (what hurts and why), **the solution** (roles
and relations), **the applications**, **the costs**, **the relations** with other patterns and **an example** in a concrete language.
The relations are sometimes more important than the pattern itself — many pairs look identical in the code (Decorator/Proxy,
Strategy/State, Adapter/Bridge), and what separates them is the motivation.

## A pattern vs an algorithm and a library
- **An algorithm** is an exact sequence of steps — executed the same way, it gives the same result.
- **A pattern** describes a shape at a higher level; the details (names, division, API) belong to the project. Two correct
  implementations of the same pattern in one repository may look different — that is not a mistake, just a fit.
- **Libraries** are imported; a pattern cannot be "installed". The code examples in `creational/`, `structural/`,
  `behavioral/` illustrate the shape — do not paste them 1:1.

## Three categories (the GoF catalog)
| Category | The question it answers | Patterns |
|---|---|---|
| **Creational** | **how and where an object is created** — who decides on the concrete class, how to assemble an object, how many instances there should be | Factory Method, Abstract Factory, Builder, Prototype, Singleton |
| **Structural** | **how elements are composed** — who wraps/contains whom, how to reconcile interfaces, how to share data | Adapter, Bridge, Composite, Decorator, Facade, Flyweight, Proxy |
| **Behavioral** | **who talks to whom and who is responsible for what at runtime** — the flow of requests, notifications, state changes | Chain of Responsibility, Command, Iterator, Mediator, Memento, Observer, State, Strategy, Template Method, Visitor |

Classifying the problem into a category is the first filter before the "symptom → pattern" table in `SKILL.md`:
- a problem with `new`, configuration at creation, the number of instances → creational;
- a problem with the static shape (incompatible interfaces, an explosion of subclasses, trees, layers) → structural;
- a problem with the flow over time (reactions to events, behaviour changing with the state, queuing actions) → behavioral.

The original GoF book also divides patterns into class and object patterns; that is not needed here — in modern TS we implement almost
everything by composing objects and functions.

## GoF patterns vs the other "patterns" in the repository
| Level | Examples | Skill |
|---|---|---|
| principles (why) | SOLID, KISS, YAGNI, composition > inheritance | eng-design-principles |
| GoF patterns (how in the code) | this skill | eng-design-patterns |
| DDD building blocks | aggregate, policy (= strategy), specification (= composite), factory, repository | ddd-tactical-design |
| business archetypes | Party, Availability, Pricing, Accounting | ddd-archetypes |
| UI patterns | compound components, loading states, error boundaries | fe-architecture |
| language idioms | discriminated unions, generators, `satisfies` | lang-typescript |

Sources: E. Gamma, R. Helm, R. Johnson, J. Vlissides, "Design Patterns" (1994); the refactoring.guru catalog — content
written in our own words, code examples written from scratch.
