# Trees, graphs and advanced structures

## Trees
- **Binary tree** and traversal: preorder (root, left, right — copying, serialization), inorder (left,
  root, right — in a BST it gives ascending order), postorder (children before the parent — deletion, computations from the leaves),
  level order (BFS with a queue).
- **Binary search tree** (BST): left < node < right; O(log n) only when balanced — without that it
  degenerates into a list (O(n)) on sorted data.
- **Balanced trees**: AVL (strictly balanced, faster reads), red-black (fewer rebuilds on writes
  — `TreeMap` in Java), 2-3 trees (the idea behind red-black trees).
- **B-trees and B+ trees**: wide nodes matched to disk pages → few reads; the basis of database indexes
  and file systems (in a B+ tree the data is in leaves linked into a list — fast ranges). ISAM — an older, static indexing
  method.
- **Heap**: a complete tree in an array, parent ≤ children; a priority queue, heapsort,
  schedules.
- **Trie**: a prefix tree — suggestions, dictionaries, routing by path.
- **Segment tree** and **Fenwick tree**: sums, minima or maxima in an interval with updates
  in O(log n) — when prefix sums are not enough because the data changes.
- **Suffix trees and arrays**: substring search, the longest repetitions in a text (usually replaced
  by a full-text index or a library).
- **Skip list**: a probabilistic alternative to balanced trees (e.g. sorted sets
  in Redis).

## Graphs
- **Representation**: an adjacency list (sparse graphs — typical), an adjacency matrix (dense, a fast "is there an
  edge"). Directed or not, weighted or not.
- **BFS** (a queue): the shortest path in an unweighted graph, levels, the distance in number of steps. **Bidirectional
  BFS** (simultaneously from the source and from the target, until the searches meet) visits far fewer nodes when the graph
  branches out quickly, e.g. in social networks. On a graph split across machines group the queries
  about neighbours from the same machine and set a limit on steps or time (arch-system-design, `project-examples.md`).
  **DFS** (a stack or recursion): connectivity, cycles, topological sorting, backtracking search.
- **Shortest paths**: Dijkstra (non-negative weights, with a priority queue — O((V + E) log V)), Bellman-Ford (negative
  weights, detects negative cycles — O(V·E)), A* (Dijkstra with a heuristic of the distance to the target — maps, games).
- **Minimum spanning tree**: Kruskal (edges from the cheapest + union-find), Prim (growing from a vertex
  with a priority queue) — the cheapest connection of all points (networks, cables).
- **Topological sorting** (DAG): the order of tasks with dependencies, detecting cycles in dependencies (modules,
  migrations, data pipelines — ddd-algorithm-recognition, `graph-order.md`).
- **Disjoint sets** (union-find) with path compression and union by rank: groups of connected elements,
  deduplicating customers from many sources.
- Large graphs and relationship queries in production: a graph database or a graph library, not your own implementation
  (arch-quality-attributes, `data-architecture.md`).

## Sources
- T. Cormen et al., *Introduction to Algorithms*; R. Sedgewick, K. Wayne, *Algorithms*
- [roadmap.sh — Data Structures and Algorithms](https://roadmap.sh/datastructures-and-algorithms) (trees, traversal,
  BST, AVL, 2-3, B-trees, ISAM, heap, trie, segment and Fenwick trees, suffix trees, skip list, graphs, BFS, DFS,
  Dijkstra, Bellman-Ford, A*, Kruskal, Prim, union-find)
Described in our own words.
