# Search, similarity, real time

| id | Matching question | Signals | Pitfalls |
|---|---|---|---|
| **inverted-index** | full-text search over documents? | "search in descriptions", filtering by words | a search engine/database index; word inflection (Polish!) |
| **approximate-string-match** | typos, almost identical names? | "Kowalski/Kowalsky", deduplicating counterparties | comparing all pairs is n² → first blocking (grouping by a key) |
| **lcs / diff** | differences between versions of a text/list? | change history, comparing contracts | — |
| **lsh / vector-similarity** | semantic similarity, recommendations? | "similar products", "similar tickets" | a trade-off between accuracy ↔ latency; a vector index instead of a full scan |
| **edf / fixed-priority** | hard deadlines of periodic tasks, preemption? | control systems, SLA in ms | priority inversion; EDF is unstable under overload |
