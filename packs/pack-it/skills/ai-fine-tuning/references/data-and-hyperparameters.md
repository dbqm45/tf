# Data, hyperparameters and fine-tuning tools

Facts as of 2026-10-17 (a search; the Hugging Face documentation was not opened, because the pages were unavailable
from the work environment). Treat the values as **a starting point to check on your own set**, not a rule.

## Data
- **The order:** cleaning → deduplication → splitting by unit → chat format → a sample manually.
- **Deduplication:** exact (a text hash) and approximate (MinHash); Lee et al. (2022) found approximate duplicates
  in popular sets and an overlap of the training set with the validation one. Deduplicate also **between** training
  and evaluation, because that is leakage inflating the score.
- **Splitting:** by customer, conversation or source document. A random split of rows puts the same conversation
  into both sets.
- **Chat format:** a list of `messages` with roles (`system`, `user`, `assistant`), rendered with the chat template of **this**
  model (a different template = a different model than at serving). The loss only on the assistant's answers; in TRL this is done with
  the `assistant_only_loss` option [unverified — the name from memory, check in the documentation of the version].
- **Labels:** inter-rater agreement (e.g. Cohen's kappa) for subjective tasks; labelling rules written down;
  borderline examples in a separate set. Treat model-generated labels like synthetic data: a sample checked
  by a human.
- **Quantity:** there is no "sufficient" number; a learning curve (25/50/100% of the data) shows whether the data helps.
  A secondary source advises against fine-tuning when the evaluation set has fewer than approx. 100 examples [an opinion, not a rule].
- **Personal data:** by default exclude or anonymize it before training. The EDPB in opinion 28/2024 (December 2024)
  states, among other things, that a model trained on personal data is not automatically anonymous, and legitimate interest
  requires a three-step test (law firm summaries, 2026-10-17; the opinion was not opened [unverified]).
  Impact assessment and legal bases: **arch-privacy-compliance**.

## LoRA / QLoRA starting points
| Parameter | Starting point | Source and notes |
|---|---|---|
| layers | all linear matrices, including MLP | Thinking Machines, "LoRA Without Regret": LoRA only on attention does worse, even with the same number of parameters (a summary from a search 2026-10-17) |
| rank `r` | 8–64 to start; more with large sets | the default `r=8` in PEFT [unverified]; the rank limits capacity, so increase it with a large set |
| `lora_alpha` | `alpha = 2r` as a common practice | the apxml tutorial (2026-10-17); the adapter scale = alpha / r, with `use_rslora` alpha / sqrt(r) (PEFT documentation, a search) |
| LoRA learning rate | approx. 10× higher than in full fine-tuning | "LoRA Without Regret" (secondary sources: 10×, in short runs up to approx. 15×); the optimal LR depends weakly on the rank |
| QLoRA learning rate | of the order of 1e-4–2e-4 | from the QLoRA paper, from memory [unverified] |
| adapter dropout | 0–0.1 | practice [unverified] |
| epochs | 1–3 | a heuristic; stop after validation stagnates |
| batch | a small effective batch is sometimes better | LoRA tolerates large batches worse (Thinking Machines, a search) |
Memory: QLoRA loads the model in 4 bits (NF4), computes in BF16; the authors showed fine-tuning a 65B model on a single 48 GB card.
The LoRA rank is 1–2 orders of magnitude smaller than the rank of the changes in full fine-tuning (Biderman et al.), so on tasks
requiring a lot of new knowledge (continued pretraining, code, mathematics) LoRA learns less, but also forgets less.

## DPO
- Data: the columns `prompt`, `chosen`, `rejected`; TRL accepts an explicit and an implicit prompt, recommends the explicit one.
- Start: `beta = 0,1` (range 0.1–0.5), a learning rate one or two orders lower than in SFT, of the order of 5e-7–1e-6
  (examples from the EasyDeL and Liquid AI documentation, a search 2026-10-17; the TRL documentation was not opened).
- Beta regulates the departure from the reference model (the KL penalty). A too high LR or a too low beta breaks the model.
- Do DPO after SFT on the same domain; the pairs must differ in quality, not in length or style.
- RLHF (a reward model + PPO) is sometimes removed from libraries; in TRL 1.x PPO was reportedly removed [unverified].

## Tools (state per a search 2026-10-17, mostly secondary sources)
- **TRL + PEFT (Hugging Face):** SFT, DPO, adapters; the basic choice when you want control and compatibility with the ecosystem.
- **Unsloth:** speed and memory on a single card; secondary sources claim savings of approx. 40% VRAM and 2–5× faster,
  but the numbers contradict each other; multi-GPU support limited [unverified].
- **Axolotl:** configuration in YAML, many GPUs and nodes (DeepSpeed, FSDP).
- **LLaMA-Factory:** a wide range of models, a web interface.
- **torchtune:** according to one source phased out in 2025 [unverified].
- **Provider APIs:** OpenAI is phasing out self-service fine-tuning (new users blocked; existing jobs
  until 2027-01-06 per secondary sources) — check the provider's page. Claude 3 Haiku on Amazon Bedrock had fine-tuning
  (GA 2024-11-01, the Oregon region); the current state unknown [unverified]. Together AI and Fireworks offer fine-tuning
  of open models (Fireworks with serving many LoRA adapters on one base model; secondary sources).

## Licences of the teacher's outputs
- Anthropic: the terms forbid using the outputs to train models competing with Anthropic (the Claude help centre,
  a search 2026-10-17). OpenAI: a similar ban in the terms (a secondary summary; check the current document).
- Llama 3.1: the licence allows using the outputs to improve other models, but the name of the released model has to start
  with "Llama" and "Built with Llama" applies (a secondary summary; Llama 3 had a ban).
- Models under Apache 2.0 or MIT usually do not have such restrictions; read the licence of the specific model anyway.
- Machine-generated outputs may not be subject to copyright, but contractual restrictions still apply
  (a legal commentary; this is not legal advice) — the legal department approves the decision.
