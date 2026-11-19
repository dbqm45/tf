# A gateway in front of the models, a managed runtime and reliability

Contents: 1. Gateway · 2. Retries and the stream · 3. Result cache and rollback · 4. A managed agent runtime

## 1. A gateway in front of the models
- **Explicit routes per feature** (`feature → model, fallback`) with a kill switch, instead of "smart" automatic
  routing whose decisions nobody will predict.
- **Fallback only to models that meet the same constraints.** Data meant for your own model must not
  silently go to an external provider (residency, a contract), and a weaker model is a silent loss of quality. There is also
  a product fallback: "show the data without the AI summary".
- **Limits in tokens, not only in requests:** reserve `max_tokens` up front and return the difference after the response.
- **Budget separately from the limit:** an alert at 80%, at 100% a policy chosen up front by the owner (block /
  cheaper route / allow with an alert).
- Logging of prompt content only after it is enabled for a route, with retention. The "fallback rate" measure is an early
  warning of an outage or degradation.

## 2. Retries and the stream
- **Retries in one layer,** with a shared time and attempt budget for the whole request. When every layer (client,
  gateway, orchestrator, SDK) retries separately, one request multiplies the provider calls and deepens the outage.
- **Stream:** after the client disconnects or cancels you stop the generation at the provider, because tokens still
  cost; settle after the end of the stream. A stream interrupted by a provider error ends with an explicit error event
  and is marked as partial — without silently stitching two answers together.
- A comment "checking the ticket" is not a result; you show the result after the service's response.

## 3. Result cache and rollback
- **Invalidating the result cache:** the key or metadata include the version of the source documents. A change or deletion
  of a document invalidates the cached answers built on it, just like the chunks in the index (ai-rag).
- Cache measures: hit rate, saved cost and latency, stale-answer incidents.
- **Rolling back an AI change covers the whole configuration:** the prompt, the model, the tool definitions, the retrieval
  and ranking settings, and the **index version** and the result cache. Without an index snapshot, going back to the previous prompt does not
  restore the previous behaviour (ai-mlops). You set the rollback conditions before the release: errors, the evaluation score,
  cost, wrong tool actions.

## 4. A managed agent runtime
Managed agent environments (e.g. Claude Managed Agents, OpenAI Agents API, Bedrock AgentCore — prices and dates
from the article [unverified]) give the loop "for free", but lock-in goes deeper:
- the tool schema dialect (renaming through the gateway);
- the sandbox format and the control plane: the container image is portable, the environment and session identifiers are not;
- the MCP wiring (authentication, name mapping);
- state and session semantics (expiry after inactivity erases the process memory).
The migration cost is the bill for evaluations: a regression of the tool contract, trajectories, state, policy and environment,
and recomputing quality and cost. For the ADR: you keep the business state in a system you control, and you have your own
evaluation set (a portable definition of success) before you trust the traces of a specific runtime.

Sources: A. Kumar, "Design an LLM Gateway…" (2026-10-22); J. Wąsowski, "Managed Agent Runtime Lock-In" (2026-10-07);
P. Kashyap, "AI System Design…" (2026-10-17); M. Ranjan, "Harness Engineering vs. Loop Engineering…" (2026-10).
