# Performance antipatterns (the Azure Architecture Center catalogue)

| Antipattern | Symptom | How to detect | Fix |
|---|---|---|---|
| **Busy Database** | the database runs logic (procedures, formatting, processing large sets) and becomes a bottleneck | high database CPU at moderate traffic, long procedures in `pg_stat_statements` | move the computation to the scalable application layer; the database for storage and queries |
| **Busy Front End** | heavy tasks in the process serving requests (also in background threads of that process) slow down all requests | the latency of all endpoints grows while one heavy task runs | a queue and separate worker processes, `202` and a status resource (be-api-design) |
| **Chatty I/O** | many small requests to the database, a service or files instead of one | the number of queries per request, N+1, traces with dozens of short calls | bulk queries, batches, responses with the needed data (be-database) |
| **Extraneous Fetching** | fetching more data than needed (all columns, the whole collection, filtering in the application) | large responses, transfer from the database disproportionate to the result | column projection, filtering and pagination in the database, DTOs for reads |
| **Improper Instantiation** | a new HTTP client, database connection or costly object created on every request | exhausted sockets or connections, a growing `TIME_WAIT`, creation time in the profile | one shared client, connection pools (`backend-performance-checklist.md`) |
| **Monolithic Persistence** | one database for data with extremely different patterns (transactions, logs, analytics, files) | resource contention, slow transactional queries during reports | split the stores by access pattern (replicas, a warehouse, an object store) — only from measurement |
| **No Caching** | the same, rarely changing data read every time from the source | repeated identical queries in the logs | a cache with a TTL and invalidation; beware of a query stampede |
| **Noisy Neighbor** | one tenant or process consumes disproportionately many shared resources | per-tenant metrics, spikes for everyone when one is active | limits per tenant, priority queues, isolation (bulkheads, separate pools, Deployment Stamps) |
| **Retry Storm** | many clients retry without a gap and a limit, finishing off a recovering service | traffic grows after an outage instead of dropping | exponential backoff with jitter, a retry budget, a circuit breaker, `Retry-After` |
| **Synchronous I/O** | a thread blocked for the duration of an input–output operation | an exhausted thread pool at low CPU | an asynchronous API (default in Node; in Java virtual threads or reactive), timeouts |
You confirm every antipattern with a measurement (a profile, traces, metrics) before the fix and after it (qa-performance-testing).

## Sources
- [Microsoft — Performance antipatterns for cloud applications](https://learn.microsoft.com/en-us/azure/architecture/antipatterns/)
- [roadmap.sh — System Design](https://roadmap.sh/system-design) (performance antipatterns)
Described in our own words.
