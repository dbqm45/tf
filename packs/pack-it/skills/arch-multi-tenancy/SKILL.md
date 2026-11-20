---
name: arch-multi-tenancy
description: Use for a SaaS for many customers — the tenant isolation model, tenant context in the request and the queue, RLS, the noisy neighbour, migrations, isolation tests.
metadata:
  visibility: name
  review: "2027-10-20"
  catalog: "Use when you design or review a SaaS serving many customers (tenants) — choosing the isolation model (silo, pool, a mixed model) with criteria, the tenant context in an HTTP request, a queue, a background job, cache and logs, isolation in the database (a tenant column with RLS in PostgreSQL, a schema or database per tenant), the noisy neighbour (limits, quotas, cost per tenant), migrations across many tenants, isolation tests as a permanent part of regression, export and deletion of a customer's data, tenant onboarding and offboarding. Not for the general schema and indexes (be-database), user login and roles (be-auth-security), GDPR (arch-privacy-compliance), the map of regulations (arch-eu-product-law) or tenant isolation in AI systems (arch-ai-solutions)."
  keywords: "multi-tenancy, multi-tenant, wielodzierżawność, najemca, tenant, tenant_id, izolacja klientów, izolacja danych klientów, firma A widzi dane firmy B, wyciek między klientami, silo, pool, bridge, baza na klienta, schemat na klienta, row level security, RLS, polityka wierszy, kontekst najemcy, kontekst tenanta w kolejce, zadanie w tle innego klienta, noisy neighbor, hałaśliwy sąsiad, limity na klienta, kwoty, koszt per klient, migracja wielu baz klientów, onboarding klienta SaaS, offboarding, usunięcie danych klienta, eksport danych klienta, reguła dla jednego klienta, fork dla klienta, konfiguracja per najemca, wersja API per klient, customer isolation, customer data isolation, company A sees company B's data, cross-tenant leak, database per customer, schema per customer, row policy, tenant context, tenant context in a queue, background job of another customer, noisy neighbour, limits per customer, quotas, cost per customer, migrating many customer databases, customer onboarding, customer data deletion, customer data export, a rule for one customer, a fork for a customer, per-tenant configuration, API version per customer"
---

# Multi-tenancy in SaaS

**The agent's role:** it matches the tenant isolation model to the requirements and makes sure the tenant context is explicit on every
path: the request, the queue, the background job, the cache, the logs, the export. A data leak between customers is a security
incident and a GDPR breach, so a test proves isolation, not a code review.

## 1. Isolation model — the choice
| Model | What the tenants share | Strength | Cost | Sensible when |
|---|---|---|---|---|
| **pool** | the application and the database; rows with a tenant column | the cheapest, one migration, easy customer onboarding | isolation depends on every query; the noisy neighbour | many small customers, no contractual requirements |
| **schema per tenant** | the application and the database server | isolation through `search_path`/permissions, easy export | migrations × the number of schemas; a limit of hundreds–thousands | tens–hundreds of medium customers |
| **silo** | nothing or only the control plane | full isolation, separate SLAs, data residency | infrastructure and operations cost × N | regulated customers, a contract requires a separate database |
| **mixed** (bridge, tiers) | the pool for the basic plan, a silo for Enterprise | the price fits the plan | two deployment and test paths | different plans with different requirements |

Criteria: the number and size of customers, contract and regulatory requirements (a separate database, a region), the cost per customer, the spread
of load, the speed of onboarding a new customer, the team to maintain it. By default: **a pool with RLS**, a silo only where
a contract or the risk requires it. You record the decision as an ADR (docs-tech-writing) with a revision criterion (e.g. "a customer > 20% of traffic").
The control plane (the tenant register, plans, customer onboarding and offboarding, per-tenant metrics) is shared
by all models.

## 2. Tenant context — explicit on every path
- **Request:** the server determines the tenant from the authenticated identity (a claim in the token, organization membership),
  never from a parameter or header given by the client without checking membership (be-auth-security).
- **Queue and background job:** the tenant identifier in the payload or header of every message; the consumer sets
  the context before the first query and clears it after the job. A job without a tenant ends with an error, not a default
  context. Jobs "for everyone" iterate over the tenant register, one context at a time.
- **Cache, files, search:** the cache key and the path in the object store start with the tenant; the search
  index filters by tenant on the server side.
- **Logs and metrics:** the tenant in every entry (ops-observability) — without it you will not compute the cost or the scope of an incident.
- You pass a context in a thread-local or async variable (`AsyncLocalStorage`, `contextvars`, `ThreadLocal`)
  consciously when moving to another thread or pool; a thread pool without clearing carries the tenant into the next job.

## 3. Isolation in the database
- **A pool in PostgreSQL:** a tenant column in every table with customer data (also in foreign keys and composite
  indexes, the tenant first), RLS with a policy comparing the column with a transaction setting
  (`set_config('app.tenant_id', …, true)` or `SET LOCAL`). Details and pitfalls: `references/rls-postgresql.md`.
- The application connects with a role without table owner privileges and without bypassing RLS; migrations run with a separate role.
- A connection pool in transaction mode: the tenant is set only for the transaction, never for the session.
- A second line of defence: the repository or ORM adds a tenant filter — RLS catches what the filter did not add.
- You mark global tables (dictionaries, plans) explicitly; the rest is per tenant by default.

## 4. The noisy neighbour and cost
- Limits per tenant: requests per second, concurrent jobs, import size, file storage (be-api-design: 429).
- Queues: fair allocation (a separate queue or a concurrency limit per tenant) instead of one FIFO.
- Cost per tenant from metrics and tags (ops-finops) — it shows when a customer should move to a silo or another plan.

## 5. Migrations and the tenant lifecycle
- Pool: one migration, but run on a large table — the expand and contract pattern (be-database).
- Schema or silo: a migration in waves (internal tenants first), migration status per tenant, resuming
  from the point of failure; the application works with the old and the new schema version during the waves.
- **Onboarding:** the tenant register, creating resources automatically (IaC for a silo), seed data.
- **Offboarding and the customer's rights:** a full export of the tenant's data in a structured format (Data Act —
  arch-eu-product-law), deletion including backups per retention (arch-privacy-compliance), proof of deletion.

## 6. Isolation tests — a permanent part of regression
- Two tenants in the test data of every integration test; for every API resource: logged in as A, a request
  for an identifier from B → 404 (not 403, so as not to reveal existence).
- An RLS test directly in the database: the application role without a tenant set sees zero rows.
- A queue test: tenant A's message handled after B's message does not see B's data.
- A cache and export test: keys and files do not cross.
- The tests in the regression suite (qa-regression) and in CI on every change; a new table without an RLS policy = a red test
  (a catalogue query: tables with a tenant column without RLS enabled).

## 7. Per-tenant behaviour without forks
A big customer wants a different rule (an extra approval step, other rounding, its own onboarding). Never answer
with a branch or a copy of the code for that customer: every fix and release would then have to be made twice.
Pick the lightest mechanism that covers the difference:
1. **Tenant configuration** — the rule is the same, only its parameters differ (approval threshold, number of
   approvers, retention days). Values live in the tenant register, are versioned and every change is audited.
2. **Feature flag per tenant** — switches on a variant that already exists in the product. Each flag has an owner
   and a removal date (or an ADR saying it is permanent) (eng-continuous-delivery).
3. **Policy per tenant** — a different rule in the domain, implemented as a strategy and picked by a factory from
   the tenant's configuration (`.claude/skills/ddd-tactical-design/references/dynamic-rules.md`). The core never
   knows customer names: `if (tenantId == "BIGCO")` in business logic is a fork in disguise.
4. **Handler per tenant** — when the whole flow differs, a registry maps the tenant (or its plan) to a command
   handler implementation, with a default handler for everyone else. The variant is tested like the core.
5. **API version per tenant** — a customer that cannot migrate yet stays on an older contract version for an agreed
   window; an adapter at the gateway translates it to the current model, so there is still one logic (be-api-design).

Rules: the tenant used to pick a variant comes from the authenticated tenant context (section 2), never from a header
or parameter the client controls. A variant is part of the product (named, tested, with an owner), not an exception
in code. When variants keep multiplying, check whether they are really separate plans or a separate bounded context
(ddd-strategic-analysis). Cloud multitenancy guidance (Azure Architecture Center, AWS SaaS Lens) also favours
configuration and feature flags over per-customer code versions [unverified: pages not read in this session].


## Rules
- The tenant context explicit and checked on the server side on every path; no context = an error, not "everyone".
- A test with two tenants proves isolation, not a code review.
- An admin panel "sees everyone" only through a separate role with an access audit (be-auth-security).
- You treat a leak between tenants as an incident (ops-security-operations) and a data breach (arch-privacy-compliance).

## Example
**Situation:** "A B2B SaaS, PostgreSQL, 300 customers in one database, a `tenant_id` column. A report from the queue showed the data
of another customer."
**Result (abbreviated):**
- Model: the pool stays (300 similar customers, no contractual requirements); an ADR with a revision criterion for Enterprise customers.
- Cause: the worker read the tenant from the session setting of a pooled connection — the previous job left a different `tenant_id`.
- Fix: the tenant in the message payload; the worker sets it with `SET LOCAL` in the job's transaction; RLS with a policy on
  `current_setting('app.tenant_id')`, the application role without bypassing RLS.
- Tests: job A after job B on the same connection; the application role without a tenant sees 0 rows; a catalogue test
  "every table with `tenant_id` has RLS".
- Incident report and breach assessment → ops-security-operations, arch-privacy-compliance.

## Checklist
- [ ] the isolation model chosen by the criteria, an ADR with a revision criterion
- [ ] the tenant from the authenticated identity; present in the request, message, job, cache, files, logs
- [ ] RLS (or a separate schema or database) and an application role that does not bypass policies; the tenant set per transaction
- [ ] limits and cost per tenant
- [ ] migrations for all tenants with resumption; export and deletion of customer data
- [ ] isolation tests with two tenants in regression and CI
- [ ] per-tenant behaviour variants as configuration, a flag, a policy or a handler, without code forks

## Sources
Described in our own words; facts and access dates in `references/rls-postgresql.md`.
