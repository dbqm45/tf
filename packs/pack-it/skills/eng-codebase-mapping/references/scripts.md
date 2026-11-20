# Scripts of the skill — catalogue

All scripts live in `.claude/skills/eng-codebase-mapping/scripts/`, use only the Python standard library, read the repository without
changing it, do not run its code and make no network calls. Run them; read their `--help` for the full flag list.

## Map and history
| Script | What it does | Typical call |
|---|---|---|
| `repo_inventory.py` | languages, build files, exclusions, modules and reading batches by token budget (tokens ≈ bytes / 4) | `repo_inventory.py <repo> [--json] [--budget-tokens 60000]` |
| `code_graph.py` | import graph for Python, TS/JS, Java, C#, Go: scored entry points (also from registries), workspace-package edges, groups with direction, upstream pairs, hubs (barrels excluded), runtime vs lazy cycles | `code_graph.py <repo> [--impact <file>] [--focus <path> [--focus <path>]] [--top N] [--group-depth N] [--json]` |
| `git_territory.py` | territory from history: rankings, quarters, co-change pairs and hubs, hotspots, contributors, bus factor | `git_territory.py --repo <repo> --all` (= every section except `--authors` and `--bus-factor`) |
| `standards_scan.py` | convention signals counted in code, with shares, `file:line` examples and exceptions — data for a standard | `standards_scan.py <repo> [--json]` |
| `schema_scan.py` | tables, columns, constraints, relations from SQL migrations (incl. Flyway), JPA, EF Core | `schema_scan.py <repo> [--json]` |

`code_graph.py` details: `--impact <file>` gives the reach of a change (two steps up plus the tests); one `--focus` shows imports across
a module boundary, two `--focus` show only the seam between the pair; a group holding more than 40% of files is split one level down.

`git_territory.py` flags: `--repo`, `--since` (default `12.months`), `--top`, `--depth`, `--exclude` (repeatable noise regex),
`--by-quarter`, `--cochange`, `--max-files` (default 30), `--authors PATH`, `--hotspots`, `--bus-factor`, `--min-commits`,
`--active-days` (default 90), `--all`, `--json`. Exit code 2 = no git repository or bad arguments.

## Reconstruction chain
Used by eng-project-reconstruction and eng-legacy-dossier: inventory → scan → module cards → evidence check → export or refresh.

| Script | What it does | Call |
|---|---|---|
| `recon_scan.py` | runs inventory, graph, territory, standards and schema in one go; full JSON to `--out`, a ≤ 60-line summary on screen | `recon_scan.py <repo> --out <dir> [--budget-tokens N]` |
| `recon_cards.py` | module cards (JSON from workers) → `modules/<card>.md` with `file:line` evidence | `recon_cards.py <modules/> --repo <repo> [--summary] [--rules] [--into report.md] [--prev <old cards>]` |
| `recon_check.py` | evidence check of a report | `recon_check.py <report.md or dir> --repo <repo> [--json] [--final]` |
| `recon_manifest.py` | records commit, cost, batch and file hashes; tells which cards to redo after changes | `recon_manifest.py write <repo> --out <manifest.json>` / `recon_manifest.py diff <repo> --manifest <manifest.json>` |
| `recon_refresh.py` | incremental refresh in steps without a model | `recon_refresh.py <prep, finish or apply> <repo> [--dir docs/project/00-reconstruction] [--cost-usd X]` |
| `recon_export.py` | reconstruction → JSON per `reconstruction-export.schema.json` | `recon_export.py <dir> --repo <repo> [--out FILE]` |

**The evidence rule of `recon_check.py`:** every `file:line` must point to an existing file and line; a quote given with the evidence
must match the code within ±2 lines; a bullet without evidence must carry `[assumption]`, `[unverified]` or `[question]`.
