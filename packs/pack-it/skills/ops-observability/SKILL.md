---
name: ops-observability
description: Use for logs, metrics, tracing, alerts and dashboards (OpenTelemetry, Prometheus, Grafana).
metadata:
  review: "2027-04-17"
  catalog: "Use for logging, metrics, tracing, healthchecks, alerts and dashboards (OpenTelemetry, Prometheus, Grafana). Not for debugging business logic or CI pipelines."
  keywords: "po wdrożeniu, regresja wydajności, opóźnienia wzrosły, metryki biznesowe, adnotacje wdrożeń, alerty, dashboard, health zwraca 200, kontener up a nie odpowiada, sonda syntetyczna, synthetic monitoring, wygasł token, bot nie odpowiadał, after a deployment, performance regression, latency went up, business metrics, deployment annotations, alerts, health returns 200, container up but not responding, synthetic probe, token expired, the bot did not respond"
---

# Observability

## Logs
- Structured (JSON), one object per event: `timestamp`, `level`, `message`, `service`, `trace_id`, context.
- Levels: `error` = needs action, `warn` = unusual but handled, `info` = business events, `debug` = disabled in production.
- Never: passwords, tokens, full card numbers, full personal data. Mask them.
- Log an error once, where it is handled — not at every level of the stack.

## Metrics (RED + USE)
- Services: **R**ate, **E**rrors, **D**uration (a histogram, percentiles p50/p95/p99) per endpoint.
- Resources: **U**tilization, **S**aturation, **E**rrors (CPU, memory, the connection pool, queues).
- Low-cardinality labels — never `user_id` or a full URL as a label.

## Tracing
- OpenTelemetry; context propagation (`traceparent`) over HTTP and queues.
- `trace_id` in every log, to link logs with traces.

### An AI agent and post-incident investigation
- **The agent's SLO:** from OpenTelemetry you get only the availability and latency of a call. The application adds the rest with one
  stable record at the end of the task: the end state (also "rightly refused" and "handed over to a human" — neither a success
  nor a failure), the task class, the number of steps, human intervention, the version when reading and writing working memory.
  You compute the SLO from this record, not from the trace backend (span names and attribute types change); attribute names
  per the OpenTelemetry GenAI conventions where they exist (check the version before use).
- **The reason a tool call was rejected is returned by the tool server** (bad structure / bad value / internal error): a tool
  failure → an alarm to the dependency owner, a wrong call by the agent → a ticket for the agent team.
- **A shared entity model for investigation:** most of the root cause analysis time goes into reconstructing the links between
  tools that name the same thing differently. An entity is created only after validation in one authoritative catalog
  (no generic "service" type that means four things); the ontology as code (PR, tests, versions); the model's output
  restricted to enums and types; a slow source degrades the graph but does not block it. The correlation engine **proposes
  chains with evidence and confidence** (e.g. "deployment → error in the logs" within a time window), it does not issue verdicts. From the incident
  channel you record the reasoning (rejected hypotheses, what worked, who knew) — the postmortem as data
  (ops-sre-incidents). Changes proposed by agents are approved by a human.

## Healthchecks
- `/health/live` — the process is alive (no dependencies).
- `/health/ready` — ready for traffic (database, cache reachable). The orchestrator routes traffic only to "ready".
- **An end-to-end synthetic probe:** a healthcheck and the container status do not prove that the service does its job (an expired token
  can push every message into an empty error-handling branch while `/health` returns 200). Periodically (e.g. every
  hour) you send a real request through the whole pipeline, from input to response, with an assertion: the response is non-empty,
  matches the schema, arrives within the SLO time. A probe failure is an alert. The probe has a separate test account and a marker, so that
  it is not counted in business metrics. This applies especially to AI agents and integrations with tokens that expire.

## Alerts
- Alert on symptoms the user feels (SLO: error rate, p95 latency), not on every cause.
- Every alert: a threshold, a duration, a link to the runbook (docs-tech-writing), an owner.
- An alert nobody responds to — remove it or fix it.
- Deployments as annotations on dashboards: a "before / after" comparison (errors, p95, a key business action, e.g. the number of
  orders) during the first minutes after a release; a latency jump from 200 ms to 5 s without errors is also an outage.

## Resources that grow slowly (disk, certificates)
Outages "out of nowhere" most often have a cause that grew for weeks. You alarm on the **trend**, not only at 100%.
- **Disk** (nodes, volumes, databases): a warning threshold and an alert from the fill-up forecast (`predict_linear`), also
  for Kubernetes volumes and inodes.
- **Log rotation** configured and checked: Docker `--log-opt max-size=… max-file=…` (the `json-file` driver),
  kubelet `containerLogMaxSize`, `logrotate` on machines; temporary files, old backups and images cleaned up by a job
  with an alert when the job stops working. A pod in Kubernetes has `ephemeral-storage` in requests/limits.
- **TLS certificates**: automatic renewal (cert-manager, ACME) **and** an independent measurement from outside (blackbox_exporter),
  because the automation breaks too. Also cover internal certificates (mTLS,
  Kubernetes webhooks, databases, queues). The validity of public certificates is shrinking (CA/B Forum: 200 days from 15.03.2026,
  100 days from 2027, 47 days from 2029) — manual renewal stops being realistic.
- Other counters with an end date: service account tokens and keys, domains, licences, plan limits (ops-secrets-identities).

## The cost of telemetry
- First establish which questions the telemetry must answer, then cut. Every sampling or data-dropping rule
  is a recorded decision — cutting "blindly" leaves blind spots exactly where they will be needed during an incident.
- A pipeline in the OpenTelemetry Collector: filtering and dropping noise, parsing into a structure, masking personal
  data, trace sampling (e.g. keep all with an error and all slow ones, a sample of the rest), aggregation at ingestion.
- A high-cardinality label (user ID, full URL) only when it drives an alert or a decision.
- Low-value data to a cheap object store instead of an indexed backend; old data rolled up.
- One collector per layer — no collecting the same data twice; scrape intervals matched to the needs.
- Sources (devops.com): [The Green Side of Observability](https://devops.com/the-green-side-of-observability-why-less-data-can-mean-more-insight/),
  [Observability's Gaslighting Problem](https://devops.com/observabilitys-gaslighting-problem-send-less-data-isnt-a-strategy/),
  [Maximize Telemetry Data Value With Observability Pipelines](https://devops.com/how-to-maximize-telemetry-data-value-with-observability-pipelines/)

## Security signals
Application logs and metrics are also evidence. It is worth alarming on (conclusions from Huntress analyses):
- **the application process starts a child process** (a shell, `curl`, an installer) — a typical trace of an RCE-type vulnerability;
- new cron entries, systemd services or scheduler tasks that the pipeline did not add;
- sustained, unusual CPU load (cryptocurrency miners) and connections to unknown hosts, especially long WebSockets;
- issuing or refreshing a user token from data center and PaaS address ranges, refreshing at fixed times
  (automation), an inconsistent user agent (be-auth-security).
Principles: log command lines and authentication events; keep logs off the machine (attackers delete local logs
and shell history); retention long enough to answer whether someone had access. An agent that notices such
signals reports them to a human (core-agent-security).

## Example
**Situation:** "Alerts for `checkout-api`; SLO: 99.5% of requests without 5xx." **Result** (a Prometheus rule):
```yaml
- alert: CheckoutApiHighErrorRate
  expr: sum(rate(http_requests_total{service="checkout-api",status=~"5.."}[5m])) / sum(rate(http_requests_total{service="checkout-api"}[5m])) > 0.005
  for: 10m
  labels: { severity: page, team: checkout }
  annotations: { runbook_url: "https://wiki.acme.example/runbooks/checkout-api#5xx-errors" }
```
A symptom from the SLO instead of a cause, a duration, an owner and a runbook; p95 is a second alert.
More examples: `references/examples.md`.

## Checklist for a new service
- [ ] structured logs with trace_id
- [ ] RED metrics
- [ ] live/ready healthcheck
- [ ] at least one SLO alert with a runbook
- [ ] authentication events and application child processes logged off the machine
- [ ] an alert from the disk fill-up forecast, log rotation checked
- [ ] an independent measurement of certificate expiry (21 and 7 days)
- [ ] deployments as annotations on dashboards

## Sources
- [10 Minor DevOps Mistakes That Can Cause Major Production Issues](https://medium.com/coinmonks/10-minor-devops-mistakes-that-can-cause-major-production-issues-191d141e7686) — Pawan Natekar, 2026 (disk, certificates, monitoring after a deployment); metrics: the node_exporter, blackbox_exporter, cert-manager and Kubernetes documentation.
