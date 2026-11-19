# Review examples

## 1. A plan review with a promise without a phase
**The step plan** "export orders to CSV": end state "the admin downloads a file of up to 50 thousand rows in < 10 s, the file does not
contain personal data"; phases: 1) endpoint, 2) a button in the panel, 3) tests.
**Report (excerpt):**
```
Grounding: 4/5 paths (src/admin/ExportButton.tsx missing — the plan assumes an existing component), 2/2 symbols, TL;DR consistent
| ID | Severity | Impact | Dimension | Place | Finding | Fix |
| P1 | critical | low | consistency | End state ↔ Phase 1 | "no personal data" — no phase removes the email and phone fields | add the list of export columns to phase 1 and a test that email does not appear |
| P2 | warning | medium | blind spots | Phase 1 | 50 thousand rows in memory — no streaming and no time limit | (A, recommended) a CSV stream · (B) a background job with a link — a larger scope |
| P3 | warning | low | feasibility | Phase 2 | the component path does not exist | fix the path or add creating the component |
Verdict: needs fixing
```

## 2. A good plan — a short report
```
Grounding: 5/5 paths, 3/3 symbols, TL;DR consistent with the plan
Dimensions: conformance to the end state ✓ · economy ✓ · architecture ✓ · blind spots ✓ · feasibility ✓
Findings: none. Verdict: ready
```
Do not add observations to make the report "look like work".

## 3. An implementation with drift and a gap
The plan: 3 phases, 7 files. The diff: 9 files.
```
Sets: in the plan and in the diff 6 · EXCESS: src/utils/date.ts, src/config/flags.ts · GAP: db/migrations/0042_status.sql
| F1 | critical | medium | conformance to the plan | db/migrations/ | the planned status migration is missing; the code reads a column that does not exist | add the migration from the plan (expand) before merge |
| F2 | warning | low | scope discipline | src/config/flags.ts:3 | a new flag outside the plan; the plan excludes configuration changes | remove it or add it to the plan as a deviation |
| F3 | observation | low | consistency | src/utils/date.ts | a helper for planned code — a harmless addition | — |
Criteria: npm test → 61 passed; npm run typecheck → 2 errors (the result verbatim in the report)
Verdict: rejected (F1 critical + typecheck)
```

## 4. Triage with a lesson
Finding F3 (warning, impact low): "a manual check of `userId` in a server action instead of the shared guard".
The human: "record as a lesson". The agent proposes the entry:
```
- 2026-10-10 **new server actions use the shared authorization guard** — Context: src/actions/** ·
  Instead: requireUser() from src/auth/guard.ts · Applies to: implementation
```
and asks: "Apply the fix in `actions/deck.ts:12` now too?" — only the human's answer closes the finding.
