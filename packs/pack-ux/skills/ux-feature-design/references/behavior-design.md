# Designing behaviour change

When a feature is meant to make people **start, continue or stop** doing something (saving, regular
bookkeeping, learning, health, account security). You start with an ethics gate, not with techniques.

## 0. Ethics gate (before the design)
- Does the behaviour serve the **user** (they would want to do it themselves if it were easier), not only a company metric?
- Would you use it yourself and recommend it to people close to you? Would the user accept the technique if they knew how it works?
- N. Eyal's matrix: a product that improves lives and that its maker uses — a "facilitator" (fine); improves,
  but the maker does not use it — a "peddler"; does not improve, and the maker uses it — "entertainment"; neither — a "dealer"
  (you do not design it).
- No addictive techniques (infinite scroll with random rewards for children, rewards for merely opening
  the app), no deceptive patterns (`content-and-ethics.md`), no scaring with loss on cancellation. Record the gate's result
  in the specification; a doubt → a human's decision.

## 1. Define the goal (actor, action, outcome)
- **Target outcome**: a change in the world that can be measured (e.g. "customers have a 3-month financial cushion").
- **Actor**: who is to act, in what context and with what constraints (from research, not demographics).
- **Target action**: a concrete behaviour that leads to the outcome ("every month transfers 10% of the salary to a savings
  account"). The kind by the Fogg grid — new / familiar / increase / decrease / stop × one-time /
  for a period / permanently — says how hard the task is (a one-time familiar behaviour is the easiest,
  permanently stopping a habit — the hardest).

## 2. Diagnosis: why it does not happen today
- **The Fogg model B = MAP**: a behaviour happens when at the same moment there is **motivation**, **ability** (ease)
  and a **prompt**. No prompt → a reminder; low motivation → a spark prompt with a reason; low ability → make it easier
  (usually the most effective lever). Ease is spoiled by: time, money, physical and mental effort, departing
  from social norms and from routine.
- **The CREATE funnel** (S. Wendel) — an action passes through six stages, failure at any of them stops it:
  **cue** (does the user notice the opportunity), **reaction** (an automatic "like / dislike"), **evaluation** (a conscious
  balance of cost and benefit), **ability** (can they do it now), **timing** (is it urgent now), **execution**.
  Measure the drop-off at each stage and fix the weakest.
- **Two systems of thinking**: fast and automatic, and slow and analytical. Most everyday actions are
  automatic — that is why defaults and habits work, and a long persuasive text usually does not.

## 3. Strategy — from the most effective
1. **"Cheat" the problem — do it for the user**: a sensible default (changeable), automation of
   repetitive steps, acting on the occasion of another action (rounding up payments into savings).
2. **Habit**: a stable cue in an existing routine (the cue → routine → reward loop), an immediate and meaningful
   reward (progress, completion visible at once), a small first step. Changing a bad habit: replace the routine for the same
   cue, help avoid the cue, make the moment of action conscious.
3. **Conscious action** (when the first two do not fit): clear information on what and why, a "when, where, how" plan
   (implementation intentions — a concrete plan increases the chance of execution), a reminder of an earlier commitment,
   bringing consequences closer in time ("you lose PLN 40 a month", not "PLN 480 a year"), progress visible and counted.

## 4. Techniques — and their limits
| Technique | Fine use | Abuse |
|---|---|---|
| default | the most often chosen option, beneficial to the user | consents, paid extras, data sharing on by default |
| social proof, comparison with others | real data ("70% of people in your company turned on MFA") | made-up numbers, shaming comparisons |
| authority | a reliable source at a decision | fake recommendations, badges without substance |
| loss aversion | honest information about a real loss (expiring funds) | intimidation on cancellation, artificial urgency |
| limiting choice | 3–5 options with a recommended one, filtering | hiding the cheaper option |
| gamification, progress | progress towards a real goal, rewards supporting the goal | points for time spent in the app, a random reward as bait |
| commitment to others | voluntary, easy to withdraw | publishing failures without consent |
| the hook model (trigger → action → variable reward → investment) | analysing why something is engaging, and building habits the user wants | designing compulsive use |
- Choose a place on the **spectrum of interventions**: a nudge for simple, reversible decisions; slowing down
  and reflection (comparison, confirmation) for important and irreversible decisions (a loan, deleting data).

## 5. Measurement and the loop
- A behaviour metric (does the action happen) and an outcome metric (did the world change) — growth of the action without the outcome
  means the wrong target action.
- Tests: A/B of a single change, multivariate with large traffic (proc-product-discovery, `experiments-and-release.md`),
  long-term observation (the habit after 30 and 90 days, not only the first week).
- You collect lessons, prioritise them by impact and effort, apply them — and return to the diagnosis.

## Sources
- S. Wendel, *Designing for Behavior Change* (2nd ed. 2020) — CREATE, three strategies, ethics;
  B. J. Fogg, [Behavior Model](https://behaviormodel.org/), [Behavior Grid](https://behaviordesign.stanford.edu/resources/fogg-behavior-grid), *Tiny Habits* (2019)
- N. Eyal, *Hooked* (2014) — the hook model and the manipulation matrix; C. Duhigg, *The Power of Habit* (2012);
  D. Kahneman, *Thinking, Fast and Slow* (2011); R. Thaler, C. Sunstein, *Nudge* (2008)
- [LogRocket — starter guide to behavioral design](https://blog.logrocket.com/ux-design/starter-guide-behavioral-design/);
  [roadmap.sh — UX Design](https://roadmap.sh/ux-design)
Described in our own words.
