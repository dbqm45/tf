---
name: ai-mlops
description: Use for the life cycle of an ML or LLM model in production — registry, features, training in a pipeline, deployment, drift, prompts (MLOps, LLMOps).
metadata:
  review: "2027-04-17"
  catalog: "Use when a machine learning model or an LLM feature has to move from a notebook into maintained production — the MLOps maturity level (Google 0–2), experiment tracking (MLflow), data versioning (DVC, lakeFS), a model registry with aliases and promotion gates, a feature store (Feast) and training-serving skew, choosing a training orchestrator (Kubeflow Pipelines, Airflow, Dagster), continuous training, data tests and model quality gates (also fairness), model deployment (shadow, canary, A/B, rollback), monitoring (data and concept drift, quality with delayed labels, latency, cost), reproducibility, the model card, LLMOps (prompt registry, evaluations in CI, tracing, cost per request, guardrail metrics); the result is an MLOps pipeline design or a readiness list. Not for data pipelines alone (data-engineering), general CI/CD (ops-ci-cd) and release strategy (ops-release-engineering), general monitoring (ops-observability), hosting models on GPUs (ops-ai-inference), evaluation methods (ai-evals) or choosing a statistical model (data-analysis)."
  keywords: "mlops, llmops, model w produkcji, wdrożenie modelu, notebook do produkcji, MLflow, rejestr modeli, model registry, feature store, Feast, training-serving skew, DVC, lakeFS, wersjonowanie danych, retraining, dotrenowanie modelu, continuous training, drift, data drift, concept drift, opóźnione etykiety, shadow deployment, canary modelu, karta modelu, model card, reprodukowalność, Kubeflow, Dagster, prompt registry, wersjonowanie promptów, zmiana promptu w produkcji, regresja po zmianie promptu, rachunek za tokeny, koszt na zapytanie, tracing LLM, guardrails, model in production, model deployment, notebook to production, data versioning, model fine-tuning, delayed labels, model canary, reproducibility, prompt versioning, prompt change in production, regression after a prompt change, token bill, cost per request, LLM tracing"
---

# MLOps and LLMOps — from a notebook to maintained production

A model is code, data and parameters at once, and it breaks without a code change (the data changed). The skill leads from
the maturity level to a pipeline design: what to version, what to test, what to monitor and when to retrain.
Do not build more than the risk level and the frequency of changes require.

## Procedure
1. **Context.** Establish: the kind (classic ML or LLM), the cost of an error, how often the data changes, **how late
   the label arrives** (hours or 90 days), who maintains the model. Record missing answers as assumptions.
2. **Maturity level** (the Google model; the source in Sources). Choose a target, not the highest one:

   | Level | Feature | Enough when |
   |---|---|---|
   | 0 — manual | a notebook, manual handover of the model for deployment | the model changes rarely, an error is cheap |
   | 1 — training pipeline | an automated pipeline, data and model validation, continuous training, a registry | the data changes, retraining every week/month |
   | 2 — pipeline CI/CD | tests and builds of the pipeline in CI, automatic deployment of the pipeline and the model | many models or teams, frequent code changes |

   The first step from a notebook to a pipeline is **data validation before training** (schema, ranges, the distribution relative to
   the previous version); without it continuous training automatically trains the model on broken data.
3. **Experiments and reproducibility.** Every run records: parameters, metrics, **the data hash**, the commit,
   the environment (a lockfile or an image), random seeds, the feature version. Test: will you reproduce the model in 6 months
   from the record alone? MLflow Tracking is the standard; the choice of tool matters less than the completeness of the record (lineage).
4. **Data versioning.** DVC — data and the pipeline (`dvc.yaml`, `dvc.lock`) next to the code in the repo, any object
   store; lakeFS — branches and commits on the whole data lake without copying. Data already in tables with time
   travel (Iceberg, Delta) → record the snapshot identifier instead of a separate tool. Data pipelines: data-engineering.
5. **Registry and promotion.** A model version in the registry points to the run, the data, the metrics and the model card. Mark promotion
   with **aliases** (`champion`, `challenger`), not stages — in MLflow stages have been deprecated since 2.9. Promotion is
   a gate (step 8), not a manual click. The code loads the model by alias, so a rollback = moving the alias.
6. **Features and skew.** Training-serving skew arises when a feature is computed differently offline and online, or when
   training "sees the future". Two ways: a feature store (Feast: consistent definitions, a **point-in-time** historical
   read, an online store) or one transformation library used in both places. A feature store
   pays off from ~a few models sharing features, or online with fresh features. **Skew test:** for a sample
   of entities and timestamps compare the online features with the offline ones; too large a difference blocks the deployment.
7. **Training orchestration** (general orchestration rules — data-engineering). Choose by criteria:
   - Kubeflow Pipelines — Kubernetes is already there, steps as containers, GPUs, many teams; the cost: maintaining the cluster;
   - Airflow — the orchestrator is already running, training is one of many flows, scheduling and integrations;
   - Dagster — the model as a data asset with lineage and partitions, an emphasis on local testability;
   - a cloud service (Vertex AI Pipelines, SageMaker), when the cloud is settled and you do not want to maintain a platform.
8. **Model CI/CD/CT** (the pipeline mechanics — ops-ci-cd). Four layers of tests:
   - code: unit tests of transformations and loss functions;
   - **data:** schema, ranges, missing values, the distribution relative to a reference; under a data contract;
   - **model (quality gate):** a metric no worse than `champion` by an agreed margin, **on slices** (segments,
     rare classes), not only on average; latency and size; **fairness** — differences in metrics between groups below
     a threshold agreed with the business and a lawyer;
   - integration: the serving contract (input, output, feature version).

   Continuous training triggers: a schedule, new data, a drift alert — each with a frequency and cost limit.
9. **Model deployment** (the mechanics — ops-release-engineering; serving — ops-ai-inference). The specifics:
   **shadow** (the new model computes in parallel, without affecting the result — you compare predictions and latency) → **canary**
   (a small fraction of traffic with a metric gate) → **A/B** (when a business metric matters; compute the power and duration
   up front). Rollback: the alias to the previous version; check that the old features are still available.
10. **Monitoring** (general metrics and alerts — ops-observability). The layers above them:
    - **feature drift** (PSI, the Kolmogorov–Smirnov test, the Jensen–Shannon distance) and data quality (missing values, new categories);
    - **prediction drift** (the distribution of scores or classes) — works without labels;
    - **quality with delayed labels:** a metric computed on mature cohorts (e.g. the cohort from 90 days ago)
      plus proxy indicators (prediction drift, the share of low confidence); an alert on labels instead of on yesterday's data is late;
    - **concept drift** (the dependence of the target on the features changed) shows only in the labels or in an experiment;
    - latency, errors and cost per prediction.

    Every alert has an action: retrain, roll back or investigate; treat PSI thresholds as a starting point for calibration.
11. **Documentation.** The model card (purpose, data, metrics on slices, limitations, risks, owner,
    review date) goes into the registry together with the version. Legal requirements — arch-privacy-compliance.
12. **LLMOps.** Differences from classic ML:
    - **the prompt as an artifact:** a registry with versions and aliases, a change through a PR, not a live edit;
    - **an evaluation set in CI** run on a change of the prompt, the model, the parameters and the tools (the method, the judge,
      the choice of cases — ai-evals); a change of the model version at the provider is a release change;
    - **tracing** of every request (steps, tools, tokens, latency) and evaluating a sample of production traffic with the same evaluations;
    - **cost per request** = input and output tokens × the price list, broken down by feature; a budget and an alert;
    - **guardrail metrics:** the share of refusals, detected personal data, prompt injection attempts,
      answers not grounded in sources. Application code with an LLM — eng-llm-features.

## Result
An "MLOps pipeline design" document (`docs/project/…`): the target level, a diagram of the stages, a table of
artifacts (what, where, who), gates with thresholds, a monitoring plan with an action per alert, gaps and the deployment order.
Template and readiness list: `references/design-and-readiness.md`.

## Example
Input: "A churn model, trained in a notebook, deployed manually every quarter; the label comes after 90 days."
Result (excerpt): level 0 → target 1 (not 2: one model, one team). Data in DVC (`dvc.lock` in the repo), runs
in MLflow with the data hash, a registry with the `champion` alias. Airflow is already running → the `train_churn` pipeline once a month.
Gate: AUC ≥ champion − 0.005 and AUC in the "new customers" segment ≥ 0.70; the recall difference between age groups
≤ 5 pp. Deployment: shadow for 7 days, then canary 10%. Daily monitoring: feature PSI (>0.25 = alert), score drift;
weekly quality on the cohort from 90 days ago. A drift alert → a human's decision, not automatic retraining.

## Checklist
- [ ] the current and target level justified; the label delay recorded
- [ ] a reproducible run: data (hash), code (commit), environment, seeds, features
- [ ] a registry with aliases; promotion only through a gate; rollback = an alias change
- [ ] a skew test and point-in-time for features; no future leakage
- [ ] gates: data, quality on slices, fairness, latency; CT triggers with a cost limit
- [ ] shadow or canary deployment with a rollback criterion; A/B with computed power
- [ ] monitoring: feature and prediction drift, quality on mature cohorts, cost; an alert has an action
- [ ] the model card in the registry; LLM: versioned prompts, evaluations in CI, tracing, cost per request

## Additional materials
- `references/design-and-readiness.md` — a pipeline design document template, a readiness list and criteria for choosing tools.

## Sources
- Google Cloud Architecture Center, "MLOps: Continuous delivery and automation pipelines in machine learning" — levels 0–2;
  the primary page could not be fetched, the description of the levels is confirmed only in secondary sources, accessed 2026-10-17 [unverified].
- MLflow: registry stages deprecated in favour of aliases since 2.9 (RFC `mlflow/mlflow#10336`, the `FutureWarning` message);
  MLflow 3 — LoggedModel, tracing, the prompt registry, `mlflow.genai.evaluate()` (docs 3.1.3 and 3.5.x), accessed 2026-10-17;
  whether stages were removed in the current release — [unverified].
- DVC: `dvc.yaml`, `dvc.lock`, any object store; lakeFS as a layer over a data lake (DVC documentation
  and comparisons, accessed 2026-10-17); the acquisition of DVC by lakeFS (2025) — a single source [unverified].
- Feast: point-in-time historical read, offline and online store (documentation, versions 0.x, accessed 2026-10-17);
  the number of the current release [unverified].
- Evidently, Arize: monitoring without labels through feature and prediction drift (documentation, accessed 2026-10-17).
- Mitchell et al., "Model Cards for Model Reporting" (2019) — the model card [unverified in this session].
- The PSI thresholds 0.1 and 0.25 are a rule of thumb from credit scoring [unverified].
