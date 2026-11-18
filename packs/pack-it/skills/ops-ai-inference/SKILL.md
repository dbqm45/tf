---
name: ops-ai-inference
description: Use for self-hosting language models — GPU memory and KV cache, vLLM, continuous batching, metrics, scaling.
metadata:
  review: "2027-01-17"
  visibility: name
  catalog: "Use for self-hosting language models and AI infrastructure — GPU memory and KV cache, prefill and decode, continuous batching (vLLM), cache-aware routing (llm-d, Gateway API Inference Extension), prefill/decode disaggregation, metrics and scaling, an API or your own server. Not for SLOs of AI features (ops-sre-incidents) or general Kubernetes operations (ops-kubernetes)."
---

# Language model inference infrastructure

A language model server is not a stateless HTTP service, but a queue in front of a very expensive and demanding accelerator.
Tools from the world of web applications (round-robin, autoscaling on CPU) work badly here.

## 0. Whether to self-host at all
Your own server makes sense with constant, high traffic, data requirements (the data must not leave the infrastructure) or a model
fine-tuned in-house. With low or uneven traffic a provider's API is usually cheaper and simpler — a GPU costs money even
when it does nothing. Record the decision as an ADR with the cost per 1000 requests on both sides (ops-finops).

## 1. What limits the GPU
- The bottleneck is usually **GPU memory (VRAM)**, not compute. Three things compete for it:
  the model weights, the activations and the **KV cache** (the stored state of the processed tokens).
- Weights: the number of parameters × bytes per parameter — a 70-billion-parameter model in 16 bits is about 140 GB, so it needs
  several GPUs (tensor parallelism, communication between GPUs over NVLink or InfiniBand at every token).
- The KV cache grows with every token of the conversation: a few long conversations can exhaust the memory even though the model itself fits.
  That is why you set the limit on context length and the number of concurrent sequences deliberately.

## 2. The two phases of generation
| Phase | What happens | Limited by |
|---|---|---|
| prefill | the whole prompt is processed at once, the first token is produced | compute; grows with the prompt length |
| decode | subsequent tokens one at a time | memory bandwidth |
The metrics correspond to the phases: time to first token (TTFT) is mainly prefill and the queue, the time between tokens — decode.

## 3. The model server
- **Continuous batching** (e.g. vLLM with PagedAttention): decode steps of many requests interleaved on one GPU, free
  slots immediately taken by new requests. According to the article's author, one GPU then serves dozens of conversations
  instead of one. Before you build a cluster, run the server alone with parallel requests and measure it.
- An OpenAI-compatible API (`/v1/chat/completions`) — clients (SDKs, LangChain) do not depend on who serves the model.

## 4. Routing: round-robin destroys the cache
- A plain Kubernetes Service or load balancer sends the next message of a conversation to a random pod. The cache of that
  conversation does not exist there, so the whole context is recomputed from scratch — that is exactly the "slow" response.
- **Cache-aware routing** (prefix-cache routing): the gateway knows the state and load of every pod and sends the message to where
  its KV cache lives. Example: llm-d (a CNCF Sandbox project, built on vLLM) with the Gateway API Inference Extension gateway
  and the endpoint-selecting component (Endpoint Picker).
- **Prefill and decode disaggregation** into separate pod pools, scaled independently; the cache transferred between them over RDMA.
- The result from the article (8 pods, 16 H100 GPUs, multi-client traffic): about 2× higher throughput than with round-robin.

## 5. Operations
- Health metrics: **the cache hit rate**, **the queue depth**, TTFT, the time between tokens, KV cache occupancy,
  GPU utilization (Prometheus). Autoscaling on the queue and latency, not on CPU.
- GPUs in Kubernetes: the `nvidia.com/gpu` resource through the device plugin (or the GPU Operator), GPU nodes with taints, so that
  regular pods do not land on them; requests and host memory limits for the server process (ops-kubernetes).
- A model change = a release: the model version and the server configuration in Git (e.g. a Kustomize overlay), a gradual rollout
  with a comparison of quality and latency (ops-release-engineering), SLOs in three layers (ops-sre-incidents, section 2).
- Models and weights from a trusted source, with a checksum; a model is also part of the supply chain (ops-supply-chain-security).
- The learning path: vLLM alone with parallel requests → a small cluster (kind/minikube with a GPU) with llm-d → production hardware.

## Checklist
- [ ] the API vs your own server decision with the cost per request
- [ ] the GPU memory budget: weights + KV cache at the target context length and number of sequences
- [ ] a server with continuous batching; cache-aware routing instead of round-robin
- [ ] metrics: cache hits, the queue, TTFT, the time between tokens; autoscaling on the queue
- [ ] the model and configuration versioned, rolled out gradually

## Source
[AI infrastructure — DevOps](https://medium.com/the-advanced-school-of-ai/ai-infrastructure-devops-0466baa552a3) — Gaurav Agnihotri,
The Advanced School of AI, September 2026 (summarized in our own words; numbers from the article marked in the text).
The weight memory calculation and the GPU rules in Kubernetes: our own.
