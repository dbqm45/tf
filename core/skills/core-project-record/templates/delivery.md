---
artifact: delivery
phase: delivery
status: proposed
version: 1
author: <agent>
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
inputs: [docs/project/05-plan/plan.md]
---
# Delivery of step #<n>: <name>

## TL;DR
<What was delivered, whether the criteria are met, what is left.>

## Step plan (approved before the code)
Approved by: <who, date>. A deviation from the plan = an update of this section in the same commit as the code.

### End state
<What is true after the step and how to check it — behaviour, not the existence of files.>
### Out of scope
- <what is deliberately NOT done in this step>
### Key decisions
| Decision | Choice | Why (1 sentence) | Source (research / reframing / plan) |
|---|---|---|---|
### Phase 1: <name>
- `<path/file>` — **Intent:** why the change (1–2 sentences). **Contract:** a signature, a schema field, a route or
  an invariant that must not be broken. A code fragment only for a non-obvious change.
- Automatic criteria: `<command>`
- Manual criteria: <what the human looks at>
### Risks and open questions
<Empty before delivery starts — questions are settled before the code or explicitly accepted as a risk.>
### Progress
> `- [ ]` to do, `- [x]` done; after the phase's commit add ` — <sha>`. You do not change numbers or titles.
#### Phase 1: <name>
- [ ] 1.1 <automatic criterion>
- [ ] 1.2 <manual criterion> (manual)

## Changes
<commits / PR, the most important files>
## Verification
<tests, lint, build — commands and the result>
## Deviations from the plan and decisions
## Human decisions vs AI proposals
| Agent's proposal | Human's decision | Why |
|---|---|---|
## Open questions
## Handoff
- **For:** <the next step / a review>
