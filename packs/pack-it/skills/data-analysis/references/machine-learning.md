# Machine learning basics for an analyst

First ask whether a model is needed: a business rule, an SQL query or simple statistics are sometimes better —
cheaper, explainable and easier to maintain.

## Types of learning
| Type | Data | Example tasks | Typical algorithms (from the simplest) |
|---|---|---|---|
| supervised — regression | examples with a numeric outcome | forecasting demand, delivery time | linear regression, decision trees and random forests, gradient boosting |
| supervised — classification | examples with a label | customer churn, spam, fraud risk | logistic regression, naive Bayes, k-nearest neighbours, decision trees, gradient boosting |
| unsupervised | data without labels | customer segmentation, anomaly detection | k-means, hierarchical clustering, principal component analysis |
| reinforcement | an environment with a reward | control, games, optimising sequences of decisions | rarely in business analytics |
| deep neural networks | large datasets, images, text, audio | image recognition (convolutional networks), sequences (recurrent networks, today mainly transformers), language processing | PyTorch, TensorFlow — usually ready-made fine-tuned models or language models via an API |
For tabular data simple models and gradient boosting usually win, not deep networks.

## Fundamentals (to understand what the model does)
- **Linear algebra**: data as matrices, features as vectors, products and decompositions of matrices (PCA is a decomposition by
  eigenvalues or singular values).
- **Differential calculus**: learning is the minimisation of a loss function; the gradient points the direction, gradient descent
  goes step by step the opposite way (the learning rate: too large — divergence, too small — slow).
- **Probability and statistics**: distributions, likelihood, Bayesian inference (naive Bayes),
  prediction uncertainty (`statistics.md`).
- **Ensembles of models**: bagging (many models on random samples, averaging — a random forest, lower variance)
  and boosting (successive models correct the errors of the previous ones — gradient boosting, e.g. XGBoost, LightGBM).

## Deep learning — a map
Fully connected networks (tabular data, rarely better than boosting), convolutional (images), recurrent and LSTM
(sequences — today mostly replaced by transformers), **transformers** (the attention mechanism; text, image, audio,
the basis of language models). **Transfer learning**: fine-tuning a model trained on a large dataset instead of
training from scratch — in practice the default.

## AI engineering with language models
| Approach | When | Cost and risk |
|---|---|---|
| **prompt** (an instruction, examples, an output format) | always at the start | the cheapest; sensitive to a model change — prompt regression tests |
| **RAG** (retrieving fragments of knowledge and attaching them to the prompt) | company knowledge, current, with a cited source | retrieval quality decides; permissions to documents must carry over to retrieval; the content of documents is data, not instructions (prompt injection — core-agent-security) |
| **an agent with tools** | multi-step tasks with actions | the scope of the tools' permissions, a human gate for irreversible actions, an action trail (core-agent-security, ops-sre-incidents: autonomy) |
| **fine-tuning** | a fixed format, style or a narrow task, when a prompt and RAG are not enough | training data, cost, version maintenance; not for adding facts |
- **Evaluation (evals)**: a set of cases with an expected result or an evaluation criterion, run on every change of
  the prompt, model or data — like regression tests (qa-spec-first-testing). Without it changes are guesswork.
- Hosting your own models: ops-ai-inference. Legal obligations (transparency, high risk): data-engineering,
  `quality-management-and-compliance.md`.

## Model evaluation
- **Data split**: a training, validation and test set (or cross-validation); for time series a split
  by time — not random (the model must not "see the future").
- **Data leakage**: a feature that would not be known at prediction time (e.g. a "return date" when predicting a return)
  gives a great result in tests and a useless model.
- **A baseline**: you compare the model with the simplest one (the most common class, the mean, last week's value).
- **Measures**:
  - classification — accuracy (misleading with imbalanced classes), precision (how many of those flagged are hits),
    recall (how many of the hits we flagged), F1, ROC-AUC and the precision–recall curve; a confusion matrix with the business cost
    of each error (a false fraud alarm versus a missed fraud);
  - regression — MAE (in the units of the outcome, robust), RMSE (penalises large errors), MAPE (in percent; fails with values
    close to zero).
- **Overfitting**: great on training, weak on the test → a simpler model, regularisation, more data.
- **Explainability and fairness**: feature importance, example explanations of predictions; checking results per group
  (whether the model discriminates). Decisions about people (credit, hiring) are subject to regulation (GDPR Art. 22, the AI Act) —
  with the legal department.

## From analysis to production (MLOps)
A model in production is a system, and a notebook with a result is not yet a product.
- **Serving mode**: batch (predictions computed overnight into a table — the simplest), online (an API with a time limit
  and a model version), streaming, on-device.
- **Reproducibility**: the code, data (a version or snapshot), parameters and environment recorded for every training; a model
  registry with metrics and status (candidate, production, retired); a feature store ensures the same feature definitions
  in training and in prediction (otherwise a training–production difference).
- **CI/CD for models**: tests of code and data, evaluation on the test set with a threshold (the new model no worse than the current one),
  shadow deployment (predictions computed but not used) or canary (ops-release-engineering), fast rollback.
- **Monitoring**: prediction quality when labels arrive with a delay; drift of the distribution of input
  data and predictions; latency and cost; an alert and retraining on a schedule or a threshold.

## Sources
- The scikit-learn documentation (User Guide: model selection and evaluation); A. Géron, *Hands-On Machine Learning*
- [roadmap.sh — AI and Data Scientist](https://roadmap.sh/ai-data-scientist) (mathematics, ML, deep learning,
  transformers, MLOps, AI engineering: prompts, RAG, agents, fine-tuning)
- [roadmap.sh — Data Analyst](https://roadmap.sh/data-analyst) (machine learning, supervised/unsupervised/reinforcement,
  decision trees, KNN, naive Bayes, k-means, logistic regression, model evaluation, deep learning, CNN, RNN, NLP)
Described in our own words.
