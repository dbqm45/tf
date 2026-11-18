# MLOps pipeline design and a readiness list

Contents: Document template · Production readiness list · Criteria for choosing tools · Common pitfalls

## Document template
```markdown
# MLOps pipeline design — <model>
Owner: … · Review date: … · Level: current X → target Y (reason)

## 1. Context
The business goal, the cost of an error, the label delay, the frequency of data changes, legal requirements.

## 2. Artifacts
| Artifact | Where | Versioning | Owner |
|---|---|---|---|
| training data | … | hash / snapshot | … |
| features | … | definition in the repo | … |
| model | registry | version + alias | … |
| model card | registry | with the version | … |

## 3. Pipeline and triggers
Stages (data → validation → training → evaluation → registration), the orchestrator and the justification of the choice,
CT triggers with a frequency and cost limit.

## 4. Gates
| Gate | Condition | Effect of failing |
|---|---|---|

## 5. Deployment and rollback
Shadow → canary → full; the rollback criterion; who decides.

## 6. Monitoring
| Signal | Frequency | Threshold | Action |
|---|---|---|---|

## 7. Gaps and the deployment order
```

## Production readiness list
Answers: yes / no / not applicable (with a reason). Every "no" goes into section 7 with an owner.

**Reproducibility**
- Can you reproduce the model from the run record: data, code, environment, seeds, features?
- Do the training and serving environments have pinned library versions?

**Data and features**
- Are the schema and the data distributions checked before training?
- Do the features have one definition for training and serving, and a skew test?
- Is the historical read point-in-time (no future leakage)?

**Model**
- Is there a baseline (a simple model or a rule) and a metric on slices?
- Has fairness been checked for the groups relevant to the use case?
- Does the model card have the purpose, the limitations and the owner?

**Deployment**
- Is rollback a single step, and has it been rehearsed?
- Did the new model go through shadow or canary before full traffic?

**Monitoring**
- Is there feature and prediction drift, and quality on mature cohorts?
- Does every alert have an action and an owner?
- Is the cost per prediction (or per LLM request) measured, and does it have a budget?

**LLM (additionally)**
- Are the prompts in a registry with versions, and does a change go through a PR and the evaluation set?
- Does tracing cover tokens, tools and latency, and is a sample of traffic evaluated?
- Are there guardrail metrics (refusals, personal data, injections, answers not grounded in sources)?

## Criteria for choosing tools
| Decision | Choose | When |
|---|---|---|
| data versioning | DVC | one project, data in an object store, a pipeline next to the code is needed |
| | lakeFS | many teams on a shared lake, branches and atomic commits on large data |
| | table snapshot (Iceberg, Delta) | the data is already in such tables |
| feature store | Feast | features shared by models, online read, point-in-time needed |
| | a shared library | one model, features computed in batch |
| orchestration | Kubeflow Pipelines | Kubernetes is there, steps in containers, GPUs |
| | Airflow | the orchestrator is already running in the organization |
| | Dagster | the model as a data asset, lineage, local tests |
| tracking | MLflow | a registry, LLM tracing and evaluations are needed in one place; another tool when the platform imposes it |

The overriding rule: a tool the team already maintains beats a better tool to be deployed from scratch,
unless it lacks a required feature (e.g. point-in-time).

## Common pitfalls
- The offline metric rises and the production one falls — usually feature skew or future leakage in the training set.
- Automatic retraining on drifted data without a gate entrenches the error; retraining always goes through a gate.
- Quality computed on "yesterday's data" with the label after 90 days says nothing — use mature cohorts.
- An average metric hides a deterioration in a segment; the gate has slices.
- Changing the LLM model version at the provider without running the evaluation set.
