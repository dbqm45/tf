---
name: ops-platform-engineering
description: Use for an internal developer platform (IDP) — platform as a product, golden paths, portal, self-service, metrics.
metadata:
  review: "2027-04-17"
  catalog: "Use when building and running an internal developer platform for many teams — platform as a product (the users are developers, discovering pain points, a roadmap, adoption metrics), the thinnest viable platform, golden paths and templates, self-service with guardrails, a portal (e.g. Backstage), infrastructure abstractions (Crossplane compositions, Terraform modules, Kubernetes operators), GitOps (Argo CD, Flux), policy as code, the platform team topology and interaction modes, success measures (DORA, SPACE, developer experience surveys), the CNCF Platforms White Paper and the Platform Engineering Maturity Model. The result is a platform charter and a roadmap. Not for dividing the organization into team types (proc-team-topologies), building pipelines (ops-ci-cd), Kubernetes manifests (ops-kubernetes), writing Terraform modules, defining DORA metrics (eng-continuous-delivery) or the foundation of cloud accounts and networks (ops-cloud-landing-zones)."
  keywords: "platforma wewnętrzna, platforma dla wielu zespołów, zespoły wdrażają po swojemu, od czego zacząć platformę, platforma której nikt nie użyje, czy platforma się opłaciła, metryki platformy, zwrot z platformy, wskaźniki sukcesu platformy, internal developer platform, IDP, platform engineering, zespół platformowy, złota ścieżka, golden path, paved road, portal deweloperski, Backstage, samoobsługa, self-service, Crossplane, GitOps, Argo CD, Flux, policy as code, developer experience, DevEx, adopcja platformy, roadmapa platformy, karta platformy, ticket do ops, szablony serwisów, dojrzałość platformy, SPACE, ankieta deweloperów, internal platform, platform for many teams, every team deploys its own way, where to start a platform, a platform nobody will use, did the platform pay off, platform metrics, platform return, platform success indicators, platform team, developer portal, platform adoption, platform roadmap, platform charter, ticket to ops, service templates, platform maturity, developer survey"
  visibility: name
---

# Platform engineering — an internal developer platform

**Boundary.** Team types and interaction modes (platform team, X-as-a-Service) — **proc-team-topologies**; here only their
application to the platform team. Pipelines — **ops-ci-cd**; manifests — **ops-kubernetes**;
DORA definitions — **eng-continuous-delivery**; the foundation of accounts and networks — **ops-cloud-landing-zones**;
releases and GitOps from the deployment side — **ops-release-engineering**. Changes on the platform's real clusters and accounts
you propose as a plan (diff, dry-run, change window) and apply after approval by a human.

## Procedure
1. **Is a platform needed.** Signals: many teams rebuild the same thing (CI, deployment, database, monitoring), long
   queues to ops, a wide variety of tools, onboarding measured in weeks. With 2–3 teams a shared
   template and good documentation are enough, not a separate team.
2. **Users and pain points.** The users are the development teams. Conduct 8–12 interviews (several teams, different
   experience levels), map the "idea → production" path with waiting times, collect the requests to ops. Record the pain points
   with the number of teams and the cost (time, risk). Without this the roadmap is guesswork.
3. **Platform as a product.** A product owner, a vision, a roadmap by impact on the pain points (proc-product-discovery, RICE/WSJF), a public backlog, a feedback loop. The platform is **voluntary**: a team chooses it because it is easier
   (CNCF Platforms White Paper: a platform should not be mandatory or block tools outside it). Only the requirements
   (security, cost) are mandatory, not the way to meet them.
4. **The thinnest viable platform (TVP).** Start with one, most painful flow for 1–2 pilot teams
   (e.g. "a new service in production in 1 day"), not with a portal. Deliver a thin layer over what already exists,
   and extend it after proof of use. Test: would the pilot go back to the old way?
5. **Golden paths and templates.** A service template contains the repository, the pipeline, observability, cost tags, secrets,
   scanning; it has an owner, a version and an upgrade path for existing services (otherwise the templates drift apart).
   The path covers 80% of cases; leaving it is allowed, but with your own maintenance.
6. **Self-service with guardrails.** A developer requests a resource declaratively (a PR, a form in the portal, a CRD file), without a ticket.
   Security is built into the abstraction (encryption by default, a private network, tags) and enforced by
   **policy as code** (e.g. OPA/Gatekeeper, Kyverno, policies in the pipeline) in audit mode, then enforcement; a denial
   returns a readable message with the fix.
7. **Infrastructure abstractions** — chosen by the required contract, not by fashion:

| Need | Tool | Note |
|---|---|---|
| consistent cloud resources with your own policy | Terraform/OpenTofu modules | a simple start; self-service requires a pipeline and state |
| your own "Database"-type API over many resources | Crossplane: XRD and Composition | reconcile in the cluster; cost: the CRD model and debugging |
| logic for one kind of resource in the cluster | a Kubernetes operator | you maintain the code; use ready ones when they exist |
| deploying state from git | GitOps: Argo CD or Flux | reconcile and drift; releases — ops-release-engineering |
   One abstraction = one contract versioned like an API (backward-incompatible changes through versions).
8. **Portal (optional).** A service catalogue, templates (software templates), documentation, status. Backstage is an open
   portal framework (a CNCF project) — it requires a team to maintain the plugins and permissions; the alternative is a ready product
   or just a template repository and a CLI. Build the portal after the paths work; start the catalogue with owners
   and dependencies, because that is what is most often missing.
9. **Team and interactions.** The platform team (platform type, about 5–9 people at the start [example]), the default mode
   X-as-a-Service, at the start Collaboration with the pilot teams, Facilitating when rolling out templates
   (proc-team-topologies). Watch the cognitive load of the platform team itself: the number of products, the on-call rotation, support.
10. **Success measures.** Four layers, none as a reward target (Goodhart's law):
   - **adoption:** the share of teams/services on the golden path, active users, onboarding time, the number of tickets to ops;
   - **DORA** (eng-continuous-delivery) at the service level, compared over time for the same system, not between teams;
   - **experience:** a survey (e.g. quarterly) on satisfaction, cognitive load, feedback loops and flow (DevEx), the SPACE dimensions (satisfaction, performance, activity, communication, efficiency);
   - **business and cost:** the "idea → production" time, the platform cost per team, incidents caused by the platform.
   A report for the management board: the trend of 3–4 measures, a conclusion and a decision, not a wall of metrics; plus a self-assessment per the CNCF Platform
   Engineering Maturity Model (item 11) as a map of gaps, without ranking teams.
11. **Maturity.** A self-assessment per the CNCF Platform Engineering Maturity Model: five aspects (investment, adoption, interfaces,
    operations, measurement) assessed separately on four levels. Use it for conversation and gaps, not for ranking teams.
12. **Result:** a platform charter (goal, users, pain points, the "is/is not" scope, measures, owner, collaboration mode)
    and a roadmap (Now/Next/Later with a hypothesis and a measure for each item) in `docs/project/`.

## Example
Input: "30 teams, each has a different pipeline and orders databases manually; ops gets 60 tickets a month."

Result (excerpt) [example, illustrative numbers]:
- Pain point no. 1 (11 of 12 interviews): "a new service in production = 3 weeks"; no. 2: a database via a ticket, 5 days.
- Charter: the goal "a new service with a pipeline, observability and a database in ≤ 1 day without a ticket". Out of scope for year 1: the portal, FinOps, ML.
- Roadmap: Now — a service template + pipeline (2 pilot teams), a database through a Composition in Crossplane or a Terraform module via PR;
  Next — policy as code in audit mode, an owner catalogue; Later — the portal.
- Measures: time to first deployment (target 1 day), the share of teams on the path (pilot 2 → 10 in 2 quarters), tickets to ops (−50%),
  a DevEx survey every quarter. We do not reward teams for numbers; we track the DORA results over time per service.
- Interaction: Collaboration with the pilots for 6 weeks, then X-as-a-Service.

## Checklist
- [ ] user interviews and pain points with the number of teams; the need for a platform justified
- [ ] a product owner, a roadmap by pain points, the platform voluntary
- [ ] the thinnest viable platform with pilot teams
- [ ] a golden path with a version and an upgrade path for templates
- [ ] self-service with guardrails (policy as code: audit, then enforcement)
- [ ] abstractions versioned like an API; the choice of tool justified
- [ ] measures: adoption, DORA over time, a DevEx/SPACE survey, cost; not as targets
- [ ] a self-assessment per the Platform Engineering Maturity Model; the charter and roadmap recorded

## Sources
- CNCF TAG App Delivery, "CNCF Platforms White Paper" (v1, 2023) — platform attributes: product, user experience, voluntariness, golden paths; tag-app-delivery.cncf.io, searched 2026-10-17 (the page could not be fetched in the session).
- CNCF TAG App Delivery, "Platform Engineering Maturity Model" (2023; per the secondary source bex.co, version 2 of 2026-03-23, core unchanged) — five aspects, four levels; the level names differ between sources [unverified].
- CNCF: Crossplane — promotion to the graduated level announced 2025-11-06; Argo — graduated since 2022-12-06 (cncf.io/projects/argo); Flux — graduated [per a secondary source, unverified]; Backstage — CNCF maturity level [unverified, sources disagree], check at cncf.io/projects.
- Forsgren et al., "The SPACE of Developer Productivity" (2021); Noda et al., "DevEx" (ACM Queue, 2023) — through secondary sources, 2026-10-17 [unverified at the source].
- DORA, "2025 State of AI-assisted Software Development" and the DORA AI Capabilities Model — one of the seven capabilities is high-quality internal platforms (secondary sources, 2026-10-17).
