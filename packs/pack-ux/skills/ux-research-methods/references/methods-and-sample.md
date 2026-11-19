# Choice of method and sample size

## Table of methods
| Method | Answers | When | Note |
|---|---|---|---|
| In-depth interview | why, how they work today, motivations | the start, understanding the context | ask about concrete past events, not opinions and future intentions |
| Moderated test | where and why they make mistakes | a prototype or the product | realistic tasks, without words from the interface |
| Unmoderated test | how many will complete, how much time | a finished flow, more people | no follow-up questions; tasks must be unambiguous |
| Survey | how many people, how often, how they rate | when you already know the questions and the answers | badly built questions give confident but wrong numbers; a survey does not explain "why" |
| Diary study | behaviours over time and in context | a process lasting days or weeks | cost: participants' motivation, dropout grows; short entries, reminders |
| Competitive benchmark | how we compare | before a rebuild, periodically | the same tasks and measures for everyone; an expert review only complements tests |
| Inclusive research | barriers of accessibility and low skills | always, from early stages | people with a screen reader, voice control, low digital skills |

Analytics data says **what** happens; a study says **why**. Start from the data if it exists.

## Sample size — heuristics
- **Qualitative test: about 5 people per segment.** Nielsen and Landauer: the share of problems found by n people
  ≈ 1−(1−L)^n, with L≈31% five people give about 85%. Caveats: L differs between products and tasks;
  the group must be homogeneous (further segments = further samples); the result is "most of the frequent problems", not
  all of them; the rule is about **rounds with fixes**, not one big study.
- **A test with measurement** (time, completion rate): more people, several dozen (NN/g gives about 40 [unverified]);
  with a small sample give a confidence interval or do not give percentages, only counts ("6 of 8").
- **Interviews:** thematic saturation — you stop when the next 2–3 sessions bring no new threads. 5–8 per segment
  is a starting point [assumption], not a norm.
- **Card sorting and tree test:** `.claude/skills/ux-information-architecture/SKILL.md`.
- **Survey:** the number follows from the required precision and the population size — compute it (data-analysis); do not pick it "by eye".
- A purposive sample is not representative: do not generalize percentages from 8 interviews to all users.

## UX benchmark
A fixed set of tasks and measures (completion, time, errors, SEQ after the task, SUS at the end), similar participants, repeated
every release or quarter. Changing the task set invalidates the comparison. SUS and SEQ are described by ux-feature-design.
