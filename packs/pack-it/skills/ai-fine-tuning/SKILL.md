---
name: ai-fine-tuning
description: Use for fine-tuning a model on your own data — prompt, RAG or fine-tuning, data, SFT and LoRA, DPO, distillation, before-and-after evaluation, licences.
metadata:
  review: "2027-04-17"
  catalog: "Use when you consider or carry out fine-tuning a language model on your own data — the prompt, RAG, fine-tuning ladder and when fine-tuning helps (format, style, a narrow task, a smaller cheaper model) and when it does not (missing knowledge), collecting, cleaning and deduplicating data, splitting into sets, chat formats, label quality, SFT, efficient methods (LoRA, QLoRA, PEFT) with hyperparameter starting points, preference tuning (DPO, an overview of RLHF), distillation from a larger model (licences of the teacher model's outputs), before-and-after evaluation on a frozen set, overfitting and forgetting, data and model licences, privacy, a provider API or your own training (TRL, PEFT, Unsloth, Axolotl). Not for the evaluation method (ai-evals), RAG (ai-rag), the MLOps pipeline (ai-mlops), hosting the model (ops-ai-inference), data pipelines (data-engineering), GDPR (arch-privacy-compliance) or shrinking the model after training (ai-model-optimization)."
  keywords: "fine-tuning, finetuning, dostrajanie modelu, dotrenować model, własny model, LoRA, QLoRA, PEFT, SFT, DPO, RLHF, destylacja, distillation, nauczyciel uczeń, dane treningowe, zbiór treningowy, jsonl, chat template, rank, alpha, learning rate, przeuczenie, overfitting, catastrophic forgetting, zapominanie, Unsloth, Axolotl, TRL, Hugging Face, adapter, czy dotrenować czy RAG, mały model zamiast dużego, model fine-tuning, train the model further, own model, teacher student, training data, training set, forgetting, fine-tune or RAG, a small model instead of a large one"
---

# Fine-tuning models — from the decision to a before-and-after comparison

Fine-tuning changes the model's **behaviour** (format, style, a narrow task), it does not add current knowledge to it.
The skill leads from the decision "whether at all" to the evaluation. The assessment method is described by **ai-evals**, RAG — by **ai-rag**,
the production pipeline — by **ai-mlops**, serving the result — by **ops-ai-inference** (`.claude/skills/ops-ai-inference/SKILL.md`).

## Procedure
1. **The evaluation set first.** Before you train anything, collect a frozen set with tasks from production
   (the method: **ai-evals**), compute the score of the base model with a good prompt. Without it "better" means nothing.
2. **The decision ladder** — go from the cheapest rung and go lower only with evidence from the set from step 1:
   | Symptom | First move |
   |---|---|
   | the model does not know the company's facts, invents, the knowledge changes | RAG (**ai-rag**), not fine-tuning |
   | a wrong format, tone, unstable output | a better prompt, examples in the prompt, structured output (**eng-llm-features**) |
   | the prompt is long and expensive, and the task narrow and repetitive | fine-tuning a small model |
   | latency or cost too high with a large model | distillation or fine-tuning a smaller model |
   | style or preferences hard to describe, easy to compare | SFT, then possibly DPO |
   Fine-tuning and RAG do not exclude each other: a fine-tuned model can read the inserted context better.
3. **Data** (details: `references/data-and-hyperparameters.md`):
   - the source and the legal basis: personal data without a basis drops out, the source's licence recorded (step 8);
   - cleaning (encoding, empty and truncated answers, templates), **deduplication** exact and approximate;
   - **splitting by unit** (customer, conversation, ticket), not by random rows, and only after deduplication;
   - a chat format matching the model's template (`messages` with roles), the loss computed only on the assistant's answers;
   - label quality matters more than quantity: review a random sample manually, with human assessment two raters
     and the agreement between them.
   Start with a small set and draw a learning curve (25/50/100% of the data); a flat curve means that the problem
   is the data or the task, not their quantity.
4. **Method:**
   - **SFT** (learning on input → desired output pairs) is the default start.
   - **LoRA/QLoRA (PEFT)** trains small adapters instead of all weights; QLoRA does it on a model frozen in 4 bits.
     Cheaper in memory and fast to iterate. Starting points: `references/data-and-hyperparameters.md`.
   - **Full fine-tuning** only when LoRA with a high rank measurably is not enough, and you have the memory and a lot of data.
   - **DPO** (pairs "better / worse answer", without a separate reward model) after SFT, when the goal is preferences.
     RLHF with a reward model and reinforcement learning is heavier; reach for it with a team that will maintain it.
5. **Distillation** (teacher → student): a large model generates answers to **real prompts from the domain**, filter them
   with a verifier or a judge, the student trains with SFT. Before the start check the terms of use of the teacher's outputs (step 8)
   and whether the prompts contain personal data.
   Distilling **an agent**: instead of SFT on the teacher's full trajectories, correct only the student's wrong turns (on-policy
   correction, like DAgger) and evaluate in the target harness — in one preprint full trajectories lowered the score
   from 78% to 63%, and turn correction gave approx. 80% (the source below; one study, the arms also differed in data).
6. **Training:** record the configuration, the seed, the data version (a hash) and the libraries; one change per run.
   Watch the training **and** validation loss and the task metric. A divergence (training falls, validation rises or stalls)
   is overfitting: fewer epochs (usually 1–3 [heuristic]), more data, a lower learning rate, a smaller rank.
7. **Before-and-after evaluation** on the same frozen set (**ai-evals**): the base model with a prompt vs the fine-tuned one,
   the score on the task **and** on a regression set of general skills (catastrophic forgetting: the model is great at the task,
   worse elsewhere). The evaluation set never goes into training; also check for leakage (approximate duplicates
   between training and evaluation). The fine-tuned model wins only when the improvement exceeds a threshold set **before** training.
8. **Licences and privacy:**
   - **data:** the licence and the rights to use it in training; customer and employee data — the basis, minimization,
     anonymization before training (**arch-privacy-compliance**); the model can memorize data and it is hard to remove it from it;
   - **the base model:** does the licence allow fine-tuning and distributing a derivative? Naming requirements or user thresholds;
   - **the teacher's outputs:** the terms of API providers often forbid training on the outputs of competing models;
     the licences of open models vary. Read the current text, not your memory (`references/data-and-hyperparameters.md`).
9. **Where to train:** a provider API (little work, no weights, lock-in, changing availability) or your own training
   (TRL + PEFT, Unsloth, Axolotl — control and weights, but GPUs and maintenance). Check the state of the offering in the documentation
   on the day of the decision; record the decision as an ADR with the cost. Deploying and versioning the adapter: **ai-mlops**, **ops-ai-inference**.

## Result
A fine-tuning card (in the repo, e.g. `docs/project/…`): Decision (the ladder rung, why) · Data (source, size, hash,
legal basis) · Method and hyperparameters · Result before and after (task + regression) · Risks and licences · Next steps.

## Example
Input: "The Fakturki ticket classifier (12 categories) on a large API model costs 2,400 PLN a month and takes 3 s."
The card result:
- **Decision:** a narrow task, the prompt already tuned, no knowledge gaps → fine-tuning a small 8B model instead of RAG.
- **Evaluation:** 400 tickets from the frozen set (split by customer), baseline: the large model 0.87 F1 [example numbers].
- **Data:** 5,200 tickets after deduplication (from 6,100), personal data masked, labels from a sample of 100 items checked.
- **Method:** QLoRA, all linear layers, 2 epochs; the threshold: ≥ 0.85 F1 and no drop on the regression set.
- **Result:** 0.88 F1, 0.4 s [example]; recorded in the card together with the set's hash and the configuration.

## Checklist
- [ ] a frozen evaluation set and the baseline score computed before training
- [ ] the prompt → RAG → fine-tuning ladder walked through with evidence on every rung; missing knowledge is not a reason to fine-tune
- [ ] data: legal basis, deduplication, split by unit, a format matching the template, a sample of labels checked
- [ ] hyperparameters from a justified starting point, one change per run, configuration recorded
- [ ] before-and-after evaluation, also the regression of general skills; the threshold set in advance
- [ ] licences: data, the base model, the teacher's outputs; personal data anonymized
- [ ] the API vs own training decision with the cost; the adapter versioned

## Additional materials
- `references/data-and-hyperparameters.md` — data preparation, LoRA/QLoRA/DPO starting points with sources, tools, licences.

## Sources
- Dettmers et al., "QLoRA" (arXiv 2305.14314, 2023) — NF4, double quantization, paged optimizers, a 65B model on
  a single 48 GB card; search 2026-10-17, the paper's content was not opened [unverified].
- Rafailov et al., "Direct Preference Optimization" (NeurIPS 2023) — DPO without a reward model and reinforcement learning;
  a summary from a search 2026-10-17.
- Biderman et al., "LoRA Learns Less and Forgets Less" (TMLR 2024) — LoRA forgets less, but also learns less
  than full fine-tuning, "not always"; summaries from a search 2026-10-17.
- Lee et al., "Deduplicating Training Data Makes Language Models Better" (ACL 2022) — duplicates, overlap of
  the training and validation set; search 2026-10-17.
- OpenAI is phasing out self-service fine-tuning (an announcement from May 2026, detailed dates from secondary sources),
  search 2026-10-17 [unverified — check the provider's page].
- Yu et al. (Salesforce AI), arXiv:2609.09134, preprint v1 of 8.09.2026, discussed by J. Wasowski ("Model–Harness
  Fit: Why A Better Teacher Makes A Worse Agent", Medium, approx. 12.10.2026); the preprint was not opened, numbers from the article
  [unverified] — distilling an agent, fitting the model to the harness.
Described in our own words.
