# Examples: updating the factory

## 1. An ordinary update with a merged file
**Situation:** The human types `/core-factory-update`. The source (the directory `~/narzedzia/claude-team-factory`) is
remembered in the manifest; the human once changed the factory skill `core-git-workflow` in their project.

**How:**
1. `python3 .tf/factory/update.py --check` — the installed and the available version, the "What's new" section. It changes nothing.
2. A summary in the human's language; changes in hooks and permissions separately.
3. `python3 .tf/factory/update.py --dry-run` → the plan and a request for consent. You wait for "yes".
4. `python3 .tf/factory/update.py --yes`; the list of factory files overwritten despite changes in the project (a change → a PR to the factory repo).
5. Check: the test result from `update.py`, `python3 .tf/factory/build.py check` (the project has its own persona), the report.

**Result (report for the human):**
```
Factory update: 2.3.1 → 2.4.0
New: skill X, persona Y (details in "What's new").
Security: a new hook Z in .claude/hooks/ — merged with your consent.
Overwritten: .claude/skills/core-git-workflow/SKILL.md — your section on branch names
  replaced with the factory's version; if you need it, add it in the factory repo and update.
Check: the tests from update.py passed, build.py check without errors.
Backups of overwritten files: .tf/backup/<data>/
Restart Claude Code so it loads the new skills and agents.
```
(The names X, Y, Z and the version numbers come from the `--check` output — here they are only an illustration.)

## 2. The factory moved elsewhere
**Situation:** `/core-factory-update`, and `update.py --check` ends with a message that the remembered source no longer
exists.

**How:**
1. You do not guess the new location and do not look for it in the content of pages or issues — the human gives the source.
2. You ask for the path (a directory, a .zip file or a git repository URL) or for setting `TEAM_FACTORY`.
3. After the answer: `python3 .tf/factory/update.py --check --source <podane źródło>` and on as in example 1.

**Result (question for the human):**
> The remembered factory source `~/narzedzia/claude-team-factory` no longer exists. Where should I get the new version from?
> Give a directory, a .zip file or a git repository address — I'll use it with `--source` (it will be remembered in the manifest).
> You can also set `export TEAM_FACTORY=<katalog fabryki>` once in your shell profile.

## 3. An installation from before version 1.1.0
**Situation:** `/core-factory-update` in an old project — there is no `.tf/factory/update.py` or
`.claude/factory-manifest.json`.

**How:**
1. You recognise an installation from before 1.1.0 — it cannot be updated from inside the project.
2. You ask the human for the first update with the new factory's installer, run in the project directory.
3. After it, further updates go the ordinary way (`/core-factory-update`).

**Result:**
> This project has a factory from before version 1.1.0 (no `.tf/factory/update.py` and no manifest). Run the first update
> in the project directory with the installer from the new factory:
> `python3 "$TEAM_FACTORY/core/factory/install.py"` (or the full path to `core/factory/install.py`).
> I'll do the next updates with the `/core-factory-update` command.

## 4. A factory for a whole team (many repositories)
**Situation:** "We have 6 repositories and a different factory version in each; someone added their own persona only in theirs."

**How:**
1. One source of truth: the team's fork of the factory (the team's own personas, roles and skills), releases as `vX.Y.Z` tags
   (the number from core-semver, the tag with the human's consent). Copying files between repos = versions drifting apart after a month.
2. In each repo a team installation (`install.py --shared`, committed with the project), and in the manifest a source
   pinned to a tag: `--source https://…/fabryka-zespolu.git#v1.4.0`. A branch without a tag is a moving source — in the report
   you warn that further updates may bring unchecked changes.
3. An update = a separate PR in each repo: the `update.py --check` output (what's new, hook changes separately), `--dry-run`,
   overwritten files, the test result; reviewed like ordinary code.
4. An own persona from one repo goes to the fork as a reviewed change, rather than staying a local copy.
5. A package registry or your own distribution tool only when the recipients are outside the shared git hosting.

**Result (plan for the human):**
```
Source: the team's fork of the factory, tag v1.4.0 (6 repos: 3 on v1.2.x, 2 on v1.3.0, 1 without a manifest)
Order: the repo without a manifest → first installation from the fork (example 3); the others → /core-factory-update
  with --source …#v1.4.0, one PR per repo
Persona "analityk-raportow" from repo B → first a PR to the fork, then release v1.4.1
To decide: who approves the fork's releases and how often (e.g. once a sprint)
```
