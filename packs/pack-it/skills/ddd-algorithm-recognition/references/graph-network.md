# Graphs: networks, routes, groups

| id | Matching question | Signals | It is not this if… | Pitfalls |
|---|---|---|---|---|
| **shortest-path** | the cheapest/shortest path between points? | a route, getting there, the cost of a passage, "get there fastest" | many points have to be visited → `tsp-vrp` | negative weights break Dijkstra (Bellman-Ford) |
| **minimum-spanning-tree** | connect everything at the lowest cost? | a network, cabling, "connect all locations" | the path from A to B counts → `shortest-path` | an MST does not minimize the distance between pairs |
| **tsp-vrp** | a round of many points (one/many vehicles, time windows)? | a courier, a service technician, the day's route, a fleet | the order follows from dependencies → `graph-order` | NP-hard; a solver/heuristics (2-opt, OR-Tools) |
| **union-find** | do things join into disjoint groups (transitively)? | "related", duplicate customers, islands, clusters | the groups have to be balanced → `graph-partition` | joining only; splitting requires recomputation |
| **graph-partition** | a division into parts of similar size with a minimum of connections between them? | dividing teams, sharding, dividing modules | — | NP-hard; heuristics (METIS); this is also a heuristic for module boundaries |
| **graph-coloring** | assign slots/colours so that neighbours (conflicts) differ? | a class timetable, exams, "not at the same time" | the conflicts are time intervals → `interval-scheduling` | NP-hard; heuristics (DSATUR) |
| **vertex-cover / clique** | the smallest set watching all the connections / a group of mutually connected ones? | control, an audit of every relationship, "everyone knows each other" | — | NP-hard; usually approximation |
