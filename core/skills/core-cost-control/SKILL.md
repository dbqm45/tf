---
name: core-cost-control
description: Use for choosing a model and for cost — benchmarks, the haiku→sonnet→opus cascade, effort, cache, compaction.
metadata:
  review: "2027-10-09"
  catalog: "Use when you choose a model or effort for a task or an executor, escalate after a failed attempt, plan a long session, compact the context or analyse cost and cache hits — a difficulty rubric, the model cascade with the model parameter of the Agent tool, cost profiles, the advisor, opusplan, cache rules, compaction, a cost report. Not for limiting hallucinations (core-grounding) or the performance of the application itself (the skills from pack-it)."
  keywords: "ile kosztowała praca agentów, koszt w złotówkach, koszt w PLN, statystyki kosztów, drogo czy tanio, koszt, tokeny, tańszy model, drogi model, haiku, sonnet, opus, effort, eskalacja, cache, kompaktowanie, compact, limit, rachunek, oszczędność, profil kosztów, doradca, advisor, opusplan, serwery MCP drogie, dryf kontekstu, przekręca nazwy plików, nowy model, ranking modeli, benchmark, domyślny model, koszt agenta w CI, fork czy subagent, agent teams, wyjście testów i buildu, tysiące linii wyjścia, szum z terminala, hook filtrujący wyjście poleceń, sesje szybko się kompaktują, sesje są drogie, rachunek za agenta wzrósł, przejść na tańszy model, how much did the agents cost, cost statistics, cheaper model, expensive model, escalation, compaction, bill, saving, cost profile, context drift, new model, model ranking, default model, agent cost in CI, terminal noise, sessions are expensive, switch to a cheaper model, kiedy delegowanie się opłaca, delegować czy zrobić samemu, klasa zadania w briefie, koszt delegowania, when delegating pays off, delegate or do it yourself, task class in the brief"
---

# Cost and model choice — the cheapest model that passes verification

Goal: every task is done by the cheapest model that gives a result passing **objective verification** (tests, lint, build,
`grounding_check`, a review). The model does not assess itself "by eye". Whether it was enough is decided by the result
of the check. Only when the check fails do you go one level up.

## 0. Yourself or delegate
By default the main session does the task: it already knows the code and the conversation, and further work in it reads the history from the cache.
A new executor starts from zero — it reads the same files again (a cache write at 1.25× the input price) and gets
only a summary, so it loses agreements. Anthropic: multi-agent systems use about 15× more tokens than a chat,
and code has fewer parts that can really be done in parallel than research (anthropic.com/engineering, 13.06.2025).
You delegate only when the handover pays off: a lot of reading and a short result (`scout`, `researcher`), parts that are really
independent (in parallel), a fresh look (a security review, clean-room tests, a diff review), a
mechanical change with a full specification and a test (`quick-fixer`), a decision that is hard to reverse (analysis on a stronger
model, the execution comes back to the session). You do not split one coherent change between executors.
A fork, a session with a worktree, a subagent or agent teams (and the nesting limit): `references/parallelism.md`.
You start the brief with the line `Class: reading|parallel|review|mechanical|decision|other` — a reason for delegating that
can be measured later (§7).

## 1. Assessing the task before delegating
Answer five questions. The routing table in the persona's prompt gives the starting tier, and the answers move it:

| Question | Yes → | No → |
|---|---|---|
| Will a command check the result (tests, lint, types, build)? | a tier lower | a tier higher or a review |
| Is the change easy to undo (git, no production data)? | a tier lower | a tier higher |
| Does the task require a **decision** (choosing an approach, a trade-off), not only execution? | a tier higher | a tier lower |
| Does it concern security, personal data, money, data migration, architecture? | deep or a deep review | — |
| Does it cover many domains or >5 files without a pattern? | split it into steps | — |

Typically: a mechanical change with a test → `haiku`; a feature in one domain → `sonnet`; an architecture choice, a security
review, a bug without an obvious cause after an attempt → `opus`.

Optionally `python3 .claude/hooks/jev_client.py --tier "<opis zadania>"` (the key TYPESAFE_API_KEY) asks these questions
of the Jev decision model in ~0.1 s for a fraction of a cent. A "NIEPEWNE" (uncertain) suggestion you settle with the rubric yourself.

## 2. The model cascade
- The Agent tool takes a `model` parameter (`haiku`, `sonnet`, `opus`). It overrides the model from the agent's definition for that
  call (and its resumptions).
- **Start:** the cheapest model that has a real chance. **Escalation by one level** when the executor reports a blocker or
  verification does not pass after 2 attempts. Add to the new call what did not work — otherwise the stronger model
  will repeat the same mistake.
- **De-escalation:** after a decision made on `opus` (architecture, a plan) commission the implementation on `sonnet` again, and
  mechanical steps on `haiku`.
- **A signal from the executor:** a report can end with the line `Tier: too low — …` or `Tier: too high — …`. The
  `log_usage` hook records it, and `cost_report.py` sums it up and suggests changing the role's tier. For the next similar task
  choose the right model right away.
- Do not switch the model of the **main session** in the middle of a task (`/model`). Each model has a separate cache, so the next
  turn reads the whole history without a discount. Delegating to an executor on another model does not spoil the session's cache.

## 3. The main session: model, profile, advisor
- **The cost profile** (`python3 .tf/factory/profile.py`) switches the whole team at once:
  - `economy` — without Opus;
  - `balanced` — the default;
  - `quality` — std with effort high and an Opus advisor.

  The profile also changes the session settings: effort, the compaction threshold and the advisor.
- **The advisor** — a cheaper main model calls a stronger one at key moments: before choosing an approach, at
  a recurring error, before announcing the end. **It judges by itself when it needs it.**
  - Typical pairs: Sonnet + an Opus advisor, Haiku + an Opus advisor (Haiku can ask, but cannot advise).
  - Cost: every consultation reads the whole conversation at the advisor's price and without cache. It pays off in long,
    multi-stage tasks, not in short ones.
  - Limitations: only the Anthropic API (not Bedrock, Vertex, Foundry); an experimental feature. Subagents inherit
    the advisor, so in the `quality` profile cheap executors can call it too.
  - Turning on: `/advisor opus`, turning off: `/advisor off`. Switching the advisor does not spoil the cache.
- **`opusplan`** — Opus in plan mode, Sonnet during execution. Every switch of plan mode changes
  the model, so it means a full read without cache. Use it when you plan once and then execute for a long time.
- You choose the model and effort **at the start of the session**.

## 4. Effort (reasoning depth)
Thinking tokens count as output tokens, that is the most expensive.
- `low` — quick exchanges, a rename, a draft;
- `medium` — everyday work with a clear scope (the default for Sonnet 5.5 and Opus 5.5);
- `high` — bugs in existing code, edge cases, verification;
- `xhigh`/`max` — hard problems to solve independently (e.g. looking for vulnerabilities).

The agents' effort follows from the tier (`.tf/config/config.yaml`), and a skill can set its own with the `effort` field. On most
models changing effort during a session also clears the cache; the exception: Opus 5.5, Sonnet 5.5, Haiku 5.5 and Fable 5.1 through
the Anthropic API or a subscription. One hard turn: `ultrathink` in the text of the instruction instead of changing the session's effort;
`ultracode` is the orchestration of a multi-agent workflow, not an effort level (`references/model-and-automation.md` §8).

## 5. Cache — what spoils it and what does not
The cache works automatically and matches the **beginning** of a request. A cache read costs 10% of the input price, and on
Opus 5.5 and Sonnet 5.5 — 5%, on Fable 5.1 — 2.5% (platform.claude.com, prompt caching, as of 2026-10-17).

| Clears the cache (the next turn costs more) | Does not clear it |
|---|---|
| a model change (`/model`, `opusplan`, a skill with a `model` field) | editing files, also CLAUDE.md (effective from `/clear`) |
| an effort change (most models) | calling a skill, the permission mode, the answer style |
| adding or removing an MCP server (when the tools load right away) | running a subagent, `/rewind`, `/recap` |
| blocking a whole tool with a deny rule | turning the advisor on or off |
| `/compact`, a Claude Code update, many images | |

Practice:
- A break longer than the cache lifetime (5 min, in a subscription the main conversation 1 h) means that the next turn reads
  everything again. After a long break come back from a checkpoint in a new session, instead of resuming a long history.
- Subagents have a 5-minute cache. Run independent commissions together, not with long breaks.
- Abandon a failed path with `/rewind`, not `/compact`: undoing hits the existing cache.
- Do not switch MCP servers in the middle of a task.

## 6. Context and compaction
- The factory sets `autoCompactWindow: 200000`. Without it models with a 1 M window compact only at ~967 thousand
  tokens. Before that every turn reads an ever longer history, and quality drops (core-grounding).
- Run `/compact <co zachować>` at the boundary of tasks, not in the middle. Save a checkpoint first
  (core-project-record).
- After compaction the content of every skill used comes back, but at most ~5000 tokens. That is why SKILL.md is to be short,
  and you keep details in `references/` (`build.py check` warns).
- A task unrelated to the previous one you start with `/clear`.
- Exploration and long outputs (tests, logs, documentation) go to a subagent. Only the report comes back to the main session.
- **Terminal noise:** first "errors only" reporters (`--reporter=dot`, `pytest -q`, `--silent`) and a log to a file
  read in fragments; a hook that filters every command is foreign code with access to everything (`skill_audit`, the human's
  consent). You measure the effect by the cost per successful task, not by the number of tokens.
- **MCP servers cost in every turn:** every connected server adds the definitions of all its tools to
  every request. Connect only the servers needed in this project, choose ones with a small number of universal
  tools (the "search + execute" pattern), and when it is known which command to run — a CLI instead of MCP. Jira,
  Confluence and APIs with a token through a script instead of MCP tools: core-api-scripts.
- A broad repo scan (git history, a dependency graph, an inventory) you commission to a cheaper model, and the heavy work is done by a CLI
  outside the context; a strong model only to deepen one flow. Packing the whole repo into one file is an ad hoc
  look at foreign code, not a standing practice.
- **Context drift — signals for a fresh session:** the agent repeats rejected fixes, mangles file names, "remembers"
  decisions that never happened, mixes in a data model from another change or phase. Do not tell it to "fix it once more": save
  a checkpoint, open a new session, load the plan and its progress, start the phase from the beginning. Quality drops with the length of the
  input before the window fills up — that is why phases with commits and a plan in a file, not an ever longer conversation.
- Between plan phases you propose to the human: continue in this session / a fresh context (with a ready instruction to
  resume from phase N) / a review of this phase first.

## 7. Measurement
**Diagnosis before leverage:** before you change the model, establish whether the problem concerns the context (files read in full
many times, input:output ~100:1, low cache hits), the model (failures of a class of tasks despite good context) or
the measurement (tokens estimated from characters) — `references/model-and-automation.md` §6.

- **The status line** (`.claude/hooks/statusline.py`): the model, effort, context fill, cache hits (with the note
  "cold" when the cache expired), the session's cost, limits. It uses no model tokens.
- `/usage` — the session's cache hits and the likely cause of the last miss.
- Cost reports from logs (`.tf/factory/cost_report.py`, `.tf/factory/cost_stats.py`) — commands and options:
  `references/model-and-automation.md` §7; the causes of a stage's cost are assessed by core-agent-retro.

## 8. Assessing a new model (before you change the default)
- **You do not compare results from different reports directly.** A result in a ranking is a task set + a metric + a protocol (a fixed
  or free harness, a step limit); without these three the number says nothing,
  and the same model in another harness comes out clearly different.
- Agentic work requires repeatability in every attempt (pass^k), not "at least once" (pass@1): 90% per step is about 59%
  for five steps in a row (0.9⁵).
- You compare **the cost of a solved task** (tokens × iterations + review time), not the price of a token — a cheap model
  that needs three rounds of fixes is more expensive.
- Your own test decides: 3–5 real project tasks with the same verification (tests, build), for agents in code —
  an evaluation set (pack-it: eng-llm-features §8). A review of news in models about every 2 weeks, not daily.
Details and an instruction for a reasoning model: `references/model-and-automation.md` §1.

## 9. Agents in automation (CI, a schedule, your own agent)
- You run them on an event that matters (a PR, a red build, a new issue), never "in a loop just in
  case" — the cost multiplies by the number of events.
- A hard limit per run: the number of turns **and** a budget in dollars (`claude -p … --max-budget-usd`, in the SDK a budget option;
  names: eng-llm-features from pack-it). An evaluator agent without tools, 1–2 turns.
- A model per role: triage and labels with the cheapest; reasoning about code with a medium one; an expensive one only for critical paths.
- The cost from the result of every run to a table or a dashboard: per PR, per triage level, per week.
- Company code in automation → an API key from a secret, not a developer's subscription login (different data and billing terms).
Details: `references/model-and-automation.md` §2–3; the contract of unsupervised work: core-async-delegation.

## Example
Escalation `sonnet` → `opus` after two failed fixes of a flaky test and the implementation going back to `sonnet`:
`references/examples.md` §2; the other examples are there too.

## Checklist
- [ ] the tier chosen with the rubric (checkability, reversibility, decision, risk, scope), not out of habit
- [ ] start from the cheapest sensible model; escalation after a blocker or 2 failed verifications, with a description of the failure
- [ ] after a decision on opus the implementation goes back to sonnet/haiku
- [ ] the session's model and effort set at the start; no `/model` in the middle of a task
- [ ] `/compact` at the boundary of tasks after a checkpoint; `/rewind` to abandon a failed path
- [ ] the cost checked in the status line or `cost_report.py`
- [ ] only the MCP servers needed; on drift signals a new session from the checkpoint
- [ ] a new model assessed with your own test and the cost of a solved task; an agent in automation with a turn limit and a budget

## Sources
- Anthropic, Claude Code documentation (as of 2026-10-03):
  - "How Claude Code uses prompt caching";
  - "Model configuration" (opusplan, effort, autoCompactWindow);
  - "Subagents" (the `model` field, the `model` parameter of the Agent tool, the model selection order);
  - "Skills" (the `model`, `effort`, `context: fork` fields);
  - "Escalate hard decisions with the advisor tool";
  - "Manage costs effectively";
  - "Customize your status line".
- Anthropic, API pricing (platform.claude.com, 2026-10-03): input/output Haiku 4.5 $1/$5, Sonnet 5.5 $2/$10,
  Opus 5.5 $4/$20 per 1 M tokens; a cache read $0.10–0.20.

- The 10xDevs course, ed. 3 (2026): prework 3.5 (model rankings), module 1 lesson 5 (the cost of MCP), module 2 lesson 4 (context
  drift), module 4 lessons 1–2 (a broad repo scan), module 5 lessons 2–3 (agents in automation) — training
  material (accessed 2026-10-09).
- `claude --help`, Claude Code 2.1.296 (2026-10-10): `--max-budget-usd` works only with `--print`.

Described in our own words.
