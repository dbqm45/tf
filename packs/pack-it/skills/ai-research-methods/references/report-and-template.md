# Research report and reproducibility checklist

## Template `docs/project/02-domain/experiment-<name>.md`
```
# Experiment: <name> | author | date | status: planned / in progress / finished

TL;DR: <the result in 2 sentences, the spread, the decision>
Handoff: <next step, owner>

## Hypothesis and decision
Hypothesis (falsifiable): ...  Failure criterion: ...  Decision the result will change: ...
## Data
Source, licence, consents, period, size, version/hash, split (temporal/group), known gaps.
## Method
Baseline (and its tuning budget), candidate, ablations, primary metric (chosen before), auxiliary ones.
## Results
Table: variant | primary metric: mean ± deviation (n seeds) | difference vs baseline [interval] | cost.
Results in subgroups. Number of comparisons and the correction applied.
## Negative results
What did not work, under what conditions (configuration, scale), how many trials.
## Limitations and threats to validity
Internal (leakage, tuning), external (does it generalize to another period, country, scale), what was not checked.
## Ethics
Personal data, representativeness, risk of applications.
## Reproducibility
Commit, configuration, seeds, data version, environment, command, compute cost.
## Decision and next steps
release a pilot / investigate further / abandon + justification.
```
Principle: the report also describes what did not work and gives the conditions. A conclusion is as strong as the weakest link
(a small spread, one scale, one dataset) — write this down explicitly.

## Reproducibility checklist
Close to the checklist of the NeurIPS 2019 reproducibility programme (Pineau et al., JMLR 2021) and to the conferences'
checklists; check the details of the items in the current conference form [unverified].
- [ ] code with a commit (or an attachment), instructions to run with one command
- [ ] all hyperparameters and search ranges, the way the best ones were chosen
- [ ] seeds, number of runs, the way the spread is computed
- [ ] data: source, version, hash, split, processing steps, explanation of exclusions
- [ ] environment: library versions (lockfile), hardware, compute time and cost
- [ ] a result with an interval or a deviation, not a single point; the test used for comparisons
- [ ] determinism: what is non-deterministic (GPU, order) and how large a spread it gives
- [ ] raw results of the runs saved next to the summary table

## Negative results and failures
Record the hypothesis, the configuration, the result with the spread, hypotheses about the cause (marked as unverified) and what
was not tried. Do not write "the method does not work", but "in this configuration, on this data, no effect above noise".
