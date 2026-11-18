# Figma frames in the change design (Figma MCP)

The change design is a contract: every requirement with an interface has a frame for every state its flow contains.
This file describes how to record it and check it through the Figma MCP server. Screen content: ux-content-design; accessibility
of frames: ux-accessibility; tokens and components: ux-design-systems.

## Two modes of work
- **A — matching (default).** The designer makes the frames. The agent reads the file, matches frames to requirements and states,
  fills the table and names the gaps. It does not change the designer's frames.
- **B — a draft by the agent (only at a human's request).** The agent creates frames per journey and state from the design system's components
  and tokens, on a separate page marked as a draft. The designer corrects; only frames accepted by the designer
  go to review. An agent's draft is easy to mistake for a finished design — that is why it is not the default.

## Procedure (mode A)
1. **File and session.** From the link `figma.com/design/<fileKey>/…` take the `fileKey`; create a Figma server session for the file
   (a server requirement: a session before other file tools).
2. **Frame inventory.** `get_metadata` (pages and top-level frames: names, `node-id`); `get_screenshot` for a frame
   whose name does not say what it shows. Do not fetch the whole file with details — the frame level is enough.
3. **Required states.** From the requirements and acceptance criteria list the flows (journeys) and states: always `idle`,
   `success` and at least one error state; then what follows from the content — `empty` (a list), `loading`/`processing`
   (an operation in progress), `validation_error` (a form), `network_failure`, `permission_denied`, `session_expired`,
   `confirmation`, `timeout`, `retry`. The list of states is fixed (the pdi contract, `conventions.design.states`).
4. **Matching.** A frame goes into a row only when it shows this state of this journey (name, text, screenshot). A link
   with the `node-id` of a specific frame, not to the whole file. A frame showing several states may appear in several rows.
5. **Gaps.** A state without a frame: `missing` and in the notes a question to the designer ("does a partial error have a separate screen?").
   A state the flow does not have: `n/a` and a reason. You do not draw frames in mode A.
6. **Record in the change's `design.md`**: the table below, above it a link to the file and the mode of work; questions to the designer also
   in the gate questions section.
7. **Check before the review:** in mode-pdi `design_check.py check CHG-n` (a script of the pdi-decisions skill,
   mode-pdi) — format, links, minimum states per story; gaps go as questions to the
   `design-review` gate.

## Table (format from the pdi contract, `conventions.design`)

| Requirement | Journey | State | Frame | Notes |
|---|---|---|---|---|
| US-3 | choosing chargers | idle | https://www.figma.com/design/AbC123xyz/Taryfy?node-id=12-34 | |
| US-3/AC-3 | applying the tariff | server_error | missing | partial error (3 of 200 offline) — a question to the designer |
| US-3/AC-3 | applying the tariff | session_expired | n/a | the operation runs in the background |

- Requirement: `US-3` or `US-3/AC-2` (a Jira key too). Minimum states are counted per story.
- The Polish header (`Wymaganie | Ścieżka | Stan | Ramka | Uwagi`) with `brak` and `nie dotyczy` is also valid.

## Without Figma
The table stays: instead of a link `missing` and a description of the state in the notes (or a text wireframe under the table). The phase works,
and the review sees the gaps as questions.

## Example
**Input:** a file with 6 frames, requirement US-3 (AC-1 choice, AC-2 applying with progress, AC-3 partial errors).
**Result:** 6 rows: `idle`, `empty`, `processing`, `success` with links; `server_error` — `missing` with a question
about the partial error screen; `session_expired` — `n/a` (operation in the background). The review gets one question.
