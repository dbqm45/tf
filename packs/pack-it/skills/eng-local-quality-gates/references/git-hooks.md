# Git hooks — ready configurations

Versions checked on 2026-10-10 in the registries: Husky 9.1.7, lint-staged 17.6.0, Lefthook 2.2.1 (npm), pre-commit 4.6.2,
pytest-testmon 2.2.0 (PyPI). The Lefthook and pre-commit configurations passed validation (`lefthook validate`,
`pre-commit validate-config`) and installation in an empty repository.

The mechanism is the same everywhere: checks on staged files, an exit code ≠ 0 rejects the commit or the push.

## Choosing the tool
| Project | Tool | Why |
|---|---|---|
| Node/TS, the repo already has `.husky/` | Husky + lint-staged | do not migrate a working configuration |
| Node/TS, new | Husky + lint-staged or Lefthook | Lefthook: one YAML file, parallelism, no `prepare` script |
| Python | the pre-commit framework | the ecosystem standard, isolated hook environments |
| several languages, a monorepo | Lefthook | one binary, `glob` and `root` per command |

## Husky + lint-staged (Node)
```bash
npm i -D husky lint-staged
npx husky init            # adds "prepare": "husky" to package.json and creates .husky/pre-commit
```
`.husky/pre-commit` (replace the default content `npm test`):
```sh
npx lint-staged
```
`.husky/pre-push`:
```sh
npx tsc --noEmit && npx vitest run
```
`package.json`:
```json
"lint-staged": {
  "*.{ts,tsx}": ["eslint --fix", "prettier --write"],
  "*.{json,md,css}": "prettier --write"
}
```
lint-staged itself appends the paths of the staged files at the end of the command and adds the fixed files back.
Useful flags (17.x): `--concurrent <n|false>`, `--fail-on-changes` (a failure when a task changed files — e.g. in CI).

## Lefthook (any language)
```yaml
# lefthook.yml
pre-commit:
  parallel: true
  commands:
    lint:
      glob: "*.{ts,tsx}"
      run: npx eslint --fix {staged_files}
      stage_fixed: true          # fixed files go back to the stage
    types:
      run: npx tsc --noEmit
pre-push:
  commands:
    tests:
      run: npx vitest run
```
Installation: `npx lefthook install`; checking: `npx lefthook check-install`, `npx lefthook validate`.
Other substitutions: `{all_files}`, `{push_files}`.

## pre-commit (Python)
`.pre-commit-config.yaml` with `repo: local`, `language: system` hooks (tools from the project's environment, without
pinning external hook repositories): `ruff check --fix` on commit, `pytest -q` with `stages: [pre-push]`
and `pass_filenames: false`. `default_install_hook_types: [pre-commit, pre-push]` makes `pre-commit install`
install both hooks. Related tests: `pytest --testmon` (pytest-testmon, data in `.testmondata`).

## Checking that the hook works
1. Introduce a deliberate error (an unused import, wrong typing) in a file, `git add`, `git commit` → the commit is rejected,
   the message points to the file.
2. Fix it, the commit passes; the formatter's fixes went into the commit (`git show --stat`).
3. A push with a red test → rejected.
Record the result in one sentence in the step report.

## Bypassing the gate
`git commit --no-verify`, `HUSKY=0`, `LEFTHOOK=0` turn the hooks off. The agent does not use them; a gate failed → fix
the cause and a new commit (core-git-workflow). Turning it off permanently is the human's decision recorded in the test strategy.
