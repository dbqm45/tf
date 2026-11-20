---
name: eng-debugging
description: Use when something works wrongly or stopped working and the cause is unclear — reproduce, hypotheses, git bisect, swallowed errors, a fix that did not help.
metadata:
  review: "2027-10-09"
  catalog: "Use when code behaves wrongly, a regression appeared, it works locally but not in CI, an API returns 200 but nothing is stored, or a fix did not help — describing the symptom, a reproducing red test, 2–4 hypotheses with deciding experiments, narrowing down (git bisect run, halving data, instrumentation, environment diff), checking assumptions, root cause, a fix without masking, a record in lessons.md, multi-source evidence and re-framing a misnamed problem. Not for running a production incident (ops-sre-incidents), diagnosing a server and network (ops-linux-networking), reviewing reports from outside (proc-issue-triage) or quarantining flaky tests (qa-regression)."
  keywords: "debugowanie, debugować, znaleźć przyczynę błędu, nie wiem czemu nie działa, przestało działać, regresja, który commit zepsuł, git bisect, bisekcja, u mnie działa, działa lokalnie a w CI nie, poprawka nie pomogła, kolejna poprawka nie pomogła, ten sam błąd wraca, przeramowanie, źle postawiony problem, zapis nie działa, API zwraca 200, nic się nie zapisuje, połknięty błąd, połknięty wyjątek, pusty catch, błąd tylko dla części użytkowników, losowy błąd, test przechodzi sam a w zestawie pada, NullPointerException, stack trace, debugger, pdb, breakpoint, odtworzyć błąd, nie da się odtworzyć, debugging, find the root cause, stopped working, which commit broke it, regression, works on my machine, works locally fails in CI, fix did not help, returns 200 but nothing saved, swallowed error, swallowed exception, cannot reproduce, flaky only in suite, root cause analysis, reframe the problem"
---

# Debugging — from symptom to cause, then a fix that does not mask

Cause before fix. Work as a loop of experiments: observe → hypothesise → predict → test → conclude. Keep a short log of what you
checked and what it showed — it stops you repeating experiments and lets someone else take over.

## Procedure
1. **Describe the symptom.** Expected vs actual; since when; where (environment, version, commit, data, user); the full error message
   and stack trace, not a summary. A difference of environment ("works for me") is the first suspect.
   A one-sentence report without a stack ("it doesn't work") → ask first: the steps, who is affected, how often, which area. Do not guess
   a cause.
2. **Reproduce.** The smallest repeatable case, ideally an automated test that is **red for the right reason** — it is the first TDD step
   of the fix (`tdd_guard` lets production code change only after it). Intermittent bug: run it N times in a loop; pin the seed, the clock,
   test order and parallelism. No reproduction → report "could not reproduce" with the list of attempts; never claim a fix.
3. **Hypotheses.** 2–4 candidates. For each: what must be true if it holds, and which experiment decides. Run the cheapest decisive
   experiment first, not your favourite. Change one thing at a time.
4. **Narrow down** along the axis that fits (examples: `references/bisection-and-tools.md`):
   - **history** — `git bisect run <script>`: exit 0 = good, 1–127 except 125 = bad, 125 = cannot test (skip), above 127 aborts.
     About log2(n) steps (200 commits ≈ 8). Keep the script outside the repo or untracked; clean build and caches between steps; merge-heavy
     history → `git bisect start --first-parent`; monorepo → limit by path `git bisect start <bad> <good> -- <path>`; first check that
     the "bad" end is really red and the "good" end green; save `git bisect log`; finish with `git bisect reset`. A skipped commit next to the
     first bad one gives an honest two-candidate answer — decide by reading both diffs. The bisect test becomes the regression test;
   - **data** — halve the input until the smallest case that still fails (delta debugging); it becomes a regression test without personal data;
   - **code** — logs and assertions at module boundaries, context-rich (ids, input values);
   - **environment** — diff versions from the lockfile, variables, flags, data, operating system.
5. **Observe.** A debugger (`breakpoint()`, `python -m pdb`, `pytest --pdb`; `node --inspect-brk` + `chrome://inspect`, `debugger;`).
   Walk backwards from the failure: the failure ← the infected state ← the defect.
6. **Check your assumptions.** Are you running the code you think (an old build, stale bytecode or cache, a server not reloaded, the
   wrong branch)? Dependency versions and configuration? Time zones, encoding, locale?
7. **Root cause.** Ask "why" until you reach the defect and the gap: why the value was wrong, why it was allowed, why the tests missed it.
   Fix the cause and the test gap.
8. **Fix without masking.** Red → minimal fix → green → the whole suite. Forbidden masks: an empty `except`/`catch`, a blind retry,
   `sleep` in tests, disabling a test or a lint rule. Search for copies of the same pattern elsewhere (`rg`).
9. **Record.** In the step report: symptom, cause, evidence, fix. A trap that may recur → `docs/project/lessons.md`.

## Cause classes — first experiment
| Class | Signal | First experiment |
|---|---|---|
| nondeterminism | fails sometimes | loop N runs, pin seed and clock |
| shared state | passes alone, fails in the suite | shuffle test order, look for globals, singletons, leftover DB rows |
| edge values | only for some inputs | halve the input, test the boundaries |
| time and zones | around midnight, month end, DST | inject a fixed clock, run in another `TZ` |
| cache and artifacts | the change "has no effect" | clean build, `PYTHONDONTWRITEBYTECODE=1`, clear caches |
| environment | works locally, not in CI | diff versions, variables, flags, OS |
| dependency | after an update | bisect the lockfile change |
| concurrency | under load, duplicates | a many-thread test, logs with request id |
| swallowed error | 200 / `ok: true`, no effect | a test that checks the stored state, not the response (`references/evidence-from-many-sources.md`) |

## When to stop and change approach
- No progress after a long session or all hypotheses refuted → hand the log to the human or to a fresh-context agent.
  (A time limit such as about two hours is a team heuristic [assumption], not a rule.)
- Production impact → restore service first (ops-sre-incidents), investigate after.
- A second failed fix of the same symptom, a plan that does not converge, or a report that bundles symptom, cause and fix
  ("duplicates — add a lock") → re-frame the problem: `references/reframing.md`.
- The `tdd_guard` hook shows the same failing test after 1–2 fix attempts → stop editing and run this procedure from step 1.

## Example
Input: "The invoice report computed totals correctly two weeks ago, now they are wrong; ~200 commits since."
Result:
- Symptom: `report_totals()` returns 1,204.10 instead of 1,204.13 for fixture `march.csv`; reproduced with a red test
  `test_march_totals` (checked on HEAD: red; on the tag from two weeks ago: green).
- Script `/tmp/check.sh` (outside the repo): `git clean -fdx -e .venv`; build; exit 125 if the build fails; run the one test.
- `git bisect start --first-parent HEAD v2.14.0` → `git bisect run /tmp/check.sh` → 8 steps → first bad `e41b9d0` "use float sum in
  aggregation". `git bisect log` saved in the step report.
- Root cause: float summation replaced `Decimal`; the tests used whole numbers only. Fix: back to `Decimal`, plus a property test
  "the total equals the sum of the rounded lines". `rg "sum(float"` found one more copy — fixed in the same commit.

## Checklist
- [ ] symptom complete (expected/actual, since when, where, full stack)
- [ ] red test reproduces it for the right reason (or "could not reproduce" with attempts)
- [ ] hypotheses with experiments logged; one change at a time
- [ ] root cause proven, not presumed; test gap closed
- [ ] no masking; whole suite green; similar places checked
- [ ] verified on every channel that showed the problem; lessons.md if the trap can recur

## Sources
- git documentation, `git-bisect` (git-scm.com/docs/git-bisect, accessed 2026-10-03); behaviour checked on git 2.43 and CPython 3.11
  (own run, 2026-10-03).
- Python documentation, `pdb` and `breakpoint()` (docs.python.org/3/library/pdb.html, accessed 2026-10-03); Node.js "Debugging guide"
  (nodejs.org, accessed 2026-10-03); Playwright documentation (playwright.dev, accessed 2026-10-03).
- A. Zeller, *Why Programs Fail*, 2nd ed., Morgan Kaufmann, 2009, and debuggingbook.org — the infection chain, delta debugging.
- D. J. Agans, *Debugging: The 9 Indispensable Rules for Finding Even the Most Elusive Software and Hardware Problems*, AMACOM, 2002.
