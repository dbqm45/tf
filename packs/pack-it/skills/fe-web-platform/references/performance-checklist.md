# Frontend performance checklist — before release and in review

Based on the roadmap.sh list "Frontend Performance Best Practices" and its source (Front-End-Performance-Checklist,
MIT), with corrections where the list is outdated or contradicts itself. The measure of success is **Core Web Vitals
from field data** (`core-web-vitals.md`: LCP ≤ 2.5 s, INP ≤ 200 ms, CLS ≤ 0.1 at the 75th percentile), not a single
Lighthouse score. Tick only what you have measured.

## High priority
- [ ] **Page weight budget** — treat the list's starting point "< 1500 KB, ideally < 500 KB" as an upper bound for
  the whole page. More important is the JS budget per route, set from measurements on users' devices (an average Android
  phone, a slower network) and enforced in CI (the "Budgets in CI" section).
- [ ] **"Loading < 3 s"** → replace it with the CWV and TTFB thresholds. **TTFB** good ≤ 0.8 s (75th percentile; the list gives 1.3 s —
  that is the old limit). TTFB is affected by: CDN caching for public pages, SSR without request chains, an early
  response (`103 Early Hints`) where the server and CDN support it.
- [ ] **Compression** Brotli (or gzip) for text: HTML, CSS, JS, JSON, SVG. Do not recompress images and WOFF2
  fonts (already compressed).
- [ ] **Number of requests**: with HTTP/2 and HTTP/3 many small files are no longer a problem, and merging everything into one
  file breaks caching (a change of one line invalidates the whole). Limit **render-blocking** requests and dependency
  chains (a request that discovers further ones), not the number itself.
- [ ] **HTTP cache**: resources with a hash in the name (`app.3f9a1c.js`) — `Cache-Control: public, max-age=31536000, immutable`;
  HTML — `no-cache` (always validation), so that a new release is visible immediately (be-api-design, `http-in-practice.md`).
- [ ] **Non-blocking JavaScript**: modules and scripts with `defer` (order preserved) or `async` (independent, e.g.
  analytics); no synchronous `<script>` in `<head>` without a reason. Minification and dead code removal are done by
  the builder (esbuild in Angular, Vite) — check that it works in production mode.
- [ ] **CSS**: minified, non-blocking apart from the critical part. **Critical CSS inline** (what is needed for the first
  screen) and the rest asynchronously — this is an exception to the "avoid inline CSS" rule, not a contradiction. In Angular with
  SSR/prerendering the critical styles are inserted by the builder (the `inlineCritical` option).
- [ ] **Images**: a matching format (AVIF or WebP for photos with a JPEG fallback, SVG for icons and vector illustrations,
  PNG only where lossless is needed), compression, a size close to the displayed one (`srcset` and `sizes`).
- [ ] **HTTPS** everywhere (a condition of HTTP/2 and HTTP/3, service workers and many APIs) and the same protocol for all
  resources — mixed content is blocked.
- [ ] **No 404s** for resources (wasted requests, often icons and source maps) — checked in an E2E test or a crawler.
- [ ] **Iframes**: only the needed ones, with `loading="lazy"` below the first screen; embeds (video, maps, chats)
  through a **facade** — an image with a button, and the full script only after the click.
- [ ] **Style complexity**: avoid very deep selectors and expensive properties on large surfaces;
  `content-visibility: auto` for long off-screen sections (fe-css).

## Medium priority
- [ ] HTML minified at generation (a small gain with compression — not a priority).
- [ ] **CDN** for static resources and public pages with edge caching.
- [ ] **Images**: `width` and `height` (or `aspect-ratio`) always — no layout shifts; lazy loading below
  the first screen, but **the LCP image never lazy**, instead with `fetchpriority="high"`. No Base64 images except
  very small ones (they enlarge HTML/CSS and bypass the cache). In Angular `NgOptimizedImage` (`ngSrc`, `priority` for LCP)
  enforces these rules.
- [ ] **Inline scripts**: as few as possible (they block the parser and require exceptions in the CSP — fe-web-platform: security).
- [ ] **Dependencies**: size and duplicates checked when adding (bundlephobia, the builder report). The list says
  "update dependencies" — in the factory the agent **does not bump the project's dependencies without a human's request**. An update is
  a separate task with tests (core-stack-sync, ops-supply-chain-security).
- [ ] **Problems in JS**: long tasks > 50 ms in interactions (INP), memory leaks, repaints — a profile in DevTools
  (Performance) on a throttled CPU (`rendering-pipeline.md`).
- [ ] **Service worker** only with a real need for offline or an application cache (`service-workers.md`); heavy
  computation rather in a Web Worker.
- [ ] **Cookies**: small and few — they travel with **every** request to the domain, including for images. Browsers
  limit the size of a single cookie to approx. 4 KB. Static resources from a domain or CDN without cookies.

## Low priority (but cheap)
- [ ] **Resource hints**: `preconnect` to 1–3 critical domains (fonts, API, image CDN); `preload` only for
  a resource needed early but discovered late (a font, an LCP image from CSS) — too many preloads take
  bandwidth from more important ones. The next page: `prefetch` or speculation rules (Speculation Rules API, Chromium) for
  a very likely navigation.
- [ ] **Merging CSS into one file** — outdated with HTTP/2. Better CSS per route or component (loaded together
  with the code) and good caching.
- [ ] **Unused CSS** removed at build time (e.g. component styles with encapsulation, tools like PurgeCSS for
  utility libraries); coverage in DevTools (Coverage) shows the scale.
- [ ] **Fonts**: WOFF2 only, a character subset (with Polish characters!), as few weights as possible (or a variable font),
  in total usually < 100–300 KB; `font-display: swap` (or `optional` for decorative fonts) instead of invisible text;
  matching the fallback font metrics (`size-adjust`) limits the shift on swap.
- [ ] **Dependency size** monitored in CI (section below).

## What the list lacks but is worth having
- **bfcache** (the back/forward cache): an instant return to the previous page. Do not use the
  `unload` event (instead `pagehide` or `visibilitychange`); `Cache-Control: no-store` for HTML usually excludes the page
  from bfcache — use it only where necessary (sensitive data). Check: DevTools → Application → Back/forward cache.
- **Third-party scripts** (analytics, tags, chats, A/B tests): an inventory with an owner and a cost, loading after
  interaction or idle, measuring their share in INP; each is also a supply chain risk (SRI, CSP — fe-architecture).
- **Server-side rendering and hydration**: in Angular SSR with incremental hydration and `@defer` for heavy
  sections below the first screen (fw-angular).

## Budgets in CI
- Angular: `budgets` in `angular.json` (e.g. the size of `initial` and `anyComponentStyle` with a warning and error threshold) —
  the build fails when exceeded.
- Lighthouse CI (or similar) on a few key pages with assertions (LCP, CLS, TBT, resource weight) — lab
  results as a regression gate, not a substitute for field data.
- Bundle size per route from the builder report compared with the main branch in a PR comment.
- Field data (RUM: the `web-vitals` library sending to your own analytics, CrUX for public pages) reviewed
  after every release (ops-observability).

## Sources
- [roadmap.sh — Frontend Performance Best Practices](https://roadmap.sh/frontend-performance-best-practices);
  [Front-End-Performance-Checklist](https://github.com/thedaviddias/Front-End-Performance-Checklist) (MIT)
- web.dev: Core Web Vitals, TTFB, bfcache, Optimize resource loading; Angular documentation: budgets, NgOptimizedImage,
  SSR and hydration
Described in our own words, with corrections.
