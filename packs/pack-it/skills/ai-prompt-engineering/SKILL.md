---
name: ai-prompt-engineering
description: Use for writing and improving prompts — structure, XML tags, few-shot examples, thinking, long context, templates and versions, a cache-friendly layout, model migration.
metadata:
  review: "2027-04-17"
  catalog: "Use when you write, improve or port a system prompt or a prompt template for a model — structure (role, context, task, constraints, output format, examples), XML tags, choosing few-shot examples, chain of thought and extended or adaptive thinking and when not to use it, prefill and structured outputs, the layout of a long context (documents at the top, the question at the end), templates and prompt versioning (a registry), a cache-friendly layout (a fixed prefix), prompt regression through evaluations, migrating a prompt to a newer model, typical mistakes (ambiguity, contradictory instructions, excessive constraints). Not for the output contract, the SDK and the tool loop (eng-llm-features), building sets and graders (ai-evals), cache rules and model choice (core-cost-control) or instructions for the coding agent (core-agent-instructions)."
  keywords: "prompt, prompt systemowy, prompt engineering, inżynieria promptów, few-shot, przykłady w prompcie, tagi xml, chain of thought, łańcuch myślenia, extended thinking, adaptive thinking, prefill, długi kontekst, szablon promptu, wersjonowanie promptów, rejestr promptów, prompt caching, stały prefiks, migracja promptu, model ignoruje instrukcję, sprzeczne instrukcje, poprawić prompt, system prompt, examples in the prompt, xml tags, long context, prompt template, prompt versioning, prompt registry, fixed prefix, prompt migration, the model ignores an instruction, contradictory instructions, improve the prompt"
---

# Prompt engineering

A prompt is code with a nondeterministic executor: you change it with a hypothesis and check it with a measurement. Before you start,
have a success criterion and a way to check it (`ai-evals`); without it an "improvement" is an impression. Not every failure
is a prompt problem — sometimes a change of the model, the output schema or the tool helps (**eng-llm-features**, the output
contract and the SDK). You check the names of models and API parameters in the provider's documentation (core-grounding); for Claude:
the `claude-api` skill built into Claude Code (Anthropic updates it). The state of 2026-10-20 and the details: `references/techniques-and-migration.md`.

## Procedure
1. **Diagnose what breaks** on 5–10 concrete bad outputs: wrong content, a wrong format, a skipped instruction,
   overeagerness, a hallucination. Each symptom has a different fix (the table below). Without examples of failures do not start.
2. **Lay out the structure** (the order from fixed to variable): the role and the goal → the context (why) → the task → the constraints
   → the output format → examples → the input data. A role in one sentence is enough. An instruction with a reason ("do not use
   an ellipsis, because the text is read by a speech synthesizer") works better than a bare ban.
3. **Separate the parts with XML tags** when the prompt mixes instructions, context, examples and data: `<instructions>`,
   `<context>`, `<example>` in `<examples>`, `<document>`. Consistent tag names across the whole prompt; user data always in a tag,
   so that the model does not take it for instructions (core-agent-security).
4. **Say what should be, not what should not.** Instead of "no markdown" → "the answer in plain paragraphs". A concrete
   output format with a description; when code reads the result, use structured outputs with a schema, not a request in the prompt.
5. **Examples (few-shot):** 3–5, **relevant** (like real inputs), **diverse** (including edge ones, so that the model does not
   pick up an unintended pattern), in `<example>` tags. An example sets the pattern very strongly — if all of them
   start the same way, so will the answers. Take the examples for the prompt from a pool disjoint from the evaluation set.
6. **Thinking.** Multi-step tasks, mathematics, analysis: turn on the model's thinking (adaptive, steered by the `effort`
   parameter; older models: extended with a budget) or ask for reasoning before the answer and the result in a separate
   `<answer>` tag. **Do not use it** for simple extraction, classification and formatting — it adds cost and latency
   without gain; check with an evaluation whether it improves the result.
7. **Long context (20 thousand tokens and more):** documents at the top, each in `<document>` with `<source>`; the instructions and
   the question **at the end**; with dense documents ask first for the quotes relevant to the question to be listed.
8. **A layout for the cache:** the fixed part (instructions, tools, examples, documents) at the beginning, the variable one (the date, user
   data, the question) at the end. The cache matches on the exact prefix in the order tools → system → messages;
   a timestamp or a user identifier in the prefix zeroes the hits. Rules, minimum lengths and prices: core-cost-control and `references/techniques-and-migration.md`.
9. **Templates and versions.** The prompt in a file or a registry, not glued together from strings across the code: a template with named
   variables, a version (SemVer or a date), a change description, a pinned model. You always run a version change through the regression
   set (`ai-evals`); the lifecycle in production: ai-mlops.
10. **One change at a time.** Change one thing, run the evaluation on the same cases, compare with the previous
    version; record the result in the change description. A prompt + model change at once does not tell what worked.
11. **Migrating to a newer model:** read the provider's migration guide, run the old prompt on the new model **without
    changes** and measure; remove the workarounds (prefill, aggressive CRITICAL/MUST, a manual thinking budget, requests for "more effort"),
    because newer models follow the prompt more strongly and tend to be overeager; only then tuning.

## Symptom → fix
| Symptom | Usual cause | Fix |
|---|---|---|
| ignores an instruction | gets lost in a long prompt, a contradiction | move it to the beginning or the end, remove the conflict, give a reason |
| a variable format | a description instead of a schema | structured outputs or an example |
| too literal / too eager | bans, capital letters, "always" | a normal tone, a reason instead of pressure |
| answers like the examples | one pattern in the examples | diversify, reduce the number |
| loses details in documents | the question at the top, no tags | documents at the top, the question at the end, quotes |
| slow and expensive | thinking on a simple task | first a cheaper model and a lower effort, then the prompt |
| a confident answer without basis | pressure to always answer | allow "I don't know", quotes before conclusions (core-grounding) |
| a minimal, "generic" result | a general request; new models do exactly what was asked | write the scope and the ambition explicitly ("a full version, going beyond the basics") |
| two instructions exclude each other | the prompt grew over years | explicit priorities or remove one |

## Example
**Input:** a ticket classification prompt, 1,800 tokens, the date and the customer's first name in the first line, "YOU MUST ALWAYS
return JSON", 30 wrong labels out of 200 cases, the cache does not hit.
**Result:**
- a fixed prefix (instructions, 4 diverse `<example>`, category definitions) at the beginning; the date and `<ticket>` with the ticket content at the end → the cache works;
- `YOU MUST ALWAYS JSON` → structured outputs with a schema (an enum of categories); in the prompt one sentence about the edge categories with a reason;
- no thinking (classification), a cheaper model; the version `ticket-classifier@1.3.0`, a change description;
- an evaluation of 200 cases before and after: 170/200 → 186/200 (85% → 93%); the regression set without new failures.

## Checklist
- [ ] a success criterion and a set of cases before the change; symptoms described with examples
- [ ] structure: role, context with a reason, task, constraints stated positively, format, 3–5 diverse examples
- [ ] data and documents in XML tags; long context: documents at the top, the question at the end
- [ ] thinking only where the evaluation shows a gain; the output format through a schema, not prefill
- [ ] the fixed prefix at the beginning, variables at the end; no time and identifiers in the prefix
- [ ] a template with a version, a pinned model, the change run through the evaluations, one change at a time
- [ ] migration: the old prompt unchanged on the new model, workarounds removed, only then tuning

## Sources
- Anthropic, "Prompting best practices" (platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices, read 2026-10-17):
  3–5 examples, relevant and diverse in `<example>`; XML tags; documents at the top, the question at the end (up to approx. 30% improvement in tests); adaptive thinking and `effort`; prefill on the last turn unsupported since the 4.6 models; softening aggressive language.
- Anthropic, "Prompt engineering overview" (the same domain, read 2026-10-17): success criteria and evaluations before prompting.
- Anthropic, "Prompting Claude Opus 5.5", "… Sonnet 5.5", "… Haiku 5.5", "Reduce hallucinations", "Increase output
  consistency" (platform.claude.com, read 2026-10-20): effort and `max_tokens` in the 5.5 models, the agent ending work
  early, the right to "I don't know", structured outputs instead of a request for a format.
- Anthropic, "Prompt caching" (platform.claude.com/docs/en/build-with-claude/prompt-caching, read 2026-10-17): the prefix order, TTL 5 min and 1 hour, invalidation.
- OpenAI, the prompting guide (developers.openai.com/api/docs/guides/prompting) — search results from 2026-10-17: the role in the system message, examples in blocks, the cache by prefix; the page was not opened directly [unverified]. Pinning the model version — a recommendation known from a second source [unverified].

Described in our own words.
