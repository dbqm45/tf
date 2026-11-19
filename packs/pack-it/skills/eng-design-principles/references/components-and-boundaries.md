# Components, boundaries, policy and detail

A supplement to SKILL.md at a level above the class: how to group code into components (Nx libraries, Java packages, Maven/Gradle
modules) and how to set up the dependencies between them. The module and seam vocabulary: eng-module-depth.

## 1. Paradigms as constraints
Every paradigm takes away some freedom and gives something in return (R. C. Martin, *Clean Architecture*):
| Paradigm | What it takes away | What it gives in a project |
|---|---|---|
| structured | `goto` — control only through sequence, selection, loop | functions that can be read and tested separately |
| object-oriented | uncontrolled pointers to functions — polymorphism is safe | dependency inversion: the detail depends on the policy |
| functional | assignment — immutable data, pure functions | no races and no hidden state; logic easy to test |
In TS and Java you mix them deliberately: immutable value objects and pure functions in the domain (ddd-tactical-design),
objects with behaviour for rules with invariants, simple procedures in glue code and scripts.

## 2. Policy and detail
- **Policy** — business rules and use cases: *what* the system does. **Detail** — the database, framework, UI, protocol,
  external API, queue: *how* it is delivered.
- Dependencies in the code point **from the detail to the policy**. The domain does not import the framework, the ORM or an HTTP client —
  it defines a port, the detail supplies an adapter (eng-design-principles: the D of SOLID).
- **Level** = the distance from input and output. A discount validation rule is higher than an HTTP controller; higher code changes
  less often and for more important reasons, so it must not depend on lower code.
- Check test: can you run the use cases in a unit test **without** a server, a database and a framework? If not,
  the detail has leaked into the policy.

## 3. The framework at a distance
- A framework is a tool, not an architecture. Domain classes do not inherit from framework classes and do not carry its
  annotations, if that can be avoided (in Java a JPA entity ≠ the domain model when the model has non-trivial rules).
- You keep framework code at the edge: controllers, DI configuration, ORM mapping, Angular components call
  use cases, they do not contain rules.
- Cost: additional mapping. For simple CRUD (transaction script, be-database) the distance is unnecessary — KISS.

## 4. A structure that screams the domain and division by actor
- The top-level directories name **business areas** (`orders/`, `billing/`, `scheduling/`), not technical
  layers (`controllers/`, `services/`, `repositories/`). A new person should see *what* the system does before they see
  *how* (Screaming Architecture; for the frontend: Feature-Sliced Design in fe-architecture).
- Division by feature (package by feature) instead of by layer: a change to one feature touches one directory,
  and package visibility hides the interior.
- **Division by actor** (Single Responsibility as Martin frames it): a module answers to one group of stakeholders.
  A shared function computing hours for accounting and HR is a trap — when one department changes the rule, it breaks it for the other.
  Similar code for different actors is often accidental duplication (DRY in SKILL.md).

## 5. Boundaries
- A boundary separates what changes for different reasons and at a different pace. Simple data structures
  (DTOs, events) cross the boundary, not entities or framework objects.
- Kinds from the cheapest: a package or library in one process → a separate local process → a network service. Every step
  to the right costs (network, versioning, observability); you choose the cheapest one that is enough (arch-quality-attributes).
- You can prepare a boundary partially (separate libraries and ports in a monolith), so that a service can later be extracted without
  rewriting; you do not set up a full boundary "just in case" (YAGNI).

## 6. Component principles
**Cohesion — what goes together in one component**
| Principle | Content | Question |
|---|---|---|
| **REP** — reuse = release | a component used by others has versions and a changelog; it keeps together the classes released together | can this be sensibly versioned as a whole? |
| **CCP** — common closure | together what changes for the same reason and at the same time (SRP for components) | does a typical change touch one component? |
| **CRP** — common reuse | do not force clients to depend on things they do not use (ISP for components) | does the client take the whole component, or a small piece of it? |
REP and CRP split things up, CCP glues them together. At the start of a project CCP matters more (easy changes), in a mature shared
library — REP and CRP (stable clients).

**Coupling — dependencies between components**
- **ADP — no cycles.** The component dependency graph is acyclic. You break a cycle by inverting a dependency (an interface
  on the user's side) or by extracting the common part into a new component. Detection: `nx graph`,
  `madge --circular`, dependency-cruiser, in Java ArchUnit (`slices().matching("..app.(*)..").should().beFreeOfCycles()`).
- **SDP — depend in the direction of stability.** Instability I = Ce / (Ca + Ce), where Ca are the incoming dependencies, and Ce
  the outgoing ones. I = 0 — stable (many depend on it, it depends on no one), I = 1 — unstable. A dependency
  should lead to a component with a smaller I.
- **SAP — stable = abstract.** Abstractness A = the number of abstract types / the number of all types.
  Stable components should be abstract (ports, contracts), so that they can be extended without change.
- **Distance from the main sequence** D = |A + I − 1|. Close to 0 — good. **The zone of pain** (A≈0, I≈0): concrete code
  that everything depends on — every change hurts (exception: things stable by nature, e.g. the standard library).
  **The zone of uselessness** (A≈1, I≈1): abstractions nobody uses — remove them.

**In practice (Nx / Java)**
- Libraries with type tags (`type:feature`, `type:ui`, `type:data-access`, `type:util`, `type:domain`) and the rule
  `@nx/enforce-module-boundaries` fix the direction of dependencies.
- You compute the metrics for a few critical components once a quarter or at an architecture review
  (eng-codebase-mapping gives the graph), not for the whole repo on every commit. The result is a signal for a conversation, not a grade.

## Sources
- R. C. Martin, *Clean Architecture* (2017) — paradigms, policy and detail, boundaries, component principles and metrics.
- R. C. Martin, [Screaming Architecture](https://blog.cleancoder.com/uncle-bob/2011/09/30/Screaming-Architecture.html) (2011).
- [roadmap.sh — Software Design and Architecture](https://roadmap.sh/software-design-architecture) (topics: component
  principles, policy vs detail, boundaries, keep framework code distant, organize code by actor, programming paradigms).
Described in our own words.
