# Database performance in production (PostgreSQL as the example)

First a measurement, then a change. The order that usually pays off: the query and the index → the connection pool → a cache → read
replicas → partitioning → sharding (last and rarely).

## The connection pool
- Every connection to PostgreSQL is a process with memory. More connections ≠ more throughput — above a certain number
  contention for the CPU, locks and I/O grows.
- A starting point for the application pool (the HikariCP wiki on pool sizing): **the number of database cores × 2 + the number of disks**
  effectively serving I/O, then tuning on a load test (qa-performance-testing). Usually small pools
  (a dozen to a few dozen) and a queue in the application work better than hundreds of connections.
- The sum: **the pool size × the number of application instances (also with autoscaling and a rolling deployment) ≤ `max_connections`**
  with headroom for administration and migrations. With many instances or serverless functions — a pooling proxy
  (PgBouncer in transaction mode; then no session state in the connection: check prepared statements and `SET`
  in the version's documentation).
- Set: a timeout for waiting for a connection from the pool (short — a fast error is better than an endless queue), a maximum
  connection lifetime (shorter than the network and database limits), a query timeout (`statement_timeout`) and an idle-in-transaction
  timeout (`idle_in_transaction_session_timeout`).
- Pool metrics in monitoring: active, idle, waiting, wait time (ops-observability).

## Slow queries
- `log_min_duration_statement` (e.g. 250–500 ms) logs slow queries; the `pg_stat_statements` extension gives
  a ranking by **total** time (a frequent moderately slow query costs more than a rare very slow one);
  `auto_explain` records the plans of slow queries.
- `EXPLAIN (ANALYZE, BUFFERS)` on production-scale data: a sequential scan of a large table, a bad row count estimate
  (stale statistics → `ANALYZE`), sorting on disk, nested loops on large sets.
- Indexes: the column order in a composite index (equality before range), partial indexes (`WHERE status = 'open'`)
  and covering ones (`INCLUDE`); every index slows writes — remove unused ones (`pg_stat_user_indexes`).
- ORM: turn on SQL logging in tests and look at the number of queries per request (N+1); fetch only the needed columns
  (`data-access-patterns.md`: reads through SQL and DTOs).

## Maintenance
- **VACUUM and autovacuum**: updates and deletes leave dead rows; autovacuum must keep up (for large,
  frequently changed tables per-table settings). Symptoms: a growing size of the table and indexes, slower scans,
  transaction ID wraparound warnings — the last one is urgent.
- Data clean-up: retention (logs, events, sessions, the outbox after sending) deleted in batches or by detaching
  partitions, not with one huge `DELETE`.

## Schema and types vs performance
Some popular advice (also in system-design-primer) comes from MySQL 5.x. Check it for your database and version.
- Money as `numeric` / `DECIMAL` (or an integer number of the smallest unit), never as a floating-point number.
- Identifiers and counters that may grow, as `bigint`. A signed `integer` ends at ~2.1 billion,
  and changing the type of a large table is an expensive migration.
- `NOT NULL` where a value is required. It is mainly about correctness, and the query planner also
  uses the constraints.
- Large files (images, documents) in an object store, and in the database only their address and metadata.
- **PostgreSQL**: `text` and `varchar(n)` are equally fast, and `char(n)` is not faster (it pads with spaces;
  the documentation advises against it). Express a length limit with a constraint, when it follows from the domain. The advice "`CHAR` instead of `VARCHAR`
  for speed" concerns old MySQL engines.
- **MySQL 8.0** no longer has the query cache. Keep the result cache in the application (be-api-design,
  `backend-performance-checklist.md`).
- A large import: disable or drop non-key indexes, load the data (`COPY` in PostgreSQL), rebuild the indexes
  and run `ANALYZE`. Every index speeds up reads, but slows writes and takes memory, so keep only
  those the queries use.
- Hot columns or rows in a separate, smaller table fit in memory. You do it only after a measurement.

## Scaling reads and data
- **Read replicas**: they relieve reports and lists. Replica lag means the user may not see
  their own write — after a write read from the primary (read-your-writes) or wait for the WAL position. A replica is also
  redundancy, but not a backup (a wrong `DELETE` replicates immediately — ops-sre-incidents).
- **Denormalization and materialized views** for read-heavy workloads (dashboards, search): refresh
  scheduled or through events; the normalized model stays the source of truth (ddd-tactical-design: read models, CQRS).
- **Partitioning** (declarative, e.g. by date) for very large tables with a natural time key: fast
  deletion of old data, smaller indexes. Queries must filter by the partition key.
- **Sharding** (splitting data across many databases) only when vertical scaling, replicas and partitioning are not
  enough: it complicates transactions, cross-cutting queries, migrations and operations. A shard key from the domain
  (the tenant, the region); the decision in an ADR with alternatives.

## Sources
- PostgreSQL documentation: Routine Vacuuming, `pg_stat_statements`, `auto_explain`, Table Partitioning,
  Runtime Config (Logging, Client Connection Defaults), Character Types, `COPY`; the HikariCP wiki "About Pool Sizing";
  MySQL 8.0 Reference Manual (removal of the query cache)
- [system-design-primer](https://github.com/donnemartin/system-design-primer) — SQL tuning (CC BY 4.0)
- [roadmap.sh — Backend Performance Best Practices](https://roadmap.sh/backend-performance-best-practices) (Databases)
Described in our own words.
