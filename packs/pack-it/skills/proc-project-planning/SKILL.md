---
name: proc-project-planning
description: Use for a project plan for the sponsor and a lifecycle model — a project charter, cost and schedule as ranges, risks.
metadata:
  review: "2027-10-03"
  catalog: "Use when planning a project before the start or when re-planning — the goal and the success measure, scope and 'out of scope', estimating cost and schedule as ranges (the cone of uncertainty, a reference class, a three-point estimate), a budget with a reserve for risks, resources and roles (RACI), stakeholders and communication, a risk register, milestones, staged funding, responding to a delay (Brooks's law), choosing a lifecycle model (waterfall, V, spiral, Agile, DevOps, an AI-native loop). Not for forecasting team throughput from data (proc-agile), deciding what to build (proc-product-discovery), the architect's technical estimates (arch-architect-practice) or cloud costs (ops-finops)."
  keywords: "plan projektu, model cyklu życia, model V, model kaskadowy, waterfall, model spiralny, harmonogram, budżet projektu, ile to będzie kosztować, kiedy będzie gotowe, termin, kamienie milowe, rejestr ryzyk, karta projektu, sponsor, kierownik projektu, szacowanie projektu, opóźniony projekt, dołożyć ludzi, project plan, lifecycle model, V-model, waterfall model, spiral model, schedule, project budget, how much will it cost, when will it be ready, deadline, milestones, risk register, project charter, project manager, project estimation, delayed project, add more people"
---

# Project planning

A project plan answers the sponsor's questions **why, what, for how much, by when, who and what can go wrong** — with explicit
uncertainty. The backlog, iterations and forecasts from throughput are in proc-agile; here is the frame the team works within.
The artifact: `docs/project/01-discovery/project-plan.md` (a template in core-project-record). For approval the sponsor gets
a **project charter** (PMI): one page with the goal, scope and out of scope, schedule and cost as
ranges, milestones, the biggest risks, the sponsor and the project manager's authority. Decisions about budget, schedule
and scope are made by a human (gate B1 in core-delivery-lifecycle); the agent prepares options and numbers.

## Rules
1. **The goal and the success measure before scope.**
   - A business outcome with a measure, e.g. "80% of bookings without a call to reception within 3 months of launch", not a list of features.
   - Scope always comes with an **"out of scope"** section.
   - You record constraints (budget, date, regulations) as inputs, not as an estimate.
2. **An estimate is a range with a date and a confidence level, never a single number.**
   - Give P50 and P80, e.g. "P50: 11 weeks, P80: 15 weeks, as of 2026-10-03".
   - **The cone of uncertainty** (McConnell): at the idea stage an estimate can be off by from 0.25× to 4×, and it narrows
     only with decisions (scope, requirements, a skeleton working end-to-end).
   - At the idea stage, instead of a point number you first propose cheap discovery that will narrow the range.
3. **The outside view first, then the inside view.**
   - Reference class forecasting (Flyvbjerg):
     1. pick a class of similar, completed projects;
     2. establish the distribution of their outcomes (cost and time: plan versus reality);
     3. place your project in that distribution.
   - Only then do you break the work into parts and estimate them with three points.
   - IT projects have a **fat tail of overruns**: in a study of 5392 projects the distribution was a power law, with a few
     overruns of many times. The sum of the estimates of the parts understates the result.
4. **A three-point estimate** (the PERT convention) for the parts:
   - the expected value E = (O + 4M + P) / 6, the deviation σ ≈ (P − O) / 6;
   - sum the E values, not the "most likely" M, because the distributions are right-skewed;
   - a range from the sum of variances assumes the parts are independent, so it is too narrow — correct it with the reference class.
   - A numerical example: `references/estimation.md`.
5. **Total cost:**
   - people × time × rate;
   - environments and cloud (ops-finops), licences;
   - AI models for the agent team (core-cost-control);
   - **maintenance after release** (phase 9 in core-delivery-lifecycle), at least for the first year;
   - state the source of the rates and the assumptions.
6. **Explicit, separate reserves:**
   - for identified risks (from the register, computed as P × impact);
   - a management reserve for the unknown, at the sponsor's disposal.
   - You do not hide a buffer in the estimates of the parts.
7. **Milestones are verifiable:**
   - you describe them by an outcome ("the end-to-end skeleton works in the test environment", "a pilot with 2 rooms"),
     not by a percentage complete;
   - the first milestone is the skeleton and checking the biggest risk (a spike).
8. **Staged funding:**
   - example stages: discovery → prototype (alpha) → a version with real users (beta) → production
     (the GOV.UK Service Manual pattern);
   - after each stage the sponsor decides: continue, change, stop;
   - the prototype from alpha may be thrown away.
9. **The risk register:**
   - the record is cause → event → impact;
   - probability and impact (1–5), response, owner, **early signal**, status;
   - responses to a threat: avoid, mitigate, transfer, accept (with a reserve); to an opportunity: exploit, enhance, share;
   - a review at every milestone (the process per ISO 31000: context → identification, analysis, evaluation → treatment →
     monitoring → reporting).
10. **People and roles:**
    - the real availability of people (leave, other projects);
    - **RACI** with one "A" per decision;
    - stakeholders with a communication plan: who, what, how often, through which channel;
    - business and legal decisions have an owner on the human side.
11. **Delay:**
    - **Brooks's law** — adding people to a late project usually delays it further (onboarding new people, more
      communication);
    - you propose in order: cutting scope (MVP, priorities), moving the date, removing obstacles;
    - adding people only for work that can be separated out, with the onboarding cost in the plan.
12. **The plan is alive:**
    - you update the forecast with data from delivery (throughput — proc-agile) at every milestone;
    - a deviation beyond the P80 range is a decision for the sponsor, not a quiet change;
    - a new version of the plan = a new approval (core-project-record).

## Lifecycle model — matching it to the project
| Model | When it fits | The risk when it does not fit |
|---|---|---|
| waterfall (sequential) | requirements are fixed and known up front, the whole is accepted at once (a contract, a tender), a lot of documentation required from outside | a change of requirements midway is expensive; errors surface only at testing |
| the V-model | verification and validation of every level are required, along with **traceability** requirement → design → test (medical devices, automotive, aviation) | heavy with uncertain requirements; combine it with short iterations inside the levels |
| spiral (Boehm) | a large, novel project with high risk: every loop starts with a risk analysis and a prototype | the analysis overhead on a small project |
| incremental / iterative, Agile (Scrum, Kanban) | requirements change, fast feedback from users matters (proc-agile) | without a goal and a budget frame, scope easily becomes endless |
| prototyping (RAD) | the interface and flows must be checked with users before the actual product is built | the prototype moves to production without a rewrite |
| DevOps / continuous delivery | the product lives long and changes often; the same team builds and maintains it (eng-continuous-delivery) | requires automated tests and deployments from the first step |
| an AI-native loop | agents write code faster than people review it: an artifact after every stage, a plan before code, evaluations, AI review of PRs (core-delivery-lifecycle) | without artifacts and gates you lose the audit trail and control |

Models are combined: e.g. the V-model at the level of requirements and system acceptance tests of a regulated system, and inside it iterations
with continuous delivery. Industry standards (e.g. IEC 62304 for medical device software) usually require
a documented process and traceability, not a specific model — check the standard's requirements for the project.

## Boundaries
- How a team plans sprints, cuts stories and forecasts from throughput: proc-agile; many teams: proc-safe.
- What to build and why (hypotheses, product metrics, feature priorities): proc-product-discovery.
- System capacity estimates and architectural decisions: arch-system-design, arch-architect-practice.

## Checklist
- [ ] the goal with a success measure; scope with "out of scope"; constraints as inputs
- [ ] cost and schedule as P50/P80 with a date; the source: a reference class + an estimate of the parts
- [ ] a risk reserve and a management reserve, separately
- [ ] milestones with a verifiable criterion; the first = the skeleton + the biggest risk
- [ ] a risk register with owners and early signals
- [ ] RACI with one A; a communication plan; the decisions for the sponsor to make listed

## Sources
- PMI, *PMBOK Guide — Eighth Edition* and *The Standard for Project Management* (November 2025): 6 principles, 7 performance
  domains — pmi.org/standards/pmbok; PMI: the project charter, risk responses — pmi.org/learning/library
- S. McConnell, the cone of uncertainty — construx.com/books/the-cone-of-uncertainty (accessed 2026-10-03)
- B. Flyvbjerg, reference class forecasting (PMI Learning Library); B. Flyvbjerg et al., the distribution of cost
  overruns of 5392 IT projects — arxiv.org/abs/2210.01573
- B. W. Boehm, "A Spiral Model of Software Development and Enhancement", IEEE Computer, 1988; V-Modell XT
- GAO-20-195G *Cost Estimating and Assessment Guide* (2020): the 12 steps of an estimate, reserves — gao.gov
- ISO 31000:2018 (the risk management process); GOV.UK Service Manual (the discovery, alpha, beta, live stages)
- F. P. Brooks, *The Mythical Man-Month* (1975)
Described in our own words.
