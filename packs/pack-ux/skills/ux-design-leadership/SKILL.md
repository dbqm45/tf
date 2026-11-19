---
name: ux-design-leadership
description: Use for strategy and leading design in an organization — UX maturity, metrics (HEART, SUS), team structure, DesignOps, career paths, ROI.
metadata:
  review: "2027-10-17"
  catalog: "Use when you lead or build the design/UX function in an organization (Head of Design, UX Strategist, DesignOps) — UX maturity assessment (the NN/g model, six stages), a design vision and strategy tied to business outcomes, UX metrics (HEART, Goals-Signals-Metrics, SUS, task success), the structure of the design team (centralized, embedded, hybrid) and trade-offs, building DesignOps and ResearchOps (tools, processes, standards, rituals such as design critique), career paths and hiring designers, managing quality and accessibility, budget and ROI arguments for the board, the rhythm of work with product and engineering; the artifacts ux-maturity.md and design-strategy.md. Not for the structure of engineering teams in general (proc-team-topologies), product metrics and choosing what to build (proc-product-discovery), frontend engineer levels (fe-engineering-levels), the architect's practice (arch-architect-practice), research planning and methods (ux-research-methods), building a component library (ux-design-systems) or accessibility technique (ux-accessibility)."
  keywords: "head of design, szef designu, dyrektor UX, UX strategist, strategia designu, wizja designu, dojrzałość UX, UX maturity, jak przekonać zarząd do UX, ROI designu, budżet na design, metryki UX, HEART, SUS, NPS to za mało, mierzenie UX, zespół designerów, ilu projektantów, scentralizowany zespół designu, designerzy w zespołach, hybryda, DesignOps, ResearchOps, krytyka projektu, rytuały designu, ścieżka kariery projektanta, rekrutacja projektanta, ocena projektantów, jakość designu, governance, współpraca z produktem i inżynierią, design bez wpływu, design director, design strategy, design vision, convince the board about UX, design ROI, design budget, UX metrics, measuring UX, design team, how many designers, centralized design team, embedded designers, hybrid, design critique, design rituals, designer career path, hiring designers, assessing designers, design quality, working with product and engineering, design without impact"
---

# Design leadership — from the maturity assessment to the rhythm of work

Goal: a design function that affects business outcomes and can be **measured, organized and defended in the budget**.
You start from the actual state, not from the ideal: the maturity assessment dictates what to do first. The skill gives
a procedure for the person leading design; the team's work techniques (research, component system, accessibility) have their own
skills.

## Procedure
1. **Maturity diagnosis.** Assess the organization with the NN/g model (`references/maturity-and-metrics.md`): six stages
   (from "absent" to "user-driven") by four factors — strategy, culture, process, outcomes.
   The model is not a list to tick off in order: point out the stage **per factor** and the evidence (who decides the priorities,
   is there a budget, does research precede decisions). Result: `docs/project/01-discovery/ux-maturity.md`.
2. **Goal and constraints.** Ask the sponsor about 1–3 business outcomes design is to influence (e.g. a drop in
   onboarding churn, fewer support contacts). Without this the strategy is a wish list.
3. **Vision and strategy.** One page: the vision (what the experience looks like in 2–3 years), 3–5 pillars, for each
   a business outcome, an initiative, a metric and an owner; what we do **not** do. Record: `design-strategy.md`.
   Choosing what to build and the opportunity tree — proc-product-discovery; here only the link between design and outcomes.
4. **Metrics.** For each pillar the HEART frame (Happiness, Engagement, Adoption, Retention, Task success) in
   the Goals → Signals → Metrics process; choose only the relevant categories (usually 2–3 per product). For surveys SUS,
   for behaviours task success and task time. A metric without a threshold and an owner is not a metric
   (`references/maturity-and-metrics.md`). NPS alone does not show what to fix.
5. **Team structure.** Match the model to the maturity and the number of product teams (the table in
   `references/team-organization-and-maturity.md`): centralized, embedded or hybrid. The decision is recorded
   as an ADR (context, options, trade-offs, when we will revisit). Engineering teams and Conway's law — proc-team-topologies.
6. **DesignOps and ResearchOps.** Start from the biggest friction (e.g. no single tool, chaos in files, no
   participant recruitment), not from the full structure: tools and licences, onboarding designers, file
   and handoff standards, rituals (design critique every week, a quality review before release, a demo), budget.
   Research methods — ux-research-methods; component library — ux-design-systems.
7. **Career and hiring.** A path with levels and behaviour criteria (craft, impact, leadership), two
   tracks: expert and managerial; hiring with a task based on a real problem and one rubric for
   all candidates. The analogy for engineering: fe-engineering-levels.
8. **Quality and accessibility.** Quality gates in the process (a design review before handoff, an accessibility check,
   implementation matching the design) with one owner. Accessibility technique — ux-accessibility.
9. **Budget and the ROI argument.** You show the board: the cost of absence (support contacts, churn, fixes after
   release), the cost of the team and the expected effect with a **range** of uncertainty, not one number. The company's own data
   before external benchmarks; mark other people's numbers with a source and a date.
10. **Rhythm with product and engineering.** A shared cycle: quarterly planning with outcomes (not with a list of screens),
    discovery running 1–2 iterations ahead of building, a design review with engineering before the end of design,
    a shared metrics review after release. The rituals recorded in one place.

Result: `ux-maturity.md` (diagnosis), `design-strategy.md` (strategy, metrics, structure, a 90-day plan). TL;DR and
Handoff by core-project-record; the first line: `Design leadership: <organization> — stage <factor:stage,…>`.

## Example
Input: "A fintech, 180 people in product; 12 designers in 6 teams, each works their own way; the board asks whether
the investment makes sense."
Result (a fragment of `design-strategy.md`):

```markdown
Design leadership: fintech — strategy: process:3 culture:2 strategy:2 outcomes:2 (NN/g stages)
Pillars: (1) frictionless onboarding → outcome: activation from 41% to 55% in 2 quarters
Metrics (HEART): Adoption = account activation in 7 days; Task success = completing the verification without support
(target ≥ 85%); Happiness = SUS ≥ 75 (the average SUS in studied products is 68, i.e. about the 50th percentile).
Structure: hybrid — designers in product teams, the head of design as the management line; 1 DesignOps person.
The first 90 days: a shared library file, critique every Thursday, a hiring rubric; budget: 1 DesignOps FTE.
```

## Checklist
- [ ] a maturity assessment on four factors with evidence; not treated as a list to tick off
- [ ] a strategy tied to 1–3 business outcomes, with a list of things we do not do
- [ ] HEART metrics in the Goals-Signals-Metrics layout with a threshold and an owner
- [ ] the team structure decision recorded as an ADR with trade-offs
- [ ] DesignOps starts from the biggest friction; rituals and quality gates have an owner
- [ ] an ROI argument with an uncertainty range and sources; [unverified] marked

## Additional materials
- `references/maturity-and-metrics.md` — the NN/g stages, HEART, SUS, a metrics frame template; read for the diagnosis and metrics.
- `references/team-organization-and-maturity.md` — team structures, DesignOps, career, ROI; read when designing the organization.

## Sources
- NN/g, *UX Maturity Model* (nngroup.com/consulting/ux-maturity-assessment/ and articles on stages 1–5), accessed
  2026-10-17: six stages (absent, limited, emergent, structured, integrated, user-driven), four factors
  (strategy, culture, process, outcomes). The description of stage 6 according to secondary sources [unverified].
- Rodden, Hutchinson, Fu, *Measuring the User Experience on a Large Scale* (Google, CHI 2010) — HEART and
  Goals-Signals-Metrics; confirmed by secondary sources, the original was not opened (accessed 2026-10-17).
- MeasuringU (Sauro, Lewis), SUS: an average of 68 ≈ the 50th percentile (accessed 2026-10-17).
- Futurice, *DesignOps — small team starter guide* — a description of the models and the risks of a hybrid (accessed 2026-10-17).
Described in our own words.
