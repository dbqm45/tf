# Payments in Stripe: choosing an API, the interface, webhooks, migrations

## 1. The API hierarchy
- **Checkout Sessions** (`checkout.sessions.create`) — payments with the customer present, one-time and subscriptions;
  discounts, shipping and adaptive pricing in the package. Tax only with `automatic_tax` and an active registration.
- **PaymentIntents** — payments without the customer present, or when you model the cart state yourself.
- **SetupIntents** — saving a payment method for later.
- Higher up: Invoicing, Payment Links, the subscriptions API. An integration uses only these levels.
- Since API version `2026-03-25.dahlia`, Checkout accepts `integration_identifier`: your own session label for comparisons
  in the dashboard; the source recommends appending 8 random letters to it.

## 2. The payment interface (from the simplest)
1. **Payment Links** — no code, simple products.
2. **Checkout** — a form hosted by Stripe or embedded; enough for most applications.
3. **Payment Element** — an embedded component with full control of appearance; feed it with a Checkout session
   (`ui_mode: 'custom'`), and only when that is impossible — with a raw PaymentIntent.

Do not propose Card Element or Payment Element in a cards-only mode; for Card Element point to the migration to Payment
Element. A surcharge for a payment method or a preview of card data before creating an Intent: Confirmation Tokens
(finalization on the server), not `createPaymentMethod` or `createToken` from Stripe.js.

## 3. Order fulfillment from a webhook
- The customer may pay and not return to the success page (a dropped connection), so logic only on that page loses
  orders.
- Handle `checkout.session.completed` and `checkout.session.async_payment_succeeded`; fulfill when `payment_status`
  is not `unpaid`. With methods that have delayed confirmation `completed` arrives before the payment.
  `checkout.session.async_payment_failed` — failure.
- Webhooks are required for subscriptions, methods with delayed confirmation and every effect after a payment
  (access, e-mail, stock level, saving the order). In a prototype: recommended right away, required before production.
- You verify the signature before handling (`references/security.md`).

## 4. Dynamic payment methods
- `checkout.sessions.create`: omit `payment_method_types` (dynamic matching is the default behavior).
- `paymentIntents.create`, `setupIntents.create`: omit it; since API version 2023-08-16 dynamic methods are the default,
  on older ones `automatic_payment_methods: { enabled: true }`.
- `subscriptions.create`: omit `payment_settings.payment_method_types`.
- An in-person terminal: `payment_method_types: ['card_present']` (in Canada also `interac_present`) — the only
  permitted case.
- The list of allowed methods for an Intent: `allowed_payment_method_types`; exclusions: `excluded_payment_method_types`;
  sets: `payment_method_configurations`.

## 5. Deprecated APIs and migrations
| API | Status | Instead |
|---|---|---|
| Charges | do not use | Checkout Sessions or PaymentIntents (Stripe's migration guide) |
| Sources | deprecated | SetupIntents |
| Tokens | outdated | SetupIntents or Checkout Sessions |
| Card Element | legacy | Payment Element |

## 6. PCI DSS
Sending a raw card number (PAN) from the server (`payment_method_data`) may require demonstrating PCI DSS compliance.
Moving card numbers from another operator: Stripe's PAN import process. The compliance program:
sec-governance-compliance.

## Sources
stripe/ai, file skills/stripe-best-practices/references/payments.md, commit 1bcd18a (2026-10-21), MIT. Described in our own
words.
