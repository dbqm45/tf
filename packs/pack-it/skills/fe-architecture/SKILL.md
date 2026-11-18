---
name: fe-architecture
description: Use for frontend structure — state and data, component boundaries, SSR/RSC, performance, resilience.
metadata:
  review: "2027-10-17"
  catalog: "Use for decisions about frontend structure (any framework) — architecture style, FSD/feature folders, state and the data layer, component boundaries, rendering (SSR/RSC), performance, resilience (errors, loading, retry), routing, client security (CSP, CSRF, tokens), component tests, AI chat UI. Not for styles (fe-css), browser APIs and a11y (fe-web-platform) or syntax (lang-*, fw-*)."
  keywords: "tabela danych, tabela z filtrowaniem i sortowaniem, filtry znikają po odświeżeniu, filtry w URL, wirtualizacja listy, zaznacz wszystkie, aria-sort, architektura frontendu, SPA, ponawianie żądań, retry w przeglądarce, odporność frontendu, stan aplikacji, zarządzanie stanem, warstwa danych frontu, podatność we frameworku frontendowym, czy to problem tylko frontendu, Server Components, mikrofrontendy, routing, micro-frontendy, micro-frontends, Module Federation, dwie wersje Reacta, współdzielone zależności, BFF, backend for frontend, SSR na brzegu, edge rendering, data table, table with filtering and sorting, filters disappear after refresh, filters in URL, list virtualization, select all, frontend architecture, request retries, retry in the browser, frontend resilience, application state, state management, frontend data layer, vulnerability in a frontend framework, is it only a frontend problem, microfrontends, two versions of React, shared dependencies, SSR at the edge"
---

# Frontend architecture

The rules are framework-independent; the examples in references are often in React ("example in React") — take
Angular idioms from fw-angular, language idioms from lang-*. First name the problem (team scale, performance, resilience,
security), then choose the pattern — not the other way round.

## Structure (feature-first)
```
src/
  app/            # bootstrap, routing, providers
  features/<x>/   # everything for one feature: ui, model/state, api, tests
  shared/         # UI kit, utils, API client — no knowledge of the domain
```
- A feature does not import from another one directly — only through its public API (`index.ts`); `shared/` does not import from `features/`.
- Folder names from the domain language (Screaming Architecture). With many teams/boundaries → full FSD
  (`app/pages/widgets/features/entities/shared`, imports only downwards) enforced by a linter.

## State — the lowest sufficient level
1. Local component state (React `useState`, Vue `ref`, Angular `signal`).
2. State in the URL (filters, pagination, tabs) — linkable, survives a refresh.
3. Server state → a layer with a cache (TanStack Query, router loaders, Angular `httpResource`). Do not copy API data into a global store.
4. A global store — only for truly global client state (UI session, preferences).

## Components and data
- Presentation (inputs → UI) separated from data fetching (container / hook / composable / service).
- > ~200 lines or > 5–6 boolean inputs → split it or use composition (children/slots, compound components).
- All API calls through one client (`shared/api`) with auth, errors, cancellation; DTO → model mapping at the boundary, not in components.
- A pure render (no side effects); every opened resource (subscription, timer, listener) has a symmetrical cleanup.

## Resilience
- Every data view has 4 states: loading, error (with "try again"), empty, data — as a union, not flags.
- An error boundary per route + around independent widgets; pass async errors to the boundary explicitly.
- Retry with backoff and jitter only for idempotent operations; 409/422 is a business outcome, not a failure.
- Forms: validation with a schema shared with the backend when possible; server errors mapped onto fields; a lock against double submission.
- Optimistic updates only for operations that almost always succeed — always with a rollback.
- Feature flags checked in one place; removed after full rollout (add a cleanup task).

## Performance
- Code splitting per route; heavy libraries (charts, editors) lazily (`import()`, Angular `@defer`). Do not lazy-load the LCP image.
- The rendering model (CSR/SSR/SSG/ISR/RSC) chosen per route.
- Measure before optimizing (LCP/INP/CLS, profiler, bundle analyzer); memoization only for a measured problem.

## Client security
- Content from users and from AI models is untrusted: framework interpolation instead of `innerHTML`; escape hatches
  (`dangerouslySetInnerHTML`, `v-html`, `bypassSecurityTrust*`) only after a sanitizer.
- The session in an `HttpOnly; Secure; SameSite` cookie (preferably a BFF), not in `localStorage`; CSRF: a token + Fetch Metadata.
- Strict CSP (nonce + `strict-dynamic`), SRI for resources from third-party CDNs, PII redacted before logs/telemetry.
- SSR, React Server Components, Angular SSR and server actions are **server code** exposed to the internet: they require
  patches within a day for critical CVEs (React2Shell, CVE-2025-55182: code execution without logging in with a single request)
  and running like a backend (no root, no shell in the image — ops-docker).
- The server side (auth, validation) — be-auth-security.

## Decisions
A change of structure (a new state library, a new pattern, micro-frontends) → an ADR per docs-tech-writing; quality
drivers — arch-quality-attributes. General principles (KISS/YAGNI/SOLID) — eng-design-principles; testing strategy — eng-testing.

## References index
Read only the file needed for the current question:
- `principles.md` — 6 fundamentals, principles (cohesion/coupling, encapsulation), the "navigation/content/affordances" model, the index of frontendpatterns.dev guides.
- `architecture-styles.md` — monolith, modular, component-based, micro-frontends, Flux, layered, serverless — advantages/disadvantages/when.
- `fsd-screaming-architecture.md` — FSD layers and rules, Screaming Architecture, kinds of state per framework, tooling in 2026.
- `rendering-models.md` — VDOM vs signals, CSR/SSR/SSG/ISR, hydration (mismatch, incremental), RSC, choice per route.
- `components/` — `component-lifecycle`, `presentational-vs-container`, `props-and-attributes`, `pure-component`, `compound-components` — when you design a component's API or split.
- `fundamentals/` — `barrel-export`, `separation-of-concerns`, `single-responsibility` — module boundaries and code splitting.
- `performance/` — `code-splitting`, `lazy-loading`, `debounce` (and throttle), `memoization`.
- `resilience/` — `async-boundary`, `error-boundary`, `error-handling`, `loading-state`, `retry`.
- `routing/client-side-routing.md` — the client router, the Navigation API, scroll and focus after navigation.
- `data-tables.md` — **data tables**: filter and sort state in the URL, server-side data, virtualization, "select all matching" versus a bulk operation, the command palette, accessibility (`aria-sort`).
- `security/` — `content-security-policy`, `csrf-protection`, `samesite-cookie`, `secure-token-storage`, `input-sanitization`, `output-encoding`, `trusted-types`, `subresource-integrity`, `pii-redaction`.
- `testing/component-testing.md` — component tests from the user's perspective (tools: tool-vitest, tool-jest, tool-playwright).
- `ai-chat-ui/` — **chat interfaces with an AI model**: the thread model as a list of messages with a status (`message-thread`),
  the prompt field with IME and Send/Stop (`prompt-input`), response streaming and SSE (`streaming-response`),
  interruption with `AbortController` also on the server (`stop-generation`), the "thinking" indicator (`thinking-indicator`),
  regeneration as variants (`response-regeneration`). Read only when building a chat/assistant UI.

Pattern files have a "Notes (state in 2026)" section — corrections to the source and equivalents in other frameworks.

## Checklist
- [ ] Feature boundaries and public module APIs preserved; imports only in the allowed direction
- [ ] State at the lowest sufficient level; server data in a layer with a cache
- [ ] Every data view handles loading/error/empty/data; errors do not take down the whole page
- [ ] Table: filters and sorting in the URL, data from the server, "all matching" as a filter, `aria-sort` on the sorted column
- [ ] No `innerHTML` with untrusted data; tokens outside `localStorage`
- [ ] Code splitting and the rendering model justified by measurement
- [ ] The structural decision described in an ADR

Sources: frontendpatterns.dev (Den Odell), M. Hrynkevych "Frontend Architecture", "The Grand Unifying Architecture of
Frontend" (playfulprogramming), LogRocket "modern frontend architecture patterns" — described in our own words, source licences unspecified.
