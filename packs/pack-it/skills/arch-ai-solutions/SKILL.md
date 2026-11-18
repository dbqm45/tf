---
name: arch-ai-solutions
description: Use for the architecture of a system with AI — the pattern (LLM, RAG, agent), provider lock-in, cost, latency, trust boundaries.
metadata:
  review: "2027-10-17"
  catalog: "Use when you design the architecture of a system with an AI component at the decision level — choosing the pattern (a plain model call, RAG, a workflow with tools, an agent, fine-tuning, classic ML) by a requirements table, the model source (an API, open-weights on your own infrastructure, a managed cloud service), data residency and lock-in, the components of the reference architecture (gateway, prompt service, retrieval and tool layer, evaluations, guardrails, review queue), the latency budget, cache, fallback and model routing, security boundaries, a cost and capacity template, tenant isolation, ADRs for AI decisions. Not for the general system design (arch-system-design), the stack selection method (arch-tech-selection), quality attributes (arch-quality-attributes), the threat model (arch-threat-modeling), RAG details (ai-rag), agent design (ai-agents), code with an SDK (eng-llm-features) or hosting models (ops-ai-inference)."
  keywords: "wymiana modelu na tańszy, zostawić harness, uzależnienie od dostawcy, wymiana harnessu, architektura ai, architekt rozwiązań ai, rag czy agent, jaki wzorzec ai, wybór modelu, api czy własny model, open-weights, rezydencja danych, lock-in dostawcy, brama llm, llm gateway, routing modeli, fallback modelu, budżet opóźnienia, koszt na żądanie, szacunek kosztu llm, prompt caching w architekturze, izolacja klientów, multi-tenant ai, human review queue, adr dla ai, referencyjna architektura ai, system AI odpowiada liczbami, pewnie złe liczby, kiedy odpowiedzi można ufać, model pisze SQL, text-to-SQL architektura, wycofanie zmiany AI, wróciliśmy do starego promptu, jakość spadła po wdrożeniu promptu, rollback promptu i indeksu, bramka LLM, gateway LLM, przełączanie dostawców LLM, swap the model for a cheaper one, keep the harness, provider dependency, harness swap, ai architecture, ai solutions architect, rag or agent, which ai pattern, model choice, api or own model, data residency, provider lock-in, model routing, model fallback, latency budget, cost per request, llm cost estimate, tenant isolation, adr for ai, reference ai architecture, ai answers with numbers, confidently wrong numbers, when answers can be trusted, model writes SQL, text-to-SQL architecture, rolling back an ai change, quality dropped after a prompt rollout, prompt and index rollback, switching llm providers"
---

# Architecture of solutions with AI — decisions before code

The skill leads from requirements to documented decisions: which pattern, which model, which components, which boundaries
and what it costs. The general system design (estimates, API, data, availability) comes from **arch-system-design**; choosing
technology by candidates and a matrix — **arch-tech-selection**. Here you add what is specific to AI.
Result: `docs/project/04-architecture/ai-architecture.md` and ADRs (template: `references/templates.md`).

## Procedure
1. **The requirements that decide.** Record six axes: knowledge freshness, required accuracy (the cost of an error), latency,
   cost per request, data sensitivity, explainability. Without numbers (e.g. p95 ≤ 2 s, ≤ 0.02 USD per request [example])
   you will not choose a pattern. A missing axis → a question to the human, not an assumption.
2. **Pattern: the simplest one that meets the axes.** You start from the top of the table and go lower only with evidence
   (an evaluation, **ai-evals**) that the higher one is not enough. Anthropic advises the same: the simplest solution, complexity
   only when it measurably helps.

   | Pattern | Choose when | Price (latency, cost, risk) |
   |---|---|---|
   | classic ML or rules | a narrow task, labelled data, explainability and low cost needed | the cheapest; needs data and MLOps (**ai-mlops**) |
   | a single LLM call | general knowledge or knowledge given in the prompt, a single-step task | 1 call; no current facts |
   | RAG | private, changing knowledge, with permissions or citations | + retrieval; details **ai-rag** |
   | a workflow with tools | steps known up front, live data, actions in systems | predictable; cost and time grow linearly with the steps |
   | an agent | the number of steps unknown up front, flexibility needed | the most expensive, the slowest, errors compound; **ai-agents** |
   | fine-tuning | a stable style, format or behaviour, a large volume, a cheaper small model | does not deliver current facts [assumption]; **ai-fine-tuning** |

   Patterns combine (RAG in a workflow step). Justify an "agent" decision by what a workflow cannot do.
3. **Model source.** Three options, criteria as in arch-tech-selection (filters, then a matrix):
   - **a model provider's API** — the fastest start and the best models; risk: data residency, version changes and retirements;
   - **a managed cloud service** (models through the cloud account) — shared IAM, a private network, region choice;
     risk: lock-in in the tooling around the model, a delay in rolling out new models [unverified];
   - **open-weights on your own infrastructure** — full control of data and a fixed cost; risk: running GPUs
     and a weaker model (**ops-ai-inference**, **ai-model-optimization**); check the weights' licence.
   Mandatory filters: the processing region (also of logs and the cache at the provider), a data processing agreement and zero-retention,
   the model's availability in the region. You limit lock-in with a thin layer of your own interface (the gateway) and a set of
   evaluations that lets you change the model in days, not months.
   The second floor of lock-in is weights used to the harness's tool format — it shows in the results, not in the configuration;
   before swapping just the model or just the harness, do a **swap test in both directions** on your own evaluations
   (the old model in the new harness and the new model in the old one); swapping just the model does not remove lock-in
   (a hypothesis from one preprint, source below).
4. **Components (reference architecture).** Pick from the list only what the requirements justify:
   - a **gateway** in front of the model: authentication, limits (requests and tokens per client), cost accounting per tenant,
     routing and fallback, logging with PII masking;
   - a **prompt service**: versioned templates, deployed like code, with an evaluation in CI (**ai-prompt-engineering**);
   - a **retrieval layer** (**ai-rag**) and a **tool layer** (contracts, permissions, idempotency);
   - **evaluations and observability**: a golden set, online evaluations, step tracing, cost and tokens per request
     (**ai-evals**, **ops-observability**);
   - **guardrails**: input and output validation, content filters, a result schema;
   - a **human review queue** for irreversible or low-confidence actions; the human sees the proposal
     and the evidence, not just "approve".
5. **Latency budget.** Break the p95 target down into steps: gateway, retrieval, model (time to first token and generation),
   tools, validation. Levers: streaming (the user sees the beginning, so the time to first token counts),
   independent steps in parallel, a smaller model in simple steps, shorter output, cache. For every step: a **timeout**
   and the behaviour after it is exceeded.
6. **Cache, fallback, routing.**
   - **Prompt caching** (at the provider): a stable prefix at the start (tools, instructions, documents), variables at the end;
     changing the tool definitions or the prefix invalidates the cache, so version the templates consciously. Prices and TTL: the table
     in **core-cost-control**; check the values in the provider's price list on the day of the decision.
   - **Result cache** (exact or semantic) only for answers independent of the user and permissions;
     the key includes the prompt and model version and the tenant.
   - **Fallback**: a second model or provider with the same output contract, degradation (an answer from the cache, a mode
     without AI, a queue to a human). The switch must pass the evaluation, not just return HTTP 200.
   - **Model routing**: a simple classifier or rule sends easy requests to a cheap model, hard ones to a strong one;
     you set the threshold on the golden set.
   - **Action idempotency**: a tool that changes state accepts an idempotency key, because a retry after a timeout
     must not issue two refunds (**be-api-design**, **be-messaging-outbox**).
7. **Security boundaries** (the full threat model: **arch-threat-modeling**). You draw them on the diagram:
   - content from documents, emails and pages is **data, not commands** (prompt injection); the model does not get write
     or send tools driven by such content without approval;
   - tools work with the **permissions of the calling user**, not a service account with full access;
     authorization on the tool's side, not in the prompt;
   - **data egress**: an allowlist of outgoing addresses, no rendering of images and links with addresses
     from the model without control, PII masking before sending to the provider (**arch-privacy-compliance**).
8. **Cost and capacity** (formula: `references/templates.md`). Request cost = Σ over calls (input tokens ×
   input price + output tokens × output price), separately **without cache** and **with cache** (a cache read costs a fraction
   of the input price, a write more). Multiply by the volume, add retrieval, tools and evaluations. Capacity: concurrent requests
   at peak × duration, the provider's token limits; your own model — **ops-ai-inference**.
   You plug in prices from a price list with a date, not from memory.
9. **Tenant isolation.** By default shared infrastructure and **logical isolation**: the tenant ID in every
   query to the index, tool and cache (a filter in the database, not in the prompt), separate encryption keys and cost
   limits per tenant. A separate index, instance or model only where a contract or the risk requires it
   (e.g. regulated data). Test: tenant A's query for B's data returns "none".
   **A numeric result from a model (e.g. text-to-SQL):** two independent paths — the model writes SQL, and a second model fills in
   a structure from the metrics catalogue that code compiles to SQL by rules. Matching results = high confidence, a discrepancy →
   a critic or a refusal, one path → lower confidence. The model writes the query, the database computes (the model's arithmetic fails).
   Before adding a component (value lookup, table selection) measure whether it helps — when the whole schema fits
   in the prompt, an extra stage can make the result worse (F. Khan, 2026-10 [unverified]).
   **A gateway in front of the models, retries and the stream, rollback with the index version, a managed agent runtime:**
   `references/gate-and-reliability.md`.
   **Handling a large volume of cases** (refunds, complaints, data changes): autonomy thresholds per intent, a confusion
   matrix with costs and "the model proposes, the orchestrator executes" — `references/case-handling.md`.
10. **Record.** `ai-architecture.md` (TL;DR, axes, pattern, components, budgets, boundaries, cost, risks) and an **ADR** for
    every key decision: pattern, model source, residency, fallback (**arch-architect-practice**,
    **docs-tech-writing**). Write the decision's revision criterion (e.g. quality on the golden set below a threshold) into the ADR.

## Example
**Input:** "A support assistant: the terms change every week, refunds in the payment system, data only in the EU, 200k
requests a day [example]."
**Result:**
- axes: high freshness, a high cost of error (money), p95 ≤ 3 s, personal data in the EU;
- pattern: a **workflow** (RAG over the terms, a `refund` tool with an idempotency key, a human's approval above
  an amount threshold); agent rejected — the steps are known, ADR-002;
- model: a managed service in an EU region or an API with a data processing agreement; a gateway with its own interface, fallback to a second model;
- p95 budget: gateway 0.1 s + retrieval 0.4 s + model to first token 1.2 s (streaming) + tools 0.8 s [example];
- cost: the formula from `references/templates.md` with and without cache; a stable prefix (instructions, tools) at the start of the prompt;
- boundaries: the terms are data; `refund` with the support agent's permissions, not a service account's.

## Checklist
- [ ] six requirement axes with numbers; the simplest pattern with evidence that a lower one is not enough
- [ ] model source: filters (region, retention, licence), a lock-in assessment, an ADR
- [ ] components matched to the requirements; a gateway with cost per tenant
- [ ] a latency budget per step, timeouts, streaming, fallback after evaluation
- [ ] state-changing actions idempotent; a human approves the irreversible ones
- [ ] trust boundaries on the diagram: data is not commands, the caller's permissions, egress
- [ ] cost with and without cache, prices with a date; capacity at peak
- [ ] tenant isolation tested; ADRs with a revision criterion

## Sources
- Anthropic, "Building effective agents" (anthropic.com/engineering, accessed 2026-10-17): the simplest solution
  first, a workflow for predictable tasks, an agent when flexibility is needed, human checkpoints and iteration limits.
- Anthropic, "Prompt caching" (platform.claude.com/docs, accessed 2026-10-17): write 1.25× (5 min) or 2× (1 h),
  read usually 0.1× the input price (the multiplier depends on the model), TTL 5 min by default, the minimum length depends on the model,
  a change of the tool definitions or the prefix invalidates the cache.
- Microsoft, "AI gateway in Azure API Management" (accessed 2026-10-17, through search results): token limits
  per consumer, a semantic cache, backend balancing — confirmed only indirectly [unverified in the full text].
- AWS, "Well-Architected Framework — Generative AI Lens" (docs.aws.amazon.com, accessed 2026-10-17): six pillars
  in lifecycle phases, controlled autonomy, responsible AI; the content of the detailed principles [unverified].
- [unverified] the delay in rolling out new models in managed services and the availability of regions — check
  with the chosen provider on the day of the decision.
- Yu et al. (Salesforce AI), arXiv:2609.09134, preprint v1 of 8.09.2026, discussed by J. Wasowski ("Model–Harness
  Fit: Why A Better Teacher Makes A Worse Agent", Medium, about 12.10.2026); the preprint was not opened, the numbers are from the article
  [unverified] — lock-in in the weights, the swap test in both directions.

Described in our own words.
