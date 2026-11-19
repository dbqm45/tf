---
name: qa-regression
description: Use for regression — suites (smoke, PR, nightly), tests affected by a change, flaky tests and quarantine, test data.
metadata:
  review: "2027-10-17"
  catalog: "Use when building and maintaining regression — layers of test suites (smoke, PR, nightly, pre-release), choosing the tests affected by a change, unstable (flaky) tests and quarantine, test data, visual and contract regression, test quality metrics. Not for designing individual cases (qa-test-design)."
---

# Regression tests

## Run layers
| Suite | When | Contents | Time budget |
|---|---|---|---|
| **smoke** | every commit / deployment | critical paths, application health | < 5 min |
| **PR** | every pull request | unit + integration tests **affected by the change** (e.g. `nx affected`, `--only-changed`, `--changed`) + e2e smoke | < 15 min |
| **nightly** | once a day | the full suite, all browsers, visual regression, mutation tests of critical modules | hours are OK |
| **pre-release** | a release candidate | the full automation + a manual checklist (qa-exploratory-manual) + UAT | per the plan |
Tag tests (`@smoke`, `@critical`, `@visual`) and run the suites with a filter, not with separate copies of the tests.
**Before CI** — local layers: after an edit (an agent hook, seconds: format, lint, tests tied to a file from the risk
area), pre-commit (staged files, a dozen or so seconds), pre-push (types, a wider suite, minutes) —
eng-local-quality-gates. Every local layer that catches a bug saves one CI cycle; it does not
replace the full suite in CI.

## Unstable tests (flaky)
- A test that is green once and red once with no code change **is a defect** (of the test or of the application), not "bad luck".
- Retries only for **detecting** instability in CI; a flaky report + a "fail on flaky" option in the nightly suite.
- **Quarantine**: a test taken out of the PR gate, with an owner, a ticket and a fix deadline; no deadline → delete or fix it.
- Typical causes: a hard wait (`sleep`) instead of an assertion with waiting, shared state/data, order dependence,
  time and time zone (use a controlled clock), a real network and external services, animations.

## Test data
Every test creates its own data (factories/builders, an API to set up state) and does not depend on other tests;
unique identifiers; no production data (GDPR). Set up state through the API, not by clicking through the UI.

More broadly (synthetic data and anonymization of a production copy, e-mails through Mailpit, a compatibility matrix, mobile
apps, API testing tools, DAST in CI, synthetic monitoring after release): `references/environment-and-special-data.md`.

## Visual and accessibility regression
Screenshots of components/pages with stabilization (fonts, animations disabled, a fixed clock and data); a review of the differences
by a human before updating the baselines. Accessibility tree snapshots detect structure changes without pixel fragility.

## Contract regression
Contract tests (e.g. Pact, validation against OpenAPI) between the front end and the API and between services — they catch changes that break
compatibility earlier and more cheaply than e2e.
**Messages** (events, commands): a snapshot of the format with the same serializer as the outbox, fixed ids and times in test data,
a backward compatibility check; in the PR suite a **consumer idempotency** test — the same id twice → one effect
(be-messaging-outbox).

## Maintenance
Tests are code: review, refactoring, removing obsolete ones. A test that has never caught a bug and duplicates another level → delete it.

## Metrics (to learn from, not as targets)
defects that escaped to production · the share of unstable tests · the PR suite time · the mutation score of critical modules ·
coverage of **requirements** by tests (qa-spec-first-testing). Line coverage percentage — only as a hint of where tests are missing.

## Example
**Situation:** every PR in an Nx monorepo runs 1,400 tests (380 e2e on three browsers) — 70 minutes.
**Result:** suites from tags, one copy of the tests:

| Suite | Command | Budget |
|---|---|---|
| smoke | `npx playwright test --grep @smoke --project=chromium` | < 5 min |
| PR | `npx nx affected -t test lint` + smoke | < 15 min |
| nightly | full Playwright (3 browsers, `@visual`) + Stryker for `payments` | hours are OK |

A flaky test from the report goes to quarantine (owner, ticket, deadline), not to `retries: 3`.

More examples: `references/examples.md`.
