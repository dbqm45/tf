---
name: core-teaching-workspace
description: Use when the human runs /core-teaching-workspace to study one topic over many sessions — a workshop directory with mission, sources, lessons, quizzes, progress.
argument-hint: "[topic] | next lesson"
disable-model-invocation: true
metadata:
  review: "2027-11-20"
  catalog: "Use only on the human's command /core-teaching-workspace [topic | next lesson] — a multi-session self-study course on one topic (a new stack, a library, the project's own code) kept in a workshop directory, so a new session continues from files, not chat history: mission, vetted sources, lessons and reference sheets, quizzes as gates, spaced review, progress records, explanation mode for code the agent wrote. Not for a one-off explanation (answer directly), for finding and vetting sources without learning (core-source-research) or for a planning interview (core-plan-interview)."
---

# Teaching workspace — a course that lives in files

Run only on the human's command. Continuity lives in the workshop directory: a new session with "next lesson" reads the
files and carries on. Nothing depends on remembering the chat.

## Workshop directory
Default `docs/learning/<topic>/`:
| File | Holds |
|---|---|
| MISSION.md | why the learner studies this: goal, observable abilities, constraints, out of scope — steers every lesson |
| SOURCES.md | vetted sources in two groups: references (docs, books, specs) and communities and practitioners; one line each on what it is good for; a "gaps" section |
| `lessons/NN-<slug>.html` | one lesson per sitting |
| `sheets/<slug>.html` | quick-reference sheets |
| `records/NNNN-<slug>.md` | progress records, numbered |
| `assets/` | shared stylesheet, quiz and simulator components reused by every lesson |
| NOTES.md | learner preferences, the review list with dates, flashcards |

Not to be committed → put the path in `.git/info/exclude` or use a directory outside the repository. Never write into `~/.claude`.

## Every session starts the same way
1. Read MISSION.md, the records and NOTES.md; look at `assets/`.
2. **Overdue reviews first** (from the review list), as retrieval questions — then new material.
3. Choose the next step from the mission and the records: the next thing the learner can just reach with help.

## First session (empty directory) — no lesson yet
1. **Mission.** Ask until it holds: a concrete goal tied to an outcome and a time frame ("review pull requests in the
   billing module within 3 weeks", not "learn Rust"), what the learner should be able to do, constraints (time per
   week, tools), what is out of scope. Write MISSION.md.
2. **What they already know.** Without it the level is guesswork. Run a short diagnostic: about 5–8 questions from easy
   to hard, in the plan-interview style (core-plan-interview: numbered, answer by number). Its result is record 0001.
3. **Sources.** Collect and vet them into SOURCES.md (core-source-research for the vetting method). For the
   project's own code the source is the code itself (`file:line`).
4. Only then lesson 1 — usually in the next turn.

## Lesson design
- **One sitting, one concrete skill**, tied to the mission.
- **Knowledge, then practice with immediate feedback.** Use retrieval (recall before re-reading), spacing (come back
  after days), interleaving (mix related problems). Aim for durable retention, not the feeling of fluency right after
  reading — effortful recall works better than re-reading (Bjork's "desirable difficulties").
- **Every claim links to a vetted source**; no model memory as a source. Each lesson recommends one main source to read
  alone. A lesson without citations is a warning sign — flag such a claim as unverifiable and either source it or cut it.
  Commands, formulas and step sequences: check them against the source character by character.
- Questions that need hands-on experience: answer as well as you can and point to a community or colleague who can
  confirm it (unless the learner opted out of that).
- **Quizzes:** options of similar length; correct answers not always in one position — **shuffle the order when the
  quiz renders** (models tend to put the right answer first).
- Build on `assets/`; a new reusable piece goes there. External libraries only with pinned versions (CDN pinning:
  docs-tech-writing, pack-docs, `diagrams-and-presentations.md`).
- Link back to earlier lessons and sheets; remind the learner that follow-up questions are welcome.

## Gates and review
- **The quiz is a gate.** The next lesson only after the exercises pass. Failed → a short recap with a different
  example (not the same text again), then the quiz again.
- No calendar integration: keep a "to review" list in NOTES.md with dates (e.g. after 1, 3, 7 and 14 days).
- After a valuable session add 3–5 flashcards: application questions, not definitions; answers of 2–3 sentences.

## Progress records
- 1–3 sentences: what the learner now knows and how that changes the next lessons.
- Write one when the learner **showed** understanding (solved a task, answered unaided — not "it was covered"),
  declared prior knowledge (with its depth), had a misconception corrected, or the mission changed (agree it first,
  then update MISSION.md).
- Records are never deleted: a newer record marks an older one as superseded.

## Understanding code the agent wrote
When you have just built something in an area the learner does not know (a caching layer, an outbox):
- switch to explanation mode, **one concept at a time** — why it is built this way, what breaks if X changes, when it
  would be the wrong choice;
- a check question after each concept; move on only after a correct answer;
- the topic is closed when the learner answers one question about the logic, a trade-off or a failure symptom
  without help. Approving a change you cannot defend means nothing was learned.
- Why it matters: an Anthropic study found that developers who relied on AI help scored lower on a comprehension
  quiz, while those who asked how the generated code works kept their understanding (2026-01-29).
- A lighter, always-on alternative: Claude Code output styles `Explanatory` (adds insight notes) or `Learning`
  (leaves `TODO(human)` parts for the learner), chosen via `/output-style` or `/config`.

## Ending the course
- Stop adding lessons when the mission is met or further lessons add nothing towards it. Propose practice instead —
  a real task in the project, a review by a mentor — and record that decision.
- Lessons come out thin or short → first try a stronger model or higher effort, then change the instructions.

## Example
`/core-teaching-workspace Rust ownership` in an empty repository:
- Turn 1: no lesson file. "What should you be able to do, and by when?" → "Review the parser crate's PRs in a month."
  Abilities: explain a borrow-checker error, choose `&`, `&mut` or an owned value. Out of scope: async, unsafe.
  MISSION.md written; 6 diagnostic questions asked.
- Answers show moves are understood, lifetimes are not → record 0001.
- SOURCES.md: The Rust Book ch. 4 and 10, the Rustonomicon (gaps only), the users.rust-lang.org forum.
- Next session ("next lesson"): reads the files, starts with lesson 1 "Borrowing rules in the parser's tokenizer",
  ends with a 4-question quiz (shuffled), review dates added to NOTES.md.

## Checklist
- [ ] started on the command only; files read before anything new
- [ ] mission and prior knowledge before lesson 1
- [ ] every claim sourced; one main source per lesson
- [ ] quiz as a gate, shuffled options; overdue reviews first
- [ ] records written on evidence, never deleted

## Sources
- Anthropic, "How AI assistance impacts the formation of coding skills", anthropic.com/research (2026-01-29).
- Claude Code docs, "Output styles", https://code.claude.com/docs/en/output-styles (accessed 2026-11-20).
- Bjork, R. A. & Bjork, E. L., work on desirable difficulties in learning; Vygotsky's zone of proximal development —
  general learning-science background.
