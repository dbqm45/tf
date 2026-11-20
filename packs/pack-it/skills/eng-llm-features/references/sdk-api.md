# SDK names and options — checked in package types

Every name below was read from the published package (type definitions or Python sources) on **2026-11-20**.
SDKs in this area release every few days and rename things every few months: pin the version in the lockfile and,
before you write code, check the name in the installed package (`node_modules/<pkg>/*.d.ts`, `site-packages/<pkg>/`)
or the official docs (core-grounding). Model IDs, prices and Messages API parameters: the built-in `claude-api` skill.

## Contents
1. Claude Agent SDK (ready-made agent harness)
2. Vercel AI SDK (agent to assemble)
3. promptfoo (evaluation matrix)
4. Other packages in the same categories

## 1. Claude Agent SDK
Packages: npm `@anthropic-ai/claude-agent-sdk` (0.3.329), PyPI `claude-agent-sdk` (0.2.186).
Entry point: `query({ prompt, options })` (Python: `query(prompt=..., options=ClaudeAgentOptions(...))`),
an async stream of messages ending with a `result` message.

| Need | TypeScript option | Python field | Notes |
|---|---|---|---|
| upper turn limit | `maxTurns` | `max_turns` | result subtype `error_max_turns` when hit |
| dollar budget per run | `maxBudgetUsd` | `max_budget_usd` | result subtype `error_max_budget_usd`; counts spend since this `query()` started |
| structured result | `outputFormat: { type: "json_schema", schema }` | `output_format` | the parsed value in `structured_output`; failure → `error_max_structured_output_retries` |
| built-in tools | `tools: string[]`, `[]` = none, or `{ type: "preset", preset: "claude_code" }` | `tools` | `[]` for a pure evaluator |
| tool permission | `allowedTools`, `permissionMode`, `canUseTool` callback | `allowed_tools`, `permission_mode`, `can_use_tool` | allowlist write tools explicitly |
| system prompt | `systemPrompt: string` or `{ type: "preset", preset: "claude_code", append }` | `system_prompt` | a custom string replaces the harness prompt |
| repo settings and CLAUDE.md | `settingSources: ("user" \| "project" \| "local")[]` | `setting_sources` | omitted = all sources (CLI default); `[]` = isolation; CLAUDE.md loads only with `"project"` |
| skills | `skills: string[] \| "all"` | `skills` | a context filter, not a sandbox: unlisted skill files stay readable on disk |
| own tools | `tool()` + `createSdkMcpServer()` | `@tool` + `create_sdk_mcp_server()` | in-process MCP server |
| sessions | `resume: <session id>`, `forkSession: true` | `resume`, `fork_session` | fork = branch without changing the original |

Result message: `subtype` (`success`, `error_max_turns`, `error_max_budget_usd`, `error_during_execution`,
`error_max_structured_output_retries`), `total_cost_usd` (an estimate, not a billing statement; read the latest result,
do not sum results), `usage`, `modelUsage` (per model — prefer it for token accounting), `num_turns`,
`permission_denials`. The `system`/`init` message carries `apiKeySource` (`ANTHROPIC_API_KEY`, `apiKeyHelper`,
`/login managed key` or `none` for a subscription login) — check it in CI and stop when it is not the key you expect.

The `env` option **replaces** the subprocess environment (it is not merged): spread `process.env` yourself if the
process still needs `PATH`, `HOME` or `ANTHROPIC_API_KEY`.

## 2. Vercel AI SDK
Package: npm `ai` (7.0.177); providers `@ai-sdk/anthropic`, `@ai-sdk/openai`, `@openrouter/ai-sdk-provider` (3.1.0).

- `generateText({ model, prompt | messages, instructions, output, tools, stopWhen, maxOutputTokens, abortSignal, timeout })`
  and `streamText(...)`. Default `stopWhen` for these is `isStepCount(1)` — one step, tools are not looped.
- `ToolLoopAgent` (`new ToolLoopAgent({ model, instructions, tools, stopWhen, output })`, then `.generate()` /
  `.stream()`): default stop condition `isStepCount(20)`. Set your own limit for automation.
- Stop conditions: `isStepCount(n)` (alias `stepCountIs`), `isLoopFinished()` — runs until the model stops calling
  tools; never use it alone in unattended runs.
- Structured output: `output: Output.object({ schema })` (also `Output.array`, `Output.choice`, `Output.json`);
  the value is in `result.output`; a model answer that does not parse throws `NoObjectGeneratedError`.
- Tools: `tool({ description, inputSchema, execute, needsApproval })`; approval can also be set per call (`toolApproval`).
- Telemetry per step: `onStepFinish` / `onStepEnd`; usage in `LanguageModelUsage`: `inputTokens`,
  `inputTokenDetails.{noCacheTokens, cacheReadTokens, cacheWriteTokens}`, `outputTokens`,
  `outputTokenDetails.reasoningTokens`; `finishReason` per step; `totalUsage` on stream results.
- The SDK does not price tokens: multiply by your price list or read the cost the provider reports
  (OpenRouter returns it in provider metadata [unverified for the current version]).

## 3. promptfoo
Package: npm `promptfoo` (0.126.0). Config `promptfooconfig.yaml` with `prompts`, `providers`, `tests`
(each with `vars` and `assert`); run `npx promptfoo eval`, view `npx promptfoo view`.
Assertion types used in this skill: `is-json` / `contains-json` (structure), `javascript` (a hard condition in code),
`llm-rubric` (a judge model with a criterion), `cost`, `latency`. In CI, `PROMPTFOO_PASS_RATE_THRESHOLD` sets the
pass rate below which the run fails (keep 100 unless a lower value is a recorded decision).

## 4. Other packages
- OpenAI Codex SDK: npm `@openai/codex-sdk` (0.171.0) — a ready-made coding agent harness driven from code;
  check option names in its types before use.
- Cloudflare Agents: npm `agents` (0.33.0) — agents as Durable Objects with persistent state, schedules and an HTTP
  address (the "agent as a service" case).
- OpenRouter: the AI SDK provider above gives one API over many model vendors; it adds an intermediary
  to the data path (arch-privacy-compliance).

## Sources
- npm registry and package type definitions: `@anthropic-ai/claude-agent-sdk` 0.3.329 (`sdk.d.ts`), `ai` 7.0.177
  (`dist/index.d.ts`), `promptfoo` 0.126.0, `@openai/codex-sdk` 0.171.0, `agents` 0.33.0,
  `@openrouter/ai-sdk-provider` 3.1.0 — read 2026-11-20.
- PyPI `claude-agent-sdk` 0.2.186 (`types.py`), read 2026-11-20.
- promptfoo documentation, "Configuration" and "Assertions and metrics" (promptfoo.dev/docs, accessed 2026-11-20).
