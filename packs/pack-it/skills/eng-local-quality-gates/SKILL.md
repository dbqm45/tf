---
name: eng-local-quality-gates
description: Use when lint, types or tests should run on the developer machine — a post-edit agent hook, pre-commit, pre-push — so errors surface in seconds, not in CI.
metadata:
  review: "2027-10-09"
  catalog: "Use when format, lint, type and test checks should run locally in layers — an agent hook after each file edit (Claude Code PostToolUse with a ready template driven by a JSON config), pre-commit on staged files, pre-push with wider tests, CI keeping the full suite — and when you decide how the agent reacts to a failing hook (fix trivial errors at once, stop after 1–2 attempts on logic, never bypass). Tools: Husky, lint-staged, Lefthook, the pre-commit framework, vitest related, jest --findRelatedTests, pytest-testmon. Not for CI pipelines (ops-ci-cd), branches, commits and PRs (core-git-workflow), agent permissions (core-agent-security) or choosing regression suites (qa-regression)"
  keywords: "hook po edycji, hook po każdej edycji pliku, po edycji przez agenta uruchom eslint, automatycznie testy po zmianie pliku, błąd wraca do agenta, PostToolUse, hook Claude Code, settings.json hooks, pre-commit, pre-push, przed commitem, przed pushem, hooki gita, husky, lint-staged, lefthook, pre-commit-config, pre-commit install, ruff przed commitem, testy przed pushem, vitest related, findRelatedTests, testy powiązane, pytest-testmon, testmon, CI za wolne, czekamy 20 minut na CI, lint tylko w CI, commit trwa minuty, warstwy sprawdzeń, bramki jakości lokalnie, agent w pętli, agent w kółko poprawia kod, hook nie przechodzi, hook trwa za długo, timeout hooka, --no-verify, pominąć hook, obejść hook, plik ze spacją w nazwie, jak sprawdzić że hook działa, post-edit hook, after every edit run eslint, run related tests automatically, error back to the agent, git hooks, pre-commit hook, pre-push hook, staged files, lint staged files, CI too slow, local quality gates, agent loops on failing hook, hook timeout, skip the hook, verify the hook works"
---

# Local quality gates — errors in seconds, not after CI

Checks that run by themselves on the developer machine do not depend on what the model remembers (they survive context
compaction) or on a person's discipline. Each layer has a time budget; a check that does not fit moves one layer up.
**Local layers never replace CI** — CI still runs the full suite.

## Layers
| Layer | What runs | Budget (rule of thumb) | Why there |
|---|---|---|---|
| post-edit (agent hook) | format/lint of the one edited file; related tests **only for risk areas** | seconds | the only layer that tells the agent mid-work |
| pre-commit | lint/format of staged files, type check, maybe related tests | ~10–20 s | also catches manual edits |
| pre-push | full type check, the unit suite or a wider test set | minutes | last stop before others see it |
| CI | integration, full E2E, security scans, build, the complete suite | as needed | the source of truth for merge |

Start with one post-edit hook and one commit gate; add more from observed leaks (what reached CI that a local layer
could have caught). Gates come from the project test strategy (qa-test-design, "Quality gates" in
`docs/project/05-plan/test-strategy.md`), each with its layer and the phase from which it applies.

## Procedure
1. **Inventory, read-only:** commands in `package.json` / `pyproject.toml` / `Makefile`; existing `.husky/`,
   `lefthook.yml`, `.pre-commit-config.yaml`; hooks already in `.claude/settings.json`; the test strategy.
   A working tool stays — do not migrate Husky to Lefthook because you prefer it.
2. **Place each check** in the cheapest layer whose budget it fits.
3. **Post-edit hook** from the template (below), with risk globs (e.g. `src/billing/**`), not the whole `src/`.
4. **Git hooks** with the tool that fits the repo: `references/git-hooks.md`.
5. **Test the gates** with deliberate errors: an edit with an unused import → the hook fires → the error reaches the
   agent; a broken staged file → the commit is rejected; a red test → the push is rejected.
6. **Record** the gate → layer → phase table and the commands in CLAUDE.md.

Changing `.claude/settings.json` or hook files happens **only on a human's request**; otherwise you hand over the
fragment to paste. Settings files: `.claude/settings.json` (project, committed), `.claude/settings.local.json`
(personal, not committed), `~/.claude/settings.json` (user).

## Post-edit hook (Claude Code)
Model: event → filter (tool matcher, path pattern) → action (command) → signal (exit code and output back to the
agent). A hook whose output never reaches the agent teaches it nothing.

Exit codes of a Claude Code command hook: **0** — OK (stdout JSON may carry `hookSpecificOutput.additionalContext` or
`systemMessage`); **2** — blocking error, stderr is shown to the model, which then fixes it; any other code — a
non-blocking error the model does not see.

Setup from the template:
1. Copy `.claude/skills/eng-local-quality-gates/templates/post_edit_checks.py` to `.claude/hooks/post_edit_checks.py`.
2. Write `.claude/quality-gates.json` from `templates/quality-gates.example.json`: `max_lines` and `checks[]`, each
   with `name`, `glob`, `cmd`, `timeout` and optional `env`.
3. Register it in `.claude/settings.json`:
```json
{ "hooks": { "PostToolUse": [ { "matcher": "Edit|Write", "hooks": [
  { "type": "command", "command": "python3",
    "args": ["${CLAUDE_PROJECT_DIR}/.claude/hooks/post_edit_checks.py"], "timeout": 60 } ] } ] } }
```
4. Check the config without running anything: `python3 .claude/hooks/post_edit_checks.py --dry-run src/billing/invoice.ts --json`.

What the script does (do not re-implement it):
- reads `tool_input.file_path` from the hook's stdin JSON; acts on Write, Edit and MultiEdit; each edit is a separate
  run (3 edited files = 3 runs);
- no config or no matching glob → does nothing;
- a failed check → exit 2 and the last `max_lines` lines of its output on stderr;
- commands run **without a shell**; `{file}` becomes the edited file's relative path as **one argument**, so a file
  name with spaces is safe;
- an exceeded `timeout`, a missing program or a bad config → exit 0 with a message: the hook never blocks through its
  own fault;
- the whole run stops after `CLAUDE_QG_DEADLINE` seconds (default 50) — keep the hook `timeout` in settings higher
  (e.g. 60); `CLAUDE_QUALITY_GATES=off` disables it;
- `--dry-run <file> [--json]` lists the checks covering a file and runs none; exit codes 0 OK, 2 failed check,
  1 bad config in dry-run;
- Python 3.9+ standard library, no network, UTF-8 forced on its streams.

Related tests (checked 2026-10-10): Vitest 5 `vitest related <file> --run` (a subcommand; no related tests → exit 0;
with an agent environment variable such as `AI_AGENT` it picks a compact reporter and no watch); Jest 30
`jest --findRelatedTests <file>` (a flag); pytest has no built-in equivalent — the `pytest-testmon` plugin
(`pytest --testmon`, data in `.testmondata`). Run them only for risk globs, not helpers or config, and keep the output
to the tail.

## Agent and a failing hook
- **Trivial** failures (format, import, type, unused variable) → fix at once.
- **A logic test** still failing after **1–2 attempts** → stop changing code; find the cause (eng-debugging) or ask the
  human. Never fit the code to green blindly and never weaken the test (tdd_guard, qa-spec-first-testing).
- Never bypass git gates: no `--no-verify`, `HUSKY=0`, `LEFTHOOK=0`. When someone wants to skip a hook to ship, fix
  the cause; a permanent disable is a human decision recorded in the test strategy.
- A hook that regularly times out (a check taking 90 s) is in the wrong layer: narrow it to the file or move it up a
  layer instead of raising the timeout again and again.

## Other agent tools
Cursor, Codex, Windsurf and Copilot have hooks or rules built on the same event → filter → command model, but with
other files, event names and input fields, and some can only block, not return a message. Check the tool's current
docs, mark per-tool details as [unverified] until tested, and run the deliberate-error test from step 5.

## Example
A FastAPI service, ruff + mypy + pytest, payments in `app/payments/` as risk area #1, CI takes 25 minutes.

| Gate | Layer | From phase |
|---|---|---|
| `ruff check --fix {file}` on `**/*.py` | post-edit | now |
| `pytest --testmon` on `app/payments/**/*.py` (timeout 30) | post-edit | after the payment tests are stable |
| ruff + `mypy app` on staged files (pre-commit framework) | pre-commit | now |
| `pytest -q` unit suite (`stages: [pre-push]`) | pre-push | now |
| integration, E2E, `pip-audit`, image build | CI | unchanged |

Test run: an unused import added by the agent → hook exit 2 with ruff's line → the agent removes it in the next edit;
the same mistake by hand → the pre-commit hook rejects the commit and shows the file; a deliberately failing unit test
→ the push is rejected. Recorded in CLAUDE.md with the commands.

## Checklist
- [ ] every gate has a layer and a phase; post-edit checks take seconds
- [ ] a failure reaches the agent (exit 2, stderr); the hook's own errors do not block
- [ ] settings changed only with the human's consent; otherwise a fragment handed over
- [ ] gates tested with deliberate errors (edit, commit, push)
- [ ] no bypass flags; CI still runs the full suite

## Sources
- Claude Code docs, "Hooks" — events, matchers, exit code semantics, JSON output (code.claude.com/docs/en/hooks,
  accessed 2026-10-10).
- Vitest CLI `related` (vitest.dev/guide/cli), Jest CLI `--findRelatedTests` (jestjs.io/docs/cli), pytest-testmon
  (testmon.org) — accessed and run 2026-10-10.
- Husky (typicode.github.io/husky), lint-staged (github.com/lint-staged/lint-staged), Lefthook (lefthook.dev),
  pre-commit (pre-commit.com) — accessed 2026-10-10.
