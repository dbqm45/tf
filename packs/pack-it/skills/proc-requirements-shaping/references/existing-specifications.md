# A repo with existing specifications (Spec Kit, OpenSpec) and a change delta

Contents: 1. Recognize first · 2. Spec Kit · 3. OpenSpec · 4. A change delta and merging into the current state

## 1. Recognize first
Before you start a session, check whether the repo already has requirements in an SDD tool. If so, **you read them as the existing
requirements, rules and plan** and add a delta at the indicated place. You do not write a parallel document: two sources of
truth quickly drift apart. You do not change the tool's conventions without the human's decision.

## 2. Spec Kit (github/spec-kit)
| File | What it is for this procedure |
|---|---|
| `.specify/memory/constitution.md` | the project's rules, read alongside CLAUDE.md (you do not copy them into the requirements) |
| `specs/<NNN-funkcja>/spec.md` (e.g. `specs/003-user-auth`) | the requirements of a feature. You do the EARS lint and the FR challenge as a report, without rewriting the file |
| the markers `[NEEDS CLARIFICATION: …]` in `spec.md` | open questions for the human (the "Challenge" phase) |
| `specs/<NNN-funkcja>/plan.md` | the plan with a section on compliance with the constitution |
| `specs/<NNN-funkcja>/tasks.md`, tasks `T001 [P] …` | `[P]` = can run in parallel (different files, no dependencies): the "In parallel with" column in the cut plan |

The commands (`/speckit.specify`, `/speckit.plan`, `/speckit.tasks` and others) and the extensions (`.specify/extensions.yml`)
change between versions, so before use you check the version in the project's repo.

## 3. OpenSpec (Fission-AI/OpenSpec)
- `openspec/specs/<obszar>/spec.md` — the **current state** of the system: `### Requirement: <nazwa>` with scenarios
  `#### Scenario: <nazwa>`.
- `openspec/changes/<nazwa-zmiany>/` — the proposal, tasks and the **specification delta**: the sections `## ADDED Requirements`,
  `## MODIFIED Requirements`, `## REMOVED Requirements` (and renames).
- **Archiving** merges the delta into `openspec/specs/` and moves the change folder to `openspec/changes/archive/` with a date.
  You read the requirements from `openspec/specs/`, and you add the current change's delta in its folder.

## 4. A change delta and merging into the current state (also without an SDD tool)
The change document describes the difference, and one main document describes how the system works today. Without merging, after 30 changes
nobody knows what applies.
- A change records requirements as a **delta**: added, modified (the full new text, not just the difference) and removed
  (with a reason). Requirements have stable names or keys, because merging matches by name.
- **Closing a change = merging** the delta into the main requirements document. The change document stays as history (why
  and who decided), not as the source of the current state.
- **The check after merging:**
  - a requirement added or modified in the delta with no counterpart in the main document is a finding;
  - a requirement removed that is still in the main document is a finding;
  - a modified requirement that lost a scenario or an acceptance criterion with no entry in "removed" is a finding.
- A change in an existing system: guarantees approved as protected behaviors enter the delta as added
  (the first record of the requirement) together with a test (eng-behavior-preserving-refactoring).

Sources (checked 2026-11-01 in the repositories): github.com/github/spec-kit (1.2.5, 2026-10-28; `templates/`,
`templates/commands/specify.md`, `tasks-template.md`); github.com/Fission-AI/OpenSpec (1.16.0, commit 2026-10-30;
`docs/overview.md`, `docs/writing-specs.md`, `docs/agent-contract.md`). Articles: Chimin, "OpenSpec + Superpower"
(2026-05-30); P. Qian, "From OpenSpec to AIDLC" (2026-09-04).
