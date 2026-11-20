---
name: qa-change-review
description: Use when reviewing a plan before code or code against the plan — consistency, grounding, drift (excess, gap), findings with weight and impact, triage.
metadata:
  review: "2027-10-10"
  catalog: "Use when a written step plan has to be checked before coding (will it work, is it consistent, does it fit the code base) or an implemented phase has to be checked against that plan before merge (drift, excess, gap, criteria really run, security and quality pass), and then the findings are walked through with the human one by one and recorded. The agent prepares evidence, the human decides. Not for configuring automatic PR review in CI or REVIEW.md (core-git-workflow), writing the plan itself (core-plan-interview), clean-code style rules (eng-clean-code) or deciding whether a test checks the requirement (qa-spec-first-testing)."
  keywords: "przegląd planu, sprawdź plan, review planu, czy plan zadziała, przegląd implementacji, zgodność z planem, dryf od planu, implementacja vs plan, przed scaleniem, ustalenia przeglądu, triaż ustaleń, co naprawić teraz, werdykt przeglądu, agent zrobił coś innego niż w planie, pliki spoza planu, plan review, review the plan, will the plan work, implementation review, conformance to the plan, drift from the plan, implementation vs plan, before merge, review findings, findings triage, what to fix now, review verdict, the agent did something different than the plan, files outside the plan"
---

# Change review — the plan before code, the code against the plan

Two moments, one record:
- **Pre-implementation plan review** — "will this plan work?" Verdict: **ready / needs fixing / needs rethinking**.
- **Post-implementation conformance review** — "did we build what the plan promised, and is it safe to merge?"
  Verdict: **approved / needs attention / rejected**.

Both end in triage with the human. The agent gathers evidence and proposes; the human decides every finding.

## Input and output
- Input: the step report `docs/project/06-delivery/NNN-*.md` (the approved plan, its end-state criteria, the "Progress" section)
  and `docs/project/lessons.md`. **No step report or plan given** → ask for it, or say that core-plan-interview produces the plan
  and core-project-record holds the `delivery` template. Never review a plan reconstructed from the conversation, never invent findings.
- Output: `docs/project/07-review/<date>-plan-review-<step>.md` or `docs/project/07-review/<date>-impl-review-<step>[-fN].md`
  (`-fN` = phase N), written from the core-project-record `review` template: the verdict, the **Grounding** line, the findings table
  with Weight, Impact and Decision.
- A previous report for the same step with `PENDING` decisions → do not review again; resume at triage.

## A. Plan review (before code)
1. **Internal consistency first** — the cheapest check with the best yield:
   - a constraint stated at the top that no phase honours;
   - an item from "out of scope" that returns in a phase;
   - an end-state criterion that no phase builds (a promise without a phase);
   - phase B uses an id, field or endpoint that phase A never returns;
   - "Progress" rows that do not map one-to-one to the criteria;
   - a summary that says something the body does not.
2. **Ground the plan yourself** (cheap, no helper): check that at least 5 paths named in the plan exist, grep the named
   functions/types/config keys, compare the summary with the body. Write it as one line, e.g.
   `Grounding: 6/7 paths exist (src/export/csv.ts missing), 4/4 symbols found, summary matches the body`.
3. **Verify the riskiest claims in code** — the 2–3 statements that would sink the plan if false ("the function has no other callers",
   "nothing exports CSV yet", "the column is nullable"). Hand them to one read-only helper (the `scout` agent) and ask for
   confirm/refute with `file:line`, other callers of functions the plan changes, and existing code that already does the job.
   Fast mode may skip this step; say so in the report.
4. **Dimensions** (look, do not pad):
   - **End state** — could every criterion go green while the goal is still missed?
   - **Economy** — phases, abstractions or options nobody asked for (YAGNI).
   - **Fit** — matches the module boundaries and dependency direction of the code base.
   - **Blind spots** — error paths, rollback, data migration, cost, changed defaults, tests, security.
   - **Feasibility** — concrete paths and verification commands in every phase, no "TODO", no "figure out later".
5. **Verdict.** A sound plan gets a short report: "no findings", verdict **ready**. Do not add observations to look thorough.
   **needs fixing** = local corrections; **needs rethinking** = the approach or the split into phases is wrong.

## B. Implementation review (after a phase, before merge)
1. **Scope from history.** Take the commits since the plan was approved (`git log`/`git diff <base>..HEAD --name-only`).
   Sort the files into three sets and keep **lists, not contents**, in the main session:
   - **MATCH** — planned and changed;
   - **EXCESS** — changed but not in the plan (outside the plan);
   - **GAP** — in the plan, no diff (e.g. a planned migration that never appeared; in a Polish report mark it `BRAK`).
   A change marked **DRIFT** is in a planned file but does something different from what the plan says.
2. **Two independent passes, in separate contexts** (separate subagents, so one does not anchor the other):
   - **Plan conformance** — drift, excess, gap, criteria, the plan's out-of-scope list respected.
   - **Security and quality** (the `security-reviewer` agent for the security part): injection, secrets in code or logs,
     authorization at boundaries (a foreign resource), N+1 and missing pagination, error handling at external edges, races,
     destructive data operations without a migration path, consistency with 1–2 sibling files of the same kind (eng-clean-code).
3. **Run the plan's automatic criteria** (e.g. `npm test`, `npm run lint`) and paste the output **verbatim**, with the exit code.
   A manual criterion ticked in "Progress" with no trace in the diff is a finding of its own: "ticked without evidence".
4. **Reading order for the human:** scope (the three sets) → risk boundaries (auth, writes, migrations, external APIs, config)
   → local patterns → tests. A green test the agent wrote is information, not proof — whether it checks the requirement
   is the job of qa-spec-first-testing.
5. **Judge only what the plan promised.** What the plan explicitly put out of scope is not scope creep, and its absence is not a gap.
6. **Verdict.** Any critical finding in a dimension → **rejected**; warnings only → **needs attention**; otherwise **approved**.
   The CI variant (the verdict as a merge gate, `.claude/skills/core-git-workflow/references/ai-review-in-ci.md`) is configured there, not here.

## Findings
Every finding has: id, **Weight** (critical / warning / observation), **Impact** (low / medium / high), dimension, place
(`file:line` or the plan section), evidence, and a fix.
- **Weight** = what it costs to ignore it. **Impact** = how hard and how broad the decision is. They are independent:
  a critical typo in a constant is critical with low impact.
- **One fix** by default. Two only when there is a real trade-off — each with approach, strength, cost, confidence and what was not
  checked, and exactly one marked as recommended.
- **At most 10 findings.** Merge near-duplicates (14 identical naming violations = one finding with the count and 2–3 examples).
- **Never print a secret's value** — describe it: "AWS access key in `config/dev.ts:12` (40 chars, starts `AKIA`)", then advise rotation.
- A finding that breaks a rule already recorded in `docs/project/lessons.md` goes one weight up and cites the lesson.

How weight and impact usually translate into a decision (a heuristic, not a rule):

| | low impact | high impact |
|---|---|---|
| **critical** | fix now, it is cheap | stop, narrow the change, decide with the human first |
| **observation** | usually skip | check whether the pattern spreads elsewhere |

## Triage with the human
1. One finding at a time, critical first. Show the evidence and the proposed fix, then offer:
   - **fix now** — show the before/after, apply, mark `FIXED`;
   - **fix differently** — the human's approach, then `FIXED`;
   - **skip** — `SKIPPED`;
   - **accept the risk** — with the human's reason, `RISK_ACCEPTED`;
   - **reject the finding** — with the reason ("not a problem because …"), `REJECTED`;
   - **record as a lesson** — pre-fill the rule from the finding, the human completes the rule and its scope, it goes to
     `docs/project/lessons.md` (core-project-record), mark `LESSON`; **then always ask whether to fix the code too**.
2. Update the saved report after every decision, so an interrupted session can resume.
3. A large change: save the report with everything `PENDING` and triage in a later session. Deferred fixes go to the step
   report's "Open questions".
4. After triage the next step is named, not run: back to implementation, or the next phase via core-delivery-lifecycle.

## Example
Input: the step report of step 003 (CSV export), phase 2 implemented, the plan lists 6 files, the diff has 8.

```
Implementation review — 003-export, phase 2. Verdict: needs attention (0 critical, 2 warnings, 1 observation)
Grounding: 6/6 planned paths read, 3/3 symbols found, summary matches the plan
Sets: MATCH 5 · EXCESS 3 (src/util/date.ts, src/api/admin.ts, package.json) · GAP 1 (migrations/007_export_jobs.sql)
Criteria: `npm test` → exit 0, 142 passed (output pasted below); "CSV opens in Excel" ticked, no trace in the diff → finding F3
| # | Weight | Impact | Finding | Evidence | Recommendation | Decision |
| F1 | warning | high | planned migration missing (GAP); the job table is created at runtime | src/export/jobs.ts:31 | add migration 007, remove runtime CREATE | PENDING |
| F2 | warning | low | admin route added outside the plan, no role check | src/api/admin.ts:14 | remove from this step or add authz + test | PENDING |
| F3 | observation | low | manual criterion ticked without evidence | Progress row 4 | attach the check or untick | PENDING |
```
More worked reports (a plan review with "no findings", a rejected implementation): `references/examples.md`.

## Sources
- Google Engineering Practices, "What to look for in a code review" (google.github.io/eng-practices) — design, functionality,
  complexity, tests and consistency as review dimensions (accessed 2026-10-10).
- ISO/IEC 20246:2017, Software and systems engineering — Work product reviews: review as a structured examination of a work
  product with recorded findings and decisions.
