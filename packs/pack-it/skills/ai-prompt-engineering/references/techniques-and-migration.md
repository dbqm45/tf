# Techniques and migration — state as of 2026-10-17

Contents: 1. Thinking · 1a. Claude 5.5 models · 2. Prefill and format · 3. Cache · 4. Migration · 5. Templates and registry · 6. Mistakes · 7. Other providers

Model names, parameters and prices change often; before a change check the current documentation page (core-grounding).

## 1. Thinking
- Claude 4.6 models and newer use adaptive thinking (`thinking: {type: "adaptive"}`): the model itself chooses whether
  and how much to think, depending on the `effort` parameter and the difficulty. In some of the newest models thinking is always on.
- Older models: extended thinking with `budget_tokens`. On 4.7 models and newer setting `budget_tokens`
  returns a 400 error; you control the budget through `effort`. During a migration replace the configuration and check it with an evaluation.
- Too frequent thinking with large system prompts you can limit with an instruction ("think only when the task
  requires multi-step reasoning").
- Few-shot examples also influence how the model reasons; give them as a problem, a method and a result.
- When thinking is off: a manual chain of thought — "reason before the answer, the result in `<answer>`". The code reads only `<answer>`.
- Do not use thinking for simple extraction, classification and format conversion; measure the quality gain and the cost.

## 1a. Claude 5.5 models (the guides "Prompting Claude Opus/Sonnet/Haiku 5.5", read 2026-10-20)
- `effort` is the main control of thinking (on Opus 5.5 thinking is always on); by default `medium` on Opus,
  Sonnet and Haiku 5.5 — set it explicitly and compare a few levels on your own evaluations. `xhigh` and `max` only where
  a gain was measured; less thinking → first a lower `effort`, not an instruction in the prompt.
- Thinking counts towards `max_tokens`, also when the thinking content is not returned: a limit set for an older model cuts
  answers off. In long agentic turns on Opus 5.5, 128,000 (the model's maximum) worked well.
- Changing `effort` between requests invalidates the cache; a change during a conversation without losing the cache — per-message effort
  (beta).
- An unsupervised agent: a turn ended with text only (a summary announcing a step) is a report, not the end of the task —
  a list of open items and a short "continue" message (core-async-delegation).
- Sonnet 5.5 on `low`/`medium` sometimes asks before the end of the work, and on every level adds unrequested tests
  and documentation; Haiku 5.5 with a long agent prompt on `low` finishes too early. An instruction helps: "work until
  everything is done; stop only without a human decision or before a risky step; after checking,
  report the result, and list ideas for additions at the end" (the factory: `work_contract` in `.tf/config/config.yaml`).

## 2. Prefill and output format
- Prefilling the last assistant message is not supported since the Claude 4.6 models (the request returns an error).
- Replacements: an enforced format (JSON, YAML, classification) → structured outputs with a schema;
  skipping the preamble → the instruction "answer directly, without a preamble", an output tag or a tool call;
  continuing an interrupted answer → a user message with the ending of the previous answer;
  refreshing the context in a long conversation → a reminder in the user turn or a tool supplying the context.
- The output contract, validation after receipt and failure handling: eng-llm-features §2.

## 3. A layout for the cache (Anthropic)
The mechanics of the API cache (the order `tools` → `system` → `messages`, `cache_control`, TTL, write and read prices, the minimum
prefix length, what invalidates it) are currently described by the built-in `claude-api` skill; the cost rules of an agent session:
core-cost-control. For the prompt one thing counts: the fixed part at the beginning, the variable one at the end, and you check the hits
in the fields `cache_creation_input_tokens` and `cache_read_input_tokens` (both 0 = no cache).

## 4. Migrating a prompt to a newer model
1. Read the provider's migration guide for the target model.
2. Run the evaluation set on the old and the new model **with the same prompt**; record the differences.
3. Remove: prefill, a manual `budget_tokens`, capital letters and "YOU MUST/ALWAYS" (instead of "CRITICAL: YOU MUST use the tool" →
   "Use the tool when …"), encouragements like "be thorough, use all the tools" — newer models are more
   proactive and overuse tools after such encouragements.
4. Add explicitly what used to be the default, if needed (e.g. an explicit request for an extensive result).
5. Tuning with single changes; the prompt version bumped (MINOR on a behaviour change, MAJOR on a change of the output
   contract [our own convention]); the model pinned in the configuration.

## 5. Templates and registry
- A template: a name, a version, variables with a description, the target model, the output schema, the evaluation set, the author and the change date.
- Variables inserted in one place (the end of the prompt), data in tags; escaping the user content.
- The registry can be a file in the repo (a review in a PR) or a service; what matters: immutable versions and linking a version to the evaluation results.
- Deployment through a flag or configuration, so that a rollback does not require a code release (ops-release-engineering).

## 6. Typical mistakes
- Ambiguity: "briefly", "professionally" without a measure → give the length, the audience, an example.
- Contradictory instructions after years of patching → a review of the whole, explicit priorities.
- Overloading with constraints: a dozen or so bans; the model starts refusing or suppresses useful content → keep those that,
  as measured by an evaluation, change something.
- A prompt "for the occasion": an instruction added for one case without adding the case to the set.
- Data in the instructions: user content pasted without tags.

## 7. Other providers [unverified]
The general rules (the fixed part at the beginning, examples in a separate block, versioning, evaluations on every release) are
shared; check the details of OpenAI's parameters in the current prompting guide — the page was not available on 2026-10-17.
