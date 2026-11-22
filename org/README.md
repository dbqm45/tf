# Company settings (the company overlay)

Standards and default settings of one organisation for all of its projects with the factory. You make them once and
change them rarely. This directory does not go into projects: it is the kit for preparing the company's pack.

| In the directory | What it is |
|---|---|
| `new_org_pack.py` | generator: copies the template into the company's repository and fills in the name, prefix and core version |
| `template/` | the template of the `pack-<company>` pack with `TODO` fields |
| `template-team/` | `pack.yaml` and `README.md` of a team overlay (`--team`); the other files come from `template/` |
| `standards_from_docs.py` | standards from the company's documents: splitting into sections, checking the assignment and quotes, overlay files |
| `README.md` | this guide |

## What the company pack sets
| Part of the pack | What it does in every project |
|---|---|
| `pack.yaml` → `org_defaults.config.autonomy.operations` | blocks agent operations across the company (`deny`); a project cannot loosen it |
| `pack.yaml` → `org_defaults.config.autonomy.triage` | paths that `tf risk` always marks for a human review |
| `pack.yaml` → `org_defaults.config.work`, `default_profile`, `commit_language.new_repo` | `tf work` limits, the cost profile, the commit language in a new repository (the conversation language is not a setting) |
| `pack.yaml` → `org_defaults.config.task.allowed_modes` | task modes allowed in the company; a person's work style (`tf style`) chooses only among them |
| `pack.yaml` → `org_defaults.config.models_approved` | models allowed in the company (an alias or an identifier, optionally `until`); a team and a project can only narrow the list. Checked by `model_check.py` (`tf doctor`), `profile.py` refuses a profile outside the list, the `model_guard` hook blocks a delegation with such a model and warns at the session start. Without a list nothing changes |
| `pack.yaml` → `org_defaults.operations.tracker` | the tracker, issue key prefixes, the Jira field with the criteria (no address and no token) |
| `analyzers/<company>-standards/rules.yaml` | standards checked **without a model** (`tf analyze`): forbidden APIs and imports, required headers, file names |
| `semgrep.yml` | semgrep rules in the scan of every slice of the `/tf-task` loop |
| `skills/<company>-standards/` | standards that need judgement: `SKILL.md` is the index, the area findings are in `references/` (`ui.md`, `api.md`, `data.md`, `releases.md`) — the agent reads only the area of its task |
| `settings.json` | Claude Code permissions for the whole company |

The pack **contains no** addresses or tokens (Jira takes them from the variables `JIRA_BASE_URL`, `JIRA_EMAIL`,
`JIRA_API_TOKEN` or `JIRA_TOKEN`) and no connections to tools (live Confluence and Jira are MCP servers in the Claude
Code configuration).

## How to generate it — step by step
1. **The skeleton** (in a clone of the factory repository):
   ```
   python3 org/new_org_pack.py acme --out ~/repos/acme-factory --title "ACME"
   ```
2. **Fill in the `TODO` fields** (`grep -rn TODO ~/repos/acme-factory`), in this order:
   1. `pack.yaml` → `org_defaults`: the autonomy policy, the paths for review, the limits, the tracker;
   2. `rules.yaml` — every finding that can be written as a pattern (with a violation example in
      `fixtures/violations/` and compliant code in `fixtures/clean/`);
   3. the scenarios `tests/skill_evals/<company>-standards.json` — a question per area;
   4. the area files `references/<area>.md` — only the findings that need judgement; the index in `SKILL.md`;
   5. `semgrep.yml` and `settings.json`, if the company needs them.
3. **Check** (in the factory repository):
   ```
   python3 tools/workspace.py check --packs pack-it,pack-acme --pack-dir ~/repos/acme-factory
   ```
   While the scenarios have `TODO`, only the skill gate fails. After filling them in, in the workspace:
   `python3 .tf/factory/skill_gate.py acme-standards` and
   `python3 tools/workspace.py sync-gate --out <workspace> --pack-dir ~/repos/acme-factory`.
4. **Publish** the directory as the company's git repository with the tag `v0.1.0`.
5. **Install it in a project:** `tf install --pack-dir <the company repository's address> --add pack-acme`.
   `tf config show` shows the company's values (source "organisation"), `tf analyze --only acme-standards` the rules.

## How to generate it from the company's documents (e.g. Confluence)
When the standards are already written down, you do not retype them. Everything that can be checked is done by the
`org/standards_from_docs.py` script; the model only assigns the findings to an area and a kind (step 3), and the script
checks the result.
1. **The documents into the directory** `~/repos/acme-factory/sources/`: an export from Confluence (HTML), Word (`.docx`),
   PDF (through `pdftotext`) or Markdown. In a session connected to Confluence (an MCP server) the agent can fetch them
   itself — then it saves a copy with the address and the fetch date. The `sources/` directory does not go into
   projects; add it to the company repository's `.gitignore` if the documents are confidential.
2. **Splitting into sections (script):**
   ```
   python3 org/standards_from_docs.py split ~/repos/acme-factory
   ```
   A section is the text under one heading, with the full heading path (`sources/sections.jsonl`); sections with the
   same content are marked as duplicates. The script also writes `sources/TASK.md` — the instruction for the agent with
   the result format and the list of sections to cover.
3. **The assignment (model):** in a Claude Code session in the overlay directory: "Do sources/TASK.md". The agent writes
   `sources/assignment.json`: every finding (`findings`) with an area (`area`: `ui`, `api`, `data`, `releases`, `common`),
   a kind (`kind`: `pattern` — a rule with a violation example and compliant code; `judgement` — into the area file),
   a verbatim quote (`quote`) and contradictions (`conflicts_with`); general practice goes into `skipped` with a reason.
4. **The check (script, no model):**
   ```
   python3 org/standards_from_docs.py check ~/repos/acme-factory
   ```
   It rejects: a quote that is not in the section; a section with no finding and no reason to skip; an unknown area;
   a contradiction without a pair; a rule that does not load or does not detect its violation example (or detects the
   compliant code); examples that would make the rule module's gate fail. The agent fixes the errors in
   `assignment.json`.
5. **The overlay files (script):**
   ```
   python3 org/standards_from_docs.py apply ~/repos/acme-factory
   ```
   The findings that need judgement go to `references/<area>.md` (common ones to `SKILL.md`) with the quote and the
   source, the patterns to `rules.yaml` with examples in `fixtures/`, and `sources/REPORT.md` collects the
   contradictions, the skipped sections and the duplicates. The script changes only the `from-docs` blocks — findings
   and rules added by hand stay. Without a passed check it writes nothing.
6. **The human's review:** `sources/REPORT.md` — settle the contradictions and review the area assignment. The script
   has already checked the quotes. Then the scenarios in `tests/skill_evals/` and steps 3–5 of the list above.

**When a document changes:** `split` shows the new, changed and removed sections since the last `apply`, and
`TASK.md` lists only those — the agent assigns only the changes, and `check` points to findings whose quote has
disappeared from the source.

The model cost is one assignment of the sections (step 3); it depends on the size of the documents [assumption: not
measured on company documents]. The same process works for a team overlay (`--team`).

## Standards from skills through the `standards` add-on
When the company already has standards skills (in a git repository, with links to Confluence), you do not retype them
into the overlay. In `pack.yaml` → `org_defaults.config.addons.standards` you give the repository URL
(`sources.<name>.git`, `ref`, `dir`) and `install: true`. In every project with the overlay `tf learn` installs the
add-on by itself, clones the repository, reads the skills and the linked pages (the agent reads Confluence through the
session's MCP, paragraphs without lists — a cheap model in a session with a quote check) and writes the rules into
`.claude/rules/addon-standards-*.md`. A team overlay adds its own sources under its own name
(`team_defaults.config.addons.standards.sources.<team>`); a project turns a source off with
`addons.standards.sources.<name>.enabled: false` in `.tf/config/config.yaml`. `tf config show addons` shows the values
and where they come from. Details: `addons/standards/README.md` in the factory repository.

## A team overlay
When the teams in the company work differently (e.g. the backend has its own API and migration rules, the frontend a
component library), each team gets an overlay above the company's:
```
python3 org/new_org_pack.py acme --team backend --out ~/repos/acme-backend-factory --title "ACME Backend"
```
This creates `pack-acme-backend`, which requires `pack-acme`. It has the same layout as the company overlay, but in
`pack.yaml` a `team_defaults` section (instead of `org_defaults`) and the skill prefix `backend-`. You write in only what
makes the team different from the company.
- **The order of the layers:** engine ← company ← team ← project ← person. `tf config show` shows the source of every value.
- **The limits:** a team, a project and a person only tighten the company's autonomy policy; the allowed task modes
  (`task.allowed_modes`) and the approved models (`models_approved`) are the intersection of the layers — nobody lower
  brings back a mode or a model the company took away. Other values (`tf work` limits, the cost profile, languages)
  the team changes for its projects.
- **The tracker:** the team's issue prefixes replace the company's; the type and the fields come from the company.
- **The check:** `python3 tools/workspace.py check --packs pack-it,pack-acme,pack-acme-backend --pack-dir
  ~/repos/acme-factory --pack-dir ~/repos/acme-backend-factory`.
- **Installation in a team's project:** `tf install --pack-dir <company repo> --pack-dir <team repo> --add
  pack-acme-backend` (the company overlay comes along by itself). A project can have at most one team overlay.

## Changes later
A change of the standards is a change in the company's repository: fix the files, bump `version` in `pack.yaml` by
SemVer (a new rule or area — MINOR, removing or renaming a skill — MAJOR), check (step 3), add a tag. Projects get the
change with `tf update`. Generating again is not needed: the generator only makes the first skeleton and refuses to
write into an existing directory.
