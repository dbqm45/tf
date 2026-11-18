---
name: ops-release-engineering
description: Use for the release method — rolling, blue/green, canary with rollback, feature flags, database migrations in CD.
metadata:
  review: "2027-04-09"
  catalog: "Use for choosing and configuring the release method — rolling, blue/green, canary with metric gates and automatic rollback, feature flags with a removal date, GitOps (Argo CD, Flux), database migrations in CD (expand–contract), preview environments for PRs. Not for building the pipeline itself (ops-ci-cd) or trunk-based and DORA rules (eng-continuous-delivery)."
  keywords: "sposób wydania, wdrożenie stopniowe, canary, blue/green, rolling, wycofanie, rollback, feature flaga, za flagą, etapy flagi, etapy udostępniania, procent klientów, najpierw pracownicy, potem wszyscy, przejście etapu, kryterium wyjścia, release.yaml, data usunięcia flagi, dark launch, GitOps, Argo CD, Flux, expand contract, release method, progressive delivery, feature flag, behind a flag, flag stages, rollout stages, percentage of customers, employees first, then everyone, stage transition, exit criterion, flag removal date"
---

# Release engineering

Goal: a release is boring. Every change has a limited reach (blast radius), a measurable success criterion and a way
back that is faster than a fix.

## 1. Choosing a strategy
| Strategy | When | Notes |
|---|---|---|
| rolling | routine changes, stateless services, backward compatible | cheap; rollback is slow (another rolling) |
| blue/green | critical paths (payments, login), when an immediate return is needed | check the inactive environment **before** switching traffic; the cost of double infrastructure |
| canary | when staging does not reproduce production (traffic, data, integrations) | needs per-version metrics and an automatic decision |
| feature flag / dark launch | separating deployment from enabling a feature | every flag has an owner, a removal date and stages in `release.yaml` |
You choose by three questions: what risk we accept, how fast we must get back, how well we can verify the version.

## 2. Canary with gates
- A traffic ladder, e.g. 1–5% → 10% → 25% → 50% → 100%, with an observation time at every step (e.g. 10–15 minutes at the first).
- Gates from the metrics of the canary version against the stable one, e.g. error rate < 0.1% and p99 < 200 ms (you pick thresholds to fit
  the service's SLO — ops-sre-incidents). Exceeding them = **automatic** rollback, without waiting for a human.
- Tools: Argo Rollouts, Flagger (Kubernetes), traffic weights in the load balancer or service mesh. Mirrored traffic
  (shadowing) lets you check a version without affecting users.
- Measure, in addition to DORA: rollback frequency and the time from detection to rollback.

A flag has the same ladder as a canary, only by users: the stages (`internal` → `10%` → `100%`) recorded
in the release plan `release.yaml` (`flags[].rollout`), each with an exit criterion from metrics ("recovered ≥ 15%,
duplicates = 0") and a minimum time (`min_days`), plus `owner` and `remove_by`. A human approves the stage transition
when the criterion is met and the minimum time has passed — not "by feel".

## 3. GitOps
- The target state (manifests, image versions, configuration) in Git; a controller (Argo CD, Flux) reconciles the cluster with it
  and reverts manual changes (drift). Rollback = `git revert`.
- Policies (security, resources, compliance) checked in the PR before the change reaches the cluster. Low-risk changes
  may merge automatically, high-risk ones — with human approval.
- Promotion between environments through Git (a PR with the version change), not through a manual `kubectl apply`.
- Secrets not in plain form: SOPS, Sealed Secrets or an external manager (Vault, External Secrets).
- Decide early: one configuration repository or separate ones per team; what the dev → staging → prod path looks like.

## 4. Database migrations in continuous delivery
- **Expand–contract in separate releases:** (1) add the new column/table and write to both, (2) switch reads,
  (3) remove the old ones. Never a schema change and the application change that needs it in one deployment.
- Every migration works with **two** application versions at once (the old and the new run in parallel during the deployment)
  and is idempotent.
- In CI a DDL linter blocks table-locking operations (e.g. `CREATE INDEX` without `CONCURRENTLY` in PostgreSQL).
- Test migrations of large tables on production-sized data (be-database).

## 5. Preview environments
- An environment per PR: isolated, created automatically, with a mandatory lifetime and deletion when the PR is closed.
- Synthetic or masked data, separate secrets, no management ports from the internet.
- The performance test environment may be smaller than production, but created on demand, not permanent.

## 6. Configuration as part of the release
A release is code **and** configuration: flags, ConfigMaps, secrets, environment variables, the AI model version. You change them
in the same PR, promote them along the same path and roll them back together. An application without the required configuration does not report
readiness, so the release stops on its own (ops-kubernetes, section 4).

## 6a. Rollback rehearsed, not assumed
A rollback plan that nobody has executed usually fails exactly when it is needed.
- **Rehearse regularly** (e.g. once a quarter and after a pipeline change): a rollback on staging or in a canary, measuring
  the time from the decision to restoration.
- Conditions you check: the previous image **is still in the registry** (the retention policy does not delete the last N production
  releases — pinned by digest); database migrations compatible with the previous version (section 4); the pipeline can still deploy
  the old version; configuration and flags go back together with the code (section 6).
- Mark irreversible changes (dropping a column, a data migration, a message format change) in the PR — for them the way
  back is a fix forward or a restore from backup (ops-sre-incidents), which you must know **before** the release.

## 6b. An emergency change in production
A manual change is sometimes necessary in an incident, but without a record it creates drift: the next deployment reverts it or a new machine
does not get it.
- You make it deliberately: a record in the incident log (who, what, why), in GitOps — an explicit pause of self-healing for
  that resource, otherwise the tool reverts the change immediately.
- The same change goes into the repository (code, IaC, manifest) **within one working day**; then you resume
  synchronization. The rule: what exists in production exists in version control.
- Drift detection (GitOps) will catch forgotten changes anyway.

## 6c. The first deployment (sprint zero)
You do the MVP deployment right after the skeleton, not after the features — it is a cheap test of the platform and the whole path to production.
1. **Input:** the platform decision (stack-decision, ADR) and the stack. The plan in read-only mode, for approval.
2. **The plan contains:** automatic steps with an owner (agent / human); accounts and services to be created manually;
   a list of secrets (names and target location — without values); exact deployment commands for the chosen platform
   variant (variants of the same platform have different commands — check against the CLI version from the project); a final
   check (public address, logs, healthcheck).
3. **Before the deployment** the agent checks which account and project the CLI is logged in to (`whoami` / `auth status`
   of the given tool) and shows it to the human.
4. Save the approved plan in `docs/project/06-delivery/deploy-plan.md` — the answer to "what was supposed to happen" when
   the run goes off track, and the input to the next steps.
5. **During:** the agent does not take steps outside the plan (a deviation = stop and ask); a human enters the secrets;
   a human approves the production deployment (section 7).

## 7. The agent and releases
The agent prepares the change (manifest, rollout configuration, a PR in the GitOps repository) and a description of the gates. It does not promote
a version to production and does not disable automatic rollback without a human's consent.
It computes the release number and the `vX.Y.Z` tag according to SemVer with the script from core-semver. It does not overwrite a published tag or an image with a full version;
a fix is a new version.

## Example
**Situation:** a new ranking in `search-api`; staging has no real traffic, SLO: errors < 0.1%, p99 < 200 ms.
**Result:** a canary in Argo Rollouts, a PR in the GitOps repository, a human approves the promotion.
- Ladder: 5% (15 min) → 25% (10 min) → 50% (10 min) → 100%; background analysis from the first step.
- Gates from Prometheus for `track="canary"`: `result[0] < 0.001` (5xx) and `< 0.2` s (p99), `failureLimit: 2`.
- The third failed measurement = automatic rollback to the stable version, without waiting for the on-call engineer.
- The image pinned by digest, `revisionHistoryLimit: 5`; you measure the time from detection to rollback.

More examples: `references/examples.md`.

## Checklist
- [ ] strategy matched to the risk and the required speed of return
- [ ] canary gates from SLO thresholds and automatic rollback
- [ ] flags with an owner, a removal date and stages (exit criterion, minimum time) in `release.yaml`
- [ ] expand–contract migrations, compatible with two application versions, a DDL linter in CI
- [ ] preview environments with a lifetime
- [ ] first deployment: approved plan in the repo, CLI account checked, secrets entered by a human
- [ ] rollback rehearsed (time measured), previous images kept in the registry
- [ ] emergency changes reproduced in the repository, GitOps self-healing resumed

## Sources
- 10xDevs course, ed. 3 (2026), module 1, lesson 5 (the first deployment with an agent in planning mode) — training
  material (accessed 2026-10-09); described in our own words.
- [Mastering the Blast Radius: Progressive Delivery in Modern DevOps](https://devops.com/mastering-the-blast-radius-deployment-without-fear-progressive-delivery-in-modern-devops/)
- [Software Deployment Strategies for Enterprise Teams](https://devops.com/software-deployment-strategies-for-enterprise-teams-a-scenario-based-guide-to-choosing-the-right-approach/)
- [GitOps in 2026: Why Pull Requests Are Taking Over Cloud Operations](https://devops.com/gitops-in-2026-why-pull-requests-are-taking-over-cloud-operations/)
- [From Legacy to GitOps: A Roadmap for Enterprise Modernization](https://devops.com/from-legacy-to-gitops-a-roadmap-for-enterprise-modernization/)
- [Avoiding Database Migration Pitfalls with Continuous Software Delivery](https://devops.com/avoiding-database-migration-pitfalls-with-continuous-software-delivery/)
- [Ephemeral Environments are Better for Scaling Your Tests](https://devops.com/ephemeral-environments-are-better-for-scaling-your-tests/)
- [10 Minor DevOps Mistakes That Can Cause Major Production Issues](https://medium.com/coinmonks/10-minor-devops-mistakes-that-can-cause-major-production-issues-191d141e7686) — Pawan Natekar, 2026 (unrehearsed rollback, manual changes in production)
