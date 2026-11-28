# The verify scope: the gate's `related` command

You read this when `run_report.py start` prints `⚠ The quality gate has no related`, or `verify` prints `ℹ … the
narrowest command`. Without `related` every `verify`
and every gate check runs the whole configured command — in a monorepo that is minutes per slice. Nobody writes `related`
by hand: you work it out once per project and record it; the human sees it in the plan question and may override it there.

## Work it out
1. Read this project's own build files (whatever it has: the package manifest, the workspace or build tool configuration,
   a Makefile, the CI configuration) and find how it runs the tests of given files or of their directories. The factory
   keeps no table of tools — the command comes from this repository.
2. Write it with a placeholder the gate fills: `{files}` (one argument per changed file), `{files,}` (one argument, the
   files joined with commas) or `{dirs}` (the directories of the changed source files).
3. **Check it once:** run it with the placeholder replaced by one existing source file, through the test lock —
   `python3 .claude/hooks/test_lock.py -- <command>` is allowed in an unattended run, a bare runner may be refused. Valid when it exits 0, or 1 with
   real test results (not "unknown command", "no such option" or a usage text), and it runs fewer tests than the full
   command — or at least runs that file's tests.

## Record it
- Valid: `run_state.py gate-related <katalog> --command "<command with the placeholder>" --rationale "<the build file
  it comes from; the check: the file, the exit code, how many tests ran>"` — written as `related` into
  `.claude/quality-gate.json` (the other keys stay) with who, when and why; prints one `✓` line.
- Invalid or unsure: `run_state.py gate-related <katalog> --not-found --rationale "<what you tried and why it fails>"` —
  the full command stays, the next run does not search again, `tf doctor` shows a `⚠`.

`stage plan` prints `verify will use: …` — one line of the plan question. The human's override in the answer → record
it the same way, with `--rationale "the human: …"`.

## The narrowest verify
- A slice's verify runs **the tests related to the slice's changed files**, through the runner's own "related to these
  files" mode (jest's `--findRelatedTests <files>` is one example) or the slice's own test files — not a whole
  directory, a project or a workspace target. In one measured run a directory took 132 s, while the specs of the two
  changed components would have taken seconds.
- `verify` prints one `ℹ` line when the command names none of the slice's files and has no placeholder. It is a hint:
  you decide; a wider run needs a reason (a shared module many tests import, a config change).
- **Do not interrupt a running verify.** A cut run (exit 130) leaves no evidence and is repeated in full; when it is too
  slow, narrow the next command instead.
- `--full` once before the PR, only when the approach says so.
