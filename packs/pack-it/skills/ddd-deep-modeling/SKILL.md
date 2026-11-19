---
name: ddd-deep-modeling
description: Use for modeling domain concepts — many-to-many, types defined by an administrator, status, Being/Behaving/Becoming.
metadata:
  review: "2027-10-17"
  catalog: "Use for discovering and refining the concepts of a model — Being/Behaving/Becoming modeling questions, 5 why, problem classification (CRUD, transformation, presentation, integration, competition for resources), modeling by examples. Not for context boundaries (ddd-strategic-analysis) or implementation patterns (ddd-tactical-design)."
  keywords: "poziom wiedzy, poziom operacji, knowledge level, rodzaje definiowane przez administratora, typ i egzemplarz, relacja wiele do wielu, ukryte pojęcie, jedno źródło prawdy, single source of truth, status zamiast pojęcia, administrator definiuje nowe rodzaje, rozdzielić w modelu domeny, operations level, kinds defined by an administrator, type and instance, many-to-many relationship, hidden concept, status instead of a concept, administrator defines new kinds, separate in the domain model"
---

# Deep modeling

A **deep model** helps understand and simplify the problem — it does not just reflect it. A model is not a database
schema: a schema stores state, a model carries behaviour and rules. A schema invented too early fixes a
misunderstanding of the domain for months.

## Modeling questions — three perspectives
For every important concept, go through three perspectives. The answers immediately tell you which model element emerges.

### Being — what it is (structure)
- What information describes this concept? **How much** of it is there (multiplicity: one, many, zero)? **Of what type** (number, amount, period, unit)?
- What range of values is allowed? What is mandatory?
- Are two instances with the same data **the same thing**? — yes → a value object; no, identity counts → an entity.
- Does the number have a unit or a currency? → a value object (Quantity, Money), not a "bare" number.

### Behaving — how it behaves (change)
- **Who** changes it? **Why** — what is the business reason for the change? What is the **effect** of the change and whom does it concern?
- **How often** does it change? Do several people change it **at the same time**? → competition for resources, aggregate size.
- Can the change be **repeated** (e.g. the same command twice)? → idempotency.
- Can the change be **reversed**? How — by deletion, correction, reversal entry, compensation? Who can reverse it?
- What rules can **reject** the change? → invariants, policies.
- **5 why** — ask "why?" until you reach the real business need:
  "The invoice status has to be changed" → why? → "because the customer paid" → why is that important? → "because then we release the goods" →
  … → the real event is "Payment posted", and the rule is "release the goods after the payment is posted".

### Becoming — what it turns into (change of essence)
- Does this concept at some point **become something else**? (lead → customer, offer → contract, reservation → rental, draft → published document)
- Is this transformation **easily reversible**? Hard to reverse → a pivotal event, often a different model/context, different rules.
- After the transformation, do different rules, different actors, different data apply? → separate the models instead of one class with flags.
- States with different allowed operations → a state machine (explicit transitions) instead of a "status" field.

## Problem classification → way of modeling
Before you design, name the problem class. Each one requires a different approach.

**First the volatility test — state it in the answer:** *can the data on which we base the decision be changed
at the same moment by another request?* Yes → competition for resources (atomicity, aggregate). No → CRUD or a calculation
with validation. **The class is determined by the effect of the operation on the system's state, not by the number of rules:** a calculation whose result we only
store is CRUD with a policy; rich validation of the request data does not change the class. The table below shows auxiliary
signals; when they contradict the test, the test decides.

| Class | Auxiliary signals | Approach |
|---|---|---|
| **CRUD** | forms, simple validations, no rules between data | do not over-model; a simple data layer, possibly validation policies |
| **Transformation / calculations** | "calculate", "price", "determine", many rules, a deterministic result | pure functions, policies/strategies, value objects at the input and output, tests on examples |
| **Presentation** | "show", "summary", "report", combining many sources | read models, projections (CQRS), no business logic |
| **Integration** | another system, another language, another pace of change | ACL / Open Host, translation, idempotency, outbox (ddd-context-mapping) |
| **Competition for resources** | "cannot happen twice", limits, reservations, concurrency | an aggregate around an invariant, choosing the granularity of locks, the availability archetype (ddd-archetypes) |

One business area usually contains several classes — separate them instead of building one "model for everything".

Strong and weak signals, signals from UI mock-ups, pitfalls, the deduction path and typical combinations: `references/problem-classes.md`.
When a calculation looks like a known problem (ordering, assignment, packing) → ddd-algorithm-recognition.

## When CRUD is enough
No rules between fields, no concurrent changes, no transformations of essence, changes do not cause effects in other
areas. Then a deep model is a cost without a gain. A signal that CRUD is no longer enough: flags appear,
a "status" field with conditions in many places, repeated `if` statements in services, conflicts with simultaneous changes.
With a "status" field, start with **5 why** (the Behaving section): ask why the status changes until you reach the business
event; only then decide on a state machine.

## Untangling the model
When facts drift apart or every need gets a new status value, reach for one of the four techniques
in `references/untangling.md`:
- **A single source of truth:** every fact has one owner, and the rest point to it by an identifier or refresh
  a copy with an event.
- **A hidden concept in a many-to-many relationship:** name it, e.g. doctor ↔ clinic is an Employment (*Zatrudnienie*) with dates
  and conditions.
- **Status is not an extension mechanism:** different data, rules and life cycle mean a separate concept or role.
- **Two levels of the model:** the knowledge level (types and rules defined by the business) and the operations level (instances
  that point to their type).

## Modeling by examples
- Describe every rule with a **concrete example** with numbers and dates (Given / When / Then), together with a **counterexample**.
- Edge examples: zero, one, many; date boundaries; simultaneous actions; reversal.
- Examples from the expert are better than yours; mark yours as **[proposal]**.

## Concept card (recorded in `docs/project/02-domain/concepts/<concept>.md`)
```markdown
# <Concept> (context: <name>)
Definition: …
Being: data, multiplicity, types, identity (entity / value object)
Behaving: who changes it, why, effect, frequency, concurrency, repeatability, reversibility
Becoming: what it turns into, whether reversibly, pivotal event
Invariants: …
Problem class: CRUD | transformation | presentation | integration | competition for resources — confidence: high/medium/low; deduction path: …
Evidence: ids of quotes from the bank (ddd-discovery-intake) or [proposal]
Examples (Given/When/Then) and counterexamples: …
Open questions (hot spots): …
```

## Continuous maturing of the model
The model evolves together with knowledge (knowledge crunching). "Blind" evolution gets stuck in a local optimum — from time to time
go back to the basic questions and check whether the new cases require remodeling, not another `if`.
