---
name: ops-multi-region-resilience
description: Use for HA and DR design across zones and regions — RTO/RPO per tier, DR strategies, replication, failover, DR tests.
metadata:
  review: "2027-04-17"
  catalog: "Use when designing resilience to a zone or region failure — business impact and RTO/RPO per service tier, choosing a DR strategy (backup and restore, pilot light, warm standby, multi-site active-active) with its cost, data replication (synchronous and asynchronous, consistency, conflicts, split-brain), traffic routing and failover (DNS, global load balancers, client retries), dependence on the region's control plane and static stability, failover and failback runbooks, DR tests and game days, chaos experiments with a blast radius limit, evidence for the auditor. The result is a resilience design with a tier table and a DR test plan. Not for SLOs, error budgets, incidents and backup basics (ops-sre-incidents), availability scenarios as a quality attribute (arch-quality-attributes), replication inside the database itself (be-database) or release strategy (ops-release-engineering)."
  keywords: "awaria całego regionu, region chmury padł, strategia DR, jaką strategię DR wybrać, ile może stać system, disaster recovery, DR, awaria regionu, awaria strefy, multi-region, wieloregionowy, failover, failback, RTO, RPO, pilot light, warm standby, active-active, active-passive, split-brain, replikacja między regionami, plan ciągłości działania, BCP, game day, test DR, chaos engineering, static stability, Route 53 health check, globalny load balancer, drugi region, ćwiczenie awarii, failure of a whole region, cloud region went down, DR strategy, which DR strategy to choose, how long can the system be down, region failure, zone failure, multi-regional, cross-region replication, business continuity plan, DR test, global load balancer, second region, failure exercise"
  visibility: name
---

# Multi-zone and multi-region resilience (HA/DR)

**Boundary.** SLOs, error budgets, incidents and backup basics (RPO/RTO, a restore test) — **ops-sre-incidents**.
An availability scenario as an architecture driver — **arch-quality-attributes**. Replication in the database engine — **be-database**.
This skill starts where the question is "what if a whole zone or region goes down, and how will we prove it?".
Changes in real infrastructure (switching traffic, a test in production) you propose as a plan with a change window
and carry out only after approval by a human.

## Procedure
1. **Business impact → tiers.** For each service (user journey): the cost of an hour of downtime, the acceptable data loss,
   legal requirements (e.g. DORA/NIS2 — sec-eu-regulations), dependencies (upstream and downstream). From this the **RTO** (time to restore)
   and the **RPO** (the window of lost data). Group services into 3–4 tiers; the target applies to the tier, not to a single team.
   A dependency cannot have a weaker tier than the service that depends on it — otherwise the target is fiction.
2. **Failure scope.** Separate: an instance failure, a zone (AZ), a region, a provider, human error or a malicious change
   (replication also replicates deletion and corruption — an immutable backup is needed, ops-sre-incidents).
   Multi-zone (HA) protects against a zone; a region requires DR. A region is not always the goal: if the SLO and the law do not require it, stop at zones.
3. **DR strategy per tier** (the four strategies from the AWS whitepaper "Disaster Recovery of Workloads on AWS"; the names are also used outside AWS):

| Strategy | What runs in the second region | Recovery | Cost and complexity |
|---|---|---|---|
| backup and restore | only backups (outside the region) | rebuilding the infrastructure and data from backups | lowest |
| pilot light | data replicated, the core ready, compute turned off | starting and scaling on failure | low |
| warm standby | a scaled-down, fully working copy | scaling up on failure | medium |
| multi-site active-active | full traffic handling in both regions | no "switchover" — one region drops out | highest, including data consistency |

   As a rough guide: the lower the RTO/RPO, the more expensive, and the thresholds between strategies depend on the system — measure your own RTO/RPO with a test,
   do not read it from the table. Warm standby and active-active make sense only for tier 0–1; the rest usually backup or pilot light.
4. **Data.** For each store choose the replication:
   - **synchronous** — RPO≈0, but write latency grows with distance and a link failure blocks writes;
   - **asynchronous** — low latency cost, RPO>0 (measure the lag and alert), on failover the last writes may be lost;
   - **multi-writer** — requires a conflict rule (last-writer-wins loses writes; CRDT, domain merging, or assigning
     a record's owner to a region); without a rule do not enable writes in two places.
   - **split-brain**: one leader with proof (quorum, lease, fencing token), automatic promotion only with a third witness outside both regions.
   Database engine details — be-database; sessions, queues, cache, objects and secrets also have replication (and their own lag).
5. **Traffic and failover.** DNS with health checks (a low TTL, but clients and resolvers stretch it — the real time ≥ TTL),
   a global load balancer/anycast, client retries with jitter and a limit (a retry storm after the switchover). The health check
   must check critical dependencies deeply, but without a cascade (too shallow = failing over a healthy region; too deep = turning both off).
   The failover decision: automatic only for clearly defined signals; the rest manual, with a recorded decision owner.
6. **Static stability and the control plane.** During a region failure **do not rely on what the failure affects**: the resource
   creation API, the console, autoscaling, IAM/SSO, the image registry, CI, the runbook tool. Rules:
   - switch traffic through the **data plane** (e.g. routing controls in Route 53 ARC with the keys/endpoints recorded in the runbook), not through the console;
   - capacity in the second region/zone **pre-provisioned** (in AWS: static stability — surplus in every zone, 3+ zones),
     not bought during the failure (limits and lack of capacity in the target region when everyone does the same);
   - break-glass credentials and access work without depending on the primary region;
   - a provider's global resources often have a home region for the control plane — check the provider's documentation [unverified for your provider].
7. **Failover and failback runbooks.** Executable commands, the order (data → application → traffic), go/no-go criteria, decision
   time, communication. **Failback** is a separate, planned move: data resynchronization, stopping writes, verification, a change window.
   First restore redundancy after the failure, only then announce the end. Runbook from ops-sre-incidents / docs-tech-writing.
8. **DR tests and chaos.** The test plan grows gradually:

| Level | What | Frequency [example] |
|---|---|---|
| tabletop | walking through the runbook without changes | quarterly |
| restore | restoring a backup to an isolated environment with RTO/RPO measurement | quarterly, tier 0 more often |
| failover in staging | a full switchover in an environment close to production | every six months |
| game day in production | a switchover or a zone failure in a window, with observers | yearly / after a major change |
   A chaos experiment: a steady-state hypothesis, **a blast radius limit** (one zone, % of traffic, a selected tenant), stop conditions
   (the SLO drops below the threshold), a kill switch, the owner's consent and a change window. Result: measured RTO/RPO versus the target, gaps, tasks with a deadline.
9. **Evidence for the auditor** (ISO 27001/22301, DORA — sec-governance-compliance, sec-eu-regulations): the tier table with business approval,
   the test plan and test records with dates, measured RTO/RPO, open gaps with an owner, versioned runbooks. Untested = undeclared.
10. **Result** in `docs/project/`: sections "Tiers", "Strategy and data", "Traffic and dependencies", "DR test plan", "Risks and cost".

## Example
Input: "A shop: payments (RTO 15 min, RPO 1 min), catalogue (RTO 4 h, RPO 15 min), reports (RTO 24 h, RPO 24 h). One region."

Result (excerpt) [example, illustrative numbers]:

| Tier | Services | RTO / RPO | Strategy | Data | Traffic |
|---|---|---|---|---|---|
| 1 | payments | 15 min / 1 min | warm standby in a second region | an asynchronous replica, lag < 30 s with an alert; manual promotion after quorum | DNS with a low TTL + a data plane switch |
| 2 | catalogue | 4 h / 15 min | pilot light | asynchronous replication + cross-region objects | a script in the runbook |
| 3 | reports | 24 h / 24 h | backup and restore | a nightly backup outside the region, a restore test | no change |
Test: restoring the reports quarterly; payments failover in staging every six months; a payments game day with a 5% traffic limit and a stop on
an SLO drop. A gap to close: the image registry only in the primary region (a dependency during a failure).

## Checklist
- [ ] tiers with RTO/RPO approved by the business; dependencies not weaker than the service
- [ ] the failure scope separated (instance, zone, region, human error)
- [ ] DR strategy and cost per tier; replication lag measured and alerted on
- [ ] a conflict rule and split-brain protection for writes in many places
- [ ] failover through the data plane, capacity pre-provisioned, emergency access without the primary region
- [ ] failover and failback runbooks executable and tested
- [ ] a DR test plan with a blast radius limit and stop conditions; results with a date
- [ ] changes in production only with human consent in a change window

## Sources
- AWS, "Disaster Recovery of Workloads on AWS: Recovery in the Cloud" (AWS Well-Architected) — the four strategies; searched 2026-10-17, the page could not be fetched in the session, description from search results [unverified at the source].
- AWS Builders' Library, "Static stability using Availability Zones" (Weiss, Furr) — control and data plane, capacity surplus in 3+ zones; 2026-10-17.
- AWS Application Recovery Controller, "Data and control planes for routing control" and "Best practices for routing control" — switching through the data plane, TTL 60–120 s; 2026-10-17.
- AWS Well-Architected, REL11-BP05 (static stability) and REL13-BP02 (recovery strategies) — 2026-10-17.
The terminology is also used by other providers; the RTO/RPO thresholds per strategy come from providers and differ — they are not given as facts.
