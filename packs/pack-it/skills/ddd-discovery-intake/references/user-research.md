# User research — plan, questions, survey, synthesis

Supports ddd-discovery-intake when the material must first be gathered, or when the questions for it need work.
Results feed the evidence bank in the same format as any other source.


## 1. Plan
- **Goal** — starts with a verb whose result can be checked: describe, assess, identify, compare. "Understand" and
  "explore" are not goals; ask what would be different after the study.
- **The decision it serves** — who decides what, and by when, based on the result. No decision → go back to the requester
  before recruiting anyone.
- **Research question ≠ interview question.** "What makes shift planning take two days?" is for the team; respondents get
  questions about their own recent work.
- **Sample** — usability tests: about 5 people per user segment; discovery interviews: 8–12 per segment, stopping when new
  interviews stop bringing new themes.
- **Recruit by behaviour, not demographics** — "planned a rota in the last month" beats "manager aged 30–45".
- **Screener** — 2–4 questions, disqualifying ones first, no yes/no questions (they invite the "right" answer); optionally
  one open question that shows whether the person can tell a concrete story.

## 2. Interview script
- Shape: broad → specific → broad (context, then one recent episode in detail, then wrap-up).
- The interviewer is the learner: the respondent is the expert on their own work.
- Ask about concrete past events, not opinions about the future. After the opening question, wait — silence brings detail.
- Probe without suggesting the answer: "what happened next?", "how did you know?", "what did that cost you?".
- A typical 20–30 minute script has 8–12 questions, roughly in this order:
  1. role and how often the activity happens;
  2. the most recent time it happened, step by step;
  3. what they do when the tool or process fails them (workarounds);
  4. what that costs — time, rework, risk, money;
  5. what they have already tried instead;
  6. what would make them change the way they work;
  7. closing: anything we did not ask; can they share an artefact (a spreadsheet, a screenshot, a ticket)?

## 3. Critiquing questions
For each question decide **keep**, **rewrite** or **remove**, and give the reason.

Red flags:
- **Hypothetical or future** — "would you use…", "would you pay…": people predict their own behaviour badly and are
  polite about it.
- **Fishing for compliments** — "do you like the idea?": the answer measures politeness, not need.
- **Leading** — the question contains the expected answer.
- **Double** — two questions in one sentence.
- **No link to the decision** — the answer would not change anything the team decides.

Rewrite toward past behaviour: the last specific time, what they did, the workaround, the cost, what they tried.
Record each rewrite as: *original* → *replacement* → *what a strong answer would show*.

Separate facts (logs, tickets, incident reports, numbers they can show) from guesses. A polished requirements document
can rest on weak evidence — flag it rather than treat it as truth.

Example:
| Original | Verdict | Replacement | Strong answer shows |
|---|---|---|---|
| "Would you use an app that plans shifts for you?" | rewrite | "Tell me about the last time you built the rota. What took longest?" | time spent, steps, where it breaks |
| "How much would you pay for it?" | rewrite | "What do you use for this today, and what does it cost you?" | existing spend or effort |
| "Do you like the idea?" | remove | — | — |

## 4. Survey
- 6–10 questions; one screening question at the start.
- Frequency and effort as ranges ("weekly", "1–2 hours"), not free numbers.
- 1–2 open questions asking for an example.
- Never ask people to rank solutions they have not seen.

## 5. Decision criteria before the research
Write down, before the first interview, what result leads to which action — otherwise any result can be read as support.
Illustrative examples, not norms:
- act if at least 3 of 5 respondents describe the same workaround without prompting, and at least 40% of the target group
  does the activity weekly;
- mixed signal → narrow the scope and test again;
- weak signal → do not build;
- first check whether an existing tool already solves it.

## 6. Synthesis
1. Read all sessions once before coding anything (familiarisation in a batch).
2. Build a codebook: each code with a definition and a sample quote in the evidence-bank format, e.g.

   ```
   ## S3 — research/interview-planner-03.md
   - **E12** > "I copy last month's rota and fix it by hand" — L41-42 [workaround]
   ```

3. A theme needs evidence from at least 2 interviews.
4. Show counter-evidence and contradictions before the themes that agree (`references/contradictions.md`).
5. Personas, when needed: a defining quote and 3–5 goals, grounded in the codes.
6. Prioritise: weight × frequency, importance versus satisfaction, impact versus effort, or an opportunity tree.

## 7. Personal data
Recordings and transcripts are personal data: consent, minimisation, anonymise before sharing, and no external
transcription or analysis service without a legal basis (arch-privacy-compliance).

## Sources
- R. Fitzpatrick, *The Mom Test*, 2013 (asking about past behaviour instead of opinions).
- GitHub `cookiy-ai/user-research-skill` (plan and synthesis routes) [unverified: accessed date].
