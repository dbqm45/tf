---
name: arch-system-design
description: Use for designing a system from requirements to scale — estimates, API and data, bottlenecks, availability.
metadata:
  review: "2027-10-17"
  catalog: "Use when a system must be designed from requirements to scaling — use cases, back-of-the-envelope estimates, the API and data model, the high-level design, deep dives, bottlenecks; latency and availability numbers, high availability, performance antipatterns. Not for choosing the stack (arch-tech-selection) or the style catalogue (arch-quality-attributes)."
  keywords: "dostępność usług, usługi połączone szeregowo, ile dziewiątek, SLA całości, szacunki ruchu, skalowanie, wąskie gardło, ile serwerów, wywołuje synchronicznie, jaką dostępność obiecać, SLA każdej zależności, service availability, services in series, how many nines, overall SLA, traffic estimates, scaling, bottleneck, how many servers, calls synchronously, what availability to promise, the SLA of every dependency, system design, back-of-the-envelope estimate"
---

# System design

The procedure leads from requirements to a design that can be justified with numbers. Skip it when the task is small —
then eng-design-principles is enough. Result: an architecture document with C4 diagrams and ADRs (arch-architect-practice).

## Procedure
1. **Use cases, constraints, assumptions** — interview (core-plan-interview), do not guess:
   - who uses it and for what (3–5 main use cases; the rest explicitly out of scope);
   - scale: the number of users, daily active ones, peak requests, growth over 1–3 years;
   - data: volume, retention, the read-to-write ratio, the size of a typical object;
   - quality requirements as scenarios (p95 latency, availability, consistency, RPO/RTO — arch-quality-attributes);
   - constraints: budget, team, regulations (data location), existing systems.
2. **Back-of-the-envelope estimates** (an order of magnitude, not precision):
   - requests per second = daily operations ÷ ~86,400 (≈ 10⁵ s), the peak usually 2–10× the average;
   - storage = objects per day × size × retention (+ replicas, indexes, backups);
   - network bandwidth = requests/s × response size; cache memory = the hot set (often ~20% of the data gives
     ~80% of the reads).
   - a month is ~2.5 million s: 400 requests/s ≈ 1 billion requests a month; powers of two and identifier lengths
     in `references/project-examples.md`.
   The numbers decide: 50 writes/s are handled by one database; 50,000 writes/s require a different design.
3. **API** (be-api-design) and the **data model** (entities, keys, access patterns — from the queries, not from the tables); choosing
   stores (arch-quality-attributes, `data-architecture.md`).
4. **High-level design**: components and flows (a C4 container diagram), the read and write paths separately, synchronous
   and asynchronous boundaries. The simplest design that meets the requirements (a modular monolith, one database).
5. **Deep dive into the key components**: where there is risk or scale — data structures, algorithms (e.g.
   identifier generation, event ordering, counters), the schema and indexes, contracts.
6. **Scaling and bottlenecks**: for every quality requirement — what breaks first at 10× traffic and how to
   prevent it: cache, replicas, partitioning, queues, a CDN, horizontal scaling of stateless services; single points
   of failure; antipatterns (`references/performance-antipatterns.md`). Every change with its trade-off named explicitly.
   Scale iteratively (measure → profile → bottleneck → change → measure), do not jump straight to the target
   design; the scaling ladder and patterns from ready exercises (fan-out on write vs on read, batch
   precomputation, consistent hashing, LRU): `references/project-examples.md`.
7. **Operations**: monitoring (RED/USE metrics, traces, alerts from SLOs), deployment and rollback, cost
   (ops-observability, ops-release-engineering, ops-finops), security (arch-threat-modeling).

## Numbers worth keeping in your head (orders of magnitude)
| Operation | Order of magnitude |
|---|---|
| a read from the CPU cache | ~1 ns |
| a read from RAM | ~100 ns |
| a read of 4 KB from an SSD/NVMe | ~10–100 µs |
| a round trip within a data centre | ~0.5 ms |
| a sequential read of 1 MB from an SSD | ~1 ms |
| an indexed database query over the network | ~1–10 ms |
| a round trip between continents | ~100–150 ms |
Conclusions: memory is orders of magnitude faster than the network, and the data centre network — than the network between continents; a chain
of synchronous calls adds up latencies; data close to the user (a CDN, a region) matters more than faster code.
The exact values depend on the hardware — measure your own.

## Latency, throughput and scalability
- **Latency** is the time of one request as felt by the user. Measure it in percentiles (p95, p99), not
  the average. It is the sum of the layers: network, queue, processing, database, dependency calls. First establish which layer
  dominates (distributed traces — ops-observability), only then optimize it.
- **Throughput** is the amount of work per unit of time (requests/s). Low latency does not guarantee high
  throughput, and high throughput does not guarantee low latency. Throughput grows mainly through
  parallelism (more instances, threads, partitions), and latency drops by shortening the path (cache, data
  proximity, fewer calls in sequence).
- **Little's law** for a system: the average number of requests in progress = throughput × the average service time. At 200
  requests/s of 50 ms each, on average 10 requests are in progress at the same time. From this you compute the size of the thread and connection pools and
  the number of instances, with headroom for the peak. When a dependency's latency grows, the number of requests in progress grows and the pools
  run out. That is why timeouts are needed (be-api-design, `backend-performance-checklist.md`).
- **Scalability is a property of the whole system, not of one component.** A system is as scalable as its weakest
  layer. Ten times more application servers on the same database does not remove the bottleneck, it only
  moves it, and often makes it worse (more connections to the database). With every change of scale check all the layers: the load
  balancer, the application, the cache, the database, the queues and external dependencies.
- Vertical scaling is simple, but it has a ceiling and a single point of failure. Horizontal scaling requires stateless
  instances (sessions and files outside the process). Sticky sessions on the load balancer are a workaround that weakens
  balancing and failover. A load balancer gives resilience through health checks, not only
  through splitting traffic (L4 vs L7 — ops-linux-networking, `web-servers-and-proxies.md`).

## Availability in numbers
| Availability | Downtime per year | per month | per week |
|---|---|---|---|
| 99% | ~3.65 days | ~7.3 h | ~1.7 h |
| 99.9% | ~8.8 h | ~44 min | ~10 min |
| 99.95% | ~4.4 h | ~22 min | ~5 min |
| 99.99% | ~53 min | ~4.4 min | ~1 min |
- **In series** (both components needed): availability = the product (99.9% × 99.9% ≈ 99.8%). **In parallel**
  (one of two independent ones is enough): 1 − (1 − A)² (two of 99.9% ≈ 99.9999% — with truly independent failures).
- Every extra nine usually means an order of magnitude higher cost and operational discipline (ops-sre-incidents,
  `sli-slo-sla.md`).

## High availability
- **Active–passive failover**: the standby takes over traffic after losing the heartbeat; the switchover time depends on whether
  the standby is "hot" (running and has the data) or "cold". Risk: split brain (both nodes think they are the primary)
  → a leader election mechanism or fencing.
- **Active–active**: both copies serve traffic; balancing (DNS, a load balancer) and resolving write conflicts
  or splitting writes (each region owns part of the data) are needed.
- Database **replication**: a primary with replicas (reads scaled, replica lag) or many write nodes
  (conflicts) — be-database, `database-performance.md`. **Federation** (a functional split: a separate database for users,
  products, orders) before sharding.
- **Service discovery**: a registry and health checks (DNS in Kubernetes, Consul) instead of addresses hard-coded
  in the configuration; the client or the load balancer asks the registry for healthy instances.
- Back-pressure, load-levelling queues, circuit breakers and bulkheads — ops-sre-incidents
  and `cloud-patterns.md`.

## Communication — in brief
TCP (reliable, ordered) vs UDP (no guarantees — media streams, DNS, QUIC as the basis of HTTP/3); REST,
RPC (gRPC), GraphQL — be-api-design, `styles-and-communication.md`; job queues and messages — be-messaging-outbox;
a **pull** CDN (fetches from the origin on the first request, simple) and a **push** CDN (you upload files up front — large, rarely
changed assets).

## Checklist
- [ ] use cases, scale and quality requirements recorded; out of scope explicit
- [ ] traffic, data and memory estimates in orders of magnitude
- [ ] the API, the data model and the stores matched to the access patterns
- [ ] for every quality requirement: the bottleneck at 10× and a response with a trade-off
- [ ] single points of failure, monitoring, cost and security discussed

## Sources
- [donnemartin/system-design-primer](https://github.com/donnemartin/system-design-primer) (CC BY 4.0) — the approach,
  availability in numbers, failover, sample solutions; J. Dean — "Latency numbers every programmer should know"
- [Microsoft — Cloud design patterns](https://learn.microsoft.com/en-us/azure/architecture/patterns/),
  [Performance antipatterns](https://learn.microsoft.com/en-us/azure/architecture/antipatterns/)
- [roadmap.sh — System Design](https://roadmap.sh/system-design)
- Developer Awam, "7 Core Infrastructure Concepts You Need to Master to Become a DevOps Engineer", CodeX / Medium,
  2026 — the scalability of the whole system, latency vs throughput, the API gateway
Described in our own words.
