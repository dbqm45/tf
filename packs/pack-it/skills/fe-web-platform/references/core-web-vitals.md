# Core Web Vitals and performance measurement

Moved from the frontend-developer import (`senior.md`, "Core Web Vitals"), supplemented with the 2026 tools.

## Three metrics (the "good" threshold at the 75th percentile of visits)

| Metric | Measures the phase | Good | Typical causes of a bad result | Typical fixes |
|---|---|---|---|---|
| **LCP** — Largest Contentful Paint | loading | ≤ 2.5 s | slow TTFB, render-blocking CSS/JS, the LCP image discovered late or lazy, heavy images | cache/CDN, SSR/SSG, `fetchpriority="high"`, preload, modern formats (AVIF/WebP), `srcset` |
| **INP** — Interaction to Next Paint | interactivity | ≤ 200 ms | long tasks, heavy handlers, large re-renders, hydration | splitting the work (`scheduler.yield()`), Web Worker, a smaller render scope, debounce, less JS |
| **CLS** — Cumulative Layout Shift | visual stability | ≤ 0.1 | images/iframes/ads without dimensions, font swapping, content injected above existing content | `width`/`height` or `aspect-ratio`, reserving space, `font-display` + fallback metrics, `transform` animations |

- **INP replaced FID** (March 2024): FID measured only the delay until the handler started, INP — the whole time from
  the interaction to the repaint, from the worst interactions in the visit.
- **TTI** is no longer a Lighthouse metric; auxiliary ones: TTFB, FCP, TBT (the lab substitute for INP).
- Each metric is a different phase — a good LCP says nothing about INP. First establish **which** one is bad, then look for the cause
  (rendering-pipeline.md).

## Field vs lab data

- **Field (RUM)** — real users: CrUX (Chrome UX Report), PageSpeed Insights, the `web-vitals` library
  (`onLCP`, `onINP`, `onCLS` with attribution — which element/script is to blame) sent to your own telemetry
  (ops-observability). These decide the assessment and SEO.
- **Lab** — Lighthouse, DevTools Performance (the panel also shows local LCP/INP/CLS live), WebPageTest;
  repeatable, for diagnosis and regressions in CI (Lighthouse CI, bundle size budgets).
- The Long Animation Frames API (LoAF) points to the scripts responsible for slow frames — better than the Long Tasks API.

## Rules

- Measure before and after a change; optimize the worst percentile of real devices (an average Android, a poor network), not
  the developer's MacBook.
- Performance budgets (JS size per route, LCP) in CI stop regressions before they reach users.
- The pre-release checklist and budgets in CI: `performance-checklist.md`.
- Patterns: code splitting, lazy loading, debounce, memoization — fe-architecture (`references/performance/`).
