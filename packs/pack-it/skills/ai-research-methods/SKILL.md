---
name: ai-research-methods
description: Use for researching and validating an ML model — baseline, data leakage (random, temporal, group split), offline vs post-deployment result, seeds, metrics, report.
metadata:
  review: "2027-04-17"
  catalog: "Use when you need to go from an AI/ML research question or hypothesis to a result that can be defended — framing the problem and a strong simple baseline, experiment design (controlled variables, ablations, seeds, mean ± spread, caution with multiple comparisons), data splits and leakage (temporal, group, test-set hygiene, benchmark contamination), a metric aligned with the decision, a compute budget and scaling from a pilot, reproducibility (configuration, code, data versions, environment), a literature review and critical reading of papers, from a paper to a product prototype, offline→online validation, a research report with negative results and limitations, an ethical review of the data; artifact docs/project/02-domain/experiment-NAME.md. Not for evaluating LLM features and agents (ai-evals), general statistics and product experiments (data-analysis), fine-tuning a model (ai-fine-tuning), experiment tracking tools and the registry (ai-mlops) or searching for facts on the web (core-source-research)."
  keywords: "badania ML, research scientist, applied scientist, hipoteza, eksperyment ML, baseline, ablacja, seedy, wariancja między uruchomieniami, średnia i odchylenie, czy nowy model jest lepszy, wyciek danych, data leakage, podział czasowy, podział grupowy, zbiór testowy, kontaminacja benchmarku, dobór metryki, pilotaż, skalowanie eksperymentu, reprodukowalność, powtarzalność wyników, przegląd literatury, czytanie artykułów, replikacja, z artykułu do produktu, offline online, raport z badania, wyniki negatywne, metoda nie zadziałała, nie poprawiła wyniku, jak zapisać badanie, metoda z artykułu, ograniczenia badania, etyka danych, model zastępczy, surrogate model, symulator, algorytm genetyczny, optymalizacja na modelu, najlepszy projekt wg modelu, rejestr hipotez, wracamy do tych samych pomysłów, claude science, literatura naukowa, bazy naukowe, publikacje z chemii lub biologii, doi, notatnik do odtworzenia wyniku, ML research, hypothesis, ML experiment, ablation, seeds, variance between runs, mean and deviation, is the new model better, temporal split, group split, test set, benchmark contamination, metric choice, pilot, scaling an experiment, reproducibility, repeatability of results, literature review, reading papers, replication, from paper to product, research report, negative results, the method did not work, did not improve the result, how to write up a study, method from a paper, study limitations, data ethics, simulator, genetic algorithm, optimization on a model, best design according to the model, hypothesis register, we keep coming back to the same ideas, scientific literature, scientific databases, chemistry or biology publications, notebook to reproduce a result"
---

# AI/ML research — from a hypothesis to a result that will hold up

The result "model B is better" has value only when someone else can repeat it and point to what undermines it.
The skill guides you through the whole research cycle. It leaves its neighbours their tasks: evaluating LLM features and agents (**ai-evals**),
statistics and product A/B tests (**data-analysis**, `.claude/skills/data-analysis/references/statistics.md`,
`.claude/skills/data-analysis/references/advanced-experiments.md`), fine-tuning (**ai-fine-tuning**), experiment
tracking tools (**ai-mlops**) and researching facts on the web (**core-source-research**).

## Procedure
1. **Question and decision.** Write the hypothesis in a falsifiable way ("adding feature X raises PR-AUC by ≥ 1 pt on data from
   quarter Q"), the decision the result will change, and the failure criterion. Without a failure criterion every result "shows something".
2. **Literature before code** (`references/literature-and-prototype.md`). Check whether someone has already done it and whether
   the result was replicated. A paper's finding = claim + evidence + conditions. Collect facts from the web per **core-source-research**.
   A project with knowledge from outside computer science (biology, chemistry, medicine, materials): the review in Claude Science or domain
   databases is run by a human; what comes back to the repo is a record of the evidence with a DOI, version, access date and a reproducible notebook
   (`references/literature-and-prototype.md`).
3. **A strong simple baseline first.** A rule, logistic regression, a tree, the last value, the most frequent class
   or the existing system. A tuned baseline (as many trials as the candidate) is a fair reference point; a candidate
   beating a weak baseline proves nothing. If a simple model is enough for the decision, the study ends here.
4. **Data split and leakage — before the first training** (`references/leakage-and-splits.md`). The split follows from
   how the model will be used: the future does not influence the past (temporal split), the same unit (customer,
   patient, document) does not land on both sides (group split). Preprocessing (scaling, imputation,
   feature selection, encoding) is fitted on the training set only. **The test set is looked at once**, at the end; tuning is done
   on validation. A test set used for selection is already a validation set.
5. **A metric aligned with the decision.** The metric follows from the cost of errors and the way of use (precision@k with a limited
   number of interventions, calibration with thresholds, the cost of a false alarm), not from what a benchmark reports.
   One primary metric fixed **before** the experiment, the rest auxiliary; results in subgroups, not only the mean.
6. **Experiment design.** You change one thing at a time; the data, splits, tuning budget and metric are identical
   for all variants. **Ablations**: remove the elements of the new method one at a time and show which one brings the gain.
   Also check a negative control (e.g. shuffled labels — the result must drop to random; if it does not, there is leakage).
7. **Seeds and variance.** A single run is one sample from a distribution. Repeat each variant on ≥ 5 seeds
   [assumption — the number depends on the spread; start with 5 and increase when the intervals overlap] and report
   **mean ± deviation (or a confidence interval)**, recording what varied: initialization, data order,
   split, hyperparameters. The sources of variability also include the choice of the data split, not only the seed
   (Bouthillier et al. 2021). Treat a difference smaller than the spread as inconclusive.
8. **Significance and multiple comparisons.** Compare **paired** (the same split and the same examples): a paired
   test, a bootstrap of the difference, McNemar for classification. Give the effect size and an interval, not only p. With
   many variants, metrics or datasets, correct for the number of comparisons (Bonferroni, Holm) or call them exploratory;
   the number of tuning trials and of "peeks" at the results goes into the report. Choosing the test: Dror et al. 2018;
   the calculation: **data-analysis**.
9. **Compute budget and scaling.** Before a large run, compute the cost (GPU-hours × variants × seeds).
   A pilot on a small model or a subset: does the pipeline work, does the metric respond, what is the spread. Do not carry conclusions from
   a small scale over to a large one without checking the trend on 2–3 sizes [assumption — the ranking of methods is often unstable].
10. **Reproducibility.** For every run record: the code commit, the configuration (hyperparameters, seeds), the version
    and hash of the data and the split, the environment (libraries, hardware), the run command. Tracking and the registry
    (MLflow, DVC) are **ai-mlops**. Checklist: `references/report-and-template.md`.
11. **From a paper and a result to a product** (`references/literature-and-prototype.md`). A prototype on your own data, not on the
    benchmark; offline validation (historical data, temporal split), then online (shadow, A/B — **data-analysis**
    and **ai-evals**, step 8). The offline↔online difference is a result: record it and its cause.
12. **Data ethics.** Before use, check the origin and licence of the data, consents, personal and special-category data
    (**arch-privacy-compliance**), representativeness and the risk of harm to groups; benchmark contamination and misuse.
12a. **A surrogate model in an optimization loop and a hypothesis register** — optimization on a model searches out its errors,
    so you check the winner with the real simulator or an experiment and report both numbers; hypotheses as a graph
    with verdicts and a condition for reopening (`references/optimization-and-hypotheses.md`).
13. **Report** `docs/project/02-domain/experiment-<name>.md` per `references/report-and-template.md`: hypothesis, method,
    results with spread, **negative results**, limitations, decision. A negative result is valuable:
    it saves the next people from dead ends, but only when the conditions under which it was obtained are described.

## Example
[example — illustrative numbers, not from a measurement]
**Input:** a customer churn model, baseline: logistic regression, PR-AUC 0.41; a new gradient boosting
with 14 temporal features gives 0.46 in one run with a random 80/20 split (several rows per customer).
**Result:**
- the split changed to temporal + group (training: months 1–9, test: 10–12, a customer on one side only);
  the baseline drops to 0.34, the new model to 0.37 — the earlier result was inflated by leakage;
- 5 seeds × 2 splits: baseline 0.34 ± 0.01, new 0.37 ± 0.02; difference 0.03, the bootstrap interval of the paired
  difference [0.01; 0.05] — there is an improvement, but smaller than the claimed 5 pts;
- ablation: 11 of the 14 features add nothing; three features "number of contacts with support" give the whole gain;
- 12 variants were compared → Bonferroni threshold 0.05/12 ≈ 0.004; the effect is still clear for the variant with three features;
- report `experiment-churn-gb.md`: verdict "shadow pilot", limitation "data from one country", negative result
  "the remaining 11 features have no effect".

## Checklist
- [ ] a falsifiable hypothesis, the failure criterion and the decision recorded before the experiment
- [ ] literature checked, papers' claims distinguished from evidence
- [ ] a strong simple baseline with the same tuning budget
- [ ] temporal/group split, preprocessing fitted on training only, test set used once
- [ ] primary metric aligned with the decision chosen before the results; results in subgroups
- [ ] ablations and a negative control; one thing changed at a time
- [ ] ≥ 5 seeds, mean ± spread, paired comparison, correction for multiple comparisons
- [ ] compute budget calculated, a pilot before a large run
- [ ] commit, configuration, data version and environment recorded
- [ ] data ethics and licences checked; a report with negative results and limitations

## Sources
- Bouthillier et al., "Accounting for Variance in Machine Learning Benchmarks", MLSys 2021 (arXiv 2103.03098,
  accessed 2026-10-17): variability from data sampling, initialization and hyperparameter choice is underestimated;
  recommendations for comparing.
- Pineau et al., "Improving Reproducibility in Machine Learning Research", JMLR 22(164), 2021 (arXiv 2003.12206,
  accessed 2026-10-17): the NeurIPS 2019 reproducibility programme with a checklist, a code policy and a replication challenge.
  Content of the checklist items: [unverified] in this environment.
- Kapoor, Narayanan, "Leakage and the reproducibility crisis in machine-learning-based science", Patterns 4(9),
  2023 (accessed 2026-10-17): leakage in 17 fields and 294 papers, eight types of leakage.
- Henderson et al., "Deep Reinforcement Learning That Matters", AAAI 2018 (accessed 2026-10-17): the result depends on
  seeds and the number of trials, a conclusion about significance tests and honest reporting.
- Dror et al., "The Hitchhiker’s Guide to Testing Statistical Significance in NLP", ACL 2018 (accessed 2026-10-17):
  a protocol for choosing a significance test; a review of ACL/TACL 2017 showed tests being omitted or misused.
- The number of 5 seeds, the pilot thresholds and carrying conclusions across scale are the skill authors' practice [assumption].

Described in our own words.
