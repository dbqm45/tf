# Feature-Sliced Design, Screaming Architecture, state and tooling

> **Contents:** Feature-Sliced Design (FSD) · Screaming Architecture · Components in practice · State management — three kinds, three tools · Tooling supporting this architecture (state in 2026) · CMS in frontend architecture (headless CMS, e.g. Contentful) · Recommendations

Source: Mykhailo Hrynkevych, "Frontend Architecture" (it synthesizes the documentation of Feature-Sliced Design, Khalil
Stemmler, Ivan Ojiego Garcia, Contentful, roadmap.sh) — supplemented with the state of FSD 2.x and the ecosystem in 2026.
Rendering models (SPA/SSR/SSG/ISR/RSC) are in `rendering-models.md`.

## Feature-Sliced Design (FSD)

A methodology that organizes code by **business features**, not by technical types ("everything about the cart in
one place", not "all hooks in one folder"). Framework-independent — it works in React, Vue,
Angular, Svelte.

**Layers (from the top; FSD 2.x):**
```
app/       → shell: bootstrap, providers, routing, global styles
pages/     → route views (composition of widgets/features for one URL)
widgets/   → large, self-contained UI blocks (header, sidebar) assembled from features/entities
features/  → user actions that deliver value (login, add-to-cart)
entities/  → business concepts (User, Product) — the entity's model + UI
shared/    → code without knowledge of the domain: UI kit, api client, lib, config
```
The `processes/` layer from FSD 1.x is deprecated (cross-page flows → `app/` or `features/`).
The source omitted `widgets/` — this is the full set.

**Import rules (the core of FSD):**
- A layer imports **only from lower layers** (`features` → `entities`, `shared`; never the other way round).
- Slices of the same layer **do not import each other** (`features/cart` ↛ `features/auth`); shared
  things go lower or are assembled higher (widget/page).
- Every slice exposes a **public API** (`index.ts`) — the rest is an implementation detail
  (fundamentals/barrel-export.md). Enforce it with a linter (`eslint-plugin-boundaries`, Steiger — the FSD linter, Nx
  `enforce-module-boundaries`).
- Segments inside a slice named by purpose: `ui/`, `model/`, `api/`, `lib/`, `config/`.

**Benefits:** a clear scaling path for growing teams; explicit boundaries (you know where to look and what to
add); fewer merge conflicts and a smaller cognitive load with a large codebase.

**When not:** a small application with a few screens — a simpler feature-first split is enough
(`app/`, `features/<x>/`, `shared/` — the SKILL.md hub). Introduce FSD when the boundaries start to blur.

## Screaming Architecture

Robert C. Martin's concept: the folder structure should "scream" about the business domain, not about the technical stack.

**Bad (the structure says "this is a React project", it says nothing about the product):**
```
/components
/pages
/hooks
```

**Good (the structure says what the product does):**
```
/billing
/checkout
/auth
```

**Benefits:** better discoverability (a new person sees the domain, not the technology), faster onboarding, alignment of the
code structure with product goals instead of with the choice of library.

**Relation to FSD:** Screaming Architecture is the principle ("name by domain"), FSD — a written-out layer structure that
implements it (`features/`, `entities/` are the domain). Take slice names from the ubiquitous language (ddd-tactical-design).

## Components in practice

- **"Smart" vs presentational component** — the smart one knows the data/logic and passes it down; the presentational one
  only renders its inputs (components/presentational-vs-container.md). Today the container role is often played by a hook /
  composable / service (Angular) or a route loader.
- **Colocation** — logic, styles and tests next to the component that uses them, not in global `/hooks`,
  `/styles` (the same justification as Screaming Architecture).
- **Modular organization** by domain (`/auth`, `/cart`, `/product`), not by technical type (`/components`,
  `/reducers`, `/services`).

## State management — three kinds, three tools

State is the behaviour of the application — design it as consciously as the folder structure.

| Kind | Description | React | Vue | Angular (fw-angular) |
|---|---|---|---|---|
| Local UI | lives in one component | `useState`, `useReducer` | `ref`, `reactive` | `signal`, `computed` |
| Server state (async) | data from the API with a loading/error/stale cycle | TanStack Query, SWR, router loaders, RSC | TanStack Query (Vue), Pinia Colada | `httpResource`/`resource`, TanStack Query (Angular) |
| Global client state | shared between unrelated parts | Zustand, Redux Toolkit, Jotai | Pinia | a service with signals, NgRx Signal Store |

On top of that, **state in the URL** (filters, pagination, tabs) — linkable and survives a refresh.

**A common mistake:** keeping API data in a global store together with UI state — it mixes two lifecycles
(cache/refresh/retry vs simple flags) and ends with manually reimplementing a server state library.

## Tooling supporting this architecture (state in 2026)

- **Meta-frameworks**: Next.js (App Router, RSC, Server Actions), React Router 7 (framework mode, formerly Remix),
  Nuxt (Vue), SvelteKit, Angular SSR (`@angular/ssr`, hybrid rendering per route) — file-based or
  declarative routing, colocated data loading, SSR/SSG per route.
- **Monorepo**: Nx (module boundaries, dependency graph, cached tasks), Turborepo (task cache, remote
  cache) — useful especially for many applications and micro-frontends (architecture-styles.md).
- **Server state**: TanStack Query (React/Vue/Solid/Angular) — replaces a manual `fetch` + effect + your own cache.
- **Global state**: Zustand, Jotai, Redux Toolkit (React); Pinia (Vue); NgRx Signal Store (Angular).
  Recoil is archived (2025) — do not choose it for new projects.
- **UI**: Tailwind CSS (v4, configuration in CSS) + headless/copied component libraries (shadcn/ui, Radix,
  Angular CDK/Aria) — UI consistency without writing a design system from scratch (fe-css).

## CMS in frontend architecture (headless CMS, e.g. Contentful)

**Benefits:** separating content from code (editors change content without a deployment); content models giving structure
to dynamic views; integration through GraphQL or REST.

**Impact on architecture:** the content team works independently of engineers; content changes less often than code,
so it fits SSG/ISR and a CDN cache (rendering-models.md) instead of rendering on every request.

## Recommendations

1. **"Think in features, not files"** — think in business features, not file types.
2. **FSD and Screaming Architecture** as concrete implementations of the above — at a scale proportional to the project.
3. **Tooling supports the structure, it does not replace it** — a good tool on a bad architecture will not fix it.
4. **Architecture serves two sides** — developers (maintainability, onboarding) and users (performance,
   accessibility, resilience).
