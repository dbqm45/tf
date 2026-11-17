# Step progress, exploration and the tracker

> Details for the core-project-record SKILL.md: the "Progress" section in the step report, research steps, human decisions
> vs AI proposals, moving the slice plan to a tracker.

## Progress of a delivery step (the "Progress" section in `06-delivery/NNN-*.md`)
The step plan (the `delivery` template) ends with a "Progress" subsection — the only place for the step's delivery state:
- the checkboxes `- [ ]` / `- [x]` are only in "Progress"; the rest of the plan has none;
- the `<faza>.<n>` numbering given at planning is never renumbered — a removed item leaves a gap,
  a changed intent is a note in the phase block, the title stays the same;
- the next step = the first `- [ ]`; the current phase = the phase of the first `- [ ]`; completion = `[x] / ([ ] + [x])`;
- you tick a box after each step; you add the SHA once, after the phase's commit (` — <sha>`, core-git-workflow).
  In the middle of a phase `[x]` without a SHA is a correct state; a phase without code changes stays without a SHA;
- manual criteria are ticked only after the human confirms; at the last phase remind about all
  unmet manual criteria from earlier phases.
The checkpoint in `wip/` says which task is in progress; "Progress" says where in the step plan you are.

## Changes, phases and exploration
- **Exploration whose product is a report** (research, a code map, a ranking of options) is a separate entry — a separate step
  report with the intent at the top: what we study, what we do NOT do at this stage (no code changes, no decision),
  who decides and when. The next step reads this report as a starting point; you do not add the research to the previous,
  closed change.
- The step report and the review report have a **"Human decisions vs AI proposals"** section: what the agent proposed,
  what the human decided and why. It is a trace of who is responsible for what.

## The slice plan in a tracker (Jira, Linear, GitHub Issues)
- **The slice plan to the tracker:** an issue from a plan item — title = Result, description = Requirements + Preconditions + Risk
  + acceptance criteria; the labels `slice` / `foundation` / `star`; dependencies as issue links;
  the change identifier in the body.
- **The agent's access to the tracker:** a token with the smallest scope (reading and creating in one project, no
  administration); deleting, changing roles and bulk status changes are done by the human in the tool's interface. After the first
  session review the activity log and agree with the team whether the agent may change and comment on other people's issues.

## An example of the "Progress" section during phase 2
```
### Progress
#### Phase 1: Model and storage
- [x] 1.1 npm test -- cards.repo.spec.ts passes — 3f9c2a1
- [x] 1.2 the migration works on a copy of the database (manual) — 3f9c2a1
#### Phase 2: Endpoint
- [x] 2.1 npm test -- cards.api.spec.ts passes
- [ ] 2.3 401 for an anonymous user (2.2 removed — the gap stays)
- [ ] 2.4 the human checked the response in the browser (manual)
```
Next step: 2.3; current phase: 2; completion: 3/5. Item 2.1 without a SHA, because phase 2 has no commit yet.

Source: the 10xDevs course, ed. 3 (2026), module 2 (the plan progress format, moving the roadmap to a tracker) and module 4,
lesson 4 (research steps) — training material (accessed 2026-10-09). Described in our own words.
