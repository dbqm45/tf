# Re-framing a problem that may be misnamed

Some problems resist fixing because the request names the wrong problem: it arrives with a cause and a solution already attached
("duplicates — add a unique index"). Before another fix, check the framing itself.

## When to use it
- a second fix of the same symptom did not help;
- the investigation keeps opening new questions instead of narrowing;
- the plan keeps deviating from what was agreed;
- the report mixes the symptom, a presumed cause and a proposed fix in one sentence;
- the area needs domain knowledge you do not have.
Not for mechanical changes, or when the human has already verified the cause.

## Steps
1. **Take the report apart** into three lines and read them back to the human:
   - *observation* — what was actually seen, verbatim where possible;
   - *assumed cause* — what the reporter thinks is behind it;
   - *proposed direction* — the fix they suggest.
2. **One round of narrowing questions** (1–3), each offering "I don't know" as an answer. The options describe observations
   ("does the duplicate have the same timestamp?"), never causes ("is it a race condition?").
3. **Map where the problem could live.** List the stages of the chain the observation passes through — input, transformation, stored
   state, side effects (messages, emails, external calls) — and mark the stage the assumed cause points to. The other stages are the
   alternatives the framing ignored.
4. **Test 2–4 hypotheses in parallel**, one per stage worth checking. Each read-only worker (at most five) receives the literal
   observation, one hypothesis, and the question "what traces would exist in code, data or logs if this were true?". It returns a verdict —
   strong / weak / none — with `file:line` or log evidence.
5. **Deciding questions** (2–5) for the human, each with a "haven't checked" option — skipped when the evidence is unambiguous.
6. **Cross-check.** A worker that sees only the observation (not the original framing) proposes its own explanation; search history and
   tickets for similar events; for the winning hypothesis list what it requires and what it forbids, and check one of each.
7. **Write `frame.md`** next to the step report (aim for 80–150 lines):
   - the observation verbatim and the original framing;
   - the chain map with the marked stage;
   - a table hypothesis / evidence / verdict;
   - the narrowing signals (answers, logs) that decided it;
   - the statement: *re-framed as …* or *original framing confirmed*;
   - confidence high / medium / low and what would raise it;
   - what changes in the plan.

## Rules
- "The original framing was right" is a valid outcome.
- No solution design here — the output is a better-named problem, the fix follows the normal procedure.
- Hypotheses come from this material and cite `file:line`; no generic lists of possible causes.
- Limits: 2–4 rounds of workers, 2–5 questions. If the human objects to the result, run a new round with their objection as input.
- Low confidence → the plan starts with one verification question or experiment.

## Example — duplicate invoices
Report: "Duplicate invoices — let's add a lock in the database." Third fix attempt failed.
- Taken apart: *observation* — some customers receive two invoices with different numbers for one order; *assumed cause* — two parallel
  inserts; *proposed direction* — a unique index or lock.
- Questions: "Do the two invoices have the same creation second?" → no, 4–6 minutes apart. "Does it happen after deployments or restarts?"
  → don't know.
- Chain map: order event → consumer → invoice creation → number allocation → email. The assumed cause points at *creation* (concurrency).
- Hypotheses: (a) concurrent inserts — **none**: timestamps minutes apart, `invoices.py:58` already runs in one transaction;
  (b) the queue redelivers the event and the consumer is not idempotent — **strong**: visibility timeout 300 s in `queue.yaml:12`,
  the consumer acknowledges after sending the email (`consumer.py:91`), the email call sometimes takes over 300 s in logs;
  (c) the frontend submits the order twice — **weak**: one order id per pair.
- Re-framed: "the invoice consumer is not idempotent under redelivery". A unique index on the invoice number would not help — the
  numbers differ. Confidence: high. Plan change: idempotency key = order id in the consumer, acknowledge before slow side effects.
