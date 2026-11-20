# Generating E2E tests through an AI agent

An agent writes Playwright tests quickly; without guidance it writes them the way most public examples do — CSS selectors,
`waitForTimeout`, shared state, assertions that only check a page loaded. This file is about getting tests worth keeping.

## 1. Is an e2e test the right tool?
Check before asking for one (test pyramid placement, qa-test-design §4):
- Does the risk cross boundaries — UI, API, database, a third party — in a way a lower-level test cannot reproduce? A discount
  rule or a validation message is a unit test, not e2e.
- Is the feature actually built and reachable? A test for a screen that does not exist yet produces invented locators.
- Is there already a test for this journey? Extend it rather than add a near-duplicate.
Budget roughly **one e2e test per critical risk**; the agent will happily write twenty.

## 2. Give an exemplar and written conventions
The two things that change agent output most across a whole project:
- **An exemplar test** — `tests/e2e/seed.spec.ts`, a short, reviewed spec showing the house style: fixtures used, how login
  happens (`storageState`), role-based locators, a web-first assertion on a business result, data created and removed by the test.
  Tell the agent to imitate it. (The built-in generator agent also starts from a seed test.)
- **Written conventions** — a short section in `CLAUDE.md` or `e2e/README.md`: locator order, no `waitForTimeout`, one test
  per file, ids in test names, which services are mocked and which are real, how test data is named and cleaned.
Fix the exemplar once instead of correcting every generated test.

## 3. The task brief
Per test, give the agent:
- **the risk** — what failure the test guards against ("a logged-in customer cannot complete a card purchase");
- **the scenario** — steps in user terms and the expected business result, with its source (case id, criterion);
- **the boundaries** — what stays real (own API, database) and what is mocked (payment provider via `page.route`, email);
- **the regression it must catch** — a concrete code change that has to turn it red ("the total ignores the discount").
Ask for one test per file and a short header comment: case id, source of the expected value, what is mocked, who generated it.

## 4. Exploring the app: accessibility tree, CLI or MCP
- The agent should read the **accessibility tree** (role, name, state), not screenshots — it yields `getByRole` locators directly
  and is far cheaper in tokens.
- For a coding agent with a shell, the Playwright CLI (`@playwright/cli`, command `playwright-cli`) is the cheaper transport:
  `playwright-cli open <url>`, `snapshot` (accessibility tree), `click`, `fill`, `console`, `requests`, `state-save` (to produce a
  `storageState` file). Check `playwright-cli --help` for the installed version.
- The Playwright MCP server suits sessions where the agent only drives a browser and has no shell.

## 5. Reviewing the result: five anti-patterns
| Anti-pattern | Question to ask | Replace with |
|---|---|---|
| sham assertion | Would this test fail if the feature were broken? (`toBeVisible()` on a heading, `status === 200` only) | an assertion on the business result: the total, the order state, the row in the list |
| brittle selector | Does this survive a CSS refactor? (`.btn-primary:nth-child(2)`, XPath) | `getByRole` with name, `getByLabel`; a test id only when nothing else exists |
| shared state | Does it pass alone and in any order? (relies on a user or cart from another test) | own data per test, `storageState` from a setup project |
| time-based waits | Is there any `waitForTimeout` or `setTimeout`? | web-first assertions, `page.clock` for time-dependent logic |
| no cleanup | What is left in the database after a run? | unique data plus `afterEach` cleanup (§7) |
When returning a test for fixes, quote the line and the replacement; reviewers and agents fix faster from a concrete diff.
These match the Playwright "Best practices" page (locators, web-first assertions, isolation).

## 6. Verifying the test catches something
A generated test that passes on the first run has proven nothing yet:
1. **Break the behaviour on purpose** in the working tree (e.g. remove the discount line, invert a condition), run the test, see it
   go red for the right reason, then restore the file with `git checkout -- <file>`.
2. **Run it twice in a row** (`--repeat-each=2`, or a second run on a fresh database) — the second run exposes leftover data
   and order dependence.
3. Run it with `--workers=4` alongside the rest of the suite to catch shared-state collisions.

## 7. Test data and cleanup
- Create data with **unique names** per run (`order-${testInfo.testId}` or a timestamp) so parallel runs and leftovers do not collide.
- Remove it in `afterEach` (via the API, not the UI).
- Add a **teardown project** (a project listed in `teardown` of the setup project) that deletes anything carrying the test prefix —
  a safety net for runs that crashed before `afterEach`.
- With row-level security (e.g. Postgres RLS, Supabase), a cleaner acting as an ordinary user may silently delete nothing: run it
  as the data owner, or with a service key kept only in CI secrets.

## 8. Example brief
```
Write one Playwright test in e2e/purchase.spec.ts, imitating tests/e2e/seed.spec.ts and the rules in e2e/README.md.
Risk: a logged-in customer cannot buy with a card (R2 in test-strategy.md).
Scenario TC-041: add "Desk lamp" (49.00) ×2 to the cart, pay by card → order page shows "Paid" and total 98.00 (source: US-07/AC-1).
Real: our API and database. Mocked: the payment provider (page.route on **/payments/**, return the success fixture).
Must catch: the order is marked Paid when the provider returns "declined".
Login via storageState from the setup project. No waitForTimeout. Create the product with a unique name, delete it in afterEach.
Then: break the paid-status check, show the test red, restore, run twice.
```
