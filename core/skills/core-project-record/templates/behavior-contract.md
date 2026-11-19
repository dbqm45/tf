---
artifact: behavior-contract
phase: delivery
status: draft
version: 1
author: <agent>
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
inputs: []
---
# Behaviour contract: <unit being refactored>

## TL;DR
<What we change (idiom from → to), what is frozen, the result (green / gaps).>

## Frozen
- **Scenarios and DSL:** <file paths>
- **Public contract:** <signatures, events, DTOs, the kind of rejection>
- **Consistency boundary:** <what is loaded and saved atomically, versions/locks>

## Assertion register
| Original assertion | Assertion in the DSL | What it no longer distinguishes | Why that is acceptable |
|---|---|---|---|

## Steps and commits
| Step | Commit | Test result |
|---|---|---|

## Coverage gaps and hidden defects
## Open questions
## Handoff
- **For:** <persona>
- **Task:** <a review / the next unit>
- **Read:** TL;DR, Assertion register
