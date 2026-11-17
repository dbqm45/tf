# FAQ

Daily work: `.tf/factory/GUIDE.md`.

## What is the factory?
A kit for working with Claude Code agents. It installs in a project personas (the agents you talk to), their
executors, skills with knowledge and procedures, hooks that enforce rules (TDD, secrets, safe commands) and scripts
that do mechanical work without tokens. It consists of the core, domain packs (`pack-*`) and working modes on
request (`mode-*`).

## How do I add the factory to a project?
In the project directory run `tf` (or `python3 <fabryka>/core/factory/install.py`). At the first installation
you choose packs and modes. You do not set a language: agents answer in the language you write in.
- **Private** (default): nothing goes into the repository. The settings are in `.claude/settings.local.json`, the rules
  in `CLAUDE.local.md`, and the factory's paths in `.git/info/exclude`.
- **Team** (`--shared`): the factory is committed together with the project. The settings are in `.claude/settings.json`,
  the rules in `CLAUDE.md`, plus a CI workflow.

A private installation does not travel through `git clone`: everyone installs the factory themselves, and CI and cloud
sessions do not have it. A repository with `AGENTS.md` and without `CLAUDE.md` needs the line `@AGENTS.md` in
`CLAUDE.local.md`. Both topics: `.tf/factory/GUIDE.md`, the section "Private and team installation".

Then run `claude` once in the project directory and accept trust in the folder. Without that, hooks and permissions
do not work.

## How do I update the factory?
- `tf update --check` shows whether there is a new version and what will change, without changing anything.
- `tf` (or `python3 .tf/factory/update.py`) updates.

After an update the factory runs a quick check (the engine's scripts and hooks compile, `build.py check` passes) —
a few seconds. The factory's full tests passed in the release CI; in the project you run them with
`python3 .tf/factory/update.py --full-check` (in parallel, a few minutes).

Before an update the new version's skills go through an audit with the tool from the installed version. The factory's
files in the project are like `node_modules`: an update overwrites them, so you make changes in the factory repo and
update. Your files (your own skills, personas, roles, `CLAUDE.local.md`) stay; in `.tf/config/config.yaml` your
settings stay, and new keys are added at the end. Going back: `python3 .tf/factory/update.py --rollback`.

## Can updates run by themselves?
Yes: `python3 .tf/factory/update.py --auto on` (to turn it off: `--auto off`). Only PATCH and MINOR releases go in
automatically. A MAJOR release, which changes the factory's public API, needs your decision.

## How do I add or remove a pack or a mode?
- `tf add <id>` and `tf remove <id>`. Removed files go to `.tf/backup/`.
- The list of available and installed ones: `tf list`.
- A default pack or mode that appears in a new version is added once at an update. The ones you removed do not
  come back.

## How do I add the company's settings?
The standards and default settings of the whole organisation live in one **company pack** in the company's own
repository. You make it once, then install it in every project. The full guide, including generating it from the
company's documents (e.g. Confluence) with the `org/standards_from_docs.py` script, which checks quotes without a model:
`org/README.md` in the factory repository.
1. **The skeleton.** In a clone of the factory repository (the output directory must be outside it):
   ```
   python3 org/new_org_pack.py <company> --out <directory> --title "Company name"
   ```
2. **Fill in the `TODO` fields** (`grep -rn TODO <directory>`; a description of every field: `README.md` in the pack):
   - `pack.yaml` → `org_defaults.config`: agent operations blocked in the company (`autonomy.operations`, tightening
     only), paths always for a human review (`autonomy.triage`), `tf work` limits (`work`), the cost profile,
     languages;
   - `pack.yaml` → `org_defaults.operations.tracker`: the tracker, issue key prefixes, the Jira field with criteria;
   - rules checkable with a pattern (`analyzers/<company>-standards/rules.yaml`, with examples in `fixtures/`): they work
     without a model in `tf analyze`; semgrep rules — `semgrep.yml`, used in the `/tf` loop's scan;
   - the standards skill (`skills/<company>-standards/`): only findings that need judgement — first the scenarios
     in `tests/skill_evals/`, then the content;
   - `settings.json`: Claude Code permissions for the whole company.
3. **Check** in the factory repository: `python3 tools/workspace.py check --packs pack-it,pack-<company> --pack-dir
   <directory>`.
4. **Publish** the directory as the company's git repository (with `vX.Y.Z` version tags).
5. **Install it in a project:** `tf install --pack-dir <company repository address> --add pack-<company>`. `tf update`
   then fetches new versions of the pack.

**A team** has its own pack above the company one: `python3 org/new_org_pack.py <company> --team <team> --out <directory>`
(the team's standards, rules and issue prefixes; it only tightens the company's prohibitions). Installation in the
team's project: `tf install --pack-dir <company repo> --pack-dir <team repo> --add pack-<company>-<team>`.

`tf config show` shows the company's values (the source "organisation", for a team "team"). A project overrides them in
`.tf/config/config.yaml` and `.tf/config/operations.json`; it will not loosen a prohibition from the company's autonomy
policy. The pack contains no addresses or tokens (Jira, Confluence): Jira takes the address and credentials from the
variables `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN` (or `JIRA_TOKEN`), and live access to Confluence is a
connection (an MCP server) in Claude Code.

## How do I set my way of working with the agent?
`tf style autonomous` (the agent goes by itself, a report at the end), `tf style step-by-step` (you approve the plan and
every slice of work) or `tf style conversation` (the task ends at the plan, and Claude Code starts in plan mode, so
an ordinary conversation also does not change files without your consent). The style applies in
all your projects; only in the current one: `--here`. It does not go into the repository and does not change other
people's work. The company, the team or the project sets the limits: a style will not turn on a mode they do not allow
(`task.allowed_modes`), nor loosen the autonomy policy's prohibitions. Details: `.tf/factory/GUIDE.md`, the section
"What can I set".

## Which model, and how much does it cost?
- Roles have tiers: `fast` (Haiku), `std` (Sonnet), `deep` (Opus).
- The team profile switches them with one command: `python3 .tf/factory/profile.py economy|balanced|quality`.
- You measure the cost with `python3 .tf/factory/cost_report.py --days 7`, and the status line shows the cost of the
  current session.

Features that are paid by nature (skill evaluations on a model, agent teams) you run consciously.

## What are the factory's hooks?
Scripts that Claude Code runs at events, independently of the model's decisions:
- `guard_bash` — dangerous shell commands;
- `guard_paths` — files with secrets;
- `cleanroom_guard` — information isolation between agents;
- `tdd_guard` — code only after a red test;
- `quality_gate` — with `.claude/quality-gate.json` a turn and a subagent do not finish with red tests (the test
  lock: `test_lock.py`);
- `scan_secrets` — secrets in saved files;
- `skill_hint` — skill hints (without frameworks and languages outside the project's stack);
- `context_guard` — a warning about a long context;
- `log_usage` — recording usage;
- `update_notice` — information about a new release.

The guards block an action also when the hook itself fails. The state of the hooks: `python3 .tf/factory/hooks_status.py`.

## Why does the agent ask for consent to a command?
The permissions are deliberately narrow: without asking, the agent runs only the commands from the `allow` list in the
settings. A command you use often you add to `allow` in `.claude/settings.local.json`. The rules and the permission
modes are described by the `core-agent-security` skill.

## The agent gave a false fact — what do I do?
Ask for the source. The factory's rule is a fact from a file, a command or a dated source, and what was not checked —
with the [assumption] marker. A recurring mistake you record in `docs/project/lessons.md`, so that the next sessions
avoid it.

## What are `.tf/` and `tf analyze`?
`tf init` creates the `.tf/` directory in the project — one place for the factory's work results: `reports/` (analysis
reports), `register/` (the work register), `cache/`, `logs/`, `runs/`, `backup/`; every directory has a `README.md` on
what is in it and whether it can be deleted. In a private installation the whole `.tf/` is in `.git/info/exclude`, in a
team one only the reproducible directories go to `.gitignore`. `tf analyze` runs the review modules (`tf analyze --list`)
and for each one writes `.tf/reports/<module>.md` with a list of actions to tick off; a repeated analysis keeps the ticks
and notes, marks what looks fixed and adds new findings at the end. For now only scripts work (floor 0), without a
model and without cost; modules are added by packs or by your own `.tf/analyzers/` directory.

## How do I uninstall the factory?
`tf uninstall --dry-run` shows what will be removed and changed. `tf uninstall --yes` removes:
- the factory's files recorded in the manifest (the engine, skills, hooks, tests) and the generated files (agents, the catalog);
- the factory's block in `CLAUDE.local.md` or `CLAUDE.md` and in `.git/info/exclude` or `.gitignore`;
- the factory's entries in the Claude Code settings (your permissions and hooks stay) and the permission mode set by a style.

Your files stay: your own skills, `.tf/config/`, the work results in `.tf/`. `--force` removes them too. The command
never touches `docs/project/` or the project's code. Before a change it saves a copy in `~/.tf/backups/<project>-<date>.zip`
(restoring: `unzip -o <file> -d <project>`).

## Where to read next?
- `.claude/catalog.md` — the personas, roles and skills of this installation.
- `.tf/factory/packs/<id>/GUIDE.md` — the modes' guides (e.g. `mode-pdi`, `mode-team`).
- `.tf/factory/PUBLIC_API.md` — what is the factory's public API and how versions are numbered.
- `.tf/factory/CHANGELOG.md` — what changed in successive versions.
