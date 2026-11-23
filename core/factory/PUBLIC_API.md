# The factory's public API and versioning rules

The factory is a **core** (`core/`), **overlays** (`packs/pack-*`) and **modes** (`modes/mode-*`, e.g. `mode-pdi`). The core is versioned according to **Semantic
Versioning 2.0.0** (semver.org): the number in `core/factory/VERSION` (in a project `.tf/factory/VERSION`), the change
history in `core/factory/CHANGELOG.md`. Each overlay has its own version (`version` in `pack.yaml`) and declares the
range of core versions it works with (`requires.core`, e.g. `">=3.0.0 <6.0.0"`). A mode is a way of working switched on
by a person (a main session agent, a process skill, scripts); it has the same format as an overlay and the field `kind: mode`. This file defines what the core's public API is,
that is, what we promise to keep within the same MAJOR version, also toward overlays.

## What belongs to the public API
| Area | Examples |
|---|---|
| names of core skills and their presence | `core-grounding`, `core-project-record`: removing or renaming one breaks references in personas, roles, overlays and project skills |
| overlay format (`pack.yaml`) | keys `id`, `kind` (`pack` or `mode`), `version`, `title`, `description`, `content_language`, `default`, `requires` (`core`, `packs`), `optional_packs`, `facets`, `vocabulary`, `skill_requires`, `always_skills`, `standalone_skills`, `unversioned_skills`, `reference_sections`, `freshness`, `skill_visibility`, `shared_agents` (with `only_for`, `main_only`, `grounding`), `consultants`, `routing`, `routing_notes`, `contributes` (`personas`, `roles`, `agents`), `contributes_when`, `migrates_from` (former factories from which the installation moves to this overlay), `org_defaults` (a company overlay, at most one per project: `config` with keys `autonomy`, `tiers`, `profiles`, `default_profile`, `work`, `loop`, `steps`, `task`, `default_language`, `default_commit_language`: a layer between the engine and the project; `operations.tracker` with `type`, `prefixes`, `fields`, without `url`), `team_defaults` (a team overlay, at most one, requires a company overlay: the same keys as `org_defaults`, a layer between the company and the project; `task.allowed_modes` is the intersection of layers, and the team's `operations.tracker.prefixes` replaces the company's prefixes), `renames` (version → old name → new name, for `migrations.py`); overlay files `roles/`, `personas/`, `traits/`, `skills/`, `hooks/`, `tests/`, `workflows/` (in a project `.claude/workflows/`), `analyzers/` (tf analyze modules, in a project `.tf/factory/analyzers/`), `settings.json`, `cleanroom.json`, `technologies.json`, `semgrep.yml` (the overlay's semgrep rules in the loop slice scan), `GUIDE.md` (a guide, in a project `.tf/factory/packs/<id>/GUIDE.md`); an optional overlay `migrations.py` with a function `migrate_values(root, dry) -> list[str]` (migration of its data in the project, called on update) |
| core agents and markers | shared agents (`scout`, `quick-fixer`, `researcher`, `mcp-runner`, `architect`, `security-reviewer`, `scope-reviewer`, `specialist`, `specialist-deep`), the `@dispatcher` marker in `only_for` and the persona field `dispatcher: true` |
| commands and their flags | `tf uninstall` (`--dry-run`, `--yes`, `--force`; backup in `~/.tf/backups/`, directory: `TF_BACKUP_DIR`; the installation manifest with a `settings` key: the Claude Code settings entries added by the factory), `update.py --full-check` (factory tests in parallel; by default only a quick check after an update), `tf` (install, update, add, remove, list, doctor, onboard, task, status, spec, trace, flag, init, analyze with the flags `--only`, `--since`, `--top`, `--list`), `.tf/factory/analyze.py` (init, list, run, gate with `--module`), `.tf/factory/build.py` (build, check, list, new-skill, managed-apply), `install.py` (including `--pack-dir`, `--drop-pack-dir`: overlays from outside `packs/`), `update.py`, `packs.py`, `migrations.py`, `profile.py`, `skill_gate.py`, `skill_audit.py`, `freshness.py`, `feedback_report.py`, `cost_stats.py`, `check.py`, `finish.py`, `facts.py`, `cost_report.py`, `hint_report.py`, `jev_calibration.py`, `system_diff.py` (`tf diff [--base <branch>] [--md|--json]`: the system diff of a branch; configuration key `system_diff`); documented script commands in `.claude/hooks/` and `.claude/skills/*/scripts/` |
| environment variables | `TEAM_FACTORY`, `TF_REPO`, `CLAUDE_SKILL_HINT*`, `CLAUDE_CONTEXT_WARN_K`, `CLAUDE_SKILL_GATE`, `CLAUDE_TDD*`, `CLAUDE_CLEANROOM_DISABLE`, `CLAUDE_JEV_*`, `TYPESAFE_*`, `TF_KB_DIR`, `TF_KB_ALLOW_LOCAL` (deprecated aliases: `EVTF_KB_DIR`, `EVTF_KB_ALLOW_LOCAL`) |
| blocking hook rules | what a hook blocks by default: `guard_bash`, `guard_paths`, `cleanroom_guard`, `tdd_guard`, `scan_secrets`: a new or stricter block enabled by default changes what used to work; `guard_bash` and `guard_paths` refuse lowering the isolation level from inside a session (since 24.0.0: `tf isolation <level>`, `isolation.py set`, `install --isolation`, the `isolation` key of `.tf/config/config.yaml`, the `sandbox` key of `.claude/settings*.json`, `.tf/plugin|cache/session-settings.json`, the sandbox template); `read_gate` only warns by default (`read_gate.mode: warn`, `max_lines: 350`; `deny` and `off` are a project's choice) |
| user configuration | configuration keys: defaults in `.tf/factory/config.yaml`, organization defaults from `org_defaults.config` of a company overlay, project overrides in `.tf/config/config.yaml` applied recursively in this order (dictionaries merged, other values replaced); own personas, roles and facets in `.tf/config/{personas,roles,traits}/` (tiers, profiles, routing, routing_notes, always_skills, standalone_skills, freshness, language_note, commit_language (`new_repo`), prices_usd_per_mtok, prices_checked, limits, managed_agents.models…; manifest keys `skill_overrides`, `packs`, `offered`, `pack_dirs`, `pack_sources`: `pack_dirs` also in the team lock), the project settings `.claude/factory-settings.json` (`language`, `commit_language`, `targets`: `claude`, `managed-agents`), the file layout of the `managed-agents/` target (`agents/`, `environments/default.yaml`, `README.md`), the schema of persona, role and facet files; skill frontmatter (`metadata.catalog`, `metadata.keywords`, `metadata.visibility`, `metadata.review`) |
| installation layout in a project | paths: `.claude/skills/`, `.claude/hooks/`, `.claude/agents/_generated/`, `.claude/tests/`, `.tf/factory/` (the engine, overwritten on update), `.tf/factory/packs/<id>/`, `.tf/factory/analyzers/`, `.tf/config/` (project configuration, an update does not touch it; since 9.0.0, earlier `factory/` and `factory/packs/<id>/` in the root directory), `docs/project/`, the files `CLAUDE.local.md`, `.claude/settings.local.json`, the `team-factory:begin`/`end` markers; the `.tf/` directory (`factory/`, `config/`, `reports/`, `register/`, `wip/`, `cache/`, `logs/`, `runs/`, `backup/`) |
| data formats | `docs/project/` artifacts (TL;DR, Handoff; Open questions; status; domain areas: Evidence / Named by the human / Candidates below the threshold), the checkpoint `.tf/wip/`, the questions file between personas `docs/project/questions.md`, scenarios `skill_evals/*.json`, the gate registry (`.claude/tests/skill_gate/<id>.json`, `.claude/skill-gate.json`), logs `.tf/logs/*.jsonl`, the run directory `.tf/runs/` (ignored by git), commit footers `Change: <key>` and `Flag: <key>` (the `commit-msg` hook of core-conventional-commits), knowledge base source registries `.claude/skills/*/references/zrodla.json` (`version`, `areas`, `sources`) and its cache `.claude/knowledge/<id>/` (`doc.txt`, `meta.json`, ignored by git); an analysis module `analyzer.yaml` (`name`, `prefix`, `title`, `description`, `version`, `review`, `skills`, `applies_when.files_any`, `incremental`, `tier0.script` or `tier0.rules`: a declarative rules file `rules.yaml` (`rules`: `id`, `title`, `files`, `exclude`, `forbid` or `require`, `head`, `severity`, `suggestion`, `basis`) executed by `.tf/factory/rules_scan.py`, `gate.min_recall`, `gate.max_false_positives`; the gate set `fixtures/<case>/repo/` and `expected.json` with a list of `{rule, file}`) and the tier-0 script output (JSON Lines: `rule`, `title`, `file`, `line`, `snippet`, `severity`, `confidence`, `evidence`, `basis`, `suggestion`), the finding id `<PREFIX>-<6 hex>`, the report `.tf/reports/<module>.md` (second line `Verdict:`, section `## Recommended actions` with checkboxes, read when merging), `.tf/reports/<module>.json`, the register `.tf/register/items.jsonl` (`id`, `kind`, `module`, `title`, `status`, `source`, `refs`, `created`, `updated`, `note`), variables `TF_ANALYZERS_PATH`, `TF_ANALYZE_NO_CACHE` |

The names of skills, personas and agents of an **overlay** or **mode** are the public API of that overlay or mode (the
version in its `pack.yaml`). **The "task → PR" loop is part of the core** (since 10.0.0): the main session agent `tf-task`, the skill `tf-task`
(the command `/tf-task`, several keys run in turn; since 22.0.0 — before that the skill `tf` and the command `/tf`), next to it the
skill `tf` (`/tf`: work with the factory without the loop) and `tf-design` (`/tf-design`: the design session), the scripts `.claude/skills/tf/scripts/run_report.py` (`start [--key KEY | --task TSK-n [--change CHG-n]]
[--source "<where from>"]`, `status`, `finish`), `intake.py` (`resolve [--json] <input>` with the fields `kind`, `key`, `tracker`,
`changes`, `options`, `intent`, `ask`, `next`; `tracker [<type> [--prefix P]]`; `fetch <KEY> [--json]`: a Jira ticket,
read only; `run_report.py start --key <KEY> --from-tracker`; variables `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`,
`JIRA_TOKEN`; the address only from `JIRA_BASE_URL`), the sections `tracker` (`type`, `prefixes`, `fields.acceptance`; `url`: only for
detecting a mismatch with `JIRA_BASE_URL`) and `deploy` (`smoke`, `rollback`, `rollback_minutes`, `approval`, `logs`) and `preview` (`url`, `start`, `routes`: where the dev server of a web
frontend answers, `tf onboard` fills it in; used by `ui_snap.py`)
of the operations card `.tf/config/operations.json`, the post-deployment check (`tf task deployed <KEY> [--version X]
[--timeout s]`, `tf task deployed <KEY> --rolled-back --by human:<id> [--note]`; the `deploy` field in `task.json`: `state` =
`ok` | `red` | `rolled-back`, `evidence`, `version`, `at`; evidence `evidence/deploy-<n>.json`; a `deploy` item on the
`waiting` list), closing a task (`tf task close <KEY> [--lesson "…" --by human:<id>] [--base <branch>] [--force --by
human:<id>]`; `tf task finding <KEY> add "<finding>" [--slice S<n>] [--round R]` and `… control <F-n> "<control>"`;
`run_state.py finding <directory> S<n> "<finding>" [--round R]`; the refusal of `run_state.py step … scope fail` without a finding
from this round; the fields `findings` (`id`, `text`, `slice`, `round`, `control`) and `closed` (`at`, `by`, `forced`, `lesson`)
in `task.json`; `tf status --all`; the file `docs/project/lessons.md`), the assignment of loop steps (the key `steps` in the configuration: step
identifier → `label`, `who`, `tier`; `tf config show steps`), task weight (`tf task weight <KEY> [--apply | --set <weight>] [--by]
[--reason] [--json]`, values `light`/`normal`/`full`, the fields `weight` and `weight_log` in `task.json`, the line `Weight:`
on stderr of `run_report.py start`, `run_state.py weight <directory> [--set <weight>]`), task mode (`tf task mode <KEY>
[plan|normal|auto]`, the factory's proposal `tf task mode <KEY> --propose [--apply] [--json]` — fields `proposal`, `reasons`, `applied`, `message`; `--apply` only lowers, never past the human's choice — the fields `mode` and `mode_by` in `task.json`, `run_state.py stage … --plan|--auto`, `run_state.py mode <directory>
[mode]`, `run_state.py approve <directory>`), the slice round limit (`run_state.py step … R<k>`: at most 2 rounds without a human decision, the third is a refusal with exit code 2;
after the `needs` stage two more; the field `limit` in `current` of the file `run.json`), the labels of `scope-reviewer` findings
(`[important]`, `[minor]`, `[pre-existing]`), the isolation level (`isolation`: `basic`, `sandbox` — the default, `container`; `tf isolation [<level>]` and `install.py --isolation <level>` set it only outside an agent session, the sandbox of the level: in the plugin layout through `tf code`, in the default layout in `.claude/settings.local.json` (the installer adds it only without a `sandbox` key; `tf uninstall` removes an unchanged one), `.tf/factory/isolation.py show [--json]` with the keys `level`, `source`, `sandbox_enabled`, `sandbox_where`, `in_container`, `gaps`; a company overlay can set it in `org_defaults.config`), a person's working style (`tf style [<name>] [--here]`; the file `~/.tf/preferences.yaml`, whose path is overridden by `TF_PREFERENCES`, and `.tf/config/me.yaml` as the last configuration layer, with the keys `style`, `task.default_mode`, `loop.blocked_slices`, `loop.confirm_each_slice`, `autonomy.operations` (tightening only); the configuration keys `styles` (with `claude.permission_mode`: the Claude Code permission mode in `.claude/settings.local.json`, the marker `style_permission_mode` in `.claude/factory-settings.json`), `task.default_mode`, `task.allowed_modes`, `loop.confirm_each_slice` with `run_state.py proceed <directory>`), a slice blocked by a question (the configuration key `loop.blocked_slices`, default `false`; `run_state.py block <directory>
S<n> --question`, `answer <directory> S<n> "<answer>" --by human:<id>`, `next <directory>`, `stage … --task`; the suffix
`· after: S<n>` / `· after: none` in a `plan.md` slice row; `events.jsonl` in the task directory with the fields `at`, `type`, `slice`,
`text`, `by`), the "waiting for you" list (`tf status [--json] [--open]`: the field `waiting` with entries `kind` = `plan` / `stop` / `slice`,
`what`, `details`, `question`, `options`, `recommended`, `how`, `since`; the field `needs_at` in `run.json`; the same `waiting` field
on the preview card), a pdi change cut task (`tf task start <CHG>-<TSK> --title … --change <CHG>
--cut <TSK>`, the fields `change` and `cut` in `task.json`), the task list (`tf status`; the script no longer maintains the index in the file `docs/project/changes/INDEX.md`:
an existing file becomes a fixed note), stop codes (`run_state.py stage <directory> needs --needs stop --code
<code>`; the list `STOP_CODES`: `question`, `split`, `source`, `plan-approval`, `tests`, `scan`, `budget`, `environment`,
`dependency`, `contract`, `permissions`; the field `stop_code` in `run.json`), stop messages
(`.claude/skills/tf/templates/stop_messages.json`: for each code `co`, `potrzeba`, `question`, `opcje` with the fields
`opcja`, `skutek`, `rekomendowana`, and `potem`; `run_state.py message <code> [--json]`), `run_state.py` (`stage`, `step`, `spec`, `flag`, `weight`, `mode`, `approve`, `message`, `trace`, `verify`, `tick`, `done`, `park`, `pr-body`, `finding`, `dashboard`), the PR description from the script (`run_state.py pr-body <directory> [--base <branch>]` → `.tf/runs/<KEY>/pr-body.md`; section headings "How it was checked", "Visual check", "System diff", "Risk", "How to roll back"; the operations card field `deploy.rollback`), the visual check of UI changes (`.claude/skills/tf/scripts/ui_snap.py`: `worth <directory> [--base <branch>]` → yes/no, exit 0/1; `capture <directory> --label before|after [--url U] [--route /p] [--viewport WxH,…] [--start [CMD]]` → `screens/<label>/<route>@<WxH>.png` + `index.json`; `compare <directory>` → `screens/compare.md`; exit codes 0 / 1 a shot failed / 2 call error, also a non-local address / 3 no browser or the server did not start; only localhost addresses; the `visual_check` section of `config.yaml`: `min_ui_files`, `min_ui_lines`, `keywords`; the `/tf` options `--visual` / `--no-visual` recorded by `run_state.py stage` in `run.json`; the PR section `## Visual check` exists only when the check is worth it, the dashboard `visual` object likewise),
`plan_drift.py` and `security_scan.py`, the options `.claude/tf.json`, variables `TF_DASHBOARD`, `TF_DASHBOARD_OPEN`,
`TF_SCAN_PATH`, `TF_SEMGREP_CONFIG`, the preview `.tf/runs/dashboard.html`, the run working directory `.tf/runs/<KEY>/`
(`run.json` with the fields `key` and `task_dir`, `parked.md`) and the task directory `docs/project/changes/<KEY>/` (`ticket.md`,
`spec.md`, `plan.md`, `report.md`, `task.json`, `evidence/`); the cut run report
`docs/project/changes/CHG-n/runs/TSK-n.md`. A cut run (`--task TSK-n`) is a task with the key `<CHG>-<TSK>`
(`docs/project/changes/CHG-n-TSK-n/`, `.tf/runs/CHG-n-TSK-n/`; `run.json` also has `change`, `task`, `flag`); the directory
`.tf/runs/cuts/<date>-<slug>/` (`story.md`) is no longer created. **Removed in 10.0.0** (the loop used to be the mode `mode-talos`):
the mode `mode-talos`, the command `/talos-story-run`, the agent `talos`, the path `.claude/skills/talos-story-run/scripts/`,
the options file `.claude/talos.json`, the variables `TALOS_DASHBOARD`, `TALOS_DASHBOARD_OPEN`, `TALOS_SCAN_PATH`,
`TALOS_SEMGREP_CONFIG` and the directory `.tf/runs/talos/`; the equivalents: `/tf-task`, the agent `tf-task`, `.claude/skills/tf/scripts/`,
`.claude/tf.json`, the variables `TF_*`, `.tf/runs/`. The mode `mode-team`: the skill `team-session`, the script
`.claude/skills/team-session/scripts/team_switch.py` (`on`, `off`, `status`).

The following do **not** belong to the public API:
- the content and wording of skills, prompts and facets, if they keep their scope;
- internal functions of scripts;
- heuristic thresholds (e.g. of the skill_hint hook);
- default tier models, which can be changed with a profile.

A change in behavior visible to a person (e.g. a different order of steps in a skill) is described in the CHANGELOG but
does not require a MAJOR.

## Which bump
| Change | Version |
|---|---|
| removing or renaming a skill, persona, agent, command, flag, variable, configuration key or `pack.yaml` key; a change of installation layout or data format that requires user action | **MAJOR**: a `### Breaking` section with migration instructions; a rename gets an entry in `.tf/factory/migrations.py` (`RENAMES`), so that `tf update` and `tf doctor --fix` correct project files by themselves |
| a new or stricter hook block **enabled by default** | **MAJOR**: the `### Breaking` section also gives the way to restore the previous behavior |
| a new skill, persona, command, flag, variable, key; a new block **disabled by default**; marking something as deprecated (it stays as an alias) | **MINOR**: sections `### Added`, `### Deprecated` |
| bug fixes, adding knowledge to a skill without changing its scope, documentation, tests | **PATCH**: sections `### Fixed`, `### Changed` |

Deprecation works like this:
1. The old name keeps working as an alias for at least one MINOR release. Example: `JEV_API_KEY` →
   `TYPESAFE_API_KEY` in 1.34.0.
2. The CHANGELOG has a `### Deprecated` section.
3. Removal happens only in a MAJOR.

## Overlay compatibility with the core (self-correction)
- `build.py check` (also in `tf doctor`) checks: the `requires.core` range of each overlay, required overlays,
  the working language overlay, name collisions (dimensions, agents, personas) and references to nonexistent skills.
- The reviewer panel at full weight: `tf task review <KEY> <reviewer> pass|fail [--note]` (the field `reviews` in
  `task.json`: `verdict`, `sha`, `at`, `note`), `run_state.py panel <directory> [--record <reviewer> pass|fail --note]
  [--base]`, the agent `spec-reviewer`; the `pr` stage of a full-weight task requires `pass` from `security-reviewer`
  and `spec-reviewer` for the current commit.
- Factory mode (plan 2026-11-20): `install.py --layout plugin|default` and `update.py --layout plugin|default` (the
  default: `default`, the classic layout in `.claude/`; an install whose manifest says `plugin` stays plugin until
  `--layout default`; the manifest field `layout`); the local plugin `.tf/plugin/` (`.claude-plugin/plugin.json` named `tf`, `skills/`, `agents/`,
  `hooks/hooks.json`, `RULES.md`, `session-settings.json`), the directory marketplace `.tf/.claude-plugin/marketplace.json`
  (`tf-project`, plugin `tf`), the hook `.claude/hooks/factory_rules.py` (SessionStart, the rules from `RULES.md`),
  `tf code [claude arguments]` (`--settings .tf/cache/session-settings.json`: the plugin's session settings with the
  isolation level, `TF_ISOLATION` names the level for the session; `isolation.py launch` builds the file), `tf cloud-setup [--apply]` (user settings: `extraKnownMarketplaces.tf-project`,
  `enabledPlugins["tf@tf-project"]`), `TF_CLAUDE`, `E0_LAYOUT=plugin`; factory skills keep their scripts and references
  under `.claude/skills/<skill>/` without `SKILL.md`.
- `tf work --once --budget <USD> [--key <KEY>] [--base <branch>] [--dry-run]` (`work.py`; configuration keys
  `work.budget_usd`, `work.task_budget_usd`, `work.permission_mode` (`acceptEdits` is the default, `dontAsk` or `plan`), `work.lock_hours`, `work.timeout_minutes`; the agent runs with `--strict-mcp-config` and only the allowed
  environment variables (additional ones: the human's variable `TF_WORK_ENV_ALLOW`, a comma-separated list); a warning and the field
  `root_changed` of the `event: end` entry when control files in the project copy change during the run; a refusal when the agent's control files in the worktree differ from the project copy, an
  `event: refused` entry with the field `drift`; the lock `.tf/locks/<KEY>.json`
  with the fields `pid`, `host`, `at`; the worktree `.tf/worktrees/<KEY>` on the branch `story/<key>`; the log `.tf/logs/work.jsonl`
  with entries `event: start` (`key`, `started`, `budget_usd`, `worktree`; before the agent is started) and `event: end`
  (`key`, `started`, `ended`, `exit`, `stage`, `worktree`); exit codes 0, 2, 3; the variable
  `TF_WORK_AGENT`).
- `metrics.py --after-update [--json]` (also in `tf doctor` and in the `tf metrics` report; the fields `update`, `from`, `to`,
  `before`, `after`, `warnings`, `notes`, `rollback`) and the log `.tf/logs/hook-blocks.jsonl` (`ts`, `hook`,
  `decision`) written by `hook_errors.record_block` from the hooks that block.
- `model_check.py [--json] [--today YYYY-MM-DD]` (also in `tf doctor`, exit code 1 on error): configuration keys
  `models_current`, `models_legacy`, `models_checked` and the optional `models_approved` (`source`, `models` with
  `until`; also in `org_defaults.config` and `team_defaults.config`, a lower layer only narrows; result fields
  `approved`, `approved_expired`, `usage`, `profile`; used by `profile.py`, which refuses a profile outside the list,
  and by the `model_guard` hook on `Agent|Task`, off without a list); the field `harness` (`claude_code`, `factory`, `packs`, `files`)
  in the entries of `.tf/logs/usage.jsonl`; the column "Noise band" and the note "(within the noise band)" in the
  `run_skill_evals.py` report.
- An overlay's references to elements of `optional_packs` overlays that are not installed are skipped without an error.
- Renames in the core and overlays are described by `.tf/factory/migrations.py`; the installer applies them after every
  update to project files (own personas, roles, overlays and skills), and `tf doctor --fix` on demand.
- From 19.0.0 the scripts no longer read the Polish forms from before 14.x (headings, labels, markers and values). The
  19.0.0 migration (`migrations.migrate_v19`, part of `migrate_values`) rewrites them to the English forms in the project
  files these scripts read: `.tf/wip/` checkpoints (`## Pitfalls and dead ends`), retrospective decisions
  `docs/project/archive/retro/*-retro.json` (`yes`/`no`/`later`), the knowledge base cache (`<!-- file: … -->`, with the
  hash in `meta.json`), the evidence bank tags in `02-domain/corpus.md` (`[mention]`, `[superseded]`, `[unverified]`), the
  factory block in `CLAUDE.md` / `CLAUDE.local.md` (`### Commands`, `### Language` — the installer does this before it
  rewrites the block, so the project's commands are kept), own skills (`## Domain concepts`, `## Version-dependent`,
  `## Sources`, `accessed`, `[unverified]`), own personas (`Run with`), `managed-agents/` files, the pdi change plan and
  artifacts (columns `Release`, `Flag`, `Kind`, `Value`, `Requirements`, `Unblocks`, `Verification`;
  `## Options considered`, `### Option`, `## Change targets`, `## Gate questions`, `## Second-model review`) and the
  pack-it reconstruction in `docs/project/00-reconstruction/` (`Incremental refresh:`, `(files)` batches, `[assumption]`,
  `[question]`, `(confidence: …)`, `(details: modules/…)`). From 20.0.0 the same migration also covers the Polish forms the scripts
  accepted without a mark: project record sections in `docs/project/` (`## Handoff`, `## Open questions`, domain areas
  `Evidence` / `Named by the human: yes|no` / `## Candidates below the threshold`, the requirements sections
  `Business rule`, `Out of scope`, `Current system`, `Constraints`, `For the stack decision`, `Quality attributes`, the
  brief's `MVP time budget:` / `MVP flow estimate:` / `Cost acknowledged:` with `days`/`weeks`/`months`, the markers
  `[assumption]`/`[unverified]`), checkpoint sections and the snapshot line (`## Steps`, `## Next step`,
  `- Branch: … · last commit: …`), `tf analyze` reports (`## Recommended actions`, `## Analysis history`,
  `Verdict:`), `## Execution and verification` in `lessons.md`, research verdicts (`confirmed`/`partial`/`unconfirmed`/
  `contradicted` instead of P/C/N/S), run security summaries (`## Security`), open tasks (`ticket.md`: `Source: … ·
  fetched:`, the data note, `## The change's intent`; `spec.md`: Given/When/Then in multi-line criteria; `plan.md`:
  `after: none`; hashes of approved files follow, as in 14.0.0), the reconstruction report headings, stack rows and the
  `<!-- card: -->` mark, and pack-it dossiers (the pack-it migration owns the dossier maps).
  The same 19.0.0 step also drops the last compatibility forms. Slice ids are `S<n>` only: `K<n>` from before 14.0.0
  is no longer read by `task_state`, `run_state`, `plan_drift`, `task_weight`, `run_report` or the migrations. In open
  tasks the migration turns `K<n>` into `S<n>` across the whole task: the `plan.md` slice lines and references such as
  `after: K1`, the `task.json` slice keys, evidence paths and the `slice` of findings, the evidence files
  `evidence/K<n>-<m>.json` (renamed, with `slice` inside), `events.jsonl`, and the task's run in `.tf/runs/<KEY>/`
  (the current and held slice in `run.json`, the `security/K<n>` scan folders). The plan's approval hash is recomputed
  only where it matched the old file, and closed tasks are left alone. The commit trailers `Rework-Cause:` (`spec-gap`,
  `agent-error`, `requirement-change`, `unknown`) and `Slice S<n>:` are read in English only. Old commits cannot be
  rewritten, so `metrics` counts a pre-19.0.0 Polish cause as `unknown`, `retro_data` shows it under its raw value,
  and a `Kawałek K<n>` footer is not mapped to a slice. The `project_record.py --hook-snapshot` hooks take the
  arguments `session end` and `context compaction`. `migrations.settings_v19` rewrites the old `koniec sesji` and
  `kompaktowanie kontekstu`: the installer runs it on the project's settings before merging the factory hooks, which
  avoids a duplicate hook, and `migrate_values` runs it on `.claude/settings.json` and `.claude/settings.local.json`,
  keeping the file's own formatting.
- In the factory repository, `python3 tools/workspace.py refs` ensures that the core does not name overlay elements
  (unless it names the overlay in the same line, e.g. "(pack-it)"), and an overlay names only elements of overlays it
  depends on (`requires.packs`, `optional_packs`). `python3 tools/workspace.py matrix` builds and tests the core alone,
  each overlay separately and all together.

## Releasing the factory
Releases are automatic ([docs/RELEASING.md](../../docs/RELEASING.md)):
1. Commits and PR titles use the Conventional Commits format; the type decides the bump according to the table above
   (`feat` → MINOR, `fix`/`perf` → PATCH, `!` or `BREAKING CHANGE:` → MAJOR).
2. After a merge to `main`, the `release` workflow computes the number (`semver.py`), writes `core/factory/VERSION` and the entry
   `## [X.Y.Z] — YYYY-MM-DD` in the CHANGELOG, commits `chore(release): X.Y.Z`, creates the tag `vX.Y.Z` and a GitHub Release.
3. `python3 .tf/factory/build.py check` (in an assembled project, `tools/workspace.py check`) checks:
   - version correctness;
   - the order of entries;
   - VERSION matching the CHANGELOG;
   - since 3.0.0: the kind of bump matching the entry's sections (earlier, since 1.35.0, in claude-team-factory).

   The `factory-checks` and `release` workflows do the same before the release commit.
4. A manual release (`python3 scripts/release.py minor|major|patch|X.Y.Z` in a `chore(release): X.Y.Z` PR) serves only to
   override the result from commits, e.g. to add a `### Deprecated` section.
5. You do not change a released version. A fix is a new PATCH version.

`update.py` compares versions by SemVer precedence, including pre-release versions (`1.36.0-rc.1 < 1.36.0`),
and on a MAJOR release it warns and points to the `### Breaking` sections (in older entries: "Niezgodne").

## History
Versions up to 2.45.0 are the history of claude-team-factory, from which the core was separated. Versions 1.0.0-1.34.0 were released before
the bump-kind check was introduced. Three PATCH releases (1.28.1, 1.29.2, 1.29.3) had a
"Nowe" (New) section, but they added evaluation results and documentation, not a new API. In line with SemVer rule 3, we do not
change released versions.
