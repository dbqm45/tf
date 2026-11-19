# Audit of an Nx monorepo with Angular — inventory and analysis

Contents: 1. Areas and questions · 2. Workspace · 3. Library inventory · 4. Dependencies · 5. Angular ·
6. Other areas · 7. First steps

You take the framework's rules from fw-angular (conventions by
version) and fe-architecture (state, components, front-end boundaries) — this file says **what to collect for the dossier**.

## 1. Areas and questions (stage 1 checklist)
| Area | Main question |
|---|---|
| Nx workspace | is the monorepo structure readable and consistent? |
| Library boundaries | do the libraries have clear responsibilities? |
| Dependency graph | do the dependencies flow in the right direction? |
| Angular architecture | do components, services and modules have responsibilities appropriate to their role? |
| Routing | are the division of routes and lazy loading justified? |
| State | where is the state and who owns it? |
| Data access | what do the communication with the API, the models and the error handling look like? |
| Shared code | what do we share and should it be shared? |
| Tests | do the tests correspond to the structure and the responsibilities? |
| Build and tools | does the Nx and Angular configuration support the adopted architecture? |

You do not assess a shared library in isolation: its consumers and what it depends on are also in scope.

## 2. Workspace
Commands (the syntax depends on the Nx version — check `nx --version` and the documentation of that version; save the output in `evidence/`):
```bash
npx nx show projects                      # list of projects
npx nx graph --file=evidence/graph.json    # dependency graph to a file (evidence for findings)
npx nx report                             # versions of Nx, plugins, Node
```
To record: the number of applications and libraries, library types, grouping, tags (`project.json`), dependency rules
(`@nx/enforce-module-boundaries` in the ESLint configuration: enabled? do the `depConstraints` match the actual
boundaries?), `nx.json` (cache, default options), generators, Nx and Angular versions. The number of libraries alone
says nothing about quality.

## 3. Library inventory
Module card = a library or an application. In the card header add `Type:` (feature / ui / data-access / util /
shared / app — only if such a division actually exists) and the tags. Business rules: usually in feature and
data-access; a purely technical library has an empty table with one sentence "none — technical library".

| Library | Type | Responsibility | Used by | Dependencies | Notes |
|---|---|---|---|---|---|
| `orders-feature` | feature | orders view | `shop-app` | `orders-data-access`, `orders-ui` | — |

Questions: does the name match the responsibility; is the division by domains, functions, layers or accidental; libraries
with an unclear responsibility; the owner of the shared code; one consumer or many.

## 4. Dependencies
From the graph (not from reading) check: a feature depending on another feature without a justification; a shared library
importing the code of one application; cycles; technical libraries with business logic; imports bypassing the public API
(`@org/lib/src/...` instead of `@org/lib`); dependencies not predictable from the structure. The layout
`app → feature → data-access / ui → shared-ui` is often justified, but do not assume that every application has it.

## 5. Angular
- **Components:** responsibility; mixing presentation, API calls and state; the flow of data and events
  (inputs/outputs, signals); whether "shared" components are actually reusable.
- **Services and business logic:** where the logic is; the scope of services; DI; whether the logic can be tested without the view.
- **Routing:** the division of routes, lazy loading, feature routes, guards and resolvers, navigation errors, the relation of routes to the
  library structure.
- **State:** the mechanisms (signals, stateful services, NgRx or others); global / domain / local state; data from the API;
  duplicated state. Do not assume one mechanism for the whole application — assess in the context of use.
- **API:** clients and adapters, models, mapping responses onto the application's models, error handling, sharing.

## 6. Other areas (according to the scope)
Unit and integration tests, e2e, aliases and import standards, shared types and models, environment
configuration, build and cache, running tests and lint (`nx affected`), generators, technical documentation.

## 7. First steps
1. Workspace: `nx show projects`, `nx graph --file=evidence/graph.json`, `nx.json`, project configurations, ESLint,
   Nx and Angular versions.
2. A list of libraries grouped by domains and responsibilities; mark the unclear ones.
3. Dependencies: those used by the application, directions against the flow, cycles, public API, whether the Nx rules work.
4. 3–5 representative business functions traced `route → feature → state/service → API → UI` (for the Flows section
   of the index; not every function has to have this layout).
5. Findings as you go into `assessment.md`; recommendations only after the analysis.
