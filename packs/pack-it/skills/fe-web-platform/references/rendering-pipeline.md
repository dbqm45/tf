# Event loop and Critical Rendering Path

Moved from the frontend-developer import (`senior.md`: Event Loop — only a pointer there, the content here; Critical
Rendering Path — full). Diagnosing **why** a page is slow before you reach for metrics (core-web-vitals.md).

## The event loop in the browser

The main thread executes alternately: **one task** (macrotask: a script, an event, `setTimeout`, a message) →
**all microtasks** (`Promise.then`, `await`, `queueMicrotask`, `MutationObserver`) → possibly
**rendering** (`requestAnimationFrame` → style → layout → paint → composite), usually every ~16 ms at 60 Hz.

Consequences:
- As long as a task + its microtasks are running, the browser **does not render and does not handle input**. A task
  > 50 ms is a **long task** — the main cause of bad INP.
- An endless chain of microtasks will starve rendering just like a synchronous loop.
- `setTimeout(fn, 0)` ≠ immediately: it is a new task after the render/other tasks; the minimum delay grows to
  4 ms after nesting, and in background tabs timers are throttled.
- Split long work: `await scheduler.yield()` (Chromium; fallback `setTimeout`/`MessageChannel`),
  `requestIdleCallback` for non-urgent work, a Web Worker for CPU computation (parsing, compression, filtering
  large sets). Visual updates — in `requestAnimationFrame`.
- Diagnose memory leaks in DevTools (heap snapshot, "Detached elements"): typical sources are listeners and timers without
  cleanup and closures holding detached DOM nodes.

## Critical Rendering Path (CRP)

1. **HTML → DOM** — streaming parsing. A `<script>` without `async`/`defer`/`type="module"` **blocks the parser** until it
   is downloaded and executed. `defer` and modules execute after parsing, in order; `async` — as soon as they are downloaded.
2. **CSS → CSSOM** — CSS is **render-blocking**: the browser does not paint content without a complete CSSOM (a later stylesheet
   may override rules). Critical CSS inline or small; the rest `media`/loaded later.
3. **DOM + CSSOM → render tree** — `display: none` elements do not enter it; `visibility: hidden` does (takes up
   space, invisible).
4. **Layout (reflow)** — the geometry of every element.
5. **Paint** — pixels on layers (colours, text, shadows, images).
6. **Composite** — compositing the layers (GPU).

The cost of changes:
- Geometry (`width`, `top`, `margin`, adding a node) → layout + paint + composite — the most expensive.
- Colour/background → paint + composite.
- `transform`, `opacity` (on its own layer) → composite only — that is why you animate them, not `top/left/width` (fe-css).
- **Layout thrashing** — interleaving style writes and geometry reads (`offsetHeight`, `getBoundingClientRect`) in
  a loop forces a synchronous layout on every read. First all the reads, then all the writes
  (or the writes in `requestAnimationFrame`).
- Limit the scope of recalculations: `contain: layout paint`, `content-visibility: auto` for off-screen sections.

## Loading priorities

- `<link rel="preload">` for a critical resource discovered late (a font, an LCP image from CSS); `rel="preconnect"` to
  key origins; `fetchpriority="high"` on the LCP image, `"low"` on less important ones.
- `rel="modulepreload"` for ES modules; Speculation Rules (`<script type="speculationrules">`) to prefetch/prerender
  the next pages in an MPA.
- Fonts: `font-display: swap`/`optional` + `size-adjust`/fallback metrics, so that the swap does not shift the layout.
