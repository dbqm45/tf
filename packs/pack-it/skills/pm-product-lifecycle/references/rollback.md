# Retiring a product or module

## Go/no-go criteria
| Criterion | Question | Data |
|---|---|---|
| Usage | how many customers use it and how often; are they key customers | analytics, a customer list with MRR |
| Revenue | how much revenue depends on the product, also indirectly (a reason to buy a bundle) | billing, sales conversations |
| Cost | people, infrastructure, licences, support, security risk | budget, tickets, dependency scans |
| Contracts | do contracts, SLAs, tender offers guarantee the function and until when | contracts, terms of service |
| Replacement | is there a replacement or a workaround and how much does the customer's migration cost | a test with customers |
| Impact | what the largest customers lose; churn risk | conversations, cohort NRR |
"Go" when the cost and risk of maintenance outweigh the revenue at risk of churn, and the contracts allow the change.

## Schedule (typical stages)
1. **Decision** internal and a plan.
2. **Announcement** — the shutdown date and the reason; the period depends on contracts and the cost of the customer's migration (usually 3–12 months).
3. **End of sale** — the product disappears from the offer and the price list for new customers.
4. **End of support** — only security fixes or nothing (say so plainly).
5. **Shutdown** — access closed; data export still available for an agreed period.
6. **Data deletion** — per the contract and the retention policy; confirmation for customers who ask for it.

## Order of stakeholders
The board and budget owners → support, sales, account managers (before a customer asks) → key customers
in person → all customers (in the product, email, documentation) → partners and integrators → publicly (a page,
a changelog note). Nobody on the team learns of it from the public announcement.

## Message to customers
What is changing · why (honestly, with a benefit for the customer, if there is one) · from when (the dates of the stages) · what the customer is to
do (a replacement, migration, export — with instructions) · who will help (a contact) · what happens to data and fees (a refund,
a plan change). No jargon and no promises that are not in the plan.

## Checklist with owners
- [ ] decision and criteria recorded (product owner)
- [ ] review of contracts, SLAs and terms of service (a lawyer)
- [ ] a replacement or migration instructions ready and tested with a customer (product team)
- [ ] data export in an open format, the duration of the export (engineering)
- [ ] billing: end of fees, refunds, plan changes (finance, be-billing-subscriptions)
- [ ] support: answers to typical questions, scripts (support)
- [ ] documentation, price list, page, sales materials updated (marketing)
- [ ] in the product: a warning for users of the module with a date (engineering)
- [ ] usage monitoring after the announcement — who still uses it a week before the shutdown (analytics)
- [ ] removal of code, data, infrastructure and costs after the shutdown (engineering)
- [ ] summary: migration, churn, savings (product owner)
