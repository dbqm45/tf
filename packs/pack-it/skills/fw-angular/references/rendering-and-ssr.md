# Rendering, SSR, hydration and `@defer`

Contents: 1. Choosing the rendering approach · 2. Rendering mode per route · 3. Hydration · 4. Server-compatible
code · 5. Request data and transfer cache · 6. `@defer` · Sources

## 1. Choosing the rendering approach
| Approach | When | Cost |
|---|---|---|
| **CSR** (the default) | dashboards, internal tools, content behind login | weak SEO, content only after the JS loads |
| **SSG** (prerendering) | marketing pages, a blog, documentation, a catalogue known at build time | a content change requires a rebuild; not for user data |
| **SSR** | product pages, news, dynamic content with SEO | a server or a serverless environment, higher cost and latency |

You choose the approach per route, not for the whole application.

## 2. Rendering mode per route
- In the server configuration a `ServerRoute[]` array assigns routes `RenderMode.Client`, `RenderMode.Prerender` or
  `RenderMode.Server`; plugged in through `provideServerRendering(withRoutes(serverRoutes))`.
- Rules:
  - specific paths before `**`; server paths consistent with the router routes;
  - `Prerender` only when the data is available at build time. The parameters of dynamic routes are returned by
    `getPrerenderParams()`: `inject()` before the first `await`, keys equal to the parameter names, values as text;
  - paths not generated at build time are handled by `fallback` (`PrerenderFallback.Server`, the default, or
    `Client`, `None`);
  - static headers in `headers`; `status` only for CSR and SSR routes.

## 3. Hydration
- `provideClientHydration()` in the configuration shared by the browser and the server. Since v22 it enables by default
  incremental hydration and replay of events from before hydration; do not add the deprecated `withIncrementalHydration()`.
- **The DOM from the server and from the browser must be identical:**
  - no different templates depending on `isPlatformBrowser`;
  - no manual inserting, removing and moving of DOM nodes;
  - valid HTML; `preserveWhitespaces` the same on both sides.
- `ngSkipHydration` on a component is a last resort and a temporary solution: Angular then renders the whole subtree from
  scratch.

## 4. Server-compatible code
- On the server there is no DOM, `localStorage` or layout measurement. You put browser-only work
  in `afterNextRender`, `afterEveryRender` or `afterRenderEffect` (they do not run on the server).
- `afterRenderEffect` splits work into phases in the order `earlyRead` → `write` → `mixedReadWrite` → `read`: in the write
  phase you do not read the layout, in the read phase you do not write; this prevents forced layout recalculations.
- `DOCUMENT` from injection instead of the global `document`; different implementations for the browser and the server behind one
  application token.
- **No leaks between requests:** request-dependent values do not go into module variables or into top-level `useValue`
  providers; a factory creates them.

## 5. Request data and transfer cache
- Tokens from `@angular/core`: `REQUEST` (the `Request` object), `RESPONSE_INIT` (the response status and headers),
  `REQUEST_CONTEXT` (the context from the server adapter). They can be `null` (CSR, SSG, build), so you always check that.
- You leave the HTTP transfer cache at its default, but you exclude user-dependent requests
  (`withHttpTransferCacheOptions({ filter })` or `transferCache: false` in the request). You do not transfer authenticated
  responses into the page HTML.
- Your own asynchronous work that the server must wait for before sending the HTML: `PendingTasks` or
  `pendingUntilEvent()`.
- A production `allowedHosts` list without wildcards; `trustProxyHeaders` only behind a trusted proxy that
  replaces the forwarded headers.

## 6. `@defer`
- Only standalone dependencies that are not referenced outside the block in the same file (also
  in view queries) go into the block. Imports through barrel files (`index.ts`) can break this.
- The `@placeholder`, `@loading` (with `after` and `minimum` against flickering) and `@error` blocks load immediately, so they are small.
- Triggers: `on idle` (the default), `viewport`, `interaction`, `hover`, `immediate`, `timer`; `when <expression>`
  fires once, when the expression becomes true. `prefetch on …` fetches the code earlier.
- `viewport`, `interaction` and `hover` need a placeholder with one root element or a reference to an element.
- **SSR:** the server renders only the placeholder and does not run triggers. When the content should be rendered on the server
  and come alive later, add `hydrate on …` (e.g. `@defer (on viewport; hydrate on interaction)`).
- **Layout stability:** you do not defer content visible immediately or the LCP element; the placeholder has the dimensions of the target
  content; nested blocks have different triggers.

## Sources
- angular/skills, the `angular-developer` skill (angular-developer/references files: rendering-strategies, server-side-rendering,
  deferrable-views, effects), commit 43ec6adc2b35049734d0d114e3948e022f1cd1e7 of 2026-10-21, MIT licence,
  author Google LLC. Described in our own words; accessed 2026-10-21.
