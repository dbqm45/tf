# Decisions and economics of an AI feature

## Choosing the tool: a rule, ML, an LLM
| Situation | Tool | Note |
|---|---|---|
| the logic can be written down, is auditable, the law requires an explanation | rule | cheap, deterministic; start here |
| there are labels, a narrow task, a fixed data shape (scoring, classification) | classical ML | requires data and maintaining the model |
| open text, summarizing, generation, many tasks at once | LLM | non-deterministic; requires evaluation and protection |
| mixed | rules for the easy majority, an LLM for the rest | reduces the cost and the error surface |

The test cost of error × who bears it: for each error type write down the effect, who bears it (the customer, an employee, the company),
whether it can be detected and undone. An irreversible and undetectable error requires a human before the effect.

## Unit economics
- **Cost per successful task** = (the cost of model calls with retries + retrieval + the judge/assessment + the time of the human
  verifying) / the number of tasks completed correctly. Cost per request understates the picture.
- Get token prices and limits from the vendor's price list on the day of the calculation (they change); mark the result with the date.
- Compare with the cost today (time × rate) and with the value (revenue, retention). Sensitivity: compute a variant with
  a 2× longer context and 2× more traffic.
- Cost levers: a smaller model for easy cases, a prompt cache, a shorter context, rules before the model
  (core-cost-control, ai-prompt-engineering).
- Coupled goals: higher quality usually = a more expensive model or more attempts = more latency. Write down the order in which they give way.

## Buy, build, API
Rungs: a ready product → an API with your own prompt and context (ai-rag) → fine-tuning (ai-fine-tuning) → your own model.
For each: the entry cost, the time to first value, the vendor dependency and its exit plan, where the data goes,
control over model changes (the vendor withdrawing a version = a regression without a change in the code).
Choosing the architecture: arch-ai-solutions.

## Data
A table: type of data (examples for evaluation, labels, source content) | do we have it | owner | legal basis for use
(RODO, the Polish name for the GDPR: arch-privacy-compliance) | freshness | preparation cost. An evaluation set from real tickets takes precedence.
