---
name: data-engineering
description: Use for data pipelines — batch, CDC, streaming, idempotency, backfill, contracts, orchestration, dbt.
metadata:
  review: "2027-10-17"
  catalog: "Use when building and maintaining data pipelines — the data lifecycle, ingestion (batch, CDC, streaming), idempotency, backfill, late data, data contracts, orchestration (Airflow, Dagster), dbt, file and table formats, reverse ETL, pipeline tests. Not for analysis (data-analysis) or choosing a data architecture (arch-quality-attributes)."
  keywords: "nightly job, incremental load, since the last run, duplicates after a failure, backfill, recompute months, rebuild the pipeline, data warehouse, idempotent load"
---

# Data engineering

The goal is to deliver **reliable data on time** to those who use it (analytics, applications, models).
Choosing the architecture (warehouse, lakehouse, OLTP vs OLAP, ETL vs ELT, CDC, batch vs streaming): arch-quality-attributes,
`data-architecture.md`. Quality, lineage, catalog, masking and law: `references/quality-management-and-compliance.md`.

## Ingestion
| Method | When | Note |
|---|---|---|
| full batch | small dictionary tables | simple, but expensive as they grow |
| incremental batch (by timestamp or key) | most tables | deletes in the source are invisible without a "deleted" marker; the source's clock must be reliable |
| CDC from the database log (e.g. Debezium) | near-real-time changes, with deletes | access to the replication log, operational cost; the source's internal schema becomes a dependency |
| domain events from a broker | integration with applications (be-messaging-outbox) | the best contract — an event designed for publication |
| APIs and files from partners | external data | limits, pagination, retries, validation on input — data from outside is untrusted |

## Pipeline design — rules
1. **Idempotency**: re-running for the same period gives the same result — writing by overwriting a partition
   or `MERGE` by key, not appending. Without it every retry creates duplicates.
2. **Processing by time partitions** (e.g. a day) with a date parameter, rather than "since the last time" held in the job's memory
   — then a **backfill** (recomputing history after a fix) is a run for a range of dates.
3. **Late data**: a recomputation window (e.g. the last 3 days) or an event timestamp vs a processing timestamp
   distinguished in the model.
4. **Schema evolution**: additive changes are safe; removing a column or changing its type is a breaking change —
   a **data contract** with the source (schema, field semantics, frequency, owner, how changes are announced), checked
   in the producer's CI, like an API contract (be-api-design).
5. **Declarative where possible**: SQL and configuration instead of procedural code for transformations; code (Python,
   Spark) for what SQL cannot express.
6. **A small blast radius**: one task = one step with a clear input and output; a failure stops the dependents and does not
   publish partial results (writing to a temporary table and an atomic swap).
7. **Cost**: partitioning and clustering tables by filter columns, reading only the needed columns, a query
   cost limit in the warehouse (ops-finops).

## Orchestration
- Tools: Apache Airflow (a DAG in Python; in version 3, among other things, DAG versioning and scheduling based on
  data assets), Dagster (data assets instead of tasks), Prefect, cloud services (Step Functions, Data Factory,
  Workflows); Luigi — older. A simple schedule (cron, a Kubernetes job) is enough for a few independent
  tasks.
- Every task: retries with a back-off, a time limit, an alert to the owner, a freshness agreement (a data SLA: "the orders
  table ready by 6:00"), dependencies through data, not through the start time.
- The orchestrator does not do heavy work itself — it delegates it to an engine (a warehouse, Spark, a container).

## Transformations: dbt and layers
- **Layers**: raw (a copy of the source, unchanged) → cleaned and unified (types, names, deduplication) → business
  models (facts and dimensions, metrics) → serving (a departmental data mart, views for BI). The same ideas
  appear as bronze/silver/gold in a lakehouse.
- **dbt**: models as a `SELECT` in the repository, dependencies through `ref()`, sources with freshness tests, data tests
  (`unique`, `not_null`, relationships, accepted values), snapshots for change history (SCD2), documentation and a lineage graph
  generated from the project. Review in a PR, run in CI on a data sample.
- Modelling: a star schema for analytics (`data-architecture.md`), normalisation in source systems,
  denormalisation in the serving layer.

## Storage: formats
- Columnar analytical files: **Parquet** (the default), ORC; row-based with schema evolution support for transfer
  and streams: **Avro**; CSV and JSON only at the input and output of an exchange.
- Table formats in a lakehouse: Apache Iceberg, Delta Lake, Apache Hudi — ACID transactions on files, schema evolution,
  time travel. The choice depends on the engines that are to read the data.
- Warehouses and engines: BigQuery, Snowflake, Redshift, Databricks, ClickHouse; distributed processing: Spark.

## Serving and reverse ETL
- Data for BI through a semantic layer (one definition of a measure — data-analysis), for applications through an API or
  materialised tables with a contract, for models through a feature store.
- **Reverse ETL**: results from the warehouse (segments, a risk score, customer revenue) sent to operational tools
  (CRM, marketing, support). The same rules as in a pipeline: idempotency, the recipient's API limits, GDPR consent for the purpose
  of processing.

## Pipeline tests
- **Unit**: transformation logic on small, hand-prepared data with an expected result (qa-spec-first-testing).
- **Data tests** on every run: schema, key uniqueness, missing values, ranges, relationships, the row count
  against the previous day (a deviation above a threshold = an alert or a halt).
- **Integration and end-to-end** on a test environment with a data sample; a **smoke** test after deployment; a **load** test
  when the scale changes (qa-performance-testing).

## Data for an AI agent (text-to-SQL)
Before an agent starts calculating on the warehouse, prepare facts about the pitfalls and put them into the business dictionary in the prompt
(in a fixed order — fixed text yields cache hits):
- NULL keys in the fact table that an `INNER JOIN` silently drops (part of the revenue vanishes from the result);
- an incomplete last period in the data (a drop that is not a drop) — the date up to which the data are complete;
- tables with a version history (SCD type 2) — without a "current version" filter entities are counted twice;
- terms without a definition ("best store") → the agent asks instead of guessing.
You measure the facts from the data with a query, you do not enter them from memory. Security of SQL from a model: sec-llm-security.

## Checklist
- [ ] the pipeline idempotent, by time partitions, with a backfill over a range of dates
- [ ] a data contract with the source; a breaking change detected in CI
- [ ] orchestration with retries, a time limit, an alert and a freshness SLA
- [ ] data tests on every run; partial results are not published
- [ ] format and partitioning matched to the queries; cost monitored

## Sources
- J. Reis, M. Housley, *Fundamentals of Data Engineering* (2022) — the lifecycle and the "undercurrents"; M. Kleppmann,
  *Designing Data-Intensive Applications*; the Apache Airflow, dbt and Apache Iceberg documentation
- [roadmap.sh — Data Engineer](https://roadmap.sh/data-engineer)
Described in our own words.
