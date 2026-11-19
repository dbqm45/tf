# Research with users (plan, interview, synthesis)

A supplement to intake: when there is too little evidence from domain experts or end users need to be understood.

## The research plan
- The goal starts with a verb that can be checked: describe, assess, identify, compare. "Understand"
  and "explore" you reject — it is unknown when the research will end.
- Name the decision the research is meant to serve. No decision — go back to the requester with a question.
- The research question (what we want to know) is something different from the first question in the interview (what we say to the interviewee).
- Sample size: approx. 5 people per segment in usability tests, 8–12 in discovery interviews (saturation) — counted per segment.
- Recruitment by behaviours ("orders online every week"), not demographics.
- A screener survey: 2–4 questions, disqualifying ones first, no yes/no questions, optionally one open question
  checking whether the person can tell a story.

## The interview script
- An hourglass shape: general → specific → general. The researcher is the student, the interviewee the expert.
- Ask about specific events ("tell me about the last time when…"), not about generalizations and the future.
- Probe ("why?", repeating the interviewee's words), without leading questions; after the opening question wait for the answer,
  do not correct the interviewee.

## Critiquing questions — do not ask about the idea
- Never: "would you use…", "do you like the idea", "would a dashboard be useful", "how much would you pay". Answers
  about the future and compliments are not evidence.
- Always: the last specific time, what was done then, the current workaround, how much it cost (time, rework, risk),
  what has already been tried.
- Before the interview separate in the material the **facts** (logs, tickets, incidents) from the **guesses**; name a polished document
  with weak evidence explicitly.
- Classify every question from the working list: **keep** (specific, about behaviour) / **rewrite** (a good intention,
  a leading question) / **remove** (a compliment, a hypothesis, pricing an imagined product, accepting a solution).
  When rewriting: "Instead of: … / Ask: … / What signal it will reveal: …".
- A 20–30 min script (8–12 questions): context and frequency → the latest story → the current workaround → the cost of the pain →
  existing alternatives → what would prompt a change → a request for a follow-up or a look at anonymized artifacts.

## Survey (a broader signal)
6–10 questions; one screening question (whether the respondent has this workflow at all); frequency and effort as
ranges; 1–2 open questions about a recent example; no ranking of solutions nobody has seen.

## Decision criteria (written down before the research)
You set the thresholds with the human **before** the interviews, e.g.:
- **act** — at least 3 of 5 interviewees describe the same recent workaround without prompting; at least 40%
  of the respondents from the target group have the problem weekly or more often; a measurable cost (time, money, rework);
- **narrow the scope** — a mixed signal;
- **do not build yet** — a weak signal;
- **an existing tool or process first** — the current solution is enough.

## Synthesis
1. Familiarization with the material (in batches), then a codebook — every code has a sample quote (the quote bank: `corpus.md`).
2. **A theme requires at least 2 interviews**; a pattern from one interview is an observation.
3. You show contradictions and counter-evidence on top (`contradictions.md`), you do not hide them.
4. A persona (if needed) has a defining quote and 3–5 goals.
5. Priorities by purpose: weight × frequency (problems), importance vs satisfaction (needs), impact/effort (ideas),
   an opportunity solution tree (product direction).

## Personal data
Recordings and transcripts are personal data: the interviewee's consent, minimization, anonymization before passing them on,
no sending to external services without a legal basis and the organization's consent.

## Source of inspiration
The 10xDevs course, ed. 3 (2026), module 5, lesson 1 (critiquing questions in the spirit of "The Mom Test" by R. Fitzpatrick, 2013) —
training material (accessed 2026-10-09); the decision thresholds are an example, not a norm.
[user-research-skill](https://github.com/cookiy-ai/user-research-skill) — the "plan" and "synthesis" routes (the principles of the goal,
sample size, recruitment, the script and synthesis), described in our own words; without the parts of the Cookiy platform (a paid
external service).
