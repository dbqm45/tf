# Backend performance checklist — before a release and in review

Based on the roadmap.sh list "Backend Performance Best Practices", with clarifications and pointers to the skills that
develop each item. The performance target follows from the SLOs and the quality attribute scenarios (ops-sre-incidents,
arch-quality-attributes). You confirm every optimization with a measurement before and after (qa-performance-testing).

## Cache
- [ ] Layers: HTTP and CDN caching for public responses (`http-in-practice.md`), a server-side cache for expensive
  computations and reads, a client-side cache only for that user's data.
- [ ] **The pattern chosen consciously**:
  | Pattern | How | When |
  |---|---|---|
  | cache-aside (lazy) | the application reads from the cache; on a miss it reads from the database and writes to the cache | the default; resilient to a cache failure |
  | read-through | the cache itself loads from the database on a miss | when a library or service provides it |
  | write-through | the write goes to the cache and the database synchronously | data read right after the write; slower writes |
  | write-behind | the write to the cache, to the database asynchronously | rarely; a risk of data loss — only for data that can be lost |
  | refresh-ahead | the cache refreshes popular keys before they expire | predictably hot data; wastes work when the prediction misses |
- [ ] **Invalidation**: a time to live (TTL) as a safeguard always, plus invalidation on change (a domain
  event → deleting the key) or a versioned key (`product:42:v17`). Record how much staleness the business accepts.
- [ ] **A query stampede** after a popular key expires: coalescing concurrent requests for the same key (single-flight),
  a random TTL jitter, earlier background refresh. The cache must not be the only path to the data — a cache failure means
  a slower system, not an outage.
- [ ] Nothing in the cache that must not be shown to another user: the key includes the tenant and the user when the data is
  private.

## Database
- [ ] A connection pool with a chosen size and timeouts; a slow query log and `pg_stat_statements`; indexes
  checked with `EXPLAIN ANALYZE`; no N+1 and no `SELECT *`; cursor pagination; maintenance (VACUUM), replicas,
  denormalization and partitioning only from measurement (be-database, `database-performance.md`).
- [ ] Loading of relations matched to the case: eager (`join`) for data always needed, lazy only when writing
  an aggregate, batch (`IN (...)`, DataLoader in GraphQL) instead of a query in a loop.

## API and network
- [ ] Request size limits, pagination, response compression, responses without unneeded fields (`http-in-practice.md`).
- [ ] Large results streamed (NDJSON, SSE) instead of building the whole thing in memory (`styles-and-communication.md`).
- [ ] **Reusable connections**: keep-alive and an HTTP connection pool for calls to other services (in Node since
  version 19 the global HTTP agent has keep-alive on by default; in Java one shared HTTP client, not a new one for
  every request).
- [ ] **Timeouts on every outgoing call** (connect and response), set from the request's time budget:
  if the user waits at most 2 s, three calls of 5 s make no sense. The remaining budget passed on
  (a deadline in gRPC, a header in HTTP).
- [ ] **Retries** only for transient errors and idempotent operations, with exponential backoff and random
  jitter, a limit on attempts and a retry budget (e.g. ≤ 10% of traffic) — otherwise retries finish off an overloaded service;
  a circuit breaker for a long-lasting dependency outage (ops-sre-incidents: designing for failure).
- [ ] Batching similar requests between services, when many small calls go to the same dependency.
- [ ] Proximity: the backend and the database in the same region and zone as most users; static assets through a CDN;
  data needed in the next step prefetched only when the probability of use is high.

## Asynchrony and scaling
- [ ] Heavy work (reports, imports, emails, file processing) in background jobs or a queue; the request returns
  `202` with a status resource (`styles-and-communication.md`); communication between services through a broker with an outbox
  (be-messaging-outbox).
- [ ] Horizontal scaling requires stateless instances (sessions and files outside the process); vertical — simpler, but with a ceiling.
  Autoscaling with an upper limit and headroom in the database connection pool (`database-performance.md`; ops-kubernetes).
- [ ] Load balancing: a least-connections or weighted algorithm for requests of different cost, readiness
  probes, graceful shutdown of instances (finish requests before closing).

## Code
- [ ] **Profiling instead of guessing**: in Java JDK Flight Recorder and async-profiler (CPU and allocation flame graphs),
  in Node `--cpu-prof` or a profile from the inspector; on data and traffic close to production. You optimize
  the critical paths and the most frequently called endpoints.
- [ ] Data structures and algorithms matched to the scale (a map instead of searching a list in a loop, streaming
  instead of loading the whole file); CPU tasks in Node outside the event loop (worker threads).
- [ ] "Rewrite in Go or Rust" or "split into microservices" are architectural decisions with a cost (the team, operations,
  the network) — only when a profile shows that the bottleneck is the language itself or the deployment boundary, and with an ADR
  (arch-tech-selection, arch-quality-attributes).

## Monitoring
- [ ] RED metrics per endpoint, resource and pool metrics, distributed traces for slow requests (ops-observability).
- [ ] **Asynchronous logging** (Logback `AsyncAppender`, Log4j2 asynchronous loggers, in Node pino with a transport
  in a separate thread) and no logging of whole request bodies on hot paths. On a buffer overflow decide consciously:
  lose logs or slow down requests.
- [ ] Performance tests regularly and a comparison with the previous result (qa-performance-testing).

## Security vs performance
Request and size limits also protect performance (OWASP API4). Authentication and authorization are not the place for
savings — cache authorization decisions only briefly and with invalidation. The list item "update dependencies": in the factory
at a human's request, as a separate task (core-stack-sync, ops-supply-chain-security).

## Sources
- [roadmap.sh — Backend Performance Best Practices](https://roadmap.sh/backend-performance-best-practices)
- Documentation: Node.js (`http.globalAgent`, keep-alive), JDK Flight Recorder, async-profiler, Logback, Log4j2, pino;
  the Google SRE Book — retry budgets and overload handling
Described in our own words.
