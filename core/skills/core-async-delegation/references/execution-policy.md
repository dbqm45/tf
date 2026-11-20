# Unattended plan execution - policy and line formats
> 6. Line formats - 7. Final report - 8. Example transcript

This is the factory's own convention for running an approved plan with `claude -p` or `/goal` while nobody is watching. The
line formats are fixed because evaluators, `/goal` conditions and reviewers read only the transcript. The engineering behind
it is ordinary: bounded retries, fail closed on surprises, and a mutation-style check that a new test fails on broken code.

## 1. Preconditions
- The plan is a file: `docs/project/<step>/plan.md` with phases, files per phase, verification commands, and a progress
  section. The first unticked progress item is where execution starts or resumes (core-project-record,
  core-delivery-lifecycle).
- Chat notes are not a plan. Without a plan file, do not start; say which file is needed.
- Every verification command named for a phase must be runnable before that phase starts. A missing tool or script is a STOP
  for that phase, not a reason to invent another check.

## 2. Per-phase loop
1. Read the phase; compare it with the repository. Minor divergence (a renamed or moved file) -> adapt and print `ADAPT`.
   Structural divergence (a missing dependency, a different architecture, the previous phase's result absent) -> STOP. In
   doubt, treat it as structural.
2. Make the change, staying within the phase's files.
3. Run the gates in order of cost:
   1. the plan's own verification commands;
   2. `git add <files>` for the phase's files by name;
   3. deliberate breakage for every new or changed test (section 3);
   4. full test suite, lint, type check;
   5. commit (section 5).
4. Tick the phase's progress items in the plan. Manual verification items stay unticked and go to the report.

## 3. Deliberate breakage
- Files are already staged, so the restore is exact.
- Break the protected behaviour in the working tree only (invert a condition, return a wrong value).
- Run only the test that should catch it. Red -> the gate passes. Green -> the assertion protects nothing: strengthen the
  assertion (not the production code, not a skip) and repeat.
- Always restore with `git checkout -- <file>`, also when something failed in between. The breakage is never committed.

## 4. Repairs and STOP
- At most 2 repair attempts per gate. A third failure stops the run.
- Never weaken a test, an assertion, a lint rule or a type check to pass a gate.
- "Not possible within scope" is a legitimate result. STOP and report; never route around a boundary.
- On STOP: leave ticked items as they are, leave work in progress uncommitted, restore any breakage, make no further changes,
  write the final report.
- With `/goal`, add a progress condition: each turn improves at least one measured value from a tool; two turns without
  improvement -> STOP; the same command run a third time with an unchanged result -> STOP; plus a turn limit.

## 5. Commits
- Only on green. Message per core-conventional-commits; files added by name.
- Unrelated dirty files are listed, not added.
- No `--no-verify`, no `--amend`. A failing pre-commit hook is a gate failure (counts toward the 2 attempts).
- Issue ids in the footer only when the plan or the conversation names them; never derived from the branch name.

## 6. Line formats
```
GATE <name>: PASS
GATE <name>: FAIL (<short reason>, attempt k/2)
ADAPT: <what changed against the plan and why>
DIRTY (not added): <files>
COMMIT phase N: <sha>
```
STOP block:
```
STOP — <STRUCTURAL DIVERGENCE | GATE FAILURE> in phase <N>
Expected: <what the plan says>
Found: <what the repository shows, with file:line or command output>
Why it blocks: <one sentence>
Resume: <what a human must decide or provide; the plan item to resume from>
```

## 7. Final report
Always written, also after STOP:
```
REPORT — <step>
Phases: <N: sha | N: STOP | N: not started>
Adaptations: <ADAPT lines or none>
Uncertainties: <assumptions taken under the conservative rule>
For manual verification (for the human): <unticked manual items>
Next step: review in a fresh context | decision needed on <...>
```

## 8. Example transcript
```
GATE plan-commands: PASS
GATE breakage(refund_rounding_test): PASS
GATE full-suite: FAIL (lint: unused import in refunds.ts, attempt 1/2)
GATE full-suite: PASS
COMMIT phase 2: 4f1c2ab
DIRTY (not added): .vscode/settings.json
STOP — STRUCTURAL DIVERGENCE in phase 3
Expected: src/payments/ledger.ts exports postEntry()
Found: ledger module replaced by src/accounting/** (git log -1 -- src/payments/ledger.ts: removed 2 days ago)
Why it blocks: phase 3 changes a module that no longer exists
Resume: update plan phase 3 to the accounting module; resume from item 3.1
REPORT — payments-refunds
Phases: 1: 9b07e1d | 2: 4f1c2ab | 3: STOP
...
```
