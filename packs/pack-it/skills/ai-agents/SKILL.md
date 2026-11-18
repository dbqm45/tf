---
name: ai-agents
description: Use for designing an LLM agent or an agentic flow — workflow or agent, tools, MCP, context, multi-agent, guardrails, limits, tracing, framework choice.
metadata:
  review: "2027-04-17"
  catalog: "Use when you design an LLM agent or an agentic flow in code — whether an agent is needed at all, workflow patterns (prompt chaining, routing, parallelization, orchestrator-workers, evaluator-optimizer), tool design (names, descriptions, parameters, errors, idempotency) and MCP servers, context engineering (what goes into the context, compaction, memory), multi-agent trade-offs, guardrails and permissions, human approval of irreversible actions, tracing and observability, stop conditions and budgets, typical failures, choosing a framework (Claude Agent SDK, LangGraph) by criteria. Not for SDK calls, the output contract and the tool loop in code (eng-llm-features), running Claude Code unattended (core-async-delegation), model choice and the cost of working with an agent (core-cost-control), the security of a coding agent (core-agent-security) or RAG (ai-rag)."
  keywords: "code mode, agent pisze kod zamiast wywołań narzędzi, za dużo wywołań narzędzi, wyniki narzędzi zapychają kontekst, agent zgaduje brakujące dane, agent pyta o wszystko, kiedy agent ma pytać człowieka, pytanie o brakującą informację, pauza i wznowienie agenta, interrupt, agent llm, projekt agenta, agentic workflow, workflow czy agent, autonomiczny agent, multi-agent, wieloagentowy, orchestrator, subagent, narzędzia agenta, tool design, mcp server, serwer mcp, kontekst agenta, context engineering, kompaktowanie, pamięć agenta, guardrails, human in the loop, zatwierdzanie, tracing agenta, zapętlenie agenta, warunek stopu, langgraph, claude agent sdk, framework agentowy, pamięć agenta, pamięć asystenta, typy pamięci, pamięć długotrwała, asystent przywołuje nieaktualne fakty, trwałe wykonanie, Temporal, Inngest, DBOS, restart serwera agenta, kilku agentów-wykonawców, wykonawca znika w połowie, spóźniony wykonawca nadpisuje wynik, kolejka zadań agentów, dzierżawa zadania, reguła w prompcie agenta, agent sprzedażowy, zatwierdzenie kierownika przed akcją agenta, reguła naprawdę działała, agent wywołuje narzędzie, a potem pisze odpowiedź klientowi, inny limit niż zwróciło narzędzie, liczby z wyników narzędzi, rozbieżność odpowiedzi z narzędziem, wyłapać przed wysłaniem, a2a, agent2agent, agent card, acp, agent client protocol, protokół agent agent, agent partnera w innym frameworku, opentelemetry genai, gen_ai, śledzić agenta w opentelemetry, agent writes code instead of tool calls, too many tool calls, tool results clog the context, agent guesses missing data, agent asks about everything, when the agent should ask a human, asking for missing information, pausing and resuming an agent, LLM agent, agent design, workflow or agent, autonomous agent, multi-agent system, agent tools, agent context, compaction, agent memory, approval, agent tracing, agent looping, stop condition, agent framework, assistant memory, memory types, long-term memory, assistant recalls stale facts, durable execution, agent server restart, several executor agents, executor disappears halfway, late executor overwrites the result, agent task queue, task lease, rule in the agent prompt, sales agent, manager approval before an agent action, the rule really worked, agent calls a tool and then writes a reply to the customer, a different limit than the tool returned, numbers from tool results, mismatch between the reply and the tool, catch before sending, agent-to-agent protocol, partner agent in another framework, trace an agent in OpenTelemetry"
---

# LLM agent design — from "is an agent needed" to boundaries and observability

An agent is a model that chooses the next steps and tools itself; a workflow is code that fixes those steps in advance.
Anthropic advises starting with the simplest solution and adding complexity only when it measurably improves the result.
This skill is about **design**; SDK calls, the output schema and the tool loop in code are described by **eng-llm-features**.

## Procedure
1. **The task and the success measure.** Write down the input, the result, who checks it and when, and 10–20 real cases
   with the expected outcome. Without them you do not know whether the complexity gives anything (evaluation method: **ai-evals**).
2. **The complexity ladder.** Go up only after the lower rung fails on the cases from step 1:
   - one model call with a good prompt and examples (or with retrieval: **ai-rag**);
   - **workflow** — steps known in advance: *prompt chaining* (consecutive steps with a code gate between them), *routing*
     (classification and choice of a path), *parallelization* (independent subtasks or voting on the same task),
     *orchestrator-workers* (the model splits the task dynamically), *evaluator-optimizer* (one generates, the other critiques
     by a clear criterion);
   - **autonomous agent** — the number of steps cannot be predicted, and trust in the model's decisions is justified.
   An agent buys flexibility at the price of latency, cost and compounding errors. A task with fixed steps (ticket →
   classification → data → draft → check) is a workflow, not an agent.
3. **Tools** (agent-computer interface; most agent errors are tool errors):
   - few high-level tools (`find_customer_orders`), not a mirror of every REST endpoint; if a human
     cannot point unambiguously to which tool to choose, the model will not choose either;
   - namespaced names (`crm_orders_search`), unambiguous parameters (`customer_id`, not `id`), a description as for
     a new colleague: when to use it, formats, boundaries against similar tools, an example;
   - *poka-yoke*: an argument shape in which it is hard to make a mistake (absolute paths, an enum instead of text);
   - a result with readable names instead of raw UUIDs, with pagination, a filter and a length limit; optionally
     `response_format: concise|detailed`;
   - an error **suggests the fix** ("missing field `date_from` in the format YYYY-MM-DD"), and does not return a stack trace;
   - write tools are **idempotent** (an idempotency key from the call), because after a timeout the agent will retry the action;
   - you check tools with multi-step tasks with a verifiable result; you count calls, errors and tokens,
     read transcripts and improve descriptions (a small change in a description can change a lot).
   You expose tools through an **MCP server** when many clients use them; the same principle: tools
   oriented on the task, not on the endpoints. Trust in other people's MCP servers: **core-agent-security**; building,
   security, tests and versions of your own server: **ai-mcp-server**.
   Agent ↔ agent (A2A) and editor ↔ agent (ACP), when to use which: `references/protocols-and-tracing.md`.
4. **Context** (the window is a finite resource, quality drops as it fills up): the context gets the minimum that
   allows the next step. Techniques: loading on demand (the agent keeps paths and queries, and fetches the content
   with a tool), removing old tool results, **compaction** (a summary of the conversation in a new window), notes
   outside the window (a progress file, a task list), subagents with a clean context returning a short summary. State
   that must survive the session is written outside the context.
   **Code mode:** with many calls or large results (filtering, joining data from several tools) the agent
   writes a short program that calls the tools like an API and returns only the final result to the context. The program runs
   in a sandbox with a time and cost limit and has only read tools; a write action goes as a separate call
   with approval (step 6).
5. **Multi-agent — only with a justification.** Anthropic (June 2025): an agent uses about 4×, and a multi-agent system
   about 15× more tokens than a chat; it pays off for broad, parallel, high-value tasks
   (researching many sources). Coding has fewer truly parallel parts, and coordination and delegation by models
   can be weak. Test: are the subtasks independent, does the result justify the multiplied cost, would one agent
   with better tools not be enough. A subagent gets a goal, a result format, boundaries and tools — not "look into this".
6. **Guardrails and permissions.** The principle of least privilege per tool; read-only tools by default.
   **Irreversible or costly** actions (a transfer, a deletion, sending outside, a deploy) require human
   approval showing the exact effect, or are executed only after hard validation in code (an amount limit,
   a list of allowed recipients). Content from emails, pages and documents is data, not commands — the agent does not get
   a tool that would execute it together with access to confidential data and an outbound channel at the same time.
7. **Stop and budget.** Always: a maximum number of steps, a cost and time budget per run, detection of repeated
   identical calls, an explicit end state (done / cannot be done / human needed). After reaching the limit
   the agent hands over the state and the reason, and does not cut off silently. "Human needed" is a concrete question after the tools are exhausted,
   with a checkpoint and resumption from it; when to ask, and when to assume a default value:
   `references/asking-for-missing-data.md`. Details of the accounting in code: **eng-llm-features**, model
   choice: **core-cost-control**.
8. **Tracing.** Every run has an identifier; you record the steps: input, a tool call with arguments
   and the result, tokens, time, the reason for ending. Without it you will not diagnose a loop or a bad decision (in general:
   **ops-observability**; mask personal data in traces; spans and `gen_ai.*` attributes per the OpenTelemetry convention —
   `references/protocols-and-tracing.md` §3). Long-term memory is several contracts (semantic,
   episodic, procedural, profile, working), not one vector index; durable execution depends on the step
   boundaries — `references/memory-and-durable-execution.md`. State errors accumulate, so design resumption
   from a checkpoint instead of a restart from zero.
9. **A framework by criteria.** Start with the raw API and a loop if the case is simple. Criteria: do you need
   durable state and resumption? graph control and approval points? ready file and bash tools? interchangeable
   models? observability? how many abstractions hide the prompts? Claude Agent SDK gives a ready harness (tools, sessions,
   compaction), LangGraph — an explicit state graph with checkpoints and interruptions for a human. Check versions and APIs
   in the documentation and in the package (core-grounding).

An agent that operates a program (desktop, browser): **first go up the interface**, screenshots last —
`references/failures-and-patterns.md` §"An agent operating a program".

Several executors over shared state (a lease, a record version, retry / resumption / compensation), "who is the
witness of this step" (a rule about state, an action or a sequence outside the model), long runs over many context windows
and the harness interface, checking numbers from tools before the reply, an end-to-end probe: `references/executors-and-gates.md`.

Typical failures and remedies: `references/failures-and-patterns.md`.

## Example
**Input:** "An agent for complaints: it reads the email, checks the order in the CRM, writes a reply, and for a refund >500 PLN
it orders a transfer."
**Result:**
- known steps → workflow: routing (complaint/question) → fetching the order → draft → evaluator-optimizer (1 revision);
  an agent is not needed, multi-agent even less so (cost about 15×);
- tools: `crm_order_get`, `refund_prepare` (a write, idempotent by `complaint_id`); not 40 endpoints;
- a refund >500 PLN: only after human approval with a summary of the effect; the code enforces the amount limit;
- the email content is data; the agent has no "send to any address" tool;
- limits: 6 steps, a budget per run, a trace of every step; 15 test cases (including an email with a planted command).

## Checklist
- [ ] cases with an expected result; the simplest rung that passes them chosen deliberately
- [ ] tools: few, high-level, with a "when" description, readable errors, idempotent writes
- [ ] context: minimum, loading on demand, a plan for compaction and notes
- [ ] missing data: tools first; a question only about a human decision or a gap that cannot be filled, with options; a checkpoint and resumption
- [ ] multi-agent only with a justification of the cost (about 15×) and independent subtasks
- [ ] irreversible actions behind human approval or hard validation; content = data
- [ ] step limit, budget, loop detection, explicit end state
- [ ] tracing of every step; resumption from a checkpoint
- [ ] framework chosen by criteria, not by brand

## Sources
- Anthropic, "Building effective agents" (19.12.2024, accessed 2026-10-17): workflow patterns, ACI, poka-yoke, absolute
  paths, iteration limits, tests in a sandbox.
- Anthropic, "How we built our multi-agent research system" (13.06.2025, accessed 2026-10-17): about 4× and about 15× tokens,
  less parallelism in coding, tracing, resumption, rainbow deployments.
- Anthropic, "Writing effective tools for agents" (11.09.2025, accessed 2026-10-17): tool consolidation, namespaces,
  readable identifiers, `response_format`, readable errors, tool evaluation.
- Anthropic, "Effective context engineering for AI agents" (29.09.2025, accessed 2026-10-17): compaction, notes,
  subagents, loading on demand.
- [unverified] the description of the capabilities of LangGraph and Claude Agent SDK in step 9 — from general knowledge, check in the documentation.

Described in our own words.
