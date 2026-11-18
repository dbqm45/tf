# The Planning / Parallelization archetype — mapper (stages, dependencies, schedule)

> **Contents:** Fit test · Model (the essence) · Questions · Mapping steps · Decisions to check (R/A/X) · Result format · Patterns and pitfalls · Quality check · Example (shortened)

It turns requirements in which work consists of **stages dependent on each other** into a graph model: stages, explicit
and implicit dependencies (a shared resource), parallel levels, the critical path, cycles and the schedule. The effect: the answer to "what can be done
in parallel?", "how long will it take?" and "what will delay us?" is **computed**, not guessed in a spreadsheet. The common protocol: `SKILL.md` →
"Mapper — the common protocol".

## Fit test
**The core question:** *is there a set of work items, some of which require the results of others, and must their order or
parallelism be determined?* Yes → it fits. The question "who will do it?" → General assignment; "is the resource free?" → Availability.

| Signal in the requirements | Fits? |
|---|---|
| "stage B can start only after A" | ✅ |
| "what can be done in parallel?", "how long will the project take?" | ✅ |
| critical path, penalties for delays, "stage X must start within a window" | ✅ |
| "two stages need the same specialist / equipment" | ✅ an implicit dependency |
| "whom to assign to maximize value?" | ❌ → General assignment |
| "book the excavator for 3–7 May" | ❌ → Availability |
| "order: new → in progress → shipped" | ❌ a state machine / process |
| "who is next for the resource?" | ❌ → Waitlist |
| "an application approval process in steps" | ⚠️ borderline |

**Borderline cases:**
- *Workflow / a business process* — do the steps have **durations and can they run in parallel**, and does the question concern the total time?
  Yes → Planning. A linear flow of statuses of one document → a state machine.
- *Planning employee shifts* — when the stages are not connected by dependencies and the problem is staffing → General assignment + Availability.

## Model (the essence)
**Problem levels:** (1) stages, some require the results of others — what **in parallel**? (2) durations — how long does the project take, which
stages are **critical** (a delay = a delay of the whole, penalties)? (3) stages need the same resources (people, equipment) —
this is also a dependency, even though nobody drew it; (4) the dependencies form a loop — which one to break? (5) the schedule: from a start date,
from a critical stage (it must start within a window), from the availability of selected resources.

| Element | Essence |
|---|---|
| **Stage** | a name, a duration, dependencies on other stages, the needed resources/competences |
| **Explicit dependency** | B requires A |
| **Implicit dependency** | A and B need the same unique resource → they cannot run in parallel |
| **Stage graph** | a topological sort into **parallel levels**; a level = stages with no dependencies between them |
| **Project time** | ≈ the sum of the longest stages of successive levels; exactly — the critical path |
| **Cycle** | contradictory plan rules → the result "no feasible plan" + a proposal of the smallest set of dependencies to remove (a human decides), not a technical exception |
| **Schedule** | a separate computation — calculators: from the start, from a critical stage, from resource availability; the parallelism plan unchanged, only the pinning to the calendar changes |

- The generic graph and the sort live **separately from the domain** (a node carries any payload) — you will use the same algorithm elsewhere.
- **Cooperation:** Planning says **what and in what order**, General assignment — **by whom** (the optimal assignment), Availability —
  **whether the resource is free**, and blocks it. Missing resources → a "demand not met" event for other processes
  (e.g. risk).

## Questions
**A — standard decisions:**
- Which dependencies follow from **the nature of the work**, and which from habit (they can be broken)?
- Can a stage start **before the previous one has fully ended** (partial dependencies)?
- What happens when a stage is **delayed** — whom does it affect, what are the penalties?
- Are durations **certain or estimated** (then ranges / simulation)?

**B — gaps** (examples):
- who approves the plan, and is it **binding** (it blocks resources) or only a simulation? · shared resources between projects ·
  the working calendar (weekends, holidays) · replanning after a delay — automatic or manual? · comparing plan variants ·
  what with a cycle — who decides which dependency to break?

## Mapping steps
1. **Stages** — a list with durations (a value or a range) and the needed resources.
2. **Explicit dependencies** — from the requirements; mark "by nature" vs "by habit".
3. **Implicit dependencies** — derive them from shared unique resources.
4. **Graph and levels** — topological sort; detect cycles → a domain result with a proposal for breaking.
5. **Time and critical path** — critical stages, penalties, time windows.
6. **Schedule** — choose the calculator(s): from the start / from a critical stage / from resource availability.
7. **Boundaries** — what you pass to General assignment (who) and Availability (blocks); the "demand not met" event.
8. **Tests** — business scenarios as examples (see below).

## Decisions to check (R/A/X)
which dependencies are hard · partial dependencies · certainty of durations (value / range) · handling of shared resources ·
the schedule calculator · the working calendar · a binding plan vs a simulation · the reaction to a cycle · the reaction to a delay and penalties ·
who approves the plan.

## Result format
```markdown
# Planning model: <area>
## Concept mapping    — | Domain concept | Archetype element | Justification |
## Unmapped concepts
## Stages             — | Stage | Duration | Resources | Critical? |
## Dependencies       — | From | To | Kind (explicit/implicit) | Hard? | Source |
## Parallel levels    — | Level | Stages | Longest stage |
## Critical path and project time
## Cycles             — detected / proposal for breaking / who decides
## Schedule           — calculator, anchor point, working calendar
## Integrations       — General assignment, Availability, events
## Decisions (R/A/X)  — | Decision | Source |
## Notes              — assumptions (X), edge cases, variable policy parameters
```

## Patterns and pitfalls
- The graph in the domain, the algorithm (topological sort, critical path) behind an interface — generic, with a domain payload.
- Missed implicit dependencies → a plan "parallel" on paper, infeasible in practice.
- A cycle as a technical exception hides a business problem — return a result with a proposal.
- Mixing the plan with the schedule: changing the start date should not recompute the parallelism.
- "May the manager change the plan?" — **authorization outside the archetype**; Planning only computes.
- A variable policy (penalties, buffers, a working calendar depending on the country) → a calculator parameter, not an `if` in the graph.

## Quality check
- [ ] every stage has a duration (or a range) and resources
- [ ] implicit dependencies derived from shared resources
- [ ] parallel levels computed; cycles handled as a domain result
- [ ] the critical path and the schedule calculator chosen
- [ ] the boundaries with General assignment and Availability described
- [ ] the mapping table and "Unmapped concepts" present; no material (X)

**Tests:** business scenarios (e.g. "research and development", "a cascade with a critical stage") as examples — input: stages
and dependencies; result: parallel levels / time / critical stage. Assertions in the language of the domain ("the Design stage is on level 2").

## Example (shortened)
**Input:** "A flat renovation: removing tiles (2 days), electrical (3), plumbing (2), plastering (4) after electrical and plumbing,
painting (2) after plastering. The electrician and the plumber are the same company, one crew. For each day past the deadline — a penalty."

```markdown
## Dependencies — removal → electrical, removal → plumbing (R, explicit) · electrical ↔ plumbing (implicit: the same crew)
## Levels — 1: removal · 2: electrical · 3: plumbing · 4: plastering · 5: painting (without the crew: 2 and 3 in parallel)
## Time — 2+3+2+4+2 = 13 days; critical path: all stages
## Schedule — from the start date; working calendar: A "Saturdays?" — It depends → parameter `working_calendar`
## Unmapped — the penalty per day (→ Pricing/Accounting) · choosing the crew (→ General assignment)
## Decisions — the crew does not split across two stages (X → ask: would a second crew shorten it to 11 days?)
```
