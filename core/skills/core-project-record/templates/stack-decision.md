---
artifact: stack-decision
phase: architecture
status: draft
version: 1
author: <agent>
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
inputs: [docs/project/03-requirements/requirements.md, docs/project/02-domain/strategic.md]
---
# Stack decision: <name>

## TL;DR
<The recommended stack in 1–2 sentences, why (3 main reasons), the biggest risk and how we will check it.>

## Decision drivers
| Driver | Source (requirement/constraint) | Weight (1–5) |
|---|---|---|
## Mandatory filters
<e.g. compatibility with the customer's hosting, licence, the team's skills at the start>
## Options considered
| Area | Option A (default, "boring") | Option B | Option C |
|---|---|---|---|
## Assessment matrix
| Criterion (weight) | A | B | C |
|---|---|---|---|
## Verified facts (versions, support, licences — with sources and a date)
| Technology | Version / LTS / end of support | Source | Checked |
|---|---|---|---|
## Recommendation
| Layer | Choice | Rationale |
|---|---|---|
## Platform and operational story (MVP)
| Axis | Concrete answer |
|---|---|
| A preview for every PR (and its protection) | |
| Secrets (where, who reads them, rotation) | |
| Rollback (command, time, migration caveats) | |
| What needs a human | |
| Logs for the agent (read only: CLI or MCP) | |
## Resilience test (devil's advocate, pre-mortem, unknown unknowns)
| Risk | Source (lens / research) | Likelihood | Impact | Action |
|---|---|---|---|---|
## Signal to revisit the decision
<Which measurable signal makes us come back to this decision (e.g. hosting cost > X per month, build time > Y min).>
## Risks and experiments (spikes)
| Risk | How we will check | Criterion for dropping the choice |
|---|---|---|
## Skills and personas
- Skills needed: <lang-*, fw-*, tool-*> — available: …, to create: …
- Suggested persona `stack`: …

## Open questions
## Handoff
- **For:** <the delivering persona>, the plan orchestrator
- **Task:** the delivery plan (05-plan/plan.md) and the spikes from the Risks section
- **Read:** TL;DR, Recommendation, Risks
