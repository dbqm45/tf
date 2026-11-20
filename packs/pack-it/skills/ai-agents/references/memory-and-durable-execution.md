# Agent memory and durable execution

## 1. Five questions instead of one vector index
| Memory | Question | Contract |
|---|---|---|
| working | what is in the current context | assembled from the others; a token budget and an order |
| semantic | what is true | a source, a verification date; consolidation replaces the old fact, it does not add a second one |
| episodic | what happened | time, context, result; it loses usefulness, not truthfulness |
| procedural | how to do it | a version, a review, a withdrawal; a write like a merge request, because a bad entry changes behaviour in many tasks |
| profile | who the user is | a short document always in the prompt, a patch in place |

A physical split into separate stores only after a symptom (a stale fact comes back as current, a temporary entry
competes with a permanent one). A type field and an expiry date in one store are often enough. Equivalents in the factory:
`docs/project/lessons.md` (semantic), the log and checkpoints (episodic), skills changed through a PR
(procedural). A write to memory is untrusted input (sec-llm-security, `references/agent-design-patterns.md` §7).
Source: J. Wąsowski, "AI Agent Memory Types…" (2026-10-08); the comparison results from the article [unverified].

## 2. Durable execution
The gain depends on the **step boundaries**, not on the tool:
- one step for every costly model or tool call; one step for the whole loop is only a queue with extras;
- everything outside a step runs again on resumption. Inngest saves the step result and on the next
  invocation looks it up by a hash of the step name; in Temporal the workflow code must be deterministic (clock, randomness,
  HTTP only in activities); DBOS saves step checkpoints in Postgres;
- **durability is not idempotency**: a step that charged a card and did not manage to report success will run a second time
  without an idempotency key at the payment provider (be-messaging-outbox).

Configuration traps:
- saving the checkpoint in the background can lose the last step;
- resumption with the same input overwrites the state;
- no fixed workflow id means that a second run starts next to the first;
- renaming a step orphans runs in progress, so you version the steps.

Choice:
- the agent is already a graph → a graph with a checkpointer in Postgres;
- the state must be in the same transaction as the data → DBOS;
- step data must not leave the network → no hosted services;
- no platform team → no cluster of your own.

**A recovery test before production:** `SIGKILL` in the middle of a run and counting what ran again.

Sources: P. Perrone, "Inngest vs Temporal vs DBOS vs LangGraph" (2026-09-22, an article sponsored by Inngest);
the Inngest documentation (the `inngest/website` repository, how-functions-are-executed) and DBOS (`dbos-inc/dbos-docs`,
architecture), read 2026-10-29. Temporal details and the LangGraph default mode [unverified].
