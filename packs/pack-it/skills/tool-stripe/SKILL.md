---
name: tool-stripe
description: Use for a Stripe integration — Checkout, Payment Element, Intents, webhooks, Billing, Connect, Tax, API versions.
metadata:
  review: "2027-01-21"
  catalog: "Use when planning, writing, reviewing or testing a Stripe integration — choosing an API (Checkout Sessions, Payment Element, PaymentIntents, SetupIntents) and moving away from deprecated ones (Charges, Sources, Tokens, Card Element), dynamic payment methods instead of payment_method_types, order fulfillment from a webhook, sandboxes and test mode, restricted keys (rk_), a secrets vault, rotation, webhook signatures, CSP, Billing with Checkout and the customer portal, usage-based billing, Connect (Accounts v2, charge types, platform fee), Stripe Tax (registrations, tax codes, automatic_tax), upgrading the API version, SDKs, Stripe.js and event destinations. Not for a provider-independent subscription model (be-billing-subscriptions), general API design (be-api-design) or PCI DSS as a compliance program (sec-governance-compliance)."
  keywords: "stripe, stripe checkout, checkout session, payment intent, paymentintent, setup intent, payment element, card element, payment_method_types, charges api, stripe webhook, checkout.session.completed, klucz stripe, sk_live, rk_live, restricted key, klucz ograniczony, stripe billing, customer portal, stripe connect, accounts v2, destination charges, application_fee_amount, stripe tax, automatic_tax, txcd, wersja api stripe, stripe-version, upgrade stripe, stripe sdk, stripe.js, stripe cli, piaskownica stripe, stripe key, stripe API version, stripe sandbox"
---

# Stripe

**The agent's role:** runs the Stripe integration the way the provider itself recommends: the highest API level that
suffices, order fulfillment from a webhook, keys with minimal permissions and an explicitly pinned API version.
The subscription model, states and dunning independent of the provider: be-billing-subscriptions.

## 1. Version and environment
- **API version:** check the current one in the Stripe documentation (the "API versioning" page). A snapshot from the source dated 2026-10-21:
  `2026-09-30.endive`; one older than a month is probably out of date. Do not guess a newer number.
- **You pin the version in code** (the SDK client configuration), and do not rely on the account's default version.
- **The SDK client as an instance** (`new Stripe(...)`, `StripeClient`); a global module key (`stripe.api_key = …`)
  is deprecated in all current SDKs.
- **Environments:** for a new integration, separate sandboxes for local work and CI instead of the account's shared test
  mode. Test mode only for an existing integration that depends on it.

## 2. Which API — a decision map
| You are building | Use | Details |
|---|---|---|
| a one-time payment | Checkout Sessions (hosted or embedded) | `references/payments.md` |
| your own payment form | Checkout Sessions + Payment Element (`ui_mode: 'custom'`) | `references/payments.md` |
| saving a payment method for later | SetupIntents | `references/payments.md` |
| a payment without the customer present, your own cart state | PaymentIntents | `references/payments.md` |
| subscriptions and renewals | Billing API + Checkout (`mode: 'subscription'`) + the customer portal | `references/billing-connect-tax.md` |
| usage-based billing (a new integration) | Metronome (according to Stripe); Billing Meters only for existing simple usage | `references/billing-connect-tax.md` |
| a platform or marketplace | Connect, Accounts v2 (`/v2/core/accounts`) | `references/billing-connect-tax.md` |
| tax (sales tax, VAT, GST) | Stripe Tax + registrations | `references/billing-connect-tax.md` |
| upgrading the API version, SDK, Stripe.js | the procedure | `references/update.md` |

The order of interface preference: Payment Links (no code) → Checkout → Payment Element. Before the code, read the
right file from `references/`.

## 3. Critical rules
- **Do not pass `payment_method_types`.** Omitting it enables dynamic payment methods (configured in the dashboard,
  methods matched to the customer). Exception: an in-person terminal (`card_present`). Restrictions through
  `payment_method_configurations`, `excluded_payment_method_types` or `allowed_payment_method_types`.
- **The webhook is not optional.** Fulfill the order in event handling, not on the success page: the customer may not
  return to the page after a successful payment. For Checkout handle `checkout.session.completed`
  and `checkout.session.async_payment_succeeded`, fulfill when `payment_status` is not `unpaid`;
  `checkout.session.async_payment_failed` for failures. Webhooks are required for subscriptions and for methods
  with delayed confirmation.
- **You verify the webhook signature** before handling; the signing secret is a secret like an API key. Idempotency and the order of
  events: be-billing-subscriptions §5.
- **A restricted key (`rk_`) instead of a secret one (`sk_`)**, separate per service and environment, with minimal permissions;
  keys in the platform's secrets vault, never in the repository, logs or client code. `references/security.md`.
- **Deprecated APIs:** do not propose Charges, Sources, Tokens or Card Element; point to the migration (`references/payments.md`).
- **`automatic_tax` without an active registration does not collect tax and returns no error.** First confirm the registration
  in the customer's jurisdiction (`references/billing-connect-tax.md`).

## 4. Typical errors in code review
- An integration "done" without webhook handling, or with order fulfillment on the return page.
- `payment_method_types: ['card']` "because the customer wants only cards".
- An `sk_live_` key in code, an `.env` file in the repository or in a mobile app; no pre-commit hook for `sk_`/`rk_`.
- A manual renewal loop on PaymentIntents instead of Billing; a `plan` object instead of `Price`; different plans as prices of one
  product.
- Mapping events to application objects through `metadata` instead of through Stripe object identifiers.
- No pinned API version; a webhook with a different API version than the code.

## 5. Stripe starter documents
Integration Options (choosing a path), API Tour (an overview), Go Live Checklist (before going to production) —
docs.stripe.com.

## Example
**Situation:** "A shop in Next.js, a card payment through `charges.create` with a token from Card Element; we mark the order
as paid on the `/success` page."
**Result (abridged):**
- Migrate to Checkout Sessions (hosted or embedded), without `payment_method_types`; Card Element → Payment Element
  only for a custom form.
- A webhook with signature verification; fulfillment on `checkout.session.completed` or `async_payment_succeeded`
  with `payment_status` other than `unpaid`; the `/success` page only shows the state.
- A restricted key with permissions for Checkout and reading events, in the secrets vault; the API version pinned in the client.
- Tests in a sandbox: a payment, a method with delayed confirmation, the same event twice.

## Checklist
- [ ] the API version pinned in code and checked in the documentation; the SDK client as an instance
- [ ] the highest sufficient API level; no Charges, Sources, Tokens, Card Element
- [ ] no `payment_method_types` (except on a terminal)
- [ ] a webhook with a signature; fulfillment from the webhook; asynchronous events handled
- [ ] restricted keys in a vault, separate per environment; a plan for rotation and for responding to a leak
- [ ] tax: registrations confirmed before `automatic_tax`; Connect on Accounts v2

## Sources
- The stripe/ai repository, the `stripe-best-practices` and `upgrade-stripe` skills, commit
  1bcd18aa0e69b0e4dad9e268b873c7e245d6da5e (2026-10-21), MIT license. Rank: primary (the provider's material).
  Described in our own words; names of parameters, events and versions copied from the source.
- The docs.stripe.com pages were not read in this session; the provider's recommendations are given after the skills, not after the documentation
  [unverified against docs.stripe.com].
