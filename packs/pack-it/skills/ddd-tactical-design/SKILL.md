---
name: ddd-tactical-design
description: Use for the model inside a context — aggregates, entities, value objects, events, policies, saga, CQRS.
metadata:
  review: "2027-10-09"
  catalog: "Use when designing the model inside a context — building blocks (aggregate, entity, value object, service, policy, specification, factory, repository, events, saga), layers, consistency boundaries, CQRS, assessing coupling through connascence. Not for the boundaries and relationships of contexts (ddd-strategic-analysis, ddd-context-mapping)."
  keywords: "magiczne wartości, zduplikowany algorytm, agregat, granica transakcji, obiekt wartości, regulamin zmienia się co rok, rozliczać według starych zasad, reguła zmienna w czasie, wersja polityki, naliczanie kar, scoring, drzewo reguł, magic values, duplicated algorithm, aggregate, transaction boundary, value object, the rules change every year, settle by the old rules, time-varying rule, policy version, calculating penalties, rule tree, granica agregatu, projektuję agregat, zdarzenia domenowe, kto publikuje zdarzenia, zgubione zdarzenia po commicie, outbox, aggregate boundary, designing an aggregate, domain events, who publishes events, events lost after commit"
---

# Tactical design

## Layers
- **The application layer** — thin application services: they carry out a use case, manage the transaction and security,
  fetch aggregates from repositories, call business methods, save, publish events. **No business rules.**
- **The domain layer** — pure business rules, without frameworks and infrastructure; testable without a server and a database.
- Work with identifiers at the input of an application service (the client does not pass "ready" domain objects).
- Hexagonal architecture: the domain in the middle, the ports (interfaces) are defined by the domain, the adapters (REST, database, queues) outside.

## Building blocks — when to use which
| Element | Use when | Rules |
|---|---|---|
| **Value object** | a concept described by values, without identity (an amount, a period, an address, a probability) | immutable, validates itself; replaces primitives and removes scattered validations ("150 places checking for null") |
| **Entity** | identity and lifecycle matter | only responsibilities proper to its nature |
| **Aggregate** | a group of objects that must be consistent immediately | one root; changes only through business methods (no setters); one transaction = one aggregate; references to other aggregates by ID |
| **Domain service** | an operation does not naturally belong to any aggregate (a transformation, a computation over several objects) | stateless; prevents "god classes" |
| **Policy** | a rule has variants (e.g. discounting, calculating penalties) | the strategy pattern; new variants without changing the core (supple design) |
| **Specification** | complex business conditions to combine (and/or/not) | the composite pattern; the condition's name in the business language |
| **Factory** | creating a complex aggregate requires decisions (which policies, which collaborators) | guarantees a valid state from the start; fewer `new` in the domain = easier tests |
| **Repository** | persistence of aggregates of a given type | a collection of aggregates, not a DAO with hundreds of methods for screens; queries for business operations |
| **Domain event** | something important happened and others may want to react | past tense, immutable; enables extensions, asynchrony, loose coupling |
| **Saga / process manager** | a process lasts long and spans many events/aggregates | the process state saved; reacts to subsequent events; compensations |
| **State machine** | behaviour depends on the state | explicit transitions and conditions instead of scattered `if (status == …)` |
| **Decider (functional core)** | you want to separate the decision from the effects (testability, a path to event sourcing) | `decide(state, command)` → a new state / events / a rejection; immutable state; I/O in the shell: load → decide → save → publish. Moving from a rich aggregate: eng-behavior-preserving-refactoring |

Heuristic: methods that are characteristic and reused across many use cases → into the aggregate;
specific to one use case → into the service.

**When one policy is not enough** (`references/dynamic-rules.md`):
- policies as pure functions composed into chains, trees and decorators, built from configuration by a policy
  factory;
- scoring with versioned components and thresholds;
- time-varying rules, where a new version is a new class chosen by the relevant date (without `if (year >= …)`);
- rules depending on the history of events (the state as a fold of the stream);
- an aggregate as a state machine.

## Designing aggregates
1. Start from the **invariants** (the yellow notes from Design Level), not from nouns and relations in the database.
2. Ask about **competition for resources**: who changes it at the same time? what if two people do it at once? (ddd-deep-modeling)
3. The smallest boundary that protects the invariant. A large aggregate = conflicts and loading unnecessary data.
4. Rules between aggregates → eventual consistency (events, policies), unless the business really requires immediate consistency.
5. **A dynamic aggregate**: when the boundary depends on the request (e.g. lock a resource in a time range → load only the time
   segments the request concerns), assemble the aggregate from smaller units for the needs of the operation (ddd-archetypes → availability).
6. Optimistic versioning on the aggregate root.
7. **Who publishes events?** (a) the aggregate returns an event or a rejection from the business method, the application service publishes it —
   explicit, easy to test; (b) the aggregate collects events, the service "pulls" them after saving. Both are OK — choose one in the project.
   Publishing from memory "after the commit" loses events on a failure; when that is unacceptable → an outbox (be-messaging-outbox).
8. **A saga** holds the process state and an explicit step type; the "what next" decision is made by the saga (purely), the execution of the steps — by a separate dispatcher.
9. Anti-pattern: a method that at the same time **mutates** the object and **returns a new instance** — choose one (an immutable VO or mutating the aggregate).
10. **An invariant in existing code** is sometimes "everywhere and nowhere": a piece in the UI, a piece in a service, a piece
    in the order of calls, nothing in the database. Symptoms: the client is the only guard, the endpoint trusts the request data, the error
    is logged and swallowed. A guard aggregate: the only place of enforcement, methods with preconditions, a named
    domain error (fail-fast), a repository loading the whole, atomicity in one transaction, a thin API route
    (parse → method → map the error). Choosing the invariant and the diagnosis in legacy: ddd-legacy-modernization.

## Reads — CQRS
When reads and writes have different needs: the write model protects the rules, separate **read models/projections** serve screens and reports.
Do not add CQRS "just in case" — it is extra complexity; justify it with a difference in access patterns.

## Anti-patterns
- **An anemic model** — entities as bags of data with getters/setters, the logic in services.
- Entities as DTOs outside the context; mixing the models of contexts.
- Getters/setters that allow changing the state freely, bypassing the rules.
- Inheritance where composition or a policy is enough.
- Flag fields (`isReserved`, `inMaintenance`, `isCustomer`) instead of separate concepts or an archetype.

## Connascence — assessing coupling
Two elements are connascent when a change of one forces a change of the other. Assess three properties:
- **Strength** (from the weaker): static — name → type → meaning (conventional values) → position → algorithm;
  dynamic (stronger) — execution order → timing → value → identity.
- **Degree** — how many elements are bound. **Locality** — how far apart they are.

Rules: accept strong connascence only **locally** (within an aggregate/module); across context boundaries allow
the weakest (name, type — through a Published Language). Refactor towards weaker forms:
- magic values ("2 = cancelled") → a value object / enum (meaning → name);
- long lists of parameters of the same type → a parameter object (position → name);
- the same algorithm (e.g. computing a price, a hash) in two places → one source (algorithm → name);
- two contexts must have "the same value" of data → one owner + events (value → event type);
- a required order of calls → one business method or a state machine (order → name).

A repeatable **measurement** of the coupling between two modules (a breakdown into agreements, the degree from lines of code, the cost, the band profile):
ddd-connascence-analysis. A shared transaction across a boundary is two agreements — execution order and value.

## Domain tests
Test the behaviour of aggregates and policies through their public methods, on examples from modelling (Given/When/Then),
without a database and a framework. Events make good assertions ("after X the event Y was created").

## Sources
- The 10xDevs course, ed. 3 (2026), module 4, lesson 5 (an invariant smeared across legacy, the guard aggregate) — training
  material (accessed 2026-10-09); described in our own words.
