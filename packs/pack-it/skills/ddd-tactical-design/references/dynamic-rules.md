# Dynamic rules, time-varying rules and history-dependent rules

When an aggregate and one policy (strategy) are not enough, because the rules are made of parts, change every year,
are defined by the business or depend on what happened before.

## 1. A policy as a function and composing policies
- **A policy** is a pure function `(context) → result`, e.g. a discount, a penalty, a limit or a yes/no decision with a justification.
  It does not save state and does no input/output (ddd-tactical-design: Decider).
- **Composition:** you combine small policies into larger ones:
  - **a chain:** consecutive steps process the result or decide who handles the case (chain of responsibility);
  - **a tree:** nodes `AND`, `OR`, `NOT`, "first matching", "sum", "minimum" and leaves with simple rules.
    A specification combined with `and`/`or`/`not` is a tree of yes/no rules;
  - **a policy decorator:** a wrapper that changes the result of another policy without changing it, e.g. capping a discount at
    30%, rounding, recording the justification, an exception for a selected customer (supple design).
- **A policy factory:** builds the tree from configuration (the knowledge level, ddd-deep-modeling). The business changes a rule
  with data, and the code knows only the building blocks and the ways of combining them.
  - The configuration has its own validation: known building blocks, correct types, no cycles.
  - The configuration has a version.
- **A result with a justification:** every policy returns not only a value but also the reason ("discount 10%: customer for more than
  2 years; cap 30%"). Without this, rules built from data cannot be explained or tested.
- **The limit:** a tree of a dozen or so building blocks is fine. When the business starts "programming" in the configuration
  (loops, variables, external calls), a rules engine or a DSL is needed. That is an architectural decision (ADR).

## 2. Scoring
- **Scoring** is a policy that turns the features of a case into a number of points. The number is compared with decision
  thresholds, e.g. a risk assessment, a ticket priority, the order of leads.
- **Structure:** a list of components (feature → points, each as a small policy), a combining function (sum, weighted sum,
  minimum), decision thresholds and a justification (which components gave how many points).
- **Rules:**
  - The components and thresholds are versioned, because they change more often than the code.
  - A decision records the scoring version and the breakdown of points (audit, disputes, appeals).
  - When the weights come from data (a statistical or ML model), that is a different field: ai-research-methods,
    data-analysis.

## 3. Time-varying rules
- **A rule has a period of validity.** You settle cases by the rule in force on the date relevant to the case
  (the date of the event, of concluding the contract, of the report), not on the date of the computation. The relevant date is set by the domain expert.
- **Copying code as a pattern:** a new version of a rule is a new class or function (`PenaltyRules2025`,
  `PenaltyRules2026`) and an entry in a "valid from" register. You do not add `if (year >= 2026)` conditions
  to the old class.
  - The old version stays untouched: old cases compute the same as they did then, and the tests of the old version still
    pass.
  - The duplicated code is a deliberate choice here, because the versions are separate legal facts. If they were shared, a change
    of one could change the other.
- **Choosing the version:** one place, e.g. a policy register or a factory, chooses the version by the relevant date. The version
  goes into the result and the event.
- **Two time axes:** when it also matters when the system learned about it (retroactive corrections, annexes dated
  earlier), you use two date ranges (ddd-archetypes, `.claude/skills/ddd-archetypes/references/agreement.md`).

## 4. Rules depending on the history of events
- **The problem:** the decision depends on a sequence of earlier events, not only on the current state. Examples:
  "the third complaint in a year", "a block after two failed payments", "a discount if the customer came back after
  abandoning the cart".
- **The solution:** the state the rule needs is a fold of the event stream: `state = events.reduce(evolve)`.
  The rule works on this state.
  - In the Decider model: `decide(state, command)` and `evolve(state, event)`.
  - With event sourcing the stream is the source of truth. Without it you keep in the aggregate only what the rule
    needs (e.g. a counter with dates).
- **Rules:**
  - The state for the rule is minimal: not the whole history, only what the rule reads.
  - The order of events is part of the rule, so the tests give a sequence (Given: events, When: a command,
    Then: events or a rejection).
  - A new rule over an old history is a data migration or a new projection.

## 5. An aggregate as a state machine
- **When:** the set of allowed operations depends on the stage of the lifecycle, e.g. an order placed, paid, shipped,
  cancelled.
- **Structure:**
  - The state is an explicit type (an enumeration or separate state classes).
  - Every business method checks the transition in one place (a transition table or a state method).
  - A successful transition emits an event.
  - A disallowed transition is a rejection with a reason, not a silent lack of change.
- **Variants:**
  - few states and simple logic: an enumeration with a transition table;
  - states with different data and behaviour: separate state types (the State pattern), e.g.
    `OrderPaid` has a payment number, and `OrderPlaced` does not.
- **The pitfall:** a state does not replace separate concepts. When a "state" has different data, rules and an owner, it is a different concept
  (ddd-deep-modeling, `.claude/skills/ddd-deep-modeling/references/untangling.md`).

## Sources
- E. Evans, *Domain-Driven Design*, Addison-Wesley, 2003, ch. 10 "Supple Design" (among others Intention-Revealing
  Interfaces, Side-Effect-Free Functions, Closure of Operations, Declarative Design) and the specification
  [unverified: according to the publisher's table of contents, without reading the text in this session].
- E. Evans, M. Fowler, "Specifications", PLoP 1997 — composing specifications (`and`, `or`, `not`)
  [unverified: a summary from secondary sources].
- E. Gamma, R. Helm, R. Johnson, J. Vlissides, *Design Patterns*, Addison-Wesley, 1994, ISBN 0201633612 —
  Decorator, Chain of Responsibility, State, Strategy.
- M. Fowler, "Temporal Patterns" (martinfowler.com/eaaDev/timeNarrative.html): Effectivity, Temporal Property,
  Temporal Object [unverified: the page was unavailable from this session].
- M. Fowler, "Event Sourcing" (martinfowler.com/eaaDev/EventSourcing.html) [unverified: the page was
  unavailable from this session].
- "Copying code as a pattern", policy factories and scoring are described in our own words based on the programme
  of the training "DDD — zaawansowane techniki modelowania i archetypy" ("DDD — advanced modelling techniques and archetypes"; Bottega IT Minds, material from the human,
  2026-10-21).
