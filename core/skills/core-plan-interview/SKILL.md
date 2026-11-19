---
name: core-plan-interview
description: Use before acting to interview a plan, decision or idea — a decision tree, rounds of questions with a recommendation.
metadata:
  review: "2027-10-09"
  catalog: "Use when a plan, decision or idea has to be interviewed before acting — a decision tree, rounds of questions with a recommendation (only questions independent of each other), facts checked on your own, decisions left to the human, the end only after shared understanding is confirmed. Not for a workshop with domain experts (the facilitation skill, pack-it) or for choosing the team (core-problem-routing)."
  keywords: "przepytaj mnie, przesłuchaj plan, grilling, zadawaj pytania przed planem, pytania z rekomendacją, ranking opcji, którą opcję wybrać, raport z badania, agent sam odpowiada na pytania, agent zaczyna kodować bez zgody, zanim zaczniesz, grill me, interview my plan, ask me before you start, questions with a recommendation, agent answers its own questions, za dużo pytań, przypadki brzegowe, plan urósł, przeinżynierowanie, too many questions, edge cases, over-engineering"
argument-hint: "[plan, decision or idea]"
---

# Plan interview

A conversation meant to reach **shared understanding** before anyone starts work. You treat the subject of the
interview as a **decision tree**: every decision has decisions that depend on it.

## Concepts
- **Frontier** — decisions whose preconditions are all settled. Only those can honestly be asked now.
- **Round** — the whole frontier asked at once and answered in full. It goes well when there are many questions and
  few rounds (e.g. a dozen or so questions in about 3 rounds).

## Procedure
1. Build the tree in your head; do not work it out to the end up front — answers change the tree's shape.
2. **Facts are your job.** What can be checked in the repo, documentation or tools you check yourself (cheap `scout`,
   `researcher`) — you do not ask the human. A check in progress is an unsettled precondition: only the questions that
   depend on it wait, the rest of the frontier you ask right away.
3. **Decisions belong to the human.** You ask each one and wait. An agent that answers its own decision questions
   breaks the whole mechanism.
4. Ask a round in this format:
   ```
   **Q1 — <title>**: <content, the possible options>
   → Recommendation: <your answer and briefly why>

   **Q2 — …**
   ```
   Two questions do not go into one round if one depends on the other. The human answers with numbers (`P1: b`).
5. After the answers, recompute the frontier: settled decisions unlock the next ones. An answer may also force a
   return to an earlier decision — then you go back explicitly.
6. Frontier empty → a summary of what was settled (decisions, assumptions, what stayed out of scope) and the
   question: "Is that how we understand it?". The end only after confirmation. **Without confirmation you do not
   start implementing.**
7. Recording: decisions to the artifact and `decisions.md` (core-project-record), concepts to the glossary
   (pack-it: ddd-facilitation), a decision meeting the ADR threshold → an ADR proposal (the documentation skill, pack-docs).

## Settings
- The human prefers single questions (accessibility, preference) → one question at a time; record it in the
  project's `CLAUDE.md`.
- No fixed question limit — the scope decides (rough numbers: "Scaling the interview"). When the human is
  unavailable: take the recommendations as assumptions and list them (decision gates in pack-it: ddd-facilitation).
- A question only a prototype or mock-up can answer — propose a prototype instead of guessing.

## Scaling the interview
- **Every input artifact holds decisions already made.** Read it before the first question and do not ask about what
  it records. You skip a question only when the artifact literally settles the answer — announce the skip with a
  quote.
- Mark the questions: **[D]** diagnostic (the problem, scope, success criterion) and **[R]** about the solution. With
  a finished code study you skip questions about the state of the code; with a finished reframing you ask only [R].
- Roughly: a simple change 4–6 questions, a medium one 7–10, a complex one 11–15; with a finished study about 1/3
  fewer, with a study and a reframing about half. Show the human the complexity estimate with its rationale
  (systems, integrations, data changes, unknowns) and let them correct it before the first round.
- **A ranking of options as input** (e.g. from a study): the first question is "which option do we implement?" —
  accepting the ranking is an explicit decision by the human, not a silent assumption.
- **New evidence along the way** (e.g. a gap turned out to be a live bug) does not go into the plan silently — it
  becomes a separate question for the human.
- **Option format:** `what it does · strength · cost`; exactly one recommended, based on evidence from the repo or an
  artifact. An option without its own "sensible when …" is dropped (no straw-man alternatives); when the artifacts
  support only one answer, say so: recommendation + "otherwise — I'll explain".
- Questions in the human's language, without the skill's jargon ("the first story that proves the product works",
  not "north star").

## When the interview breaks
- **The agent answers decision questions itself or starts implementing** — most often when the interview is part of
  a "solve the ticket" task: the task framing looks like consent. Prevention: in the project's `CLAUDE.md` the line
  "Do not implement without explicit consent after the interview".
- **A weaker model** collapses the rounds into 2–3 general questions and an outline → switch to a stronger model or
  single-question mode; do not shorten the procedure.
- **Dependent questions in one round** (the frontier is the agent's judgement, not a computed graph) → the human
  points out the dependency, the agent explicitly reopens the branch in the next round.
- **Scope too big for one session** (dozens of decisions, several areas) → first a map: a list of areas and their
  dependencies as separate tasks in `docs/project/`, then an interview for each task separately.

## Without excess
An interview without context pulls out every edge case as something to solve and ends in over-engineering. You rank
questions by impact and likelihood; the answer "just fail with a readable error" is fully valid (the minimalism
ladder: eng-design-principles in pack-it). Process warning signs: a backlog of generated tickets nobody will do, and
PR descriptions longer than anyone will read.

## Anti-patterns
Starting work without consent; shortening the interview to a few generalities; all questions computed up front
instead of recomputing the frontier; asking the human about facts from the repo; mixing dependent questions in one
round.

## Example
**Situation:** "I'm adding a CSV export of orders in the admin panel — grill me". The roles in the panel and the
number of orders (about 2 million) are established by `scout`, not the human. **Result (round 1, independent
questions only):**
```
**Q1 — Who exports**: a) admin, b) admin and support → Recommendation: a — the file holds customer data.
**Q2 — Personal data**: a) full, b) none, c) selectable → Recommendation: b — no copy of the data outside the system.
**Q3 — Filters**: a) dates, b) dates and status → Recommendation: b — covers the described case.
```
How a large file is delivered waits for round 2 — it depends on the filters from Q3.

More examples: `references/examples.md`.

## Source
The 10xDevs course, ed. 3 (2026), module 2 (step planning, roadmap) and module 4, lesson 4 (the decision gate in the
plan) — training material (accessed 2026-10-09).
[mattpocock/skills](https://github.com/mattpocock/skills) (MIT), the `grilling` skill; description:
[aihero.dev](https://www.aihero.dev/skills-grilling). Described in our own words.
