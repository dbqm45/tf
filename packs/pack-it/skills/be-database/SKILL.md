---
name: be-database
description: Use for a relational database — schema, migrations, indexes, SQL/ORM queries, transactions, N+1, performance and scaling.
metadata:
  review: "2027-10-17"
  catalog: "Use when working with a relational database — the schema, migrations, indexes, SQL/ORM queries, transactions, query performance (N+1), PoEAA patterns (Unit of Work, Identity Map, Data Mapper). Not for designing endpoints (be-api-design) or the database infrastructure."
  keywords: "diagram encji, ERD, erDiagram, diagram bazy danych, schemat bazy jako diagram, blokada optymistyczna, blokada pesymistyczna, blokady w PostgreSQL, wyścig o ostatnie miejsce, dwóch użytkowników kupuje to samo, nadpisują sobie edycję, SELECT FOR UPDATE, wersja wiersza, zakleszczenie, write skew, entity diagram, database diagram, database schema as a diagram, optimistic locking, pessimistic locking, locks in PostgreSQL, a race for the last seat, two users buy the same item, they overwrite each other's edits, row version, deadlock, database migration, index, N+1 query"
---

# Database

## Migrations — safe in production
1. Every schema change = a migration in the repo. Never manual changes on the database.
2. Migrations are **backwards compatible** with the previous version of the application (deploy and rollback without downtime).
3. Incompatible changes through expand → migrate → contract (a backfill in batches, removing the old column in a separate
   release); indexes on large tables `CONCURRENTLY`, `NOT NULL` on a large table not in one step.
4. Every migration has a sensible `down` or is explicitly marked as irreversible.

## Queries
- Always parameterized. String concatenation in SQL = a critical bug.
- Select the needed columns, not `SELECT *` in production code.
- Detect N+1: a loop with a query inside → a join / `IN (...)` / eager loading.
- Logic and data access patterns (a transaction script vs a domain model, Active Record vs Data Mapper, Unit of Work,
  Identity Map, lazy loading, an ORM for writes and SQL for reads, DTOs and mappers): `references/data-access-patterns.md`.
- Every query by a column in `WHERE`/`JOIN`/`ORDER BY` on a large table has an index — check `EXPLAIN ANALYZE`.
- Performance in production (the connection pool and its size, slow queries and `pg_stat_statements`, VACUUM, replicas,
  materialized views, partitioning, sharding): `references/database-performance.md`.

## Transactions
- Operations that must succeed together, in one transaction; short transactions, without network calls inside.
- Races — choosing the lock, in order:
  1. whether one atomic query (`UPDATE … SET available = available - 1 WHERE id = … AND available >= 1`, checking the number
     of changed rows) or a constraint (`UNIQUE`, `EXCLUDE`) removes the window between the read and the write — then no lock;
  2. a window longer than one short transaction (a form, several requests) → a row version / `ETag` + `If-Match`
     (optimistically) or a lease with expiry in the application; never a transaction open for the user's thinking time;
  3. rare hits on the same row → optimistically, with a limited number of retries and jitter; a hot row →
     `SELECT … FOR UPDATE` (pessimistically);
  4. costly lost work (an external, non-idempotent effect) → a lock before the work.
  Pitfalls: deadlocks (a fixed locking order), no network calls under a row lock, `NOWAIT` or
  a wait timeout instead of hanging; a row version does not protect against *write skew* (a rule over several rows —
  Serializable isolation or locking a shared parent); a lock in Redis only for performance, for correctness fencing
  tokens.
- A bulk write with a version (`UPDATE … FROM (VALUES …) WHERE version = …`): check that the number of changed rows = the expected one;
  fewer → a conflict, roll back the whole.
- **Outbox:** a table (an id assigned at write time, a type, a payload, a status, a creation time; an index on the status and time) written in the same
  transaction as the state; cleaning up the sent ones; many pollers → `FOR UPDATE SKIP LOCKED` or a compare-and-set of the status.
- **Inbox (deduplication):** `UNIQUE(message_id)` + `INSERT … ON CONFLICT DO NOTHING` in the same transaction as the effect — not
  "check, then write". Details: be-messaging-outbox.

## Read models
Merge continuous periods and aggregate over ranges with window functions (`LAG`, `SUM() OVER`) in SQL — instead of a loop in the application.
For time ranges: range types + an exclusion constraint (PostgreSQL), when the database has them (ddd-archetypes → resource holds).
A schema per module (e.g. a separate `schema` in PostgreSQL) strengthens module boundaries in a monolith.

## Integrity
- Foreign keys, `UNIQUE`, `CHECK` in the database — not only validation in the application.
- Time in UTC (`timestamptz`), money as `numeric`/integers in the smallest unit, never `float`.

## Entity diagram (ERD)
- A diagram as code: Mermaid `erDiagram` in `docs/project/04-architecture/erd.md` (GitHub and most tools
  render it). No images from graphical tools — they cannot be reviewed in a PR or compared.
- The source of truth is the migrations, not the diagram. Preferably generate it from the schema (e.g. `prisma-erd-generator`, SchemaSpy,
  a script over `information_schema`) or check in CI that the tables from the diagram exist in the database after the migrations.
- A migration changing tables or relations updates `erd.md` in the same PR. The diagram has only domain tables,
  keys and relation cardinalities; you skip technical columns.
- With several modules a separate diagram per module (schema), plus one overview with the relations between modules.

## Checklist
- [ ] the migration backwards compatible and tested (up + down)
- [ ] no N+1, indexes for new queries
- [ ] no raw SQL with concatenation
- [ ] a change of tables or relations updated `erd.md` in the same PR
