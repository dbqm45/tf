# Data architecture: consistency, kinds of databases, analytics and processing

## Guarantees and trade-offs
- **ACID** (atomicity, consistency, isolation, durability) — transactions in one relational database. The isolation level
  matters: the default "read committed" in PostgreSQL does not protect against every anomaly — "no more than N" rules require
  a lock, a constraint or `SERIALIZABLE` (be-database: transactions).
- **CAP**: during a network partition a distributed system chooses between consistency and availability. **PACELC** adds that
  even without a partition you must choose between latency and consistency — a more frequent, everyday trade-off.
- **BASE** (basically available, soft state, eventual consistency) — typical for distributed systems and many NoSQL
  databases. **Eventual consistency** requires design: what the user sees in the meantime (read-your-writes, monotonic
  reads), how you resolve conflicts (versions, last write wins — with data loss, merging).
- There are no ACID transactions between services: an outbox and idempotent consumers (be-messaging-outbox), a saga with compensations
  (ddd-tactical-design), CQRS with a read model updated by events.

## Kinds of databases — the choice
| Kind | Model | Good for | Note |
|---|---|---|---|
| relational (PostgreSQL, MySQL, SQL Server, Oracle) | tables, SQL, transactions | the default choice for business data | JSONB in PostgreSQL covers many "document" needs |
| document (MongoDB, Couchbase) | JSON documents | data with a variable structure read as a whole | relations and multi-document transactions are more expensive |
| key–value (Redis, DynamoDB) | key → value | cache, sessions, counters, a very large scale of simple reads | queries only by key (or designed indexes) |
| wide-column (Cassandra, ScyllaDB) | rows with many columns, partitions | huge write volumes, time series | the data model designed up front for the queries |
| graph (Neo4j, Neptune) | nodes and edges | multi-level relations (recommendations, networks, ReBAC permissions) | |
| time series (TimescaleDB, InfluxDB, Prometheus) | a measurement over time | metrics, IoT, telemetry (e.g. EV chargers) | retention and aggregation over time |
| search (Elasticsearch, OpenSearch) | an inverted index | full-text search, faceted filters | not as the source of truth |
**Several databases in one system** (polyglot persistence) only for a reason — each one is an operating cost, backups, monitoring
and skills. By default one relational database plus a cache.

## Analytics: OLTP vs OLAP
- The transactional database (OLTP) serves the application; analytical queries (OLAP) on it slow production down. Analytics
  in a separate store: a data warehouse (BigQuery, Snowflake, Redshift, ClickHouse) or a lakehouse (columnar files
  in an object store + a table format, e.g. Apache Iceberg or Delta Lake).
- Warehouse modelling: the **star schema** — a fact table (events, measures) and dimension tables (who, what, when,
  where); the snowflake — normalized dimensions. Dimension change history: SCD type 2 (a new row with a validity period).
- **ETL** (transforming before loading) or **ELT** (loading raw data, transformations in the warehouse,
  e.g. dbt) — ELT is more common today. Personal data: minimization and pseudonymization before it reaches analytics (GDPR).
- **CDC** (capturing changes from the database log, e.g. Debezium) instead of periodic full dumps; domain events
  as a better contract than the internal table schema (ddd-context-mapping: Published Language).

## Processing big data
- **Batch**: MapReduce (Hadoop's historical model: mapping and reducing distributed across a cluster), today usually Apache
  Spark (in-memory processing, SQL, DataFrame) or the warehouse engine.
- **Streaming**: Kafka Streams, Apache Flink, Spark Structured Streaming — when the result is needed in seconds (fraud
  detection, alerts, live counters). Time windows, late events, exactly-once vs at-least-once.
- First check whether the data is really "big": many workloads fit in one database or warehouse without a Spark
  cluster (KISS, cost — ops-finops).

## Sources
- M. Kleppmann, *Designing Data-Intensive Applications* (2017); D. Abadi — PACELC (2012);
  R. Kimball — dimensional modelling
- [roadmap.sh — Software Architect](https://roadmap.sh/software-architect) (ACID, CAP, CQRS and eventual consistency,
  NoSQL, warehouses, ETL, Hadoop, Spark, MapReduce)
Described in our own words.
