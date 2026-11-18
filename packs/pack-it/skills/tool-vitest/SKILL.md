---
name: tool-vitest
description: Use for tests in Vitest — structure, tables of examples, test doubles, controlled time, browser mode, Stryker.
metadata:
  review: "2027-01-09"
  catalog: "Use for unit, integration and component tests in Vitest — test structure, tables of examples, test doubles (vi.fn, vi.when), controlled time, projects, browser mode, coverage, mutation testing with Stryker, version migrations. Not for oracle rules (qa-spec-first-testing) or Jest (tool-jest)."
---

# Vitest

## Rules
1. **A table of examples from the specification** (`it.each`) with the case ID and a comment on where the expected value comes from; boundaries: below/at/above.
2. **The test first and red** — run `vitest` in watch mode; a new test must fail for the right reason (qa-spec-first-testing).
3. **Domain logic without a framework and DOM** — the `node` environment; DOM/components in **browser mode** (a real browser)
   instead of jsdom, when UI behavior matters.
4. **Test doubles at the boundaries (ports), not inside a module:** fake > stub (`vi.when(...).calledWith(...).thenReturn(...)`) > mock.
   `vi.mock` of your own modules only exceptionally — a sign of a bad split of dependencies.
5. **Time:** `vi.useFakeTimers()` + `vi.setSystemTime(...)`, restored in `afterEach(() => vi.useRealTimers())`.
6. **A known defect:** `it.fails('TC-020 (BUG-7): …')` — the test stays as it is in the specification; only a new source changes the expectation.
7. **Properties** (fast-check) for calculations and invariants.

## Patterns (verified: Vitest 5.0, fast-check 4, Chromium)
```ts
import { describe, it, expect, vi } from 'vitest';
import fc from 'fast-check';

describe('H1-AC2 quantity discount', () => {       // source: requirements.md "5% from 10 pieces inclusive"
  it.each([
    { id: 'TC-013', qty: 9,  expected: 18000 },
    { id: 'TC-014', qty: 10, expected: 19000 },
    { id: 'TC-015', qty: 11, expected: 20900 },
  ])('$id: $qty pcs × 20.00 PLN = $expected gr', ({ qty, expected }) => {
    expect(orderTotal(2000, qty)).toBe(expected);
  });
});

it('sum of parts = amount', () => {
  fc.assert(fc.property(fc.integer({ min: 0, max: 1e6 }), fc.integer({ min: 1, max: 50 }), (total, parts) => {
    expect(splitEvenly(total, parts).reduce((a, b) => a + b, 0)).toBe(total);
  }));
});

it('H3-AC1: exchange rate from the port', () => {
  const rates = vi.fn<(c: string) => number>();
  vi.when(rates, { onUnmatched: 'throw' }).calledWith('EUR').thenReturn(4.25);   // Vitest 5
  expect(priceIn(42500, 'EUR', rates)).toBe(10000);
});
```
A component in the browser:
```ts
import { page } from 'vitest/browser';
await page.getByRole('button', { name: 'Add' }).click();
await expect.element(page.getByRole('status', { name: 'Count' })).toHaveTextContent('1');
```
```ts
// vitest.config.ts — projects instead of workspace; the browser provider as an object
import { playwright } from '@vitest/browser-playwright';
export default defineConfig({ test: { projects: [
  { test: { name: 'unit', include: ['src/**/*.spec.ts'] } },
  { test: { name: 'browser', include: ['src/**/*.browser.spec.ts'],
      browser: { enabled: true, provider: playwright(), instances: [{ browser: 'chromium' }] } } },
] } });
```
A configuration file in ESM: `"type": "module"` in package.json or `vitest.config.mts`.
Suites (qa-regression): `vitest --changed origin/main`, `--project unit`, `--shard`.

## Mutation tests (Stryker)
`@stryker-mutator/core` 10 with **`testRunner: "command"`** (`"commandRunner": { "command": "npx vitest run" }`) works with Vitest 5
(verified: a result of 93.55%, the surviving mutant `quantity < 1 → <= 1` pointed to a missing test for 1 piece).
`@stryker-mutator/vitest-runner` 10 with Vitest 5 **reported 0% (all mutants survived) — that is a false result**; with a result of
0% or a suspicious 100%, first check whether the runner activates the mutants at all. Mutate the domain logic (`mutate`), not the whole repo.
- Narrowing: `npx stryker run --mutate "src/discount.ts:1-40"` (a file or a line range) and `--incremental` (results
  in `reports/stryker-incremental.json` speed up the next run with this flag) — before a merge, not after
  every commit. `--mutate` on a file without tests ends with a "no tests" error (unless `--allowEmpty`) — aim
  at modules that have tests.
- The result for the agent: the `json` reporter (`reports/mutation/mutation.json`) alongside `html`; Stryker 10 has no markdown
  reporter in the core. You assess surviving mutants one by one (qa-spec-first-testing: "A surviving mutant — decision").
- Do not carry configurations with `@stryker-mutator/vitest-runner` from materials and blogs over to Vitest 5 — the `command` runner stays.
- Tests related to the edited file: `vitest related <file> --run` (a subcommand); in the agent environment (the variable
  `AI_AGENT`) Vitest 5 uses the `minimal` reporter by default and does not enable watch — local gates: eng-local-quality-gates.

## Version-dependent
| Version | What changed |
|---|---|
| 3.0 | baseline: `workspace`, experimental browser mode, `vi.fn`/`vi.spyOn`, `it.each`, `it.fails`, `--changed` |
| 3.2 | `projects` instead of the `workspace` file (the old way being deprecated) |
| 4.0 | browser mode stable; providers as objects from the `@vitest/browser-playwright`/`-webdriverio`/`-preview` packages, the `vitest/browser` import; `workspace` removed → `projects`; `coverage.all` removed (set `coverage.include`); `poolOptions` flattened to top-level options; the `basic` reporter removed |
| 5.0 | Node ≥ 22.12, Vite ≥ 6.4; `clearMocks: true` by default (call history cleared before every test); `vi.when(...)` for conditional stubs (also with `using`); strict locators in browser mode; reporter output in the `.vitest` directory by default; Stryker: use the `command` runner |

## Checklist
- [ ] the case ID in the name, the expectation from the source, the test was red
- [ ] no `vi.mock` of your own modules without justification; test doubles only on ports
- [ ] the fake clock restored; no real network
- [ ] the mutation score of critical modules measured and credible (not 0%)

## Sources
- Stryker 10.0 `stryker run --help` and the option schema (`--mutate` with a line range, `--incremental`, `--allowEmpty`,
  reporters, default report paths); Vitest 5.0.3 `--help` and code (`related`, the `minimal`/`agent` reporter) — verified 2026-10-10.
- The 10xDevs course, ed. 3 (2026), module 3, lesson 2 (mutation testing with an agent) — training material (accessed 2026-10-09);
  the factory's position on the `command` runner stays (see `skill.meta.json`).
