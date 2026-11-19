# Test data, environments and special tests

## Managing test data
- **Synthetic data by default**: factories and builders in the test code (with sensible defaults
  and overriding only what matters in the test), generators (e.g. Faker with the `pl` locale for names, addresses, NIP (the Polish tax ID)
  with a correct checksum). Every test creates its own data and does not depend on the order (SKILL.md).
- **Reference data** (dictionaries, a product catalog, configuration) as a versioned starter set (seed) loaded
  by a script, identical locally and in CI.
- **A production copy** only with the data owner's consent and after **irreversible anonymization** before leaving
  production: masking that preserves format and relations (the same customer → the same pseudonym in all tables),
  a subset of the data instead of everything, removal of special-category data. Pseudonymization is still personal data (GDPR).
- **Data for performance tests** at production scale, but synthetic (qa-performance-testing).
- State reset: a transaction rolled back after the test, a separate schema or database per CI run, test containers
  (Testcontainers). E2E tests clean up through the API, not through the UI.

## Testing e-mails
- Locally and in CI an intercepting SMTP server, e.g. **Mailpit** (SMTP on port 1025, a web UI and REST API on 8025):
  the application sends normally, the test fetches the message through the API (`GET /api/v1/search?query=to:address@test`,
  `GET /api/v1/message/{ID}`), checks the subject, recipient, content and link, and then opens the link in Playwright (password reset,
  account confirmation). Cleanup: `DELETE /api/v1/messages`.
- A unique address per test (`user+<uuid>@test.local`), so that parallel tests do not get mixed up.
- Mailpit also has a link check, HTML compatibility with mail clients and (with SpamAssassin) a spam score.
  The look in real clients (Outlook, Gmail) you check with separate preview tools.
- Never real mailboxes or public disposable-address services for data other than fully test data.

## Compatibility
- **A matrix from data**, not from habit: browsers, systems and resolutions from product analytics (e.g.
  covering 95% of traffic) plus contractual requirements. Record it in the test plan.
- Playwright: the projects `chromium`, `firefox`, `webkit` in CI for critical paths; the rest on one engine.
  Device emulation (size, touch, user agent) is not a real device — check key mobile paths
  periodically on real Safari iOS and Chrome Android (a device farm or manually).
- The minimum version: what we still support (e.g. the last two versions of the major browsers) — with Browserslist in the repo,
  the same list for building and tests.

## Mobile applications (when the project has them)
- Native: Espresso (Android) and XCUITest (iOS) — fast, stable, in the platform's language. Cross-platform: Appium
  (WebDriver, many languages), Detox for React Native (synchronization with the app limits instability).
- The same rules as on the web: tests through the user interface only for critical paths, the rest lower; data
  set up through the API; emulators in CI, real devices before release.
- Specifics: system permissions, interruption (a call, the background), a weak network and airplane mode, an app
  update that keeps data, different sizes and orientations.

## API tests (tools)
Keep API tests in the repository as code, next to the application tests: Playwright `request` or supertest in TS, REST Assured
in Java, Karate for teams that prefer BDD syntax. Postman collections (run through Newman in CI) — when the team
already uses them; then in the repo, with no secrets in collection variables. Response validation against the OpenAPI schema
(be-api-design, `lifecycle-and-security.md`).

## Security in QA work
- An authorization matrix: roles × actions × "own / someone else's object" as API tests (be-auth-security, `authorization-models.md`).
- A DAST scan on staging: OWASP ZAP in baseline (passive) mode in CI for every deployment, a full active scan
  periodically and only on a test environment — never an active scan of other people's or production systems without consent.
- Cases from the OWASP Top 10 and API checklists (be-auth-security, `api-security-checklist.md`) in the test plan.

## After release (shift right)
- **Synthetic monitoring**: a few Playwright tests of critical paths run every few minutes on production,
  on dedicated test accounts, with no business effects (orders marked and cancelled, payments in the provider's
  test mode) — an alarm on failure (ops-observability).
- **Error tracking** (e.g. Sentry) and logs as a quality signal: new error types after release, a rise in JS errors
  on a page, a comparison with the previous version; the tester reviews them like a test report.
- Every production defect → an escape analysis (qa-test-design, `test-strategy-and-plan.md`).

## Sources
- [Mailpit](https://github.com/axllent/mailpit) (README and API routes); Playwright, OWASP ZAP, Testcontainers — documentation
- [roadmap.sh — QA](https://roadmap.sh/qa) (test data management, email testing, compatibility, mobile automation,
  backend automation, security testing, vulnerability scanning, monitoring & logs)
Described in our own words.
