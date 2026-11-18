# Detecting contradictions

**Detection ≠ resolution.** The critic (a separate agent in a fresh context) only finds and describes contradictions;
the human resolves them, and the decision goes into `decisions.md`.

## Kinds of contradictions
1. The same rule described in two incompatible ways.
2. Different numbers, thresholds or deadlines for the same thing.
3. A decision or expectation breaking a stated constraint.
4. Mutually exclusive requirements.
5. A silent change of mind (someone claims something different than before, without marking the change).

## These are NOT contradictions
- similar words about **different subjects** (two different processes, two departments),
- an explicit change of decision ("formerly X, from January Y"),
- different preferences of people (that is a topic for a conversation, not a conflict of facts),
- a generality next to a specific statement that refines it.

## The same-subject test
Before you report: read 2–3 lines before and after both quotes — an exception or a narrowing often stands in the next sentence.
Report only when both quotes concern the same subject, at the same time and under the same conditions.

## Format (`docs/project/02-domain/contradictions.md`)
| # | Conflict (weight: high/medium/low) | Quotes (id, source, location) | Why they exclude each other | Diagnostic question | Status |
|---|---|---|---|---|---|
| C1 | Does the system add resources by itself? (high) | E3 S1 L20 · E41 S2 lane: Planner/7 | interview: "it only suggests"; board: a policy adds automatically | "When a person is missing, should the system **propose** a candidate, or assign them **by itself**?" | open |

A diagnostic question: specific, resolvable in one sentence, without accusing ("who is right?" — wrong).
Statuses: `open` → `resolved → D-xxx` | `deferred` (goes to Open questions) | `rejected` (with a reason).
Cache the critic's result by the hash of the bank content — re-running on the same bank does not change the list.
