# Security of a Stripe integration

## 1. API keys
- The key is not in source code or in committed environment files. Strings `sk_live_…` and `rk_live_…` are production
  keys; `sk_test_…` in code is also a risk — warn.
- Storage: the platform's secrets vault (AWS Secrets Manager or Parameter Store as `SecureString`, Google Secret
  Manager, Azure Key Vault) with read access only for the application that needs the key. Vercel has no built-in vault:
  an add-on that syncs secrets or a variable marked as sensitive. An environment variable only when the platform
  has no vault. In general: ops-secrets-identities.
- Separate keys for production, staging and QA; you do not log the key or return it in errors; no endpoint
  dumps environment variables.
- A pre-commit hook detecting `sk_` and `rk_` (eng-local-quality-gates); rotation when people with access leave.
- Keys never in client code or a mobile app (they can be extracted). Calls through your own backend; when the client
  must talk to Stripe — ephemeral keys (short-lived, scoped to a resource).

## 2. Restricted keys (RAK, `rk_`)
They have only the permissions granted, so a leak does less harm than a leak of `sk_`. One key per service, minimum permissions.
Migrating from a secret key:
1. From the request logs in Workbench, list the calls the secret key makes.
2. Create a restricted key in test mode with those permissions.
3. Watch the logs (`stripe logs tail` in the Stripe CLI) and test; every `403` is a missing permission.
4. Create the production equivalent, swap the key, then retire or expire the old secret key.

Additionally access policies (IP restriction) per key, different for each environment.

## 3. A key leak
1. Immediately roll or delete the key in the dashboard — also when unsure whether anyone used it.
2. Review the request logs of that key in Workbench.
3. Unknown activity → Stripe support. Incident handling: ops-security-operations.

Preparation: practice rotating keys, scan the repository, a pre-commit hook.

## 4. Webhooks, browser, OAuth
- You always verify the webhook signature before handling; you treat the signing secret like an API key. Additionally an allowlist
  of Stripe IP addresses on the endpoint.
- **CSP:** a `Content-Security-Policy` header in every application with Stripe.js; at least `https://*.stripe.com`
  in `script-src`, `frame-src`, `connect-src` (the full list: Stripe's integration security guide). Not
  `default-src *`. In general: fe-web-platform.
- **OAuth (Connect, Link, Stripe Apps):** the `state` parameter — unique, unpredictable, checked in the callback (CSRF).

## 5. Dashboard access and Connect
- Two-factor login through passkeys or an app, not SMS (number takeover). SSO through SAML
  and SCIM provisioning for teams.
- Connect: with Express and Custom accounts the platform is responsible for fraud and disputes; onboarding hosted by Stripe
  instead of your own (less personal data on the platform's side). Account configuration: `references/billing-connect-tax.md`.

## Sources
stripe/ai, file skills/stripe-best-practices/references/security.md, commit 1bcd18a (2026-10-21), MIT. Described in our own
words.
