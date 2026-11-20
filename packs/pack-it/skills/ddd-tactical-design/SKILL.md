---
name: ddd-tactical-design
description: Use when designing the model inside one context — aggregates, value objects, events, sagas, deciders, policies, coupling (connascence), time-varying rules.
metadata:
  review: "2027-11-20"
  catalog: "Use when designing the domain model inside one bounded context — layers (application, domain, hexagonal), building blocks (value object, entity, aggregate, domain service, policy, specification, factory, repository, domain event, saga with a dispatcher, state machine, decider), aggregate boundaries from invariants, one aggregate per transaction, how events are published (outbox), sagas for long processes, CQRS when justified, anti-patterns, coupling assessment with connascence (strength, degree, locality), domain tests, and dynamic rules (policy trees, scoring, rules versioned by effective date, rules depending on history). Not for context boundaries and relations (ddd-strategic-analysis, ddd-context-mapping)."
  keywords: "projektowanie agregatu, granica agregatu, agregat w TypeScript, agregat za duży, agregat wczytuje za dużo, wolne ładowanie agregatu, obiekt wartości, value object czy encja, encja z identyfikatorem, niezmiennik, jedna transakcja jeden agregat, referencja po identyfikatorze, kto publikuje zdarzenia domenowe, zgubione zdarzenia po commicie, outbox, saga, proces wieloetapowy, proces trwa kilka dni, kompensacja, dispatcher, menedżer procesu, decider, czysta funkcja decyzji, funkcyjny rdzeń, maszyna stanów, polityka, strategia, specyfikacja, fabryka, repozytorium, warstwa aplikacji, warstwa domeny, architektura heksagonalna, model anemiczny, magiczne wartości, status = 2, metoda skopiowana w dwóch modułach, connascence, sprzężenie, reguła rozsmarowana po warstwach, reguła tylko w UI, błąd domenowy, reguły zmieniają się co rok, regulamin kar co roku, stare sprawy według starych zasad, wersjonowanie reguł, data obowiązywania, scoring, punktacja, drzewo reguł, reguły zależne od historii, trzecia reklamacja w roku, CQRS, model odczytu, testy domenowe, aggregate design, aggregate boundary, oversized aggregate, value object vs entity, invariant, one aggregate per transaction, reference by id, who publishes domain events, events lost after commit, saga, long-running process, process manager, dispatcher, decider, pure decide function, functional core, state machine, policy pattern, specification, repository, hexagonal architecture, anemic model, magic values, duplicated algorithm, connascence, coupling, smeared invariant, domain error, rules change every year, effective-dated rules, scoring model, rule tree, history-dependent rules, CQRS, domain tests"
---

# Tactical design — the model inside one context

Boundaries and relations between contexts are settled elsewhere (ddd-strategic-analysis, ddd-context-mapping). Here we
design what lives inside one context. No invariants, concurrency facts or domain examples given → ask for them before
proposing aggregates.

## 1. Layers
- **Application layer:** thin services that run one use case — open the transaction, check security, load aggregates
  through repositories, call business methods, save, publish events. No business rules. Input: identifiers and plain
  data, not ready-made domain objects.
- **Domain layer:** pure rules, no framework, testable without a server or a database.
- **Hexagonal:** the domain in the centre defines its ports; adapters (database, HTTP, queues) live outside.

## 2. Building blocks
| Block | Use for | Key rule |
|---|---|---|
| Value object | a concept defined by its values (money, period, address, probability) | immutable, validates itself, compared by value; replaces primitives and scattered validation |
| Entity | something with identity and a lifecycle | compared by id; behaviour, not setters |
| Aggregate | a cluster that must be consistent immediately | one root; changed only through business methods; one aggregate per transaction; other aggregates referenced by id |
| Domain service | an operation that belongs to no single aggregate | stateless |
| Policy | a rule with variants | strategy; a new variant without touching the core |
| Specification | combinable business conditions | named in business language |
| Factory | creation that needs decisions | the object starts valid |
| Repository | a collection of aggregates | not a DAO for screen queries |
| Domain event | a fact that happened | past tense, immutable |
| Saga / process manager | a long process across events and aggregates | persisted state, explicit steps, compensations |
| State machine | lifecycle-dependent operations | explicit transitions instead of status `if`s everywhere |
| Decider | decisions as a pure function | `decide(state, command)` → events or rejection; `evolve(state, event)` → state |

Behaviour reused by many use cases belongs in the aggregate; behaviour specific to one use case belongs in its service.

## 3. Designing an aggregate
1. **Start from invariants** (rules that must hold after every change — Design Level notes), not from nouns or tables.
2. **Ask who changes it at the same time.** Users editing different parts → probably separate aggregates.
3. **Smallest boundary that protects the invariant.** A large aggregate causes write conflicts and loads too much: an
   `Order` holding the `Customer`, all `Invoice`s and their lines should keep only what its invariant needs and point to
   the rest by id.
4. **Rules across aggregates** are eventually consistent (events, policies) unless the business needs them immediate.
5. **Dynamic aggregate:** when the boundary depends on the request (lock a resource for a time range → load only the
   affected time segments), assemble it from smaller units (ddd-archetypes, resource holds).
6. **Optimistic concurrency:** a version on the root.
7. **Publishing events — pick one variant per project:**
   - (a) the business method **returns** the events (or a rejection); the application service publishes them;
   - (b) the aggregate **collects** events; the service takes them after saving.
   Publishing in memory "after commit" loses events when the process dies between commit and publish → if that is
   unacceptable, write the events to an **outbox** in the same transaction (be-messaging-outbox).
8. **Anti-pattern:** a method that both mutates the object and returns a new instance.
9. **A rule spread over several layers** (a piece in the UI, a piece in a service, nothing in the database): the aggregate
   becomes the single guard — preconditions in its methods, a named domain error on violation (fail fast), the repository
   loads the whole aggregate, one transaction, a thin route that maps the error to a response. Finding such rules in an
   existing codebase: ddd-legacy-modernization.

## 4. Long processes — saga and dispatcher
A process that runs for hours or days across payment, warehouse and courier, where any step may fail:
- the saga keeps the **process state**, persisted, and an explicit **step type** (`AwaitingPayment`, `AwaitingPickup`, …);
- deciding *what next* is a pure function of the saga's state and the incoming event;
- **executing** the next step (sending a command, calling a provider) is done by a separate **dispatcher**;
- each step that can fail has a compensation (refund, release the reservation) and a timeout.

## 5. Decider — decisions as a pure function
- `decide(state, command)` returns events or a rejection; `evolve(state, event)` returns the next state; state is immutable.
- The shell does the I/O: **load → decide → save → publish**. The core needs no mocks to test.
- With event sourcing the state is `events.reduce(evolve, initial)`.
- Moving an existing rich aggregate to a decider: step by step, behaviour preserved (eng-behavior-preserving-refactoring).

## 6. CQRS
Separate read models (projections) only when read and write access patterns really differ — not "just in case".

## 7. Anti-patterns
Anemic model; entities passed outside the context as DTOs, or one model mixing several contexts; free getters and setters
that bypass rules; inheritance where delegation or a policy is enough; flag fields (`isReserved`, `inMaintenance`)
instead of named concepts (ddd-archetypes).

## 8. Coupling — connascence
Elements are connascent when changing one forces a change in the other. Assess three properties:
- **strength** — static and weaker: name (CoN), type (CoT), meaning (CoM), position (CoP), algorithm (CoA); dynamic and
  stronger: execution order, timing, value (CoV), identity;
- **degree** — how many elements are bound together;
- **locality** — how far apart they are.
Rule: strong connascence only locally (inside an aggregate or module); across a context boundary only the weakest (name,
type, through a published language).

| Found | Kind | Fix |
|---|---|---|
| `status = 2` means "cancelled" | meaning | enum or value object |
| long list of same-typed parameters | position | parameter object |
| the price calculation copied in 2 modules | algorithm | one source (a policy or domain service) |
| the same value kept in 2 contexts | value | one owner plus events |
| methods that must be called in order | execution order | one business method or a state machine |

A repeatable measurement with a report: ddd-connascence-analysis. A transaction shared across a boundary binds both
order and value.

## 9. Domain tests
Test aggregates and policies through public methods on the modelling examples (Given / When / Then), without a database or
framework; emitted events are the assertions.

## 10. Dynamic rules
Rules that vary by configuration, by date or by history — policy trees, scoring, rules versioned by effective date,
rules that depend on past events, aggregates as state machines: `references/dynamic-rules.md`.

## Example
**Situation:** "A `Reservation` aggregate in TypeScript — where is the boundary, and who publishes events so they are not
lost after a commit?"
**Result:**
- Invariant: a room has no overlapping confirmed reservations in a time range; contention: many people book the same
  room in the same morning → the aggregate is the room's schedule for the affected days (dynamic), not the whole calendar.
- `Reservation` is referenced by id from `Invoice`; one aggregate per transaction.
- Variant (a): `schedule.reserve(slot, guest)` returns `[ReservationConfirmed]` or `SlotTaken`; the application service
  saves the aggregate and the events to the outbox in one transaction; a relay publishes them.
- Tests: Given `ReservationConfirmed(10:00–11:00)`, When `reserve(10:30–11:30)`, Then `SlotTaken`.
