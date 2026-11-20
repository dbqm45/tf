# SLI, SLO, SLA in practice

A three-level model (a pyramid): an **SLI** is a metric, an **SLO** is a metric with a threshold, an **SLA** is a threshold with consequences.
Each level builds on the previous one — there is no sensible SLA without an SLO, nor an SLO without a defined SLI.

## 1. Choosing an SLI
First the question: what will the user consider "working"? Only then the metric.

| Service type | Typical SLIs |
|---|---|
| API / HTTP service | availability (the share of requests without 5xx), latency (the share of requests faster than a threshold), throughput as context |
| frontend | the share of page loads without an error, Core Web Vitals (e.g. the share of visits with LCP < 2.5 s — fe-web-platform) |
| queue / asynchronous processing | freshness (the share of messages handled within N s), the share processed without an error |
| batch job | the share of runs finished before the deadline, correctness of the result |
| data store | durability, the share of successful reads and writes, latency |
| AI feature | three layers: infrastructure, inference, behavior (the skill, section 2) |

Principles:
- Write an SLI as **a ratio**: good events / all valid events × 100%. Then every SLI has the same scale
  0–100% and the same way of computing the budget.
- Measure as close to the user as possible (the load balancer, the API gateway, RUM in the browser), not in the middle of the system.
- Explicit exclusions: e.g. client-side 4xx errors, requests from probes and synthetic tests.
- Throughput (how many requests the system will handle) is usually a capacity requirement, not an SLI — it describes whether we will hold the SLO
  under load (arch-quality-attributes).
- Latency: percentiles, not the average — the average hides the tail that some users see. Put the latency threshold into the SLI
  ("a request is good when it takes < 300 ms"), so that availability and speed are counted the same way.
- 3–5 SLIs per service are enough; more dilutes attention.

## 2. The SLO specification (template)
```
Service:       orders-api
Journey:       placing an order
SLI:           the share of POST /orders requests finished with a code < 500 and in < 800 ms,
               measured at the load balancer; excluding probe and synthetic test requests
Objective:     99.9%
Window:        rolling 28 days
Budget:        0.1% of requests (with 2 million requests per 28 days ≈ 2000 bad requests)
Owner:         the orders team
Policy:        budget < 25% → only changes that improve reliability, a review of every release required
SLO review:    every quarter (does the objective still match the expectations of users and the business)
```
- **A rolling window** (e.g. 28 or 30 days) better reflects how users feel; a calendar window (a month) fits
  reports and SLAs.
- You set the objective from historical data and business needs, not "out of thin air"; you start with an objective the team meets today,
  and tighten it when the need grows.

## 3. How much that is in time
The unavailability budget in a 30-day window (43,200 minutes):

| SLO | Budget |
|---|---|
| 99% | 7 h 12 min |
| 99.5% | 3 h 36 min |
| 99.9% | 43.2 min |
| 99.95% | 21.6 min |
| 99.99% | about 4.3 min |

With a request-based SLI the budget is a number of bad requests, not minutes — a short, total outage at night uses
less of it than a long, partial one at peak hours.

## 4. Dependencies and the SLA
- A service that calls several dependencies in series has an availability no higher than the product of their availabilities:
  three dependencies at 99.9% give at most about 99.7%. A higher SLO requires redundancy, a cache, a degraded
  mode (the skill, section 8) or removing the dependency from the critical path.
- Check the providers' SLAs (cloud, payments, mail): your SLO cannot promise more than their SLA, unless you have
  a workaround. The consequence of a provider's SLA is usually service credits, not coverage of your losses.
- You set the SLA for the customer looser than the internal SLO (e.g. SLO 99.9%, SLA 99.5%) and with a clear definition of the measurement,
  the exclusions (planned maintenance) and the way of filing claims.

## 5. Typical mistakes
- An SLI measured on resources (CPU, memory) instead of on the user experience.
- The average instead of a percentile; no definition of an "outage".
- The SLO equal to the SLA — the first miss of the objective costs money right away.
- An objective of 100% or so high that no release fits in the budget.
- An SLO without an owner, a budget policy and a regular review — then it is just a dashboard.
- The same metrics for all service types; a batch service, a data store and an API need different SLIs.

## Sources
- [Service Level Objectives (SLI, SLO, SLA) Explained Simply](https://froehlich.medium.com/service-level-objectives-sli-slo-sla-explained-simply-fb4b91dd4a07) — Steve Froehlich, 2023 (the SLI → SLO → SLA pyramid, example SLIs, defining an outage through an error threshold, an SLA with consequences)
- [Google SRE Book — Service Level Objectives](https://sre.google/sre-book/service-level-objectives/)
- [Google SRE Workbook — Implementing SLOs](https://sre.google/workbook/implementing-slos/)
- Budget and composite availability calculations: our own.
