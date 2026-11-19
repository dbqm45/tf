---
name: eng-local-quality-gates
description: Use for local quality gates — a post-edit hook, pre-commit, pre-push, related tests.
metadata:
  review: "2027-10-09"
  catalog: "Use when setting up local quality gates in a project — placing lint, formatting, types and tests between the agent's post-edit hook, pre-commit, pre-push and CI; tests related to the edited file; exit codes and feedback for the agent; the agent's behaviour with a failing hook; Husky, lint-staged, Lefthook, pre-commit; the post_edit_checks.py hook template with the quality-gates.json configuration. Not for CI pipelines (ops-ci-cd), branches, commits and PRs (core-git-workflow), agent permissions (core-agent-security) or choosing regression suites (qa-regression)."
  keywords: "hook po edycji, hook PostToolUse, pre-commit, pre-push, husky, lint-staged, lefthook, formatowanie po edycji, lint przy zapisie, testy powiązane z plikiem, vitest related, findRelatedTests, bramka przed commitem, git hooks, hooki gita, agent dostaje błąd lintera, szybka informacja zwrotna, post-edit hook, PostToolUse hook, formatting after edit, lint on save, tests related to a file, gate before commit, agent gets a linter error, fast feedback"
---

# Local quality gates

Goal: a format, lint or type error or a broken test in a risk area surfaces on the machine, within seconds of the edit, not
after 20 minutes in CI. The agent's hook is a deterministic layer: it works regardless of what the model remembers from the instructions,
also after context compaction. CI still runs the full suite — the local layers do not replace it.

## Which check goes where
| Layer | What | Time budget | Notes |
|---|---|---|---|
| post-edit (agent hook) | format and lint of one file; tests related to a file from a risk area | seconds | the only layer that tells the agent about an error while it works |
| pre-commit (git) | lint and format of staged files; types; possibly tests related to staged files | a dozen or so s | also catches manual edits and edits from outside the agent |
| pre-push (git) | full types, a wider set of tests | minutes | |
| CI | integration, full E2E, scans, build | minutes and more | ops-ci-cd |

- A check longer than a few seconds → one layer up, or narrow it to the file.
- The post-edit hook runs separately for every edit (3 files = 3 runs), without aggregation.
- Start with one hook (format/lint) and one commit gate; add more when you see what slips through.
- The gates follow from the project's test strategy (qa-test-design, the "Quality gates" section) — each has a layer and a phase
  from which it applies.

## Procedure
1. **Inventory (read only).** The lint, format, type and test commands (`package.json`, `pyproject.toml`), existing
   hooks (`.husky/`, `lefthook.yml`, `.pre-commit-config.yaml`, the `hooks` section in `.claude/settings.json`), the test
   strategy (`docs/project/05-plan/test-strategy.md`). You do not migrate a working configuration to another tool.
2. **Place the checks** per the table above; for related tests list the globs of risk areas (e.g. `src/billing/**`),
   not the whole `src/`.
3. **The agent's post-edit hook** — the template below. Change `.claude/settings.json` and `.claude/hooks/` only at the human's
   request (CLAUDE.md); without consent you hand over a ready fragment to paste.
4. **Git hooks** — `references/git-hooks.md` (Husky + lint-staged, Lefthook, pre-commit; versions checked).
5. **Test the gates:** edit a file → the hook runs → the error returns to the agent; a broken staged file → the commit is rejected;
   a red test → the push is rejected. Without this a gate is a wish.
6. **Record:** a "gate → layer → from when" table in the test strategy; the commands in the "Commands" section of the project's `CLAUDE.md`.

## The agent hook model
event (after a tool use) → filter (the `Edit|Write` tool, a path pattern) → action (a command) → signal
(the exit code and the output that returns to the agent). The file path is in the JSON on stdin: `tool_input.file_path`.

| Hook exit code (Claude Code) | Effect |
|---|---|
| 0 | OK; JSON on stdout can add `hookSpecificOutput.additionalContext` (context for the model) or `systemMessage` (for the human) |
| 2 | a blocking error — the stderr content goes to the model as the hook's message |
| other | a non-blocking error — visible in verbose mode, the model does not get it |

A hook whose result does not return to the agent will not teach it the fix. Configuration: `.claude/settings.json` (the project, in the repo),
`.claude/settings.local.json` (local, outside the repo), `~/.claude/settings.json` (the user).

### Template: `templates/post_edit_checks.py` + `.claude/quality-gates.json`
A ready hook (the Python standard library, test: `tests/test_post_edit_checks.py`). You describe the gates in JSON,
without writing a hook from scratch; example: `templates/quality-gates.example.json`.
- no configuration or no matching `glob` → nothing; a command failure → code 2 and the last `max_lines` lines on stderr;
- the command runs without a shell, `{file}` = the relative path of the edited file (one argument, also with spaces);
- an exceeded `timeout`, a missing program, a bad configuration → code 0 and the message "narrow it or move it to pre-commit";
- the whole hook's own limit `CLAUDE_QG_DEADLINE` (50 s by default, it ends with code 0 before the Claude Code limit);
  UTF-8 forced on stdin/stdout/stderr (Windows); `CLAUDE_QUALITY_GATES=off` turns the hook off;
- `python3 .claude/hooks/post_edit_checks.py --dry-run src/billing/invoice.ts [--json]` shows which checks
  will cover the file — it runs nothing.

Installation in a project (with the human's consent): copy the template to `.claude/hooks/`, the configuration to
`.claude/quality-gates.json`, and in `.claude/settings.json`:
```json
"PostToolUse": [
  { "matcher": "Edit|Write",
    "hooks": [ { "type": "command", "command": "python3",
                 "args": ["${CLAUDE_PROJECT_DIR}/.claude/hooks/post_edit_checks.py"], "timeout": 60 } ] }
]
```

## Tests related to a file
| Runner | Command | Notes (checked 2026-10-10) |
|---|---|---|
| Vitest 5 | `vitest related <file> --run` | `related` is a subcommand; `--run` turns off watch mode; no related tests → code 0 |
| Jest 30 | `jest --findRelatedTests <file>` | a flag, not a subcommand |
| pytest | `pytest --testmon` (the pytest-testmon plugin) or a file → test directory map | no native equivalent |

- Vitest 5 in an agent environment (it detects, among others, `AI_AGENT`, which Claude Code sets) chooses the reporter
  `minimal` (alias `agent`) by default and turns off watch — less noise in the context.
- Related tests only for risk globs, not for helpers and configuration.
- Limit the output to the tail (template: `max_lines`).

## The agent and a failing hook
- **Trivial** (format, import, type, an unused variable) — the agent fixes it itself in the next step.
- **A logic test** fails after 1–2 fix attempts → stop: the cause per eng-debugging or a question to the human. You do not
  blindly fit the code to green and you do not weaken the test (tdd_guard, qa-spec-first-testing).
- You do not bypass a git gate (`--no-verify`, `HUSKY=0`, `LEFTHOOK=0`); it failed → fix the cause, a new commit.
- A hook that regularly exceeds the limit you move up — you do not extend the `timeout` endlessly.

## Other agent tools
Cursor, Codex, Windsurf and Copilot have the same model (event → filter → command), but different files, event names
and input fields; some tools only block and do not pass the result to the agent. Check a hook ported 1:1 against the current
documentation of the given tool (core-source-research) and with the test from step 5. [unverified: per-tool details]

## Example
**Situation:** a TS project (Vitest 5, ESLint), risk #1 from the test strategy — billing in `src/billing/`. CI takes
18 minutes, and every second PR the agent hands over code with a lint error.
**Result:**

| Gate | Layer | From when |
|---|---|---|
| `npx eslint --fix {file}` for `src/**/*.{ts,tsx}` | post-edit (`post_edit_checks.py`) | right away |
| `npx vitest related {file} --run` for `src/billing/**/*.ts` | post-edit | after phase 1 of the strategy (billing tests exist) |
| lint-staged (`eslint --fix`, `prettier --write`) + `npx tsc --noEmit` | pre-commit (Husky) | right away |
| `npx vitest run` | pre-push | right away |
| full E2E, build, scans | CI | unchanged |

Testing the gates: an unused import in `src/billing/invoice.ts` → the hook returned code 2 with the ESLint error, the agent fixed it in the next
step; the same error introduced by hand → the commit rejected by lint-staged.

## Checklist
- [ ] every gate from the test strategy has a layer and a phase from which it applies
- [ ] the post-edit hook takes seconds; related tests only for risk globs
- [ ] a failure returns to the agent (code 2 / stderr), an error of the hook itself does not block work
- [ ] a change of `settings.json`/`.claude/hooks/` only with the human's consent
- [ ] the gates tested (edit, commit, push); the result in the report
- [ ] CI still runs the full suite

## Sources
- The 10xDevs course, ed. 3 (2026), module 3, the lesson on hooks and local quality layers — training material (accessed 2026-10-09).
- Claude Code — the hooks documentation (code.claude.com/docs/en/hooks): the PostToolUse event, exit codes, `additionalContext`;
  the handling of code 2 and the stderr message confirmed in the Claude Code 2.1 code (2026-10-10).
- Vitest 5.0.3 `--help` and the source code (`related`, the `agent`/`minimal` reporter, agent detection through std-env), Jest 30.5.2
  `--help`, pytest-testmon 2.2.0 `--help` — checked locally 2026-10-10.
- Husky 9.1.7, lint-staged 17.6.0, Lefthook 2.2.1, pre-commit 4.6.2 — the npm/PyPI registries and configuration validation 2026-10-10.
