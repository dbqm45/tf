# Browser compatibility — policy, checking, tests

> **Contents:** 1. Support policy · 2. Feature detection and progressive enhancement · 3. Polyfills · 4. Checking code against the policy (CI) · 5. Test matrix · Example · Sources (accessed 2026-10-18)

Facts checked on 2026-10-18 in the project repositories and on npm (sources at the end). Package versions change quickly —
before entering one into a project check `npm view <package> version`.

## 1. Support policy
**Baseline** (WebDX Community Group, the `web-features` package) describes whether a feature works in the core browser set:
Chrome (desktop and Android), Edge (desktop), Firefox (desktop and Android), Safari (macOS and iOS).

| Level | Meaning | How you use it |
|---|---|---|
| *Newly available* | works in the current stable versions of all browsers in the set | with feature detection and a fallback path |
| *Widely available* | 30 months have passed since the day the last browser in the set added support | without hesitation |
| *Baseline YYYY* | all the features that were Newly available by the end of the year YYYY | a target fixed in time, e.g. in a contract with the client |
| outside Baseline | missing in at least one browser in the set | only as progressive enhancement |

The policy is a product decision, not a developer's. The decision sources are analytics data (the browsers' share among
users), contracts with clients (e.g. Safari required on iPads in the field), the market and the cost of testing. Record it in an ADR
(docs-tech-writing) and in the repo.

### browserslist — one source for the tools
A `.browserslistrc` file (in the current or a parent directory) or the `browserslist` key in `package.json`. The same
query is used by the transpiler, CSS prefixes and the JS lint.

```
# .browserslistrc — an example of a policy based on Baseline (browserslist ≥ 4.26)
baseline widely available
```

| Query | Meaning |
|---|---|
| `baseline widely available` | browsers compatible with Widely available as of today |
| `baseline newly available` | browsers compatible with Newly available |
| `baseline 2024` | a yearly target |
| `baseline widely available on 2026-01-01` | the state as of a date (repeatable builds) |
| `... with downstream` | adds browsers on an engine from the set (e.g. Opera, Samsung Internet) |
| `defaults` | `> 0.5%, last 2 versions, Firefox ESR, not dead` — based on usage shares, not on Baseline |

- Share-based queries (`> 0.5%`, `last 2 versions`) depend on the `caniuse-lite` database — update it
  (`npx update-browserslist-db@latest`) regularly, e.g. as part of dependency updates.
- The Baseline data is supplied by the `baseline-browser-mapping` package; it warns when the data is more than 2 months old. Do not silence
  the warning with an environment variable — update the dependencies.
- Check what the query actually produced: `npx browserslist` prints the list of versions.

## 2. Feature detection and progressive enhancement
```js
if ('share' in navigator) { /* Web Share */ } else { /* copy the link */ }
if (CSS.supports('container-type: inline-size')) { /* ... */ }
```
```css
.card { display: block; }
@supports (container-type: inline-size) { .list { container-type: inline-size; } }
```
- Never `navigator.userAgent` for decisions about features: it lies, it changes and it blocks browsers that do have the feature.
- The basic path (a form, a link, content) works without JS and without the new feature; the novelty enhances it.
- The support map of device APIs and fallback paths: `native-browser-apis.md`.

## 3. Polyfills
- First the question: is a fallback path enough? A polyfill is code sent to everyone or loaded conditionally.
- Conditional loading (`if (!('x' in window)) await import('./polyfill-x.js')`), not a global package "for everything".
- The size of polyfills within the bundle budget (`performance-checklist.md`); you remove them when the policy stops covering
  the browsers that needed them.
- A polyfill from a third-party CDN is a supply chain risk — only from your own build.

## 4. Checking code against the policy (CI)
| Area | Tool | Policy source | Status |
|---|---|---|---|
| JS (browser APIs) | `eslint-plugin-compat` | `browserslist` from `package.json` | community |
| CSS in ESLint | `@eslint/css`, the `css/use-baseline` rule (by default `available: "widely"`; options `"newly"` or a year) | the rule's own option | official ESLint package |
| CSS in stylelint | `stylelint-plugin-use-baseline`, the `plugin/use-baseline` rule | its own option | community |

- Set the threshold in the CSS rules in line with `browserslist` — two policy sources are a risk of divergence; record this in an ADR.
- `css/use-baseline` does not report features used inside `@supports` — this encourages the correct pattern.
- Exceptions (`allowProperties` etc.) with a comment on why the feature is safe (e.g. it has a fallback path).
- The lint does not replace tests: it does not see implementation bugs or differences in engine behaviour.

## 5. Test matrix
| Layer | Browsers | When |
|---|---|---|
| PR | Playwright `chromium` | every PR |
| nightly | `chromium`, `firefox`, `webkit` + mobile devices (`devices['iPhone 13']`, `devices['Pixel 7']`) | once a day (qa-regression) |
| before release | selected paths on real Safari and iOS | when the policy or reports require it |
| branded Chrome/Edge | `channel: 'chrome'` or `'msedge'` | when a feature depends on the branded browser (e.g. codecs, DRM) |

```ts
// playwright.config.ts — fragment
projects: [
  { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
  { name: 'webkit', use: { ...devices['Desktop Safari'] } },
  { name: 'mobile-safari', use: { ...devices['iPhone 13'] } },
],
```
Running only one project in a PR: `npx playwright test --project=chromium`. Tool details: tool-playwright.

**WebKit from Playwright is not Safari.** Playwright builds WebKit from the latest sources (often before the release in Safari),
with its own patches, and it does not work with branded Safari. System-dependent features (e.g. codecs) differ between
platforms; the closest to Safari is WebKit run on macOS. The `iPhone 13` emulation changes the screen, touch and the user-agent,
not the engine or the system. Therefore:
- you reproduce bugs reported from iPhones first in `webkit` with device emulation; when they do not reproduce — on
  a real device (Safari Web Inspector on macOS) or in a device cloud;
- a cloud of real devices is paid — only with a business requirement, for a few critical paths, with a budget
  (core-cost-control).

**iOS:** outside the EU all browsers on iOS use WebKit, so "Chrome on an iPhone" is in practice the Safari engine.
In the EU since iOS 17.4 (iPadOS 18) Apple allows other engines for browsers with the Web Browser Engine entitlement
(developer.apple.com/support/alternative-browser-engines, accessed 2026-10-20). No released browser with Gecko or Blink
on iOS in the EU was found (as of 2026-10-20, a search) — test on WebKit in the EU as well.

## Example
**Situation:** a B2B SaaS, clients in the EU; analytics: 61% Chrome, 22% Safari (half of which iOS), 9% Edge, 6% Firefox.
Reports "it does not work on the iPad" after rolling out CSS nesting and `:has()`.
**Result (summary):**
- Policy: `baseline widely available` in `.browserslistrc`, an ADR with the analytics data; Newly available only with `@supports`.
- CI: `eslint-plugin-compat` for JS, `css/use-baseline` with `available: "widely"` for CSS; existing violations on
  an exception list with a fix deadline.
- Tests: PR — `chromium`; nightly — three engines and `iPad (gen 7)`; before release — login and payment on a real iPad.

## Sources (accessed 2026-10-18)
- web-platform-dx/web-features, `docs/baseline.md` — definitions, the browser set, 30 months.
- browserslist README and CHANGELOG — Baseline queries (since 4.26.0), configuration files, `defaults`.
- browserslist/update-db README; web-platform-dx/baseline-browser-mapping README.
- eslint/css, `docs/rules/use-baseline.md`; amilajack/eslint-plugin-compat README; ryo-manba/stylelint-plugin-use-baseline.
- microsoft/playwright, `docs/src/browsers.md` (projects, channels, WebKit vs Safari), `docs/src/emulation.md`.
- developer.apple.com/support/alternative-browser-engines/ — engines other than WebKit in the EU.
The web.dev and MDN pages were unreachable from the session — the Baseline definitions were taken from the specification repository.
Described in our own words.
