# Challenging a recommendation before it is recorded

Used by arch-architect-practice (section 4) and arch-tech-selection before a stack or platform recommendation is
written down. The aim is not to reverse the choice but to find what the agreement hid.

## When
- Before an ADR, a stack choice or a hosting choice is recorded.
- When everyone (including the model) agreed in the first minutes.
- Before handing over a recommendation built from desk research.
Skip it for cheap, easily reversed choices — the cost of the exercise must match the cost of being wrong.

## Frame the question against the option
Replace "is X a good fit for Y?" with "what makes X a bad choice for Y?". Give the model or the room the leading option,
the constraints and the quality scenarios, and ask for the case against — not for a balanced summary.

## Three angles
| Angle | Ask for | Good finding | Weak finding |
|---|---|---|---|
| Devil's advocate | 3–5 concrete weaknesses: limits, prices, failure modes, lock-in | "starter tier allows 25 connections; we run 6 instances × 10 pool size" | "may not scale" |
| Pre-mortem | a short story: six months on, the choice failed — why | assumption → event → consequence, with a date or a load figure | "the project ran late" |
| Unknown unknowns | 3–5 risk classes outside the assessment, each as a control question | "Where are backups stored and for how long after we cancel?" | "compliance issues" |

Risk classes that are often missing: data residency and backups, exit cost from the provider, features still in beta or
preview, dependence on another team's roadmap, licensing changes, support hours, quotas that are only visible in the
billing console.

The pre-mortem technique asks people to assume failure has already happened, which makes it easier to voice doubts
(Klein, HBR 2007). Keep the narrative short; its value is the causal chain.

## Deciding on each finding
Every finding gets exactly one outcome:
- **accept** — understood, cheap or unlikely; one line in the ADR consequences;
- **known limitation** — recorded in the risk register with a mitigation or a trigger to revisit;
- **change** — the finding breaks a constraint or a high-priority scenario; go back to the options.

Risk register row:

| Risk | Found by | Likelihood | Impact | Outcome / action | Owner |
|---|---|---|---|---|---|

A finding with no outcome is not finished. Unanswered control questions become tasks with an owner before acceptance.

## Is it still doing anything?
Look back over the last several decisions. If the challenge never changed a choice, never added a register row and never
raised a question nobody could answer, it has turned into a ritual: sharpen the prompt (ask for numbers and names), invite
someone outside the team, or drop it for small decisions.

## Worked example
Leading option: a managed message broker from the cloud provider for order events.

- Devil's advocate: message size capped at 256 KB, so large order payloads need a claim-check; ordering only within a
  partition key; no replay beyond 7 days of retention; per-request pricing grows with chatty consumers.
- Pre-mortem: "In March a marketing push tripled orders; one consumer fell behind, retention expired before it caught up,
  and 4,000 order events were lost for the warehouse."
- Unknown unknowns: Is the dead-letter queue retained after the subscription is deleted? Does the provider's regional
  outage plan include this service? Is the schema registry feature generally available or in preview?

Outcomes: the choice stays. Known limitations: retention raised to 14 days plus a lag alert at 1 hour (owner: platform
team); payloads over 200 KB go through object storage. Action: confirm the registry's availability status before
the ADR is accepted. Changed: nothing.

## Sources
- G. Klein, "Performing a Project Premortem", Harvard Business Review, September 2007.
