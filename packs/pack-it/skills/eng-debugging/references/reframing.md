# Reframing — are we solving the right problem

Investigation fills in missing data; reframing corrects a wrongly posed problem. The order depends on what is blocking.

## When
- a second failed fix of the same symptom;
- the investigation opens more and more questions instead of narrowing down to a contract;
- the implementation once again does not meet the criteria or persistently deviates from the plan in the same way;
- the report combines a symptom with a cause and a fix ("X breaks, let's do Y");
- a lack of expertise in the area.

Not for mechanical changes or when the human has verified the cause themselves.

## Procedure
1. **Separate three things and read them back to the human:** the observation (the literal effect) · the assumed cause or
   approach · the proposed direction. Only the observation is certain, the rest are hypotheses. You do not merge them, even when
   the human pushes "just plan the fix".
2. **One round of 1–3 questions** narrowing down the observation (which symptom is the main one, one or several, a single case or
   a class), with the option "I don't know / I didn't separate them". The options describe observations, never causes or fixes.
3. **A map of dimensions** from the code and documents read: every stage of the chain (input, transformation, state, side
   effects — or the axes of a design decision) in which the problem could arise. Mark where the human's assumption
   lands. You skip a dimension with no trace in the material.
4. **Hypotheses in parallel** — 2–4 (at most 5 read-only workers, the assignment in one message). Each one gets
   the literal observation, one hypothesis and the question "what traces would have to exist if the problem were here — and do they?".
   The result: strong / weak / none, with `file:line`.
5. **Deciding questions** (2–5 in total): each one shifts the ranking of the hypotheses; always with the option "I haven't checked". The evidence
   is unambiguous → skip them and say why.
6. **A test from a different side:** a new worker gets only the observation, without the name of the leading hypothesis; you look for similar
   events in the history (commits, reports, tickets); you check what the hypothesis requires and what it forbids.
   A contradiction → go back to step 4.
7. **A record** `frame.md` next to the step report (80–150 lines): the observation (verbatim) · the original framing (kept) ·
   the map of dimensions · a table Hypothesis | Evidence | Verdict · narrowing signals · the problem reframed or confirmed
   (one sentence) · confidence (high / medium / low + what to check before the plan) · what changes in the plan.

## Rules
- "The original framing was right" is a fully valid result — you do not invent a reframing by force.
- No designing of the solution (phases, files, technical decisions) — the step plan does that.
- Hypotheses from the map of this material, not from "I've seen this in other systems"; a hunch without `file:line` does not go
  into the result.
- The limit: 2–4 rounds of workers and 2–5 questions. Longer → a reproduction or data collection is needed, not analysis.
- The human's objection → a new round of hypotheses with their argument, not a defence of the thesis.
- The step plan that got `frame.md` does not repeat the diagnostic questions; with "low" confidence it asks one: first
  verification or a plan with a risk.

## Example
The report: "duplicate invoices — let's add a unique index". The observation: two invoices with the same order number,
both entries approx. 2 s apart. The assumed cause: no lock in the database. The direction: an index. The map: a button in the UI →
a request → a queue → a consumer → a write. Hypotheses: (a) a double click, (b) a retry from the queue without idempotency,
(c) a race of two consumers. Evidence: in the broker logs the same message id delivered twice after the acknowledgement
limit was exceeded → (b) strong. Reframing: the problem is a consumer without idempotency (be-messaging-outbox); an index
would turn the duplicate into a 500 error on a retry.

## Sources
- The 10xDevs course, ed. 3 (2026), module 2, lesson 4 (reframing as a lifeline in planning) — training
  material (accessed 2026-10-09).
Described in our own words.
