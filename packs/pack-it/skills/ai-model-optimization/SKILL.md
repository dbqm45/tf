---
name: ai-model-optimization
description: Use for shrinking or speeding up a model as an artifact — measurement, quantization, GGUF, ONNX, TensorRT, OpenVINO, weight memory budget, size choice.
metadata:
  review: "2027-04-17"
  catalog: "Use when a model is to be smaller, faster or cheaper as a file and a runtime environment — baseline measurement (quality, latency, cost, memory), post-training quantization (INT8, INT4, GPTQ, AWQ, FP8, FP4, GGUF with llama.cpp), assessing the quality loss after quantization, distillation for size, pruning, export and compilation of classical and vision models (ONNX, TensorRT, OpenVINO, torch.compile), speculative decoding as a model-side choice, the GPU memory budget for weights (parameters times bytes), choosing the model size. Not for servers, KV cache, batching and routing (ops-ai-inference), training and fine-tuning (ai-fine-tuning), the complexity of algorithms in code or the evaluation method (ai-evals)."
  keywords: "kwantyzacja, quantization, INT8, INT4, FP8, GPTQ, AWQ, GGUF, llama.cpp, Q4_K_M, zmniejszyć model, model za duży, nie mieści się w GPU, ile pamięci potrzebuje model, ile VRAM, ONNX, TensorRT, OpenVINO, torch.compile, przyspieszyć model, model za wolny, dekodowanie spekulatywne, speculative decoding, przycinanie, pruning, mniejszy model, Ollama, lokalnie na laptopie, wnioskowanie na CPU, ResNet, model wizyjny, shrink the model, model too large, does not fit in the GPU, how much memory the model needs, how much VRAM, speed up the model, model too slow, smaller model, locally on a laptop, inference on CPU, vision model"
---

# Model optimization — a smaller and faster file, without a blind risk to quality

This skill is about **the model artifact** (weights, format, compilation). The server, KV cache, batching and routing are described by
**ops-ai-inference** (`.claude/skills/ops-ai-inference/SKILL.md`) — do not repeat that content here. Training and fine-tuning are
**ai-fine-tuning**, the evaluation method — **ai-evals**.

## Procedure
1. **The goal and the baseline measurement.** Write down what is to improve and to what value (e.g. p95 < 40 ms, fits in 24 GB,
   the cost per 1000 requests). Measure the current state on **the target hardware**: quality on the task's evaluation set, latency
   (for an LLM: time to first token and tokens per second; for a vision model: p50 and p95 per image), throughput,
   peak memory, cost. A warm-up before the measurement, many repetitions, the same batch size as in production.
   A profile (where the time goes) before choosing a technique: a bottleneck in I/O, in preprocessing or in memory
   will not disappear after quantization.
2. **The weight memory budget:** the number of parameters × bytes per parameter (FP16/BF16: 2, FP8 and INT8: 1, INT4: 0.5; formats with blocks
   of scales add a few percent, e.g. NVFP4 about 4.5 bits per value per secondary sources).
   70 bn × 2 B = 140 GB; in INT8 70 GB; in INT4 about 35–40 GB. On top of that come activations and the KV cache (its budget:
   **ops-ai-inference**). A model that "fits" without headroom for the context does not fit.
3. **Choosing the model size.** The smallest model that passes the task evaluation wins. Compare on your own set
   variants with similar memory: a larger quantized one vs a smaller one in higher precision vs a smaller fine-tuned one (**ai-fine-tuning**).
   Do not assume the order — check it.
4. **Quantization** (a table of formats and hardware: `references/quantization.md`):
   - first the mildest variant: FP8 or INT8 (on a GPU with native support), then 4 bits (AWQ, GPTQ);
   - GGUF for llama.cpp, Ollama and a CPU or a laptop; choosing the level (`Q8_0`, `Q5_K_M`, `Q4_K_M`) by RAM;
   - calibration data from the production distribution (language, domain, length), not from someone else's benchmark;
   - the format must be supported by the target engine and GPU; check the compatibility matrix of the version you have.
5. **Quality loss after quantization.** The same set as in step 1 (**ai-evals**), before and after, **split into slices**:
   language, input length, task type, difficulty. The average hides regressions: an EMNLP 2025 study (Mekala et al.) showed
   at 8 bits on average about 0.8% loss, and at 4 bits drops of up to 59% on long-input tasks, stronger
   outside English. Perplexity and the KL divergence against the full-precision model are quick indicators
   for comparing variants, but they do not replace the target task. Set the acceptance threshold **before** the measurement.
6. **Classical DL and vision:** export to ONNX, running in ONNX Runtime, OpenVINO (Intel CPU) or TensorRT (NVIDIA GPU),
   INT8 quantization with calibration; `torch.compile` when you stay in PyTorch. Details and traps: `references/export-and-compilation.md`.
   After the export check numerical parity with the original model and the task metric, not only the speed.
7. **Distillation for size, pruning.** Distillation (teacher → a smaller student) usually gives a bigger gain than pruning;
   the training mechanics and the licences of the teacher's outputs: **ai-fine-tuning**. Unstructured pruning (zeroing weights)
   rarely speeds things up without hardware support; structured pruning removes heads or layers and requires retraining. Start with quantization.
8. **Speculative decoding** (LLM, latency): a small model drafts tokens, the large one verifies them in one pass,
   and the output distribution stays the same as the large model's (Leviathan et al.). It requires a compatible tokenizer or trained heads
   (Medusa, EAGLE); the gain depends on the acceptance rate and grows with small batches. Enabling it in the server: **ops-ai-inference**.
9. **Result:** a table of variants and a decision; version the artifact (the weights hash, quantization parameters, calibration, tool versions),
   because rebuilding on another version gives a different result.

## Result
A table, one line per variant: variant · weight memory · quality (task + slices) · latency p50/p95 · cost per 1000 requests ·
decision (accepted/rejected and why).

## Example
Input: "Llama 70B in BF16 does not fit on one 80 GB card; we want a chat with an 8k context."
Result:
| Variant | Weights | Quality (a set of 300 queries) | Decision |
|---|---|---|---|
| BF16 | 140 GB | baseline | rejected, 2 cards |
| FP8 | 70 GB | −0.4 pp [example] | rejected, 10 GB of headroom for the KV cache |
| AWQ INT4 | about 38 GB | −1.8 pp, of which −5 pp on long Polish documents [example] | accepted conditionally |
Next step: AWQ calibration on Polish documents and a repeated measurement; a threshold of −2 pp on every slice.

## Checklist
- [ ] a numerical goal and a baseline measurement on the target hardware (warm-up, p95, peak memory)
- [ ] the weight memory budget computed, headroom for the KV cache and activations
- [ ] quantization from the mildest variant; calibration on production data
- [ ] quality before and after on the task set, split into slices; the threshold before the measurement
- [ ] after the export numerical parity and the task metric, not only the speed
- [ ] the artifact versioned (hash, parameters, tool versions)

## Additional materials
- `references/quantization.md` — formats (FP8, INT8, GPTQ, AWQ, GGUF, FP4), hardware and choice.
- `references/export-and-compilation.md` — ONNX, ONNX Runtime, TensorRT, OpenVINO, torch.compile, traps.

## Sources
- Lin et al., "AWQ" (arXiv 2306.00978; MLSys 2024) — protecting about 1% of salient channels by activations; search 2026-10-17.
- Frantar et al., "GPTQ" (arXiv 2210.17323; ICLR 2023) — one-shot quantization to 3–4 bits; search 2026-10-17.
- Mekala et al., "Does quantization affect models' performance on long-context tasks?" (EMNLP 2025, arXiv 2505.20276)
  — numbers from the abstract, search 2026-10-17.
- Leviathan, Kalman, Matias, "Fast Inference from Transformers via Speculative Decoding" (2022/2023) — the output distribution preserved;
  the abstract from a search 2026-10-17.
- Tool and format versions: `references/quantization.md`, `references/export-and-compilation.md` (with dates).
Described in our own words.
