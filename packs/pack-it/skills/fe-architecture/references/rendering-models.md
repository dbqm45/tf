# Rendering models: CSR, SSR, SSG, ISR, hydration, RSC

The mechanism (how it works) and the decision (when to use which). Merged from the import: frontend-developer `senior.md` (Virtual DOM,
SSR, hydration, RSC) and frontend-architect (rendering models per route). Browser phases (CRP, event loop) and
metrics (LCP/INP/CLS) — fe-web-platform (`.claude/skills/fe-web-platform/references/rendering-pipeline.md`, `.claude/skills/fe-web-platform/references/core-web-vitals.md`).

## Reactivity and DOM updates

Frameworks differ in **how** they determine what to change in the DOM:

| Model | Examples | How it works | Consequences |
|---|---|---|---|
| Virtual DOM + reconciliation | React, Preact, Vue (with an optimizing compiler) | render into an object tree → diff with the previous one → minimal DOM mutations | the cost of rendering a component ≠ the cost of changing the DOM; list keys and render purity matter |
| Signals / fine-grained reactivity | Angular (signals, zoneless), Solid, Svelte 5 (runes), Vue Vapor | dependencies tracked per value; a change updates only the dependent nodes | no diff of the whole subtree; pitfalls: reading a signal outside a reactive context |
| Compilation to imperative updates | Svelte, Vue Vapor | the compiler generates code that mutates specific nodes | a small runtime; the reactivity logic visible in the compiler |

**Reconciliation (VDOM) — common rules:** a different element type at the same position → the whole branch is replaced; the same
type → the changed attributes/children are updated; lists are compared by **key**. An unstable key (e.g. an index in
a sorted/filtered list) causes unnecessary unmounts and loss of state (input value, focus). Distinguish
"the component re-rendered" (JS work, diff) from "the DOM changed" (commit) — these are two different costs.
The equivalent in Angular: `@for (…; track item.id)` — the same role as `key`.

## Rendering modes

- **CSR (client-side)** — the server sends an almost empty HTML and the bundle; the UI is built in the browser. Fast TTFB,
  slow first display of content (FCP/LCP wait for the JS to download and execute); weaker SEO.
- **SSR (server-side, on request)** — the server renders the full HTML per request; the content is visible at once, but the page
  is not interactive until hydration finishes. Streaming SSR (sending HTML in chunks at
  Suspense / `@defer` boundaries) shortens the time to the first content.
- **SSG (at build time)** — HTML generated once; the cheapest to serve (CDN). For content that rarely changes.
- **ISR / revalidation** — static pages refreshed in the background after a time or on demand (tag/path). For content from a CMS.
- **Hydration** — the framework "attaches" to the HTML from the server: it restores the state and wires up event handling without
  building the DOM from scratch. **Hydration mismatch** — the HTML from the server differs from the client's first render
  (`Date.now()`, `Math.random()`, reading `window`/`localStorage`, locale/time zone) → warnings, flicker,
  and in the worst case a client re-render. Set client-dependent values after hydration.
- **Variants that limit the cost of hydration:** partial/"island" (Astro islands — only the islands are interactive),
  **incremental** (Angular `@defer` with `hydrate on …`, stable since v20 — a fragment hydrates on entering the
  viewport/on interaction), **resumability** (Qwik — no re-execution on the client), selective (React —
  priority for the part the user interacts with). Angular additionally replays events
  clicked before hydration (event replay).
- **The gap between "I can see it" and "I can click it"** — in pure SSR the user may click a button before its handler
  is attached. Formerly measured as TTI (a metric withdrawn from Lighthouse); today the symptom shows in INP and in long hydration
  tasks. Progressive enhancement (forms that work without JS) closes this gap.

## React Server Components (RSC)

- Components executed **only on the server** (or at build time); their code and dependencies **do not end up**
  in the client bundle. In SSR the same components render on the server **and** are hydrated on the client; in RSC —
  only on the server.
- They can read the database/secrets directly (these do not leak to the client — as long as you do not pass them in props to
  a client component; props crossing the boundary are serialized and visible).
- `"use client"` marks a **boundary**: from there down, the usual model (hydration, state, effects). Keep the boundaries low
  (the leaves of the tree), so that as much as possible stays on the server.
- **Server Actions / Functions** (`"use server"`) are public endpoints — validate the input and authorize every
  call like a regular API (be-auth-security).
- Ecosystem: Next.js App Router, React Router 7 (RSC experimentally). This model is specific to React;
  conceptually it implements the "navigation / content / affordances" split from `principles.md`.

## Decision: which model per route

The choice is not global — meta-frameworks (Next.js, Nuxt, SvelteKit, React Router 7, Angular SSR with server
routes `RenderMode.Server | Prerender | Client`) let you choose the model **per route**.

| Model | When the HTML is produced | When to choose it |
|---|---|---|
| CSR/SPA | in the browser | applications behind a login, where SEO and the first paint are secondary |
| SSR | on the server, per request | personalized, frequently changing content, SEO matters |
| SSG / prerender | at build time | marketing, documentation, blog |
| ISR / revalidation | statically + background refresh | product catalogue, content from a CMS |
| RSC (+ streaming) | server, without JS for the non-interactive parts | large mostly-read trees, heavy dependencies (markdown, formatting) |

Example: a product page from a CMS — ISR; the user panel — SSR or CSR; the home page/marketing — SSG.

**Compute near the data, not near the user.** SSR at the edge without a distributed database runs several queries
across half the world and can be slower than a render in the database's region. The pattern: the edge serves a static page shell
from the cache, and the dynamic parts are streamed from a function in the data's region (e.g. Partial Prerendering in Next.js).
Before you move rendering to the edge, measure the time to first byte with the database queries, not without them. The status
of specific edge products at the providers changes — check their documentation, with a date.

**The MPA alternative in 2026:** a plain multi-page application + cross-document View Transitions + Speculation Rules
(prefetch/prerender) gives smooth transitions without a client router — consider it for content sites
(routing/client-side-routing.md).

## Checklist

- [ ] The rendering model chosen per route, with a justification (SEO, personalization, frequency of change)
- [ ] No non-deterministic values in the first render (no hydration mismatch)
- [ ] `"use client"` / `@defer` / island boundaries as low in the tree as possible
- [ ] Server Actions/endpoints validate and authorize the input
- [ ] Impact measured (LCP/INP, JS size) — fe-web-platform
