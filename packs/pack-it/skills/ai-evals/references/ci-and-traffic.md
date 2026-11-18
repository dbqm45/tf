# The CI gate and evals on traffic

Contents: 1. The CI gate · 2. Thresholds from the spread · 3. Cost · 4. Offline versus online · 5. Report format · 6. Agent

## 1. The CI gate
| Suite | When | Size | Goal |
|---|---|---|---|
| smoke | every PR | 10–20 tasks, a cheap judge model | catch obvious regressions |
| regression | every PR changing the prompt, the tools, the schema | the whole regression dataset | no fixed bug comes back |
| full | nightly, before a release, on a model change | all layers, k trials | the release decision |

A change of the model, the harness version, the prompt, a tool description or the schema triggers the full suite. The same model in a different
harness gives different results, so after a swap you measure from scratch.

## 2. Thresholds from the spread
1. Run the baseline (the current version) n = 3–5 times [practice]; record the minimum, the maximum, the mean.
2. The absolute threshold = the lower bound of the spread minus a margin agreed with the team (not a round number "by eye").
3. A regression = a drop against the baseline outside the spread; with small datasets compute a confidence interval or use a test on
   pairs of tasks (data-analysis).
4. Regression tasks: a threshold close to 100%, every flipped task is red.
5. Loosening a threshold is a decision with a record (who, why, until when), not an edit of a number in the config.
6. Alert: a metric drop in CI or online above the threshold → a ticket to the owner; the weekly trend in the report.

## 3. Cost
Cost = tasks × trials × candidates × (generation + judge). Compute it before launching. Savings: a cheap model
for the judge after calibration, caching the fixed prefix (core-cost-control), smoke instead of the full suite, parallelism
without increasing the number of trials. Variance is reduced by repetitions, not by longer judge prompts.

## 4. Offline versus online
- **Offline:** repeatable, cheap, before deployment. It will not see the distribution of real users.
- **Shadow:** the new version processes the same traffic in the background, you compare its results with the current one; the user does not see them.
  Good for high-risk changes.
- **A/B:** part of the traffic gets the new version; a business metric (resolved cases, conversion, escalations) and guardrail
  metrics (cost, time, complaints). The duration and sample size from data-analysis.
- **Traffic samples:** random and from negative signals (thumbs down, a retry, an escalation) for manual rating; new
  failures return to the regression dataset.
- Telemetry and production alerts: ops-observability.

## 5. Report format (full version)
```
Evaluation: <feature> | date | commit/prompt version | model + harness
Dataset: <layers, N, version> | k trials: <k> | judge: <version, agreement with humans>
Result: success <x% [min–max]> vs baseline <y% [min–max]> | pass^k <..> | pass@k <..>
Cost: <USD/run>, time p50/p95 | Trajectory limits: steps <..>, forbidden tools <0>
Regressions: a list of tasks with a link to the transcript | New failures for the dataset: a list
Verdict: release / hold / investigate — the justification in 1–2 sentences
```

## 6. Agent
- A clean environment for every trial (no shared state, no leaks between trials).
- Outcome: the final state; trajectory: step and cost limits, forbidden tools, loops.
- A human reads the failure transcripts at least for a sample — this also checks the grader's honesty.
