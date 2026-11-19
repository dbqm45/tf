# Templates: implementer brief and audit report

## Brief for an implementer (stage 1)
```
Code audit — dimension: <dimension>. Depth: <quick|standard|full>.
Scope: <modules / directories>; outside the scope: <vendor/, generated code, …>.
Inventory (read it first, do not scan the repo from scratch): docs/project/07-review/<date>-code-audit-inventory.md
Load the skills: <skill-1>, <skill-2>.
Question: <one question, e.g. "Which places let a user read someone else's data?">
Do not change the code. Do not run scans against running systems.
Result (≤ <N> findings, the most important first; "nothing significant" is a correct result):
| ID | file:line | risk (1–4) | reach (1–3) | cost of the fix (S/M/L) | evidence | proposal |
At the end: what you did not check and why (1–3 points).
```

## Report (`docs/project/07-review/<date>-code-audit.md`)
```markdown
---
artifact: review
phase: review
status: proposed
version: 1
author: <who>
created: <date>
updated: <date>
inputs: [docs/project/07-review/<date>-code-audit-inventory.md]
---
# Code audit — <system>, <date>

## TL;DR
- Scope: <dimensions>, depth <…>, budget <…>.
- Blockers: <count> (below).
- The 3 most important findings: <…>.

## Blockers (outside the ranking, for an immediate decision)
| ID | dimensions | file:line | evidence | proposal |
|---|---|---|---|---|

## Ranking
Priority = risk × reach ÷ cost (S = 1, M = 2, L = 4).
| # | ID | dimensions | file:line | risk | reach | cost | priority | description | proposal | handover |
|---|---|---|---|---|---|---|---|---|---|---|

## Top 10 — a sketch of the change
<!-- for each: what to change, briefly a diff or steps; you do not carry it out -->

## Quick wins
<!-- cost S with risk ≥ 2 -->

## Hypotheses to check (without evidence, outside the ranking)

## Contradictions and decisions for the human
<!-- who recommends what, the compromise, the proposed ADR -->

## What was not checked
<!-- skipped dimensions, missing tools, modules outside the scope, environment limitations -->

## Audit cost
| Stage | Implementers | Models | Cost |
|---|---|---|---|
Total: <amount> out of the budget <amount> (source: `python3 .tf/factory/cost_report.py --days 1`).

## Comparison with the previous audit (if there was one)
| ID | status (RESOLVED / NEW / CHANGED) | notes |
|---|---|---|

## Handoff
- **For:** <the human / the persona carrying out the fixes>.
- **Task:** decisions on the blockers and contradictions, then fixes according to the ranking (separate tasks).
- **Read:** TL;DR, Blockers, Ranking.
```

The inventory file (`<date>-code-audit-inventory.md`) lies in the same directory, so it has the same header (without the `inputs`
from the inventory: `inputs: []`) and the TL;DR and Handoff sections. After writing: `python3 .claude/hooks/project_record.py check`.
