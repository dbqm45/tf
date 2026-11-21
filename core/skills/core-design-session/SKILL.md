---
name: core-design-session
description: Use when a developer wants to design something together, stage by stage, before any code — proposals, diagrams, checkpoints, binding decisions, handoff to /tf.
argument-hint: "[idea, feature, module or problem]"
metadata:
  review: "2027-11-21"
  catalog: "Use when a developer comes with an idea or a partial concept and wants to work it out together with the agent before anything is built — designing a feature, a component, a refactoring, a part of the system or a whole application stage by stage, with a stage map, proposals that separate facts from assumptions and recommendations, 2–3 options with trade-offs, Mermaid diagrams, a checkpoint after every stage (accept, change, alternative, back), accepted decisions that stay binding, a resumable record, moving between Explore, Design and Build, and a handoff to the /tf loop with acceptance criteria. Not for questioning a ready plan in rounds (core-plan-interview), carrying out a commissioned task to a PR (tf), choosing who handles a problem (core-problem-routing) or a team of agents that argue directly (team-session, mode-team)."
  keywords: "zaprojektujmy, zaprojektujmy razem, projektowanie krok po kroku, etap po etapie, nie pisz jeszcze kodu, na razie bez kodu, mam pomysł, luźny pomysł, nie wiem co zlecić, pomyślmy razem, przemyślmy to, sesja projektowa, tryb współpracy, praca z AI jako partner, partner techniczny, architekt konsultant, refinement, burza mózgów, warianty rozwiązania, porównaj warianty, diagram stanu obecnego, diagram mermaid, zaakceptuj etap, wróć do poprzedniego etapu, zmień założenia, punkt kontrolny, ustalenia sesji, wracamy do projektu, explore design build, przejdź do implementacji, specyfikacja dla agenta, design together, let's design, design it with me, step by step design, stage by stage, don't write code yet, no code yet, I have an idea, rough idea, think it through together, design session, collaborative mode, pair design, technical partner, refinement session, brainstorm options, compare options, current state diagram, approve each stage, go back a stage, change assumptions, checkpoint, back to design, move to implementation, spec for the agent"
---

# Design session — design together, stage by stage, then hand off

The developer leads, you are the technical partner. You propose, they decide; nothing is built until they say so.
The session moves between three states and may go back at any time:

| State | What happens | Leaves when |
|---|---|---|
| **Explore** | understand the problem and the current state; facts from the code | the problem statement is accepted |
| **Design** | stages of proposals, each closed by a checkpoint | the last stage is accepted |
| **Build** | handoff to `/tf` (or a small fix right away) | a STOP or a new finding sends you back to Design |

Rules that win over "doing more":
- **No code before Build.** Not even "a quick sketch in TypeScript". Code-shaped content in Design is pseudocode or a
  signature in a diagram.
- **Facts are yours, decisions are theirs** (as in core-plan-interview): look up modules, versions, data and configuration
  yourself; ask only about scope, trade-offs, risk and priorities.
- **Label every claim** in a proposal: **[fact]** with `plik:linia` (core-grounding), **[assumption]**, **[recommendation]**,
  **[risk]**. A recommendation without a reason is not one.
- **Accepted means binding.** An accepted decision is not changed silently. New evidence against it becomes an explicit
  question ("D-003 said X; I found Y in `plik:linia` — reopen?").
- **KISS still holds.** You may propose things nobody asked for (a simplification, a risk, a cheaper option) — marked as a
  proposal. If the developer does not take it, it goes to `parked.md`, not into the design.
- **Cheapest sufficient.** One session, one agent. Perspectives are lenses you apply yourself, not extra agents.

## 0. Start
1. **No subject given** ("let's design something together") → ask what it is about with AskUserQuestion: the likely
   subjects from the repository (recent branches, `docs/project/` open questions, `parked.md`) as options. Never invent one.
2. **Is a session needed?** A one-file change or a question about the code → say so and answer or route it (`/tf`, a direct
   answer). A ready plan to be questioned → core-plan-interview. Say in one sentence what you chose.
3. **Checkpoint:** `python3 .claude/hooks/project_record.py wip start "design: <subject>" --slug design-<slug>`.
   Resuming → read the checkpoint and the session artifact first; tell the developer where you are and what is accepted.
4. **Explore:** read the relevant code and records (TL;DR and Handoff of `docs/project/`, `decisions.md`, earlier specs).
   A contradiction with an earlier specification or decision → name it now, as a question.

## 1. The stage map
Propose the stages before the first stage; the developer accepts or edits them. Typical maps (pick, trim, merge):

| Subject | Stages |
|---|---|
| a feature | problem and scope → current state → options → chosen option in detail → edge cases and risks → plan |
| a refactoring | current state and pain → target shape → migration path → safety net (tests) → plan |
| a component / module | responsibilities and boundary → interface → data and states → failure modes → plan |
| a whole system | goals and constraints → context (C4 L1) → containers → key flows → decisions → slices |

Three to six stages. More → split the subject and design one part at a time (map of areas first, as in core-plan-interview).

## 2. One stage
1. **Proposal**, short: what you propose, why, labelled claims (above). Uneven depth: spend words where the risk is.
2. **Options** when a real choice exists: 2–3, each with what it costs, what it buys, when it fails, and one
   recommendation. A decision that is costly to reverse (data model, public API, security boundary, vendor) → ask the
   `architect` subagent for options instead of improvising them; say that you did.
3. **Diagram** only when it explains faster than text — choose the form from `references/diagrams.md` (Mermaid in the
   artifact; GitHub and IDEs render it). Current state and proposal as two diagrams, not one mixed.
4. **Lenses** on stages that decide structure: run the checklist in `references/lenses.md` (Architect, Senior Developer,
   QA, Security, Product Owner, DevOps) and report only the lenses that found something.
5. **Checkpoint** — always AskUserQuestion, the recommended answer first with "(Recommended)":

| Option | What follows |
|---|---|
| Accept (Recommended) | record the decisions (§3), next stage |
| Change | the developer's change; a new version of this stage, then the checkpoint again |
| Show an alternative | a different option or angle for the same stage |
| Go back | to the stage they name; later stages that depended on it become open again — list them |

"Skip this stage" and "go to implementation" come through "Other"; skipping an assumption-heavy stage → write the
assumptions down as **[assumption]** in the artifact. Several independent questions in one stage → one AskUserQuestion
call with several questions; dependent ones wait for the next round.

**On request only** (the developer says "grill me", "find every ambiguity", "refinement"): run core-plan-interview on the
current stage or the whole subject, then come back to the checkpoint with its summary. Not by default — it is the
expensive part of a session.

## 3. The record
Everything the session agrees lives in the project record (core-project-record) — no new mechanism:
- **Session artifact** `docs/project/04-architecture/design-<slug>.md` (template `references/session-template.md`):
  header keys as in core-project-record, `status: proposed` until the developer accepts the whole design.
  Each stage is a section: proposal, chosen option, rejected options with one-line reasons, diagram, open questions.
- **Decisions**: every accepted choice → a row `D-NNN` in `decisions.md` ("accepted by: user"), linked from the stage.
  A decision costly to reverse → also propose an ADR.
- **Versions**: changing an accepted stage after a "Go back" → the artifact goes to `version+1`, the previous file to
  `archive/` (`status: superseded`), so variants stay comparable. A diagram changed within a stage before acceptance
  just changes.
- **Checkpoint** after every checkpoint answer: `project_record.py wip snapshot` with the stage, what is accepted, what is
  next. The session can stop at any point and resume tomorrow from it.
- Then `python3 .claude/hooks/project_record.py check`.

## 4. Build — handoff to /tf
After the last stage, ask: implement now (`/tf` normal), plan only (`/tf --plan`), unattended (`/tf --auto`), or stop
here with the design. Before the handoff, the artifact gets its **Handoff** section (`references/session-template.md`):
- the story in one paragraph, **acceptance criteria** AC-1…n written so that a test can check them, out of scope,
  accepted decisions to respect (D-NNN), parked ideas;
- a split into tasks when the design is bigger than one PR — one `/tf` run per task, in order.

Then: `/tf docs/project/04-architecture/design-<slug>.md [--plan|--auto]` — the loop takes the file as the story and its
acceptance criteria from the Handoff section. One task of a split → pass only that task's part as a story.
The developer runs it, or you do after they chose the option. A small change of 1–2 files → right away, one commit.

**Back from Build:** a `/tf` STOP with the code `question`, `split` or `plan-approval` that touches the design →
resume this session at the affected stage, not a workaround in code. Record the reason in the stage.

## 5. Ending without Build
The developer stops or chooses "design only" → summary in four lines (accepted, assumed, open, parked), the artifact
stays `proposed` (or `accepted` after an explicit yes), `wip pause` or `wip done`.

## Failure modes
- Writing code in Design because the answer "looks obvious" → stop, put it back as a proposal.
- A wall of text per stage → three short parts: proposal, options, the checkpoint question.
- Asking the developer what the code can answer → look it up first.
- Running all six lenses on every stage → only on stages that decide structure; report only the findings.
- Re-deciding an accepted choice because a new option looks nicer → explicit question, or `parked.md`.
- A diagram that mixes current and proposed state → two diagrams.

## Example
"I'd like to design a permissions mechanism in my app. Don't write code yet."
```
Explore: [fact] roles are a string column users.role (src/models/user.ts:14), checks are inline
         if (user.role === 'admin') in 23 places (grep). Diagram: current state (flowchart).
Stage map (accepted): problem → current state → options → option in detail → edge cases → plan.
Options: 1 fixed roles enum · 2 roles with inheritance · 3 policies (ABAC)
         [recommendation] 2 — covers the 3 role levels named in the brief, 3 is costly to reverse
         (asked architect: agrees, warns about cycles).
Checkpoint → "Accept" with a change: inheritance one level deep only → D-004.
Option in detail: diagram (classDiagram Role → parent), [risk] conflicting grants → deny wins (D-005).
Edge cases (QA + Security lenses): a cycle in roles → rejected at save; role removal with users → blocked.
Handoff: AC-1…6, out of scope: per-resource ACL (parked). Developer picks "/tf --plan".
```
More: `references/session-template.md`, `references/diagrams.md`, `references/lenses.md`.

## Checklist
- [ ] subject known (asked, not invented); session needed; checkpoint started
- [ ] stage map accepted; every stage closed by a checkpoint; claims labelled
- [ ] accepted decisions in `decisions.md`; superseded versions in `archive/`; `project_record.py check` passes
- [ ] no code before Build; Handoff with acceptance criteria before `/tf`
