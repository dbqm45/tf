# Billing, Connect and Stripe Tax

Contents: 1. Billing · 2. Usage-based billing · 3. Connect · 4. Stripe Tax · 5. Treasury · Sources

## 1. Billing (subscriptions)
- A recurring revenue model (subscriptions, seats, usage) → the Billing API, not your own renewal loop on
  PaymentIntents (Billing does renewals, retries and dunning).
- Front end: Checkout with `mode: 'subscription'` (the first payment, a trial period, proration); self-service plan change,
  cancellation and card change through the customer portal (Customer Portal).
- **Catalog:** one product per plan (Starter, Pro, Enterprise), several prices only for variants of the same plan
  (monthly and annual, currencies). The product name goes onto invoice lines. The `plan` object is deprecated — `Price`.
- **Webhooks required:** the lifecycle (`customer.subscription.*`, `invoice.paid`, `invoice.payment_failed`) and risk
  (`charge.dispute.created`, `charge.refunded`, `radar.early_fraud_warning.created`); `customer.updated` when you keep
  a local copy of customer data. Subscribe only to the events you react to.
- You map an event to an application record through a Stripe object identifier (e.g. of the subscription), and `metadata` only as
  an emergency fallback.
- In every answer about Billing mention tax (section 4). Provider-independent mechanics:
  be-billing-subscriptions.

## 2. Usage-based billing
According to Stripe, new usage-based billing integrations go to **Metronome** (metering, pricing, contracts, prepaid
credits, a usage preview). **Billing Meters** stay for a simple "pay for use" that already runs on them,
or when the usage price has to work with Connect, Adaptive Pricing or Workflows. A fixed or per-seat fee
plus usage: the fee stays in the Stripe subscription, Metronome bills only the usage (the Metronome customer is created
with the Stripe customer identifier). Do not cancel an existing subscription when adding usage.

## 3. Connect (platforms and marketplaces)
- **Accounts v2** (`POST /v2/core/accounts`); do not create accounts through `type: 'express' | 'custom' | 'standard'` (v1).
- Three independent dimensions of an account: access to the dashboard (`dashboard`), who pays Stripe fees
  (`defaults.responsibilities.fees_collector`), who covers a negative balance (`losses_collector`).

| Model | `dashboard` | fees / losses | Charge type |
|---|---|---|---|
| marketplace, on-demand services, a subscription platform | `express` | `application` / `application` | destination |
| SaaS with payments, a shop like Shopify, an AI/API platform | `full` | `stripe` / `stripe` | direct |
| crowdfunding (hold and payout), a multi-seller cart | `express` | `application` / `application` | separate charges and transfers |
| white label (advanced only) | `none` | `application` / `application` | destination or direct |

- **Who owns the customer relationship?** Sellers run their own business → direct (the seller is the party to
  the sale). The platform runs the checkout → destination. One payment split among many → separate charges
  and transfers.
- **Fee:** `application_fee_amount` only with direct and destination; with separate charges and transfers
  you transfer less than was collected.
- **Readiness:** before a payment, check the v2 capability status: merchant —
  `configuration.merchant.capabilities.card_payments.status`, recipient —
  `configuration.recipient.capabilities.stripe_balance.stripe_transfers.status` (`active`); not `charges_enabled`
  or `payouts_enabled`. Track changes with account webhooks.
- Recipient accounts (marketplace) without a merchant configuration; subscriptions on connected accounts through the customer
  v2 configuration and `customer_account`, without a separate v1 customer.
- **Embedded components:** `account_onboarding`, `notification_banner` (always), `account_management`; onboarding
  embedded or through account links, not through the API.
- **Forbidden combinations:** `losses_collector: "stripe"` with destination or separate; `application_fee_amount`
  with separate; an `express` dashboard with `losses_collector: "stripe"`. `dashboard: "none"` only on an explicit white label request.

## 4. Stripe Tax
- **Order:** the head office address in the tax settings (without it the status is `pending` and there are no calculations) → a registration
  for every jurisdiction where the company is already registered → `automatic_tax: { enabled: true }` on Checkout,
  a subscription, an invoice or a Payment Link.
- **Pitfall no. 1:** `automatic_tax` without an active registration in the customer's jurisdiction collects zero tax without an error.
  Check the registrations (the Tax Registrations API) and a test calculation; look at `taxability_reason`, not at the amount.
  `not_collecting` means no registration or the code `txcd_00000000` (non-taxable) on the product — check both.
- `automatic_tax` does not combine with manual `tax_rates` on the same object — remove them first (for many subscriptions
  Stripe's tax migration tool).
- **The product tax code** (`txcd_…`) take from Stripe's list (the Tax Codes API), never from memory; not the default general code
  for electronic services for sales in the USA. Show the candidates, a human confirms the choice. The code on the product,
  `tax_behavior` on the price.
- **PaymentIntents without Checkout:** no `automatic_tax`; you create a tax calculation, take the Intent amount from it
  and record the tax transaction after payment (otherwise the sale will not reach the reports).
- **B2B and reverse charge:** collect the tax number (`tax_id_collection` in Checkout); without it cross-border B2B
  sales are counted as B2C.
- **A registration in Stripe is not a registration with the tax office** — only a record of where the company is already registered.
  You do not decide on the obligation to register or on the EU VAT scheme; that is for a tax adviser. VAT and OSS in general:
  be-billing-subscriptions.
- The sandbox has separate settings and registrations; before the first real payment add the registrations in production.
  Threshold monitoring works only on production transactions.
- Connect: first establish (with an adviser) who settles the tax — the platform or the connected account — and set
  `automatic_tax.liability`.

## 5. Treasury
Financial accounts in new integrations: the v2 Financial Accounts API (`/v2/core/vault/financial_accounts`); v1 Treasury
only in existing integrations.

## Sources
stripe/ai, file skills/stripe-best-practices/references/{billing,connect,tax,treasury}.md, commit 1bcd18a (2026-10-21),
MIT. Described in our own words; names of fields, events and parameters copied from the source. The Metronome recommendation is
the provider's position.
