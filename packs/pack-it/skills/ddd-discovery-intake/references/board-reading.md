# Reading an Event Storming board from a photo or an export

## Rules
- Read the board as **a numbered flow in each lane** (swimlane), not as bags of sticky notes by colour.
  Add the note type in brackets: `7. Reservation confirmed (event)`.
- Record pivotal events and hot spots as **indexes to steps** (`pivotal: Customer/7, Planner/3`), without repeating the content.
- Mark uncertainty explicitly: `[illegible]`, `[partial: "Reserv…"]`, `[order uncertain]`. These places are not evidence
  until the human confirms them.
- Do not "correct" the board: typos and odd phrasings stay — that is the participants' language.

## Fixed sections of the result (`02-domain/boards/<name>.es.md`)
Legend (colours → types) · Lanes · Flow (per lane, numbered) · Pivotal events (indexes) · Hot spots (indexes) ·
Glossary (terms from the notes) · Observations from the layout (e.g. "the Finance lane is empty after step 5").
The header contains **the hash of the image file** (`sha256sum` — computed by an agent with a shell, e.g. the orchestrator) and the version of the reading instructions — a change of the image invalidates only this description.

## Quality gate
Show the human: the number of notes per type and lane, **3 random notes from different lanes** to compare with the photo, the number of
illegible ones. When more than every 10th note is illegible — ask for better input (an export from the tool, a photo per lane)
instead of repeating the reading.
