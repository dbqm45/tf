---
artifact: design
change: {CHG}
phase: design
status: proposed
version: 1
---

# Design of change {CHG}

Figma file: <link to the file> · mode: matching the designer's frames (a frame draft by the agent only at a human's request)

## Frames per requirement and state

Format from the pdi contract (`conventions.design`): a state from the list `idle`, `loading`, `processing`, `success`,
`validation_error`, `server_error`, `timeout`, `retry`, `empty`, `confirmation`, `session_expired`, `network_failure`,
`permission_denied`; the frame — a link with `node-id`, `missing` (with a question) or `n/a` (with a reason). Every story:
at least `idle`, `success` and an error state. Check: `design_check.py check {CHG}`.

| Requirement | Journey | State | Frame | Notes |
|---|---|---|---|---|
| US-? | <journey> | idle | missing | <what is missing — a question to the designer> |

## Flows

## Gate questions
