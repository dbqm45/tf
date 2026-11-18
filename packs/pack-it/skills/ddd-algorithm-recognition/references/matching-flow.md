# Graphs: matching and flow

## bipartite-matching — the most pairs
- **Question:** do we join elements of two sets (people–tasks) so that as many as possible have a pair, and the admissibility of a pair is yes/no?
- **Signals:** "assign", "match", "each one can handle only…".
- **It is not this if** the pairs have a cost → `assignment`; both sides have preferences → `stable-matching`; an element can have many pairs with a limit → `max-flow`.

## assignment (Hungarian method) — the cheapest matching
- **Question:** does each pair have a cost/gain and are we looking for the matching with the best sum?
- **Signals:** "cheapest", "best matched", the cost of an assignment, a competence rating.
- **Pitfalls:** maximum, stable and cheapest matching are three different problems; the generalized version (a task takes part of
  a person's capacity — GAP) is NP-hard → `optimization.md` (multidimensional knapsack / solver).

## stable-matching — preferences of both sides
- **Question:** do both sides have preference lists, and there must not exist a pair that would prefer each other?
- **Signals:** recruitment, assigning students, "both sides choose".
- **Pitfalls:** the result favours the proposing side — that is a decision about fairness.

## max-flow / min-cut — throughput
- **Question:** does something limited by capacity flow through a network, and are we asking about the maximum or the bottleneck?
- **Signals:** throughput, daily limits, "bottleneck", dividing a volume between channels.
- **Mapping:** edge = capacity; minimum cut = the bottleneck. An assignment with limits on both sides = a flow.
