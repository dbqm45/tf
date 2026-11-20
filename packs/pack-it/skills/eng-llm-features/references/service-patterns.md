# LLM calls inside a service — latency, call patterns, persistent agents, cost accounting

## Contents
1. Latency when a user waits
2. Call patterns in a service
3. Agent as a persistent service
4. Cost accounting per task
5. Agents with many tools

## 1. Latency when a user waits
Work in this order and re-run the quality evaluation after every step (a faster setup that fails cases is not faster):
1. Measure a baseline on real inputs: time to first token (TTFT) and total time, p50 and p95.
2. The fastest model that still passes the evaluation set; lower reasoning effort where the provider offers it.
3. Shorter prompt and answer: cut boilerplate, cap output tokens, ask for the fields you use only.
4. A fixed prompt prefix (instructions, tool definitions, examples) before the variable part, so the provider's prompt
   cache applies (ai-prompt-engineering, cache prefix).
5. Streaming — it improves perceived latency, not total time.

## 2. Call patterns in a service
- **Parallel analyses share one deadline.** Fire the analyses together under one overall deadline (e.g. 20 s for the
  report), assemble the answer from the results that arrived in time and mark the late ones as "not included" —
  one hanging call must not hold the whole response. Cancel the late calls (abort signal) so they stop costing money.
- **Expensive analysis on demand, cached per unit of work.** Key the cache by the thing analysed (incident id, commit
  sha, document hash), not by the user. The first request claims the entry conditionally as "in progress"
  (a conditional insert, `SET NX` with expiry, or a unique row); other requests for the same key wait for that result
  instead of starting their own (single-flight). An "in progress" entry older than the deadline expires, so a crashed
  worker does not block the key forever.
- **Streams carry the whole answer so far** in each event, not only the delta — a client that lost an event still
  shows a correct state.
- **User feedback joins the trace.** A thumbs-up/down is stored with the trace id of the run; a thumbs-down during
  working hours is an alert and a candidate case for the regression set (ai-evals).
- **Changing the result shape:** add the new field beside the old one and remove the old one only after every
  client has migrated.
- **Confidence thresholds follow the cost of an error:** an automated action that is expensive to undo (closing a
  ticket, retrying a payment) needs a higher threshold than a preview the user corrects anyway.

## 3. Agent as a persistent service
Choose a platform with persistent state (for example Cloudflare Agents on Durable Objects) when the agent needs an HTTP
address others call, state between calls, its own schedule, or an "in progress" answer to a second caller.
- Anything that must survive hibernation or a restart goes to the persistent store; in-memory fields are only a cache.
- Scheduled tasks are idempotent: a schedule fired twice does the work once.
- If nobody calls the agent from outside and it runs on a trigger, a local script or a CI job is enough.

## 4. Cost accounting per task
- Log per call: input tokens, cache-read tokens, cache-write tokens, output tokens, reasoning tokens, model, step
  number and task id. Compute the price at report time from a dated price list, so a price change does not
  rewrite history.
- Report **cost per completed task** (a resolved ticket, a merged PR), not per call: p50, p95, p99. The tail is where
  retry loops and looping agents live; the mean hides them.
- Effective input price = input cost / input tokens. If it does not drop after you introduced caching, the prefix
  is not stable (a timestamp, a user name or tool order changing at the top).
- Count failed and abandoned tasks too: their spend is part of the cost of the tasks that completed.
- Non-interactive work goes through the provider's batch API; repeated identical questions through a result cache;
  triggers fire on meaningful events only (not on every push to every branch).

## 5. Agents with many tools
- Do not send 150 tool definitions on every call: load tools lazily — a tool search / deferred loading mechanism
  of the provider (Anthropic: tool search with `defer_loading`; details in `claude-api`) or your own router that
  exposes the 5–10 tools relevant to the current step.
- Cascade: a cheap model first; escalate to a strong model on low confidence, a failed validation or a hard task class.
  Simple escalation rules are a good start; measure before investing in a learned router [unverified that learned
  routers rarely beat simple rules].
- Deterministic tool results (a schema, a config file, a service catalogue) go to an ordinary cache with a TTL.
- Keep the prompt prefix stable: system prompt and tool definitions first, in a fixed order, no timestamps or
  request ids there; the variable part comes last.
- Measure the effect as cost per completed task (section 4), not cost per call.

## Sources
- Anthropic, "Reducing latency" — choose the model, optimise prompt and output length, stream
  (docs.claude.com/en/docs/test-and-evaluate/strengthen-guardrails/reduce-latency, accessed 2026-11-20).
- Netflix Tech Blog, "Making Failure Diagnosis Reliable with Pensive AI" (2026-10) — parallel analyses under a
  shared deadline, per-incident caching, full-state streaming events, feedback attached to traces [numbers unverified].
- S. Singhal, "The Economics of Agents" (2026-08-18) — token categories per call and cost per completed task
  with tail percentiles [numbers unverified].
- Cloudflare Agents documentation (developers.cloudflare.com/agents, accessed 2026-11-20).
