# Hosting an MVP — choosing the deployment platform

Part of the stack decision (arch-tech-selection, step 8). Platform offers, limits and prices change from month to month:
every fact in the comparison carries its primary source (the provider's docs or pricing page) and the date it was checked.

## 1. Questions before any comparison
Ask the human; record yes / no / don't know:
- Does the app hold **long-lived connections** (WebSockets, server-sent events), run background workers or tasks longer
  than a few minutes?
- Which matters more right now: lowest cost, or least operational work?
- Has the team deployed to any of the candidates before?
- Will users be spread across continents in the first year?
- Should the database and file storage come from the same provider?
Long-lived connections and long tasks are a hard requirement; the other answers change the weights.

## 2. Hard filters
Reject a platform without scoring when:
- it does not support the runtime or version the project uses;
- the app needs long-lived connections, workers or long tasks and the platform runs only short request-scoped functions;
- it cannot keep the data in the required region.

## 3. What to compare
Score each candidate as meets / partly / does not meet, with a source and a date:

| Criterion | What "meets" looks like |
|---|---|
| Full operation from the command line | deploy, rollback, logs, environment variables and scaling without a web console |
| Managed building blocks | managed database, storage, TLS and domains instead of raw virtual machines to patch |
| Repeatable deploys | one scripted command, a non-zero exit code on failure, the same result from CI and a laptop |
| Docs an agent can read | current, versioned documentation in text form; CLI help that matches it |
| Agent tooling | an official API or MCP server for read-only status and logs — a tie-breaker, low weight |
| Cost at expected load | the price at launch and at 10× users, including egress and database size |

Record the maturity of each feature used (generally available / beta / preview / limited regions). A beta feature is not
an argument for production.

## 4. Shortlist and challenge
Keep three candidates. Challenge the leader before recording it — devil's advocate, pre-mortem, unknown unknowns
(arch-architect-practice, `.claude/skills/arch-architect-practice/references/decision-resilience-test.md`).

## 5. How we will operate it
Write concrete answers, not "supported":
- **Preview environments** — is there one per pull request, and who can open it (protect it if it holds real data)?
- **Secrets** — where they live, who and what can read them, how they are rotated.
- **Rollback** — the command, how long it takes, and what happens to the database: migrations follow expand / contract so
  that the previous release still runs against the new schema (ops-release-engineering).
- **Steps that need a human** — accounts, billing, domains and DNS, production secrets.
- **Logs and metrics for the agent** — read-only access, so the agent can diagnose without deploy rights.

## 6. First deploy and the signal to revisit
Check the first steps against the version the project actually uses; do the first deploy by ops-release-engineering.
Write down what would make the choice worth revisiting: scheduled jobs, long-running tasks, a dedicated database, global
traffic, or monthly cost above an agreed figure at N users.

## Example
**Situation:** a team of three builds a live auction MVP (Phoenix with LiveView, PostgreSQL), customers in the EU.
- Questions: long-lived connections — yes (LiveView keeps a socket per user); least operational work matters more than cost.
- Hard filters: two function-only platforms rejected (no persistent sockets); one provider rejected (no EU region for its
  managed database).
- Shortlist: a container platform with a managed PostgreSQL, a PaaS with an EU region, a managed Kubernetes service.
- Comparison: the container platform meets CLI, repeatable deploys and docs; managed database backups only on the paid tier
  (source: pricing page, checked 2026-11-20).
- Pre-mortem: "A bad migration on auction day locked the bids table and rollback did not help" → expand/contract migrations
  and a tested restore before launch.
- Decision: the container platform. Known limitation: daily backups require the paid database tier — budgeted. Revisit
  when concurrent sockets exceed the plan's limit or a second region is needed.
