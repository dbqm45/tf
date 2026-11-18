---
name: eng-algorithms-data-structures
description: Use when code performance matters — complexity, choosing data structures, algorithm techniques, graphs, LRU.
disable-model-invocation: true
metadata:
  status: "inactive"  # measured 2026-11-16: docs/inactive-skills.md
  review: "2027-10-17"
  catalog: "Use for code where the performance or the correctness of an algorithm matters — complexity (O, time, memory), choosing a data structure in TS and Java, solving patterns (two pointers, window, intervals, top-k, BFS/DFS), techniques (recursion, backtracking, dynamic programming, greedy), trees and graphs. Not for recognizing a problem in the domain (ddd-algorithm-recognition)."
---

# Algorithms and data structures in everyday code

In production code you usually **choose** a ready structure or algorithm from a library, rather than writing it from scratch.
What matters is knowing what each thing costs and recognizing when a loop inside a loop turns 1000 records into a million
operations. A classic problem hidden in business requirements (a schedule, an assignment, routes): ddd-algorithm-recognition.

## Complexity — how to count it
- O notation describes the growth of the cost relative to the input size n (the worst case, unless stated otherwise);
  Θ — the exact order, Ω — a lower bound. You drop constants and lower-order terms, but **in practice constants
  matter** for a small n.
- Typical classes: O(1) constant, O(log n) logarithmic (splitting the space in half), O(n) linear, O(n log n)
  (good sorting), O(n²) (a loop inside a loop), O(2ⁿ) exponential (all subsets), O(n!) (all permutations).
  At n = 10⁶: O(n log n) ≈ 2·10⁷ operations — a fraction of a second; O(n²) = 10¹² — hours.
- Counting: nested loops multiply, consecutive ones add up; recursion — the number of calls × the work per call (e.g. split
  in half and merge linearly → O(n log n)); **hidden loops**: `includes`, `indexOf`, `filter` in a loop, `contains` on a list,
  a database query in a loop (N+1 — be-database).
- **Memory** is counted the same way (extra arrays, the recursion stack). **Amortization**: appending to a dynamic
  array is usually O(1), sometimes O(n) on growth — O(1) on average.

## Choosing a data structure
| Need | Structure | TS / JS | Java | Cost of typical operations |
|---|---|---|---|---|
| a list with access by index | dynamic array | `Array` | `ArrayList` | access O(1), append at the end O(1)*, insert in the middle O(n) |
| lookup by key | hash table | `Map` (not a plain object for dynamic keys) | `HashMap` | O(1) on average |
| uniqueness, "has it been seen" | hash set | `Set` | `HashSet` | O(1) on average |
| FIFO queue | queue / deque | an array with a head index or a library (`shift()` is O(n)) | `ArrayDeque` | O(1) |
| LIFO stack | stack | `Array` with `push`/`pop` | `ArrayDeque` | O(1) |
| always the smallest / largest, top-k | heap (priority queue) | a library (none in the standard) | `PriorityQueue` | insert and remove O(log n), peek O(1) |
| sorted keys, ranges, "the nearest greater" | balanced tree | a library or a sorted array with binary search | `TreeMap`, `TreeSet` | O(log n) |
| a list with frequent insertion at a known place | linked list | rarely needed | `LinkedList` (usually slower than `ArrayList` because of the CPU cache) | insert O(1) at a node, access O(n) |
| text prefixes (suggestions) | trie | a library / your own | a library | O(word length) |
| groups of connected elements | disjoint sets (union-find) | your own (a dozen or so lines) | your own | almost O(1) |
Check the specific implementations and their properties for your version (lang-typescript, lang-java). In a database
the counterpart of choosing a structure is an index (B-tree, hash, GIN — be-database).

## Sorting and searching in practice
- Use the library sort: `Array.prototype.sort` is stable (since ES2019), but **without a comparator it sorts
  as text** (`[10, 9, 1]` → `[1, 10, 9]`) — always pass a comparator; `toSorted` does not mutate. In Java sorting
  objects is stable (TimSort), sorting arrays of primitive types does not have to be (it does not matter for numbers).
- Binary search only on sorted data; off-by-one errors and overflow of the midpoint in languages with fixed-width
  numbers (`mid = lo + (hi − lo) / 2`).
- Frequent lookup in a list → convert it to a `Map`/`Set` once (O(n)) instead of `find` in a loop (O(n²)).
- Instead of sorting everything for the k largest — a heap of size k (O(n log k)) or selecting the k-th (O(n) on average).

## Correctness
- For a non-trivial algorithm write down the **invariant** (what is true at the start of each loop iteration) and the edge
  cases: an empty set, one element, duplicates, negative values, overflow.
- Property-based tests (fast-check, jqwik) that compare against a simple, obviously correct version (e.g. the library
  sort, a brute-force search) on random data (qa-spec-first-testing).
- Recursion: the stack depth is limited (in JS approx. a few to a dozen or so thousand frames, depending on the engine) — for large
  data an iterative version with an explicit stack.

## More
- Problem-solving patterns and algorithm design techniques: `references/patterns-and-techniques.md`.
- Trees, graphs and advanced structures: `references/trees-and-graphs.md`.

## Review checklist
- [ ] the complexity of loops and queries estimated for a realistic n (also hidden loops and N+1)
- [ ] the data structure matched to the operations (Map/Set instead of searching a list)
- [ ] sorting with a comparator; no mutation where it is not needed
- [ ] edge cases and invariants; a property test for non-trivial logic
- [ ] recursion bounded or iterative

## Sources
- T. Cormen et al., *Introduction to Algorithms*; S. Skiena, *The Algorithm Design Manual*; the ECMAScript specification
  (`Array.prototype.sort`), the Java Collections documentation
- [roadmap.sh — Data Structures and Algorithms](https://roadmap.sh/datastructures-and-algorithms)
Described in our own words.
