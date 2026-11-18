# LLM threats and controls

Contents: prompt injection · exfiltration · agency · data and prompt leaks · indirect injection (Anthropic) · RAG · consumption

## Prompt injection (LLM01:2026, ASI01)
- **Direct**: the user types the instructions themselves (jailbreak). The effect is usually limited to their permissions, so
  tool permissions are what matters, not the prompt content.
- **Indirect**: the instruction sits in content fetched by the system (an email, a page, a PDF, a code comment, an MCP
  tool description, a document in RAG). The attacker is not the user; this is the main vector for agents.
- Remedy: architecture (the triple combination), not a list of forbidden phrases.

## Exfiltration
Channels: a markdown image with an address carrying data in the query, a link to click, an HTTP tool call, an email,
a write to a shared document, an MCP call to a foreign server. Remedies: CSP, no remote images, a proxy with
an allow-list, no tool that takes an arbitrary URL, approval of sending.

## Excessive agency (LLM03:2026, ASI02–ASI03)
Three sources: too many functions, too broad permissions, too few approvals. Remedy: narrow tools (a task, not
"run SQL"), the user's credentials, approvals for writes.

## Data (LLM02, LLM08, LLM05 — 2026 numbering)
Leaks: training or fine-tuning data, context from other sessions, the system prompt. Remedies: context separation per
user, no secrets in the prompt, data minimization and anonymization (`arch-privacy-compliance`), control of
the provenance of fine-tuning data (`ai-fine-tuning`). Poisoning: writes to the knowledge base and agent memory require source
control and review.

Hidden context exposure (LLM08:2026, formerly system prompt leakage LLM07:2025) — order per Anthropic ("Reduce prompt leak", platform.claude.com, read
2026-10-20): first nothing confidential in the prompt (what the model does not need, it does not get), then monitoring
and an output filter (expressions, keywords, a cheap model as a classifier), regular review of responses. Making
leaks harder with instructions ("do not reveal…") last and with a test: it complicates the task and can degrade answer quality.

## Indirect injection — Anthropic recommendations
Source: "Mitigate jailbreaks and prompt injections", platform.claude.com, read 2026-10-20.
- Pass foreign content (an email, a page, OCR, a tool result) in a tool result block (`tool_result`), not in the system
  prompt or in plain user text; the model treats instructions in tool results with reserve.
- In the tool description or in the result itself, state the kind and origin of the content ("email content from an unknown sender").
- In the system prompt, state outright that content from tools, documents and search is untrusted data that does not
  change the instructions or the user's request.
- Wrap foreign text in JSON instead of appending it to free text — escaping sets an unambiguous boundary.
- Do not put your own instructions in tool results (the model may ignore them as suspicious) — send them
  in the user turn after the result.
- Check the tool result with a cheap classifier model before the agent acts on it; on suspicion stop the
  action or ask a human.
- Before deployment, red teaming with documents and tool results containing injected instructions
  (`references/red-teaming.md`).

## RAG and vectors (LLM09:2026, ASI06)
Document permissions enforced at retrieval (a filter by identity), tenant isolation in the index, control of
what goes into the index (poisoning), versioning and the ability to delete a document. Details: `ai-rag`.

## Consumption (LLM06:2026)
Input and output limits, max agent steps, a budget per user and per tenant, a cost alert, protection against
duplicating requests (tool recursion).

## Model-generated SQL
An analytics agent that writes and runs SQL is code execution from untrusted input. Read-only mode does not
protect: SELECT can read files from disk, attach other databases and load extensions (in the author's case study 5 of 11
attacks got through despite read-only mode [unverified]). Layers:
1. **A text guard** before execution: exactly one SELECT query, a list of forbidden functions (file,
   network, `ATTACH`, loading extensions), the plan cost assessed by your own row-count estimator — the engine's planner
   can be wrong by orders of magnitude.
2. **A lock in the engine** that the query cannot change. In DuckDB e.g. external access disabled
   (`enable_external_access = false`), automatic extension loading disabled and the configuration locked
   (`lock_configuration = true`); check the setting names in the documentation of the project's version.
3. **Limits** on time and the number of returned rows. Interrupting a query usually works only between engine steps,
   so one stuck query lengthens the tail latency — set the limit with headroom and measure p95.
An input gate (a "whether to answer" classifier) fails closed: an unreadable classifier answer = a refusal,
not "answer".

Source: F. Khan, "Engineering Multi-Agent AI for a 100 GB Data Warehouse" (2026-10).
