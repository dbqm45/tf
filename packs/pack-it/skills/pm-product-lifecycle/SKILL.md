---
name: pm-product-lifecycle
description: Use for the life stage of a product or module — growth, maturity, decline; a decision to extend, replace, maintain or retire; a retirement plan with customers.
metadata:
  review: "2027-10-23"
  catalog: "Use when a product, a pricing plan or a module stops growing or costs more than it gives — recognising the lifecycle stage (introduction, growth, maturity, decline) from data, choosing a move (invest, extend life, replace, maintain without development, retire) with go/no-go decision criteria, a retirement plan: the order of stakeholders, a message to customers, a schedule (announcement, end of sale, end of support, shutdown), migration and data export, contracts and law, a checklist with owners. Not for technical retirement of an API version (be-api-design), releases and feature flags (ops-release-engineering), SaaS metrics or choosing new features (proc-product-discovery)."
  keywords: "cykl życia produktu, produkt przestał rosnąć, rynek nasycony, schyłek produktu, wycofać produkt, wyłączyć moduł, wygaszenie produktu, sunset, end of life, koniec wsparcia, koniec sprzedaży, mało kto używa, utrzymanie kosztuje, zastąpić produkt, przedłużyć życie produktu, migracja klientów, ogłoszenie wycofania, product lifecycle, the product stopped growing, saturated market, product decline, retire a product, switch off a module, product sunset, end of support, end of sale, hardly anyone uses it, maintenance costs too much, replace a product, extend a product's life, customer migration, retirement announcement"
---

# Product lifecycle and retirement

Goal: a decision about a product or module based on data, and when the decision is "retire" — a shutdown without surprising
customers, without losing their data and without breaking contracts. A human decides; you provide data, options and a plan.

## Procedure
1. **The stage from data**, not from an impression: the trend of revenue and of the number of active customers (12–24 months), cohort retention,
   share of revenue, cost of maintenance (people, infrastructure, support), competitors' price pressure.
   Stages: introduction → growth → maturity (growth slows, the market is saturated, competition on price) → decline
   (customers and revenue fall).
2. **Moves to choose from** — compare at least three with cost, risk and impact on customers:
   - **keep investing** — when growth has a cause we know how to strengthen;
   - **extend life** — new users (a segment, a country), new uses, more frequent use among current ones;
   - **replace** — a new product or module takes over the customers (migration as a project);
   - **maintain without development** — only fixes and security, minimal cost, revenue collected to the end;
   - **retire** — when cost and risk (security, dependencies without support) outweigh the value.
3. **Go/no-go for retirement** — the criteria in `references/rollback.md` (usage, revenue, cost, contracts, a replacement,
   impact on key customers); the result recorded as a decision with a date (core-project-record).
4. **Retirement plan** — a schedule, the order of stakeholders, a message, migration, a checklist with owners:
   `references/rollback.md`. The order of people and the communication plan per pm-stakeholders.
5. **Law and contracts** — customer contracts and SLAs, terms of service, data export and deletion (GDPR), for cloud
   services the customer's right to switch provider and move data (Data Act) — with arch-eu-product-law.
6. **After the shutdown** — measure: how many customers moved to the replacement, how many left, support tickets,
   cost savings; lessons to the project log.

## Example
A reports module: 4% of customers active monthly, 1 FTE of maintenance, a chart library without support for a year.
Options: maintain (the cost of 1 FTE, a security risk), replace with an export to a spreadsheet + a template in a BI tool,
retire without a replacement. Recommendation: replace. Go criteria: 3 of the 5 largest customers of the module accept
the replacement in conversations, the contracts do not guarantee the module. Schedule: day 0 — the support team and account
managers; day 7 — conversations with key customers; day 14 — an in-product announcement and an email; day 14 —
end of availability to new customers; day 104 — shutdown (90 days after the announcement), data export available
until day 134, then deletion.

## Sources
- T. Levitt, "Exploit the Product Life Cycle", *Harvard Business Review* (1965) — the stages and ways of extending
  a product's life.
- Regulation (EU) 2023/2854 (Data Act), Chapter VI — switching between data processing service providers.
Described in our own words.
