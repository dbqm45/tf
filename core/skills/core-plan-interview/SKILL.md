---
name: core-plan-interview
description: Use when a plan, decision or idea must be questioned before work starts — rounds of independent questions with recommendations, facts checked by you, confirmation.
argument-hint: "[plan, decision or idea]"
metadata:
  review: "2027-11-20"
  catalog: "Use when the human asks to be interviewed or questioned about a plan, decision or idea before anything is built, when an agent answered its own decision questions or started coding mid-interview, when an interview drowns in edge-case questions, or when a study's ranking of options has to be accepted — rounds of questions that can be asked now, one recommendation per question, facts looked up by the agent, a summary confirmed by the human, recording of decisions. Not for workshops with domain experts on shared vocabulary (ddd-facilitation, pack-it) or choosing which team or skill handles a task (core-problem-routing)."
  keywords: "przepytaj mnie, przesłuchaj mój plan, wypytaj mnie, zadaj mi pytania, zanim zaczniesz, zapytaj mnie przed startem, grill me, wywiad o planie, doprecyzuj plan, pytania przed implementacją, plan w głowie, rundy pytań, rekomendacja do pytania, agent sam odpowiada na pytania, agent zaczął kodować, za dużo pytań, przypadki brzegowe, 40 pytań, przeinżynierowanie, ranking opcji, którą opcję wybrać, raport z badania, potwierdzenie planu, czy tak to rozumiemy, jedno pytanie naraz, człowiek niedostępny, założenia, interview me, question my plan, grill my plan, ask me before you start, clarify the plan, questions before implementation, decision questions, agent answered its own questions, too many questions, edge cases, over-engineering, ranking of options, confirm the plan, one question at a time"
---

# Plan interview — ask in rounds, recommend, confirm before acting

The goal is shared understanding of a plan before any implementation. You ask, the human decides; you never answer
their decisions for them, and you never start building before they confirm the summary.

## Before round 1
1. **Read every input** — the brief, a study, a ranking, a reframing, the relevant code. A question that an input
   already settles is skipped; say so and quote the line.
2. **Facts are your job.** Versions, existing modules, data sizes, roles, configuration: look them up (grep, config files,
   a cheap read-only scout or researcher subagent). Never ask the human what the repository can answer. A lookup still
   running blocks only the questions that depend on it.
3. **Decisions are the human's.** Scope, risk appetite, trade-offs, policy, priorities: ask and wait.
4. **Estimate the size** and show it with reasons (systems touched, integrations, data changes, unknowns): roughly
   4–6 questions for a simple change, 7–10 for a medium one, 11–15 for a complex one, fewer when a study already exists.
   The human may adjust it. These are soft ranges, not a quota.
5. **Too big for one session** (several areas, dozens of decisions) → first write a map of the areas and their
   dependencies as separate tasks under docs/project/, then interview one task at a time.

## Rounds
- See the subject as decisions that depend on each other. In each round ask **every question that can be asked now** —
  those whose preconditions are already settled. Many questions per round, few rounds (around a dozen questions in
  about three rounds is typical).
- Do not draft the full question list up front: answers change what comes next. After each set of answers, work out
  again which questions are now open.
- Two questions where one depends on the other never go in the same round; the dependent one waits.
- An answer that changes an earlier decision → say so and reopen it explicitly.
- Evidence found during the interview (e.g. the "missing feature" is actually a live bug) becomes its own question,
  not a silent change to the plan.
- A question only a prototype or mock-up can settle → propose building one instead of speculating.

## Question format
```
Round 1 — 3 questions, answer by number (e.g. "Q1: b, Q2: ok, Q3: own answer")

Q1. Message ordering
   a) per key (all events for one order in sequence) — matches today's behaviour; costs partition planning
   b) none — simplest; consumers must tolerate reordering
   Recommendation: a — the invoice consumer assumes order (billing/consumer.ts:41).
```
- Exactly one recommended answer per question, backed by evidence from the code or an input.
- Each option in one line: what it does, its strength, its cost. Drop options nobody would sensibly pick.
- If the evidence supports only one answer, say so and invite correction.
- Plain language in the human's own words; no process jargon. Mark questions as diagnostic (problem, scope, success
  criterion) or solution questions; with a finished code study skip code-state questions, with a finished reframing ask
  only solution questions.

## Keep it proportionate
- Rank questions by impact and likelihood. Treating every edge case as something to solve leads to over-engineering;
  "fail with a clear, readable error" is a perfectly good answer for unlikely cases. Prefer the minimal design
  (the minimalism ladder in eng-design-principles, pack-it).
- Warning signs of a bloated interview: dozens of generated tickets nobody will do, plans that grow from days to weeks,
  PR descriptions nobody reads.

## Input with a ranking of options
When a study or report ranks options, the **first** question is which option to pursue. Accepting the ranking is an
explicit decision by the human, never an assumption. State which questions you will not ask because the study already
answered them (quote it), and still give a recommendation for each question you do ask.

## Ending
1. When no open questions remain: summarise **decisions**, **assumptions**, **out of scope**, and ask
   "Is that how we understand it?" No implementation until the human confirms.
2. Record: decisions in the artifact and `decisions.md` (core-project-record); new terms in the glossary
   (ddd-facilitation); an ADR proposal when a decision meets the ADR threshold (documentation skill, pack-docs).
3. **Human unavailable** (on leave, not answering): turn the recommendations into explicitly labelled assumptions
   A1…An, list them, implement nothing, and wait for confirmation.
4. **One question at a time** preferred (accessibility, taste): honour it and offer to record the preference in the
   project's CLAUDE.md.

## Failure modes
| Symptom | Fix |
|---|---|
| The agent answers its own decision questions or starts coding (often when the interview sits inside a "solve the ticket" task) | Stop, explain, restart. Add to the project's CLAUDE.md: "After a plan interview, implement nothing without the human's explicit consent to the confirmed summary." |
| A weaker model collapses to 2–3 vague questions | Use a stronger model or one-question mode; do not shorten the procedure |
| Dependent questions asked together | When the human points it out, reopen that branch in the next round |
| Questions about facts in the repo | Look them up yourself, report what you found |
| Full question list produced up front | Ask only what can be asked now; recompute after answers |

## Example
"I'm moving our queue from RabbitMQ to Kafka — interview me first."
- Facts checked first: 4 consumers found in the services directory, messages ~2 KB, no ordering code except in billing.
- Size: complex (two systems, four consumers, a cutover) → about 11–13 questions; the human agrees.
- Round 1 (independent): ordering needs, retention period, which consumers move first, rollback expectation — each with
  a recommendation.
- Held back: "cutover method (dual-write vs. replay)" — depends on the consumer answers; it goes to round 2.
- End: summary of 12 decisions, 2 assumptions, out of scope "schema registry"; "Is that how we understand it?" → the
  human confirms → decisions written to `decisions.md`.

More worked examples (auth migration, feature flag, unavailable human): `references/examples.md`.

## Checklist
- [ ] inputs read; facts looked up, not asked
- [ ] size estimated with reasons and accepted
- [ ] each round = only questions that can be asked now; dependent ones held back
- [ ] one recommendation per question, with evidence
- [ ] summary (decisions, assumptions, out of scope) confirmed before any implementation
- [ ] decisions recorded; preferences in CLAUDE.md when asked
