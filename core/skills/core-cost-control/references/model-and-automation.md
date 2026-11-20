# New models, agents in automation, authentication, effort keywords
> 4. Prompting reasoning models - 5. ultrathink and ultracode - Sources

## 1. Assessing a new model
A leaderboard number is three things: a task set, a metric and a protocol. Check all three before comparing.
- **Task set**: does it look like your work (fixing bugs in an existing repository, building features, terminal work)? Old
  sets saturate and may have leaked into training data.
- **Metric**: a single-attempt pass rate overstates reliability for agents that loop. What matters is whether the model
  succeeds every time: at 90% per step, five dependent steps succeed about 59% of the time (0.9^5) and ten about 35%.
- **Protocol and harness**: the same model scores very differently with different agent scaffolding. Record whether the
  harness was fixed (the same scaffolding for every model) or free (each vendor's own), plus model version and inference
  settings. A vendor's 80% in its own harness and your model's 65% in someone else's report are not comparable.

Decide with your own test:
1. 3-5 real tasks from your project, with the same verification you use day to day.
2. Several repetitions per model (results vary between runs).
3. Compare **cost per solved task** = tokens x iterations + human review time, not price per token.
4. For agents built in code, keep an evaluation matrix (cases x models) and re-run it after any harness change too
   (pack-it `eng-llm-features`).
5. Record a change of the default model together with the test results; revisit news about every two weeks.

## 2. Agents in CI and schedules
- **Trigger** on meaningful events (a PR, a red build, a new issue) with path filters or labels - not on every push.
- **Cheap triage first**: a small model assigns a risk level; only higher levels get the expensive review.
- **Hard limits**: a turn limit AND a dollar cap (`claude -p ... --max-budget-usd <amount>`; the cap works only with
  `--print`). `--max-turns` did not appear in `claude --help` of 2.1.329 [unverified] - check your version's help.
- **Evaluator** steps get no tools and 1-2 turns.
- **Smaller input**: filter lockfiles and generated code out of diffs.
- **Model per role**: triage on the cheapest, code reasoning on the middle tier, the expensive model only on critical paths.
- **Record** cost, turns and time per run (per PR, per triage level, per week) and review monthly: verdicts that are always
  rubber-stamped -> loosen triage; bugs that passed a green review -> add an evaluation case.

## 3. Authentication and the bill
- Company code and automation use an API key from a secret store: commercial terms, per-token billing, visible in reports.
- The SDK or `claude -p` may fall back to a developer's subscription login when no key is set (consumer terms, plan limits;
  how programmatic use counts against a plan is [unverified]). Set the key explicitly in automation and check the run's
  account in its log.

## 4. Prompting reasoning models
Give the goal, the hard constraints and a measurable success criterion. Do not impose thinking steps unless the process
itself is mandatory (migration, payments, security procedure) or the model missed after 1-2 attempts - then ask for 2-3
alternative approaches before choosing one.

## 5. ultrathink and ultracode
- `ultrathink` anywhere in a prompt asks for deeper reasoning on that turn only; the stored effort does not change. Typed in
  the terminal (Claude Code 2.1.311+) it can also raise that turn to `xhigh`, unless `CLAUDE_CODE_EFFORT_LEVEL`,
  `maxEffortLevel` or an organization limit is below `xhigh`, or the provider does not support it (e.g. Bedrock).
  `CLAUDE_CODE_DISABLE_ULTRATHINK=1` turns the keyword off.
- `ultracode` is a setting, not an effort level: with it on, Claude orchestrates multi-agent dynamic workflows for
  substantive tasks. On via `/effort ultracode`, `"ultracode": true` in settings, or `--effort ultracode` (the flag and the
  SDK value also set `xhigh`). Every workflow agent has its own context and 5-minute cache, so cost grows with the number of
  agents.
- For one hard question in the middle of a task: `ultrathink` on that turn is the cheapest option and keeps the session's
  settings; switching `/effort` to max affects every later turn (and the cache on models without the exception); ultracode
  fits a large multi-part task, not one question.

## Sources
- Claude Code docs, "Model configuration", code.claude.com/docs/en/model-config - accessed 2026-11-20 (ultrathink, ultracode, effort limits).
- Claude Code docs, "Run Claude Code programmatically", code.claude.com/docs/en/headless; `claude --help` 2.1.329 - accessed 2026-11-20.
- Claude Code docs, "Manage costs effectively", code.claude.com/docs/en/costs - accessed 2026-11-20.
