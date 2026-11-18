# Red teaming LLM features

Only with the system owner's consent, in a test environment or with an agreed scope; no attacks on other parties' services.

## Minimum scenarios
1. Direct jailbreak and bypassing the content policy.
2. Indirect injection: an instruction in an email, a page, a PDF, a tool result, a RAG document, an MCP tool description.
3. Exfiltration: whether data from the context will leave the system through an image, a link, a tool or an email.
4. Tool abuse: a call with someone else's identifier (IDOR), arguments outside the schema, a chain of tools.
5. Leaks of the system prompt and of data from other sessions or tenants.
6. Consumption: loops, very long inputs, cost per user.
7. Privilege transfer: whether the agent acts with the user's permissions, not broader ones.
The success criterion is the system's behaviour (whether the action ran, whether data left), not the content of the answer.

## Tools
- **garak** (NVIDIA, Apache 2.0): a scanner with a library of probes and detectors (injection, jailbreaks, leaks); good as
  a baseline model scan and regression. Research paper: arXiv:2406.11036.
- **PyRIT** (Microsoft AI Red Team): a framework for your own campaigns, including multi-turn ones (e.g. Crescendo, TAP).
- A comparative study (arXiv:2410.16527) points to problems with the reliability of detecting successful attacks in such
  scanners: verify the results manually on a sample. [conclusions from a search summary 17.10.2026, without reading the paper]
- Tools do not replace application tests (permissions, tools, egress): those are your own scenarios.

## MITRE ATLAS
A database of tactics and techniques of attacks on AI systems (the counterpart of ATT&CK). Use it as a vocabulary for the report and for mapping
scenarios; identifiers (e.g. AML.T0051 LLM Prompt Injection, AML.T0054 LLM Jailbreak) [unverified:
from a secondary source, check in atlas.mitre.org before citing].

## From a test to an evaluation
Every successful attack: a record (input, context, effect) → a case in the `ai-evals` set with an assertion on behaviour
(no tool call, no data in the output) → a gate in CI on a change of the model, prompt or tools.

## Adaptive attacks
A defence checked only with a fixed list of attacks says little. Nasr, Carlini et al., "The Attacker Moves Second" (arXiv
2510.09023, 2025-10, USENIX Security 2026): adaptive attacks (optimization, RL, search, humans) got around
12 defences with a success rate usually above 90%, although the defence authors had reported near zero; on AgentDojo a fixed template
reached 28%, and adaptive search 99%. Conclusions:
- a result of "blocks 99% from the list" is not proof of robustness — test with an attacker who knows the defence and iterates;
- **AgentDojo** (NeurIPS 2024) is a ready harness: the judge checks the environment state after the run, not the model's text,
  so it cannot itself be injected;
- robustness comes from architecture (isolation patterns, permissions — `agent-design-patterns.md`), a filter is an additional
  layer.
