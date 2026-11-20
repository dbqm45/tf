# Task selection — which tasks to take on and who covers them

## When it applies
- Signal: not everything fits, resources are not interchangeable, and tasks differ in value.
- Not this: round-robin or a duty rota — that is just a policy.

## Core shape
- Abstract form:
  - **resources** with features (skills, certificates, seniority, location);
  - **tasks** with a value and a list of **requirements**, each satisfied by a predicate over resource features
    (`skill = data-engineer AND seniority ≥ 3`).
  - Goal: choose the most valuable subset of tasks such that every requirement of every selected task is covered by its
    own **distinct** matching resource. A multidimensional knapsack / assignment problem. Tasks with no requirements are
    always selected.
- **Engine** behind one interface, chosen by scale and need:
  - greedy heuristic by value or value density — small cases or a quick good-enough answer; call it a heuristic;
  - dynamic programming or branch-and-bound — exact answers for medium cases;
  - a MIP solver — large or heavily constrained cases;
  - weighted assignment (Hungarian algorithm or MIP) when the value depends on the task–resource pair.
  The order in which tasks are considered is a parameter. Validate every engine on known examples.
- **Generic optimiser** (knows nothing about projects or people) separate from a **domain adapter** that translates
  engagements, staff and skills into the abstract form and back.

## Rules
- The output is a **recommendation** and holds nothing. A separate approval step places resource holds; if a hold
  conflicts, recompute.
- What-if questions run as before/after scenarios (hire one more person, move someone between teams); the value
  difference is the answer.
- Explain exclusions: which requirement could not be covered.
- Pitfall in DP code: a table whose cells all reference one shared mutable object.

## Decisions to settle
- Mandatory tasks regardless of value?
- Bans and preferences (person X never on client Y)?
- Stability: how much may a recomputation change already published assignments?
- Tie-breaking between equal-value solutions.
- Partial fulfilment of a task, or all-or-nothing?
- Part-time resources (0.5 of a person)?

## Belongs elsewhere
- Whether a person is free in a period → resource holds.
- Order of stages → stage scheduling.
- Algorithm recognition in general → ddd-algorithm-recognition.

## Traps
- Hand-coded matching loops in a service ("take the first free architect").
- Greedy presented as optimal.
- Assignment results written straight into calendars without approval.

## Worked example
Requirement: a consultancy has more client engagements per quarter than staff; engagements need specific skills
(cloud architect, data engineer) and have different margins; which to accept and who staffs them; would hiring another
data engineer pay off?
- Resources: 6 people with skill sets. Tasks: 9 engagements with margin and requirements, e.g. `E3: margin 180k,
  needs {cloud-architect, data-engineer, data-engineer}`.
- Scale: 9 tasks × 6 people → exact branch-and-bound is cheap (decision A); MIP if the portfolio grows past ~50.
- Result: accept E1, E3, E5, E8 (total 610k); E2 excluded — needs a third data engineer.
- What-if: add a hypothetical data engineer → optimum 760k; difference 150k vs the yearly cost of the hire → the answer
  to "does hiring pay off".
- Recommendation goes to the partners; holds on people's calendars only after approval.
- Open: are some engagements mandatory (strategic client)? How stable must assignments stay if a new engagement arrives?
