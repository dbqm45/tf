---
name: proc-agile
description: Use for organizing a team's work — Scrum, Kanban and flow metrics, user stories (INVEST), Definition of Done.
metadata:
  review: "2027-10-17"
  catalog: "Use when planning and organizing a team's work — the values and principles of the Agile Manifesto, Scrum (Scrum Guide 2020 + Expansion Pack 2025), Kanban and flow metrics, user stories (INVEST, vertical slicing, story map, splitting patterns), Definition of Done, forecasting. Not for scaling across many teams (proc-safe) or flow economics."
  keywords: "jeden zespół, Scrum czy Kanban, sprint, retrospektywa, daily, planowanie sprintu, tablica Kanban, limit WIP, mapa historyjek, story map, co wejdzie do pierwszego wydania, historyjka nie mieści się w sprincie, podzielić historyjkę, za duża historyjka, nikt nie widzi całości backlogu, pociąć historyjkę, cięcie pionowe, historyjka rozbita na zadania, one team, Scrum or Kanban, retrospective, sprint planning, Kanban board, WIP limit, user story map, what goes into the first release, story does not fit in a sprint, split a story, story too big, nobody sees the whole backlog, slice a story, vertical slicing, story split into tasks"
---

# Agile: Scrum and Kanban in practice

## The Manifesto — the core
Individuals and interactions, working software, customer collaboration, responding to change — **over** processes and tools,
documentation, contract negotiation and following a plan (the items on the right have value too). Key principles: frequent
delivery of working software, changing requirements are welcome, daily collaboration between the business and the team,
a sustainable pace, simplicity — the art of maximizing the amount of work **not done**, regular reflection and adjustment.

## Scrum (Scrum Guide 2020)
- **Pillars of empiricism**: transparency, inspection, adaptation. **Values**: commitment, focus, openness, respect, courage.
- **Accountabilities**: Developers (how), Product Owner (what and in what order, maximizing value), Scrum Master (the effectiveness of the team and of Scrum).
- **Events**: Sprint (≤ 1 month), Sprint Planning (why/what/how), Daily Scrum (15 min, progress toward the Sprint Goal),
  Sprint Review (inspecting the outcome with stakeholders), Sprint Retrospective (how we work).
- **Artifacts and commitments**: Product Backlog → **Product Goal**; Sprint Backlog → **Sprint Goal**; Increment → **Definition of Done**.
- **Expansion Pack (2025)** — an optional *addition*, not a replacement: an emphasis on outcomes instead of features alone,
  working under uncertainty, teams using AI.

## Kanban
- Visualize the flow, **limit work in progress (WIP)**, actively manage the flow, explicit policies (e.g. a definition of "done" for columns), improve.
- **Flow metrics**: WIP, throughput, cycle time, **work item age** (the best early signal of a problem).
- Rule: finish before you start new work ("stop starting, start finishing").
- **Specification in the cycle (working with agents):** the backlog and refinement are at the level of the goal and intent; the contract matures
  in the sprint (Scrum) or just before the commitment point (Kanban, with a WIP limit on the analysis stage so that specifications
  do not age in the queue). Definition of Ready is the team's agreement on input quality, not a gate against the PO. You choose the level
  of specification (spec-first, spec-anchored, spec-as-source — B. Böckeler) to fit the problem and measure cycle time,
  the rework rate and the ratio of Markdown lines to code, instead of trusting the feeling of speeding up.

## Stories and the backlog
- A story = a user need and value, not a technical task: "As a … I want … so that …" + **acceptance criteria** (Given/When/Then — eng-testing).
- Stories follow INVEST and are cut vertically; from Event Storming results you cut along events (ddd-event-storming); example: `references/examples.md` §2.
- A **story map**, when the backlog is long and nobody sees the whole: a backbone of user activities and steps
  (left to right), stories under each step (the most important first), horizontal release lines — the first release
  is the thinnest slice through all the steps that delivers an outcome (a walking skeleton). Patterns for splitting a story that is too big
  (flow steps, rule variants, data, interfaces, paths, a spike): `references/map-and-split.md`.
- A shared, verifiable **Definition of Done** (tests, review, documentation, deployed to an environment…).

## Forecasting
Instead of promises from estimates — forecasts from data: historical throughput + a Monte Carlo simulation ("85% chance of X items by date Y").
Treat estimates (e.g. points) as a tool for a conversation about understanding, not a measure of productivity.

## Anti-patterns
"Scrum ceremonies without empiricism", the sprint as a mini-waterfall, the Daily as a report to a manager, velocity as a goal,
a backlog as a wish list with no order, no working increment at the end of the sprint.

## Example
**Situation:** "How many items will you finish in 6 weeks?" Throughput over 10 weeks: 4, 6, 3, 5, 7, 2, 5, 6, 4, 5.
**Result:** instead of the average × 6 (≈ 28, i.e. about a 50% chance) — Monte Carlo, 10,000 simulations drawing weeks
from the history:

| Confidence | 50% | 70% | 85% | 95% |
|---|---|---|---|---|
| Items in 6 weeks (at least) | 28 | 26 | 25 | 22 |

Answer: "an 85% chance of at least 25 items in 6 weeks"; you refresh the forecast every week.

More examples: `references/examples.md`.
