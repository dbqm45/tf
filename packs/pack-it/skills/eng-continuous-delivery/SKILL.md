---
name: eng-continuous-delivery
description: Use for the way of delivering — trunk-based, small batches, CI/CD, DORA metrics, Twelve-Factor.
metadata:
  review: "2027-10-17"
  catalog: "Use for decisions about the way of delivering — trunk-based development, small batches, feature flags, continuous integration and delivery, DORA metrics, the Twelve-Factor App principles, \"shift left\" security. Not for configuring specific CI tools (ops-ci-cd) or everyday git (core-git-workflow)."
---

# Continuous delivery

## Practices
- **Trunk-based development**: short-lived branches (≤ 1–2 days) or commits straight to main with pair review;
  integration at least daily. Long feature branches = a hidden integration risk.
- **Small batches**: a small PR is easier to review, deploy and roll back. A large change → a series of steps, each deployable.
- **Feature flags** separate deployment from release; every flag has an owner and a removal date.
  The rollout stages (internal → percentage → 100%), each with an exit criterion and a minimum time, you record
  in the release plan `release.yaml` (`flags[].rollout`, `remove_by`), not only in the release description — then it is possible to
  check whether the release is going according to plan and when the flag should disappear.
- **The main branch always deployable**: we fix a red build before new work.
- **Branch by abstraction / expand–contract** for large changes and data migrations (be-database).
- **Shift left**: tests, static analysis, dependency and secret scanning in the pipeline, not before the release.
- **Blameless postmortems**; the conclusions as tasks.

## DORA metrics (at the application/service level)
| Group | Metric | Definition |
|---|---|---|
| throughput | change lead time | from the commit to production |
| throughput | deployment frequency | the number of deployments in a period |
| throughput | failed deployment recovery time | the time to fix a deployment that requires intervention |
| instability | change failure rate | deployments requiring immediate intervention (rollback, hotfix) |
| instability | deployment rework rate | unplanned deployments resulting from incidents |

Speed and stability go together, they are not a trade-off. The metrics are for learning, **not targets** (Goodhart's law);
compare the system with itself over time, not teams with each other.

### The delivery health dashboard (also with AI agents)
- **Lagging indicators** hold you to account: the change failure rate, the rate of defects reaching users, the rework rate,
  the realization of the return on investment.
- **A leading indicator** goes onto the dashboard only when it predicts one of the lagging ones: the queue of PRs waiting
  for human review (the number, the age of the oldest) → failed changes; specification drift (the code diverges from the spec) →
  defects reaching users; the time since a template or rule was last checked against reality → rework.
- Every speed measure is paired with a quality measure that will move when someone starts gaming the first. You measure the system,
  never a person.
- Three views: the board quarterly (lagging, return), management monthly (trends of both kinds), the team lead
  weekly (the full leading set with the pairs). Start from four numbers: the review queue, specification drift,
  the change failure rate, defects reaching users — you agree the definitions of "defect" and "escape" before the first measurement.
Source: J. Wąsowski, "SDD Factory Dashboard…" (2026-08-12).

## Twelve-Factor (summary)
One codebase, explicit dependencies, configuration in the environment, backing services as attached resources, separated
build/release/run, stateless processes, port binding, scaling with processes, fast startup and graceful shutdown,
environment parity, logs as an event stream, admin tasks as one-off processes.

## Example
**Situation:** the branch `feature/new-checkout` has lived for 3 weeks, 74 files, conflicts on every rebase.
**Result:** a series of 5 deployable PRs: (1) the interface `CheckoutFlow` over the old cart (branch by abstraction),
(2) `CheckoutFlowV2` behind the flag `checkout-v2` (owner, removal date, off by default), (3) the *expand* migration,
(4) the flag for the internal team, (5) turning it on for everyone and *contract* — removing the old code and the flag.
From then on branches ≤ 1–2 days and daily integration.
More examples: `references/examples.md`.
