# The deployment platform for an MVP

Choosing the hosting is part of the stack decision (`stack-decision.md`, the platform section). Facts about platforms (features,
statuses, limits, prices) change within weeks — always from a primary source with a check date
(core-source-research), never from memory.

## 1. Hard filters (they reject without scoring)
- the stack's runtime unsupported (the language version, the framework adapter);
- persistent connections (WebSocket), background processes or long tasks required → platforms that are serverless only drop out;
- compliance requirements (the data region, e.g. the EU) impossible to meet.

## 2. Five criteria (Pass / Partial / Fail)
| Criterion | Weight | Question |
|---|---|---|
| a CLI for full operation | high | deployment, rollback and logs without a web panel? |
| a managed service instead of raw machines | high | who patches the system, scales it, makes backups? |
| a deterministic, scriptable deployment | high | one command with an exit code that the agent and CI can check? |
| documentation readable for the agent | medium | markdown, `llms.txt`, current examples for the project's version? |
| an MCP server or another integration with the agent | low | it settles ties |
For every feature a status: GA / beta / preview / regionally limited + a check date. A feature in beta is
not an argument for choosing it for production.

## 3. Interview (yes / no / don't know)
Persistent connections? Cost or convenience? A platform known to the team? Global reach? The database and storage from one
provider? The answers change the criteria weights, they do not exclude (the exception: persistent connections → a hard filter).

## 4. Candidates and the operational story
Three candidates, the decision resilience test on the leader (arch-architect-practice). Then the "operational story" —
one concrete answer per axis:
| Axis | A concrete answer |
|---|---|
| a preview per PR (and its protection against public access) | |
| secrets: where, who reads them, how to rotate | |
| rollback: the command, the time, caveats for database migrations | |
| what requires a human (accounts, domains, payments, production secrets) | |
| logs for the agent, read-only (CLI or MCP) | |

## 5. First steps and the signal to change the decision
- You check the "first steps" (CLI commands, the framework adapter) against **the project's version** — platform adapters and CLIs
  change between major versions; a general guide is often outdated.
- You plan the first deployment per ops-release-engineering ("First deployment").
- Record the signal to change the decision: what will invalidate it after leaving the MVP (recurring jobs, long tasks, a dedicated
  database, global traffic, the cost at N users).

## Example
SvelteKit + PostgreSQL, a team of 2, an MVP in the EU. Filter: WebSockets needed for notifications → a serverless-only platform
drops out. Candidates A (PaaS with containers, a full CLI, Pass×4), B (serverless + an external WebSocket
service, Partial), C (a VM with a panel, Fail on the managed service). The resilience test on A: the pre-mortem reveals no
database backup on the basic plan → recorded as a known limitation + the task "a nightly backup to storage". The operational
story of A: a preview per PR with a password, secrets in the platform's store (only the runtime reads them), rollback with a command
to the previous release (~1 min, expand–contract migrations), a human creates the account and the domain, the agent reads logs through
the CLI read-only.
