---
name: core-cost-control
description: Use when choosing a model or effort, deciding whether to delegate, escalating after a failure, or when token cost, cache, context or compaction is the concern.
metadata:
  review: "2027-11-20"
  catalog: "Use when you pick the cheapest model and effort that will pass objective verification, decide whether to do the work in the main session or delegate it (and in which form: subagent, fork, worktree session, agent teams), escalate one level after failed verification, protect the prompt cache, keep context and compaction under control, cut MCP and terminal-output cost, assess a new model before switching, bound agents in CI and schedules, and read cost reports and statistics. Not for invented facts and verification of claims (core-grounding), application or database performance (pack-it skills such as be-database) or handing work to unattended agents (core-async-delegation)."
  keywords: "koszt, koszty, rachunek, rachunek za Claude, drogo, tańszy model, tańszy, oszczędzać tokeny, tokeny, który model, wybór modelu, haiku, sonnet, opus, effort, wysiłek, eskalacja, po dwóch próbach, delegować czy samemu, delegowanie, subagent, wykonawca, Klasa:, Tier: za niski, cache, przełączam /model, /model w połowie sesji, kompakcja, /compact, /clear, /rewind, kontekst, dryf kontekstu, przekręca nazwy plików, wraca do odrzuconych poprawek, MCP, serwery MCP, definicje narzędzi, mcp-runner, fork, worktree, agent teams, advisor, doradca, opusplan, ultrathink, ultracode, xhigh, profil economy, profil quality, cost_report, cost_stats, złotówki, PLN, NBP, ile kosztowało, koszt tygodnia, nowy model w rankingu, publiczny ranking, ranking programowania, punktów więcej w rankingu, przestawić model domyślny, domyślny model dla zespołu, model w CI, benchmark, benchmark agentowy, wyniki porównywalne, przejść na nowy model, harness, szum z terminala, wyjście testów tysiące linii, hook filtrujący, agent w CI, budżet, max-budget-usd, klucz API, subskrypcja, cost, bill, cheaper model, which model, escalate, delegate or do it yourself, prompt cache, compaction, context drift, MCP cost, leaderboard, new model, CI agent cost, token usage"
---

# Cost control - the cheapest setup that passes verification

Principle: use the cheapest model and effort whose output passes an **objective check** (tests, lint, build, type check,
grounding check, independent review). "Looks fine" is not a check. Step up only when the check fails.

## 0. Do it yourself or delegate
Default: the main session does the work. It already holds the code it read and the agreements from the conversation, and
later turns read that history from the cache. A new executor starts cold: it re-reads files (a cache write costs about
1.25x the input price) and gets only your summary, losing agreements. Multi-agent runs used about 15x the tokens of a chat
in Anthropic's research system; code has fewer truly parallel pieces than research.

Delegate only when one of these holds:
- **reading**: a lot to read, a short result (`scout`, `researcher`);
- **parallel**: parts that are genuinely independent;
- **review**: a fresh, unbiased look is the point (security review, clean-room tests, diff review);
- **mechanical**: a fully specified change with a test (`quick-fixer` on a cheap model);
- **decision**: a hard-to-reverse choice analysed on a stronger model, execution returns to the session.
Never split one coherent change across executors.

Every executor brief starts with `Class: reading|parallel|review|mechanical|decision|other` (the hook also accepts the
Polish `Klasa:`; an unknown word is logged as `other`). The `log_usage` hook records it in
`.tf/logs/delegation.jsonl`; `python3 .tf/factory/cost_report.py --delegation` shows cost per class. A costly class that
returns short reports is a signal to do that work yourself. Forms of delegation and their costs (fork, worktree session,
subagent, agent teams, nesting limits): `references/parallelism.md`.

## 1. Assess the task
Five questions:
1. Can a command check the result? Yes -> a lower tier is enough; no -> higher tier or a review.
2. Is it easy to undo? Yes -> lower; no -> higher.
3. Does it need a decision or trade-off? Yes -> higher; no -> lower.
4. Security, personal data, money, data migration or architecture? -> deep tier or a deep review.
5. Many domains or more than 5 files without a common pattern? -> split into steps first.

Typical mapping: mechanical change with a test -> haiku; a feature within one domain -> sonnet; architecture, security review,
a bug still unexplained after one attempt -> opus. Optional: `python3 .claude/hooks/jev_client.py --tier "<task description>"`
(needs `TYPESAFE_API_KEY`); an "uncertain" verdict is settled by the five questions.

## 2. Cascade and escalation
- The Agent tool's `model` parameter (`haiku|sonnet|opus`) overrides the agent definition for that call and its resumptions.
- Start with the cheapest model that has a real chance. Escalate **one level** when the executor reports a blocker or after
  **2 failed verifications**, and pass on what failed. After the decision work, go back down (implementation to sonnet,
  mechanical work to haiku).
- Executors may end their report with `Tier: too low — <reason>` or `Tier: too high — <reason>`; the hook logs it and the
  cost report suggests tier changes per role (`.tf/config/config.yaml`).
- Do not switch the main session's model mid-task with `/model`: every model has its own cache, so the next turn re-reads the
  whole history at full price. Delegating a step to another model does not touch the session's cache.

## 3. Main-session settings
- Choose model and effort **at the start** of a session.
- Profiles switch the whole team at once: `python3 .tf/factory/profile.py economy|balanced|quality` (`--dry-run` to preview;
  balanced is the default). Economy has no Opus; quality raises effort and adds an Opus advisor. A profile also changes
  effort, the compaction threshold and the advisor.
- **Advisor** (`/advisor opus`, `/advisor off`): a cheaper main model consults a stronger one at key moments (before choosing
  an approach, on a repeated error, before declaring done). Each consultation reads the whole conversation at the advisor's
  price without cache, so it pays off in long multi-stage work. Toggling the advisor keeps the cache. Experimental, Anthropic
  API only; subagents inherit it.
- **`opusplan`**: Opus in plan mode, Sonnet for execution. Every switch of mode is a model switch with an uncached re-read -
  worth it when you plan once and then execute for long.
- **Effort**: thinking tokens are billed as output, the most expensive kind. low - quick exchanges, renames, drafts; medium -
  everyday work (default for Sonnet 5.5 and Opus 5.5); high - bugs in existing code, edge cases, verification; xhigh/max -
  hard independent problems. Executors get effort from the tier config. On most models a mid-session effort change clears the
  cache; with an API key or subscription it is kept on Opus 5.5, Sonnet 5.5, Haiku 5.5 and Fable 5.1+ (not on Bedrock, Agent
  Platform, a Claude apps gateway, or with `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS`).
- **`ultrathink`** in a prompt deepens reasoning for that one turn without changing the stored effort
  (`CLAUDE_CODE_DISABLE_ULTRATHINK` turns it off). **`ultracode`** is a setting, not an effort level: Claude orchestrates
  multi-agent workflows for substantive tasks (`/effort ultracode`, `"ultracode": true`, or `--effort ultracode`, which also
  sets xhigh). It spends many contexts, each subagent with a 5-minute cache. Details: `references/model-and-automation.md`
  section 5.

## 4. Cache
- Automatic; it matches the beginning of a request. Reading from cache costs a fraction of input (per `.tf/factory/config.yaml`
  prices: 10% on haiku, 5% on sonnet and opus, 2.5% on fable); writing costs about 1.25x input for the 5-minute lifetime.
- **Clears the cache**: a model change (`/model`, `opusplan`, a skill's `model` field), an effort change on most models,
  adding or removing an MCP server when tools load upfront, denying a whole tool, `/compact`, a Claude Code upgrade, many images.
- **Keeps the cache**: file edits (CLAUDE.md takes effect at `/clear`), skill calls, permission mode, output style, running
  subagents, `/rewind`, `/recap`, toggling the advisor.
- Lifetime: 5 minutes; the main conversation on a subscription gets 1 hour. After a longer break the next turn re-reads
  everything - after long breaks resume from a checkpoint (core-project-record) in a new session. Subagents have a 5-minute
  cache, so launch independent briefs together. Abandon a failed path with `/rewind`, not `/compact`. Do not swap MCP servers
  mid-task.

## 5. Context, compaction, MCP, terminal output
- The factory sets `autoCompactWindow: 200000`; without it 1M-window models compact only near the limit, and quality drops
  well before that. `/compact <what to keep>` at task boundaries after a checkpoint; `/clear` for an unrelated task. After
  compaction each used skill is re-attached up to about 5000 tokens.
- **Context drift** - the agent repeats rejected fixes, mangles file names, "remembers" decisions never made: write a
  checkpoint, start a new session, load the plan and progress, restart the phase. Attention to the middle of a long input
  degrades; the cache lowers the price, not the clutter. Between plan phases offer: continue / fresh context with a resume
  instruction / review first. Fact-checking itself is core-grounding.
- **MCP costs twice**: tool definitions travel with every request (tool search loads them on demand) and results stay in the
  history. So the main session does not call MCP: the `mcp-runner` agent on a cheap model does, with a fields filter and a
  call budget, in the background when the work can go on (`run_in_background`); it keeps large results in its own context or
  `.tf/cache/mcp/` and returns a short answer. Read once: a result already saved (`ticket.md`, a cache file) is not
  fetched again. Connect only the servers you need, prefer a few general tools
  (search + execute) over dozens of narrow ones, and use a CLI when the command is known.
- **Terminal output**: quiet reporters first (`pytest -q`, a dot reporter, `--silent`, errors only); write long logs to a file
  and read fragments (`tail`, `grep`). A hook that filters every command is foreign code with full access: audit it and get the
  human's consent. Measure the effect as cost per successful task, not raw token count.
- **Broad repository scans**: a script or a cheap model collects the inventory, history and dependency graph; a strong model
  deepens one flow.

## 6. Measuring
- Diagnose before changing the model. **Context problem**: the same files read in full again and again, input far larger than
  output, low cache-hit rate, frequent compaction -> fix context, not model. **Model problem**: a high failure rate in one task
  class despite good context, many turns to the first correct edit -> change the tier per section 1. **Measurement problem**:
  subscription numbers instead of API data, benchmark instead of production, tokens estimated from characters -> use the
  vendor's counters first.
- One session: run `/usage` rather than estimating - session cost, the `Prompt cache (main)` line and, on subscription plans,
  attribution to skills, subagents, plugins and MCP servers with recommendations (code.claude.com/docs/en/costs). The status
  line (`.claude/hooks/statusline.py`) keeps model, context, cache and cost in view without model tokens. `claude -p
  --output-format json` returns `total_cost_usd` (`tf work` records it per run).
- Across sessions, per task class, over time (what `/usage` does not give): `python3 .tf/factory/cost_report.py --days 7`, `--delegation`; `python3 .tf/factory/cost_stats.py --period
  day|week|month` (USD and PLN at the NBP average rate, a cheap/typical/expensive band against the median of earlier periods,
  an "incomplete data" marker). No logs -> say what is missing; never invent a number.
- New model, agents in CI and schedules, authentication versus the bill: `references/model-and-automation.md`.

## Example
Rename a field across 12 files, module tests cover it -> `Class: mechanical`, `quick-fixer` with `model: haiku`. Check:
module tests + type check. Two failed attempts -> one level up to sonnet with both failure outputs in the brief. More
worked cases (escalating a flaky test diagnosis to opus and back, reading a costly week from the cost report):
`references/examples.md`.

## Sources
- Claude Code docs, "Prompt caching", code.claude.com/docs/en/prompt-caching - accessed 2026-11-20 (what invalidates the cache, effort exceptions, lifetimes).
- Claude Code docs, "Model configuration", code.claude.com/docs/en/model-config - accessed 2026-11-20 (effort, `ultrathink`, `ultracode`, `opusplan`).
- Claude Code docs, "Manage costs effectively", code.claude.com/docs/en/costs - accessed 2026-11-24 (`/usage`: session cost, prompt cache line, plan usage attribution).
- Claude Code docs, "Run Claude Code programmatically", code.claude.com/docs/en/headless - accessed 2026-11-24 (`total_cost_usd` in JSON output).
- Claude Code docs, "Subagents" and "Agent teams", code.claude.com/docs/en/sub-agents - accessed 2026-11-20.
- Claude Code docs, "Skills", code.claude.com/docs/en/skills - accessed 2026-11-20 (5000-token re-attachment after compaction).
- Anthropic Engineering, "How we built our multi-agent research system", anthropic.com/engineering/multi-agent-research-system - accessed 2026-11-20 (about 15x tokens).
- Anthropic Engineering, "Code execution with MCP", anthropic.com/engineering/code-execution-with-mcp - accessed 2026-11-20.
- Factory prices: `.tf/factory/config.yaml` (`prices_usd_per_mtok`).
