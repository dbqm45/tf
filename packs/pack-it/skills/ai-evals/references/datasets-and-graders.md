# Datasets and graders

Contents: 1. Dataset layers · 2. Sourcing tasks · 3. Contamination · 4. Choosing a grader · 5. The LLM judge · 6. Calibration ·
7. The judge lifecycle · 8. Pitfalls

## 1. Dataset layers
| Layer | Contents | Expected result | Refresh |
|---|---|---|---|
| golden | 20–50 tasks with a reference solution, checked by hand | grows with quality | on a change of requirements |
| regression | every fixed bug as a task | close to 100% | you add one after every fix |
| edge | empty input, too long, ambiguous, foreign language, missing data | depends on the case | on new discoveries |
| adversarial | a prompt injection in the data, an attempt to bypass the rules | refusal or ignoring | from security reviews |
| traffic samples | anonymized, random and from negative signals | monitor the trend | weekly or monthly |

Evals with a low initial score (*capability*) are a "hill to climb"; once they reach a high score,
they move to the regression ones.

## 2. Sourcing tasks
- Sources: manual attempts, the bug tracker, the support queue, human-rated answers from production.
- An unambiguous task: two experts give the same verdict; there is a reference solution. 0% successes over many
  trials usually means an error in the task or the grader.
- Traffic data: RODO (the Polish name for the GDPR) — anonymization, a legal basis, retention (arch-privacy-compliance).

## 3. Contamination
- The eval dataset does not go into the prompt, the few-shot examples, the tuning data or a public repository.
- Take examples for the prompt from a separate pool; once an example is included in the prompt, exclude it from the dataset.
- A public benchmark may have ended up in the model's data; a result on it does not replace your own dataset.
- Symptom: the score jumps after adding examples similar to the dataset, but does not grow on fresh traffic samples.

## 4. Choosing a grader
| Type | When | Advantages | Drawbacks |
|---|---|---|---|
| code | format, an exact answer, tests, environment state | fast, cheap, repeatable | brittle, does not assess nuance |
| LLM judge | tone, factual consistency, completeness, summaries | flexible, scalable | non-deterministic, costly, needs calibration |
| human | calibration, a disputed case, a sample audit | the quality reference | expensive, slow |

A task's result can be binary (all graders must pass), weighted or mixed. A grader resistant to gaming:
passing requires actually solving the task, not meeting the letter of the check.

## 5. The LLM judge
- Rubric: a separate description of every level of the scale with an example; numbers without a description produce noise.
- One dimension per judge (tone, facts, completeness separately), then aggregation in code.
- The judge sees the input, the answer and the criterion; it does not see the candidate's name or the order (randomize positions in pairwise comparisons).
- The result in a fixed format (JSON: `reasoning`, `score`), reasoning before the score; an "unknown" option.
- A different model than the generating one (bias towards its own answers) [an assumption from practice; the Anthropic docs recommend a different model].
- A low judge temperature; one judge version pinned to the dataset, because changing the judge changes all results.

## 6. Calibration
1. 30–50 answers of varying quality; two humans rate them independently [the size is practice, not a rule].
2. Compute the agreement of the humans with each other (the ceiling) and of the judge with the humans: the share of agreeing ratings or Cohen's kappa.
3. Read the disagreements; typical causes: an unclear rubric, a too strict or too lenient judge, two dimensions in one.
4. Fix the rubric, repeat. Stop when the judge agrees with the humans almost as well as the humans agree with each other.
5. Come back periodically: a production sample for manual rating every week or month detects judge drift.

## 7. The judge lifecycle
Calibrating once at the start is not enough. The judge is a versioned component with an owner.
1. **Agreement of reasoning, not only of labels.** "A right label, a wrong reason" you detect by comparing the judge's reasoning
   with the human's reasoning (a meta-judge, checked first on human ratings). Tuning the rubric only on labels
   can silently break one criterion.
2. Every "bad" label in the golden dataset has a written human justification.
3. One judge per criterion; aggregation in code.
4. **The judge as a gate and a critic:** the reason for a rejection returns to the generator, with a limit of revisions (e.g. 3). After the limit
   "do not show" instead of "show a weak one".
5. **A drift threshold against the human spread:** the judge is no worse than the raters' mean minus 2 standard deviations,
   on a fixed, stratified weekly sample.
6. **A rubric change** only after a human's approval. The rubric and the judge have versions, and the previous version can be
   restored immediately (rollback).
7. Human review also catches gaps in the rubric itself (cases it does not describe), not only judge drift.
8. A judge is admitted only where it agrees with the humans as often as the humans agree with each other. You never tune it on
   the golden dataset you assess it on. The golden dataset and the evals are owned by the team: they are what lets you safely
   change the model to a cheaper one.

Source: the Netflix Tech Blog on grading with LLM judges (2026-09-04, the arXiv paper 2608.18300 [unverified]); the
"2 deviations" threshold and the limit of 3 revisions are the authors' examples, not a rule.

## 8. Pitfalls
- The mean from one run treated as the truth (variance).
- A judge rating longer answers higher (length bias) — add to the rubric that length is not a virtue.
- Changing the dataset and the model at once — it is unknown what changed the result.
- Evaluating only the happy path.
- A result without reference points (majority class, blind arm, oracle) and choosing the configuration on the test
  set — `measurement-pitfalls.md`.
