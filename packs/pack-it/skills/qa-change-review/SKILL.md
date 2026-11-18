---
name: qa-change-review
description: Use when reviewing a plan before code or code against the plan — drift, severity, triage, verdict.
metadata:
  review: "2027-10-10"
  catalog: "Use when you must check a step plan before the agent starts coding (consistency, grounding in the repo, verification of risky claims, dimensions, verdict), or an implementation against the approved plan after a phase or before merge (three sets of files, drift, excess and gaps, security and patterns, criteria), and then walk through the findings with the human (a severity × impact matrix, triage with decisions, recording as a lesson). Not for the PR process and configuring review through a service or CI (core-git-workflow), security alone (the security-reviewer agent), code readability without a plan (eng-clean-code), interviewing the human before a plan (core-plan-interview), or reviewing a requirements specification before a plan — a panel of independent reviewers (core-delivery-lifecycle)."
  keywords: "przegląd planu, sprawdź plan, review planu, czy plan zadziała, przegląd implementacji, zgodność z planem, dryf od planu, implementacja vs plan, przed scaleniem, ustalenia przeglądu, triaż ustaleń, co naprawić teraz, werdykt przeglądu, agent zrobił coś innego niż w planie, pliki spoza planu, plan review, review the plan, will the plan work, implementation review, conformance to the plan, drift from the plan, implementation vs plan, before merge, review findings, findings triage, what to fix now, review verdict, the agent did something different than the plan, files outside the plan"
---

# Reviewing a change against the plan

A bad plan costs hours of work, a plan review costs minutes. A **plan review** asks "will this plan work?",
an **implementation review** asks "did we build what we planned, and can it be merged safely?".
The agent prepares the report and runs the triage; the verdict and the decisions belong to the human. Findings are not hunted
for: a good plan or good code gives a short report.

## Input
- The step report `docs/project/06-delivery/NNN-*.md` with the plan (end state, out of scope, phases, criteria)
  and the "Progress" section (the `delivery` template in core-project-record).
- A study or reframing next to the step report, if they exist.
- `docs/project/lessons.md` — a finding that breaks a recorded lesson has a higher severity.
- An earlier review report → resume from triage (findings with the decision `PENDING`).

## Mode A — plan review (before code)
1. **Internal consistency** (this is where most hits are):
   - contradiction — a constraint described at the top and ignored in the phases; an "out of scope" item that returns in a phase;
   - a promise without a phase — an end-state criterion that no phase builds;
   - a broken contract — phase B needs an identifier or field that the result of phase A does not return; a decision
     the implementer would have to guess;
   - "Progress" ↔ phases — every criterion has its own row, checkboxes only in "Progress".
2. **Grounding** (on your own, without implementers): the existence of at least 5 paths from the plan, a `grep` of function names and keys,
   the TL;DR matching the content. The result in one line, e.g. `Grounding: 5/5 paths, 3/3 symbols, TL;DR consistent with the plan`.
3. **Verification in code** (skipped in fast mode): the 3–5 riskiest claims of the plan → one
   implementer (e.g. `scout`) with three tasks: confirm or refute each claim with `file:line`; find the other
   callers of the functions being changed (a reach the plan does not know about); check whether existing code already solves what
   the plan builds from scratch.
4. **Dimensions:**
   - conformance to the end state — can all the criteria pass and the goal still not be achieved?
   - economy — is the goal achievable without this phase; an abstraction "just in case"; changes "while we're at it";
   - fit to the architecture — a new pattern next to an existing one, the direction of dependencies, "refactor as needed";
   - blind spots — error paths, rollback, cost, a change of defaults, tests, security boundaries;
   - feasibility — concrete paths and verification commands, no TODOs.
5. **Verdict:** **ready** / **needs fixing** (concrete plan fixes) / **needs rethinking** (a problem with the approach —
   go back to the study or reframing).

## Mode B — implementation review (after a phase or before merge)
1. **Scope from git:** the commits since the plan was approved (`git log --since`, `git diff <base>...HEAD --stat`) and three
   sets of files: in the plan and in the diff (check the content) · in the diff without the plan (**EXCESS** — an unplanned change) ·
   in the plan without a diff (**GAP**). The main session holds the plan and the file list, not their content.
2. **Two independent passes** (in parallel, in separate contexts):
   - **drift** — for every planned change: MATCH / DRIFT / GAP / EXCESS, with a quote from the plan and `file:line`;
   - **security, quality, patterns** — injections, secrets, authorization at the boundaries; N+1 and missing
     pagination; error handling at external boundaries, races; destructive data operations without a migration
     path; a comparison with 1–2 similar files in the repo (only significant differences; with ≤ 3 files, briefly).
3. **Criteria:** run the automatic commands from the plan and show the result verbatim. A manual criterion ticked off
   in "Progress" with no trace in the diff → the finding "ticked off without checking".
4. **The order of reading the diff for the human:** scope → risk boundaries (auth, data writes, migrations, external
   APIs, configuration) → local patterns → tests (would the test catch the error we want to avoid; the agent's green test
   is information, not proof — qa-spec-first-testing).
5. **Dimensions:** conformance to the plan · scope discipline · security and quality · architecture · consistency of patterns
   · success criteria. The plan defines what "tested" means — you do not assess what it did not promise, and its
   "out of scope" is not scope creep.
6. **Verdict:** **approved** / **needs attention** / **rejected** (any critical failure of a dimension).

## Finding
`ID · severity · impact · dimension · place · detail with evidence · fix`
- **Severity** — how bad if we ignore it: critical / warning / observation.
- **Impact** — how hard the decision is: low (the fix is obvious and local) / medium (a real trade-off) /
  high (wide reach: data, contract, product). Severity and impact are independent.
- **Place** — `file:line` or a section of the plan.
- By default one fix. Two only with a real trade-off; then each has: approach · strength ·
  cost · confidence · what was not checked, and exactly one is recommended.
- At most 10 findings — merge similar ones ("6 files break the naming convention" = one finding). You describe a secret without
  its value.

## Severity × impact matrix (heuristic)
| Severity \ impact | low | medium | high |
|---|---|---|---|
| critical | fix now | fix carefully | stop, narrow the fix |
| warning | fix or skip | depends on context | usually needs planning |
| observation | usually skip | a note or a lesson | check whether the problem occurs in many places |

## Triage (one by one, starting with the critical ones)
For each finding the human picks a decision:
- **fix now** — show before/after, confirm, a minimal change;
- **fix differently** — the human's approach;
- **skip**;
- **accept the risk** — with a justification;
- **reject** — the finding is wrong, with a justification;
- **record as a lesson** — an entry in `docs/project/lessons.md` pre-filled from the finding (context = place,
  problem = detail); the human completes the rule and the scope (lesson format: core-project-record). Then **always**
  the question "apply the fix in the code too?" — you do not decide for the human.
Not every finding has to be fixed. After each decision, update the saved report.

## Recording
- `docs/project/07-review/<date>-plan-review-<step>.md` or `…-impl-review-<step>[-fN].md`, the
  `review` template (core-project-record) with the Impact and Decision columns and a "Grounding" line.
- Decisions: `PENDING` / `FIXED` / `SKIPPED` / `RISK_ACCEPTED` / `REJECTED` / `LESSON`.
- Deferred fixes → the step report's "Open questions".
- A larger change: save the report, let the human read it in peace, triage in the next conversation.
- The same pattern in CI (the verdict as a workflow gate, inline comments): core-git-workflow,
  `.claude/skills/core-git-workflow/references/ai-review-in-ci.md`.

## Example
**Situation:** an implementation review of the step "saving accepted flashcards", phase 2. Three sets: 6 files matching,
EXCESS `src/lib/format.ts` (a helper for planned code), GAP — none.
**Report (excerpt):**
```
Grounding: 6/6 paths, 4/4 symbols, TL;DR consistent with the plan · npm test → 48 passed
| ID | Severity | Impact | Dimension | Place | Finding | Decision |
| F1 | critical | low | security | api/cards/save.ts:18 | the save endpoint bypasses the shared authorization guard | FIXED |
| F2 | observation | high | consistency | db/schema.ts:40 | a new status name in the database (frontend, backend, historical data) | SKIPPED (note) |
| F3 | warning | low | patterns | actions/deck.ts:12 | a manual userId check instead of the guard | LESSON + FIXED |
Verdict: needs attention → after triage approved
```
More (plan review, a good plan with no findings): `references/examples.md`.

## Checklist
- [ ] mode chosen (plan / implementation); input read, lessons taken into account
- [ ] plan: consistency, grounding (a line with numbers), risky claims checked in code, dimensions
- [ ] implementation: three sets of files, drift and security separately, criteria run, result verbatim
- [ ] every finding with severity, impact, place and evidence; at most 10
- [ ] triage with the human's decision for every finding; a lesson always with the question about the fix
- [ ] the report in `07-review/`; the verdict belongs to the human

## Sources
- The 10xDevs course, ed. 3 (2026), module 2, lessons 2–3 (plan review, implementation review, triage) and module 5,
  lesson 3 (review in CI) — training material (accessed 2026-10-09).
- Google Engineering Practices, "What to look for in a code review" — google.github.io/eng-practices (accessed 2026-10-10).
- Factory conventions: core-project-record (the step report, "Progress", lessons), core-git-workflow (PR, `REVIEW.md`).
Described in our own words.
