---
name: qa-performance-testing
description: Use for performance testing — a load model, thresholds from SLOs, k6 and Gatling, analysis, a report.
metadata:
  review: "2027-10-17"
  catalog: "Use when planning, writing and analysing performance tests — types (smoke, load, stress, soak, spike, breakpoint), a load model from production traffic, thresholds from SLOs, k6 (TS/JS) and Gatling (Java), environment and data, bottleneck analysis, a report, a smoke test in CI. Not for frontend performance in the browser (fe-web-platform) or SLOs and alerts (ops-sre-incidents)."
---

# Performance testing

They answer the question "will the system meet the requirements under the expected traffic, and how will it behave beyond it". The requirement
comes from a quality attribute scenario or an SLO (arch-quality-attributes, ops-sre-incidents), not from "the faster,
the better".

## Types of tests
| Type | Question | Load shape | When |
|---|---|---|---|
| **smoke** | does the script work and what is the baseline | 1–5 virtual users, briefly | after every script change; in CI |
| **load (average)** | do we meet the thresholds under typical traffic | average production traffic, 5–60 min, with a ramp-up | regularly, before releasing big changes |
| **stress** | what happens above expectations | 1.5–3× the average, 5–60 min | before a campaign, a season, a new customer |
| **soak** | does anything build up over time (memory leaks, connections, disk) | average traffic, hours | after changes in resource management, periodically |
| **spike** | will the system survive a sudden inflow and recover | very heavy traffic in a short time | before events with abrupt traffic (a sale, a publication) |
| **breakpoint** | where is the capacity limit | a gradual increase until failure | rarely, for capacity planning — not on a shared environment |
The order: smoke → load → the rest by risk.

## Procedure
1. **Goal and thresholds**: an (H,H) scenario, e.g. "p95 of order placement time < 800 ms and < 1% errors at 200 orders
   per minute". The thresholds written in the script — a test without thresholds decides nothing.
2. **A load model from production**: which paths, in what proportions (e.g. 70% browsing, 20% search,
   10% purchase), the request or arrival rate at the peak, think times, the data distribution (popular and rare products).
   An **open** model (a constant arrival rate — like the real internet) rather than a closed one (a fixed number of users
   who wait for a response and hide the slowdown) when you test a public service.
3. **Environment**: as similar to production as possible (sizes, configuration, data at a similar scale); the load generator
   outside the system under test and with spare resources (the generator itself must not be the bottleneck). External dependencies
   (payments, SMS) — stubs with realistic response times, never real services and real money.
   A test on production only with the human's consent, with a plan and a time window.
4. **Test data**: enough accounts and records for caches and indexes to behave as in production; synthetic data
   (qa-regression, `.claude/skills/qa-regression/references/environment-and-special-data.md`).
5. **The script** (k6 for TS/JS, Gatling for Java teams): scenarios with response checks (status and content —
   a fast response with an error is not a success), data parametrization, correlation of tokens and identifiers, tags per
   path, thresholds.
6. **A run with observation**: system metrics in parallel (CPU, memory, database connections, queues, GC, dependency
   latency — ops-observability) and distributed traces for slow requests.
7. **Analysis**: where the time grows — the application, the database (slow queries, locks, connection pool), the network, a dependency;
   the USE method for resources (utilization, saturation, errors). One change at a time, repeat the test after the fix.
8. **The report**: the goal and thresholds, the load model, the environment and differences from production, results (p50/p95/p99, throughput,
   error rate, resources) on a chart over time, bottlenecks with evidence, recommendations, risks and limitations of the test.

## k6 — a sketch
```js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  scenarios: {
    purchases: { executor: 'ramping-arrival-rate', startRate: 10, timeUnit: '1m', preAllocatedVUs: 50,
              stages: [{ target: 200, duration: '5m' }, { target: 200, duration: '20m' }, { target: 0, duration: '2m' }] },
  },
  thresholds: {
    'http_req_failed': ['rate<0.01'],
    'http_req_duration{path:order}': ['p(95)<800'],
  },
};

export default function () {
  const res = http.post(`${__ENV.BASE_URL}/api/orders`, JSON.stringify({ sku: 'A-1', qty: 1 }),
    { headers: { 'Content-Type': 'application/json' }, tags: { path: 'order' } });
  check(res, { 'created': (r) => r.status === 201 });
  sleep(1);
}
```
A missed threshold → a non-zero exit code, so CI marks the test as failed. The environment address and tokens through environment
variables, never in the script.

## Performance tests in CI
- A **performance smoke test** on every PR to critical paths (short, little traffic) — catches regressions of an order
  of magnitude (N+1, a missing index).
- A **load test** overnight or before a release on a dedicated environment, with a comparison to the previous result
  (the trend, not just the threshold).
- Results saved (a CI artifact, a dashboard), so it is visible when things started getting worse.

## Checklist
- [ ] thresholds from the requirements in the script, checks of the response content
- [ ] a load model from production data, an open model for public services
- [ ] the environment and data described with differences from production; dependencies stubbed
- [ ] system metrics collected during the run; bottlenecks with evidence
- [ ] a report with the test's limitations; a performance smoke test in CI

## Sources
- [Grafana k6 — load test types](https://grafana.com/docs/k6/latest/testing-guides/test-types/),
  [thresholds](https://grafana.com/docs/k6/latest/using-k6/thresholds/)
- B. Gregg — the USE method; [roadmap.sh — QA](https://roadmap.sh/qa) (load & performance, stress testing, k6, Gatling,
  JMeter, Locust, Artillery)
Described in our own words.
