# The General Assignment archetype — mapper (tasks, resources, assignment with constraints)

> **Contents:** Fit test · Model (the essence) · Heuristic or solver · Optimization vs simulation — two modules · Recommendation or binding decision · Questions · Mapping steps · Decisions to check (R/A/X) · Result format · Patterns and pitfalls · Quality check · Example (shortened)

It turns requirements in which you must choose **which** tasks/orders/projects to carry out and **with which** resources, when
the resources have different features and the tasks different requirements and value (specialists for projects, vehicles for orders, rooms for classes,
machines for orders), into an optimization model. Manual `if`s and sorting "by value" give random results. The effect:
assignment as **a pure function** — testable with examples and ready for "what if" simulation. The common protocol: `SKILL.md` →
"Mapper — the common protocol".

## Fit test
**The core question:** *do you need to choose a subset of tasks and match resources with different features to them so as to maximize
value with limited capacity?* Yes → it fits. The question is only "is the resource free?" → Availability.

| Signal in the requirements | Fits? |
|---|---|
| "whom to assign to the project", "which vehicle for the order" | ✅ |
| resources differ in features (competences, load capacity, equipment) | ✅ |
| "there is not enough for everyone — which tasks to take?" | ✅ |
| "how much will we gain by hiring one more person?" | ✅ simulation |
| "is the room free on Tuesday?", double bookings | ❌ → Availability |
| "in what order the stages, what in parallel?" | ❌ → Planning |
| "who is first in the queue for a released place" | ❌ → Waitlist |
| "which product options may be combined" | ❌ → Configurator |
| "assign a ticket to the person on duty according to the rota" | ⚠️ borderline |

**Borderline cases:**
- *Assignment by a simple rule* (round-robin, rota) — is there **a choice with a value conflict** (not everything will fit,
  resources are not interchangeable)? No → a rule/policy; yes → General assignment.
- *A schedule with time* — order and dependencies are Planning; who performs a stage — General assignment; occupation in time — Availability.

## Model (the essence)
| Element | Essence |
|---|---|
| **Capacity dimension** | a single available resource with defined features ("senior Java developer", "12 t truck on Monday") |
| **Weight dimension** | a requirement of a task that **is satisfied by** a defined capacity dimension — the predicate "does this resource satisfy this requirement" |
| **Item** | a task with a name, a **value** (profit, priority) and a total weight (a list of requirements); tasks without requirements are taken **always** |
| **Total capacity** | the set of available resources |
| **Solution** | a multidimensional **knapsack problem**: a subset of tasks with maximum total value, where each requirement of a chosen task is assigned to a **different**, matching resource. The result: value, chosen tasks, the assignment task → resources |
| **Order of consideration** | a parameter (e.g. descending by value) |

The problem class **transformation/computation** (ddd-deep-modeling): a pure function, easy to test with examples and to
simulate "what if" (what will we gain by hiring one more person).

## Heuristic or solver
| Situation | Engine |
|---|---|
| few tasks and resources, a "good enough" result, a fast answer | **a greedy heuristic** (sort by value/density, take what fits) |
| medium scale, the optimum needed | dynamic programming / search with pruning |
| large scale, many constraints (costs, preferences, limits), optimality required | **a MIP solver** (integer programming) |
| the value depends on the task–resource pair (travel cost, fit) | the weighted assignment problem / MIP |

An interchangeable engine behind one interface — start with the simplest, measure quality with examples.

## Optimization vs simulation — two modules
| Module | Role |
|---|---|
| **Optimization** | a generic engine: elements with value and requirements, capacities as dimensions with the predicate "does it satisfy"; it knows nothing about projects or people. Easy to test with textbook examples |
| **Simulation** | a domain adapter: it maps projects, competence requirements and people's availability onto elements and capacities, and the result — back into the language of the business |

- Typical decision support questions as two **before/after** simulations: "how much will we gain by hiring/buying additional capability?",
  "what will happen to the profit if we move a person between projects?". **The difference in value = the answer.**
- An implementation pitfall: with **dynamic programming** tables do not fill all cells with **the same** mutable
  object — each cell needs its own instance.

## Recommendation or binding decision
The result of the assignment is by default **a recommendation** (a plan, a simulation) — it blocks nothing. When it becomes **a binding decision**, a separate
approval step calls **Availability**, which **blocks** the resources; a block conflict (someone took the resource in the meantime) → a new
computation. General assignment plans, Availability blocks.

## Questions
**A — standard decisions:**
- What is the "value" of a task for the business? **Does the value depend on the assigned resource?**
- Which resource features decide the match? **Can one resource handle several requirements?**
- Is the assignment **a plan** (a simulation) or **a binding decision** (then Availability blocks the resources)?
- How often do we recompute, and must the result be **optimal**, or is **good** enough?
- Can a task be carried out **partially** (some of the requirements), or all or nothing?

**B — gaps** (examples):
- mandatory tasks (a contract, a penalty) regardless of value? · preferences/bans (this person not with that customer)?
- stability: may a recomputation reshuffle an announced assignment? · ties between equal results?
- why a task was dropped (an explanation)? · partially available resources (half-time)?

## Mapping steps
1. **Resources → capacity dimensions** — the list of resources with the features relevant to matching; the source of availability (Availability).
2. **Requirements → weight dimensions** — for each requirement a "satisfies" predicate (e.g. level ≥ senior, load capacity ≥ 10 t).
3. **Tasks → items** — name, value (where from), requirements; mandatory tasks and tasks without requirements.
4. **Matching rules** — one resource = one requirement? partial fulfilment? preferences and bans.
5. **Engine** — heuristic / DP / MIP per the table; the order of consideration as a parameter; the "good enough" criterion.
6. **Modules** — the boundary optimization (generic) / simulation (domain adapter); before/after scenarios.
7. **Result status** — a recommendation or a decision; the approval point and the call to Availability; conflict handling.

## Decisions to check (R/A/X)
the definition of value · value depending on the resource · matching predicates · one resource — one or many requirements ·
partial fulfilment · mandatory tasks · the engine (heuristic/DP/MIP) and the quality criterion · the order of consideration ·
recomputation frequency and stability · recommendation vs binding decision · ties.

## Result format
```markdown
# General Assignment model: <area>
## Concept mapping    — | Domain concept | Archetype element | Justification |
## Unmapped concepts
## Capacity dimensions — | Resource | Features | Availability |
## Weight dimensions  — | Requirement | "Satisfies" predicate |
## Items              — | Task | Value (rule) | Requirements | Mandatory |
## Engine             — heuristic/DP/MIP, order, quality criterion
## Modules            — optimization / simulation; before/after scenarios
## Result status      — recommendation/decision, approval, block, conflict
## Decisions (R/A/X)  — | Decision | Source |
## Notes              — assumptions (X), variable policy parameters, boundaries with Availability/Planning
```

## Patterns and pitfalls
- Sorting "by value" without checking the match gives random results — if it is a heuristic, name it explicitly.
- An engine that knows "projects" and "developers" — not testable with examples; the domain only in the **simulation**.
- An assignment that blocks resources immediately makes "what if" impossible — the block only after approval.
- **Outside the archetype:** "who may approve the assignment?" and "may a person be moved from customer X's project?" — authorization
  and policies (the application layer). Variable policies (the value weight, the ban list) come as **parameters** of the engine.

## Quality check
- [ ] resources and requirements mapped; "satisfies" predicates unambiguous
- [ ] the task value defined (and whether it depends on the resource)
- [ ] the engine chosen with a justification (scale, optimality); the order of consideration as a parameter
- [ ] the optimization/simulation split; at least one before/after scenario
- [ ] settled: a recommendation or a decision, where the Availability block happens
- [ ] the mapping table and "Unmapped concepts" present; no material (X)

## Example (shortened)
**Input:** "A renovation company has 5 crews (different permits: gas, electrical, roofing). Every week there are more orders
than crews. We want to take the orders with the highest margin. Is it worth training a second gas crew?"

```markdown
## Capacity dimensions | crew_A | gas, electrical | rota (Availability) | … |
## Weight dimensions  | gas_permit | the crew has "gas" | roof_permit | the crew has "roofing" |
## Items              | bathroom_renovation_12 | margin 8,000 PLN | gas + electrical | no |
## Engine — ≤ 30 orders/week: DP, optimum (A)
## Simulation — before: 5 crews → 41,000 PLN; after: + gas for crew_C → 47,500 PLN; difference 6,500 PLN/week vs the training cost
## Decisions
| one crew = one order per week? | X → asked: "It depends" → parameter `max_orders_per_crew` from the operational policy (A) |
| result = recommendation; the manager approves → crews blocked in Availability | A |
| warranty orders mandatory | X → hot spot |
```
