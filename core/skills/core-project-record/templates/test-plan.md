---
artifact: test-plan
phase: plan
status: draft
version: 1
author: <agent>
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
inputs: [docs/project/03-requirements/requirements.md]
---
# Test plan: <scope>

## TL;DR
<Scope, the highest risks, the number of cases (automatic/manual), levels, the exit criterion.>

## Scope and risks
| Area / requirement | Impact | Likelihood | Risk | Techniques | Level |
|---|---|---|---|---|---|

## Test cases
The expected result comes from the source — never from the code (pack-it: qa-spec-first-testing).
| ID | Requirement | Technique | Preconditions | Steps / input | Expected result | Source of the result | Level | Auto/manual | Priority |
|---|---|---|---|---|---|---|---|---|---|

## Exploratory sessions and UAT
| Charter | Time | Who |
|---|---|---|

## Entry and exit criteria
- Entry: <e.g. acceptance criteria approved>
- Exit: <e.g. all H cases green or with a defect accepted by the owner; mutation score of the critical logic ≥ …>

## Open questions
## Handoff
- **For:** <the test automation persona>
- **Task:** automate the cases marked "auto", starting with priority H; red first
- **Read:** TL;DR, the cases table
