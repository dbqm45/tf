# RLS in PostgreSQL for a tenant pool — details and pitfalls

Facts checked by the `researcher` agent on 2026-10-18. The source pages were not opened from the cloud session
(proxy 403), so the verdicts rest on search engine summaries from official domains — marked [secondary].
Before a production decision check the documentation of your PostgreSQL version.

## Facts
| Fact | Source | Status |
|---|---|---|
| The table owner bypasses RLS policies by default, unless the table has `FORCE ROW LEVEL SECURITY`; a superuser and a role with `BYPASSRLS` always bypass them. | postgresql.org/docs/current/ddl-rowsecurity.html (confirmed by copies of the version 12 and 15 documentation) | [secondary] |
| RLS enabled without any policy = default deny: no visible or modifiable rows. | as above | [secondary] |
| `SET LOCAL` works until the end of the current transaction (commit or rollback); `set_config(name, value, true)` — the same. | postgresql.org/docs/current/sql-set.html; …/functions-admin.html | [secondary] |
| PgBouncer in `transaction` mode: `SET`/`RESET` marked as unsupported ("Never") — the next transaction may land on another connection; the exception are tracked parameters (e.g. `TimeZone`, `application_name`). | pgbouncer.org/features.html; pgbouncer.org/config.html | [secondary] |
| The silo, pool, bridge models; the "noisy neighbor" — one tenant's load degrades the others. | docs.aws.amazon.com/wellarchitected/latest/saas-lens/silo-pool-and-bridge-models.html | [secondary] |
| The latest released major version: PostgreSQL 18 (released 25.09.2025); PG 19 in RC1 since 15.10.2026; PG 14 support ends 12.11.2026. | postgresql.org/support/versioning/ | [secondary] |

## Pattern (a sketch)
```sql
ALTER TABLE invoice ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoice FORCE ROW LEVEL SECURITY;   -- also when the application is the owner (better: it is not)
CREATE POLICY tenant_isolation ON invoice
  USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
  WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
```
In the application's transaction: `SELECT set_config('app.tenant_id', $1, true);` before the first query.
`current_setting(…, true)` returns NULL when unset, so the comparison lets no row through.

## Pitfalls
- The application role owns the tables (migrations with the same role) → RLS does not work without `FORCE`. A separate migration role.
- `SET` (without `LOCAL`) in a connection pool → the tenant "leaks" into the next transaction of another customer.
- Views: by default they run with the view owner's permissions; from PostgreSQL 15 the `security_invoker` option
  [secondary, 2026-10-20: the CREATE VIEW man page from the postgresql15 package, the Supabase blog — postgresql.org documentation
  unavailable from the session].
- `SECURITY DEFINER` functions bypass RLS if their owner bypasses it — review every such function.
- Composite indexes with `tenant_id` first; without them the policy turns queries into a scan (be-database).

## Catalogue test (a sketch)
```sql
SELECT c.relname
FROM pg_class c JOIN pg_attribute a ON a.attrelid = c.oid AND a.attname = 'tenant_id'
WHERE c.relkind = 'r' AND NOT c.relrowsecurity;   -- has tenant_id, but RLS disabled → a red test
```
