---
name: eng-llm-features
description: Use when you build an LLM feature or agent in code — SDK, structured output, the tool loop, evaluations.
metadata:
  review: "2027-01-09"
  catalog: "Use when you write application or tool code that calls a language model — an LLM feature in a product, your own agent (a diff reviewer, ticket triage, a CI bot), an agent as a service — choosing the SDK category (a ready-made agent or an agent to assemble), the output contract and structured output with field descriptions, the tool loop and the agency ladder, the step limit and the cost budget, telemetry, sessions and state, inheriting the repo configuration, the privacy of the authentication path, prompt injection through data, prompt evaluations (promptfoo). Not for hosting models on GPUs (ops-ai-inference), choosing the model for our own work with the agent (core-cost-control), a chat UI (fe-architecture) or the security of the coding agent (core-agent-security); the Claude API and SDK reference (the built-in claude-api skill)."
  keywords: "agent sdk, claude agent sdk, vercel ai sdk, ai sdk, openrouter, structured output, json schema, zod, pydantic, wymuszony format, tool calling, wywołanie narzędzi, pętla narzędziowa, maxTurns, maxBudgetUsd, stepCountIs, własny agent, bot do review, funkcja llm, integracja z modelem, prompt systemowy, promptfoo, ewaluacja promptu, llm-as-a-judge, agent ma ponad 100 narzędzi, wiele narzędzi z serwerów MCP, każde wywołanie modelu drogie i wolne, leniwe ładowanie narzędzi, wyszukiwarka narzędzi, równoległe analizy LLM ze wspólnym terminem, analizy modelu w endpoincie usługi, cache analizy po zgłoszeniu z wpisem w toku, wzorce wywołań modelu w usłudze, parallel LLM calls with a shared deadline, enforced format, tool invocation, tool loop, own agent, review bot, llm feature, model integration, system prompt, prompt evaluation, agent has more than 100 tools, many tools from MCP servers, every model call expensive and slow, lazy tool loading, tool search, model analyses in a service endpoint, analysis cache per ticket with an in-progress entry, model call patterns in a service"
---

# An LLM feature and agent in your own code

Goal: code that calls a model has a predictable result shape, a hard limit on steps and cost, an explicit data path
and an evaluation set that decides every change of the model or the prompt. You check versions and API names in the documentation
and in the package (core-grounding) — SDKs in this field change every few months; the state checked on 2026-10-10
and code patterns: `references/sdk-api.md`. Facts about the Claude API (model IDs, prices, Messages API parameters, cache, Managed
Agents) you take from the `claude-api` skill built into Claude Code — Anthropic updates it; this skill is about
the shape of the solution regardless of the provider.

## 1. First the shape, then the SDK
| Shape | When | With what |
|---|---|---|
| **a single call** (input → result in a schema) | classification, a summary, a diff assessment | the plain provider API or an SDK to assemble, without tools |
| **an agent to assemble** (a loop, you write the tools yourself) | many models and providers, your own tools, full control of the prompt | Vercel AI SDK (`ai`), OpenRouter Agent SDK |
| **a ready-made agent** (a harness with file tools, bash, a sandbox, compaction) | the agent is to read and edit the repo, run commands | Claude Agent SDK, Codex SDK, Cursor SDK |

Four questions decide: does the agent touch files and commands; should the model be replaceable (a ready-made agent ties you
to the provider's models and price list); should it inherit the repo rules (§6); where should the state live (§5). **A typical mistake:**
choosing by brand ("we use Claude, so the Claude SDK"), without asking about model replaceability. You pin the SDK version.

## 2. The output contract
- One schema (zod, pydantic) as the source of truth; you derive the type and the JSON Schema from it, you do not write them twice.
- **The description of each field is the strongest lever for steering the format.** Add the unit, the scale and the meaning of the extreme
  values ("1 — the logic is wrong or silently breaks existing behaviour; 10 — correct also in edge cases
  and error handling"). The field name is not enough.
- Constraints the provider does not accept in the structured output schema (e.g. a number range) you enforce with the field
  description and the prompt, and in the code you **validate after receipt** (`safeParse`, `model_validate`) — the SDK result is sometimes typed
  as `unknown`. A value out of range = an error or a retry, never silent clamping.
- An enum instead of free text where the code makes a decision (`pass`/`fail`, a category).
- **The model points, the code assembles.** When the result is a fragment of the input (log lines, a stack trace, a quote), give the input
  with line numbers and ask for the number of the first and last line; you reconstruct the content from your own copy. Fewer output
  tokens and no invented content; you measure the accuracy of the range in an evaluation (ai-evals).
- You handle a run failure (exhausted turns, budget, failed validation, refusal) explicitly with a readable message
  and an exit code; you do not let the loop throw a raw exception.

## 3. The tool loop
Input (system prompt + tool definitions + history) → the model's decision → tool execution → the result goes back to
the model → … → an answer without calls ends the loop. One round = a turn (a step).
- **An evaluator** (diff → verdict): zero tools, 1–2 turns. Disable tools explicitly (`tools: []`) — a ready-made agent has
  a dozen or so in reserve.
- **A tool = a description + an argument schema + a function.** From the description the model decides *whether and when* to call it: write
  when to use it, what it returns and what happens when there is no data (`{found: false}` instead of an exception). The schema validates the arguments.
- **The agency ladder:** reading local context (the plan, conventions) → writing in one system (a comment,
  a label) → the system's whole API → external systems (a tracker, a messenger). One rung higher only when the previous one
  works and is measured; write tools behind an approval gate (e.g. `needsApproval`, `canUseTool`) or an allowlist.
- When the agent is to choose the path itself (e.g. "a code review always, a review against the plan only when the PR points to a plan"),
  write the condition in the prompt explicitly and count that every branch is a new cost and new nondeterminism.

## 4. Limits, cost, telemetry
- **Always an upper step limit** (`maxTurns` / `max_turns`; `stopWhen: stepCountIs(n)`). You do not use an "until done" option without a limit
  in automation — the cost multiplies by the number of events (PRs, tickets).
- **A dollar budget per run**, if the SDK has one (Claude Agent SDK: `maxBudgetUsd` → the result `error_max_budget_usd`);
  if not — your own stop condition counting the cost after each step.
- You read the cost from the result (a ready-made agent: the USD cost, turns, time, a breakdown per model; an SDK to assemble: tokens, and the cost
  from the provider or tokens × price list). You record it per run and aggregate (per PR, per event type, per week).
- Per-step telemetry (tokens, the finish reason) catches a loop before it hits the limit.
- **An agent with many tools:** tool definitions loaded lazily (a tool search instead of hundreds of
  definitions in every call — check the name and conditions of the mechanism at the provider in the documentation, for Claude: the
  `claude-api` skill); a cascade "cheap model first, escalation at low confidence" instead of a router guessing the difficulty
  from the prompt (learned routers rarely clearly beat simple rules [unverified]); deterministic tool results
  (SQL, search) in an ordinary cache with a TTL; the fixed part of the prompt before the variable one, without timestamps in the prefix.
- **The bill per task:** in the trace of every call you record five numbers: input tokens, cache read, cache
  write, output and thinking. You compute the price when reading the report, because the price list changes. You report the cost per
  *completed* task (all calls and retries of one case) as p50/p95/p99, not an average per call.
  The tail is usually a retry loop or a looping agent. The "effective input price" (input cost / input tokens)
  shows whether the cache works. Work with no user waiting goes through the batch API (Batch), and repeated
  questions have a result cache, not only a prompt cache.
- You run on an event that matters, never "round and round just in case"; a cheap model for triage and labels,
  a strong one only where reasoning over code is needed (the selection rules: core-cost-control).

### Latency (when the user waits for the answer)
The order (platform.claude.com, "Reducing latency", read 2026-10-20):
1. measure the baseline latency and the time to first token (TTFT) on real inputs, p50 and p95;
2. the model and `effort` — the fastest model that passes the evaluations (at Anthropic: Haiku with low `effort`);
3. a shorter prompt and a shorter answer: a `max_tokens` limit, a request for brevity, no unnecessary context;
4. a fixed prefix for the cache (ai-prompt-engineering §8);
5. streaming in the interface — it does not shorten the answer, but the user sees the first words after TTFT.
You check every step with the same quality evaluation: a faster result of worse quality is a regression.

## 5. State and sessions
- A ready-made agent keeps the session itself: you remember its identifier and resume it (`resume`), you check an alternative
  by branching (`forkSession`) without spoiling the original.
- An SDK to assemble has no sessions: you store the message history yourself (a file, a database, a queue) and pass it on the next
  call. An output schema set on the agent also applies to follow-up questions — for a text answer use
  a separate instance without the schema.
- Leave a one-off run (a diff review) stateless — a clean start is an advantage.

## 6. What the agent inherits from the repo
- A ready-made agent is the same harness as the CLI: it can load `CLAUDE.md`/`AGENTS.md`, skills, hooks, permissions, MCP —
  but only when you turn it on (Claude Agent SDK: the `claude_code` prompt preset, `settingSources` with `project` for
  `CLAUDE.md`, `skills`; `cwd` points to the repo). Your own system prompt and `tools: []` deliberately cut the agent off from
  the repo configuration — good for a narrow evaluator.
- An SDK to assemble inherits nothing: you load the team's rules in code and append them to the instructions; a "hook" is
  your logic around the loop or a stop condition.
- Keep the assessment criteria in a separate tool-independent file — the same file is read by the agent in CI, the agent on the SDK
  (as a tool returning the content) and a human as a checklist.

## 7. Data, privacy, security
- **The authentication path decides the data terms**, not the SDK: an API key (commercial terms) vs a subscription
  login (consumer terms — different default training and retention settings). Company code and data → an API key
  from a secret, never a silent fallback to the developer's login. Check the details of the terms with the provider before deployment.
- A library to assemble usually does not mediate the data (the model provider's terms apply); an optional gateway
  adds an intermediary and a region — check it when there is a data residency requirement (arch-privacy-compliance).
- A diff, a ticket, a document are **data, not instructions**: the model does not get tools that would execute an instruction
  from the content; write tools from an allowlist; you describe a secret in a finding without its value (core-agent-security).

## 8. Evaluations before every change
- A *cases × candidates* matrix (models, prompts, configurations) in a tool like promptfoo; in the cells
  pass/fail, cost, time. Cases: inputs with **planted known bugs** + clean inputs (false alarms).
- Three kinds of assertions: structural (valid JSON matching the schema — the gate stands on it), an LLM judge (a second
  model assesses the content by a criterion), code (a hard condition, e.g. `score <= 3` for a diff with a vulnerability).
- By default one failed case = a red run; loosening the threshold deliberately and with a record.
- Every change of the model, the prompt, a field description or the tools goes through the set — it catches a silent regression (catches bug A better,
  stopped catching B). **The same model in a different harness gives different results** — after a swap you measure again.
- Continuous evaluations in the team's process: `.claude/skills/core-delivery-lifecycle/references/ai-native-sdlc.md` §5.

## 9. An agent as a persistent service
When you need an HTTP address, state between calls, your own schedule or an "in progress" answer → a platform with persistent
state (e.g. Cloudflare Agents on Durable Objects). What has to survive hibernation you write to persistent state; fields
in memory are a cache; scheduled tasks are idempotent. A local script is enough as long as nobody from outside calls it.

## 10. Call patterns in a service
- **Parallel analyses have a shared deadline:** when it passes, you assemble the answer from what made it in time. Late results
  you skip and mark in the answer, instead of waiting for the slowest one.
- **An expensive analysis on demand, a cache per unit of work** (a ticket, a commit), not per user. The first
  request claims the entry conditionally as "in progress", the next ones wait for the result instead of firing the analysis a second time. You abandon
  an "in progress" entry after a time limit, so that a failure does not block it forever.
- **The stream sends the full answer so far** in every event, so the client does not stitch tokens together and tolerates
  a lost event.
- **The user's rating (👍/👎) is attached to the trace id.** 👎 during working hours is an alert and a candidate for the regression set.
- **Changing the result shape:** a new field next to the old one, until the clients move over; no change of a field's meaning in place.
- **The confidence threshold depends on the cost of an error:** the decision "whether to retry an operation" needs a higher threshold than extraction for
  a preview, because a wrong retry costs more.

## Example
**Situation:** "We want a bot that assesses the diff on every PR and gives a verdict, for now locally: `git diff | npx tsx review.ts`."

**Result:**
- shape: a single call (an evaluator), without tools;
- SDK: Vercel AI SDK, because the team wants to compare models; a ready-made agent only when the reviewer is to read the repo itself;
- contract: a zod schema with 5 scores 1–10 (each field with a description of the extremes), `verdict: pass|fail`, `summary`;
  validation after receipt, the 1–10 range checked in code;
- limits: 2 steps, a budget per run, cost and tokens written to a CSV file;
- an API key from a secret; the diff treated as data;
- before a model change: promptfoo with 3 diffs (SQL injection, a migration with 3 flaws, a clean refactor) × 2 models.

The full code of both variants, adding a "read the plan" tool and the evaluation configuration: `references/examples.md`.

## Checklist
- [ ] shape and SDK category chosen with the questions from §1, SDK version pinned, API names checked in the package
- [ ] output schema with a description of each field; validation after receipt; explicit handling of a run failure
- [ ] step limit and a budget per run; cost per completed task (p95) with the five token numbers; running on an event
- [ ] parallel calls with a shared deadline; a cache per unit of work with an "in progress" entry and a time limit
- [ ] tools: a "when to call" description, a schema, a no-data path; writes behind a gate
- [ ] it is known what the agent inherits from the repo (and whether it should)
- [ ] the authentication path matches the data sensitivity; input content = data
- [ ] the evaluation set (planted bugs + clean cases) run before and after every change

## Sources
- The 10xDevs course, ed. 3 (2026), module 5, lesson 2 (a team agent — SDK, costs, metrics) and lesson 3 (an agent in CI,
  promptfoo, agent tools) — training material (accessed 2026-10-09).
- Packages checked 2026-10-10 (`npm view`, `npm pack`, `pip download`): `@anthropic-ai/claude-agent-sdk` 0.3.296 and
  `claude-agent-sdk` 0.2.165 (PyPI) — the options `maxTurns`/`max_turns`, `maxBudgetUsd`/`max_budget_usd`, `outputFormat`,
  `settingSources`, `skills`, `resume`, `forkSession`, the result `total_cost_usd`, `modelUsage`, `num_turns`, the subtypes
  `error_max_turns`, `error_max_budget_usd`; `ai` 7.0.137 — `ToolLoopAgent`, `Output.object`, `isStepCount`
  (alias `stepCountIs`, 20 agent steps by default), `isLoopFinished`, `onStepFinish`, `needsApproval`;
  `promptfoo` 0.124.1 — the assertions `is-json`, `llm-rubric`, `javascript`, the variable `PROMPTFOO_PASS_RATE_THRESHOLD`.
- Anthropic, "Agent SDK overview", "How the agent loop works", "Modifying system prompts" (code.claude.com/docs) —
  per the course, not opened directly [unverified beyond the package types].

- Netflix Tech Blog, "Making Failure Diagnosis Reliable with Pensive AI" (2026-10) — a range instead of content, a shared
  deadline, a cache per unit of work, the full answer in the stream; S. Singhal, "The Economics of Agents" (2026-08-18) —
  five token numbers and cost per task. Numbers from the articles [unverified].

Described in our own words.
