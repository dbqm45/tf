# The process of writing technical documentation

> **Contents:** Stages · Gathering information · The documentation project (plan) — what it should contain · Verification and review · Proofreading — a pass separate from the content review · Taking over documentation written by someone else · Summary (post-mortem) after the work ends

An expansion of the docs-tech-writing hub. In projects with a `docs/project/` record, the plan, statuses and handoffs are run by
core-project-record — here only the process of writing the document itself.

## Stages

1. gathering information about the described system,
2. creating the project/structure of the documentation,
3. writing the content,
4. verification,
5. fixes and filling in the gaps.

Stages 4 and 5 usually repeat several times until all defects are removed — this is not a linear,
one-off pass.

Do not write the document linearly from the first to the last paragraph. Better: first lay out the full structure
(chapters → subchapters → sub-subchapters, and so on), and then fill the successive nodes of this
structure with content. Advantages: (1) when you hit a fragment you cannot write at the moment (e.g. you are waiting for
a consultation with a developer), you mark it and move to another node instead of blocking the whole work; (2)
the state of the work is visible at a glance — what is ready, what needs filling in, what is not even started; (3) you avoid
the situation in which the whole content is already written, but it turns out that the layout should be different.

## Gathering information

Three main sources, usually combined:
- reading the already existing fragments of documentation,
- working with the program itself and analysing the source code,
- consultations (usually with the developers who built the system).

When you run/use the system for the first time as a "user" — **write down everything that caused
difficulty**. It is very likely that a real user will run into the same difficulties — it is a natural
signal of which places to describe with particular care.

Always work on the **current development code**, not on an old version or a cut-down demo version. If
the system keeps changing while you write the documentation, ask the developers for short, regular (e.g.
daily) information about changes — these need not be detailed reports, one line like "I changed
such-and-such class" is enough; you yourself judge whether a given change requires updating the document.

### Consulting developers — how to do it effectively

- Consult first the person **lowest in the hierarchy** who may know the answer (developer → team
  lead → project manager), and go higher only when the lower level cannot answer. Reason: the time of people higher
  in the hierarchy is more valuable to the organization.
- **Prepare before the conversation** — find out on your own as much as you can, so that you ask precise
  questions and understand the answers better. Prepare a concrete list of questions and send it to the person
  in advance, so that they can prepare.
- When talking to someone who has little time — use a recording instead of notes taken during the conversation (but
  **announce it right at the start of the conversation**, never halfway through, and never without an announcement). Notes
  taken "as you go" take the other person's time with unproductive pauses; a recording keeps the natural
  pace of the conversation.
- If a person never has time — ask them **to propose a date themselves**. If that does not help after a few
  attempts, look for another person with this knowledge; if that is impossible, report the problem to your manager.
- At the end of a consultation always ask: **"is there anything else I should know?"** — this question
  regularly brings out information you would not ask about yourself, because it would not occur to you.
- If the time for the meeting is running out and the topic is not closed — do not drag it out, set another
  date.
- **Add the information from the consultation to the documentation right after it ends.** Putting this off risks
  problems deciphering your own shorthand notes later.

## The documentation project (plan) — what it should contain

- the title of the documentation,
- the type of documentation (e.g. user manual, API documentation, runbook),
- the expected completion date,
- the author(s),
- a short description of the scope — what the documentation will contain,
- an estimated number of pages (best by comparison with existing, similar documents),
- the list of main chapters,
- the milestone dates.

### Milestones

Two are usually enough:
- **the first** — when about 2/3–3/4 of the text is written, and the target places for figures/screenshots are
  already marked (they need not be filled).
- **the second** — when practically the whole text and (almost) all illustrations are already in the document, and the defects from
  the verification after the first milestone are fixed.

A milestone is the moment when the documentation goes to verification/review — not the end of the work.

### A marker for unfinished places

Set **one consistent symbol** (e.g. `TBD`) for places that need filling in, instead of ad hoc descriptions
("to be filled in", "check later" etc.). The reason is purely practical: thanks to one fixed string
of characters, all unfinished places in the whole document can be found with one search.

## Verification and review

Verification covers:
- reading carefully in search of errors,
- checking that the screenshots match what is actually visible at the described moment,
- **performing the procedures/instructions from the documentation** and checking that they really give the described result
  (do not assume the description is correct — test it like code),
- passing it to review and collecting comments.

It is also useful to ask someone **without deep knowledge of the system** to read it and check that
they understood everything — the author of the documentation may miss something "obvious to them", and a reviewer who knows
the system well may not notice this gap, because they do not need this explanation themselves.

### Three methods of collecting reviewers' opinions

1. **A joint meeting** (the most effective with a small number of reviewers) — everyone together
   goes through the chapters/paragraphs, comments raised aloud are considered at once by the whole team.
   Risk: the conversation easily drifts off topic, especially when there are more participants — with a larger group
   it is worth appointing a **moderator** (a person not taking part in the review) who only keeps the meeting on
   topic and does not speak on the substance.
2. **Send out and consolidate** — the documentation goes to all reviewers in parallel, the comments come back
   separately, the author consolidates them. It needs attention with **contradictory suggestions**: inform both authors
   of the contradictory comments about the situation and ask them to reconsider the other side's position; if nobody gives way
   and the documentation author has no opinion of their own — lean towards the proposal of the person higher in the hierarchy, but
   if the author personally prefers the version of the person lower in the hierarchy — consult this with your manager
   before deciding.
3. **Sequential passing** — the documentation + the comments of each successive reviewer go to
   the next one, so everyone (except the first) also sees the comments of their predecessors. The most thorough, but the most
   time-consuming method.

When the document goes to a **repeated** review — always mark what changed since the previous version, so that
the reviewers do not have to read everything again.

After the documentation is handed over to production, it is "frozen" — further changes go to an erratum (attached
separately), not back into the frozen document; the actual fixes go into the next version.

**Collect comments from real readers** after delivering each finished part to them, not only from
internal reviewers — it is a source of both concrete fixes and signals that the adopted
standards need to change (e.g. a reader asks for a larger font because their eyesight is weak). Especially important after
the first delivered part, for the same reasons as internal reviews.

After deployment it is also worth monitoring **what problems readers bring to support** — if
they concern something described in the documentation, it is a signal that the given fragment has an error, is unclear or
is not detailed enough.

## Proofreading — a pass separate from the content review

- **Never combine** looking for content errors with looking for typos/grammar/
  punctuation errors in one pass — these are different kinds of attention, and done together they catch both types
  of errors worse. First polish the content to the end, then do a separate proofreading pass.
- An automatic spellchecker alone is not enough — it will not detect an error that happened to turn one
  correct word into another correct word.
- To catch typos: **print the text** (or move it to a different medium/format than the one in
  which it was written) — the human eye catches errors more easily on paper/in a new context than in the same editor
  window in which the text was created.
- One technique: read paragraphs **from the end of the chapter to the start** — this forces focus on the spelling
  word by word instead of on the meaning of the whole (when reading from the start the brain "fills in" the meaning and it is easier
  to miss a typo).
- Pay particular attention during proofreading to: spelling/grammar/punctuation, first and last names,
  initials, titles, company names and other proper names, numbers, dates.
- Polish text: give the proofreading to the skills txt-polish-correctness (correctness) and txt-polish-style (editing) or
  to the persona Stefan (editor).

### Checklist before sending to reviewers

Before the author passes the document to review, they should answer themselves:
- is the documentation extensive enough for the current milestone?
- is the information properly organized/laid out?
- is the technical information accurate?
- are the concepts the reader may not know explained?
- is the language of the documentation consistent?
- are the examples well chosen and placed in the right spots?
- are the page numbers in the table of contents/index correct?

## Taking over documentation written by someone else

Before adding new chapters:
- read what is already written,
- if possible, talk to the previous author — what they did not manage to write, what they intended to change,
- sit down with the developers, verify that there are no errors in the documentation and find out what is new
  in the system since the existing content was written,
- look at/test the described system yourself and judge how well it matches the current content of the document,
- find out whether readers previously reported comments or change requests.

## Summary (post-mortem) after the work ends

It is worth doing always, and in team work — as a meeting. Questions to ask:
- how much time did writing this documentation take, and how much should it have taken?
- what problems got in the way or slowed the work down?
- what (e.g. which tool) was useful and helpful?
- which people were obliging and willing to help?
- how much time was spent just waiting for information?
- was the communication between the people writing the documentation good?
- was the communication with the people giving consultations good?
- what can be done to write the next documentation better or faster?

The goal is not ritual — it is a real mechanism for improving the process next time, analogous to a retro after
a sprint.
