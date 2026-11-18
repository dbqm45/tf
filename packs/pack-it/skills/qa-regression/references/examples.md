# Regression examples

The names of projects, tests and the numbers are illustrative.

## 1. Splitting a 70-minute suite into layers
**Situation:** "Every PR in an Nx monorepo runs all 1,400 tests, including 380 e2e in Playwright on three
browsers — 70 minutes. People merge without waiting for the result".

**How:**
1. You tag tests (`@smoke`, `@critical`, `@visual`) instead of copying them into separate suites.
2. Smoke: critical paths and application health, one browser, < 5 min.
3. PR: only the projects affected by the change (`nx affected`) + e2e smoke, < 15 min.
4. Nightly: the full suite, three browsers, visual regression, mutation tests of the payments module.
5. You measure the PR suite time and the share of flaky tests, not the number of tests.

**Result:** the layout of the suites and a CI fragment.

| Suite | Trigger | Command | Contents | Budget | Now |
|---|---|---|---|---|---|
| smoke | a push to `main`, every deployment | `npx playwright test --grep @smoke --project=chromium` | 24 tests: login, cart, payment, `/health` | < 5 min | 3 min 40 s |
| PR | every pull request | `npx nx affected -t test lint` + smoke | unit and integration of the affected projects | < 15 min | 9–13 min |
| nightly | 2:00 every day | `npx playwright test` + `npx nx run-many -t test` + Stryker for `payments` | everything, `chromium`/`firefox`/`webkit`, `@visual` | hours are OK | 2 h 10 min |
| pre-release | a `v*-rc.*` candidate | nightly + checklist + UAT | automation and manual tests (qa-exploratory-manual) | per the plan | 1 day |

```yaml
# .github/workflows/pr.yml (fragment)
on: pull_request
jobs:
  affected:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@<SHA>
        with:
          fetch-depth: 0
      - run: npm ci
      - run: npx nx affected -t test lint --base=origin/main --head=HEAD
  smoke-e2e:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@<SHA>
      - run: npm ci
      - run: npx playwright test --grep @smoke --project=chromium
```

## 2. An unstable test in quarantine
**Situation:** "The test `checkout.spec.ts › BLIK payment completes the order` in the flaky report failed 4 times out of 50 runs
this week. Let's add `retries: 3` and have peace".

**How:**
1. Retries stay only for detecting instability; it is a defect of the test or of the application, not bad luck.
2. Quarantine: the test taken out of the PR gate, with an owner, a ticket and a fix deadline.
3. Diagnosis by the typical causes — here a hard wait for the payment gateway's response.
4. The fix: an assertion with waiting instead of `waitForTimeout`; the test returns to the gate after 20 green nightly runs.
5. After the deadline with no fix you delete or fix the test — you do not extend it forever.

**Result:** an entry in the quarantine register and the fix.

```yaml
# tests/quarantine.yaml
- test: "checkout.spec.ts › BLIK payment completes the order"
  tag: "@quarantine"
  owner: "@anowak"
  issue: "QA-1187"
  since: "2026-09-28"
  deadline: "2026-10-12"
  symptom: "4/50 red, a timeout on 'Order accepted'"
  cause: "waitForTimeout(2000) instead of waiting for a state; the BLIK simulator's response takes 1.5–3 s"
```

```ts
// before
await page.waitForTimeout(2000);
expect(await page.getByRole('heading').textContent()).toBe('Order accepted');
// after
await expect(page.getByRole('heading', { name: 'Order accepted' })).toBeVisible({ timeout: 10_000 });
```

## 3. Consumer idempotency in the PR suite
**Situation:** after a release a customer received two e-mails with an invoice, because the `InvoiceIssued` event arrived twice.
"Add an e2e test that will catch it".

**How:**
1. A message contract regression is cheaper than e2e — the consumer idempotency test goes into the PR suite.
2. Test data with a fixed event id and a fixed time; the same serializer as the outbox.
3. The same id twice → one effect (one e-mail, one entry).
4. A snapshot of the event format guards backward compatibility.

**Result:** the consumer's test suite.

| Test | Input | Expected effect | Suite |
|---|---|---|---|
| `invoice-issued: duplicate id` | `InvoiceIssued` with `eventId=7f3a…01` twice | 1 e-mail in Mailpit, 1 row in `processed_events` | PR |
| `invoice-issued: different ids` | two events with different `eventId` | 2 e-mails | PR |
| `invoice-issued: format snapshot` | an event from the factory, a fixed time `2026-01-15T10:00:00Z` | matches the saved snapshot | PR |
| `invoice-issued: old schema version` | an event without the field added in the new version | processed without an error | PR |
