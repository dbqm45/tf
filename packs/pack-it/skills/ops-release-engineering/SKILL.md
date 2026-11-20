---
name: ops-release-engineering
description: Use when choosing how a change reaches production — canary or blue/green, flag stages, GitOps, expand-contract migrations, rollback, the first deploy plan.
metadata:
  review: "2027-11-20"
  catalog: "Use when choosing and configuring the release method — rolling, blue/green, canary with metric gates and automatic rollback (Argo Rollouts, Flagger), feature-flag stages in release.yaml, GitOps (Argo CD, Flux) and emergency changes under it, expand-contract database migrations, preview environments, configuration as part of a release, rehearsed rollback, the first (MVP) deployment with an approved plan. Not for building the pipeline itself (ops-ci-cd) or trunk-based development and DORA metrics (eng-continuous-delivery)."
  keywords: "canary, wdrożenie canary, blue green, rolling update, automatyczne wycofanie, rollback, wycofanie wdrożenia, progressive delivery, argo rollouts, flagger, bramki metryk, etapy flagi, flaga funkcji, feature flag, wdrożenie flagą, release.yaml, kryterium wyjścia, gitops, argo cd, flux, self-heal, zmiana awaryjna na produkcji, ręczna zmiana na produkcji, dryf konfiguracji, migracja bez przestoju, zmiana nazwy kolumny, expand contract, środowisko podglądowe, preview environment, środowisko per PR, próba wycofania, pierwsze wdrożenie, wdrożenie MVP, plan wdrożenia, deploy plan, jak wypuścić wersję, zero downtime deployment, release strategy, traffic shifting, rollback rehearsal, emergency change, first deployment, schema migration without downtime"
---

# Release engineering — how a change reaches users

Every release method buys three things: a **limited blast radius**, a **measurable success criterion** decided before the release,
and a **way back that is faster than a fix**. If one of the three is missing, the method is not finished.

## 1. Choosing the method
Ask three questions: how much risk is acceptable (payments ≠ an internal report), how fast must we be able to go back, and can we
verify the new version before it gets all traffic?

| Method | When | Cost / weakness |
|---|---|---|
| Rolling update | stateless services, low risk, backward-compatible changes | cheap; rollback is another rollout, so it is slow; old and new pods serve at the same time |
| Blue/green | you need an instant switch and a full check of the idle environment first | double capacity during the switch; shared database must suit both colours |
| Canary | staging differs from production, risk is high, per-version metrics exist | needs metrics split by version and an automated decision |
| Feature flag | separate *deploy* from *release*; target audiences | flag debt: every flag has an owner, stages and a removal date |

Usually you combine them: a canary deploy of the binary + a flag for the behaviour.

## 2. Progressive exposure
### 2a. Canary with metric gates
- Tooling: **Argo Rollouts** (Rollout + AnalysisTemplate) or **Flagger** (Canary resource with a service mesh or ingress).
- A ladder of traffic weights with observation windows, for example **1–5% → 10–25% → 50% → 100%**; the first windows are the longest,
  because that is where most problems show up (cold caches, a new query plan, a rare client).
- Gates compare canary to stable, not to an absolute number: **error rate** and **p99 latency** with thresholds derived from the SLO
  (e.g. error rate of the canary ≤ stable + 0.5 pp, p99 ≤ SLO target; ops-sre-incidents for SLOs). Thresholds are illustrative — derive yours.
- A gate breach means an **automatic rollback** to stable, no human needed at 2 a.m. A gate with no data (no traffic) is a failure, not a pass.
- Optional before the first step: mirrored (shadow) traffic, responses discarded.
- Measure the method itself: how often canaries roll back and the time from detection to completed rollback.

### 2b. Feature-flag stages in `release.yaml`
Stages by audience (internal → percent → everyone) with the same discipline as a canary: each stage has an **exit criterion** taken from
metrics and a **minimum time** (`min_days`), a human approves the move to the next stage, and the flag has an `owner` and a removal date
(`remove_by`). These keys are a factory convention read by core-delivery-lifecycle and eng-continuous-delivery — keep the names.

```yaml
flags:
  - key: payment-retry
    owner: team-payments            # decides on each stage transition
    remove_by: 2027-03-31           # the flag and the dead branch are deleted by then
    rollout:
      - { stage: internal, min_days: 3, exit: "retry success ≥ 95%, no double charge, 0 P1/P2" }
      - { stage: "10%",    min_days: 7, exit: "payment error rate ≤ control + 0.2 pp, support tickets not above baseline" }
      - { stage: "100%" }
```
A stage is never passed "on feel": no exit criterion met, or `min_days` not elapsed → stay, or roll back the flag.

## 3. GitOps
- The desired state lives in Git; a controller (Argo CD, Flux) reconciles the cluster and reverts drift (self-heal). Rollback = `git revert`.
- Policy checks (schema, OPA/Kyverno, image-from-allowed-registry) run on the PR; auto-merge only for low-risk changes (e.g. an image bump in dev).
- Promotion between environments is a PR (dev → staging → prod), not a manual sync.
- Secrets are never plain in Git: SOPS / Sealed Secrets or an external secret store (ops-secrets-identities).
- Decide the repository layout early (app code vs. config repo, a directory per environment); changing it later moves every application.

## 4. Database migrations: expand-contract
During a rolling update or a canary **two application versions run at the same time**. Each migration step must work with both.
1. **Expand** (release 1): add the new structure (column, table, index) without removing anything; the new code writes to both.
   Indexes on large PostgreSQL tables with `CREATE INDEX CONCURRENTLY` (outside a transaction block), backfill in batches.
2. **Migrate** (release 2): reads switch to the new structure; verify data parity.
3. **Contract** (release 3, after old versions are gone and rollback no longer needs them): remove the old structure.
- Each step is idempotent and rehearsed on production-sized data.
- A DDL linter in CI (for example squawk for PostgreSQL) blocks locking operations (`ALTER TABLE … RENAME`, adding a `NOT NULL`
  column with a volatile default, a non-concurrent index).
- Never "change the schema and the code in one deployment". Schema design itself: be-database.

## 5. Environments and configuration
### 5a. Preview environments
Created automatically per PR, deleted when the PR closes, plus a TTL as a safety net. Synthetic or masked data only, secrets separate
from staging/production, no management ports exposed to the internet. Cost: a cap on concurrent previews.

### 5b. Configuration is part of the release
Flags, ConfigMaps, environment variables and model versions change in **the same PR and through the same path** as the code,
and are rolled back together with it. A missing required configuration value fails the readiness probe instead of starting a half-working
pod (ops-kubernetes, section 4).

## 6. Rollback and changes on production
### 6a. Rollback — rehearsed, not assumed
- Rehearse on a schedule (e.g. quarterly) and after every pipeline change: deploy N, roll back to N−1, measure the time.
- Conditions: previous images kept in the registry by digest (retention policy does not delete them), migrations compatible with N−1,
  the pipeline can still deploy the old version, flags and config revert with it.
- Label **irreversible changes** in the PR (dropping a column, a data migration, a changed event format on a queue) and write down the
  way forward (fix-forward, a backup restore path, ops-sre-incidents) before the release, not during the incident.

### 6b. Emergency change on production under GitOps
1. Log who, what, why and when (incident channel or ticket).
2. Pause reconciliation **for that one application only**: Argo CD — turn off automated sync/self-heal for the Application;
   Flux — `flux suspend kustomization <name>` (or `helmrelease`). Never disable the controller globally.
3. Make the change; confirm the effect.
4. Reproduce it in the repository as a PR within one working day; after merge, resume sync (`flux resume …` / self-heal back on)
   and check that the controller reports no drift. Drift detection is the safety net for forgotten steps.

### 6c. First deployment (MVP) — with an approved plan
Do it as soon as the walking skeleton exists, not at the end.
1. Read the stack decision (`docs/project/04-architecture/stack-decision.md`, the platform section; arch-tech-selection).
2. Write a **read-only plan** to `docs/project/06-delivery/deploy-plan.md` and get it approved before any command runs. Per step:
   the owner (human or agent), the exact CLI command for the chosen platform variant, the manual account/console steps,
   the **names** of required secrets (never values) and the final checks (health URL, logs, rollback command).
3. Before the first mutating command show the human which account the CLI login is using: `gh auth status`, `aws sts get-caller-identity`,
   `gcloud auth list`, `az account show`, `vercel whoami`, `fly auth whoami`… Wrong account → stop.
4. The human enters secrets into the platform's secret store and approves the production step; the agent executes only the plan's steps.
   Anything off-plan → stop, update the plan, ask again.
5. Afterwards: the plan marked done with the actual URL and version; the release number and the `vX.Y.Z` tag from core-semver's script
   (`.claude/skills/core-semver/scripts/semver.py`) — never move or overwrite a published tag.

## 7. The agent's boundary
The agent prepares manifests, rollout and analysis definitions, migration PRs and gates, and runs read-only checks. It does **not** promote
to production, skip a canary stage or disable automatic rollback without a human's explicit consent — "the canary keeps failing,
just turn off the rollback" is a reason to look at the metrics, not to remove the gate.

## Example
Request: "Rename `customer.fullname` to `display_name` in a 40 M-row PostgreSQL table; the app ships by rolling update."

Result:
- R1 (expand): `ALTER TABLE customer ADD COLUMN display_name text;` — the app writes both columns, reads the old one; batch backfill
  of 10k rows; `CREATE INDEX CONCURRENTLY` if needed. Old and new pods both work.
- R2 (migrate): reads switch to `display_name`; a parity check query returns 0 differences.
- R3 (contract, after R2 is stable and N−1 rollback is no longer needed): `ALTER TABLE customer DROP COLUMN fullname;` — marked
  **irreversible**, restore path = backup from before R3.
- CI: squawk blocks a direct `RENAME COLUMN`.

More in `references/examples.md`: 1. a canary with gates in Argo Rollouts · 2. renaming a column through expand-contract ·
3. an emergency change with GitOps enabled.

## Related skills
ops-ci-cd (the pipeline that builds the artifact) · eng-continuous-delivery (trunk-based, DORA) · ops-kubernetes ·
ops-sre-incidents (SLOs, restore) · be-database · core-semver · core-delivery-lifecycle.

## Sources
- Argo Rollouts documentation: canary strategy, analysis and automated rollback (argo-rollouts.readthedocs.io), as of 2026-11.
- Flagger documentation: canary analysis with metric checks (docs.flagger.app), as of 2026-11.
- Argo CD documentation: automated sync policy and self-heal (argo-cd.readthedocs.io); Flux documentation: `flux suspend` /
  `flux resume` (fluxcd.io), as of 2026-11.
- PostgreSQL documentation: `CREATE INDEX`, section "Building Indexes Concurrently" (postgresql.org/docs), as of 2026-11.
- Kubernetes documentation: Deployments — rolling update and rollback (kubernetes.io), as of 2026-11.
- squawk — PostgreSQL migration linter (squawkhq.com), tool documentation, as of 2026-11.
