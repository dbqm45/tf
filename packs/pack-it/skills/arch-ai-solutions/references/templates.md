# Templates: ai-architecture.md, cost, ADR

## ai-architecture.md template
```
# AI architecture — <system>
TL;DR: pattern, model source, cost per request, p95, the main risk.
Handoff: open decisions, revision criteria.
1. Requirement axes (freshness, accuracy, latency, cost, data, explainability) — numbers and source
2. Pattern and rejected alternatives (with evidence from evaluation)
3. Model source, region, retention, model change plan
4. Components and a diagram with trust boundaries
5. Latency budget, timeouts, fallback, cache
6. Cost and capacity (table below)
7. Tenant isolation
8. Risks, ADRs
```

## Cost of a request and of a month
The values in brackets are **symbols**; you take the prices from the provider's price list with a date, not from memory.

```
call_cost_without_cache = (T_in × C_in + T_out × C_out)
call_cost_with_cache    = (T_fixed × C_read + T_variable × C_in + T_out × C_out)
                          + write on a miss: T_fixed × C_write
C_read  = m_read × C_in    (the multiplier depends on the model)
C_write = m_write × C_in   (the multiplier depends on the TTL)
request_cost = Σ calls (workflow steps, retries, online evaluation)
             + retrieval + tools
month_cost = request_cost × requests_per_day × days
```
Hits: `h` = the share of calls with a cache read; average cost = h × with_cache + (1 − h) × (without_cache + write).
With traffic sparser than the cache TTL `h` drops, so estimate `h` from the real distribution of gaps between requests.

| Item | Symbol | Value [example] | Source and date |
|---|---|---|---|
| fixed tokens (instructions, tools) | T_fixed | 6,000 | measurement |
| variable input tokens | T_variable | 800 | measurement |
| output tokens | T_out | 400 | measurement |
| input / output price | C_in / C_out | from the price list | provider, date |
| daily volume | | 200,000 | requirements |
| cache hit share | h | 0.8 | measurement after a pilot |

Capacity: concurrent requests at peak ≈ requests/s × average duration (Little's law);
compare with the provider's tokens-per-minute limits. Your own model: **ops-ai-inference**.

## ADR template for an AI decision
```
# ADR-NNN: <decision>
Status: proposed | accepted | superseded
Context: requirement axes, constraints (region, licence, team)
Options: at least 2–3, including the "boring" one; facts with a source and a date
Decision: the chosen option and why
Consequences: cost (with and without cache), latency, lock-in, risks
Evidence: the evaluation result (set, metric, model and prompt version)
Revision criterion: e.g. quality below a threshold, price changed by X%, model retirement
```
Decisions that deserve an ADR: the pattern (workflow or agent), the model source and region, the retention policy at the provider,
fallback and routing, tenant isolation, the scope of actions without a human's approval.
