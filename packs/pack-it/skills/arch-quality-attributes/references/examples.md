# Examples — quality attributes and the architecture style

## 1. Scenarios and the utility tree for room booking
**Situation.** "We are building a conference room booking system for a chain of 40 office buildings. It must be fast, secure and reliable.
Write down the quality requirements."

**How.**
1. I turn every "must be fast" into a scenario `source → stimulus → (environment) → artifact → response → measure`;
   a sentence without a measure does not pass.
2. I review the list of attributes (ISO 25010, abbreviated) — modifiability and accessibility (a11y), which nobody asked about, are added.
3. I record performance and availability straight away as an SLI/SLO (ops-sre-incidents).
4. I give every scenario a pair (importance, difficulty) on an H/M/L scale; only (H,H) shape the architecture.
5. For (H,H) I propose a fitness function in CI.

**Result** (the "Quality attributes" section in `03-requirements/requirements.md`):

| ID | Attribute | Scenario (source → stimulus → environment → artifact → response → measure) | Priority |
|---|---|---|---|
| QA-1 | performance | 100 employees → book a room → the 8:45–9:15 peak → the booking API → accepts the requests → p95 < 300 ms | (H,H) |
| QA-2 | reliability | 2 people → book the same slot in the same second → normal operation → the booking module → one wins, the other gets a message → 0 double bookings | (H,H) |
| QA-3 | availability | a user → opens the calendar → working days → the application → responds → an SLO of 99.5% successful requests in a 30-day window | (H,M) |
| QA-4 | modifiability | the product owner → adds a new resource type (a parking space) → development → the booking model → a change in 1 module → ≤ 5 days of work | (H,H) |
| QA-5 | security | an employee of company A → tries to read company B's bookings → production → the API → refusal → 0 successful reads in abuse tests | (H,M) |
| QA-6 | accessibility (a11y) | a screen reader user → books a room → the browser → the form → completes the task → without another person's help | (M,L) |

Fitness functions for (H,H): QA-1 — a load test in CI with a threshold of p95 < 300 ms; QA-2 — a concurrency test
(50 parallel attempts on one slot → exactly 1 success); QA-4 — a change impact report (ddd-model-stress-test).

## 2. A trade-off in an ADR: a price cache
**Situation.** "The product page loads in 1.2 s, because we compute the price with promotions every time. Let's add a cache."

**How.**
1. First a scenario with a measure: entering the product page during a campaign → p95 < 400 ms.
2. I name the trade-off explicitly: performance ↔ consistency (a stale price for the entry's lifetime) and performance ↔ modifiability
   (every new promotion rule must invalidate the cache).
3. I point to the **sensitivity point** (the entry's lifetime decides the price freshness) and the **trade-off point** (the cache itself: performance
   goes up, consistency and modifiability go down).
4. I record it in an ADR together with a rollback condition.

**Result** (a fragment of the ADR):
```markdown
## ADR-014: Cache of the computed price on the product page
Status: proposed
Driver: QA-7 (performance, H,H) — the product page during a campaign, p95 < 400 ms (today 1.2 s).
Decision: a price cache per product, a lifetime of 60 s; a promotion change invalidates the entries of its products.
Trade-offs:
- performance ↔ consistency: a customer may see a stale price on the list for ≤ 60 s; the cart and the order compute the price without the cache.
- performance ↔ modifiability: a new promotion type = a new invalidation rule (a cost in every price list change).
Sensitivity point: the entry lifetime (60 s). Trade-off point: the cache as such.
Fitness function: a load test of the product page, threshold p95 < 400 ms; a test "promotion change → new price after ≤ 60 s".
Rollback: if price complaints > 0 in a month, we shorten the lifetime or turn off the list cache.
```

## 3. "We want microservices" with one team
**Situation.** "We are starting a course enrolment platform. Team: 5 people. Let's do microservices right away, so that it scales."

**How.**
1. I ask about the (H,H) scenarios: the hardest is the enrolment peak — 2000 requests/s for 10 minutes at the start of the term, p95 < 300 ms;
   there are no independent teams or different reliability requirements per context.
2. I compare with the styles table: microservices are justified by the independent deployment of many autonomous teams — here there is one.
3. The simplest by default: a **modular monolith** with contexts as modules; the enrolment peak is handled by horizontal scaling
   of the whole application.
4. I guard the boundaries with a fitness function, so that a possible extraction is cheap later — only when a specific (H,H) requires it.

**Result** (recorded in `04-architecture/stack-decision.md`, "Decision drivers", and an ADR):

| Driver | Modular monolith | Microservices |
|---|---|---|
| QA-1: 2000 requests/s for 10 min, p95 < 300 ms | horizontal scaling of instances | scaling per service (not needed here) |
| a team of 5, one backlog | one deployment, one observability | the network, eventual consistency, a platform — cost without gain |
| QA-4: changing the enrolment rules in 1 module | module boundaries + an architecture test | service boundaries |
| **Decision** | **chosen** | rejected; it comes back when a second autonomous team appears |

A fitness function in CI (module boundaries and a performance budget):
```yaml
architecture-fitness:
  stage: test
  script:
    - npm run test:architecture   # the "enrolment" module does not import the inside of the "payments" module
    - npm run test:perf -- --threshold-p95=300
```
