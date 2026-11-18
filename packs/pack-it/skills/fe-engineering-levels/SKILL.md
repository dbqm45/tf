---
name: fe-engineering-levels
description: Use for assessing the level of a frontend solution (Senior, Staff, Principal) and investment in DevEx.
metadata:
  review: "2027-10-17"
  catalog: "Use when you must assess at which level (Senior → Staff → Principal) to solve a frontend problem, and for work \"beyond the code\" — review and mentoring, a design system and standards for many teams, DevEx (FLOW, tight-loose), ROI and communication with the business, technical vision, sponsorship. Not for code knowledge (fe-architecture, fe-web-platform, fe-css) or DORA metrics (eng-continuous-delivery)."
  keywords: "tarcie programistów, wolny build, DevEx, standard dla wielu zespołów, koszt migracji, uzasadnienie dla biznesu, developer friction, slow build, standard for many teams, migration cost, business justification"
---

# Frontend engineer levels: Senior → Staff → Principal

This skill describes the **behaviours and competencies** of an engineer, not code. It is a map of questions: does the problem concern one
feature (the Senior lens), many teams in the company (Staff), or the whole company/industry (Principal). Technical knowledge
lives in the technical skills — here only pointers and expectations.

## Which lens to apply

| Question | Lens | Read |
|---|---|---|
| Does the problem fit within one feature/one repo/one team? | Senior | `references/senior.md` |
| Does the decision concern many teams, a shared design system, a standard, tooling for many repos, a budget? | Staff | `references/staff.md`, `references/devex.md` |
| Is the decision hard to reverse at company scale, does it concern a platform, the frontend/infra boundary or the industry? | Principal | `references/principal.md` |

- **Start from the lowest lens**, go higher only when the decision really goes beyond the team. The Principal lens
  on a local problem is the same mistake as overusing patterns (eng-design-principles).
- Distinguish **reversible** decisions (choosing a library in a module — decide quickly) from **irreversible** ones (a design
  system contract, a framework for hundreds of teams, the data model of a shared API — rigour, an ADR per docs-tech-writing).

## Expected behaviours (summary)

**Senior** — delivers a feature from idea to production with observability; explains and diagnoses (event loop,
leaks, CRP, LCP/INP/CLS, hydration) instead of reciting definitions; applies a pattern to a named problem and sees
its overuse; reviews with a concrete alternative and a split into blocking/nit; mentors through questions.

**Staff** — sets the standards of **many** teams and enforces them through automation (lint, CI, a shared HTTP client), not
individual knowledge; runs the design system as a product (tokens, governance, a contribution SLA, living documentation);
calculates the tooling migration cost **before** the decision; manages debt systematically (strangler fig, codemods, an explicit budget);
diagnoses DevEx friction before choosing a tool; translates decisions into business metrics (cost, benefit, payback horizon).

**Principal** — formulates the architecture "north star" by which teams decide on their own; treats the frontend as
a platform (roadmap, versioning, migration paths, adoption); talks with infrastructure as an equal
(edge, CDN, serverless — where the boundary lies); influences standards (open source, TC39, W3C); **sponsors** people
(opens opportunities), not only mentors them; shapes the culture (blameless postmortem, ADR, resolving disputes).

## Business communication — a shared rule for Staff+
- Express a technical cost in a metric the business already tracks (lead time, incidents, conversion, LCP → revenue), not "the code is ugly".
- A large investment = cost (person-time, risk of a delivery stall) + a measurable benefit + a payback horizon.
- "Loose" decisions (local to the team) do not require escalation; "tight" ones (many teams, budget, schedule) do.

## Where the technical knowledge is

| Topic | Skill |
|---|---|
| Event loop, CRP, Core Web Vitals, service workers, i18n, accessibility and WCAG | fe-web-platform |
| Architecture styles, FSD, micro-frontends, rendering models (SSR/RSC), patterns, client security | fe-architecture |
| Tokens, themes, style isolation | fe-css |
| Language and framework | lang-typescript, lang-javascript, fw-angular |
| GoF patterns, design principles | eng-design-principles |
| DORA, trunk-based, feature flags | eng-continuous-delivery |
| Team boundaries, platform team | proc-team-topologies |

## Checklist
- [ ] A named lens (Senior/Staff/Principal) and a justification for why not a lower one
- [ ] The decision marked as reversible/irreversible; an irreversible one has an ADR
- [ ] A standard for many teams enforced automatically (lint/CI), not only described
- [ ] A Staff+ decision has a cost, a benefit and a payback horizon in business language
- [ ] A DevEx change preceded by a friction diagnosis and measured after rollout

Sources: our own competency ladder from the "frontend-developer" import; DevEx — networkperspective.io, conlea.pl, signadot (described in our own words).
