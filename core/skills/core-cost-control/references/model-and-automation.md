# Assessing a new model, context and agents in automation

> **Contents:** 1. Assessing a new model · 2. Agents in automation — cost · 3. Authentication versus the bill and data · 4. Context — MCP, drift, a repo scan · 5. Example: a decision to change the model · 6. Diagnosis before leverage · 7. Cost reports · 8. `ultrathink` and `ultracode` in Claude Code

## 1. Assessing a new model
**How to read a ranking.** A number in the table = a task set + a metric + a protocol (the harness, a step limit, the number of attempts).
Before you compare it, check all three:
- **the set** — does it measure your type of work (fixing a reported bug ≠ building a new feature ≠ working in a terminal);
  older sets saturate, and the results may reflect tasks memorised from training data;
- **the metric** — pass@1 ("it worked at the first attempt") overstates the reliability of a loop. An agent performs steps
  one after another, so repeatability counts: at 90% per step five steps in a row succeed in about 59% (0.9⁵),
  ten — in about 35%;
- **the protocol** — the same model in different harnesses (other tools, system prompt, instructions file) can
  differ by a dozen or so points; some positions in rankings are harnesses tuned for the benchmark itself.
  With each result write down whether the harness was **fixed** (the same for all models) or **free** (tuned
  for the model), plus the model version and inference settings — without that the numbers are not comparable. In one preprint
  the harness alone, fitted to the model, raised the result from 29% to 78% without changing the weights (Yu et al., arXiv:2609.09134, v1
  8.09.2026, after J. Wasowski's write-up, about 12.10.2026; a single study [unverified]).

**How to decide.**
1. The candidate must pass the same test as the current model: 3–5 real project tasks (from the issue history),
   the same verification (tests, build, `grounding_check`), preferably several repetitions.
2. You count **the cost of a solved task**: input and output tokens × the number of iterations until green verification +
   the human's review time. A cheaper token with two extra rounds of fixes is a more expensive task.
3. For agents built in code (a reviewer in CI, triage) — a matrix of cases × models in the evaluation set
   (pack-it: eng-llm-features §8), also after a harness change with the same model.
4. You record a change of the team's default model with the test result (the cost profile, `.tf/config/config.yaml`), not
   from an announcement's headline. A review of news about every 2 weeks is enough.

**An instruction for a reasoning model:** the goal + hard constraints + a measurable success criterion. Do not impose thinking
steps or an example solution — unless the process is mandatory (data migration, payments,
security) or the model misses after 1–2 attempts; then ask for 2–3 approaches to choose from.

## 2. Agents in automation — cost
| Lever | Rule |
|---|---|
| trigger | an event that matters (a PR opened, a red build, a new issue); a path filter or a label, so a PR with documentation alone does not pay for a review |
| triage before the agent | a cheap step (the number and paths of files, the diff size, labels) assigns a risk level: low → a fast cheap run, critical paths → a stronger model and always a human |
| run limit | the number of turns **and** a budget in dollars; a loop without an upper step limit is forbidden |
| tools | an evaluator without tools (1–2 turns); every added tool means more turns and tokens |
| input | lockfiles, generated code and dumps filtered out of the diff — cost and noise |
| model per role | triage/labels — the cheapest; reasoning about code — a medium one; an expensive one only for critical paths |
| measurement | the cost, turns and time from the result of every run to a table or a dashboard: per PR, per triage level, per week |
| feedback loop | every month: where the human only rubber-stamped the verdict (the triage can be loosened), where a bug got through a green review (a new case in the evaluation) |

Running from the command line: `claude -p "<zadanie>" --max-budget-usd <kwota> --allowedTools "<lista>"`
(the budget works only with `--print`). Check the turn limit in the CLI and in CI actions in the documentation of your version
[`--max-turns` is not listed in `claude --help` 2.1.296 — unverified]. The SDK option names:
`.claude/skills/eng-llm-features/references/sdk-api.md`.

## 3. Authentication versus the bill and data
- **An API key** (commercial terms, billing per token) — the default choice for company code and every automation.
- **A subscription login** — the SDK and `claude -p` can silently use the developer's login when there is no key. Then
  consumer terms apply (different default training and retention settings) and the plan's limits; programmatic use
  on subscription plans is sometimes counted from a separate pool [unverified — check the current terms and pricing
  before rollout].
- In CI you set the key from a secret explicitly and check that the run uses it (no silent fallback to the login).

## 4. Context — MCP, drift, a repo scan
- **MCP:** the tool definitions of every connected server go into every request. A server with dozens
  of tools costs even when you do not use it. Choose servers with a few universal tools (search for
  an operation + execute), turn off unused ones before the session (not during it — that clears the cache), and operations with a known
  command do through a CLI (explicit, they stay in the history).
- **Context drift** (symptoms in `SKILL.md` §6): the middle of a long input gets less attention, and similar but
  irrelevant fragments act as distractors — that is why quality drops before the window fills up. The reaction: a
  checkpoint (core-project-record) → a new session → the plan and progress → the phase from the beginning. Two failed fixes of the same
  bug are also a signal for a fresh context (core-grounding).
- **A broad repo scan:** an inventory, git history, a dependency graph are collected by a script or a CLI, and a cheap model summarises
  the result; a strong model gets a condensed report and deepens one flow (a code map, pack-it: eng-codebase-mapping).

## 5. Example: a decision to change the model
**Situation:** a new model has 5 points more in a public ranking; the team wants to switch to it for the agents in CI.

**How:**
1. The ranking: the set concerns fixing issues, and the agent in CI does a PR review — a different type of work.
2. The test: 5 closed PRs from the history (2 with a bug found later by a human, 3 clean) × the current and the new model,
   3 repetitions each; the reviewer's evaluation set with assertions.
3. The result: the new model catches both bugs in 3/3 repetitions (the current one in 2/3), but gives 1 false alarm on a clean PR
   and uses 40% more tokens per run.

**Result:**
```
Decision: the new model only for PRs with the triage level "critical" (auth, payments, migrations);
the rest stays on the current one. The cost per PR measured for 2 weeks, then a review of the decision.
The false alarm → a new case in the evaluation set and refined review criteria.
```

## 6. Diagnosis before leverage
Before you change the model, establish which problem you have:
- *context*: the same files read in full several times, an input to output token ratio of about 100:1 and more,
  frequent compaction, low cache hits despite a fixed prompt, the agent rediscovers every session who owns
  what → context engineering (SKILL.md §5–6), not a cheaper model;
- *model*: a high failure rate for a class of tasks despite good context, many turns until the first correct edit →
  a model change, checked as in SKILL.md §8;
- *measurement*: a subscription instead of the API, a benchmark instead of production, tokens estimated from characters → first the
  vendor's counters.
The cache lowers the price of a repeated prefix, but does not take the content out of the window — context rot stays.

Source: J. Wąsowski, "Your Claude Code Bill Demystified" (2026-10-09); the thresholds are the author's examples [unverified].

## 7. Cost reports
- `python3 .tf/factory/cost_report.py --days 7` — the cost per agent and model, escalations, `Tier:` signals and recommendations
  to change the roles' tiers.
- `python3 .tf/factory/cost_report.py --delegation` — the cost of executors by the class from the brief (the `log_usage` hook records every
  Agent call in `.tf/logs/delegation.jsonl`). An expensive class with a short report → do such tasks yourself.
- `python3 .tf/factory/cost_stats.py` (`--period day|week|month`) — tokens, the share of models, the cost in USD and PLN (the NBP
  average rate), changes in git and a "cheap / typical / expensive" band against the median of previous periods; gaps in the logs are marked
  "incomplete data". The causes of a stage's cost and the executors' tiers are assessed by the agent retrospective (core-agent-retro).

## 8. `ultrathink` and `ultracode` in Claude Code
- **`ultrathink`** in the text of an instruction asks for deeper reasoning **in this one turn** and does not change the saved
  effort of the session. In the terminal the word can raise the turn to `xhigh` (it is then highlighted in rainbow colours; Claude Code
  ≥ 2.1.311). It will not raise the turn when `CLAUDE_CODE_EFFORT_LEVEL` or the `maxEffortLevel`/organisation limit is below
  `xhigh`, or on Amazon Bedrock — there you set the effort. Other phrases ("think hard") are plain text.
  `CLAUDE_CODE_DISABLE_ULTRATHINK` turns it off.
- **`ultracode`** is a setting, not an effort level: Claude orchestrates **dynamic workflows** (many agents)
  for tasks that need it, at the current effort level. Turning on: `/effort ultracode` (turning off
  `/effort ultracode off`), `"ultracode": true` in the settings or `claude --effort ultracode` — only the flag
  and the Agent SDK value set the effort to `xhigh` at the same time. Unavailable when workflows are turned off or the model does not
  support `xhigh`. Cost: many agents are many separate contexts (subagents have their own 5-minute cache),
  so you turn it on for tasks that pay off to split, not permanently.
- **When which:** one hard turn → `ultrathink`; a whole hard session → effort set at the start; a task to
  split across many executors → `ultracode` or explicit delegation (§2, `parallelism.md`).
- Changing effort during a session: on most models the next request reads the whole history without cache. On Opus 5.5,
  Sonnet 5.5, Haiku 5.5 and Fable 5.1 through the API or a subscription the cache stays (not on Bedrock, Agent Platform, the
  Claude apps gateway or with `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS`).

Sources (checked 2026-11-01): code.claude.com/docs/en/model-config ("ultrathink keyword", "Ultracode"),
code.claude.com/docs/en/prompt-caching ("Changing effort level"); the anthropics/claude-code CHANGELOG up to 2.1.316.
