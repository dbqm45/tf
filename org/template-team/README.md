# {{TITLE}} team pack (`pack-{{COMPANY}}`)

The standards and defaults of one team, on top of the company standards (`pack-{{ORG}}`). Keep this directory in the
team's (or the company's) own repository, not in the factory repository.

Configuration layers in a team project: engine ← company ← **team** ← project ← person (`tf config show` shows the
source of every value). The team **can only tighten** the company autonomy policy and **can only narrow** the allowed
task modes; it cannot unblock anything the company has forbidden.

## What to fill in
Every place to change has a `TODO` marker. List them: `grep -rn TODO .`

| File | What to write |
|---|---|
| `pack.yaml` → `description` | one sentence in English (shown by `tf list`) |
| `pack.yaml` → `team_defaults.config` | only what makes the team differ from the company (same keys as the company `org_defaults`) |
| `pack.yaml` → `team_defaults.operations.tracker.prefixes` | the team's issue key prefixes |
| `analyzers/{{COMPANY}}-standards/rules.yaml` | team rules a pattern can check (`tf analyze`, no model), with examples in `fixtures/` |
| `skills/{{PREFIX}}standards/` | team rules that need judgement: `SKILL.md` is the index, the areas are in `references/` — write the scenarios in `tests/skill_evals/` first |
| `semgrep.yml` | the team's semgrep rules in the scan of every `/tf` loop chunk |
| `settings.json` | the team's Claude Code permissions (e.g. `deny` for tools the team does not use) |

Do not repeat the company standards: they apply in the project through the `pack-{{ORG}}` pack. This pack holds only
what applies in the team on top of them (e.g. backend: API and migration rules; frontend: the component library).

## Checking and installing
```
python3 tools/workspace.py check --packs pack-it,pack-{{ORG}},pack-{{COMPANY}} --pack-dir <company repo> --pack-dir <this directory>
tf install --pack-dir <company repo> --pack-dir <team repo> --add pack-{{COMPANY}}
```
The company pack installs by itself (`requires.packs`). To change later: edit the files, bump `version` (SemVer), add a
tag; projects get the change on `tf update`. The overall guide: `org/README.md` in the factory repository.
