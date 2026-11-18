# A/B experiments and launch readiness

## When A/B, and when not
A/B answers the question "does change X improve metric Y" with high traffic. It is not suited to the question "why"
(interviews, usability tests), to low traffic (the result will not reach power), to changes that cannot be undone,
or to features required by law.

## Test design (before the start, written down)
1. **Hypothesis**: "If [change], then [metric] will rise by [minimum meaningful effect], because [evidence from discovery]".
2. **The primary metric** (one) and **guardrail** metrics (errors, load time, cancellations, revenue).
3. **The unit of randomization** (the user, not the session — otherwise the same person sees both variants) and the target group.
4. **Sample size and duration** from a power calculator: the significance level (usually 5%), power (usually 80%), the minimum
   detectable effect, the baseline value. Duration: full weeks (the weekly cycle), at least 1–2.
5. **The decision rule**: what you will do on a win, a loss and no difference.
Implemented through feature flags with the variant assigned on the server side (eng-continuous-delivery, ops-release-engineering).

## Other kinds of tests
- **An incremental test (an A/B of a single change)**: one difference between the variants, so the result can be attributed to it. The default
  choice when validating a single design decision.
- **A multivariate test**: several elements at once (headline × image × button) and their interactions. The number of combinations
  grows multiplicatively, so much more traffic is needed — with low traffic, run successive A/B tests.
- **An incrementality test** (a control group with no intervention at all, e.g. no campaign or notifications): it measures how much
  effect the intervention had at all, not which version is better.

## Pitfalls
- **Peeking at results** and ending the test when "it came out significant" — false wins. Either a fixed duration or a sequential
  method planned from the start.
- **A sample ratio mismatch** (SRM, e.g. 50/50 planned, 52/48 came out with a large sample) — an assignment or data-collection
  error; the result goes in the bin, fix it first.
- **Many metrics and segments** without correction — one will "win" by chance. Treat segments as hypotheses for the next test.
- **The novelty effect** — a rise from curiosity fades after weeks; look at the daily trend.
- Ethics and law: no testing of discriminatory prices, deceptive patterns or changes to consents; a note in the privacy
  policy that you run experiments.

## Launch readiness
- **Goals**: success and guardrail metrics, baseline values, a dashboard, the date of the post-launch review (e.g. 2 and 6 weeks).
- **Product**: edge and error states checked (ux-feature-design), accessibility (WCAG 2.2 AA), content and translations,
  consents and the privacy policy if you collect new data.
- **Technology**: flags and a gradual rollout plan, rollback rehearsed, monitoring and alerts, load tests
  if traffic will grow (ops-release-engineering, ops-sre-incidents).
- **Organization**: customer support trained and given answers to typical questions, documentation and release
  notes, sales and marketing know what and when; an owner of the "release / hold" decision.
- **Constraints**: law and regulations (the legal department), partner deadlines, dependencies on other teams.

## Sources
- R. Kohavi, D. Tang, Y. Xu, *Trustworthy Online Controlled Experiments* (2020)
- [Atlassian — product launch checklist](https://www.atlassian.com/agile/product-management/product-launch-checklist);
  [roadmap.sh — Product Design](https://roadmap.sh/product-design) (A/B testing, experimentation, launch readiness)
Described in our own words.
