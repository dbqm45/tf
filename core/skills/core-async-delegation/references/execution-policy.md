# The policy for executing a plan unsupervised — formats

## A `/goal` command to copy
The goal condition is the session's stop test; the policy from `SKILL.md` §4 is the way to meet it. The evaluator
sees only the conversation, so the condition refers to what the agent prints.
```text
/goal Execute all phases of the plan docs/project/<step>/plan.md per the core-async-delegation §4 policy.
Done when: every automatic item in the plan's progress section is ticked, every phase has its own commit
(Conventional Commits) with the SHA printed in the conversation, and at the end there is a list of items for manual verification.
Constraints: do not change or weaken existing tests unless the plan says so; do not touch files
outside the plan's scope. Stop after <N> turns if you do not finish.
```
Running without a window (a tool list without network and without `git push`, if the task does not need them):
```bash
claude -p "<polecenie>" --allowedTools "<lista>" --permission-mode acceptEdits --max-budget-usd <kwota>
```

## Verdict lines (after each gate)
```text
GATE tests-from-plan: PASS
GATE deliberate-breakage: PASS (test red on the broken code, file restored)
GATE lint: FAIL (2 errors in src/limits.ts, attempt 1/2)
GATE lint: PASS
DIRTY (not added): .env.local, notes.md
ADAPT: the plan points to src/limits.ts, the file is in src/limits/index.ts
COMMIT phase 2: a1b2c3d
```

## Deliberate breakage (only phases that add or change tests)
1. The phase's files are already in the index (`git add <pliki>`), so the restore will be exact.
2. In the production code invert or weaken the protected behaviour — a change only in the working tree.
3. Run only that test. Red = the gate PASSES.
4. Always restore with `git checkout -- <plik>`, also after a failure; the breakage never goes into a commit.
5. The test is green on the broken code → the assertion protects nothing → strengthen the assertion (do not weaken the code, do not skip the step).

## The STOP block (then the end: no further changes and no commit)
```text
STOP — <STRUCTURAL DIVERGENCE | GATE FAILURE> in phase <N>
Expected: <what the plan says / what the gate requires>
Found: <the actual state / a summary of the error>
Why it blocks: <why it cannot continue without the human's decision>
Resume: <what to fix>, then again from phase <N>
```
Before stopping: ticked items stay, work in progress stays uncommitted in the working tree,
the deliberate breakage restored.

## The final report (always — after success and after STOP)
```text
REPORT — <step>
Phases: <done>/<all>
- Phase 1: <title> — <SHA> (gates: tests, deliberate-breakage, lint, types: PASS)
- Phase 2: <title> — STOP (<reason>)
Adaptations: <one line each or "none">
Uncertainties: <points where the plan and the code disagreed, without an independent source — or "none">
For manual verification (for the human): <items from the plan, literally>
Next step: a review in a fresh context (core-git-workflow; tests from the specification, pack-it: qa-spec-first-testing)
```

## References in commits
Issue identifiers (`ABC-123`, `#123`) you add in the commit footer only when they came up in the conversation or
the plan — you never make them up from the branch name.
