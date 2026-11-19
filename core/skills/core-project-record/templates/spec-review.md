---
artifact: spec-review
phase: requirements
status: draft
version: 1
author: <agent>
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
inputs: [03-requirements/requirements.md]
---
# Specification review: <name>

## TL;DR
<Verdict: BLOCKED / READY FOR THE PLAN — the number of blocking, major and minor findings, how many are closed.>

## Panel
| Reviewer | Task | Model |
|---|---|---|
| adversary | holes, contradictions, uncheckable requirements | |
| operator | failures, partial writes, concurrency, retries | |
| implementer | whether it can be built and checked with a test | |

Independence: <reviewers in separate contexts, the same model vendor — agreement is weaker evidence than a review by people>.

## Findings
| ID | Weight | Raised by | Requirement | Problem (scenario) | Closure (REQ / DEC / rejected: reason) |
|---|---|---|---|---|---|
| F1 | blocking | adversary, operator | REQ-… | | |

## Divergences for the human's decision
<The finding, the reviewers' positions, the decision and the rationale.>
