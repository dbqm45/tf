---
name: be-billing-subscriptions
description: Use for subscriptions and recurring payments — plans, prorated plan changes, trials, dunning, provider webhooks, VAT, invoices.
metadata:
  visibility: name
  review: "2027-10-20"
  catalog: "Use when you design or review SaaS billing — the model of plans, prices and periods, a subscription and its states, a plan change mid-period with proration, a trial period, usage-based billing, failed payments and dunning, idempotent webhooks of a payment provider (Stripe, Adyen, PayU, Przelewy24) and state reconciliation, money in code (currency, rounding), VAT for electronic services and OSS, invoices and corrections, KSeF, cancellation and withdrawal. Not for the general design of queues (be-messaging-outbox), the pricing and accounting model in the domain (ddd-archetypes: Pricing, Accounting), the map of EU rules for a product with AI (arch-eu-product-law) or login (be-auth-security)."
  keywords: "subskrypcja, abonament, płatność cykliczna, billing, rozliczenia saas, plan taryfowy, zmiana planu, upgrade, downgrade, proration, rozliczenie proporcjonalne, okres próbny, trial, rozliczenie za zużycie, metered billing, nieudana płatność, karta odrzucona, dunning, windykacja, ponowienie płatności, past_due, webhook stripe, webhook przyszedł dwa razy, idempotencja płatności, uzgadnianie płatności, faktura subskrypcji, faktura korygująca, VAT OSS, VAT usług elektronicznych, kwota w groszach, zaokrąglenie kwot, anulowanie subskrypcji, subscription, recurring payment, SaaS billing, pricing plan, plan change, prorated billing, trial period, usage-based billing, failed payment, card declined, payment retry, the webhook came twice, payment idempotency, payment reconciliation, subscription invoice, credit note, VAT on electronic services, amount in cents, rounding amounts, subscription cancellation"
---

# Subscriptions and billing in SaaS

**The agent's role:** it designs the subscription model and the money flow so that the customer never pays twice,
access matches the payment state, and every amount can be reproduced from the invoice. The source of truth about a payment is
the payment provider; the source of truth about access — our subscription reconciled with the provider.
The specific API, webhooks, keys and versions at the Stripe provider: tool-stripe.

## 1. Model
- **Product → plan (price) → subscription → subscription items → invoice → payment.** A price is immutable and versioned:
  a price list change = a new price, existing customers stay on the old one until a business decision says otherwise.
- A billing period with an anchor (the billing day), a currency assigned to the customer, the period's time zone explicit (eng-i18n).
- You compute entitlements (what the customer can do) from the subscription state in one place, not from a plan scattered across the code.
- The domain model of prices, discounts and balances — the price-calculation and value-ledger archetypes (ddd-archetypes); here only the subscription mechanics.

## 2. Subscription states and access
Typical states (names as at the provider, e.g. Stripe): trialing, active, past due (the first failed payment),
unpaid, canceled, paused, incomplete (the first payment did not go through). Details: `references/states-and-webhooks.md`.
- For every state record the decision: full access, access with a warning (a grace period), read and export only, none.
- Cutting off access never deletes data — deletion per retention and the right to export (arch-multi-tenancy §5).

## 3. Plan change, trial, usage
- **A change mid-period:** an upgrade — immediately, with a prorated amount for the rest of the period (an invoice now or
  an item on the next one); a downgrade — usually from the next period, without a refund. Record the rule in the terms and in a test.
- The proration is computed by the provider or by one function in the code (seconds or days of the period, rounding at the end, once).
- **Trial period:** with or without a card; a reminder before the end; the end without a payment method → a clear state, not an error.
- **Usage (metered):** usage events with an idempotency identifier, aggregation at the end of the period, a correction before
  the invoice is closed; a counter per tenant (arch-multi-tenancy).

## 4. Failed payments and dunning
- Retries per the provider's schedule (e.g. Stripe Smart Retries — 8 attempts over 2 weeks recommended, configurable;
  `references/states-and-webhooks.md`) or your own, matched to the business; an email with a link to update the card,
  a grace period with access.
- After the last attempt: the "unpaid" state or cancellation per the decision; access per the table in §2.
- Payment authentication (SCA, 3-D Secure) on renewal: a "requires action" state and a link for the customer.

## 5. Provider webhooks — idempotently
- You verify the signature on the raw request body and the time tolerance; the secret from the secrets manager (ops-secrets-identities).
- You store the event (the event id as a unique key) and respond 2xx immediately; handling asynchronously
  with deduplication in the same transaction as the effect (an inbox — be-messaging-outbox).
- Ordering is not guaranteed and events repeat: the handling does not trust the order, when in doubt it fetches
  the current object from the provider's API.
- Calls to the provider (creating a subscription, a refund) with an idempotency key — a retry after a network error does not
  create a second payment.
- **Reconciliation:** a periodic job compares the subscription and invoice states at our side and at the provider; a discrepancy = an alert.

## 6. Money, taxes, invoices
- Amounts as an integer in the smallest currency unit or a decimal type — never a floating-point number;
  the number of decimal places depends on the currency (ISO 4217). Rounding in one place, with an explicit rule.
- **VAT:** a B2C electronic service in the EU — the consumer's country rate, settled through OSS; B2B with a valid EU VAT number —
  the reverse charge. You store the evidence of the consumer's location (address, card, IP) with the invoice. Facts and thresholds:
  `references/states-and-webhooks.md` [to be checked by accounting].
- **Invoices:** continuous numbering, immutable after issue; a change = a corrective invoice (credit note). In Poland KSeF
  (deadlines: accounting; notes `.claude/skills/arch-eu-product-law/references/outside-factory-scope.md`). Invoice amounts = the amounts collected, with a reproducible calculation of the items.
- **B2C cancellation and withdrawal:** cancellation as simple as purchase, withdrawal and refund per consumer rights
  (a lawyer; notes `.claude/skills/arch-eu-product-law/references/outside-factory-scope.md`).

## Rules
- One source of truth about the payment state (the provider) and one about access (the subscription), reconciled by a job.
- Every webhook and every provider call idempotent; a test "the same event twice" in the suite.
- You do not store card data — the provider's tokens (the PCI DSS scope: sec-governance-compliance).
- Tests on a controlled clock (the end of a period, the end of a trial, a time change) and in the provider's test mode.
- Tax and legal facts go to accounting or a lawyer; in the code you keep them as configuration with an effective date.

## Example
**Situation:** "The renewal failed, the `invoice.payment_failed` webhook came twice, the customer lost access
immediately and got two emails."
**Result (abbreviated):**
- Webhook: an events table with a unique `event_id`; the second delivery → 2xx without an effect. The email is sent from the outbox once.
- State: "past due" instead of an immediate block; a grace period of 7 days [a business decision], a banner with a link to the card.
- Retries: the provider's schedule; after the last failed one → read and export only.
- Tests: a double event; events in reverse order (first `paid`, then `failed` of an older attempt);
  the end of the grace period on a test clock.

## Checklist
- [ ] the model product → price → subscription → invoice; prices versioned
- [ ] a table of subscription states with an access decision for each
- [ ] the plan change and trial rules recorded and tested
- [ ] dunning: retries, communication, the grace period, the final state
- [ ] webhooks: signature, storage with the id, 2xx immediately, deduplication, no trust in ordering; idempotency keys in the API
- [ ] amounts without floating-point numbers; VAT/OSS and invoices confirmed by accounting; reconciliation with an alert

## Sources
Described in our own words; facts with access dates in `references/states-and-webhooks.md`.
