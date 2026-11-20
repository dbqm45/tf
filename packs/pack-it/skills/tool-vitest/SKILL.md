---
name: tool-vitest
description: Use when writing tests in Vitest — it.each tables, doubles at ports and vi.when, fake time, browser mode, fast-check, Stryker with the command runner, v3–v5.
metadata:
  review: "2027-01-09"
  catalog: "Use when writing or running tests in Vitest 3–5: example tables with it.each and case ids, test doubles at ports (vi.fn, vi.when with onUnmatched, clearMocks defaults), fake timers and vi.setSystemTime, known defects with it.fails, property tests with fast-check, browser mode and projects for component tests, selecting tests (--changed, related, --project, --shard), mutation testing with Stryker on Vitest (the command runner, a false 0%, --mutate ranges, --incremental, the json report), version differences. Not for Jest (tool-jest), choosing which cases to test (qa-test-design), where expected values come from and what to do with surviving mutants (qa-spec-first-testing) or e2e tests (tool-playwright)."
  keywords: "Vitest, vi.fn, vi.when, vi.mock, stub, atrapa, zaślepka, dubler testowy, port, clearMocks, restoreMocks, mockReset, kontrolowany czas, sztuczne zegary, tryb przeglądarki, test.each, tabela przykładów, Stryker, mutanty, spec.ts, test double, fake timers, controlled time, browser mode, examples table, mutation testing"
---

# Vitest — tests, doubles, browser mode, mutation testing

Versions: written for Vitest 5.0, works from 3.0 (table below). Evidence of what was run: `skill.meta.json`.

## Writing tests
- **Example tables** with `it.each`; the case id and the source go into the name, the boundaries below/at/above:
  ```ts
  // Source: H1-AC2 "5% from 10 items" (business accounts)
  it.each([
    { id: 'TC-011', qty: 9,  expected: 900.00 },
    { id: 'TC-012', qty: 10, expected: 950.00 },
    { id: 'TC-013', qty: 11, expected: 1045.00 },
  ])('$id: $qty × 100.00 → $expected', ({ qty, expected }) => {
    expect(priceFor({ qty, unit: 100, business: true })).toBe(expected);
  });
  ```
  Expected values come from the specification (qa-spec-first-testing), never from running the code.
- Work in watch mode (`npx vitest`); a **new test must fail first**, for the right reason.
- **Environment:** pure domain logic in the default `node` environment; UI behaviour in **browser mode** (a real browser)
  rather than jsdom.
- **Known defect:** `it.fails('BUG-231: rounding at 100.00', …)` — the test passes while the bug exists and turns red when fixed;
  do not edit the expectation.
- **Property tests** with fast-check for invariants:
  ```ts
  import fc from 'fast-check';
  it('H2-AC1: split parts always add up to the amount', () => {
    fc.assert(fc.property(fc.integer({ min: 0, max: 10_000_00 }), fc.integer({ min: 1, max: 12 }), (cents, n) => {
      const parts = split(cents, n);
      return parts.length === n && parts.reduce((a, b) => a + b, 0) === cents && Math.max(...parts) - Math.min(...parts) <= 1;
    }));
  });
  ```

## Test doubles at ports
- Replace only what crosses a **port** (exchange rates, clock, payment gateway, repository). Preference: **fake** (a small
  working in-memory version) > **stub** (fixed answers) > **mock** (verifying calls). `vi.mock` of your own module is a smell —
  it couples the test to the file layout.
- **`vi.when`** (Vitest 5) — a stub that answers per arguments; with `onUnmatched: 'throw'` any call with undefined arguments fails
  loudly instead of returning `undefined`:
  ```ts
  const getRate = vi.fn<(from: string, to: string) => number>();
  vi.when(getRate, { onUnmatched: 'throw' }).calledWith('EUR', 'PLN').thenReturn(4.30);
  ```
  Check the exact option placement in the Vitest 5 API docs for your minor version. **Before Vitest 5** there is no `vi.when`:
  write the stub by hand — `vi.fn((from, to) => { if (from === 'EUR' && to === 'PLN') return 4.30; throw new Error('unexpected ' + from + '/' + to); })`.
- **`clearMocks` is `true` by default in Vitest 5** — call history is cleared before every test. Tests that counted calls across
  tests, or relied on history from `beforeAll`, change behaviour after an upgrade. `restoreMocks`/`mockReset` are still opt-in.

## Time
```ts
beforeEach(() => { vi.useFakeTimers(); vi.setSystemTime(new Date('2026-03-02T10:00:00Z')); });
afterEach(() => { vi.useRealTimers(); });
```
Advance with `vi.advanceTimersByTime(ms)` or `await vi.runAllTimersAsync()`.

## Browser mode and projects (component tests)
```ts
// vitest.config.mts (or "type": "module" in package.json — the config is ESM)
import { defineConfig } from 'vitest/config';
import { playwright } from '@vitest/browser-playwright';
export default defineConfig({ test: { projects: [
  { test: { name: 'unit', environment: 'node', include: ['src/**/*.spec.ts'] } },
  { test: { name: 'browser', include: ['src/**/*.browser.spec.ts'],
            browser: { enabled: true, provider: playwright(), instances: [{ browser: 'chromium' }] } } },
] } });
```
In the test: `import { page } from 'vitest/browser'` and `await expect.element(page.getByRole('button', { name: 'Save' })).toBeVisible()`.
Vitest 5 locators are strict: a locator that matches several elements fails. Component tests formerly written in
Playwright CT belong here.

## Choosing what to run
- `vitest run --changed origin/main` — tests affected by the diff; `vitest related src/discount.ts --run` — tests importing a file.
- `--project unit`, `--shard=1/3` (merge with `--merge-reports`).
- In an agent environment (the `AI_AGENT` variable set) Vitest 5 uses a minimal reporter and does not start watch mode; pass
  `--run` explicitly on older versions.

## Mutation testing with Stryker (StrykerJS 10 + Vitest 5)
- Use the **command runner**: `testRunner: "command"`, `commandRunner: { command: "npx vitest run" }`. On the factory's check the dedicated
  `@stryker-mutator/vitest-runner` reported a **false 0%** with Vitest 5, while the command runner gave 93.55% and one surviving mutant that pointed
  at a genuinely missing test.
- **Always sanity-check the score.** 0% (all mutants survived) or a suspicious 100% means the mutants are not activated or the
  tests do not run — fix the setup before reading results. Older Stryker/Vitest runner configs do not carry over.
- Mutate **domain logic only** (`mutate: ["src/domain/**/*.ts", "!src/**/*.spec.ts"]`).
- The command runner reruns the whole command per mutant, so narrow it:
  `npx stryker run --mutate "src/discount.ts:20-60"` for the changed lines before merge, `--incremental` to reuse earlier results.
- A run that finds nothing to test errors out; `--allowEmpty` accepts it deliberately (e.g. a PR with no domain changes).
- For agent triage use the **json** report (`reporters: ["json", "clear-text", "progress"]` → `reports/mutation/mutation.json`);
  there is no built-in markdown reporter. What to do with survivors: qa-spec-first-testing.

```json
{
  "testRunner": "command",
  "commandRunner": { "command": "npx vitest run --project unit" },
  "mutate": ["src/domain/**/*.ts", "!src/**/*.spec.ts"],
  "reporters": ["json", "clear-text", "progress"],
  "incremental": true
}
```

## Version-dependent
| Version | What changed |
|---|---|
| 3.0 | minimum supported baseline |
| 3.2 | `projects` in the config (replaces the workspace file) |
| 4.0 | browser mode stable; providers as packages (`@vitest/browser-playwright`); workspace removed; `coverage.all` removed; `poolOptions` flattened; `basic` reporter removed |
| 5.0 | Node ≥ 22.12, Vite ≥ 6.4; `clearMocks: true` by default; `vi.when`; strict browser locators; reporter output in `.vitest/` |

## Example
"Stryker on Vitest 5 shows 0% on `src/discount.ts`":
1. Switch to `testRunner: "command"` with `npx vitest run`.
2. Run `npx stryker run --mutate "src/discount.ts"`; expect a plausible score, not 0%.
3. Still 0% → run `npx vitest run` alone: do the tests pass and import `src/discount.ts` (not a built copy in `dist/`)?
4. Read survivors from `reports/mutation/mutation.json`, triage per qa-spec-first-testing.

## Sources
- vitest.dev: blog (release posts 3.2, 4.0, 5.0), Migration guide, Browser mode, Mocking, Test filtering (accessed 2026-09-27).
- stryker-mutator.io: StrykerJS configuration and command runner docs; `npx stryker run --help` (accessed 2026-09-27).
- fast-check.dev — properties and arbitraries (accessed 2026-09-27).
- Factory measurement 2026-09-27 (vitest 5.0.2, Stryker 10.0), recorded in `skill.meta.json`.
