---
name: ops-finops
description: Use for cloud costs — tags, cost in the PR (Infracost), budgets and alerts, clean-up, rightsizing, unit cost.
metadata:
  review: "2027-04-17"
  catalog: "Use when a change affects cloud costs or they need to be reduced — owner tags, cost in the PR (Infracost), budgets and alerts, cleaning up unused resources, rightsizing, cost policies as code, environment lifetime, unit cost. Not for just writing Terraform or the cost of telemetry (ops-observability)."
---

# FinOps for engineers

Cost is a quality attribute like performance: the decision about it is made in the PR, not at a quarterly review of the invoice.

## 1. Ownership
- Every resource has the tags `team`, `env`, `project` (and `expires` for temporary ones). A missing tag blocks the plan — a policy,
  not a wiki page.
- Costs visible per team and service; the team that creates a resource sees its bill.

## 2. Cost before deployment
- Infracost (or an equivalent) comments on every PR with Terraform/OpenTofu with the difference in monthly cost.
- Cost policies as code (OPA/Conftest, Sentinel) in layers: cheap defaults in modules and templates,
  a warning on risky choices, a hard block only for obvious waste (e.g. the most expensive instance
  classes outside production).
- Non-production environments: a list of allowed sizes, a mandatory lifetime (ops-release-engineering, section 5).

## 3. Budgets and anomalies
- Budgets per team and environment with alerts at 80%, 100% and 120%.
- The provider's cost anomaly detection (e.g. AWS Cost Anomaly Detection) with a notification to the owner.

## 4. Clean-up and rightsizing
A weekly review, the owner gets 7 days to object, then deletion:
- machines with CPU < 5% for 30 days, unattached disks, snapshots older than 90 days, load balancers without targets;
- resources used below 40% for 30 days — downsizing, unless the owner justifies the size.
In Kubernetes: resource requests from actual usage, not from headroom (ops-kubernetes); Kubecost or
OpenCost shows the cost per namespace.

## 5. Measures
Unit cost (per customer, per transaction, per deployment) and the waste rate say more than the invoice total —
a growing bill with growing traffic can be healthy.

## The agent and costs
The agent shows the cost difference in the description of an infrastructure change; it does not delete "unused" resources without the approval of
the owner and a human (deletion is an irreversible operation).

## Example
**Situation:** A Terraform PR enlarges `orders-db` and adds a database in `preview`; Infracost: +1,240 USD/month.
**Result** (a fragment of the PR description):
```text
| Resource          | Diff    | Notes                                    |
| orders-db (prod)  | +610    | CPU p95 = 85% for 3 weeks — justified    |
| orders-preview-db | +630    | WARN: class not on the list for env=preview |
Decision: preview → the smallest allowed class (+90), tag expires=2026-11-15; total +700 USD/month.
```
More examples: `references/examples.md`.

## Checklist
- [ ] owner tags enforced by a policy
- [ ] the cost difference in the PR
- [ ] budgets with alerts at 80/100/120%
- [ ] a weekly clean-up with an objection period
- [ ] unit cost tracked

## Sources (devops.com)
- [FinOps Meets DevOps: Engineering Cost Ownership in 2026](https://devops.com/finops-meets-devops-engineering-cost-ownership-in-2026/)
- [Policy as Code for Cost Control, Not Just Compliance](https://devops.com/policy-as-code-for-cost-control-not-just-compliance/)
