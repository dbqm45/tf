---
name: tool-playwright
description: Use when writing e2e or API tests in Playwright — role locators, web-first assertions, isolation, page.clock, flaky policy in CI, aria snapshots, test agents.
metadata:
  review: "2027-01-09"
  catalog: "Use when writing or fixing end-to-end and API tests with @playwright/test: locator priority and web-first assertions, test isolation and storageState, page.clock and network mocking, known defects (test.fail, test.fixme), playwright.config for CI (retries as a detector, failOnFlakyTests, trace on-first-retry, webServer, tags and --grep, --only-changed, sharding), aria snapshots and axe, the built-in planner/generator/healer agents, version differences 1.44–1.63, and generating E2E tests through an AI agent. Not for choosing which cases to test (qa-test-design), where expected values come from (qa-spec-first-testing), component tests (tool-vitest browser mode) or regression suite upkeep (qa-regression)."
---

# Playwright — e2e and API tests

Versions: written for 1.63, works from 1.44; see the table below before using a newer API. Evidence: `skill.meta.json`.

## Rules
1. **Expected values come from the test case or the acceptance criterion**, never from what the app shows today
   (qa-spec-first-testing). The test name carries the id: `test('TC-014: order total with shipping', …)`.
2. **Locators, in this order:** `getByRole(role, { name })` → `getByLabel` → `getByText` → `getByTestId`. CSS and XPath last.
   If an element cannot be found by role and accessible name, that is usually an **accessibility defect** — report it instead of
   reaching for a CSS selector.
3. **Web-first assertions** (`await expect(locator).toHaveText(…)`, `toBeVisible`, `toHaveURL`) wait and retry by themselves.
   Never `page.waitForTimeout()` or fixed sleeps.
4. **Isolation:** every test gets a fresh browser context. Prepare state through the API or a `storageState` file produced by a
   setup project — not by clicking through the UI, not by relying on another test having run first.
5. **Time and network:** control time with `page.clock` (`setFixedTime`, `install` + `runFor`) — 1.45+. Mock **external**
   services with `page.route()` or a HAR file (`routeFromHAR`); keep your own API real.
6. **Few e2e tests,** only for critical user journeys. Rules and calculations are tested lower (qa-test-design §4).
7. **Known defect:** `test.fail(true, 'BUG-231 price rounding')` or `test.fixme()` with the bug link. Never edit the expected
   value to make it pass.
8. **API tests** use the `request` fixture (`request.post('/api/orders', { data })`) — no browser needed.
9. **Fixtures over page objects** for shared setup; a page object is fine for long flows, but keep assertions in the test.

## playwright.config.ts for CI
```ts
import { defineConfig, devices } from '@playwright/test';
const CI = !!process.env.CI;
export default defineConfig({
  testDir: 'e2e',
  fullyParallel: true,
  forbidOnly: CI,                       // a forgotten test.only fails the build
  retries: CI ? 2 : 0,                  // a detector of flakiness, not a cover for it
  failOnFlakyTests: CI,                 // 1.52+: passed-on-retry = failed run
  reporter: CI ? [['blob'], ['github']] : 'html',
  use: { baseURL: 'http://localhost:3000', trace: 'on-first-retry' },
  webServer: { command: 'npm run start', url: 'http://localhost:3000', reuseExistingServer: !CI },
  projects: [
    { name: 'setup', testMatch: /.*\.setup\.ts/ },
    { name: 'chromium', use: { ...devices['Desktop Chrome'], storageState: 'e2e/.auth/user.json' }, dependencies: ['setup'] },
  ],
});
```
- A flaky test is a bug in the test or the app: open the trace (`npx playwright show-trace`), fix the cause, do not raise retries.
- **Suites by tag:** `test('TC-020: delivery date', { tag: '@smoke' }, …)`, run with `npx playwright test --grep @smoke`.
- **Only what a PR touched:** `npx playwright test --only-changed=origin/main` (1.46+). On older versions: run the `@smoke` tag
  plus the spec files changed in the diff (`git diff --name-only origin/main -- e2e`).
- **Sharding:** `--shard=1/4` per CI job, blob reports, then `npx playwright merge-reports --reporter html ./all-blob-reports`.

## Accessibility
- `await expect(page.getByRole('main')).toMatchAriaSnapshot(…)` (1.49+) checks the accessibility tree; review snapshots like code.
- Automatic scan: `@axe-core/playwright` (`new AxeBuilder({ page }).analyze()`), plus a manual keyboard pass.
- `page.accessibility` was removed in 1.57 — use aria snapshots or axe.

## Built-in test agents (1.56+)
`npx playwright init-agents --loop=claude` (or `vscode`, `opencode`) adds the **planner** (explores the app, writes a plan),
**generator** (turns the plan into tests) and **healer** (repairs failing tests). Treat their output as a junior's pull request.
The healer may fix **locators and waits**; it must never change an expected value or an asserted text — a changed expectation is
a defect report, not a repair.

## Generating E2E through an AI agent
Before asking an agent for tests, the exemplar spec (`tests/e2e/seed.spec.ts`), written conventions, the task brief, exploration
with `playwright-cli`, the anti-pattern review and verification by deliberately breaking the code: `references/e2e-with-agent.md`.

## Version-dependent
| Version | What changed |
|---|---|
| 1.44 | minimum supported baseline |
| 1.45 | `page.clock` |
| 1.46 | `--only-changed` |
| 1.49 | `toMatchAriaSnapshot`; headless runs use the Chromium headless shell by default |
| 1.52 | `failOnFlakyTests`, `toContainClass` |
| 1.56 | test agents (`init-agents`: planner, generator, healer) |
| 1.57 | `page.accessibility` removed |
| 1.63 | experimental component testing (`@playwright/experimental-ct-*`) on the way out — write component tests in Vitest browser mode (tool-vitest) |

## Example
"The Recalculate button test is flaky and uses a CSS class":

```ts
test('TC-031: recalculating updates shipping', { tag: '@smoke' }, async ({ page }) => {
  await page.clock.setFixedTime(new Date('2026-03-02T10:00:00'));   // shipping prices depend on the date
  await page.goto('/cart');
  await page.getByLabel('Quantity').fill('10');
  await page.getByRole('button', { name: 'Recalculate' }).click();  // was: page.locator('.btn-recalc')
  await expect(page.getByRole('status')).toHaveText('Shipping: 0.00'); // H4-AC1: free from 100.00
});
```
If `getByRole('button', { name: 'Recalculate' })` finds nothing because the "button" is a `<div>` with a click handler,
report it as an accessibility defect.

## Sources
- playwright.dev: Release notes, Best practices, Test agents, Aria snapshots, Clock, Test configuration, Test sharding
  (accessed 2026-09-27; versions verified with @playwright/test 1.63.0, see `skill.meta.json`).
