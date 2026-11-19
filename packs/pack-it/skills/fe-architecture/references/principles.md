# Foundations and principles of frontend architecture

> **Contents:** Six foundations (frontendpatterns.dev) · General architectural principles (Hrynkevych) · The "three responsibilities" mental model… · frontendpatterns.dev guides for multi-factor decisions…

Sources: frontendpatterns.dev/foundations ("Core Principles — core principles that shape how we
build for the web"), Mykhailo Hrynkevych's article "Frontend Architecture", dev.to/playfulprogramming
"The Grand Unifying Architecture of Frontend".

## Six foundations (frontendpatterns.dev)

1. **Accessibility as a Foundation** — accessibility is not an add-on at the end, it is the foundation on
   which the rest of the UI decisions stand (semantics, focus management, ARIA, keyboard) — fe-web-platform
   (`references/accessibility/`).
2. **Component-Driven Architecture** — UI built from isolated, reusable components as
   the basic unit of code organization, independent of a specific framework.
3. **Logical Separation of Concerns** — separating presentation, business logic and data
   access into distinct, independently testable layers.
4. **Performance as a Foundation** — performance designed from the start (code splitting, lazy
   loading, memoization), not optimized post hoc as a "fix" at the end.
5. **Resilience by Design** — the application is designed to cope with network errors, a slow backend,
   partial failure (error boundaries, retry, loading states); it does not assume the happy path.
6. **The Progressive Enhancement Mindset** — the basic functionality works without JS/under
   constraints; JS/CSS *enhance* the experience, they are not a condition for anything to work.

**Rule of application:** these six foundations **are not optional in large projects** — they apply to
every decision regardless of the chosen architecture style (`architecture-styles.md`) or the scale of the
project. A small, simple frontend (e.g. a frameworkless script) should still have accessible
forms, should still handle a `fetch()` error, should still have a sensible `loading state` —
"simple" does not mean "without foundations".

## General architectural principles (Hrynkevych)

- **Separation of Concerns (SoC)** — isolating presentation from logic, business rules from
  infrastructure; it increases testability and readability.
- **High cohesion, low coupling** — cohesion: logic that changes together
  should live together; coupling: the minimal number of dependencies between independent
  parts.
- **Encapsulation** — hiding implementation details behind a well-defined interface,
  especially in reusable components and hooks — the consumer should not know the internals.
- **DRY / KISS / YAGNI** — the definitions, the limits (when DRY does harm) and resolving conflicts between them are in
  eng-design-principles; here only a reminder that in UI YAGNI is most often broken by premature memoization,
  code splitting "just in case" and a component abstraction before the second use.
- **Horizontal, not vertical scalability** — the architecture should grow by
  feature/module/team (adding a new module = adding a new directory, not growing one
  existing file), not by constantly adding code to the same, ever larger files.

**The goals of frontend architecture according to the same article:** a clear delineation of the business
domain, code scalability, easier team collaboration, support for performance/
accessibility/resilience, enabling safe evolution of the software without friction.

## The "three responsibilities" mental model (framework-agnostic)

From the article "The Grand Unifying Architecture of Frontend" — the thesis: regardless of the implementation
philosophy (SPA, MPA, HTMX, LiveView, Server Components, Sync Engines), **every** frontend
solution addresses the same three lasting responsibilities:

1. **Navigation (client)** — the browser manages orchestration based on the URL; JavaScript gives
   control at the root level, regardless of whether it is an SPA or an exchange of HTML fragments.
2. **Content (server)** — the server is the authoritative source of markup or JSON data, triggered
   by navigation requests initiated by the client.
3. **Affordances (client)** — local UI state, work in progress (in-progress), optimistic updates —
   fast feedback for the user without waiting for a round trip to the server.

**Flow pattern:** navigation (client) → content (server) → affordances (client). A write
"travels up" as navigation; a read "flows down" as content. **This
asymmetry prevents conflicting, stateful systems** on both sides — if the client and the server are
both "owners" of the same state without a clear division of roles, that is a source of
synchronization bugs, not just an inconvenience.

**Where different approaches lie on the spectrum:**
- **HTMX** — minimal client logic, the server responds with heavy HTML.
- **LiveView** — extended server capabilities with persistent sessions.
- **React SPA** — client logic dominates, communication through a JSON API.
- **Server Components** — an explicit, three-layer separation (navigation/content/affordances separately).
- **Sync Engines** — replicated local data stores with an optimistic overlay.

**Practical conclusion:** the differences between competing approaches are mainly **a choice of transport and
an efficiency trade-off**, not a fundamental difference in what the system must do. When assessing
a new framework/approach — ask how specifically it separates these three responsibilities, instead of
assessing it in isolation from this model.

**A technical note from the article (Solid 2.0, as an illustration, not as a general requirement):** avoiding
hydration mismatch through "single hydration" — content is keyed by the call of the server
function that produced it; stale responses fail version validation; a client
component "claims" a node rendered on the server only once. This is a concrete mechanism
implementing the three responsibilities model without a client/server conflict over the same DOM node.

## frontendpatterns.dev guides for multi-factor decisions (external)

An index of 11 guides from frontendpatterns.dev/guides (Den Odell) — entry points when the question is "which of several
approaches and why", not "how to implement one thing". The content of the guides is not copied — when needed,
read the original.

| Guide (`/guides/…`) | Scope of the decision | Local equivalent |
|---|---|---|
| accessible-interaction-playbook | interactions that work for mouse, keyboard, touch and screen reader | fe-web-platform `accessibility/` |
| building-with-progressive-enhancement | layering features: a base without JS, enhancements gradually | foundation 6 above |
| choosing-css-strategy | CSS Modules vs utility-first vs CSS-in-JS vs BEM | fe-css |
| choosing-a-frontend-framework | criteria for choosing a framework | arch-tech-selection |
| choosing-a-networking-style-for-realtime-apps | WebSocket vs SSE vs long polling | fe-web-platform |
| choosing-a-state-management-approach | local state / context / store / server state | fsd-screaming-architecture.md |
| designing-component-apis | predictable component APIs that are hard to misuse | components/props-and-attributes.md, components/compound-components.md |
| managing-ai-response-states | a consistent flow of AI chat UI states | ai-chat-ui/ |
| managing-async-ux-states | idle/loading/error/success for asynchronous operations | resilience/loading-state.md |
| securing-frontend-data-flows | CSP, CSRF, tokens, encoding as one strategy | security/ |
| testing-confidence-ladder | test level vs confidence vs cost | eng-testing, testing/component-testing.md |
