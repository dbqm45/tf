---
name: fe-web-platform
description: Use for browser APIs and accessibility — fetch, DOM, event loop, Core Web Vitals, service workers, WCAG.
metadata:
  review: "2027-10-20"
  keywords: "wspierane przeglądarki, które przeglądarki wspieramy, polityka wsparcia przeglądarek, zgodność przeglądarek, browserslist, Baseline, Widely available, Newly available, caniuse, eslint-plugin-compat, use-baseline, polyfill, wykrywanie funkcji, feature detection, @supports, progressive enhancement, macierz przeglądarek, Safari, iPhone, iOS, WebKit, Firefox, cross-browser, nie działa w Safari, wyszukiwarka na żywo, wyniki starszego zapytania, wyścig odpowiedzi, AbortController, czysty fetch, response.ok, supported browsers, which browsers we support, browser support policy, browser compatibility, browser matrix, does not work in Safari, live search, results of an older query, response race, plain fetch"
  catalog: "Use for browser APIs regardless of the framework — fetch and cancellation, DOM events, the event loop and rendering, Core Web Vitals, storage, service workers, i18n (Intl; the whole system — eng-i18n), DOM security (XSS), accessibility and HTML semantics (ARIA, focus, keyboard, live regions, WCAG) and supported browsers (browserslist, Baseline, compatibility lint, a Chromium/Firefox/WebKit test matrix, real Safari and iOS). Not for syntax (lang-*), framework conventions (fw-*), styles (fe-css) or application structure (fe-architecture)."
---

# The web platform (the browser)

## Network requests
```js
const res = await fetch(url, { signal });
if (!res.ok) throw new HttpError(res.status, await res.text());
const data = await res.json(); // data from the network is untrusted — validate at the boundary
```
- `fetch` does not throw on 4xx/5xx — always check `res.ok`. Parameters in the URL through `encodeURIComponent`/`URLSearchParams`.
- Cancel through `AbortController` when leaving a view and in "live" search; ignore the responses of stale requests.
  Timeout: `AbortSignal.timeout(ms)`, combining signals: `AbortSignal.any([...])`.
- A conflict (409) and a business rejection (422) are normal results — show them to the user, do not treat them as failures.
- Realtime: SSE (`EventSource`) for a server→client stream, WebSocket for two-way; always with reconnection and backoff.

## Performance
- The main thread: tasks > 50 ms block input (bad INP) — split the work (`scheduler.yield()`), heavy computation to a Web Worker.
- Debounce for search fields (~250–300 ms), throttle/`requestAnimationFrame` for scroll/resize, `passive: true` for scroll/touch.
- Event delegation for long lists; virtualization with thousands of elements.
- Lazy loading of heavy modules (`import()`) and images below the fold (`loading="lazy"`); the LCP image — `fetchpriority="high"`, never lazy.
- Images/iframes with `width`/`height` (no CLS). Do not interleave layout reads and writes in a loop (layout thrashing).
- Measure LCP ≤ 2.5 s, INP ≤ 200 ms, CLS ≤ 0.1 on field data (p75), not only in Lighthouse.

## Security
- Never `innerHTML` with user or AI model data — `textContent`, the DOM API or sanitization (DOMPurify / Sanitizer API `setHTML`); trust the framework's escaping and do not bypass it.
- A ban on `eval`, `new Function`, `setTimeout("string")`; URLs from the user — only the `http(s):` scheme.
- Do not keep session tokens in `localStorage` if `HttpOnly` cookies can be used.
- CSP without `unsafe-inline` (nonce + `strict-dynamic`), Trusted Types where available. Patterns — fe-architecture (`references/security/`).

## Storage and browser state
- `localStorage`/`sessionStorage` only for preferences and convenience (it can be empty or unavailable) — in `try/catch`; larger data — IndexedDB.
- State that must survive and be consistent belongs to the backend. A service worker only with a real offline/PWA need.

## Device and system APIs
- Before adding a library check the platform API (sharing, clipboard, tab synchronization, wake lock, files), but
  also its support: many work only in Chromium. Feature detection, HTTPS, a call inside a click handler, permissions
  in context, a fallback path, access behind an adapter, an SSR guard — `references/native-browser-apis.md`.

## Accessibility and semantics
- **Native HTML first**: `button` for actions, `a href` for navigation, `label` for fields, landmarks (`header`, `nav`, `main`, `footer`), headings in order. A `div` with `click` is a bug.
- **ARIA is the last resort** — only for widgets without a native equivalent; bad ARIA is worse than none. A role does not add behaviour — you write the keyboard handling yourself.
- Dialogs: `<dialog>` + `showModal()` (focus, Escape, inert background, focus return); `popover` for menus/tooltips.
- Focus: after an overlay opens, into it; after it closes — back; after SPA navigation onto the `<h1>` of the new view; a visible `:focus-visible`.
- Keyboard: everything reachable with Tab; WAI-ARIA APG patterns (arrows in lists/tabs, Escape closes, roving tabindex).
- Asynchronous messages (e.g. "slot taken", "saved") in an `aria-live` region (`role="status"`, urgent — `role="alert"`), the region present in the DOM beforehand.
- Forms: the error linked to the field (`aria-describedby`, `aria-invalid`), native `required`, focus on the first error after submit.
- Target: **WCAG 2.2 AA** (a legal requirement in the EU — European Accessibility Act since 06.2025). Automated tools catch only part — test with the keyboard and a screen reader.

## Supported browsers
- **A policy recorded in the repo:** one `browserslist` query (`.browserslistrc` or `package.json`) for transpilation,
  CSS prefixes and lint. You describe decisions in Baseline language: *Widely available* — you use it without hesitation; *Newly
  available* — with feature detection and a fallback path. You choose the policy from user data and contracts with the client.
- **Feature detection, not browser detection:** `'x' in window`, `CSS.supports()`, `@supports`; never `userAgent`.
  Progressive enhancement — the basic path works without the new feature.
- **A polyfill only with a budget:** loaded conditionally, its size within the bundle budget; instead of a polyfill often a fallback path.
- **Code checked against the policy in CI:** JS — `eslint-plugin-compat` (it reads `browserslist`); CSS — the
  `css/use-baseline` rule from `@eslint/css` or a stylelint plugin, with the same Baseline threshold as the policy.
- **Test matrix:** Playwright `chromium` in every PR, `firefox` and `webkit` nightly (qa-regression, tool-playwright).
  WebKit from Playwright is not Safari — real Safari and iOS (a device or the cloud, paid) only with a business
  requirement or reports from those users.
Tools, queries and the matrix: `references/browser-compatibility.md`.

## i18n
- Texts in ICU MessageFormat (plurals in the message), formats exclusively through `Intl.*`; `<html lang dir>`; layout on CSS logical properties (RTL). The whole system (backend, time zones, currencies, translation flow): eng-i18n.

## References index
- `rendering-pipeline.md` — event loop (tasks/microtasks, long tasks), Critical Rendering Path, the cost of style changes, loading priorities.
- `performance-checklist.md` — a performance checklist before release (priorities, corrections of outdated recommendations, bfcache, budgets in CI, Angular).
- `core-web-vitals.md` — LCP/INP/CLS: thresholds, causes, fixes; field vs lab data.
- `seo-public-pages.md` — a public application (SSR/prerendering): indexing, metadata, structured data, AI bots.
- `native-browser-apis.md` — 21 APIs (Web Share, BroadcastChannel, Wake Lock, Clipboard, File System Access, WebOTP…): a support map, fallback paths, what not to use.
- `service-workers.md` — lifecycle, cache strategies, updates, push/background sync, when not to.
- `browser-compatibility.md` — the support policy (browserslist, Baseline), feature detection, polyfills, compatibility lint, the test matrix and real devices.
- `i18n.md` — i18n vs l10n, ICU, Polish plurals, `Intl`, RTL, pseudolocalization.
- `accessibility/` — read the file depending on the problem:
  `semantic-html` (native elements), `aria-roles-and-attributes` (roles, states, combobox 1.2), `accessible-forms`,
  `keyboard-navigation` (roving tabindex, shortcuts), `focus-management` (modal, route, removing from a list), `focus-trap`
  (`<dialog>`, `inert`), `live-regions` (polite/assertive), `wcag-levels` (A/AA/AAA, WCAG 2.2, EAA/ADA).

## Checklist
- [ ] `res.ok` checked, requests cancelled when leaving a view
- [ ] No `innerHTML`/`eval` with untrusted data
- [ ] Native interactive elements, keyboard support and a visible focus
- [ ] Asynchronous messages announced (live region), form errors linked to the fields
- [ ] No long tasks in interactions; images with dimensions; LCP not lazy
- [ ] Formats through `Intl`, no concatenated texts
- [ ] The browser policy in `browserslist`, a compatibility lint in CI, a test matrix (PR: chromium, nightly: firefox and webkit)
- [ ] Device APIs with feature detection and a fallback path; unused features disabled in `Permissions-Policy`

Sources: frontendpatterns.dev (Den Odell) — accessibility patterns; WAI-ARIA APG, WCAG 2.2 (W3C), web.dev — described in our own words.
