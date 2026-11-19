---
name: qa-exploratory-manual
description: Use for manual and exploratory testing — chartered sessions, heuristics, UAT, manual accessibility, defect reports.
metadata:
  review: "2027-10-17"
  catalog: "Use for manual and exploratory testing — chartered sessions (session-based testing), exploration heuristics, acceptance tests with users (UAT), manual accessibility, manual regression checklists and defect reporting. Not for automation (tool-*, qa-regression)."
  keywords: "zgłoszenie błędu, zgłoszenie defektu, jak napisać zgłoszenie, raport defektu, testy ręczne, sesja eksploracyjna, UAT, jak opisać błąd, bug report, defect report, how to write a bug report, manual testing, exploratory session, how to describe a bug"
---

# Manual and exploratory testing

Automated checks verify what we anticipated. Exploration looks for what we **did not anticipate**: gaps in the requirements,
usability problems, unexpected combinations. The two kinds complement each other.

## Exploratory session (session-based)
- **Charter:** "Explore *<area>* using *<resources/data/role>* to discover *<kind of information/risk>*".
  E.g. "Explore booking a room as two users at once to discover concurrency problems".
- **Time:** 45–90 minutes, with no breaks for other tasks.
- **Notes:** what was checked, ideas for further charters, **defects**, **questions** (ambiguities in the requirements).
- **Debrief:** coverage, problems found, risks, recommendations for new automated tests.

## Heuristics
- **SFDPOT**: Structure, Function, Data, Platform, Operations (how people really use it), Time (time zones, deadlines, concurrency).
- **CRUD** on every object; **Goldilocks** (too little / too much / just right); **interrupt** (refresh, back, network loss, close the tab halfway);
  **boundaries** (qa-test-design); **roles and permissions** (what does another user see?); **localization** (Polish characters, date format, currencies).

## When manual, when automated
| Manual | Automated |
|---|---|
| new features (first familiarization), usability, visual assessment, accessibility with a screen reader, UAT | repeatable checks, regression, edge data, many combinations, critical paths |
A manual case executed a third time unchanged → a candidate for automation.

## The agent as a manual tester
The agent explores through a browser (e.g. Playwright in headed mode or browser tools), keeping notes as in a session.
What it cannot assess on its own (user feelings, a screen reader) it prepares as a **session charter for a human**.

## User acceptance tests (UAT)
Scenarios from the acceptance criteria in business language, executed by users; the result: acceptance / a list of remarks with a priority.

## Defect report
```markdown
**Title:** <what is wrong, where> (e.g. "The 5% discount is not applied for exactly 10 units")
**Environment:** version/commit, browser, data
**Steps:** 1. … 2. … 3. …
**Expected:** … — **source:** requirements.md H1-AC2 / TC-014
**Actual:** …
**Evidence:** screenshot, trace, log, automated test (file:line)
**Severity / priority:** critical | high | medium | low — with a justification (impact × frequency)
```
One defect = one report; no judging of people, just facts.
