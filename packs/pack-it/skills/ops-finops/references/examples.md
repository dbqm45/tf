# FinOps examples

The amounts and names in the examples are illustrative — in real work they come from Infracost, the provider's cost report
and utilization metrics.

## 1. Cost in a PR with a database change
**Situation:** A Terraform PR enlarges the `orders-db` database and adds the `orders-preview` environment. Infracost
commented on the difference, and a Conftest policy raised a warning.

**How:**
1. Read the monthly cost difference from the Infracost comment and break it down by resource.
2. Check the tags `team`, `env`, `project` and `expires` on temporary resources — a missing tag blocks the plan.
3. Distinguish the policy layers: a warning (a risky choice) from a block (obvious waste outside production).
4. Put the cost difference and the justification in the PR description.

**Result:** a fragment of the PR description
```text
Cost (Infracost): +1,240 USD/month

| Resource                    | Before | After | Diff    | Notes                                  |
|-----------------------------|--------|-------|---------|----------------------------------------|
| orders-db (prod)            | 610    | 1,220 | +610    | a 2× larger class; CPU p95 = 85% for 3 weeks |
| orders-preview-db (preview) | 0      | 630   | +630    | a production class outside production  |

Policy: WARN orders-preview-db — class not on the allowed list for env=preview
Decision: preview changed to the smallest allowed class (+90 instead of +630),
          tag expires=2026-11-15; new difference: +700 USD/month
```
```hcl
tags = {
  team    = "orders"
  env     = "preview"
  project = "checkout"
  expires = "2026-11-15"
}
```

## 2. A weekly clean-up review
**Situation:** "Agent, prepare a list of things to delete from the dev account — the bill is growing."

**How:**
1. Collect candidates by thresholds: CPU < 5% for 30 days, unattached disks, snapshots older than 90 days, load
   balancers without targets; separately resources used below 40% (to downsize).
2. Assign the owner from the `team` tag; a resource without a tag goes to the platform team.
3. Send the list to the owners with a 7-day objection deadline.
4. Do not delete anything — the deletion is done by a human after the deadline passes.

**Result:**
```text
Review 2026-10-05 (dev account) — objections until 2026-10-12

| Resource            | Criterion               | Cost/month  | Owner      | Proposal        |
|---------------------|-------------------------|-------------|------------|-----------------|
| vm-batch-old-2      | CPU 1.8% for 30 days    | 140 USD     | data       | delete          |
| vol-0a91 (200 GiB)  | unattached for 41 days  | 16 USD      | no tag     | delete          |
| snap-ci-* (37 items)| older than 90 days      | 52 USD      | platform   | delete          |
| lb-legacy-api       | no targets              | 18 USD      | orders     | delete          |
| vm-search-1         | CPU 22%, memory 31%     | 280 USD     | search     | halve the size  |

Potential savings: 226 USD/month (deletions) + about 140 USD/month (downsizing)
Agent: no deletions; waiting for the owners' decision and a human's approval.
```

## 3. A growing bill and unit cost
**Situation:** The budget of the `payments` team exceeded the 100% threshold, the manager asks whether this is waste.

**How:**
1. Put the cost next to a business measure (transactions) — the bill alone does not answer the question.
2. Compute the unit cost month over month.
3. When the unit cost is flat, the growth is healthy; when it grows, look for anomalies and resources to clean up.
4. Propose a budget correction or corrective actions, with alerts at 80/100/120%.

**Result:**
```text
| Month     | Cost [USD]  | Transactions | USD / 1000 transactions |
|-----------|-------------|--------------|-------------------------|
| July      | 8,000       | 4.0 million  | 2.00                    |
| August    | 9,100       | 4.6 million  | 1.98                    |
| September | 11,900      | 4.8 million  | 2.48  ← +25%            |

Conclusion: July→August is healthy growth (flat unit cost). In September the unit cost
jumped by 25% with +4% traffic — an anomaly: a load-testing cluster without the expires
tag has been running since 3.09 (about 2,600 USD). Action: the owner confirms the shutdown, a policy
requires expires for env=perf; the budget unchanged.
```
