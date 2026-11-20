# Data structures hidden in requirements

| id | Matching question | Signals | Pitfalls |
|---|---|---|---|
| **priority-queue** | do we keep choosing the next most important element, and the priorities change? | urgency, a waiting queue, "VIP first", a reserve list | changing the priority of an element in the queue (decrease-key); fairness (starvation) |
| **selection / percentiles** | top-k, median, percentile without a full sort? | "the 10 best", SLA p95, ranking | approximate aggregates in a stream (t-digest) |
| **trie / prefixes** | search by prefix, suggestions? | autocomplete, codes, hierarchical numbering | usually a database/search engine index is enough |
| **b-tree / ranges** | range queries over an ordered key? | "from–to", paging by date | the database index does this — do not implement it |
| **segment-tree / sums over an interval** | sums/minima over intervals with frequent changes? | occupancy in a time window, limits within an interval | SQL window functions are often enough |
| **interval-tree / overlapping intervals** | do time intervals overlap; free windows? | reservations, leave, resource locks, a schedule | half-open intervals `[from, to)`; time zones; in the database: an exclusion constraint on ranges — the Availability archetype |
| **kd-tree / nearest point** | nearest points in several dimensions? | "the nearest service technician", search within a radius | weakens with many dimensions; a geo extension in the database |
| **point-location** | in which zone/area does a point lie? | delivery zones, regions, geographic tariffs | geometric types in the database instead of your own code |
