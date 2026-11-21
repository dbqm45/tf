# A specification review by a panel of reviewers

## When
After phase 3 (requirements) and before the cut plan — when the requirements are to be delivered by agents (the `/tf-task`
loop, executors), the change is large or touches areas from the high-risk triage (`tf risk`: permissions, money, data,
schema). A small change with a few criteria: an ordinary plan review is enough.

## The panel
2–3 reviewers, each as a separate subagent in a **fresh context**, without a view of the others' answers and without
the conversation in which the specification was written. Each gets only the specification (and the ADRs, if any) and
its task:
- **the adversary** — holes and contradictions: requirements that cannot be checked, ambiguous ones, ones that
  contradict each other, missing edge cases, an unbounded scope, open questions pretending to be answers;
- **the operator** — what happens at failures: partial writes, concurrency, retries and duplicates, unavailable
  dependencies, limits, observability of errors, recovery;
- **the executor** — whether it can be built and checked with a test in the agreed stack: acceptance criteria as tests,
  test data, dependencies between requirements, the order.
Every finding: an identifier (F1…), a severity (blocking / serious / minor), the requirement or the fragment, a scenario
showing the problem, a proposal.

## The course
1. Start the reviewers in parallel (Agent, separate contexts); the brief contains the specification path and the task,
   without the conclusions of the specification's author.
2. Collect the findings into the report `03-requirements/spec-review.md` (the `spec-review` template in core-project-record).
3. For every finding a decision: a change of a requirement (a new REQ or a correction), a recorded decision (DEC/ADR) or
   a rejection with a reason. The human settles business decisions and divergences.

## Reading the results
- **Convergent** (several reviewers pointed it out independently) — treat it as a defect.
- **Single** — to be weighed one by one; often the most valuable (e.g. a missed failure scenario).
- **Divergent** (one sees a problem, another explicitly sees it as correct) — the human's decision, recorded with a reason.
- **Limited independence:** the reviewers come from the same model provider; agreement is weaker evidence than a review
  by people or by different models — write that in the report.

## The gate
You move to the cut plan when all **blocking and serious** findings are closed with a trace (the identifier of a
requirement or a decision at the finding). Minor ones can stay open with a note. The executor and the task reviewer can
later quote a finding by its identifier (e.g. reject work that breaks a requirement added after F5).

## Limits
The panel does not replace a conversation with a domain expert or tests — it finds holes in the text, not in reality.
Cost: a few model runs per specification; not worth it for small changes.
