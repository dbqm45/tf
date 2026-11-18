# Heuristic evaluation, expert review and usability tests

## Nielsen's 10 heuristics (for evaluation and for justifying comments)
1. **Visibility of system status** — the user knows what is happening (progress, saved, how much is left).
2. **Match with the user's world** — their words and order, not the language of the database.
3. **User control and freedom** — an emergency exit: cancel, undo, go back without losing data.
4. **Consistency and standards** — the same thing looks and works the same way; platform conventions.
5. **Error prevention** — constraints, good defaults, confirmation before the irreversible.
6. **Recognition rather than recall** — options visible, context next to the field, recently used.
7. **Flexibility and efficiency** — shortcuts for the proficient, without making it harder for beginners.
8. **Aesthetics and minimalism** — every piece of information competes for attention; remove the unneeded.
9. **Recognizing, diagnosing and recovering from errors** — a message in plain language: what happened and what to do.
10. **Help and documentation** — in the context of the task, short, with steps.

## Heuristic and expert review — procedure
1. Scope: flows and screens, for whom, which tasks.
2. 3–5 evaluators independently (one finds less than half of the problems), preferably people who did not design
   the screen. The agent can be one of the evaluators, not the only one.
3. Every problem: the location (screen, element), the violated heuristic or principle, a description, **severity 0–4**
   (0 not a problem, 1 cosmetic, 2 minor, 3 major — fix before the release, 4 catastrophe — blocks the task),
   a recommendation. Also strengths — so as not to break them.
4. Merge the results, agree the severities, sort. An expert review extends the heuristics with guidelines, cognitive psychology
   and the evaluator's experience; it does not replace tests with users.

## Usability test
- **Participants**: real or representative users; about 5 per segment in a qualitative test (most
  frequent problems), more for quantitative measurement (about 20+ and clearly defined measures).
- **Tasks** realistic, with a goal, without hinting with words from the interface: "Return the shoes that came in the wrong
  size" instead of "Click Returns". Order from easy ones; each with a success criterion.
- **Thinking aloud**, a neutral moderator (does not help, does not explain, asks "what did you expect?").
- **Forms**: moderated (on site or remote) — a deeper "why"; unmoderated remote — faster and cheaper,
  without follow-up questions.
- **Measures**: task completion, time, errors, post-task difficulty rating (SEQ, 1–7), at the end SUS (10 questions, a score
  of 0–100; the average from many studies about 68).
- **Report**: the most important problems with severity, frequency (how many participants), a quote and a recording or screenshot, recommendations;
  what worked well. Recordings are personal data — consent and retention (ddd-discovery-intake).

## UX benchmark
The same tasks and measures repeated every release or quarter (and at competitors, if possible) show whether
changes improve the experience. Condition: a fixed set of tasks, similar participants, a sufficient sample.

## Sources
- J. Nielsen, *10 Usability Heuristics for User Interface Design* (NN/g, 1994, updated 2020); Nielsen's severity scale
- NN/g: [UX Expert Reviews](https://www.nngroup.com/articles/ux-expert-reviews/),
  [Usability Testing 101](https://www.nngroup.com/articles/usability-testing-101/),
  [Benchmarking UX](https://www.nngroup.com/articles/benchmarking-ux/); J. Brooke — SUS (1996)
Described in our own words.
