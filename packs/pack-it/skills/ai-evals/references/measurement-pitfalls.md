# Measurement pitfalls and regression from traces

> **Contents:** 1. Bounds of the result · 2. One variable at a time · 3. Configuration selection and the test · 4. The label and the component metric · 5. Invariants · 6. The model + harness pair manifest · 7. Regression from traces · 8. Rules as the regression floor · 9. The harness change gate · 10. The report and choosing the oracle · 11. A decision classifier (an LLM as a classifier) · 12. Utility with a penalty (an agent answering with numbers)

> **Table of contents:** 1. Bounds of the result · 2. One variable at a time · 3. Configuration selection and the test · 4. The label and the component metric · 5. Invariants · 6. The model + harness pair manifest · 7. Regression from traces · 8. Rules as the regression floor · 9. The harness change gate · 10. The report and choosing the oracle · 11. A decision classifier (an LLM as a classifier) · 12. Utility with a penalty (an agent answering with numbers)

Contents: 1. Bounds of the result · 2. One variable at a time · 3. Configuration selection and the test · 4. The label and the component metric ·
5. Invariants · 6. The model + harness pair manifest · 7. Regression from traces · 8. Rules as the floor · 9. The harness change gate ·
10. The report and choosing the oracle · 11. A decision classifier · 12. Utility with a penalty (an agent answering with numbers)

Silent measurement errors *improve* a metric more often than they hurt it, so you check a good result the same way as a bad one.

## 1. Bounds of the result
A system's result can be interpreted only when you know three reference points computed on the same dataset:
- **a constant majority class** — the model always answers "yes" (or with the most frequent label). 72% accuracy with 70%
  of "yes" answers in the dataset is almost nothing;
- **a blind arm** — the same model without context (without retrieval). It shows how much it knows from the weights alone;
- **an oracle** — the model gets only the golden passage. That is the ceiling for retrieval.

The system lies between the blind arm and the oracle. If both lose to the constant class, the dataset or the model does not
distinguish the architectures: first fix the dataset, and only then compare graphs with vectors.

## 2. One variable at a time
- Every constant in the processing (document truncation, the candidate limit, a threshold, the number of passages) is a hyperparameter.
  You change one, freeze the others and record them.
- The comparison arms get **the same constants**. An oracle reading 4000 characters against a system reading 1100
  measures truncation, not retrieval.
- Check whether a constant does not throw out the golden answer before the model. Example: the candidate limit cuts off the golden document
  in part of the questions, which no prompt will fix.

## 3. Configuration selection and the test
- You choose the configuration on a selection set, and you report the result **only from a separate, held-out test set**.
  The best of 40 configurations on the same 200 examples is inflated by the selection itself.
- **A control on shuffled labels:** repeat the choice of the best configuration after randomly shuffling the labels.
  The advantage you get on noise is the threshold below which a gain means nothing.
- If the optimum lies at the edge of the parameter grid, the grid is too narrow — widen the range before you announce the result.

## 4. The label and the component metric
- **A label from the distribution, not from a regex.** When the model classifies, take the decision from the probabilities of the label tokens
  (sum the spelling variants). Parsing free text produces silent errors, and the same value gives the confidence on which
  refusing to answer depends.
- **A component metric must model what happens next.** A worse precision of a component (e.g. concept matching) can
  give a better system when a downstream filter rejects false hits. Assess the pair: coverage and leakage on control
  questions (a question with one concept swapped for a random one), not the component's metric alone.

## 5. Invariants
- Derived structures (parallel arrays of labels, identifiers, results) have an assertion on matching length and order
  and an independent recomputation from the source on a sample. Misaligned arrays do not throw an error, they just change the result.
- You key the eval result cache by the **whole** input (prompt, model, parameters, dataset version), not by the question alone.
- You test a validator (of citations, of the format) on edge cases, e.g. a bracket with several identifiers.

## 6. The model + harness pair manifest
An eval result belongs to the pair, not to the model. For every report record:
`model (full identifier) | prompt hash | tool schema version | policy/rubric version | environment
image hash | eval suite version`. A change of any field, including a silent model change at the provider, is a new pair
to measure again.

## 7. Regression from traces
- Every production trace carries **the contract version**: the prompt hash and the eval policy (required words, the minimum
  and maximum of tool and model calls, the judge rubric version).
- A new deterministic rule you run on **recorded traces without re-running the agent**: cheaply
  and repeatably. A lower limit on tool calls ("it had to search") catches the answer "check on services X" given without
  searching.
- You run the LLM judge only on a random sample or on traces with a negative user rating (👎, a retry,
  an escalation).
- **Immutable copies of inputs.** Production input data (logs that expire after 7–30 days) you archive
  asynchronously, without overwriting. The evals read the archive, so a change in the result comes from the system, not from the source.
- The same suite runs locally, on the PR preview environment (the thresholds block the merge), after promotion (an alarm to the on-call person)
  and periodically in production (drift).

## 8. Rules as the regression floor
When an LLM replaces or complements existing rules (regex, heuristics):
- the rules keep running, and the LLM result sits next to them;
- the eval checks **inclusion**: whether what the rule found is in the LLM result. You measure the precision of every
  element separately;
- you measure **dataset-level noise**: an element present in more than approx. 30% of the results is noise. It goes onto an exclusion list
  in the code, because the prompt will not remove it;
- when the model has to point to a fragment of the input, it returns the numbers of the first and last lines, and the code assembles the text from its own copy.
  The content cannot be made up, but a wrong range can still happen, so you measure range accuracy in the eval.

## 9. The harness change gate
A change of a prompt, a skill, a hook, a tool description or a schema, manual or from a self-improvement loop:
1. In the PR a **prediction**: which cases should go from failure to success and what risks a regression.
2. The result against a frozen baseline **and** a held-out dataset. You accept the change when it improves the working dataset
   and does not worsen the held-out one. A "working versus held-out" gap is a signal that the change is learning the exam.
3. The author of the change (a human or an agent) does not change, in the same PR, the scenarios they are graded on.
4. Then deployment or rollback, with a record in the report.

## 10. The report and choosing the oracle
- **The main readiness signal is the share of tasks passed in full** (all rubric criteria). The mean of met
  criteria and the spread between repetitions go alongside as diagnostics: a report pointing out 8 of 10 risks is not
  "80% useful". The mean can be a reward in training, not a measure in a report.
- **You choose the substitute oracle by the reversibility of the action:** a deterministic assertion in the loop (the database state after
  the conversation, the last request matching the schema), a rubric and a fact verifier in the middle, a human before an irreversible
  action. With a self-improvement loop — a frozen test set and a versioned judge (§9).
- Compare harnesses or models on **the same execution resources** (CPU, memory, time limits) and with the same number of
  repetitions — a difference in the result can come from the infrastructure.

## 11. A decision classifier (an LLM as a classifier)
- A test of option order and names: shuffle and rename the options, count the changed answers.
- A threshold fitted on your own labels **separately for every decision point**, never the default 0.5.
- A cascade (a cheap model, and the expensive one only under uncertainty) measured against the expensive model alone.
- Particular caution with irreversible steps: a confident wrong choice is the typical failure — there a lower threshold for
  handing over to a human.
- Before attributing a gain to fine-tuning: a control on the frozen base model with the same prompt.
- The test set split by case (the same document does not end up on both sides), preferably closed;
  a public benchmark saturates. Changing words in the option definitions is a model change, so a new test.
- You check the licence in the weights file, the base model and the data, not on the repository badge.

## 12. Utility with a penalty (an agent answering with numbers)
- Goals written down before the first version of the agent: accuracy, the share of wrong answers among those given **together
  with coverage**, p50 and p95 of time.
- **Utility with a penalty:** +1 a good answer or a justified refusal, 0 an unnecessary refusal, −2 a confident wrong number. An agent that
  refuses everything does not win, and one that guesses loses.
- A change is accepted when utility grows (or stays flat while time falls), with a **paired bootstrap** on the same
  questions. You hold out **whole question templates**, not just instances — the result on new templates is often clearly lower.
- You measure time with a single user and an empty cache, not only under eval concurrency.

Sources: F. Khan, "Structuring 40 Million Documents into an Agentic Knowledge Graph" (2026-08-26, the numbers from his repo
[unverified]); A. Punnen, "Eval-Driven Development" (2026-08-18); Netflix Tech Blog, "Making Failure Diagnosis
Reliable with Pensive AI" (2026-10); J. Wąsowski, "AI Harness Evolution: … Overfitting Without a Holdout" (2026-10-22);
F. Khan, "Engineering Multi-Agent AI for a 100 GB Data Warehouse" (2026-10); A. Alcaraz, "Grounded Reasoning For Agents"
(2026-10-20). The authors' numbers [unverified].
The thresholds (30% noise, 7–30 days of retention) are examples from these articles, not rules [assumption].
