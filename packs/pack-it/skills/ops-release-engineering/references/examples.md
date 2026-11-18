# Release examples

> **Contents:** 1. A canary with gates in Argo Rollouts · 2. Renaming a column through expand–contract · 3. An emergency change with GitOps enabled

The numbers in the scenarios are illustrative; you always take gate thresholds from the given service's SLO (ops-sre-incidents).

## 1. A canary with gates in Argo Rollouts
**Situation:** "A new ranking in `search-api` passed staging, but staging has no real traffic and no full index.
We want to release without risk for all users". SLO: errors < 0.1%, p99 < 200 ms.

**How:**
1. Choosing the strategy (section 1): staging does not reproduce production → canary.
2. Ladder 5% → 25% → 50% → 100%, the longest observation at the first step (15 min).
3. Gates from the canary version's metrics, thresholds from the SLO; exceeding them = automatic rollback.
4. `revisionHistoryLimit` keeps the previous ReplicaSets, and the image is pinned by digest (section 6a).
5. The agent prepares a PR in the GitOps repository; a human approves the promotion to production (section 7).

**Result:** the plan and the manifests.

| Step | Traffic | Observation | Gate (canary) | When exceeded |
|---|---|---|---|---|
| 1 | 5% | 15 min | 5xx errors < 0.1%, p99 < 200 ms | automatic rollback to 0% |
| 2 | 25% | 10 min | as above | automatic rollback |
| 3 | 50% | 10 min | as above | automatic rollback |
| 4 | 100% | — | background analysis until the end of the rollout | — |

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: search-api
  namespace: search
spec:
  replicas: 10
  revisionHistoryLimit: 5
  selector:
    matchLabels:
      app: search-api
  template:
    metadata:
      labels:
        app: search-api
    spec:
      containers:
        - name: search-api
          image: registry.example.com/search-api@sha256:3f1c0d9e8b7a6f5e4d3c2b1a0f9e8d7c6b5a4f3e2d1c0b9a8f7e6d5c4b3a2f1e
          ports:
            - containerPort: 8080
  strategy:
    canary:
      canaryService: search-api-canary
      stableService: search-api-stable
      trafficRouting:
        nginx:
          stableIngress: search-api
      analysis:
        startingStep: 1
        templates:
          - templateName: search-api-slo
        args:
          - name: service
            value: search-api
      steps:
        - setWeight: 5
        - pause: {duration: 15m}
        - setWeight: 25
        - pause: {duration: 10m}
        - setWeight: 50
        - pause: {duration: 10m}
---
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: search-api-slo
  namespace: search
spec:
  args:
    - name: service
  metrics:
    - name: error-rate
      interval: 1m
      failureLimit: 2
      successCondition: result[0] < 0.001
      provider:
        prometheus:
          address: http://prometheus.monitoring.svc:9090
          query: |
            sum(rate(http_requests_total{service="{{args.service}}",track="canary",code=~"5.."}[5m]))
            /
            sum(rate(http_requests_total{service="{{args.service}}",track="canary"}[5m]))
    - name: p99-latency
      interval: 1m
      failureLimit: 2
      successCondition: result[0] < 0.2
      provider:
        prometheus:
          address: http://prometheus.monitoring.svc:9090
          query: |
            histogram_quantile(0.99, sum by (le) (
              rate(http_request_duration_seconds_bucket{service="{{args.service}}",track="canary"}[5m])))
```
In the PR description: "Gates: errors < 0.1%, p99 < 200 ms; three failed measurements = rollback. We measure the time from detection
to rollback".

## 2. Renaming a column through expand–contract
**Situation:** "Change `customers.phone` to `phone_e164` and add an index on the new column — in one PR, it will be faster".
The table has tens of millions of rows, the deployment is rolling (the old and new versions run together).

**How:**
1. Split it into three releases (section 4) — one PR would break the old application version during the rolling update.
2. Every migration idempotent and compatible with two application versions.
3. The index with `CONCURRENTLY`, because the DDL linter in CI blocks the table-locking version.
4. You test the backfill and the migration on production-sized data (be-database).
5. You mark release 3 in the PR as irreversible (section 6a).

**Result:** the release plan.

| Release | Schema | Application | Rollback |
|---|---|---|---|
| v2.14.0 (expand) | `ADD COLUMN IF NOT EXISTS phone_e164 text`; index `CONCURRENTLY`; backfill in batches of 10,000 rows | write to both columns, read from the old one | `git revert`, the column stays (harmless) |
| v2.15.0 (switch) | no changes | read from `phone_e164`, still write to both | revert to v2.14.0, data consistent |
| v2.16.0 (contract) | `DROP COLUMN IF EXISTS phone` | only `phone_e164` | **irreversible** — fix forward or backup |

```sql
-- V2_14_0__expand_phone_e164.sql
ALTER TABLE customers ADD COLUMN IF NOT EXISTS phone_e164 text;
CREATE INDEX CONCURRENTLY IF NOT EXISTS customers_phone_e164_idx ON customers (phone_e164);
```

## 3. An emergency change with GitOps enabled
**Situation:** an incident at 2:40 — `checkout-api` exhausts its database connection pool. The on-call engineer wants to raise
`DB_POOL_SIZE` from 20 to 40 right away through `kubectl edit`, and Argo CD has self-healing enabled.

**How:**
1. An entry in the incident log: who, what, why (section 6b).
2. Explicitly disable self-healing for this application only — otherwise Argo CD reverts the change after a few minutes.
3. The manual change, watching the pool metrics.
4. The same change as a PR in the configuration repository within one working day.
5. After the merge, restore self-healing; check that Argo CD shows no drift.

**Result:** the state of the Argo CD application during the incident and the timeline.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: checkout-api-prod
  namespace: argocd
spec:
  project: checkout
  source:
    repoURL: https://git.example.com/platform/gitops-config.git
    targetRevision: main
    path: apps/checkout-api/overlays/prod
  destination:
    server: https://kubernetes.default.svc
    namespace: checkout
  syncPolicy:
    automated:
      prune: true
      selfHeal: false  # INC-2291: paused for the emergency change, restore after the PR is merged
```

| Time | Action | Who |
|---|---|---|
| 02:45 | entry in INC-2291, `selfHeal: false` for `checkout-api-prod` | on-call engineer |
| 02:48 | `DB_POOL_SIZE=40` manually, errors return to normal | on-call engineer |
| 10:30 | PR "fix(checkout): DB_POOL_SIZE 40" in `gitops-config` | service owner |
| 11:15 | merge, `selfHeal: true`, no drift in Argo CD | service owner |
