# Data splits and leakage

Leakage is information from the test set or from the future that gets into training. The result is then
inflated, and the model disappoints after deployment. Kapoor and Narayanan (Patterns 2023) describe eight types of leakage, from
textbook errors to open research problems.

## Choosing the split
| Situation | Split |
|---|---|
| data over time, the model predicts the future | temporal: training earlier, test later; validation with a rolling window |
| many rows for the same unit (customer, patient, device, document) | group (GroupKFold): a unit on one side only |
| both at once | temporal with groups: a unit does not cross the boundary |
| duplicates and near-duplicates (copies of text, snapshots of the same object) | deduplication before the split, approximate too |
| a rare class | stratified, but still temporal/group if the situation requires it |
| little data | nested cross-validation (tuning inside, assessment outside) |

## Typical sources of leakage
- scaling, imputation, feature selection or PCA computed on the whole dataset before the split;
- a feature known only after the event (the return date when predicting a return), including a derivative of the label;
- the same unit in training and test; duplicates;
- labels created on the basis of the future relative to the moment of prediction;
- hyperparameter tuning and model selection on the test set (silent leakage, the most common);
- benchmark contamination: the test set or its answers were in the training data of the base model.
  For language models check the reported overlap (n-grams), use your own or a hidden set, and do not
  attribute a gain in the result to the method without a control.

## Detection
1. A result that is too good: compare with a simple baseline and with the literature; a jump of a dozen or so points is a reason for an audit.
2. Negative control: shuffle the training labels — the test result must drop to the random level.
3. Feature importance: a dominant feature that you do not know at the moment of prediction is a suspect.
4. A "forward" test: train on older data, assess on the newest data, never seen at all.
5. A validation↔pilot difference larger than the spread between seeds → look for leakage or drift.

## Test-set hygiene
- The test set is frozen (hash, date), access is restricted; the number of reads is recorded.
- Every read "burns" the set: after many rounds of changes based on the test, treat it as a validation set and collect a new one.
- Decisions about the architecture, threshold and features are made on validation.
- Report the test result once, together with the number of tuning runs that led to it.
