# New overlay or mode

A guide for the factory author (the tf repository). The full list of `pack.yaml` keys and overlay files belongs to the
public API: `core/factory/PUBLIC_API.md`.

## Overlay or mode
- **Overlay** (`packs/pack-<name>/`, `id: pack-<name>`): domain knowledge: skills, roles, personas, consultants.
  Installed when the project needs it.
- **Mode** (`modes/mode-<name>/`, `id: mode-<name>`, `kind: mode`): a way of working switched on by a person: a main
  session agent, a process skill, scripts, permissions, a `GUIDE.md` guide.
The same format and loader; the installer checks that `kind: mode` lives in `modes/` and an overlay in `packs/`.

In a Claude Code session started in the tf repo, the `tf-new-pack` skill leads you through this
(`.claude/skills/tf-new-pack/`, it does not go into projects): it asks about scope, prefix, dependencies and roles,
proposes scenarios, and calls the generator and the gates.

## A skeleton with one command
```
python3 tools/workspace.py new-pack <name> [--kind pack|mode] [--prefix abc-] [--title "…"] [--description "…"]
                                    [--skill abc-name] [--role role-name] [--no-check]
```
Creates:
- `pack.yaml` with version `0.1.0`, `default: false`, `requires.core` from the current core version to the next MAJOR,
  and one dimension (`facets`) with the prefix;
- a skeleton of the skill `skills/<prefix>…/SKILL.md` and of the scenarios `tests/skill_evals/<skill>.json`;
- optionally a role `roles/<role>.yaml` with that skill; for a mode, `GUIDE.md`;
- an entry in the CI matrix (`.github/workflows/factory-checks.yml`, before `all`).

Then it runs `workspace.py check --packs <id>` and `refs` and prints a to-do list (unless `--no-check`).
An existing directory, a taken prefix, a bad name or a skill outside the prefix → exit code 2 with no changes on disk.
**The scenario skeleton deliberately fails the gate** (`skill_gate.py --status` and hint hits) until real scenarios
and content exist.

## Order of work
1. **Scope and boundaries**: which questions the overlay should handle and which belong to existing skills (check
   `python3 tools/workspace.py assemble --packs all` and `.claude/catalog.md` in the workspace).
2. **Prefix**: short, one per overlay or dimension (`facets`); it must not collide with the core or another overlay.
   `order` sets the order of dimensions in the skill list.
3. **Dependencies**: `requires.packs` (the overlay does not work without another) or `optional_packs` (references are
   skipped when the overlay is absent). Skill content may refer only to those overlays; `refs` enforces this.
4. **Scenarios before content** (core-skill-authoring): 2× trigger with a gap, 1× no-trigger with a neighbor.
5. **Skill content**, roles and personas (`roles/`, `personas/`); with many rarely used skills consider
   `skill_visibility.name_only_prefixes`: the description does not take budget from the skill list.
6. **Gates** in the workspace: `python3 factory/skill_gate.py <skill>` and `--hints` (also on `--packs all`), then
   `python3 tools/workspace.py sync-gate --out .work/<id>`.
7. **Verification**: `python3 tools/workspace.py check --packs <id>`, `check --packs all`, `refs`; a PR titled
   `feat(<id>): …`.

## An overlay outside the factory repository
An overlay can live in another repository (e.g. domain knowledge together with its sources). The contract is the same
as in `packs/`: `pack.yaml` with `kind` and an id prefix (`pack-`/`mode-`), `requires.core`, scenarios and the gate
registry in `tests/`.
- Installation in a project: `install.py --pack-dir <directory|git address> --add <id>` (or `update.py`/`tf` with these
  flags). The source is a directory with `pack.yaml`, a directory with `*/pack.yaml`, or a git repository
  (`#<tag|branch>`; without it the latest `vX.Y.Z` tag, and without tags the default branch). The manifest (and the
  team lock) remembers the source in `pack_dirs`, so an update downloads the overlay again; `--drop-pack-dir <source>`
  forgets it.
- The installer refuses when the id is taken by a factory overlay, when the source is gone while an overlay from it is
  selected (give the new `--pack-dir` location), and when `skill_audit.py` reports a high weight in the overlay's
  skills.
- Checking together with the factory: `python3 tools/workspace.py check --packs pack-it,<id> --pack-dir <directory>`
  (workspace `.work/<overlays>+ext`); `sync-gate --out <that workspace> --pack-dir <directory>` writes the gate results
  to `<directory>/tests/skill_gate/<id>.json`.

## A company overlay
Standards and defaults of one organization: a separate set in the `org/` directory (generator
`org/new_org_pack.py`, template `org/template/`, guide `org/README.md`). A company overlay is an ordinary overlay with
the `org_defaults` key:
- `config`: organization defaults between the engine and the project (`autonomy`, `tiers`, `profiles`,
  `default_profile`, `work`, `loop`, `steps`, `task`, `commit_language`); read by `build.py`, `guard_bash` (the
  autonomy policy still only tightens), `tf risk`, `tf work` and `tf config show` (the "organization" source);
- `operations.tracker`: the default tracker, prefixes and `fields` of the operations card; without an address (`url`).
At most one overlay with `org_defaults` per project; a key outside the list is a `build.py check` error with no effect.
The rules module from `tier0.rules` is run by the core scanner `.tf/factory/rules_scan.py`; the overlay's `semgrep.yml`
goes to `.tf/factory/packs/<id>/` and into the loop-slice scan.

## Versioning
- The core version and CHANGELOG are computed by the release workflow from Conventional Commits (`docs/RELEASING.md`).
  Nothing bumps an overlay's version (`version` in `pack.yaml`) automatically: you change it by hand following SemVer
  [a recommendation, not a rule checked in CI]: a new skill or role is a MINOR, renaming or removing a skill, role or
  persona is a MAJOR with an entry in `factory/migrations.py` (renaming a skill as a MAJOR is a decision from
  2026-10-21).
- `requires.core` narrows the range when the overlay starts using features of a newer core.

## Project data migrations
When a new overlay version changes the format of files that its skills assume in the project (e.g. headers of a
document checked by a script), add `packs/<id>/migrations.py` with a function `migrate_values(root, dry) -> list[str]`:
it returns the changed paths, with `dry=True` it writes nothing, and a repeated call after migration returns an empty
list. The installer copies the file to `.tf/factory/packs/<id>/`, and the core's `migrations.migrate_values` calls it
on update; the core does not name overlay skills. Example: `packs/pack-it/migrations.py` (legacy dossier).
