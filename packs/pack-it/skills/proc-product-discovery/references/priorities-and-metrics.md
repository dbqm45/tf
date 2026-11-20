# Product priorities and metrics

## Prioritization — choosing a method
| Method | How | When | Pitfall |
|---|---|---|---|
| **RICE** | (Reach × Impact × Confidence) / Effort. Reach: the number of people or events in a period; Impact: 3 massive, 2 high, 1 medium, 0.5 low, 0.25 minimal; Confidence: 100% / 80% / 50%; Effort: person-months | comparing many ideas in the backlog | false precision — the numbers are estimates; Confidence keeps you from inflating guesses |
| **MoSCoW** | Must / Should / Could / Won't (this time) | the scope of one release or deadline | "Must" grows without end — a limit (e.g. ≤ 60% of effort) and the question "does the release make no sense without it?" |
| **Kano** | a survey: for each feature the question "how do you feel when it is there" and "when it is not" → categories: must-be, linear (the more, the better), attractive, indifferent, reverse | deciding what is a baseline and what is a differentiator | attractive features become must-be over time; run the survey per segment |
| **value / effort** | a 2×2 matrix: quick wins, big bets, fillers, time sinks | a quick review in a workshop | ratings from one head — do it with engineering and data |
| **WSJF** | cost of delay / duration | when time matters (deadlines, a market window) | estimate the cost of delay relatively, on the same scale for all items |
The method structures the conversation, it does not replace the decision. Record the inputs next to the result so that they can be challenged.

## Success metrics
- **HEART** (Google) — choose the dimensions that fit the feature, not all of them:
  | Dimension | An example metric |
  |---|---|
  | Happiness | a rating in a short in-product survey, SUS (`ux-feature-design`), NPS |
  | Engagement | the number of active days per week, feature use per user |
  | Adoption | the share of new users of the feature within 7 days |
  | Retention | the share of users returning after 30 days, cancellations |
  | Task success | the share of completed tasks, time, errors |
  For each dimension: a **goal** (in words) → a **signal** (the behavior that indicates the goal) → a **metric** (a number).
- A **north star metric** captures value for the customer and the business at once; **guardrail metrics**
  make sure that its growth does not break something else (errors, load time, cancellations, support tickets).
- **OKR**: a qualitative objective + 2–4 measurable key results (outcomes, not tasks: "time to first invoice ≤ 10 min",
  not "ship the wizard"). A team's results follow from the company's objectives.
- **Product-market fit**: signals — retention that flattens instead of dropping to zero; growth
  from referrals; in Sean Ellis's survey ≥ 40% of answers "very disappointed" if the product disappeared (a heuristic, not a law).

## Product analytics
- **An event plan** before implementation: the event name (a verb in the past tense, e.g. `invoice_sent`),
  properties, when it is sent, which metrics you compute from it. The plan lives in the repo, reviewed in the PR together with the code.
- Events from the server for business facts (payment, shipping) — they are not lost to ad blockers; from the client for
  UI interactions.
- Consent and GDPR: non-essential analytics only after consent (a banner without deceptive patterns, `ux-feature-design`), no personal
  data in event names and properties, retention defined.
- Heatmaps and session recordings: only with field and content masking, with consent, on selected screens — a lot of personal
  data, few answers to "why" (interviews and tests give those).

## Sources
- Intercom (S. McBride) — RICE; DSDM — MoSCoW; N. Kano (1984); K. Rodden et al., Google — HEART (2010)
- [roadmap.sh — Product Design](https://roadmap.sh/product-design) (prioritization frameworks, success metrics,
  business metrics & OKRs, product analytics, heatmaps, session recordings, product-market fit)
Described in our own words.
