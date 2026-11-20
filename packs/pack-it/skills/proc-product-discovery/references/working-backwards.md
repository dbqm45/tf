# Working backwards from the customer: a press release, an epic as a hypothesis, an outcome-based roadmap

## A press release and FAQ before building
You write a launch-day document before any code exists — a check whether we know for whom and why.
**The press release (at most 1 page, in the customer's language, no jargon):**
1. Title — the name and the benefit for a specific customer.
2. Subtitle — who gains what, in one sentence.
3. The problem — how the customer copes today and how much it costs them (with evidence from discovery).
4. The solution — what changes for the customer, not how it works inside.
5. A quote from the company — why we are doing this.
6. How to get started — the customer's first step.
7. A customer quote — how they would describe the benefit (a hypothesis to check in conversations).
**The external FAQ** — customers' questions (price, migration, security, what it does not do).
**The internal FAQ** — questions from the team and the board: who the customer is and how many there are, what the outcome is and how we will measure it,
cost and team, the biggest risks in four categories (value, usability, feasibility, viability), what
must be true, what we will not do, what will stop the project.
**The test**: 5–8 conversations with target customers based on the press release (would they want it, what would they change, how much would they
pay) and a review of the internal FAQ with engineering and finance. You rewrite the document until the answers
stabilize; only then the scope and the plan.

## An epic as a hypothesis
```
We believe that [solution] for [customer] will solve [problem / opportunity].
We will know it by [outcome and metric: baseline value → target value] in [time].
Early signals: [leading metrics after 2–4 weeks].
We stop or change direction if [stopping criterion].
First we will check [the weakest important assumption] through [the cheapest test].
```
An epic with no metric and no stopping criterion is a list of work, not a hypothesis. After the release you compare the outcome with the hypothesis
and record the decision (continue, change, withdraw).

## An outcome-based roadmap
Instead of features with dates for a year — three columns:
- **Now** — the problems and outcomes the team is working on (with a metric and a known scope);
- **Next** — the problems next in line, with solution hypotheses, with no commitments about features;
- **Later** — opportunities and areas to investigate, with no solutions.
Each item: a problem or opportunity, an outcome and metric, evidence, confidence. Dates only where there is an external
commitment (a regulation, a contract, an event). A review after each release: items move according to results,
not according to the calendar. You show stakeholders what we want to change and how we will measure it (pm-stakeholders).

## Sources
- C. Bryar, B. Carr, *Working Backwards* (2021) — a press release and FAQ before building (an Amazon practice).
- J. Bastow, the now / next / later roadmap (ProdPad, 2012 and later write-ups).
- J. Gothelf, J. Seiden, *Lean UX* (3rd ed., 2021) — a hypothesis with an outcome and a metric.
Described in our own words.
