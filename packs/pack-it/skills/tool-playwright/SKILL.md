---
name: tool-playwright
description: Use for e2e and API tests in Playwright — role-based locators, web-first assertions, fixtures, trace, flaky tests in CI.
metadata:
  review: "2027-01-09"
  catalog: "Use for e2e and API tests in Playwright (@playwright/test) — role-based locators, web-first assertions, fixtures, projects and tags, accessibility snapshots, clock, trace, sharding, flaky tests in CI, test agents. Not for choosing test cases (qa-test-design) or oracle rules (qa-spec-first-testing)."
---

# Playwright

## Rules
1. **The expected result comes from the test case** (TC/AC in the name), never "from what the application shows" — qa-spec-first-testing.
2. **Locators like a user:** `getByRole(…, { name })` > `getByLabel` > `getByText` > `getByTestId`; CSS/XPath only as a last resort.
   The lack of a good role-based locator is often an **accessibility defect** — report it.
3. **Web-first assertions** (`await expect(locator).toHaveText/ToBeVisible/…`) — never `waitForTimeout` or a manual `sleep`.
4. **Isolation:** every test has a fresh `context`; prepare the state (user, data) through the API or `storageState` in a
   "setup" project, not by clicking. Zero dependencies between tests.
5. **Time under control:** `page.clock.setFixedTime(...)` / `page.clock.install()` instead of the real clock.
6. **Network:** external services through `page.route()` (or HAR); your own API — the real one (this is an e2e test).
7. **Few e2e tests** — critical paths only; test business rules lower down (qa-test-design).

## Pattern (verified: Playwright 1.63, Chromium)
```ts
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('order @smoke', () => {
  test.beforeEach(async ({ page }) => { await page.goto('/'); });

  test('TC-014 H1-AC2: 10 pcs with a 5% discount', async ({ page }) => {
    await page.getByLabel('Quantity').fill('10');
    await page.getByRole('button', { name: 'Recalculate' }).click();
    await expect(page.getByRole('status')).toHaveText('Total: 190.00 PLN'); // the value from requirements.md
  });

  test('page structure', async ({ page }) => {
    await expect(page.getByRole('main')).toMatchAriaSnapshot(`
      - heading "Order" [level=1]
      - spinbutton "Quantity"
      - button "Recalculate"
    `);
  });

  test('accessibility (axe)', async ({ page }) => {
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  });
});
```
A known defect: `test.fail(true, 'BUG-7')` or `test.fixme()` with a link — do not change the expected value.

## Configuration (excerpts)
```ts
export default defineConfig({
  fullyParallel: true, forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,           // retries detect flaky tests, they do not hide them
  failOnFlakyTests: !!process.env.CI,        // (1.52+) e.g. in the nightly suite
  use: { baseURL: 'http://localhost:4173', trace: 'on-first-retry' },
  webServer: { command: 'npm run preview', url: 'http://localhost:4173', reuseExistingServer: !process.env.CI },
});
```
Suites (qa-regression): tags in the title/`{ tag: '@smoke' }` + `--grep @smoke`; PR: `--only-changed=origin/main` (1.46+);
CI: `--shard=1/4` + `merge-reports`. A Page Object only when it simplifies — prefer fixtures (`test.extend`) and helper functions.
API tests: the `request` fixture (`request.post(...)`, `expect(res).toBeOK()`).

## Test agents (1.56+)
`npx playwright init-agents` generates the planner → generator → healer agents. Treat their output like code from a junior:
compare the plan with the cases from qa-test-design, and the **healer must not change expected values** — only locators/waiting.

Generating E2E through an agent (the gate before the test, the model test `seed.spec.ts`, the task template, CLI vs MCP, the review of
five anti-patterns, deliberate breaking, data cleanup): `references/e2e-with-agent.md`.

## Version-dependent
| Version | What changed |
|---|---|
| 1.44 | baseline: `getByRole`, `toHaveAccessibleName`, `expect.toPass`, tags (`{ tag }`), `webServer`, projects and dependencies |
| 1.45 | the `page.clock` clock API |
| 1.46 | `--only-changed` (only tests touched by a change in git) |
| 1.49 | `toMatchAriaSnapshot` (accessibility tree snapshots); `chromium-headless-shell` by default in headless mode |
| 1.52 | `failOnFlakyTests`; `toContainClass` |
| 1.56 | Playwright Test Agents (`init-agents`: planner, generator, healer) |
| 1.57 | removed `page.accessibility` (use aria snapshots / axe) |
| 1.63 | component tests (`@playwright/experimental-ct-*`) being deprecated — test components in Vitest (browser mode) |

## Checklist
- [ ] the name contains the case/criterion ID, the expectation has a source
- [ ] only role/label locators; no `waitForTimeout`
- [ ] data and login through the API/`storageState`; the test is independent
- [ ] trace on retry; flaky tests reported, not hidden
- [ ] an agent-generated test passed the review of five anti-patterns and deliberate breaking
