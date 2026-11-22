# {{TITLE}} company pack (`pack-{{COMPANY}}`)

Standards, rules and defaults of {{TITLE}} for every project that runs the tf factory. Keep this directory in the
company's own repository, not in the factory repository.

## What to fill in
Every place to change has a `TODO` marker. List them: `grep -rn TODO .`

| File | What to write |
|---|---|
| `pack.yaml` → `description` | one sentence in English (shown by `tf list`) |
| `pack.yaml` → `org_defaults.config.autonomy` | which agent operations to block across the company (`deny`); the organization can only tighten |
| `pack.yaml` → `org_defaults.config.autonomy.triage` | paths a person at the company always reviews (`tf risk`) |
| `pack.yaml` → `org_defaults.config.work` | spending limits for unsupervised work (`tf work --once`) |
| `pack.yaml` → `org_defaults.operations.tracker` | tracker, issue key prefixes, the field with acceptance criteria |
| `analyzers/{{COMPANY}}-standards/rules.yaml` | **rules a pattern can check**: banned APIs and imports, required headers, file names — they run without a model (`tf analyze`) |
| `analyzers/{{COMPANY}}-standards/fixtures/` | a violation example for each rule (`violations/`) and compliant code (`clean/`) — the module gate |
| `skills/{{PREFIX}}standards/SKILL.md` | the index: a few shared rules and the table of areas — keep it short, every task with this skill reads it |
| `skills/{{PREFIX}}standards/references/<area>.md` | the rules of one area (UI, API, data, releases) that need judgement; the agent reads only the file for its task's area |
| `tests/skill_evals/{{PREFIX}}standards.json` | one question per area (with `none` for rules of another area) and 1 question unrelated to the company — **before** the skill content |
| `semgrep.yml` | the company's semgrep rules (patterns in code syntax) for the scan of every `/tf-task` loop slice |
| `settings.json` | Claude Code permissions for the whole company (`allow`, `deny`); added to the project settings |

**Rules first, then the skill.** A rule that a pattern can express goes into `rules.yaml`, not into the skill: the
factory scanner points to the violation with file and line at no token cost, and the agent does not have to read the
rule in every session. The skill gets what a pattern cannot check. Semgrep rules (patterns in code syntax, e.g. "call
without a timeout") go into `semgrep.yml` at the pack root — the `/tf-task` loop uses it in the scan of every slice. An empty
rule list changes nothing in the scan.

**Split by area.** A change to the look alone should not load the API rules. That is why `SKILL.md` is an index and the
area rules live in `references/`; narrow the rules in `rules.yaml` to the area's directories with the `files` field.
Make a separate skill per area only for a large area that people ask about in different words: several similar skills
compete for the same question and the model may pick the wrong one.

More skills: another `skills/{{PREFIX}}<name>/` directory with a scenario file in `tests/skill_evals/`. Your own roles
and personas: `roles/`, `personas/` (same format as in the factory packs).

## What does not go here
- **Addresses and tokens** (Jira, Confluence, cloud). The Jira address and credentials live only in environment
  variables (`JIRA_BASE_URL`, `JIRA_EMAIL` with `JIRA_API_TOKEN` or `JIRA_TOKEN`).
- **Tool connections** (Confluence, live Jira, Slack). These are connections (MCP servers) in the Claude Code
  configuration or in settings managed by the organization, not in the factory.
- **General knowledge** the model already has — it adds nothing and takes up context in every session.

Full guide, including generation from company documents (e.g. Confluence): `org/README.md` in the factory repository.

## Checking
Rules without a model, in a project with the pack: `tf analyze --only {{COMPANY}}-standards` (report in `.tf/reports/`)
and the module gate `python3 .tf/factory/analyze.py gate --module {{COMPANY}}-standards`.

In the factory repository:
```
python3 tools/workspace.py check --packs pack-it,pack-{{COMPANY}} --pack-dir <this directory>
```
The skill gate fails while the scenarios still contain `TODO`. That is expected. Once filled in, in the workspace:
`python3 .tf/factory/skill_gate.py {{PREFIX}}standards`, then
`python3 tools/workspace.py sync-gate --out <workspace> --pack-dir <this directory>`.

## Installing in a project
```
tf install --pack-dir <this directory or a git repository URL> --add pack-{{COMPANY}}
```
The factory remembers the source, so `tf update` fetches the new pack version by itself. Values from `org_defaults`
appear in `tf config show` as "organisation". A project overrides them in `.tf/config/config.yaml` (the autonomy policy
cannot be loosened) and in `.tf/config/operations.json`.

## Versions
Describe the change in the commit and bump `version` in `pack.yaml` following SemVer: a new skill or rule — MINOR;
removing or renaming a skill — MAJOR.
