# The Activity / Process archetype — mapper (procedures, activities, work orders)

> **Contents:** Fit test · Model (the essence) · Questions · Mapping steps · Decisions to check (R/A/X) · Result format · Patterns and pitfalls · Quality check · Example (shortened)

It turns requirements about **work** (an inspection, a repair, a rollout, handling a ticket) into a model that separates the procedure
(how the work should proceed) from the execution (what was actually done, by whom, when, with what result). The effect: you can
answer "was it done according to the procedure?", account for working time and reconstruct the course of events, instead of keeping everything
in one `status` field. The common protocol: `SKILL.md` → "Mapper — the common protocol".

## Fit test
**The core question:** *do you need to distinguish HOW the work should proceed (the procedure, the template) from what was ACTUALLY
done, by whom, when and with what result?* Yes → it fits. If only when the work is to take place matters → Planning.

| Signal in the requirements | Fits? |
|---|---|
| "procedure / checklist / instruction", "according to the procedure" | ✅ activity specification |
| "work order", "who performed it, when, with what result" | ✅ execution |
| "working time on the order", "many performers, roles" | ✅ assignments and time tracking |
| "a suspended / interrupted / abandoned order" | ✅ execution states |
| "schedule, parallel levels, critical path" | ❌ → Planning (`planning.md`) |
| "a queue of those waiting for a released place" | ❌ → Waitlist |
| "who should perform it so the cost is minimal" | ❌ → General assignment |
| "what we are working on, what state the device is in" | ❌ → `resource-service.md` |
| "workflow engine / Camunda / task queue" | ❌ a technique, not a domain model |
| "an approval process with many paths" | ⚠️ borderline |

**Borderline cases:**
- *An approval process* — if it only changes the state of a document, a state machine is enough; if it has a procedure, performers
  and time, it is Activity.
- *Schedule vs execution* — the plan says **when** something is to be done; the execution, **what was done**. The plan and the execution are two
  entities (see the plan and the protocol below); dates from the plan do not overwrite facts.
- *Decision rules inside a step* — decisions are a separate notation and a separate module, not part of the activity.

## Model (the essence)
The factory's modelling reasoning; the sources in `## Sources` confirm only the facts indicated there.

- **Activity specification (procedure) vs the actual activity** — the procedure has steps, a structure (an activity composed of steps)
  and **a version**; the execution points to the version it followed. This is our conclusion from the type/instance convention; the pattern
  literature (Hay) has chapters on procedures and activities, but we do not attribute the chapters' content `[assumption]`.
- **The work chain** (concept names after Silverston's data models): the work requirement → the work order or
  work execution (work effort) → the assignment of parties with roles (Work Effort Party Assignment) → time tracking
  (Work Effort Time Tracking). The requirement says **what is needed**, the execution **what was done**; one requirement
  may yield many executions and vice versa.
- **Proposed vs implemented action** — Fowler (ch. 8) separates "Proposed and Implemented Action", as well as "Completed
  and Abandoned Actions" and "Suspension". In our model: the states `proposed → started → suspended ⇄ started →
  completed | abandoned`, each transition as an event with a time and a person.
- **Plan and protocol** — Fowler's ch. 8 also contains "Plan" and "Protocol". We understand them this way: a plan is an intended sequence
  of actions, a protocol is the pattern of conduct by which a plan is created. Scheduling is Planning.
- **Accountability between parties** — who is responsible for what towards whom (Fowler's ch. 2 is titled "Accountability").
  The performer's role in an activity is a relationship with a party (Party), not a text attribute; permissions stay outside the archetype.
- **Time tracking** — working time is separate entries (who, from–to, the order), not an `hours` field. Totals and costs are computed by
  Accounting / Pricing.
- **Step result** — the result is execution data (a rating, a measurement, a remark), with a type defined in the step specification.

**Choosing the notation** (when what):

| Notation | When | Note |
|---|---|---|
| BPMN 2.0.2 (OMG, January 2014) | a process with a course known in advance | ISO/IEC 19510:2013 corresponds, according to OMG, to version 2.0.1 |
| CMMN 1.1 (OMG, December 2016) | a case, the course depends on people's decisions | do not force a sequence |
| DMN 1.5 (OMG, formal/24-01-01, 2024) | decisions and rules (decision tables) | DMN 1.6 was in beta (September 2024); status in 2026 `[unverified]` |

- **Control-flow patterns** (van der Aalst et al. 2003) serve as **a checklist of cases**: parallelism,
  synchronization, choice, cancellation. For each step ask whether any of them occurs and how it affects the states.
- **A workflow engine is a technique**: the domain model describes activities and states; the engine is an implementation choice.

## Questions
**A — standard decisions:**
- Is there a **procedure** (steps, version)? Who changes it, and do executions remember the version?
- Where does the work come from: a requirement, a ticket, a schedule? One order – one execution, or many?
- What **states** does the execution have (suspended, abandoned, resumed)? Who changes them and with what justification?
- What performer **roles**, and does one step have many performers?
- Do we track **working time**, and at what level (order, step)?
- What course: known in advance (BPMN), dependent on people's decisions (CMMN), or driven by rules (DMN)?

**B — gaps** (examples):
- parallel activities and synchronization · cancelling a step in progress · repeating a step · changing the procedure during
  execution · a negative step result (what next) · a composite activity completed partially · corrections after completion (reopen) ·
  attachments/evidence · change audit · deadlines and escalations (a parameter, not the archetype's logic).

## Mapping steps
1. **Separate** the procedure (the specification) from the execution; settle versioning.
2. **The procedure's structure** — steps, order, result types; an activity composed of steps.
3. **The source of the work** — requirement → order; 1–N relationships.
4. **Execution states** — proposed, started, suspended, completed, abandoned; transition events.
5. **Parties and roles** — assignments with a role and a period (the interface with Party); who is responsible.
6. **Working time** — time entries; refer the totals to Accounting.
7. **Flow cases** — go through the list: parallelism, synchronization, choice, cancellation.
8. **Boundaries** — Planning (dates), General assignment (who), resource-service (on what), the engine (technique).

## Decisions to check (R/A/X)
Procedure versioning · the number of executions per order · the list of states and transitions · suspension/abandonment · performer roles ·
the level of time tracking · a negative step result · changing the procedure mid-way · the notation (BPMN/CMMN/DMN) · reopening.

## Result format
```markdown
# Activity / Process model: <area>
## Procedures            — | Procedure | Version | Steps (order) | Step result type |
## Executions            — | Order | Procedure (version) | Source (requirement) | States |
## States and transitions — | State | Event | Next state | Who / justification |
## Assignments and time  — | Execution | Party | Role | Period | Time entry |
## Flow cases            — | Case (parallelism / synchronization / choice / cancellation) | Where | Rule |
## Concept mapping       — | Domain concept | Archetype element | Justification |
## Unmapped concepts
## Integrations          — | Event | From / to archetype | Reaction |
## Decisions (R/A/X)     — | Decision | Source |
## Notes                 — assumptions (X), notation, variable policy parameters, [unverified]
```

## Patterns and pitfalls
- One `status` field and one `performer` field instead of events and assignments: you lose history, suspensions and roles.
- A procedure edited "in place" – old executions lose their point of reference. Version it or copy the steps into the execution.
- Mixing the plan with the execution: a moved date does not change the fact that the step was done earlier or later.
- Assuming that every process is a sequence; cases with people's decisions (CMMN) require states, not a rigid order.
- A workflow engine as the domain model: the engine's states are not business concepts; step names should come from the expert's language.
- Rules ("if the result < threshold, then repeat") hard-coded into the activity – that is a variable policy, pass it as a parameter.
- Authorization "who may approve a step" – outside the archetype; the archetype records who did it.

## Quality check
- [ ] the procedure separated from the execution; the version recorded in the execution
- [ ] execution states include suspension and abandonment, with transitions as events
- [ ] party assignments have a role and a period; working time is separate entries
- [ ] the flow cases reviewed (parallelism, synchronization, choice, cancellation)
- [ ] the boundaries with Planning, General assignment and `resource-service.md` described
- [ ] the mapping table and "Unmapped concepts" present; no material (X)

## Example (shortened)
**Input:** `[example]` "A vehicle's technical inspection according to a procedure with a checklist (brakes, lights, exhaust emissions).
The inspector performs the inspection; each item gets a positive or negative result; we track the inspector's working time."

```markdown
## Procedures — | passenger car inspection | v3 | brakes → lights → exhaust (any order) | positive/negative + remark |
## Executions — | inspection of vehicle X | passenger car inspection v3 | customer request | proposed → started → completed |
## Assignments and time — | inspection X | inspector A | performer | 10:00–10:40 | time entry 40 min |
## Flow cases — choice: negative brake result → inspection completed with a negative verdict (X → ask
   whether to continue the remaining items) · cancellation: the customer drives away mid-way → abandoned with a justification
## Unmapped — the inspection price (→ Pricing) · the inspection bay (→ resource-service / Availability) ·
   the visit date (→ Availability / Planning)
## Decisions — procedure version recorded in the execution (R) · time at the order level (X, small) ·
   the effect of a negative result (X → ask)
```

## Sources
Accessed 2026-10-17.
- D. Hay, "Data Model Patterns: Conventions of Thought", Dorset House 1996 — **a book; table of contents confirmed in a library catalog**; the chapter "Procedures and Activities" is confirmed. The ISBNs in the sources contradict each other, we do not give one. The distinction "specification vs actual activity" in the chapter's content was not confirmed `[assumption]` from the type/instance convention. In "Enterprise Model Patterns" (Technics Publications, ISBN 978-1-935504-05-4, year 2011 partly confirmed) ch. 7 "Activities" concerns defining activities and their breakdown.
- L. Silverston, "The Data Model Resource Book", Vol. 1 Revised Edition, Wiley 2001, ISBN 978-0-471-38023-8 — **a book; table of contents confirmed at O'Reilly (secondary)**; partly confirmed concepts: work requirement, work effort, Work Effort Party Assignment, Work Effort Time Tracking.
- M. Fowler, "Analysis Patterns: Reusable Object Models", Addison-Wesley 1997 (the author gives 1996), ISBN 0-201-89542-0 — **a book; table of contents confirmed at the publisher (InformIT)**; titles: ch. 8 "Planning" (Proposed and Implemented Action, Completed and Abandoned Actions, Suspension, Plan, Protocol), ch. 2 "Accountability". The content of the patterns described in our own words and with the factory's interpretation.
- OMG, BPMN 2.0.2 (formal, January 2014); ISO/IEC 19510:2013 corresponds, according to OMG, to version 2.0.1 — **a standard/specification, primary**; the version and its use; the specification itself was not read, the concepts are general knowledge.
- OMG, CMMN 1.1 (December 2016) — **primary**; the version.
- OMG, DMN 1.5 (formal/24-01-01, 2024) — **primary, partly confirmed**; version 1.6 in beta since September 2024, its status in 2026 not confirmed.
- W. M. P. van der Aalst, A. H. M. ter Hofstede, B. Kiepuszewski, A. P. Barros, "Workflow Patterns", Distributed and Parallel Databases 14(1), 5–51, 2003 — **primary (an article)**; control patterns as a checklist. The extension of the list in 2006 and the data/resource perspectives partly confirmed.

Described in our own words; the content of books and standards was not quoted.
