# Guide: working with the factory's team of agents

The factory installs a team of Claude Code agents in the project: personas (who lead the conversation), their
executors, shared agents, skills with knowledge and procedures, hooks that enforce rules, and scripts that do
mechanical work without tokens. This file describes daily work; answers to frequent questions are in `.tf/factory/FAQ.md`.

## Start here
Four steps from zero to the first PR. The rest of this file is details for the curious.

1. **Install.** In the project directory type `tf`. Answer the questions about packs and modes.
2. **Prepare the repository.** `tf onboard --yes` detects the project's commands, creates `verify.sh` (lint, types,
   tests in one command), turns on the quality gate and saves a readiness report in `.tf/reports/readiness.md`. With
   `--verify` it runs the verification once. `tf doctor` tells you whether the installation is healthy and whether the
   gate works.
3. **Commission the first task.** Run `claude` in the project directory and choose a way from the table below.
4. **Review the result.** `tf risk` shows what in the change a human must look at. You merge, not the agent.

| I want to… | Use | What I get |
|---|---|---|
| do a task with acceptance criteria | `/tf-task <issue numbers or text>` or an ordinary sentence ("deliver EBO-1236") | a plan, tests, code, a commit per slice, one PR per task; several keys run one after another |
| work out an idea with the agent before any code | `/tf-design <topic>` or a sentence ("let's design it together, no code yet") | stages with a checkpoint each, diagrams, decisions in `docs/project/`, then a handoff to `/tf` |
| work with the factory without the loop (also on an issue as material: "like EVD-45678, but …") | `/tf <text>` (type `/tf` to see `/tf`, `/tf-task`, `/tf-design` side by side) | the project context, issues read as data, skills for the problem; a proposal of `/tf-task` or `/tf-design` when the work grows |
| ask about the code, or I do not know where to start | `claude --agent maja` (the `pack-it` pack) | an answer or a choice of people and approach |
| make a small change | an ordinary `claude` session | a change under the hooks' control, without a plan |
| work in one role (tests, UX, domain…) | `claude --agent <persona>` from `.claude/catalog.md` | a conversation with the persona and its executors |
| review the repository without model cost | `tf analyze` | reports in `.tf/reports/` |

Something does not work, or a command was blocked? Ask in the session: "what blocked me and what can I do?" — the
agent will point to the file that made the decision. Frequent questions: `.tf/factory/FAQ.md`.

## 1. What an installation consists of
**The factory mode.** The factory lives in a local plugin in `.tf/plugin/` (skills, agents, hook registration, rules) that
only a factory session loads: `tf code` (e.g. `tf code --continue`) starts `claude --plugin-dir .tf/plugin --settings
.tf/cache/session-settings.json` (the plugin's `session-settings.json` with the isolation level: the sandbox for
`sandbox` and `container`). A plain `claude` in the project loads nothing from the factory — no hook, skill, agent,
rule or status line — so your own skills in `.claude/skills/` are never shadowed; factory skills appear in a factory session
as `tf:<skill>`. A cloud environment becomes a factory environment with the setup script printed by `tf cloud-setup`
(the factory files must be in the repository: a team install). `tf work --once` and the measurements use the same plugin.
An update of an older install moves it here (a copy in `.tf/backup/`, back: `python3 .tf/factory/update.py --rollback`);
`install.py --layout default` keeps the old layout, in which every session in the project loads the factory.

| Element | Where in the project | What it does |
|---|---|---|
| the core | `.tf/factory/`, `.claude/skills/core-*`, `.claude/hooks/`, `.claude/tests/` | building agents, updates, costs, working rules, the project record |
| packs (`pack-*`) | `.tf/factory/packs/<id>/`, their skills in `.claude/skills/` | domain knowledge, roles and personas (e.g. `pack-it`, `pack-ux`, `pack-docs`, `pack-editorial-pl`; domain packs also from outside the factory: `tf install --pack-dir`) |
| modes (`mode-*`) | like packs | a way of working turned on on request: `mode-team` (agent teams), `mode-pdi` (the change cycle) |
| agents | `.claude/agents/_generated/` | built by `python3 .tf/factory/build.py` from the core and the packs — do not edit by hand |
| the catalog | `.claude/catalog.md` | the list of personas, roles and skills of this installation |
| project settings | `.tf/config/` | `config.yaml`, your own personas, roles and traits — an update does not touch them |
| work results | `.tf/reports/`, `.tf/register/`, `.tf/cache/`, `.tf/logs/`, `.tf/backup/` | analysis and metrics reports, the findings register, cache, usage (`usage.jsonl`), copies from before an update; `tf init` creates the skeleton |

What is installed: `tf list`. The installation's state: `tf doctor`.

**The company pack.** The organisation's standards and default settings (the autonomy policy, `tf risk` rules, `tf work`
limits, the cost profile, the tracker and issue prefixes) come from one company pack: `tf install --pack-dir
<company repository> --add pack-<company>`. Its values appear in `tf config show` as "organisation"; the
project overrides them in `.tf/config/` (it will not loosen the autonomy policy). The pack contains no addresses or
tokens (Jira, Confluence) — they are in environment variables and Claude Code connections.

**The team pack.** Above the company, a team can have its own pack `pack-<company>-<team>` (the generator:
`org/new_org_pack.py <company> --team <team>`): code rules, standards, issue prefixes, permissions. The order of layers:
engine ← company ← team ← project ← person; `tf config show` shows the source ("team"). The team and the project
only tighten the autonomy policy and only narrow the allowed task modes (`task.allowed_modes`). Installation:
`tf install --pack-dir <company repo> --pack-dir <team repo> --add pack-<company>-<team>`.

### Private and team installation
| | Private (default) | Team (`--shared`) |
|---|---|---|
| settings and hooks | `.claude/settings.local.json` | `.claude/settings.json` |
| the factory's rules | `CLAUDE.local.md` | `CLAUDE.md` |
| ignore entries | `.git/info/exclude` (does not go into the repo) | `.gitignore` (temporary files only) |
| what is in the repository | nothing | the factory, settings, rules, the CI workflow |

In a private installation the factory excludes each of its paths separately (e.g. `.claude/skills/ai-evals/`), not the
whole `.claude/`. Git sees your own skill in `.claude/skills/` and you commit it as usual. `--gitignore` gives a private
installation with entries in `.gitignore` instead of `.git/info/exclude`.

**The drawback of a private installation: the factory is only in your copy of the repository.** `.git/info/exclude`
and local files do not travel through `git push` or `git clone`. The consequences:
- every person in the team installs the factory themselves, so versions, packs and settings (`.tf/config/`) can differ,
  and the agents of two people behave differently;
- a new clone has no factory: a new machine, CI and a Claude Code cloud session (claude.ai/code clones the repository
  afresh) work without the factory's hooks and skills until someone installs it there;
- a configuration change on your side does not reach anyone else.

A private installation fits a trial of the factory, one person's work and a repository in which the team does not want
the factory's files. When the whole team, CI or cloud sessions use the factory, choose `--shared`.

**A repository with `AGENTS.md`.** Claude Code reads `AGENTS.md` by itself only when there is no `CLAUDE.md`,
`.claude/CLAUDE.md` or `CLAUDE.local.md` in the project directory and above. A private installation creates
`CLAUDE.local.md`, so in a repository without `CLAUDE.md` Claude stops reading `AGENTS.md` (the installer warns about
this in one sentence). The fix: add the line `@AGENTS.md` at the start of `CLAUDE.local.md`, outside the factory's
section — an update replaces only the section between the factory's markers. The import works in every Claude Code
version. Details of how instruction files load: the `core-agent-instructions` skill (`references/context-scaling.md`).

## 2. How to start working
1. **Start a factory session:** `tf code` (or `tf code --agent <persona>`; in the old layout `claude --agent <name>`).
   **Choose a persona** from `.claude/catalog.md` and run it: `tf code --agent <name>` (e.g. `kuba` — product
   engineer, `ewa` — domain analyst, `kasia` — tests, `natalia` — UX). The persona talks with you and delegates
   work to its executors (`<persona>-<role>`) and to the shared agents.
2. **Do not know whom to choose?** The pack's dispatcher (`maja` in `pack-it`; a domain pack can have its own —
   `tf list` and `.claude/catalog.md`) will recognise a problem described
   in plain text and choose personas, skills and an approach.
3. **Enter the project's commands** (test, lint, types, build): `tf onboard` writes them into the factory rules
   (`.tf/plugin/RULES.md`; in the old layout the factory's section in `CLAUDE.local.md` or `CLAUDE.md`) — the executors use
   them for verification.

Shared agents, available to every persona:
- `scout` (cheap code search);
- `quick-fixer` (small changes);
- `researcher` (current facts from sources);
- `mcp-runner` (MCP tools — Jira, Confluence, Figma — through a cheap model, a short answer back);
- `architect` (decisions, analysis only);
- `security-reviewer` (a review of sensitive changes);
- `scope-reviewer` (whether the diff goes beyond the plan);
- `specialist` (an ad-hoc perspective of skills).

## 3. The project's course and the record
- **The project record** in `docs/project/` (the `core-project-record` skill): every phase leaves an artifact with a
  TL;DR and a "Handoff" section, the human's decisions are recorded, and the next session starts from them instead of
  reading the whole code.
- **A checkpoint** for a longer task: `python3 .claude/hooks/project_record.py wip start "<goal>"`. After a break the
  session starts from it and from `git status`.
- **The phases from the idea to maintenance** (personas, gates, readiness): the `core-delivery-lifecycle` skill.
- **A sweep of stale notes** (monthly, before a big change, after installing the factory in an old project): the
  `core-sweep` skill reports TODOs, plans and rules that are no longer true, with evidence; after your consent it moves
  documents to `docs/project/archive/sweep/`, which the `guard_paths` hook keeps agents out of (`TF_ARCHIVE_READ=1` lifts it).
- **A plan before the code, then TDD:** first a test that fails, then the code. The `tdd_guard` hook blocks production
  code without a red test. The quality gate: the `.claude/quality-gate.json` file with the test command, e.g.
  `{"command": "npm test", "watch": ["src/", "test/"]}` — the `quality_gate` hook will not let a turn end with a red
  build (described in the header of `.claude/hooks/quality_gate.py`). For speed add `"related"` — only the tests
  of the changed files, a command for the project's own stack (the factory knows no test tool; the /tf-task loop proposes
  one at the first task and writes it after your consent). Placeholders: `{files}` the changed files, `{dirs}` the
  directories of the changed source files, one argument per value; with a comma (`{files,}`) joined with commas.
  E.g. `"npx nx affected -t test --files={files,}"` or `"go test {dirs}"`. The gate and slice verification run it instead
  of the whole `command` (a placeholder with nothing → the whole `command`), and `run_state.py verify … --full`
  (`tf task verify … --full`) runs the whole suite once before the PR. When the gate is off (no file, the switch, a
  declared red batch), `tf doctor` and the session start say so in one sentence.

## 4. Modes and automation on request
| What | How | When |
|---|---|---|
| the factory loop (in the core) | `/tf-task <task>` or `claude --agent tf-task` | one task with acceptance criteria → a specification, a plan of slices, a commit per slice, evidence, one PR, a cost report; a live preview (a local server that pushes every state change to the page, or `.tf/runs/dashboard.html`); for a visible UI change also screenshots before/after, looked at against the criteria (`--visual` / `--no-visual`, only when worth it); guide: `.tf/factory/LOOP.md` |
| Agent teams (`mode-team`, `tf add mode-team`) | `team_switch.py on`, a new session, `/team-session <task>` | the roles must talk to each other along the way; experimental and expensive; guide: `.tf/factory/packs/mode-team/GUIDE.md` |
| A code audit (`pack-it`) | after the scope is approved: the `/code-audit` workflow | a full audit in many dimensions with a ranking (the `eng-code-audit` skill) |
| An Event Storming simulation (`pack-it`) | `/ddd-es-simulation` or `claude --agent es-host` | facilitation training with AI participants |

### Project analysis: `tf analyze`
A fast review of the repository with scripts, without a model and without token cost. Every analysis module looks for
one class of problems; packs provide the modules (`pack-it`, `accessibility` — `pack-ux`):

| Module | What it looks for |
|---|---|
| `security` | secrets in code, `.env` files in the repo, unsafe APIs, disabled TLS, a weak password hash, a missing lockfile |
| `architecture` | import cycles, dependencies in both directions between module groups, hubs (the import graph) |
| `authz` | endpoints that change data (POST/PUT/PATCH/DELETE) without a visible permission check: Express, NestJS, Next.js, FastAPI, Spring |
| `data-classification` | fields with personal data without a class in migrations, schemas and models (a draft data inventory), personal data in logs and analytics |
| `tech-debt` | TODO/FIXME without an issue (with the age from git), skipped tests without a reason, silenced checks, files over 1000 lines |
| `observability` | a service without a health check and without a request identifier, `console.log`/`print` instead of a logger, swallowed errors |
| `i18n` | interface text outside translation (in a project with a translation library), dates without a locale, amounts without `Intl.NumberFormat` |
| `accessibility` (`pack-ux`) | images without `alt`, buttons and links without a name, fields without a label, a click without a keyboard, `tabindex` > 0, a missing `lang` |

- `tf analyze --list` shows the modules and whether they fit the repo; `tf analyze` runs all the fitting ones,
  `--only security,authz` the chosen ones, `--since <commit>` only the files changed since a commit, `--top N` shortens the report.
- The result: `.tf/reports/<module>.md` with a list of actions (checkboxes), `.tf/reports/<module>.json` and an overview
  `.tf/reports/README.md`. Every finding has a stable `id`, so a repeated analysis keeps your ticks, and the register
  `.tf/register/items.jsonl` remembers the findings' state between runs. The results are cached per commit
  (`TF_ANALYZE_NO_CACHE=1` turns it off).
- A finding is a heuristic, i.e. "check this", not proof: a layer the scanner does not see (a network gate, a global
  filter) may check the permission. A false hit you describe in the code and tick off in the report.
- A full audit with a model and a ranking is a separate thing: the `/code-audit` workflow (the table above).

### Change risk: `tf risk`
`tf risk [--base main]` assesses the current branch's diff against the base: a high, medium or low level and a list of
"what a human must see" (the file, the reason). A high level comes from e.g. authentication, payments, the database
schema, deployment and CI, the specification and weakened tests (removed assertions, skips, a deleted test); a new
module without an ADR is an "evidence" point on the list. `--md` gives a section for the PR description (the `/tf-task` loop
inserts it itself: `run_state.py pr-body`), `--json` a result for scripts. The triage is advisory and never blocks a
merge. Your own rules (e.g. price list paths as high risk) you enter in `autonomy.triage` in `.tf/config/config.yaml`.

### Unsupervised work: `tf work --once`
`tf work --once --budget 5` takes one task you gave the Auto mode (`tf task mode <KEY> auto` — that is your consent to
unsupervised work), of light or normal weight, and runs it with the `/tf-task --auto` loop in a separate worktree
(`.tf/worktrees/<KEY>`, the branch `story/<key>`). A spending limit is mandatory (`--budget` or `work.budget_usd` in
`.tf/config/config.yaml`); the agent works in the `acceptEdits` permission mode: it saves files in its worktree, and any
other tool outside the allowed list in the `.claude` settings is rejected rather than waiting for you. A lock
(`.tf/locks/`) holds the task, so two parallel runs will not take the same one. The result is a PR or a STOP block in
the task's worktree, and an entry goes to `.tf/logs/work.jsonl`; the factory merges and deploys nothing. It does not take
a task with a worktree again by itself — resuming: `tf work --once --key <KEY>`; all the runs of one task together
will not exceed `work.task_budget_usd` (20 USD by default). `--dry-run` shows the task and the command without running
it. Only the factory's files (`.claude/`, `.tf/factory/`), the configuration and the task folder go from the
installation into the worktree — without symlinks and without files outside them (e.g. `.env`). Before the start the
factory compares the files that steer the agent (`.claude/settings.json` and the scripts its commands point to, hooks,
agents, skills, `CLAUDE.md` — also in subdirectories — `.mcp.json`, `.tf/factory/`, `.tf/config/`) with your copy of
the project: when the task's branch has any of them different (e.g. after someone else's push or your uncommitted
change), the run does not start and you get a list of files. The agent loads no MCP servers (`--strict-mcp-config`) and
gets only the system's, the proxy's and Claude's authentication environment variables; a GitHub or cloud token you pass
consciously in your environment: `TF_WORK_ENV_ALLOW=GITHUB_TOKEN tf work --once …` (configuration from the repository
will not extend this list; without a token the loop stops before pushing the branch with a clear message). When the
steering files in your copy of the project change during the run, you get a warning with a list. What these locks by
nature do not cover: the loop runs the project's tests and build scripts from the task's branch (that is its job), and
the agent sees the files of your home directory. Full isolation means running `tf work` in a container or a separate
machine without your credentials.

## 5. Costs
- **The team profile:** `python3 .tf/factory/profile.py` shows the active profile. Available ones:
  - `economy` — without Opus;
  - `balanced` — the default: Haiku for mechanics, Sonnet day to day, Opus for expensive mistakes;
  - `quality` — a higher effort and an Opus advisor.
- **Measurement:** `python3 .tf/factory/cost_report.py --days 7` (usage per agent and model from `.tf/logs/usage.jsonl`);
  the status line shows the session's cost, time and tokens and how full the context is; every `/tf-task` task shows its
  cost, time and tokens on the dashboard, in `report.md` and in the PR description. Every entry in `usage.jsonl` has a harness
  fingerprint (the `harness` field: the versions of Claude Code, the factory and the packs, a hash of the installed
  files), so costs from different factory versions can be separated.
- **Model names and prices:** `python3 .tf/factory/model_check.py` (also in `tf doctor`) checks whether the
  configuration and the engine refer to an unknown or older model. The current models are in `models_current`, the
  allowed older ones in `models_legacy`, the check date in `models_checked` (the engine's configuration; your own model
  pins in `.tf/config/config.yaml`). A date older than 90 days is a reminder to check the names and the price list.
- **Approved models (optional):** when the organization allows only some models, list them under `models_approved`
  (in the company pack, the team pack or `.tf/config/config.yaml`; a lower layer only narrows the list). Then
  `model_check.py` reports a tier or a session setting of the active profile outside the list, `profile.py` refuses
  a profile that needs such a model, and the `model_guard` hook denies a delegation that names one. Without the
  list nothing changes. At the session start the same hook warns when the session's model (from the settings) is
  outside the list; a model you switch to later with `/model` is not checked.
- **After a factory update:** `python3 .tf/factory/metrics.py --after-update` (also in `tf doctor` and in the
  `tf metrics` report) compares the window after the last update with a window of the same length before it: the share
  of reverted changes, hook blocks (`.tf/logs/hook-blocks.jsonl` — the time, the hook and the decision, without content)
  and hook errors. With a clear deterioration it gives the command to go back to the previous version
  (`python3 .tf/factory/update.py --rollback`). The factory does not roll itself back: with few changes this indicator
  can be random, so the decision is yours.
- **The factory's effectiveness:** `tf metrics [--weeks 4] [--revert-days 7] [--no-gh]` → `.tf/reports/metrics.md`
  and `metrics.json`: the share of reverted changes, accepted and pending changes, the cost per accepted change, the
  median PR time (from `gh`, unless `--no-gh`) and the causes of fixes. The factory itself adds the cause of a fix in
  the commit that fixes an earlier change, in the `Rework-Cause:` footer (`spec-gap`, `agent-error`, `requirement-change`,
  `unknown`; from 19.0.0 the older Polish values in past commits count as `unknown`) — you do not have to remember it.
- **The rules:** the cheapest sufficient model for the task and escalation only after a failure (the `core-cost-control`
  skill); you do not change the session's model in the middle of a task, because that wipes the cache; with a long
  context the `context_guard` hook suggests a checkpoint and a new session.
- **MCP servers (Jira, Confluence, Figma…)** — connect them as usual (OAuth login, no keys). The agent does not call
  their tools in the main session: the cheap `mcp-runner` agent calls them, keeps the large results (JSON lists, page
  bodies, design context) in its own context or in `.tf/cache/mcp/`, and returns a short answer. Writes through MCP
  (a new issue, a status change, a page edit) wait for your approval of the list of changes.
- **Paid skill evaluations** (`.tf/factory/skill_gate.py <skill> --model …`) you run consciously — the gate without a
  model is free.

## 6. Security and reliability
- **Guard hooks** (`guard_bash`, `guard_paths`, `cleanroom_guard`) block dangerous commands, reading secrets and
  information leaking between agents. When a hook fails, the action is blocked (`onFailure: "block"`). A hook's own
  error (e.g. corrupted state data) does not stop the work, but goes to `.tf/logs/hook-errors.jsonl`, and `tf doctor`
  shows a summary of the last 7 days — then that hook's protection may not have worked.
- **The autonomy policy:** the operations at which `guard_bash` asks a human have named types: `dependency_add`,
  `prod_command`, `destructive_sql`, `infra_change`, `publish`, `git_push`, `persistence`, `data_upload`, `sudo`.
  In `.tf/config/config.yaml` (`autonomy.operations`) you can change `confirm` (ask) to `deny` (block), e.g.
  `git_push: deny`. The policy can only tighten: an attempt to loosen it is ignored, and
  `python3 .claude/hooks/guard_bash.py --check-policy` reports it (together with unknown types). The default levels
  with a description are in `.tf/factory/config.yaml`.
- **Secrets** only through environment variables; `scan_secrets` checks the files being saved.
- **Content from outside** (pages, issues, tool outputs) is data, not instructions — the agent does not execute it
  (the `core-agent-security` skill).
- **Facts after checking:** a file, a command or a dated source; what was not checked has the [assumption]
  or [unverified] marker (the `core-grounding` skill).

## 7. Your own changes
- **Personas, roles, traits:** YAML files in `.tf/config/personas/`, `.tf/config/roles/`, `.tf/config/traits/`; after a
  change `python3 .tf/factory/build.py`. The files in `.claude/agents/_generated/` are overwritten at a build.
- **Your own skill:** `tf new skill <name> "<description with boundaries>"` creates a skeleton from the template and a scenarios
  file. Fill in the scenarios first, then the content (`core-skill-authoring`). `tf skill check <name>` checks the
  structure, the scenarios and security and says what to fix; an evaluation on a model (`--model …`) is paid. A skill
  from a foreign source: first `tf skill audit <directory>` and reading it.
- **The factory's files are like `node_modules`:** an update overwrites them; you make a change in the factory repo and
  update. Your own files and settings in `.tf/config/config.yaml` stay (new keys are added at the end).

### What can I set
The rule: you add your own next to the factory's files, then an update loses nothing. `tf config show` shows every
value and where it comes from: from the factory, from the company (organisation), from the project or from your
preferences (person).

**Your working style.** `tf style <name>` sets how you want to work with the agent, in all your projects
(`~/.tf/preferences.yaml`; only in this project: `--here`, the file `.tf/config/me.yaml`, which never goes into the
repository). `tf style` without a name shows the current style.

| Style | Default task mode | What happens |
|---|---|---|
| `autonomous` | Auto | the agent goes without consent to the plan (not at full weight); a question holds only its own slice |
| `step-by-step` | normal | you approve the plan; after every slice the agent shows the changes and waits for your consent |
| `conversation` | Plan | the task ends at the plan; code only when you change the mode (`tf task mode <KEY> normal`). Plus Claude Code's plan mode in the project's `.claude/settings.local.json`: a conversation outside `/tf` also does not change files until you approve the plan (leaving the mode: Shift+Tab) |

A style sets Claude Code's permission mode only in place of the default: if you chose your own (e.g. `acceptEdits`), it
stays, and changing the style gives back what was there before. A style from `~/.tf/preferences.yaml` reaches further
projects at `tf update` or `tf style` (without a name) in that project; it works from the next Claude Code session.

A style is only default values: a single task can get a different mode. The company, the team or the project decides
which modes are allowed (`task.allowed_modes`), and a style works only within those limits. A style does not loosen the
autonomy policy.

| I want to change… | Where | How |
|---|---|---|
| the models and effort of the `fast` / `std` / `deep` levels | `.tf/config/config.yaml` → `tiers` | enter only the changed fields, then `python3 .tf/factory/build.py` |
| the overall cost level | the cost profile | `python3 .tf/factory/profile.py <profile>` |
| who performs a step of the `/tf-task` loop and at what level | `.tf/config/config.yaml` → `steps` | e.g. `steps: {review: {tier: deep}}`, then `python3 .tf/factory/build.py`; a preview with the model and effort: `tf config show steps` |
| the operations the factory asks about or blocks | `.tf/config/config.yaml` → `autonomy` | it can only be tightened (a question → a block) |
| the language of the conversation and of commits | nothing to set | agents answer in the language you write in; commits in the language of the repository's history (`git log`), in a new repository in English (`.tf/config/config.yaml` → `commit_language.new_repo`) |
| whether the factory runs feature flags itself | `.tf/config/config.yaml` → `feature_flags.auto` | `true` by default: the factory asks you for the flag's name, creates it and makes sure it is off outside the test environment; `false`: you add flags yourself (in the code, in an external service), and the factory neither creates nor requires them |
| the project's verification commands | `verify.sh`, `.claude/quality-gate.json` | `tf onboard --yes` or by hand |
| turning off the quality gate for yourself | `.claude/settings.local.json` → `env` | `"QG_GATE_DISABLE": "1"` — `tf doctor` will keep reminding you |
| your own persona, role, trait | `.tf/config/personas/`, `roles/`, `traits/` | a YAML file, then `python3 .tf/factory/build.py` |
| your own skill | `.claude/skills/<name>/` | `tf new skill`, `tf skill check` |

## 8. Command cheat sheet
| Command | What it does |
|---|---|
| `tf` | an update (or an installation when there is no factory) |
| `tf update --check` | whether there is a new version and what will change (changes nothing; fetches only the version and the list of changes) |
| `python3 .tf/factory/update.py --full-check` | all the factory's tests in the project, in parallel (after an update only a quick check by default) |
| `tf uninstall [--dry-run] [--yes] [--force]` | uninstalling the factory: removes its files and entries, yours stay (`--force`: your additions too); a copy in `~/.tf/backups/` |
| `tf add <id>` / `tf remove <id>` | a pack or a mode |
| `tf list`, `tf doctor [--fix]` | what is installed; the installation's state and repairs |
| `tf new skill <name> "<description>"`, `tf skill check <name>`, `tf skill audit <directory>` | your own skill: a skeleton with scenarios, the quality gate, a security audit |
| `tf style [<name>] [--here]` | your working style: `autonomous`, `step-by-step`, `conversation`; without a name — the current one |
| `tf config show [<key>]` | the configuration after merging and where every value comes from |
| `tf spec new <KEY>`, `tf spec check <KEY>` | the task's specification (`spec.md`): a template and a check whether the criteria have Given / When / Then, what stays unchanged and whether there are no blocking questions; with errors the task will not move to the plan |
| `tf task freeze <KEY> <file> --by human:<id>`, `tf task reopen <KEY> <file> --by human:<id> --reason "…"` | protecting the task's basis: a frozen file (e.g. an acceptance test), an approved task file and `spec.md` from the delivery stage on the agent changes only with your consent; `reopen` removes the protection and records the reason |
| `tf trace <KEY> [--md]` | the trace: every `AC-n` criterion from the specification → a test with that identifier → whether the TDD hook saw it red → a commit → the slice's evidence; a criterion without a test blocks the review; `--md` gives a table for the PR description |
| `tf task flag <KEY> set <flag>`, `… none --reason "…"`, `… allow <environment> --by human:<id>`, `tf flag check <KEY>` | a feature flag per story: the new behaviour is behind a flag turned on only in the test environment; turning it on elsewhere needs your consent. The factory takes the flags file and the environments from the card `.tf/config/operations.json` (`tf onboard` creates it); without it, it says plainly that the flag has to be checked by hand |
| `tf task weight <KEY>`, `… --set <weight> [--by human:<id> --reason "…"]` | the task's weight: light (a small change, no specification, one slice), normal or full (login, payments, migrations, secrets — you approve the plan before the code); the factory chooses it itself and gives the reason, anyone can raise it, only you can lower it |
| `tf task deployed <KEY> [--version X]`, `… --rolled-back --by human:<id>` | a check after deployment: runs the smoke test from the operations card (`deploy.smoke` in `.tf/config/operations.json`) and records the result in the task. Green → the "deployment" stage. Red → the question "roll back?" with the rollback step, the time and the logs command from the card, and the task goes on the "waiting for you" list; you record the rollback decision. Without a smoke test in the card the factory ends at the merge and says so plainly. The factory deploys nothing and rolls nothing back by itself |
| `tf task close <KEY> [--lesson "…" --by human:<id>]`, `tf task finding <KEY> control F1 "…"`, `tf status --all` | closing a task: only a merged change, with no deployment waiting for a decision and with a control recorded for every important review finding (a test, a hook, a rule or the reason it is missing); it reminds you about the flag's removal date; it adds a lesson to `docs/project/lessons.md` only on your command. Closed tasks disappear from `tf status` (all of them: `--all`) |
| `tf task mode <KEY> [plan\|normal\|auto]`, `tf task approve <KEY> plan.md --by human:<id>` | the task's mode: Plan ends at the plan, normal lets the code in after your consent to the plan, Auto goes without consent (not at full weight) |
| `tf status` | the list of tasks: the stage, how many slices have current evidence, which files need refreshing and what waits for you (a question with a recommendation); `tf status --open` opens the preview in a browser |
| `tf task start <KEY> --title "…"`, `tf task stage <KEY> <stage>`, `tf task status <KEY>` | one place for a task: `docs/project/changes/<KEY>/task.json`; `tf status` gives the list of tasks |
| `tf onboard [--yes] [--verify] [--dry-run] [--json]` | preparing the repository: detecting commands, `verify.sh`, a readiness report, the quality gate, commands in the instruction file |
| `tf init` | the `.tf/` skeleton for the factory's results (reports, the register, cache, logs) |
| `tf analyze [--only a,b] [--since <commit>] [--top N] [--list]` | analysing the project with modules → `.tf/reports/<module>.md` |
| `tf risk [--base <branch>] [--md\|--json]` | a risk triage of the change on the branch (advisory) |
| `tf metrics [--weeks N] [--revert-days N] [--no-gh]` | the factory's effectiveness → `.tf/reports/metrics.md` |
| `tf work --once --budget <USD> [--key <KEY>] [--dry-run]` | unsupervised work: one task in the Auto mode in a separate worktree, with a spending limit; without merging |
| `python3 .claude/hooks/guard_bash.py --check-policy` | checking the autonomy policy from `.tf/config/config.yaml` |
| `python3 .tf/factory/update.py --rollback` | going back to the state from before the last update |
| `python3 .tf/factory/build.py` | rebuilding the agents and the catalog |
| `python3 .tf/factory/profile.py <profile>` | the team's cost profile |
| `python3 .tf/factory/cost_report.py --days 7` | a cost report |
| `python3 .claude/hooks/detect_stack.py` | the project's stack and the skills' compatibility with versions |
