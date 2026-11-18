---
name: proc-safe
description: Use when many teams work in SAFe — the Agile Release Train, PI Planning, roles, WSJF, Inspect & Adapt, LPM.
metadata:
  review: "2027-10-17"
  visibility: name
  catalog: "Use when the work spans many teams in a large organization that uses SAFe — the Agile Release Train, PI Planning, roles (RTE, Product Management, System Architect, Business Owners), the backlog hierarchy, WSJF, Inspect & Adapt, Lean Portfolio Management — and when assessing whether SAFe fits. Not for the work of a single team (proc-agile)."
---

# SAFe (Scaled Agile Framework)

State of knowledge: SAFe 6.0 with the 2025 updates (the model of **five disciplines**: Leadership and Culture, Team and Technical Agility,
Product Development Flow, Large Solution Integration and Delivery, Lean Portfolio Management; the AI-Driven Agility initiative).
The basic constructs (ART, PI Planning, LPM) are unchanged. Check details at framework.scaledagile.com.

## The 10 Lean-Agile principles of SAFe
1. Take an economic view. 2. Apply systems thinking. 3. Assume variability; preserve options. 4. Build incrementally with fast,
integrated learning cycles. 5. Base milestones on an objective evaluation of working systems. 6. Make value flow without
interruptions. 7. Apply cadence and synchronize planning across domains. 8. Unlock the intrinsic motivation of knowledge
workers. 9. Decentralize decision-making. 10. Organize around value.

## Constructs
- **Configurations**: Essential (teams + ART), Large Solution (many ARTs), Portfolio (+ portfolio management), Full.
- **Agile Release Train (ART)**: a long-lived team of teams (usually ~50–125 people) organized around a value stream.
- **Program Increment (PI)**: a cadence usually of 8–12 weeks (several iterations + an IP iteration: innovation and planning).
- **ART events**: **PI Planning** (everyone together, PI objectives and dependencies on the program board), ART Sync (Coach Sync + PO Sync),
  **System Demo** (an integrated increment every iteration), **Inspect & Adapt** (a demo, metrics, a problem-solving workshop).
- **Roles**: Release Train Engineer (RTE), Product Management (what, at the ART level), System Architect, Business Owners
  (they accept the PI objectives and their value), in the teams the Product Owner and Scrum Master/Team Coach.
- **Backlog**: Epic (portfolio, with a hypothesis and a Lean business case) → Capability (Large Solution) → Feature (ART, fits in a PI) → Story (team).
- **Priorities: WSJF** = cost of delay (business value + time criticality + risk reduction/opportunity enablement) / size.
- **Lean Portfolio Management**: funding value streams instead of projects, Portfolio Kanban, limiting WIP of epics.

## When it fits and when it does not
- It fits: many teams work on a shared solution with real dependencies and a need for synchronization; the organization
  is ready to change funding and structure around value streams.
- It does not fit / risks: a few independent teams (proc-agile is enough), SAFe as a layer of names over the old process
  ("SAFe-washing"), PI Planning as a scope contract instead of a shared plan, ARTs cut by departments instead of by value.
- Before you add coordination, **reduce dependencies**: context boundaries (ddd-strategic-analysis) and the structure of teams
  (proc-team-topologies) often remove the need to scale the process.

## Example
**Situation:** Product Management is arguing: "BLIK brings the most, so it goes first". **Result (WSJF, relative
ratings):** BLIK has the highest cost of delay, but smaller features give more per unit of work; this is the basis
for a conversation at PI Planning, not a verdict.

| Feature | Cost of delay | Size | WSJF |
|---|---|---|---|
| Feature flags | 1 + 2 + 8 = 11 | 2 | **5.5** |
| Replacing the encryption library | 2 + 8 + 7 = 17 | 5 | **3.4** |
| BLIK payment | 9 + 7 + 2 = 18 | 6 | **3.0** |

More examples: `references/examples.md`.
