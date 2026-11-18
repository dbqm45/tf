# A catalogue of architecture styles and patterns

A complement to the "Architecture styles" table in SKILL.md. You choose a style from the quality attribute scenarios, not from fashion;
by default the simplest one that meets the (H,H) scenarios. You record the choice in an ADR with the rejected alternatives.

## The structure of the whole system
| Style | When | Cost and risk | A signal of a bad choice |
|---|---|---|---|
| **Layered** (presentation → application → domain → infrastructure) | almost always inside a module | "pass-through" layers without logic; a feature change goes through all the layers | every change touches 4 directories → a split by feature (eng-design-principles, `components-and-boundaries.md`) |
| **Client–server** | an application with central data and many clients | the server as a bottleneck and a single point of failure | — (it is the background of almost every web system) |
| **Modular monolith** | the default start | boundary discipline (ArchUnit) | modules know about each other's tables |
| **Microservices** | independent deployment and scaling of contexts, autonomous teams | the network, eventual consistency, observability, a platform | a distributed monolith: services deployed together, a shared database, chains of synchronous calls |
| **SOA** | integrating many systems of the organization through shared contracts | the integration bus (ESB) with routing and transformation logic becomes a central monolith | business rules in the bus; microservices prefer "smart endpoints, dumb pipes" |
| **Event-driven** | asynchronous reactions, many consumers, audit | hard flow tracing, ordering, duplicates | a chain of events nobody can draw |
| **Serverless** | irregular traffic, a small team, short tasks | cold start, time limits, provider dependency, cost under constant traffic | long processes split by force; the bill grows faster than the traffic |
| **Peer-to-peer** | no central server by design (file sharing, distributed networks, offline synchronization) | consistency, security and node discovery without a centre | you need a central authority anyway (permissions, billing) |

## Patterns inside the system
| Pattern | What it is | When | Pitfalls |
|---|---|---|---|
| **Microkernel (plug-in)** | a small core with minimal functionality + plug-ins through a contract and a registry | a product with extensions (IDE, ESLint, Nx plug-ins), rules per customer or market | the plug-in contract is a public API — versioning and backwards compatibility; external plug-ins are untrusted code (isolation, permissions) |
| **Blackboard** | a shared data space + independent knowledge sources that read and complete it + control choosing the next source | problems without a known algorithm, assembled from partial results (recognition, planning, AI agent teams) | hard tests and debugging, non-determinism; clear rules for writing to the blackboard needed (the factory uses this idea: `docs/project/` as the blackboard, the orchestrator as the control) |
| **Publish–subscribe** | the publisher publishes to a topic without knowing the consumers; the broker delivers to every subscriber | many independent consumers of the same fact | "at least once" delivery → idempotent consumers; ordering only within a partition; a message schema change is a contract change (be-messaging-outbox) |
| **Pipes and filters** | data passes through successive independent steps | batch processing, ETL, compilers, image processing | a shared format between the steps; errors in the middle of the pipeline |
| **MVC / MVP / MVVM** | separating the model, the view and the control or the view state | UI | business logic in the controller or component; in Angular components and signals are closer to MVVM (fe-architecture) |

## Orchestrating business processes
Long processes with many steps, waiting (for a human, a partner, a deadline) and compensations:
- **Choreography** (every service reacts to events) — loose coupling, but the flow is hard to see and change.
- **Orchestration** (one coordinator knows what comes next) — the flow visible in one place: a saga in code
  (ddd-tactical-design), a BPMN engine (e.g. Camunda — a process modelled with a diagram, ddd-event-storming: section 6a)
  or a durable execution engine (e.g. Temporal — a process as code whose state survives restarts and failures).
- BPEL (XML, the SOA and integration bus era) you will meet in older systems — model new processes in BPMN or in code.
- A process engine is a heavy dependency: choose it when there are many processes, they last long and the business wants to see
  and change them; a single flow is an ordinary saga with a state table.

## How to choose
1. List the (H,H) scenarios from the utility tree (SKILL.md).
2. For 2–3 candidates assess every scenario: meets / partly / does not, with a justification.
3. Add the operating cost (people, platform, on-call) — distributed styles require ops maturity (ops-*).
4. Plan a fitness function that guards the chosen style (SKILL.md).
You combine styles: e.g. a modular monolith with publish–subscribe between modules and a microkernel for per-customer rules.

## Sources
- F. Buschmann et al., *Pattern-Oriented Software Architecture, Vol. 1* (1996) — layers, pipes and filters, blackboard,
  microkernel, MVC.
- M. Richards, [Software Architecture Patterns](https://www.oreilly.com/library/view/software-architecture-patterns/9781491971437/)
  (O'Reilly) — the chapter on the microkernel architecture (an available excerpt).
- [roadmap.sh — Software Design and Architecture](https://roadmap.sh/software-design-architecture) (architectural
  styles and patterns: client-server, peer-to-peer, SOA, microkernel, blackboard, publish-subscribe, MVC, serverless).
Described in our own words.
