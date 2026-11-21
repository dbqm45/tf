# Session artifact template

Path: `docs/project/04-architecture/design-<slug>.md`. Header keys and section rules: core-project-record
(`## TL;DR`, `## Open questions`, `## Handoff` are matched literally by `project_record.py check`; no `<…>` left over).

```markdown
---
artifact: design-session
phase: architecture
status: proposed
version: 1
author: <agent>
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
inputs: [<code paths and records read in Explore>]
---
# Design: <subject>

## TL;DR
<state (Explore | Design: stage N of M | Build), the chosen direction, accepted decisions D-NNN, the top risk>

## Problem and scope
<the problem in the developer's words, the goal, in scope, out of scope>

## Stage map
| # | Stage | Status |
|---|---|---|
| 1 | <stage> | accepted / open / skipped (assumptions below) / reopened |

## Stage 1: <name>
**Proposal.** <short; claims labelled [fact] plik:linia, [assumption], [recommendation], [risk]>
**Options.** | Option | Buys | Costs | Fails when | — the chosen one marked, rejected ones with one-line reasons
**Diagram.**
<Mermaid block; current state and proposal as separate diagrams>
**Decision.** D-NNN — <one line> (accepted by: user, <date>)

## Open questions
- <question> — <who answers>

## Handoff
**Story.** <one paragraph: who, what, why>
**Acceptance criteria.**
- AC-1 <observable behaviour a test can check>
**Out of scope.** <items; parked ideas go to parked.md>
**Decisions to respect.** D-NNN, …
**Tasks** (when bigger than one PR): 1. <task> → `/tf …` · 2. …
```

## What makes it good
- A reader who missed the session understands the direction from the TL;DR and the stage map alone.
- Rejected options keep one line each: the next person does not propose them again without a new reason.
- Acceptance criteria describe behaviour, not implementation ("a role cycle is rejected with a message", not
  "add a DFS in RoleService").
- Depth follows risk: the stage with the costly decision gets the words, the obvious ones get a line.
