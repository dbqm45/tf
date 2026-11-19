# Subscription states, webhooks, idempotency, VAT — facts

Facts checked by the `researcher` agent on 2026-10-18. The source pages were not opened from the cloud session
(WebFetch ENOTFOUND, proxy 403), so the verdicts rest on search engine summaries from official domains —
marked [secondary]. The example is Stripe; at other providers the names and rules differ — check their documentation.

## Stripe — facts
| Fact | Source | Status |
|---|---|---|
| Subscription statuses: `trialing`, `active`, `past_due`, `unpaid`, `canceled`, `incomplete`, `incomplete_expired`, `paused` (`paused` among others after the end of a trial without a payment method). | docs.stripe.com/api/subscriptions/object | [secondary; the list not seen in full] |
| Prorated billing of a plan change: by default `create_prorations` (items on the next invoice); `always_invoice` issues an invoice immediately; `none` turns it off for the given request. | docs.stripe.com/billing/subscriptions/prorations; docs.stripe.com/api/subscriptions/update | [secondary] |
| Webhooks: event ordering is not guaranteed, duplicates are possible (deduplication by the event id), the signature in the `Stripe-Signature` header; a response other than 2xx causes a retry. | docs.stripe.com/webhooks; docs.stripe.com/events/how-events-work | [secondary] |
| Smart Retries retries failed payments; the recommended setting: 8 attempts within 2 weeks, configurable. | docs.stripe.com/billing/revenue-recovery/smart-retries | [secondary] |
| The `Idempotency-Key` header, max. 255 characters; API v1 keeps the keys for at least 24 h, API v2 — a 30-day window. | docs.stripe.com/api/idempotent_requests | [secondary] |

## Mapping states to access (a template for the business decision)
| State | Meaning | Access (proposal) |
|---|---|---|
| trialing | before the first payment | full |
| active | paid | full |
| past due | the payment did not go through, retries ongoing | full + a banner (grace period) |
| unpaid | retries exhausted, the subscription continues | read and export only |
| paused | e.g. the end of a trial without a card | read and export only |
| incomplete / incomplete expired | the first payment did not go through | none (an account without a plan) |
| canceled | the end | none; data per retention and the right to export |

## Money and VAT
| Fact | Source | Status |
|---|---|---|
| From 1.07.2021 a single EU threshold of EUR 10,000 (distance sales of goods and TBE services together) for a supplier from one EU state; above the threshold the consumer's country VAT, settled through OSS. For TBE services the threshold existed already from 1.01.2019. | taxation-customs.ec.europa.eu/online-sellers_en; vat-one-stop-shop.ec.europa.eu/one-stop-shop_en | [secondary; to be confirmed by accounting] |
| Decimal places: JPY 0, KWD 3, BHD 3 (CLDR `supplementalData.xml`, `<fractions>`; the SIX list not checked). An amount as an integer in the smallest unit is a practice, not something a standard states. | github.com/unicode-org/cldr, `common/supplemental/supplementalData.xml` (main, accessed 2026-10-20) | confirmed in CLDR |

Legal and tax facts (KSeF, consumer rights, withdrawal) are outside the factory's scope — notes
in `.claude/skills/arch-eu-product-law/references/outside-factory-scope.md`; before deployment check them
in primary sources (EUR-Lex, ISAP, tax administration pages) or with accounting.

## Webhook — a handling sketch
1. Read the raw body → verify the signature and time tolerance → 400 on an error.
2. `INSERT … ON CONFLICT (event_id) DO NOTHING` into the events table → 2xx.
3. A worker (inbox): in one transaction the effect + marking the event as handled; when the order is in doubt it
   fetches the current object from the provider's API and reconciles the state.
