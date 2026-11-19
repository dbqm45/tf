---
name: ops-cloud-migration
description: Use for migrating workloads to the cloud or between environments — portfolio, 7R strategies, waves, data, cutover, rollback.
metadata:
  review: "2027-04-17"
  visibility: name
  catalog: "Use when you plan to move applications, databases or a whole data center to the cloud or between clouds and environments — discovery and portfolio assessment (dependencies, data gravity, licences), the 7R strategies (retire, retain, rehost, relocate, replatform, repurchase, refactor), waves and move groups, a pilot, data migration (offline transfer, replication, dual-write, cutover with a downtime budget), a cutover runbook and a rollback plan, hybrid connectivity, success criteria, post-migration optimization, typical mistakes. The result is a migration plan with waves and a cutover runbook. Not for release strategy (ops-release-engineering), database schema migrations (be-database), the Strangler pattern in code (eng-refactor-planning) or building the cloud foundation (ops-cloud-landing-zones)."
  keywords: "migracja do chmury, cloud migration, lift and shift, 7R, rehost, replatform, refactor, repurchase, retire, retain, relocate, fale migracji, wave planning, discovery, portfel aplikacji, przeniesienie serwerowni, cutover, rollback, przełączenie, okno przestoju, replikacja danych, DMS, migracja bazy do chmury, połączenie hybrydowe, Direct Connect, ExpressRoute, migracja między chmurami, migration waves, application portfolio, moving a server room, switchover, downtime window, data replication, migrating a database to the cloud, hybrid connectivity, migration between clouds"
---

# Cloud migration: portfolio, waves, cutover

The goal: move workloads predictably, with a reversible switchover and proof that after the migration things are no worse.
The result: `docs/project/05-plan/migration-plan.md` (core-project-record): the portfolio with a strategy, waves, a data plan,
a cutover runbook, success criteria. The target foundation (accounts, network, identity) is ops-cloud-landing-zones and must
exist before the first wave. The skill does not switch anything over: production changes go with a plan, a change window and a human's
approval; every step has an owner.

## Procedure
1. **The goal and constraints.** Why we are migrating (exiting a data center by the contract date, cost, scaling, regulations)
   and what is non-negotiable (the date, the downtime budget, data residency). The goal "because cloud" does not let you choose a strategy.
2. **Discovery.** An inventory: servers, applications, databases, **dependencies** (network traffic, who talks to whom — from
   observation over at least a full business cycle, e.g. the end of the month, not from documentation), owners,
   the operating system and vendor support, **licences** (whether running in the cloud is allowed, the per-core/socket model),
   **data gravity** (size, rate of change, who reads it), requirements: RPO/RTO, latency, compliance.
   Provider tools (AWS Application Discovery Service / Migration Hub, Azure Migrate, Google Migration Center)
   [unverified: current names and features]. Mark gaps in the data explicitly.
3. **A strategy per application (7R)**, per AWS Prescriptive Guidance:
   | Strategy | Meaning |
   |---|---|
   | retire | switch off, because nobody uses it (often a few to a dozen or so % of the portfolio [example]) |
   | retain | leave it where it is (a reason and a reassessment date) |
   | rehost | "lift and shift", without application changes |
   | relocate | a move at the hypervisor or container level without buying hardware and without application changes |
   | replatform | a small optimization (e.g. a managed database) without changing the architecture |
   | repurchase | a switch to another product, usually SaaS |
   | refactor | an architecture change for the cloud (code: Strangler Fig in eng-refactor-planning) |
   By default the cheapest strategy that meets the goal (from step 1); refactor only when business value justifies it,
   not as part of a migration under date pressure. The definitions of retire, retain and repurchase are summarized [unverified: the literal AWS text];
   the sources list seven categories, but not identically in every guide (origin from Gartner: 2011 or 2019).
4. **Waves and move groups.** A group = applications that must move together (strong dependencies, a shared database,
   latency). A wave = groups moved in one time window. The order:
   - **a pilot**: 1–3 low-risk but representative applications (they test the process, the tools, the network and the team);
   - then from the simplest and least connected to the hardest; critical and strongly coupled ones at the end;
   - a limit on the team's throughput (how many cutovers at once) and the business calendar (not at the peak of the season).
   A dependency between waves = a shared bottleneck: record it and check it (e.g. a shared database splits a group).
5. **Hybrid connectivity.** For the duration of the migration both sides see each other: a VPN or a dedicated link (Direct Connect,
   ExpressRoute, Cloud Interconnect), consistent addressing without overlapping CIDRs (the registry from ops-cloud-landing-zones),
   DNS resolving both sides, identity available on both. Calculate the bandwidth and latency: an application
   talking to a database "on the other side" often becomes slow (many small queries over the WAN). Plan the link
   with headroom and decide when it is switched off.
6. **Data.** The choice by size, rate of change and the downtime budget (the switchover time):
   | Approach | When | Note |
   |---|---|---|
   | offline transfer (a physical device, a copy) | large, rarely changed data, a slow link | calculate the delivery time and the catch-up of the delta |
   | a one-off copy in the window | small data, a long window | a simple rollback = the old source |
   | continuous replication (CDC, native replication, DMS) | large and live data, short downtime | monitor the replication lag; you switch over at a lag ≈ 0 |
   | dual-write | when there is no replication; very carefully | a risk of divergence, requires reconciliation; the last option |
   Verification: row counts, checksums, a business sample. The schema and version migrations: be-database.
   Data residency and personal data: arch-privacy-compliance.
7. **Cutover and the runbook.** A separate document per group: numbered steps with an owner, a time and a command;
   a change **freeze**; a final sync; a smoke test; switching the traffic (DNS with a TTL lowered beforehand, the load
   balancer; release patterns: ops-release-engineering); a **go/no-go** decision with criteria written down in advance. Record
   **the point of no return** (after it a rollback is a restore, not a switch back) and the downtime budget broken down into steps.
   A dress rehearsal on a copy against the clock; after it a corrected runbook.
8. **Rollback.** The rollback plan ready before the cutover: trigger conditions (metrics, time), steps, who decides,
   what happens to the data written on the new side (reverse replication or a loss agreed with the business). The source
   stays running and unchanged until the end of the stabilization period (e.g. 2–4 weeks [example]); switched off only
   after acceptance.
9. **Success criteria and after the migration.** Before the start, measure the baseline: p95 latency, errors, cost, availability
   (ops-observability; SLO: ops-sre-incidents). Success = thresholds in the same measures plus the source shut down.
   Then optimization: rightsizing, reservations after 1–3 months of data, tags and budgets (ops-finops),
   switching off links and licences, a wave retrospective.
10. **The record.** The portfolio (a table: application, strategy, group, wave, owner, risk), the wave schedule, the data plan,
    the runbook and rollback per group, risks. Status `proposed`; execution after a human's approval.

## Typical failures
- Hidden dependencies (a batch job once a month, hardcoded IPs, a shared network drive).
- Uncalculated WAN latency and the cost of outbound data transfer.
- The licence does not carry over to the cloud, and this comes out after the cutover.
- No dress rehearsal and no point of no return in the runbook.
- Lift and shift without later optimization: the bill is higher than in the data center.
- Switching off the source on the day of the cutover.

## Example
**Situation:** "We are leaving the server room by the end of March. 120 applications, an orders database of 2 TB (it changes all day), a downtime window of 30 minutes."
**Result** (a fragment, numbers [example]):

| Application | Strategy | Group | Wave |
|---|---|---|---|
| legacy-intranet | retire | — | 0 |
| batch-reports | rehost | G2 | 1 (pilot) |
| orders + database | replatform (managed database) | G5 | 3 |
| legacy-ERP (per-socket licence) | retain until renegotiation, assessment 2027-Q2 | — | — |

The orders database: continuous replication from T-14 days; cutover at night: freeze → replication lag < 5 s → cut off
writes → sync → smoke test → DNS (TTL lowered to 60 s a day earlier). The 30-minute budget: freeze+sync 10, test 10,
DNS 5, headroom 5. The point of no return: after the first write to the new database; a rollback until that moment = switching DNS back.

## Checklist
- [ ] the goal and non-negotiable constraints; the target foundation ready
- [ ] dependencies from observing a full cycle, licences and data gravity in the inventory
- [ ] a 7R strategy with a justification for every application (including retire and retain)
- [ ] a representative pilot; dependency groups; waves with the business calendar
- [ ] hybrid connectivity: CIDRs without collisions, DNS, bandwidth, latency
- [ ] the data method matched to the downtime budget; data consistency verification
- [ ] a runbook with go/no-go, a point of no return and a dress rehearsal; a rollback with conditions
- [ ] a measurement baseline before the migration, the source kept until the end of stabilization
- [ ] optimization and a retrospective after the wave

## Sources
- AWS Prescriptive Guidance: migration strategies (7R), glossary, detailed portfolio discovery — search 2026-10-17,
  documentation pages not directly accessible; the definitions of relocate, rehost and replatform confirmed, retire/retain/repurchase [unverified]
- Microsoft Learn: Cloud Adoption Framework (Migrate); Google Cloud: Migration Center and migration guides — not checked in detail
  [unverified]
