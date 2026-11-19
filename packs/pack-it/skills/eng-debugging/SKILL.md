---
name: eng-debugging
description: Use when something works wrongly or stopped working and the cause is not obvious — reproduction, hypotheses, git bisect.
metadata:
  review: "2027-10-09"
  catalog: "Use when a program works wrongly and the cause is not obvious — describing the symptom, reproduction (preferably with a red test), hypotheses with a deciding experiment, narrowing down (bisection in history with git bisect run, in input data, in code and configuration), the debugger and logs, typical classes of causes (nondeterminism, shared state, cache, environment, versions), the root cause and a fix without masking. Not for running a production incident (ops-sre-incidents), diagnosing a server and network (ops-linux-networking), reviewing reports from outside (proc-issue-triage) or quarantining flaky tests (qa-regression)."
  keywords: "debugowanie, błąd, bug, nie działa, dlaczego to nie działa, przyczyna błędu, wyjątek, stack trace, NullPointerException, regresja, git bisect, który commit zepsuł, debugger, breakpoint, pdb, odtworzyć błąd, działa lokalnie a nie w CI, poprawka nie pomogła, kolejna poprawka, znowu ten sam błąd, przeramowanie, zapis nie działa, API zwraca 200, połknięty błąd, debugging, error, does not work, why does this not work, cause of the error, exception, regression, which commit broke it, reproduce the bug, works locally but not in CI, the fix did not help, another fix, the same bug again, reframing, saving does not work, API returns 200, swallowed error"
---

# Debugging — from the symptom to the cause

The rule: **first the cause, then the fix.** A fix without understanding the cause usually moves the bug elsewhere
or masks it. You work as in an experiment: observation → hypothesis → prediction → test → conclusion.
You keep a short log (what was checked, the result), so as not to check the same thing twice and to be able to hand the work over.

## Procedure
1. **Describe the symptom precisely:**
   - what is expected, what is actual;
   - since when, where (environment, version, commit, data, user);
   - the full message and call stack, without summarizing.
   The discrepancy "works for me / does not work in CI" is already information: the difference between environments is the first suspect.
   A user report in one sentence, without a stack trace → first questions (steps, scope, frequency, area),
   then sources of evidence: monitoring, logs, the browser, code — `references/evidence-from-many-sources.md`.
2. **Reproduce the bug:**
   - the smallest, repeatable case, preferably **an automated test that is red** for the right reason;
     this is also the first TDD step of the fix (the `tdd_guard` hook);
   - a random bug: run it many times in a loop, fix the random seed, the clock, the test order and parallelism;
   - without a reproduction you do not announce a fix, only "could not reproduce" with a list of attempts.
3. **Pose hypotheses and decide them with an experiment:**
   - write down 2–4 possible causes;
   - for each, record what would have to be true and what experiment will confirm or refute it;
   - start with the one that is cheapest to check, not your favourite;
   - change one thing at a time.
4. **Narrow down by half:**
   - **in history**: `git bisect run <script>` finds the first bad commit in log₂(n) steps (200 commits → approx. 8);
     code 125 skips a commit that cannot be checked — `references/bisection-and-tools.md`;
   - **in data**: split the input into halves until the smallest case triggering the bug remains (delta debugging);
   - **in code**: logs or assertions at module boundaries — where the state is still good and where it is already bad;
   - **in the environment**: compare the working and the non-working one (versions from the lockfile, variables, flags, data, system).
5. **Observe instead of guessing:**
   - the debugger: a breakpoint, inspecting variables, stepping (`breakpoint()` in Python, `node --inspect-brk`,
     the IDE debugger);
   - a log with context (identifiers, input values), not "I am here";
   - go **backwards from the failure**: which value is wrong, where did it come from, where did it first become wrong (defect →
     infected state → failure).
6. **Check the assumptions** that "are surely true":
   - are you running the code you think (an old build, bytecode cache, a server not reloaded, another branch);
   - dependency versions and configuration;
   - time zones, character encoding, locale settings.
   Example: in a Python bisection a stale `__pycache__` gave a false result — see the reference.
7. **Find the root cause:**
   - ask "why" several times: why was the value wrong, why did the code allow it, why did the test not catch it;
   - you fix the cause and the gap in the tests, not only the symptom.
8. **Fix without masking:**
   - test red → minimal fix → test green → the whole test suite;
   - you do not mask: an empty `except`, retrying without a cause, `sleep` in a test, disabling a test or a linter rule;
   - you check similar places in the code with `grep` — the same bug is often in several copies.
9. **Record** in the step report: the symptom, the cause, the evidence (a test, the commit from the bisection) and the fix. A trap that may
   come back goes to `docs/project/lessons.md` (core-project-record).
10. **Know when to stop:**
    - after approx. 2 hours without progress or after all hypotheses are refuted, present the log and the hypotheses to a human
      or hand the problem to an agent in a fresh context;
    - a production bug affecting users: first restore the service (ops-sre-incidents), diagnosis later;
    - a second failed fix of the same symptom, a plan that does not converge on a decision, or a report with a ready
      fix ("X breaks, let's do Y") → reframing (`references/reframing.md`): the problem may be wrongly
      named, not poorly investigated.

## Typical classes of causes
| Class | Signal | First experiment |
|---|---|---|
| nondeterminism | the bug every n-th run | a loop N times; a fixed seed, clock, order; no parallelism |
| shared state | the test passes alone, fails in the suite | run in a different order; look for global variables, singletons, a shared database |
| edge values | the bug for part of the data | empty, `null`, zero, very large, non-ASCII characters, the turn of a day/month |
| time and zones | the bug at a specific hour or date | set the clock to that moment; check the server and database zone |
| cache and artifacts | "the fix does not work" | a clean build, clear the cache, check which file is executed |
| environment | works locally, not in CI/production | compare versions, variables, permissions, data |
| dependency | after an update | bisection over the lockfile, release notes (ops-dependency-upgrades) |
| concurrency | rare, under load | a test with many threads; logs with a thread/request identifier; locks and transactions |
| swallowed error | the API returns 200/`ok`, but the effect (a write, a send) did not happen; a warn in the logs | look for error handling that logs and returns success; the test checks the stored state, not the response |

## Boundaries
- A production incident (command, communication, rollback): ops-sre-incidents. Server and network symptoms (DNS, TLS,
  ports, processes): ops-linux-networking. Performance: qa-performance-testing.
- A report from outside (category, reproduction, a brief for the implementer): proc-issue-triage. Flaky tests in CI
  (quarantine, metrics): qa-regression.

## Checklist
- [ ] symptom described with the full message, version and environment
- [ ] bug reproduced with a test that was red for the right reason
- [ ] hypotheses with experiments in the log; one change at a time
- [ ] root cause named and proven (a test, a commit, a measurement)
- [ ] fix without masking; the whole test suite green; similar places checked
- [ ] fix verified on every channel that showed the problem (test, monitoring, logs, browser)

## Sources
- A. Zeller, *Why Programs Fail* and debuggingbook.org (the scientific method, the defect → infection → failure chain, delta debugging)
- D. J. Agans, *Debugging: The 9 Indispensable Rules*
- git-scm.com/docs/git-bisect (`git bisect run`, code 125); behaviour checked on git 2.43 (2026-10-03)
- The 10xDevs course, ed. 3 (2026), module 2, lesson 4 (reframing) and module 3, lesson 5 (debugging from many sources) —
  training material (accessed 2026-10-09)
Described in our own words.
