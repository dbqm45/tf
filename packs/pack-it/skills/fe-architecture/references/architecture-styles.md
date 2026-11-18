# Architecture styles of the whole frontend application

> **Contents:** Notes (state in 2026) · Frontend composition styles (LogRocket) · Classic software architecture styles applied to the… · How to choose between these two taxonomies

Sources: blog.logrocket.com "A guide to modern frontend architecture patterns" (5 composition
styles + hybrid) and Hrynkevych's article (classic software architecture styles
applied to the frontend). These two taxonomies complement each other — LogRocket describes **how to physically
compose** a frontend, Hrynkevych describes **the broader system patterns** in which the frontend is
embedded (some of them, such as Micro Frontends, appear in both, consistently).

## Notes (state in 2026)

- The choice of the style of the whole system (modular monolith, microservices, events) and quality attributes — arch-quality-attributes;
  technology choice — arch-tech-selection; recording the decision as an ADR — docs-tech-writing.
- "Flux" is today a family of solutions (Redux Toolkit, NgRx, Pinia); in parallel the **signals** model is growing (Angular,
  Solid, Svelte 5, Preact) — reactive state without a central dispatcher. A central store only for truly
  global client state (fsd-screaming-architecture.md).
- Micro-frontends in 2026: Module Federation 2.0 (webpack/Rspack, Vite plugins), Native Federation (Angular, based on
  import maps), Single-SPA; often a **modular monolith** in a monorepo (Nx/Turborepo) with boundaries
  enforced by a linter is enough — independent deployments are the only strong argument for MFE.
- **Micro-frontends — the typical failure:** drift of shared dependencies, i.e. two versions of the framework on one page
  (broken hooks, context, double size). It is prevented by `singleton: true` with `strictVersion`/`requiredVersion`
  in the federation configuration and a version compatibility check in CI before deployment. The "MFE or not" decision follows from the pain
  of deployments between teams, not from the complexity of the application. A heuristic (T. Kanjariya, 2026-08-06, not a rule): up to
  about 15 people a modular monolith; several dozen people and teams blocking each other on deployments → consider MFE.
- **BFF (Backend for Frontend) as a pattern:** a thin backend per client type (web, mobile), owned by the frontend
  team, which shapes the data for one interface, aggregates calls and keeps the session in an `HttpOnly` cookie.
  When not: one client and the API already fits the screens — a BFF is then just an extra network hop. Cost:
  another service to maintain and a single point of failure for the client (the pattern described by P. Calçado and S. Newman
  [unverified — the primary sources were not opened in this session]).

## Frontend composition styles (LogRocket)

### Monolithic architecture

"Hosts the entire app frontend's interfaces, resources, and dependency module sources in just one
project codebase."

- **Advantages:** the simplest structure for small projects; easy to debug and test; fast
  deployments.
- **Disadvantages:** growing code complexity affects maintainability; scaling limits; potential
  conflicts when merging code (merge).
- **When to use:** small and medium projects, where fast product delivery is the priority.

### Modular architecture

It splits the code into "separate, maintainable, and installable modules" based on functionality.

- **Advantages:** reduces the complexity of the main repository; makes teamwork and parallel
  development easier; better management of tests and deployments.
- **Disadvantages:** difficulty browsing the full project from one repository; potentially slower
  deployment (coordination between modules).
- **When to use:** large codebases that need better collaboration between teams.

### Component-based architecture

"Components host a template, UI logic, and styles" — reusable interface elements as
the basic unit.

- **Advantages:** improves maintainability and productivity; consistent UI/UX; easier decomposition
  of the interface into smaller parts.
- **Disadvantages:** difficulties with state management in large component trees; the need to
  implement mock services for tests; requires knowledge of best practices, otherwise badly designed
  components come easily.
- **When to use:** the basis of modern libraries/frameworks (React, Vue, Angular, Svelte) — this
  is today the starting point, not an alternative to the other styles on this list.

### Micro-frontend architecture (Micro Frontends)

"Divide the app frontend into isolated, maintainable frontend projects" — with a host application that
loads the individual micro-frontends delivering functionality on demand.

- **Advantages:** excellent scaling and maintainability; deployment without restarting the whole application;
  easy assignment of separate projects to separate teams.
- **Disadvantages:** complicates the product architecture; slower initial development (setup); requires
  UI/UX standardization between teams, otherwise the product drifts apart visually/behaviourally.
- **When to use:** large, complex projects maintained by large, autonomous teams.

### Flux architecture

A pattern introduced by Meta: "centralized state stores and unidirectional data flow".

- **Three elements:** **Dispatcher** (sends actions to the store), **Store** (holds the state and the logic),
  **View** (UI components, read from the store).
- **Advantages:** reduces the complexity of state management; a predictable, unidirectional data flow;
  an easy, replayable history of state changes (useful for debugging/time travel).
- **Disadvantages:** not easy for beginners; extra boilerplate; can needlessly complicate
  simple projects without really complex state.
- **When to use:** medium and large component applications with complex, shared state.

### Hybrid/mixed architecture

A combination of several patterns at once — e.g. monolithic + component-based, or modular + Flux +
component-based. **The source's key conclusion:** "There is no strict rule telling you to follow just
one architecture pattern — you can adhere to multiple patterns" depending on the project's needs and
the team's preferences — these styles are not mutually exclusive categories.

### Comparison table (LogRocket)

| Factor | Monolith | Modular | Component-based | Micro-frontends | Flux |
|---|---|---|---|---|---|
| Simple projects | recommended | no | recommended | no | no |
| Medium projects | partly | recommended | recommended | partly | recommended |
| Large projects | no | partly | recommended | recommended | recommended |
| For beginners | yes | could be | yes | no | no |

## Classic software architecture styles applied to the frontend (Hrynkevych)

### Layered architecture

The application divided into stacked layers:
- **Presentation layer** — UI, components (e.g. React).
- **Business logic layer** — domain, state management (Redux, Zustand).
- **Data access layer** — API, databases, CMS.

Advantages: a clear separation of responsibilities, modularity. Disadvantages: rigidity, potential
unnecessary coupling between layers if the boundaries are not guarded.

### Client-server architecture

The browser sends requests to the backend, which sends back responses — the standard for modern
frontend applications; GraphQL and REST structure this interaction. Advantages: simplicity, centralized
data handling. Disadvantages: server-side bottlenecks, network latency.

### Microservices and Micro Frontends

**Microservices** — the backend divided by business capabilities.
**Micro Frontends** — the frontend divided analogously, each team manages its slice of the UI;
tools: Webpack Module Federation, Turborepo, Single-Spa. Advantages: team autonomy, independent
deployment. Disadvantages: integration complexity, a larger infrastructure burden.

### Serverless (Functions as a Service)

Logic divided into functions run in the cloud (AWS Lambda, Vercel Functions); in Next.js:
API routes, edge middleware. Advantages: scalability, no server management. Disadvantages: cold starts,
dependence on the provider (vendor lock-in).

### Distributed systems

A modern frontend communicates with many external systems at once — payment gateways,
CMSs, third-party authentication systems. Challenges: latency, data consistency, handling
partial failures. Solutions: caching, retry logic, CDN strategies — see also the pattern catalogue,
the Resilience category (`resilience/`).

## How to choose between these two taxonomies

They are not competing — they ask about different axes:
- **"How to physically compose the repo/deployment?"** → the LogRocket section (monolith/modular/
  component-based/micro-frontends/Flux).
- **"How does the frontend communicate with the rest of the system and how is the logic organized inside the layers?"**
  → Hrynkevych's section (layered/client-server/microservices/serverless/distributed systems).

A real project usually combines one answer from each axis — e.g. "component-based + Flux" (LogRocket)
**and** "client-server + serverless" (Hrynkevych) at once, which is a common combination for a modern
Next.js/React application with API routes.
