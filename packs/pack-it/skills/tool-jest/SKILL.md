---
name: tool-jest
description: Use for tests in Jest — test.each, test doubles, fake timers, ESM, configuration, migration to Jest 30.
metadata:
  review: "2027-01-17"
  catalog: "Use for tests in Jest (existing projects, Node, React Native, Angular with jest-preset) — structure, test.each, test doubles and fake timers, ESM, configuration, migration to Jest 30 and when to move to Vitest. Not for oracle rules (qa-spec-first-testing) or Vitest (tool-vitest)."
  keywords: "jestjs, Jest w projekcie, jest.useFakeTimers, fałszywy zegar, setSystemTime, jest.mock, jest.config, snapshot, Jest in a project, fake clock"
---

# Jest

## Rules
The same as in tool-vitest (a table of examples from the specification with IDs, the test red first, test doubles only
on ports, controlled time, a known defect as `test.failing`), in Jest syntax:

| Goal | Jest |
|---|---|
| table of examples | `test.each([...])('TC-014: %i pcs', …)` |
| known defect | `test.failing('TC-020 (BUG-7): …', …)` — passes while the bug exists; after the fix it starts failing → remove `failing` |
| time | `jest.useFakeTimers().setSystemTime(new Date(...))` |
| cleaning up doubles | `restoreMocks: true` in the configuration (or `using spy = jest.spyOn(...)` — requires an environment that supports `using`, e.g. TS transpilation) |
| array matching | `expect.arrayOf(expect.objectContaining({...}))` (30+) |

## Pattern (verified: Jest 30.5, ESM, Node 22)
```js
import { jest } from '@jest/globals';
import { createCart } from './cart.js';
const fixedClock = { now: () => new Date('2026-03-01T10:00:00Z') };   // a fake instead of a mock

test.each([
  [[['A', 1]], 1],
  [[['A', 2], ['B', 3]], 5],
])('H2-AC1: item count for %j = %i', (adds, expected) => {
  const cart = createCart(fixedClock);
  adds.forEach(([s, q]) => cart.add(s, q));
  expect(cart.count()).toBe(expected);
});

test.failing('H2-AC3 (BUG-9): merges the same SKU into one line', () => {
  const cart = createCart(fixedClock);
  cart.add('A', 1); cart.add('A', 2);
  expect(cart.lines()).toEqual([{ sku: 'A', qty: 3 }]);
});
```
ESM without transpilation: `transform: {}` in the configuration and `NODE_OPTIONS=--experimental-vm-modules jest`.
The `using` syntax does not work in Node 22 without transpilation (verified: `SyntaxError`).

## Jest or Vitest?
A new project on Vite/ESM/TS → **Vitest** (native ESM and TS, browser mode, faster watch). An existing suite in Jest →
stay with it until it hurts; migration is a change of imports (`vi` instead of `jest`) and of the configuration — do it as a separate step, not in passing.
Do not raise the Jest version in a project without being asked (core-stack-sync) — use the syntax of the project's version.

## Version-dependent
| Version | What changed |
|---|---|
| 29 | baseline: `test.each`, `test.failing`, modern fake timers by default, `--testPathPattern` (singular) |
| 30 | dropped support for Node 14/16/19/21; TypeScript ≥ 5.4; `--testPathPattern` → `--testPathPatterns`; jsdom 26; removed matcher aliases (`toBeCalled`, `toBeCalledWith`… → `toHaveBeenCalled*`); spies with `using` (automatic cleanup); `expect.arrayOf`; `jest.unstable_mockModule` for ESM; faster runs that use less memory |

## Checklist
- [ ] the case ID in the name, the expectation from the source
- [ ] `restoreMocks`/`clearMocks` in the configuration; no state leaking between tests
- [ ] matchers in the full form (`toHaveBeenCalledWith`) — compatible with Jest 30
