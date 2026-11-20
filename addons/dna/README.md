# dna — project knowledge for the factory

`dna` learns how a project is built — stack with exact versions, commands, tooling, and in later versions its
standards, code conventions and official documentation for the versions in use — and writes it as guidelines in
`out/`. The factory reads `out/` through the add-on contract (`addon.yaml`, contract 1). Everything the add-on needs
and produces lives in this directory; removing the directory detaches it.

Implementation plan: `docs/plans/2026-11-19-addons-dna-plan-wdrozenia.md` in the factory repository.

## Use

```bash
python3 dna.py learn --root <repository>     # build out/
python3 dna.py refresh --root <repository>   # learn again only when the inputs changed
python3 dna.py verify --root <repository>    # check out/ against the contract
python3 dna.py status --root <repository>    # what out/ holds
python3 dna.py docs query react "useTransition"   # official docs of the project's version (local index)
python3 dna.py check --base main             # the change against the guidelines; exit 1 = blocking
```

`learn` reaches the network only for documentation (`--offline` or `DNA_OFFLINE=1` to stop it): package registries
(npm, PyPI) and the hosts listed in `registry/docs-sources.yaml`, https only, GET of files by package name and
version; the question asked in `docs query` never leaves the machine.

In a project the add-on sits in `.tf/addons/dna/`; the factory runs `refresh` in the background at the start of
every session (hook `addons_refresh.py`); `--root` defaults to the git top level of the current directory.

## What 0.9.0 knows

| Area | Source | Version from |
|---|---|---|
| JavaScript / TypeScript | `package.json` (workspaces too) | `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock` |
| Python | `pyproject.toml`, `requirements*.txt` | `uv.lock`, `poetry.lock`, `==` pins |
| Go | `go.mod` (direct requirements) | `go.mod` |
| Rust | `Cargo.toml` | `Cargo.lock` |
| JVM | `pom.xml` (parent, properties), `libs.versions.toml`, Spring Boot Gradle plugin | the build files |
| .NET | `*.csproj`, `*.fsproj` | `packages.lock.json` or `Version` |
| Commands | `package.json` scripts, `pyproject.toml`, build tools, `Makefile` | — |
| Tooling | prettier, eslint, biome, stylelint, ruff, editorconfig, golangci-lint, checkstyle | — |
| Exemplar files | git history, paths and content (`lib/exemplars.py`) | — |
| UI building blocks | imports, exports and styles in the code (`lib/code.py`) | — |
| Documentation | installed npm package; npm tarball and PyPI description of the exact version; `registry/docs-sources.yaml` | the stack facts above |

Many npm packages ship only a short README that points to a website; for those, add the official, version-specific
source to `registry/docs-sources.yaml` (rules in the file's header).

Only technologies in `registry/detectors/*.yaml` count as stack. A version without a lockfile is reported as a range
and listed in `coverage.md`.

## Agreed rules

dna describes the code; the project's agreed rules come from a decisions add-on (`addons/standards`). dna declares
`consumes: [decisions]`, so the factory passes it those decisions: rules that forbid an import are enforced by
`check` and keep such files out of the exemplars. Without that add-on dna works the same, without them.

## Output (contract 1)

| File | Content |
|---|---|
| `out/knowledge.json` | the canonical record; schema in `schema/knowledge.schema.json` |
| `out/INDEX.md` | ≤ 15 lines for the agent's permanent context |
| `out/exemplars.md` | per kind of change: the file to follow, its test, imports and users |
| `out/rules/ui.md` | rule with `paths` for UI files: components to use, import form, styling, tokens, theme |
| `out/catalog/ui.md` | full UI catalog with evidence |
| `out/docs-index.md` | ≤ 8 KB: technology@version → topics, for the permanent context |
| `out/coverage.md` | sources read and not read, notes (e.g. several versions of one library) |

Every item has evidence `path:line` (or an https URL with a fetch date) that `verify` checks against the
repository. The Markdown is generated from `knowledge.json` and must not be edited by hand.

## Rules for changes

- Nothing here imports from the factory (`core/`, `packs/`, `modes/`, `tools/`); the tests check it.
- Standard library and PyYAML only.
- Tests: `python3 tests/test_dna.py`, `tests/test_docs.py`, `tests/test_code.py`, `tests/test_check.py`, `tests/test_exemplars.py` (also the `addon-dna` job in CI).
- Version by SemVer in `addon.yaml`; changes in `CHANGELOG.md`.
