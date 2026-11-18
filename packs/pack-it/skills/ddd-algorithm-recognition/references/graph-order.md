# Graphs: order and dependencies
Entry format: **Matching question** · Signals · Mapping · It is not this if… · Pitfalls

## topological-sort — order from dependencies
- **Question:** do the elements have the relation "X must be before Y" and are we looking for an admissible order or parallel levels?
- **Signals:** "depends on", "first… then", "blocks", stages, steps, "what can be done in parallel".
- **Mapping:** node = stage/task; edge = dependency; level = a set of things that can be done in parallel.
- **It is not this if** durations and a deadline count → `job-scheduling`; the dependencies form cycles → `feedback-arc-set`.
- **Pitfalls:** a cycle means contradictory business rules — that is a question for the expert, not a technical error; implicit dependencies
  (e.g. a shared resource) are edges too.

## job-scheduling (critical path, CPM) — a schedule with durations
- **Question:** do tasks with dependencies have durations, and are we asking about the earliest finish, the slack, the critical path?
- **Signals:** a deadline, a delay, "a penalty for being late", "what is critical", time slack, a cascade of delays.
- **Mapping:** a DAG of stages, weight = duration; critical path = the longest path.
- **It is not this if** limited resources come in → resource-constrained scheduling (NP-hard; heuristics/a CP solver).
- **Pitfalls:** with resource constraints the problem stops being simple; uncertain durations → PERT/simulation.

## transitive-closure — who affects whom (reachability)
- **Question:** are we asking what indirectly depends on a given thing (a cascade of effects)?
- **Signals:** "affects indirectly", "if X is delayed, what else", risk analysis, transitive dependencies.
- **Mapping:** reachability in the dependency graph.
- **Pitfalls:** the full closure is dense (n²) — compute on demand (BFS/DFS) instead of storing it.

## feedback-arc-set — breaking cycles
- **Question:** do the dependencies form cycles, and do we have to point to the fewest dependencies to remove?
- **Signals:** "goes round in circles", mutual blocking, contradictory orders.
- **Pitfalls:** NP-hard in general; heuristics. The decision which dependency to break is made by the business.

## connectivity (critical points/edges)
- **Question:** does removing one element disconnect the network (a single point of failure)?
- **Signals:** "if this person leaves", "the only connection", redundancy.
- **Mapping:** bridges and articulation points in the graph.
