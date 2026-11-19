---
name: proc-lean
description: Use for work flow and priorities — Lean, waste, Little's law, VSM, MVP, cost of delay, WSJF.
disable-model-invocation: true
metadata:
  status: "inactive"  # measured 2026-11-16: docs/inactive-skills.md
  review: "2027-10-17"
  catalog: "Use when improving the flow of work and making priority decisions — the principles of Lean Software Development, waste in IT, flow and Little's law, value stream mapping, Lean Startup (build–measure–learn, MVP), cost of delay and WSJF. Not for Scrum/Kanban rituals (proc-agile) or SAFe (proc-safe)."
  keywords: "WIP, praca w toku, czas realizacji, przepływ, wąskie gardło w procesie, ile zadań naraz, koszt opóźnienia, work in progress, lead time, flow, process bottleneck, how many tasks at once, cost of delay"
---

# Lean in software development

## Flow
Little's law, pull instead of push, waste according to Lean Software Development; in practice:
- **WIP = 1–2 per person**, WIP limits on the board; less work in progress means a shorter lead time.
- **Value stream mapping (VSM)**: the steps from idea to production with work time and waiting time; flow
  efficiency = work time / total time. **Improve the biggest wait, not the most expensive stage.**
- Against handoffs and waiting (reviews, environments, decisions): cross-functional teams, SLAs on reviews,
  automated environments, trunk-based development.

## Lean Startup
Build → measure → learn. An **MVP** = the cheapest experiment that verifies a hypothesis (it may not be software).
A hypothesis with a success measure and a decision threshold set **before** the experiment; the decision: continue / change direction (pivot) / abandon.

## Economic priorities
**WSJF** = cost of delay (how much we lose per week of delay) / size: short things with a high cost of delay first.
