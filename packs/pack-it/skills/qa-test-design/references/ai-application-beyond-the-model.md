# An AI application: failures outside the model

Evals (ai-evals) assess the model's response. A large share of an AI application's failures happen around it: in the UI,
the session, routing, tools, integrations, data and billing. Each class below has a test that can be
automated or walked through manually before release. The classes come from S. Gundeti's review ("9 AI Application
Failures That Aren't Model Problems", 2026-10); the author's examples are generalized — treat them as classes of failure.

| # | Class | Test |
|---|---|---|
| 1 | The UI shows success despite an API error | force 403, 500, a timeout and an expired token; compare the screen with the server's response; the corrective action matches the cause ("sign in again", not "try later") |
| 2 | A long agent task and a dropped connection | disconnect the client midway, let the task finish in the background, come back: the real final state is visible, not an eternal "working…" |
| 3 | Model routing | the first trivial message does not pin the session to the cheap route; a disabled model is no longer served; the fallback follows the policy and is visible to the user |
| 4 | The tool contract | an empty, malformed, duplicated and too large tool result; an interrupted pending call (the agent asks, the user writes a new message); a loop with no progress (raising the recursion limit is a symptom, not a fix); values rewritten by the model (URL, ID, tokens) treated as untrusted |
| 5 | Text-to-SQL | nonexistent columns, identifiers with spaces; three different results told apart for the user: an empty hit, a query error, an undefined metric (a zero that "looks like a fact") |
| 6 | Integrations | personal and company accounts, a revoked token, a list longer than one page, a file link opened from outside the app; it is explicit whose identity the agent acts under |
| 7 | Migrations | tests on accounts with data from before the change, not only on fresh ones |
| 8 | Isolation | the API called directly as a low-privilege user; memory and cache do not cross user and tenant boundaries; revoking a role takes effect immediately |
| 9 | Costs | usage reconciled with the provider's raw per-call records; turns longer than the sync window and sessions across midnight; a price list change does not rewrite history |

You assign priority like for any risk (SKILL.md, "Priority"): impact × probability. Classes 1, 4 and 8 are usually
the highest — a visible false success, uncontrolled tool action, a leak between users.

Related: assessing the response and the agent's trajectory — ai-evals; view states (loading, error, empty, data) —
fe-architecture; permissions per resource — be-auth-security; permissions in the RAG index — ai-rag.
