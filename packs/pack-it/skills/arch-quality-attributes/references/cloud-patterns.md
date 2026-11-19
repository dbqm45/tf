# Cloud patterns and choosing a runtime platform

## Pattern catalogue (Azure Architecture Center) — where in the factory
Pattern names are a shared vocabulary in ADRs and reviews. The "in the factory" column says where the procedure is.
| Group | Patterns | In the factory |
|---|---|---|
| resilience | Retry, Circuit Breaker, Bulkhead, Health Endpoint Monitoring, Throttling, Rate Limiting | ops-sre-incidents (designing for failure), be-api-design (`http-in-practice.md`, `backend-performance-checklist.md`), ops-observability |
| data | Cache-Aside, Materialized View, Index Table, Sharding, CQRS, Event Sourcing | be-api-design (`backend-performance-checklist.md`), be-database (`database-performance.md`), ddd-tactical-design |
| messaging | Publisher-Subscriber, Competing Consumers, Queue-Based Load Leveling, Priority Queue, Sequential Convoy, Claim Check, Messaging Bridge, Idempotent Consumer | be-messaging-outbox, `style-catalog.md` |
| distributed consistency | Saga, Compensating Transaction, Choreography, Scheduler Agent Supervisor, Leader Election | ddd-tactical-design (saga), be-messaging-outbox |
| gateways and the edge | Gateway Routing, Gateway Aggregation, Gateway Offloading, Backends for Frontends, Gatekeeper, Ambassador, Sidecar | be-api-design (`styles-and-communication.md`), ops-linux-networking (`web-servers-and-proxies.md`) |
| integration and migration | Anti-Corruption Layer, Strangler Fig, Asynchronous Request-Reply, Pipes and Filters | ddd-context-mapping, eng-behavior-preserving-refactoring, be-api-design (`202`) |
| deployment and scale | Deployment Stamps, Geode, Compute Resource Consolidation, Static Content Hosting, External Configuration Store | ops-release-engineering, ops-security-operations (multiple regions) |
| security | Federated Identity, Valet Key (a signed URL), Quarantine | be-auth-security, ops-supply-chain-security |
Notes on selected ones:
- **Strangler Fig**: the new system takes over the old one's functions gradually behind a shared facade (routing by path or
  function), the old one is switched off piece by piece — instead of a "big bang" rewrite. Every step released and reversible.
- **Deployment Stamps**: repeatable, independent copies of the whole system (with data) per region or customer group —
  they limit the blast radius of failures and help with data location requirements; cost: many environments to maintain.
- **Sidecar / Ambassador**: auxiliary functions (proxy, mTLS, logs) in a separate container next to the application; the basis of a service
  mesh. Before you add one — would a library or the platform not do it cheaper?

## Where to run
| Platform | When | Watch out for |
|---|---|---|
| **PaaS / frontend hosting** (Vercel, Netlify, Render, Railway, Heroku, App Service) | a small team, a web application or API without unusual requirements | cost at high traffic, dependence on platform features, the data region |
| **functions** (AWS Lambda, Azure Functions, Cloud Functions) | events, irregular traffic, short tasks | cold start, time and memory limits, database connection pools (a proxy), cost under constant load |
| **containers without a cluster** (Cloud Run, ECS on Fargate, Azure Container Apps) | HTTP services and background jobs without managing a cluster | less control over the network and scheduling |
| **managed Kubernetes** (EKS, GKE, AKS) | many services and teams, a need for a shared platform | operating cost and skills (ops-kubernetes); the platform as a product (proc-team-topologies) |
| **virtual machines** | software that requires it, specific hardware | patching and configuration (ops-linux-networking), immutable machines from images |
Smaller providers (DigitalOcean, Hetzner) are often much cheaper for simple workloads — at the cost of fewer
managed services. The decision in an ADR by the quality scenarios, cost (ops-finops) and the team's skills
(arch-tech-selection).

## Sources
- [Microsoft Azure Architecture Center — Cloud design patterns](https://learn.microsoft.com/en-us/azure/architecture/patterns/)
- [roadmap.sh — DevOps](https://roadmap.sh/devops) (cloud design patterns, cloud providers, serverless, PaaS,
  container orchestration)
Described in our own words.
