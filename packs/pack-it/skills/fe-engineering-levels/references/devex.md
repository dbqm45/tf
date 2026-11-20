# Developer Experience (DevEx)

> **Contents:** Definition · Why it matters for the business (not only for engineers'… · The tight-loose model (governance) · Three sources of data about DevEx · Metrics: FLOW and DORA · Anti-patterns (5 typical mistakes) · 9 practices for improving DevEx (from the signadot article) · The AI-readiness model (5 criteria, from conlea.pl) · A practical rollout plan (5–6 steps, from… · When to apply this knowledge

Sources: networkperspective.io/devex-polska/procesy-developer-experience, blog.conlea.pl/jak-developer-
experience-devex, medium.com/@signadot/how-to-improve-and-measure-devex-in-your-organization — described in our own
words. DevEx is not specific to the frontend; this file describes it as a Staff/Principal competency.

## Definition

DevEx is **"invisible infrastructure"** — the whole of the conditions, processes and tools that affect how
easily, quickly and without frustration a developer goes from an idea to working, deployed code. It can
also be put as **"the UX of a technology organization"**: just as UX measures how easy it is for a user to use the
product, DevEx measures how easy it is for an engineer to use the internal systems, processes and tools of their
company.

It is not only "a good IDE" or "fast CI" — DevEx covers the whole cycle: onboarding, documentation quality,
time waiting for review, stability of test environments, quality of communication between teams, clarity
of priorities.

## Why it matters for the business (not only for engineers' well-being)

Estimates cited in the sources (treat them as indicative, dependent on the industry/company, not as a universal
constant):
- Organizations with good DevEx record a **40–50% shorter cycle time** (the time from starting work on
  a task to deploying it to production) and a similar order of magnitude of overall delivery speed-up.
- Well-optimized CI/CD pipelines are sometimes even **10× faster** than unmaintained ones, which directly
  shortens the developer's feedback loop.

The mechanism of this effect: every friction — a slow build, an unclear error, missing documentation, a flaky test —
costs not only time but also **context switching**, which is disproportionately
expensive cognitively. DevEx is not "polishing" engineering work — it is removing a real, measurable
cost from every iteration.

## The tight-loose model (governance)

A practical model of managing DevEx consists in distinguishing what should be **strictly** (tight) standardized
across the whole organization and what can be left **loose** to the team's decision:

| | Tight (shared standard) | Loose (team decision) |
|---|---|---|
| Examples | CI/CD pipeline, commit format, security policy, observability/logging | choice of editor, internal folder structure within the convention, the way stand-ups are run |
| Goal | consistency, the ability to move between teams, a lower cost of maintaining the platform | team autonomy, no imposing of a solution that does not fit the local context |

A mistake in either direction is costly: excessive "tight" (imposing everything centrally) kills autonomy and
pace; excessive "loose" (no standard at all) creates fragmentation, which makes rotating people between
teams harder and raises the cost of the platform supporting everyone.

## Three sources of data about DevEx

1. **Automatic data (telemetry)** — metrics from systems (build time, review time, number of
   deploys, DORA indicators — see below). Objective, but they do not say "why".
2. **Data from people (surveys/interviews)** — the subjective feeling of friction, satisfaction, frustration. They say
   "why", but they are prone to bias and need regularity to capture a trend.
3. **Data from AI/analytical tools** — a newer category: automatic analysis of patterns in telemetry
   and text data (e.g. sentiment in retros/surveys) at a scale a human will not analyse
   manually.

None of these sources alone gives the full picture — telemetry without human context leads to
optimizing the wrong metric (see "anti-patterns" below); surveys without telemetry do not show whether the feeling
corresponds to a real change.

## Metrics: FLOW and DORA

**FLOW** — metrics focused on the flow of work through the system (not on the individual developer):
- **Flow velocity** — the pace at which work flows through the pipeline (how many work items finish in a given
  period).
- **Flow efficiency** — the ratio of active work time to total time (the rest is waiting: for review,
  for CI, for a decision).
- **Flow time** — the total time from the start of a task to its completion.
- **Flow load** — the amount of work in progress (WIP) — too high a load scatters attention and lengthens flow time
  disproportionately (a queueing effect, not linear).

**DORA** (DevOps Research and Assessment) — delivery metrics regarded as an indicator of delivery maturity,
called a "quantitative" approach in the sources. The current set (since the 2024 report — five metrics: deployment frequency,
change lead time, failed deployment recovery time, change fail rate, deployment rework
rate) with definitions is in **eng-continuous-delivery** — do not duplicate it here. The import sources still knew the
four-element version with "time to restore service".

**A note on the completeness of the sources:** the signadot article, despite a title promising a broader overview of ways
of measuring DevEx, in practice names explicitly and in detail only DORA as a quantitative framework — it does not discuss
explicitly the SPACE or DX Core 4 frameworks, even though these are known, publicly documented alternative/
complementary DevEx measurement models (SPACE: satisfaction, performance, activity, communication, efficiency;
DX Core 4: speed, effectiveness, quality, impact — it combines DORA, SPACE and DevEx). So do not assume that this skill (or the source article) exhausts the topic
of DevEx metrics — SPACE/DX Core 4 are worth reading up on separately if a full map of the available
frameworks is needed.

## Anti-patterns (5 typical mistakes)

1. **Measuring activity alone, not the outcome** — the number of commits/lines of code as a proxy for productivity;
   it rewards noise, not value.
2. **Per-person metrics used to assess/rank individuals** — DORA/FLOW are **system/team** metrics, not
   a tool for ranking developers; used that way, they trigger metric gaming and the hiding of problems.
3. **Collecting data without acting on it** — surveys/dashboards that lead to no change
   quickly lose the team's trust and stop getting honest answers.
4. **Solving a problem before understanding it** — rolling out a tool/process "because others do it" without
   a prior diagnosis of where the friction actually is in this particular organization.
5. **Treating DevEx as a one-off project** — rolling out a survey/dashboard once and considering the topic
   closed, instead of a continuous process.

## 9 practices for improving DevEx (from the signadot article)

Summary — the practices the article points to as concrete actions that improve DevEx (not only measure it):
removing manual, repetitive steps (onboarding automation, self-service environments), shortening
the feedback loop (faster tests/build, per-branch/preview environments), reducing flaky tests, clear and
current internal documentation, standardizing tooling in the spirit of the tight-loose model (see above), actively
removing "toil" (operational work without development value), investing in platform engineering (internal
self-service platforms instead of manual ticketing to other teams), regular, qualitative (not
only quantitative) collection of feedback from teams, and celebrating/communicating the removal of a concrete
friction — so that the team sees that a reported problem actually leads to a change (it closes the loop with
anti-pattern 3 above).

**The overriding rule from this source:** "identify the pain before you start solving it" — a tool/process
rolled out without a prior diagnosis of the real problem in a particular team is likely to hit the wrong
place, even if it is a good practice elsewhere in itself.

## The AI-readiness model (5 criteria, from conlea.pl)

Criteria by which an organization can assess whether its DevEx/processes are ready for the effective use of
AI in engineering work (and not only "we have access to an AI tool"):
1. **Quality and availability of data/context** — does the AI have access to current documentation, code history,
   team conventions, or does it work in an information vacuum.
2. **Standardization of processes** — repeatable, well-defined processes are easier for AI to support/
   automate than chaotic, ad-hoc ones.
3. **Quality of the existing code/architecture** — AI supports well-structured code faster; technical
   debt and inconsistency make effective AI support harder in the same way as they make it harder for people.
4. **A culture of feedback and iteration** — the organization must have the habit of assessing and correcting results (including
   AI results), not only accepting them without verification.
5. **Security and data governance** — clear rules on which data/code may go to AI tools, so that
   the speed-up does not create a new compliance/security risk.

## A practical rollout plan (5–6 steps, from networkperspective.io)

1. **Diagnose before you choose a tool** — collect data (telemetry + surveys) about where the friction actually
   is in this particular organization, instead of copying a solution from another company.
2. **Set the tight-loose model** — decide consciously what is a shared standard and what is team autonomy,
   instead of leaving it to chance.
3. **Choose a small set of metrics (FLOW + DORA)** and start collecting them systematically before you invest in
   large process changes.
4. **Roll out changes iteratively, in small steps**, measuring the effect of each change — not one large "DevEx
   transformation programme" rolled out all at once.
5. **Close the loop with the team** — communicate which change resulted from their feedback (anti-pattern 3 and the
   "celebrating" practice above) — this is what keeps subsequent surveys honest.
6. **Treat it as a continuous process**, not a project with an end date — repeat the cycle diagnosis → change →
   measurement regularly.

## When to apply this knowledge

The Staff/Senior Staff level is usually the first level at which an engineer has a real influence on the DevEx of a whole
team/domain (not only their own work) — see `staff.md`. The Principal level usually influences the DevEx of the whole
technology organization and decides on the choice of platforms/standards at that level — see
`principal.md`.
