---
name: ai-evals
description: Use for evaluating LLM features and agents — datasets, graders, an LLM judge, pass@k and pass^k, a CI gate, online evals.
metadata:
  review: "2027-04-17"
  catalog: "Use when you must measure the quality of an LLM feature or an agent, not just write the first test matrix — eval-driven development, dataset design (golden, regression, edge cases, adversarial, traffic samples, contamination), grader types (code, an LLM judge with a rubric and calibration to human ratings, human review), assessing an agent's outcome and trajectory, pass@k versus pass^k, offline and online evals (A/B, shadow), a CI gate with thresholds and a regression alert, eval cost and variance, the report format. Not for the basic promptfoo matrix, the output schema and loop limits (eng-llm-features), evals of Claude skills (core-skill-authoring) or code test oracles (qa-spec-first-testing)."
  keywords: "ewaluacje, evals, eval, zbiór testowy, golden set, sędzia llm, llm-as-a-judge, rubryka, kalibracja sędziego, zgodność z ludźmi, pass@k, pass^k, niespójny agent, trajektoria agenta, regresja jakości, bramka w ci, próg jakości, a/b test, shadow, ewaluacja online, kontaminacja, wariancja ewaluacji, raport z ewaluacji, jak mierzyć jakość agenta, czy wynik jest dobry, trafność systemu, klasa większościowa, punkt odniesienia, wyrocznia, ramię ślepe, wybór najlepszej konfiguracji, przetestowane konfiguracje, siatka parametrów, przetasowane etykiety, zaraportować wynik, ślady z produkcji, regresja ze śladów, dryf sędziego, evaluations, test set, llm judge, rubric, judge calibration, human agreement, inconsistent agent, agent trajectory, quality regression, ci gate, quality threshold, online evaluation, contamination, eval variance, eval report, how to measure agent quality, is the result good, system accuracy, majority class, baseline, oracle, blind arm, choosing the best configuration, tested configurations, parameter grid, shuffled labels, report the result, production traces, regression from traces, judge drift, drugi model ocenia odpowiedzi, model ocenia model, ocena od 1 do 5, czy można ufać sędziemu, a second model grades answers, model grading a model, 1-5 rating, can we trust the judge"
---

# Evaluating LLM features and agents

The basic matrix (cases × candidates, assertions, planted errors) comes from **eng-llm-features** §8; this skill starts
where the first matrix stops being enough: the datasets grow, the assessment is subjective, the agent is sometimes inconsistent, and the result must
block a merge.

## Procedure
1. **Start from failures, not from theory.** Write down 20–50 simple tasks from real errors (bug reports, the support
   queue, manual attempts). That is a good start; the dataset grows with every new failure. Each task: an input, a success
   criterion, a reference solution. Two experts should reach the same verdict — otherwise the task is unclear.
   The success criterion is specific, measurable, achievable and relevant (e.g. "F1 ≥ 0.85 on the test set", not "good
   quality"); soft traits (tone, consistency) you measure with a scale with described levels. More cases with automated grading
   give more than a few graded by hand.
2. **Dataset layers** (`references/datasets-and-graders.md`): *golden* (reference, small, checked by hand), *regression*
   (fixed bugs; expected approx. 100%), *edge* (empty, too long, ambiguous, in a foreign language),
   *adversarial* (injections, bypass attempts), *traffic samples* (anonymized, refreshed). For every
   behaviour add cases where it should occur **and** cases where it should not (otherwise you optimize one-sidedly).
3. **Contamination and leakage.** You do not paste the eval dataset into the prompt, the few-shot examples or the tuning
   data; examples for the prompt come from a separate pool. Public benchmarks may be in the model's data — for
   product decisions your own dataset is what counts.
4. **Choose the grader** (from the cheapest): code (exact match, a schema, a unit test, the state in the database) →
   an LLM judge (nuance, tone, factual consistency) → a human (calibration and samples). The rule: *deterministic where
   possible; an LLM where necessary; a human for validation*.
5. **An LLM judge — build and calibrate it.** A rubric with a description of every level, **one dimension per judge**, an option
   "unknown / not enough data", a different model than the generating one, the result in a fixed format, **reasoning before the score**
   (a judge with thinking turned on or a `reason` field before the verdict in the schema). Calibration: 30–50 examples
   rated by humans, you compute the agreement (the share of agreeing ratings or Cohen's kappa [set the threshold with the team]), you read the disagreements
   and fix the rubric. Without this the judge is an unknown instrument. After that the judge lives like code: agreement
   of reasoning (not only labels), a drift threshold from the human spread, a rubric change with a human's approval and a version to roll back to
   (`references/datasets-and-graders.md` §5–7).
6. **Agent: outcome or trajectory.** The basis is the **outcome** (the state of the environment after the run: the booking exists in
   the database, the tests pass), because rigidly checking the path penalizes correct, different solutions. The trajectory (tool
   calls, the number of steps, the cost) you check separately: limits, forbidden tools, failure diagnosis. For multi-step
   tasks award partial credit. Run every trial in a clean environment.
7. **Repeat trials and choose the metric.** An agent is non-deterministic, so `k` trials per task.
   **pass@k** = the chance of at least one success in k trials (grows with k; when one good
   solution is enough). **pass^k** = the chance that all k trials succeed (falls with k; when consistency matters, e.g. customer service).
   A 75% success rate per trial gives pass^3 ≈ 42%.
8. **Offline, then online.** Offline: the dataset before deployment, the gate. Online (after deployment): shadow (the new version
   computes in parallel, the user does not see it), A/B on part of the traffic with a business metric, samples for manual
   review, and new failures from traffic return to the dataset. The pattern and thresholds: `references/ci-and-traffic.md`.
9. **The CI gate.** A fast subset (smoke) on every PR, the full suite nightly or on a change of the model, the prompt, the tools.
   Set the threshold against **a baseline with its spread** (repeat the baseline 3–5 times), not "by eye"; a regression = a drop outside
   the noise interval. Change the threshold only deliberately, with a record. Details: `references/ci-and-traffic.md`.
   A ready tool (**run** it, do not rewrite it): `python3 .claude/skills/ai-evals/scripts/eval_gate.py baseline` computes
   the spread and the threshold from 3–5 runs of the current version (the team sets `--margin`), and `check` judges
   a candidate run: release / investigate / hold (exit code 1 blocks the merge; also on a failed regression task and on
   cost over `--budget-usd`). It reads results as JSON Lines and runs no model.
10. **Cost and variance.** Compute the cost of a run (cases × trials × candidates × judge) before launching it;
    a cheap model for triage, the full suite only on a change. 0% successes over many trials is usually a broken task or
    grader, not an incapable agent. Read the transcripts of failures — that is the fastest diagnosis.
11. **Interpret the result between bounds** (`references/measurement-pitfalls.md`): a constant majority class, a blind arm
    (without context), an oracle (the golden passage); arms with the same constants, one variable at a time. You choose the configuration
    on a selection set, you report the result from a held-out test; a control on shuffled labels.
    New grading rules you run on recorded traces (with the prompt and policy version), without re-running the agent.
12. **Report** in a fixed format (below), with a manifest of the model + harness pair. The readiness signal is the share of tasks
    passed in full, the mean of criteria only as diagnostics; a decision classifier you test by shuffling the options
    and with a per-decision threshold; an agent answering with numbers — by utility with a penalty (`references/measurement-pitfalls.md`
    §10–12). Saturation (the dataset passes ~100% and does not
    distinguish versions) → add harder tasks.

## Report format
```
Evaluation: <feature> | dataset: <name, N tasks, date> | candidate vs baseline: <model/prompt>
Metrics: success <x%> (baseline <y%>), pass^3 <..>, cost/run <..>, time <..>
Baseline spread: <min–max from n repetitions> | Verdict: release / hold / investigate
Regressions: <task → cause>; New failures for the dataset: <list>
```

## Example
**Input:** a refunds support agent, 40 tasks from the support queue, 4 repetitions, a result of 75% per trial.
**Result:**
- the outcome grader: code checks the order state in the test database (refund created, amount ≤ order);
  an LLM judge only for the tone of the answer, calibrated on 40 human ratings (agreement 85%, the rubric fixed once);
- pass^4 = 0.75⁴ ≈ 32% → too low consistency for the customer, despite the 75% average; pass@4 ≈ 99.6%;
- the baseline repeated 4 times: 72–78% → the regression threshold in CI is 68%, not 75%;
- the report: the verdict "hold", 3 new failures from transcripts added to the regression dataset.

## Checklist
- [ ] a starting dataset from real failures, the layers described, "should" and "should not occur" cases
- [ ] the dataset separated from the prompt and the examples (contamination)
- [ ] success criteria measurable; the cheapest possible grader; an LLM judge with a rubric, an "unknown" option, reasoning before the score and calibration to human ratings
- [ ] agent: outcome grading, the trajectory separately, a clean environment, k trials, pass@k or pass^k chosen
- [ ] a baseline with its spread; the CI threshold derived from it; smoke on PRs, the full suite periodically
- [ ] the cost computed before launching; the failure transcripts read
- [ ] failures outside the model (UI, session, tools, integrations, isolation, costs) in the test plan — qa-test-design
- [ ] the result between bounds (majority class, blind arm, oracle); the configuration chosen outside the test set
- [ ] online traffic (shadow, A/B) feeds the dataset; the report in a fixed format with a model + harness manifest

## Sources
- Anthropic Engineering, "Demystifying evals for AI agents" (2026-01-09, accessed 2026-10-17): task, trial, transcript,
  outcome; code, model and human graders; pass@k and pass^k (the example 75% → approx. 42% for 3 trials); 20–50 tasks from
  real failures; grading the outcome instead of the path; the "Unknown" option and a separate judge per dimension; saturation.
- Anthropic, "Create strong empirical evaluations / Define success criteria and build evaluations"
  (platform.claude.com/docs/en/test-and-evaluate/develop-tests, accessed 2026-10-20, an undated page): SMART criteria, task-specificity,
  automation, volume over the quality of a single case, edge cases, a different model as the judge, the judge's reasoning before the score.
- OpenAI, the evals guide (platform.openai.com/docs/guides/evals) — [unverified]: the page was unreachable
  from this environment on 2026-10-17; only the general principle "evals on every release" comes from it, without API details.
- F. Khan (2026-08-26), A. Punnen (2026-08-18), Netflix Tech Blog (2026-09-04, 2026-10), J. Wąsowski (2026-10-22) —
  measurement pitfalls, regression from traces, the judge lifecycle, the harness change gate; the authors' numbers [unverified].
- The kappa thresholds, the calibration sample size (30–50) and the "3–5 baseline repetitions" rule are the skill authors' practice [assumption].

Described in our own words.
