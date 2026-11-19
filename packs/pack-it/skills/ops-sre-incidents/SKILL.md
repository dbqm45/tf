---
name: ops-sre-incidents
description: Use for reliability and incidents — SLI/SLO, error budget, burn rate, on-call, postmortems, backups.
metadata:
  review: "2027-04-17"
  catalog: "Use for service reliability and incidents — SLI, SLO and SLA, the error budget and its policy, burn rate alerts, on-call, severity levels, incident command, blameless postmortems, toil, designing for failure, chaos engineering, autonomy levels of AI agents in operations. Not for instrumentation and dashboards (ops-observability) or release strategy (ops-release-engineering)."
---

# SRE and incident handling

## 1. SLI → SLO → SLA
Three levels, each answers a different question:

| Level | Question | What it is | Example |
|---|---|---|---|
| **SLI** (indicator) | what do we measure? | a metric: the ratio of good events to all valid ones | the share of `GET /orders` requests without a 5xx error and faster than 300 ms |
| **SLO** (objective) | what value of the indicator is enough for us? | SLI + threshold + time window | 99.9% of such requests in a 30-day window |
| **SLA** (agreement) | what happens when we miss the objective? | SLO + consequences (e.g. a partial refund of the fee in credits) | 99.5% monthly, below that — a 10% credit |
- You usually sign an SLA with an external customer and the business is responsible for it together with the legal department; inside the company SLOs are enough.
  **The SLO is stricter than the SLA** — the difference is the buffer in which the team reacts before the company pays.
- Never 100%: every dependency (the network, the cloud, the user's browser) has its own unreliability, and the last "nines" are
  expensive and slow down changes.
- "Availability" needs a definition of an outage (e.g. an error rate ≥ 10% in a minute = the service is unavailable). Describe latency
  with percentiles (p95, p99), not the average.
- How to choose an SLI, write the specification, compute the budget and the composite availability of dependencies: `references/sli-slo-sla.md`.

## 2. SLOs from the user's side
- You define an SLO per **user journey**, not per service: e.g. payment and sign-up 99.95–99.99%,
  login p99 < 200 ms, auxiliary features 95–99%. The indicator (SLI) measures what the user sees (the share of successful
  requests, latency), not CPU usage.
- AI-based features have three SLO layers with separate budgets: infrastructure (availability, latency), inference
  (time to first token, the share of fallback responses) and behavior (stability and correctness of results). You set thresholds for
  behavior from production data in a rolling window — there is no industry standard yet.

## 3. The error budget and alerts
- Budget = 100% − SLO (for 99.9% over 30 days that is about 43 minutes). **A budget policy** written down in advance: what we do when
  the budget runs out (e.g. pausing feature releases in favor of reliability work, a mandatory change review).
- Alerts on the budget burn rate in two windows at once, thresholds per the Google SRE Workbook; a fast burn
  wakes the on-call person, a slow one creates a ticket without waking anyone.
- An alert that has not required any action for 90 days — you remove it or move it to a channel without notifications.

## 4. On-call
- A weekly rotation: a primary and a secondary on-call person; a 30-minute handover with a note in the team channel.
- The goal: at most 2–3 incidents requiring action per shift. Measure the number of alerts per shift, the distribution of the load
  between people and the recurrence of incidents. On-call is paid or compensated with time off.
- With teams in several time zones: follow-the-sun instead of night-time wake-ups.

## 5. The incident
| Level | Example | Response |
|---|---|---|
| SEV1 | a critical service unavailable, data loss, a security incident | an incident commander (IC), an incident channel, updates every 30 min, escalation to management |
| SEV2 | significant degradation, some users | IC, updates every hour |
| SEV3 | a minor problem, a workaround exists | a ticket in the team backlog |
- The IC coordinates and decides, does not fix things alone; separate roles: communication, change operator, timeline scribe.
- First mitigation (rollback, failover, turning off a flag), only then the cause.
- A security, credential or personal data incident: immediately the security team and the rules from core-agent-security
  (no "cleaning up" before evidence is preserved); conditions for notifying the legal department agreed in advance.
- You report the time to restore (MTTR) in phases: detection, acknowledgement, diagnosis, decision, fix, verification —
  then you can see where we lose time.

A security incident (an attack, a leak, a compromised account) has additional steps — preserving evidence against
changes, containment without revealing the detection, GDPR (RODO)/NIS2 notifications: ops-security-operations.

## 6. After the incident
- A blameless postmortem: the question "how did the process allow this?", not "who missed it?". A draft with the timeline,
  the customer impact and links to logs, metrics and traces prepared before the meeting.
- Corrective actions that are concrete, with an owner and a deadline, tracked in the backlog until closed.
- Every incident caused by a bug in the code leaves **a regression test** (red before the fix — eng-debugging),
  and when agents write the code, also **a permanent agent evaluation scenario**: the task that led to the bug,
  with the expected behavior. You run the scenario set on changes to `CLAUDE.md`, skills, hooks and the model
  (`.claude/skills/core-delivery-lifecycle/references/ai-native-sdlc.md`).
- The metrics the incident exposed (e.g. the 5xx rate, PR cycle time) go under control bands with response levels
  (`core-delivery-lifecycle/scripts/control_band.py`); SLO alerts stay on burn rate (section 3).
- Also review "near misses" and outages that passed on their own: a short description (the trigger, the first signal, the smallest
  change that would have prevented it).
- Template and record: docs-tech-writing (runbook, postmortem), decisions in the project log.

## 7. Toil and runbooks
- Operational work at most about 50% of the team's time; a runbook step done by hand several times goes to the automation
  backlog.
- A runbook that is current and executable (commands, not prose); outdated runbooks block any automation, AI included.

## 8. Designing for failure
- Define a **degraded mode** in advance: what we turn off, delay or simplify when a dependency fails; show it
  in the UI and on the dashboard.
- Failure isolation: bulkheads (separate connection and thread pools per dependency or client), limiting inflow
  (backpressure) instead of an avalanche of retries, circuit breakers, timeouts on every call.
- Chaos engineering gradually: first the steady state (metrics), then fault injection in CI (delays, 429,
  5xx — e.g. WireMock), then canary, finally production.

- **Backups count only after a restore.** For every data store: RPO (how much data may be lost)
  and RTO (how long a restore may take), a copy outside the production account and region, at least one immutable copy (protection
  against ransomware and mistakes), **a regular restore test** with time measurement and an alert when a backup did not run.
- **Single points of failure**: once a quarter a list of components whose failure stops the whole service (one database without
  a replica, one NAT, one DNS provider, one signing key, one person with access); for each a decision —
  redundancy, a degraded mode or a consciously accepted risk.
- **A capacity review** before an expected growth (a campaign, a new customer, a season) and periodically: a load test
  on the forecast traffic, not on today's; a system good for 1,000 users does not have to work for 100,000.

## 9. AI agents in operations
| Level | When | Rules |
|---|---|---|
| 1. autonomously | the alert matches a tested runbook, the resource is on the allowlist, the action is reversible and idempotent, the result can be checked with a metric | limits (e.g. scaling within min/max), a gap between actions, automatic escalation when verification fails |
| 2. with human approval | several possible causes, impact on users | explicit approval, for exactly this command and target, expiring after a few minutes; no answer ≠ approval |
| 3. human-led | cascading failures, security, credentials, the database schema, money | the IC decides; the agent only reads and collects evidence |
The decision about the level is made by a policy outside the language model. The agent has its own identity with separated read and write,
a kill switch, a limit of actions per hour, and every step (trigger, decision, action, effect) goes to the audit
log. First shadow mode (the agent proposes, a human executes), then gradual expansion. Preconditions:
current runbooks, mature SLOs and an owner for incidents caused by the agent itself.

## Checklist
- [ ] SLIs defined as a ratio of good events; SLOs per user journey, stricter than the SLA
- [ ] a written error budget policy
- [ ] burn rate alerts in two windows; alerts without actions removed
- [ ] severity levels, the IC role and an update template
- [ ] a blameless postmortem with actions tracked until closed
- [ ] a degraded mode, timeouts, circuit breakers; chaos in CI
- [ ] an AI agent in operations only at the level from the policy, with an audit log and a kill switch

## Sources
devops.com: [Why Your SLO Dashboard is Lying](https://devops.com/why-your-slo-dashboard-is-lying-moving-beyond-vanity-metrics-in-production/),
[So Agentic Systems Are Messing Up Your SLO Framework](https://devops.com/so-agentic-systems-are-messing-up-your-slo-framework/),
[On-Call Rotation Best Practices](https://devops.com/on-call-rotation-best-practices-reducing-burnout-and-improving-response/),
[The Power of Blameless Postmortems](https://devops.com/from-incidents-to-insights-the-power-of-blameless-postmortems/),
[Designing for Failure: 4 Resilience Practices](https://devops.com/designing-for-failure-4-resilience-practices-that-make-outages-boring/),
[Chaos Engineering for APIs](https://devops.com/chaos-engineering-for-apis-integrate-failure-testing-into-your-ci-cd-pipeline/),
[The Three Tiers of Agentic Incident Response](https://devops.com/the-three-tiers-of-agentic-incident-response-when-to-trust-ai-autonomy/),
[Before You Go Agentic: Guardrails for AI Agents in Observability](https://devops.com/before-you-go-agentic-top-guardrails-to-safely-deploy-ai-agents-in-observability/),
[The AIRE Gap](https://devops.com/the-aire-gap-why-organizations-are-buying-ai-sre-tools-they-arent-ready-to-use/).
Burn rate thresholds: [Google SRE Workbook — Alerting on SLOs](https://sre.google/workbook/alerting-on-slos/).
SLI/SLO/SLA: [Service Level Objectives (SLI, SLO, SLA) Explained Simply](https://froehlich.medium.com/service-level-objectives-sli-slo-sla-explained-simply-fb4b91dd4a07) (Steve Froehlich),
[Google SRE Book — Service Level Objectives](https://sre.google/sre-book/service-level-objectives/).
The severity levels and update frequency are an example convention — adapt them to the organization.
- [10 Minor DevOps Mistakes That Can Cause Major Production Issues](https://medium.com/coinmonks/10-minor-devops-mistakes-that-can-cause-major-production-issues-191d141e7686) — Pawan Natekar, 2026 (backups and restore, single points of failure, capacity)
