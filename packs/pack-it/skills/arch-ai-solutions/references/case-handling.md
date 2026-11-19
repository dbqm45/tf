# AI in handling a large volume of cases

A pattern built from elements the factory has separately (a golden set and calibration — ai-evals; a saga — ddd-tactical-design;
idempotency — be-messaging-outbox). S. Yegge's description ("Counting House", 2026-10) came from conversations with companies, without
data from deployments — treat it as a design to verify, not a result.

## 1. Policy table per intent
Every intent (case type) has its own autonomy threshold:
| Threshold | What the model does | Who decides |
|---|---|---|
| off | nothing | a human |
| shadow | answers in parallel with the human, the answer is scored, invisible to the customer | a human |
| assist | a suggestion for the human | a human |
| contain | answers the customer | the model, without state changes |
| transact | changes state through the orchestrator | the model within the policy limit |

An intent is promoted to a higher threshold only after an evaluation on a golden set from human ratings and after the owners sign off
(operations, finance, legal). This is the same logic as "permissions grow with evidence" in core-async-delegation §5.

## 2. A confusion matrix with costs
Accuracy is not enough. For intents that are easy to confuse, every off-diagonal cell has a cost: a routing mistake
to a queue is something else than missed help for a customer in a difficult situation. For payouts precision counts, for cases
that harm the customer — recall. You compare the same matrix for people (the cost of errors + the cost of work), not only the model
against zero errors.

## 3. The model proposes, the orchestrator executes
- The model issues a **write intent** in a schema (e.g. `{"action": "refund", "order_id": …, "amount": …}`).
- The orchestrator (code) checks the permission on the **live source system**, not on the copy the model read; it assigns
  an idempotency key from the request fields; it approves automatically up to the policy's threshold, above it — a human.
- Execution as a saga with compensating actions and a read after the write.
- A refusal with a reason code goes to the right human queue.
- The model has no credentials to the systems and does not see PII (a gateway that tokenizes PII reversibly).

## 4. The judge and the golden set
An LLM judge only where it agrees with people as often as people agree with each other, never tuned on the golden
set (ai-evals, `references/datasets-and-graders.md` §7). The golden set and the evaluations are the company's property — they
are what lets you change the model for a cheaper one.

From the article without an entry: the "model welfare" thread. What stays is the practice: a truthful prompt, without threats and false
urgency, and the model has the right to refuse with a reason code and a proposed fix to the procedure.
