# Quantization formats — choice and caveats

State from a search on 2026-10-17; most sources are blogs and comparisons (secondary), the official documentation of vLLM,
llm-compressor and llama.cpp was not opened in this session. Treat numbers from blogs as indicative, your own measurement is decisive.

| Format | For what | Notes |
|---|---|---|
| FP8 | newer-generation NVIDIA GPUs, serving (e.g. vLLM) | usually the first choice: a small loss, calibration is sometimes optional; the "FP8 dynamic" scheme with weights scaled per channel and activations scaled dynamically (secondary). Native support depends on the GPU generation [unverified] |
| INT8 | broadly, also older GPUs and CPUs | usually a small loss; requires calibration when quantizing activations |
| AWQ (INT4, weights only) | serving on GPU | per secondary sources usually not worse than GPTQ; support depends on the GPU and the engine (e.g. none on AMD in vLLM per one source). Creating new checkpoints: llm-compressor (AutoAWQ archived per one source) [unverified] |
| GPTQ (INT3–4, weights only) | when AWQ is missing, broad CUDA support | a second-order method, one-shot quantization; the authors: a 175 bn model in about 4 GPU hours |
| GGUF (llama.cpp) | laptop, CPU, mixed CPU/GPU, Ollama, LM Studio | a file with weights and metadata; it is not a format for vLLM. Presets: `Q8_0` (close to lossless), `Q5_K_M`, `Q4_K_M` (a common compromise). Lower levels (Q3 and below) require an importance matrix (`imatrix`) |
| NVFP4 / MXFP4 | the newest GPUs (Blackwell) | about 4.5 / 4.25 bits per value; NVIDIA claims a drop of ≤ 1% against FP8 on one model (a secondary source, requires your own verification) |
| bitsandbytes NF4 | fine-tuning (QLoRA), quick trials | slower in serving; results sensitive to the model (Mekala et al.) |

## Choice in three questions
1. **Where does it run?** A GPU server → FP8, then AWQ/GPTQ; a laptop or CPU → GGUF; an Intel CPU with classical DL → OpenVINO.
2. **How much memory?** Compute parameters × bytes (SKILL.md, step 2) and leave headroom for the context.
3. **How much quality can be lost?** A threshold from the task evaluation; the fewer bits, the more important calibration and the split into slices.

## Assessment after quantization
- The target task split by language, input length and difficulty. A Cohere study on Command A: languages with a non-Latin script
  and hard tasks (mathematics) degraded the fastest, and automatic metrics underestimated the loss (on average 1.7% in automatic
  tests against 16% in human evaluation for Japanese; search 2026-10-17, the paper was not opened [unverified]).
- llama.cpp: `llama-perplexity` on your own text to compare variants; `llama-imatrix` + `llama-quantize --imatrix`
  for low bits. Tables of "percent perplexity loss per level" from blogs differ in metrics and models — do not carry them over.
- A regression set: a few dozen examples on which the full precision is correct; check how many stop being correct.
