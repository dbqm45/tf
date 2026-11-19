# dna — project knowledge for the factory

`dna` learns how a project is built — stack with exact versions, commands, tooling, and in later versions its
standards, code conventions and official documentation for the versions in use — and writes it as guidelines in
`out/`. The factory reads `out/` through the add-on contract (`addon.yaml`, contract 1). Everything the add-on needs
and produces lives in this directory; removing the directory detaches it.

Implementation plan: `docs/plans/2026-11-19-addons-dna-plan-wdrozenia.md` in the factory repository.

## Use

```bash
python3 dna.py learn --root <repository>     # build out/
python3 dna.py verify --root <repository>    # check out/ against the contract
python3 dna.py status --root <repository>    # what out/ holds
```

In a project the add-on sits in `.tf/addons/dna/`; `--root` defaults to the git top level of the current directory.

## What 0.1.0 knows

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

Only technologies in `registry/detectors/*.yaml` count as stack. A version without a lockfile is reported as a range
and listed in `coverage.md`.

## Output (contract 1)

| File | Content |
|---|---|
| `out/knowledge.json` | the canonical record; schema in `schema/knowledge.schema.json` |
| `out/INDEX.md` | ≤ 15 lines for the agent's permanent context |
| `out/coverage.md` | sources read and not read, notes (e.g. several versions of one library) |

Every item has evidence `path:line` (or an https URL with a fetch date) that `verify` checks against the
repository. The Markdown is generated from `knowledge.json` and must not be edited by hand.

## Rules for changes

- Nothing here imports from the factory (`core/`, `packs/`, `modes/`, `tools/`); the tests check it.
- Standard library and PyYAML only.
- Tests: `python3 tests/test_dna.py` (also the `addon-dna` job in CI).
- Version by SemVer in `addon.yaml`; changes in `CHANGELOG.md`.
