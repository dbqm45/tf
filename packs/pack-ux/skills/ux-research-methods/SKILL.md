---
name: ux-research-methods
description: Use for research with users (UX Research, ResearchOps) — research question, choice of method, plan, recruitment, GDPR consent, synthesis, repository.
metadata:
  review: "2027-10-17"
  catalog: "Use when you need to plan and run a study with users — from the research question through the choice of method (interviews, moderated and unmoderated usability tests, surveys, diary studies, competitive benchmark, inclusive research), the study plan, recruitment and screener, participant consent and GDPR, running sessions, sample size heuristics with caveats, synthesis (affinity mapping, atomic nuggets, AI-assisted synthesis checked by a human), the research repository and ResearchOps (panel, backlog, playbooks) up to turning findings into decisions; the artifacts research-plan.md and research-report.md. Not for deciding what to build, opportunity trees, JTBD and assumption tests (proc-product-discovery), heuristics and usability tests during design (ux-feature-design), UAT (qa-exploratory-manual), statistics (data-analysis), DPIA (arch-privacy-compliance) or information architecture (ux-information-architecture)."
  keywords: "badania użytkowników, UX research, wywiady z użytkownikami, wywiad pogłębiony, badanie jakościowe, test użyteczności, ankieta, diary study, badanie dzienniczkowe, rekrutacja uczestników, screener, panel badawczy, zgoda uczestnika, nagrywanie sesji, ilu uczestników, ile osób, synteza badań, mapowanie powinowactwa, insighty, repozytorium badań, ResearchOps, raport z badań, pytanie badawcze, plan badania, moderowanie sesji, user research, user interviews, in-depth interview, qualitative study, usability test, survey, participant recruitment, research panel, participant consent, session recording, how many participants, research synthesis, affinity mapping, insights, research repository, research report, research question, study plan, moderating sessions"
---

# Research with users — from the question to the decision

A study exists to change a specific decision. Without a decision it is meant to set, you are left with a collection of quotes.
The skill leads from the question to the report; **what** to build (opportunity tree, JTBD, assumption tests) is settled by
**proc-product-discovery**, and heuristics and quick tests during design by **ux-feature-design**
(`.claude/skills/ux-feature-design/references/heuristics-and-tests.md`). This skill starts where a real study is needed.

## Procedure
1. **Decision and question.** Write down: which decision the result will change, who will make it and by when. From it derive 1–3
   research questions (not questions for the participants). Bad: "Do people like the new onboarding?". Good: "Where in the first
   week do users abandon the setup and for what reason?". If you already know what they do (data) — ask why.
2. **Method** — the table in `references/methods-and-sample.md`. The shortcut rule: *why and how* → qualitative (interview,
   moderated test, diary); *how many and how often* → quantitative (survey, analytics, unmoderated test on a sample);
   *context over time* → a diary or observation; *how we compare with others* → a benchmark. Two methods
   of a different nature (qualitative + quantitative) give a stronger conclusion than one.
3. **Study plan** `docs/project/01-discovery/research-plan.md` by `references/plan-and-report-template.md`: decision,
   questions, method with a justification, participants and their number, schedule, materials, risks, who observes, how
   data is recorded and retained. Show the plan to the stakeholders **before** recruitment — agreeing on the questions costs less than arguing about the results.
4. **Participants and screener.** The criteria follow from the question (behaviour, not demographics: "issued invoices in the last
   3 months"). Screener: 5–10 questions, it does not reveal the criteria, behaviour questions with answers to choose from
   and a "none of the above" option, a question excluding employees of the company and of competitors. Include people with accessibility
   needs and with low digital skills — they are part of the sample, not an extra (`references/recruitment-consent-gdpr.md`).
   Recruit with a reserve for no-shows (usually +20–30% [assumption — adjust to your own panel]).
5. **Consent and GDPR — before the first session.** Information (controller, purpose, basis, recipients, retention
   period, rights), a separate consent to recording, withdrawal at any moment without consequences, minimal
   data. Details and a template: `references/recruitment-consent-gdpr.md`. Large scale, special-category data, children or
   profiling → an impact assessment (DPIA) in **arch-privacy-compliance**.
6. **Pilot** with 1 person from inside or outside the team: are the tasks and questions understandable, do the tools record,
   how long the session really takes. Fixes before the actual sessions.
7. **Session.** A neutral moderator, open questions ("tell me about the last time you…"), silent seconds, no
   prompting; in a task test, thinking aloud. A second observer takes notes as it happens (time, quote, event),
   without interpretation during the session. The participant can stop at any moment. Questions and pitfalls:
   `references/running-sessions.md`.
8. **Synthesis** — after 2–3 sessions you start ordering, not only at the end. Observations → atomic nuggets
   (one observation, a quote, a source) → grouping (affinity mapping) → patterns → findings with confidence
   (how many participants, what quality of evidence). AI may summarize and propose groups, but **a human checks every finding
   against a quote in the transcript**; a finding without a quote is dropped. Details: `references/synthesis-and-repository.md`.
9. **Report** `docs/project/01-discovery/research-report.md`: a TL;DR with the decision and the recommendation at the top, findings
   with evidence and confidence, recommendations with an owner and a date, the study's limitations (sample, method), what we do not
   know. Finish with an entry in the research repository (tags, nuggets, consents and data deletion dates). The panel, the research
   backlog and the playbooks are ResearchOps — `references/synthesis-and-repository.md`.
10. **From findings to decisions.** A workshop with the team within a week: finding → decision (do / change / research
    further / reject) → owner. After the rollout check whether the indicator from the plan moved. Hypotheses for further
    tests go to proc-product-discovery; numerical results from large samples to data-analysis.

## Sample size — heuristics with caveats
- Qualitative test: about 5 people per segment, in **several small rounds** with fixes between them; this is no guarantee
  of finding 85% of problems — the model assumes similar tasks and a homogeneous group.
- Interviews: count up to saturation (new sessions bring no new threads); usually 5–8 per segment to start [assumption].
- Quantitatively (survey, unmoderated test): the number follows from the needed precision, not from a rule of thumb; compute it
  with data-analysis. For measurements in a usability test, several dozen people (`references/methods-and-sample.md`).
- More segments = a sample for each segment.

## Example
Input: "New customers of the invoicing app 'Fakturka' drop out in the first week. Plan a study."
Result (a fragment of `research-plan.md`):

```markdown
## Decision and questions
Decision: whether to rebuild the account setup in Q1 (Anna K., PM, by 15.11).
Q1: At which setup step do new users abandon it and what gets in their way then?
Q2: What do they expect from the app after the first day?
## Method
In-depth interviews of 45 min (Q2, context) + a moderated setup test on a prototype (Q1), remote.
## Participants
8 people registered in the last 30 days who did not issue an invoice in 7 days (2 with a screen reader);
recruiting 10 people, a reserve of 2. Screener: 6 behaviour questions.
## Data
Screen and voice recording with a separate consent; transcripts without names; recordings deleted 90 days after the report [to be agreed with the DPO].
```

In the report: "Finding F1: 6/8 people do not understand the 'buyer's tax ID (NIP)' field on the first invoice (quotes C3, C5, C8…)
→ decision: add a GUS lookup preview, owner Anna K."

## Checklist
- [ ] decision, owner and date written down; research questions told apart from questions for participants
- [ ] the method justified by the question; the number of participants with a caveat about what follows from it
- [ ] a behaviour screener, participants with accessibility needs included
- [ ] information and consent (recording separately), withdrawal, retention with a deletion date
- [ ] a pilot; a neutral moderator; an observer takes notes
- [ ] every finding with a quote and confidence (also when AI did the synthesis)
- [ ] a report with a TL;DR, recommendations with an owner and limitations; an entry in the repository

## Additional materials
- `references/methods-and-sample.md` — the table of methods, sample size with caveats; read when choosing a method.
- `references/plan-and-report-template.md` — the templates of research-plan.md and research-report.md.
- `references/recruitment-consent-gdpr.md` — screener, panel, consent, participants' GDPR, inclusive design.
- `references/running-sessions.md` — the script, questions, moderator mistakes.
- `references/synthesis-and-repository.md` — nuggets, affinity mapping, synthesis with AI, ResearchOps.

## Sources
- Nielsen, "Why You Only Need to Test with 5 Users" (NN/g, 2000) — the model 1−(1−L)^n, L≈31%, 5 people ≈85%; secondary
  summaries checked 2026-10-17, the original was not opened [unverified].
- GOV.UK Service Manual, "Find user research participants" and "Running research sessions with disabled people"
  (search 2026-10-17; the page contents were not opened) — participants are actual or potential users, including disabled people
  and people with low digital skills.
- ISO 9241-210:2019 — human-centred design as an iterative process (a description from standards catalogs,
  2026-10-17; the four activities from own knowledge [unverified]).
- GDPR (2016/679) Art. 5, 6, 7, 13 — the article numbers from own knowledge, the text of the regulation was not opened in the session
  [unverified]; a secondary guide confirmed the information duty before consent and the right to withdraw (2026-10-17).
Described in our own words.
