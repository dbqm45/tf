# Problem-solving patterns and algorithm design techniques

## Patterns (recognize the shape of the problem)
| Pattern | Signal in the task | Idea | Cost |
|---|---|---|---|
| **two pointers** | a sorted array, a pair or triple with a given sum, removing duplicates in place | pointers from the ends, or a fast and a slow one in the same direction | O(n) instead of O(n²) |
| **sliding window** | "the longest / shortest substring meeting a condition", a sum in a window | extend the right end, shrink the left when the condition is broken; the window state in a map or a counter | O(n) |
| **fast and slow pointer** | a cycle in a list or sequence, the middle of a list | one pointer moves by one step, the other by two (Floyd's algorithm) | O(n), O(1) memory |
| **merging intervals** | overlapping appointments, reservations, ranges | sort by start, merge with the previous one when they overlap | O(n log n) — in a database: range types and exclusion constraints (be-database) |
| **cyclic sort** | numbers from the range 1..n, missing or duplicated | put each number at its index | O(n), O(1) memory |
| **top-k / the k-th element** | the k largest, most frequent, nearest | a heap of size k or selection (quickselect) | O(n log k) / O(n) on average |
| **two heaps** | the median of a stream, the middle of a changing set | a max-heap for the lower half, a min-heap for the upper | O(log n) per element |
| **grid traversal** ("islands") | connected areas on a map, a plan, in a matrix | BFS or DFS with marking of visited cells | O(rows × columns) |
| **binary search on the answer** | "the smallest value at which the condition holds", a monotonic condition | binary over the range of answers, checking the condition | O(log of the range × the cost of a check) |
| **prefix sums** | many queries about the sum in an interval | `pref[i] = sum up to i`; interval sum = a difference | build O(n), query O(1) |
| **monotonic stack** | "the nearest greater element", histograms | a stack that keeps the order | O(n) |

## Techniques
- **Brute force**: check all the possibilities — a reference point for tests, and usually enough for a small n.
- **Recursion**: a base case + reducing the problem; watch the stack depth.
- **Backtracking**: build the solution step by step, go back when a partial solution breaks a constraint
  (permutations, subsets, puzzles, assignment with constraints). Exponential — prune branches as early as possible;
  for large business problems a solver (ddd-algorithm-recognition, `optimization.md`).
- **Divide and conquer**: split, solve the parts, combine (merge sort, quicksort, binary
  search).
- **Dynamic programming**: the problem has overlapping subproblems and an optimal substructure (the edit distance
  of texts, knapsack, the number of paths, the longest common subsequence). Define the state and the transition; compute top-down with memory of
  results (memoization) or bottom-up with a table; the memory can often be reduced to one row.
- **Greedy**: choose the locally best option — it works only when this can be proven (making change for
  typical denominations, scheduling the largest number of disjoint intervals, a minimum spanning tree); in other
  cases it gives a fast approximation without a guarantee.
- **Randomized**: a random choice of the pivot in quicksort, sampling, probabilistic structures (a Bloom filter —
  "definitely not there" or "probably there", HyperLogLog — an approximate count of unique values). The result is correct with high
  probability or approximate — describe this in the code.

## Structures composed of simple ones — example: an LRU cache
A frequent task: a cache with a limited capacity that, on overflow, evicts the least recently used element.
- A **map** key → node and a **doubly linked list** in the order of use (the head is the most recent, the tail is
  the oldest). Read: find the node in the map and move it to the head. Write: add at the head, and on
  overflow remove the tail of the list and its key from the map. Everything in O(1).
- In TS / JS `Map` keeps the insertion order: "move to the head" is `delete` + `set`, and the oldest is
  `map.keys().next()`. In Java `LinkedHashMap` with access order (`accessOrder = true`) and an overridden
  `removeEldestEntry`.
- In production use a library (e.g. `lru-cache` in Node, Caffeine in Java). They give size and time-to-live limits and
  statistics. LRU is not the only policy: LFU (least frequently used) or TinyLFU (Caffeine) cope better with
  one-off scans.
- The same scheme "a map for fast access + a second structure for order" is used in a priority queue
  with priority updates (a map + a heap) and in rankings (a map + a tree).

## How to approach a new problem
1. Examples of input and output, also edge cases; what the maximum data size is (it determines the acceptable
   complexity).
2. A brute-force solution and its cost.
3. Does any pattern or technique fit? Which data structure removes the most expensive operation?
4. Pseudocode, the invariant, a check on the examples; only then the code.
5. Tests: examples, edges, a comparison with the brute-force version on random data.
For practice: LeetCode, Codewars, Exercism, Edabit — they teach pattern recognition; at work the ability to
estimate the cost and choose a ready tool matters more.

## Sources
- S. Skiena, *The Algorithm Design Manual*; the "Grokking the Coding Interview" materials (patterns)
- [system-design-primer](https://github.com/donnemartin/system-design-primer) — `solutions/object_oriented_design/lru_cache`
  (CC BY 4.0); the `LinkedHashMap` documentation, Caffeine
- [roadmap.sh — Data Structures and Algorithms](https://roadmap.sh/datastructures-and-algorithms) (two pointer,
  sliding window, fast and slow pointers, merge intervals, cyclic sort, kth element, two heaps, island traversal,
  brute force, recursion, backtracking, divide and conquer, dynamic programming, greedy, randomised algorithms)
Described in our own words.
