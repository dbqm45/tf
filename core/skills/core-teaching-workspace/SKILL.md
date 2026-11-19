---
name: core-teaching-workspace
description: Use on the human's command to learn a topic over many sessions in a workshop directory — lessons, cheat sheets, progress.
metadata:
  review: "2027-10-10"
  catalog: "Use only on the human's command (`/core-teaching-workspace`) — learning one topic over many sessions in a workshop directory (mission, sources, HTML lessons, cheat sheets, progress records), e.g. onboarding into a new stack or the project's code. Not for a one-off explanation or for researching sources without learning (core-source-research)."
argument-hint: "[topic] | next lesson"
disable-model-invocation: true
---

# Learning workshop

Learning one topic over many sessions that build on each other. Continuity comes from the **directory**, not the
conversation history: a new session in the same directory + "next lesson" = the course continues.

## Where
By default `docs/learning/<temat>/` in the project; if the human does not want to commit it — a path in
`.git/info/exclude` or a separate directory outside the repo. Before writing, check that the files go where they
should (not into `~/.claude`).

| File | Contents |
|---|---|
| `MISSION.md` | **why** the human is learning — the first file, it steers every lesson |
| `RESOURCES.md` | vetted sources: **Knowledge** (documentation, books) and **Wisdom** (communities), each with one sentence on "what for"; a `Luki` section |
| `lessons/NNNN-nazwa.html` | one lesson = one session = one new skill |
| `reference/*.html` | cheat sheets to come back to: syntax, algorithms, a glossary |
| `learning-records/NNNN-nazwa.md` | ADR-style progress records |
| `assets/` | shared components: stylesheet, quiz, simulator |
| `NOTES.md` | the learner's preferences |

## Procedure
**First session (empty directory):** do not start with a lesson. First talk about the mission until `MISSION.md` has:
a concrete goal ("onboard into the billing module and do reviews within 3 weeks", not "learn X"), what they will be
able to do (observable), constraints, what is out of scope. Also ask directly what they already know — otherwise the
level of the first lesson is guesswork. Then sources, then lesson 1.
**Later sessions:** read the mission, the progress records and `assets/`; pick the next step in the **zone of
proximal development** (hard but reachable); write the lesson.

## Lesson
- Short (one sitting), tied to the mission, gives one concrete skill.
- **Do not trust your own memory**: every claim links to a source from `RESOURCES.md`; the lesson recommends one main
  source to read on one's own. A lesson without footnotes = a sign of fabrication. For project code the source is
  the code itself (file:line).
- Knowledge first (here difficulty gets in the way), then practice with immediate feedback (here difficulty helps):
  **retrieval practice**, **spacing**, **interleaving** related topics. The goal is lasting retention, not momentary
  fluency that gives an illusion of mastery.
- Quiz: answers of the same length, order shuffled **at display time** (models tend to put the correct answer first).
- Build from `assets/` (a shared stylesheet from the first lesson); a new reusable element goes to `assets/`. No CDN
  libraries without a pinned version (the documentation skill from pack-docs: docs-tech-writing,
  diagrams-and-presentations.md).
- Links to previous lessons and cheat sheets; a reminder that the learner can ask the agent follow-up questions.

## Progress record (`learning-records/`)
One to three sentences: what is already known and why it changes the next lessons. You write one when: the learner
**showed** understanding (a task, an answer — "it was covered" is not enough), declared prior knowledge (with depth),
a misconception was corrected, the mission changed (after agreement, with an update to `MISSION.md`). An old record
is marked "superseded by NNNN", not deleted.

## Diagnosis, reviews and the end of the course
- **Before lesson 1:** a short diagnosis (5–8 questions from easy to hard, in the style of core-plan-interview), the
  result as the first record in `learning-records/`. Without it the lesson level is guesswork, and lessons assume
  unexplained jargon.
- **The quiz is a gate:** the next lesson only after passing the previous lesson's exercises; after a failure — a
  short recap with a different example, not the same lesson.
- **Reviews:** the skill has no calendar. Keep a "to review" list with dates in `NOTES.md` (e.g. after 1, 3, 7 and 14
  days); at the start of a session first the overdue reviews (retrieval practice), then the new lesson.
- **Build, then take apart** (when the agent delivered a solution in an area new to the learner): explanation mode,
  one concept at a time — "why this way", "what breaks when I change X", "when is this a bad choice"; after each step a
  checking question, moving on only after a correct answer. The topic is closed when the learner, without hints,
  answers one question about the logic, a trade-off or a failure symptom. Approving a change the learner cannot
  defend is a sign that no learning happened. In an Anthropic study (2026, 52 programmers) the group with AI did
  worse on a comprehension test, and the results held for those who, after generating code, asked how it works or
  asked about the concepts.
- **Flashcards after a valuable session:** 3–5 question–answer pairs (answer 2–3 sentences, questions about
  application, not definitions) added to the "to review" list in `NOTES.md`.
- **A default mode instead of discipline:** in Claude Code the `Explanatory` output style ("Insight" blocks with the
  rationale for decisions) or `Learning` (it also leaves the learner fragments with a design decision to write,
  marked `TODO(human)`) — switch with `/output-style <styl>` or `/config`.
- **When to stop adding lessons:** the mission is achieved or further lessons give no new skill from the mission →
  propose moving to practice (a task in the project, a review with a mentor) and record it in `learning-records/`.
- Shallow or too short lessons → first a stronger model or higher reasoning effort, only then a change of
  instructions. Domains with precise notation (sequences, commands, formulas) — check them in the source especially
  carefully.

## Questions that need experience
Try to answer, but point to a community (a forum, a group, a team channel, a person on the team) where it can be
checked in practice — unless the learner wrote in `NOTES.md` that they do not want that.

## Source
Anthropic, "How AI assistance impacts the formation of coding skills" (anthropic.com/research, 2026-01-29) and Claude
Code "Output styles" (code.claude.com/docs/en/output-styles), accessed 2026-10-10; the 10xDevs course, ed. 3 (2026),
lesson 1.3 (learning with AI) — training material (accessed 2026-10-09).
[mattpocock/skills](https://github.com/mattpocock/skills) (MIT), the `teach` skill (MISSION, RESOURCES,
LEARNING-RECORD formats); description: [aihero.dev](https://www.aihero.dev/skills-teach). Described in our own words.
