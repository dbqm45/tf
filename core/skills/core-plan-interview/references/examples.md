# Plan interview — worked examples

Contents: 1. Auth migration (independent first round, a held-back question) · 2. Feature flag (summary and
confirmation) · 3. OAuth move while the human is away (assumptions) · 4. Pruning an over-grown interview

## 1. Moving login from sessions to an identity provider
Facts checked first (not asked): the app uses cookie sessions in the auth module; 3 roles (`admin`, `agent`,
`customer`); 40k active users in the last 30 days (from the metrics dashboard config).
Size: complex — an external provider, user data, every page → about 12 questions in three rounds.

```
Round 1 — 4 questions, answer by number

Q1. Which provider
   a) the company's existing Entra ID tenant — already paid for, staff accounts there; customers would need guest accounts
   b) a customer-facing IdP (e.g. Auth0) — built for external users; new contract and cost
   Recommendation: b — 95% of users are customers (role counts above).

Q2. Existing passwords
   a) migrate hashes to the IdP — no reset for users; needs a compatible hash format
   b) force a reset on first login — simple; friction for 40k users
   Recommendation: a, if the IdP accepts bcrypt imports — I will check its docs before round 2.

Q3. Admin accounts — same flow as customers or a separate one?
   Recommendation: separate, with MFA required.

Q4. Deadline driver — a security audit, a contract, or none?
   Recommendation: none assumed until you say otherwise.
```
Held back to round 2: "big-bang switch or gradual by role" — it depends on Q1 and Q3.
Round 2 adds that question plus session lifetime and logout across devices.

## 2. Adding a feature flag around a new checkout
After two rounds (7 questions):
```
Summary — is that how we understand it?
Decisions
  D1. Flag key checkout-v2, default off, toggled per tenant.
  D2. Old checkout stays until 100% rollout plus two weeks.
  D3. Metrics: conversion and payment errors per variant.
Assumptions
  A1. The existing flag service handles per-tenant targeting (confirmed in its config; no new service).
Out of scope
  - Redesign of the cart page.
Reply "yes" or correct a line by its number.
```
The human replies "D2: one week, otherwise yes". Only now is the plan written; D1–D3 go to `decisions.md`.

## 3. "I'm on leave until Monday — plan the OAuth move"
No decision may be taken for the human, so the recommendations become labelled assumptions:
```
Nothing will be implemented before you confirm. Assumptions taken from my recommendations:
  A1. Provider: the customer-facing IdP (Q1 b).
  A2. Password hashes migrated, no forced reset (Q2 a) — the IdP accepts bcrypt (checked in its import docs).
  A3. Admins use a separate flow with MFA (Q3).
  A4. No external deadline (Q4).
Open, needs you: big-bang vs. gradual rollout.
```
The plan draft is marked "based on unconfirmed assumptions A1–A4"; work waits for Monday.

## 4. Pruning an over-grown interview
A simple CSV export produced 40 edge-case questions and a three-week plan. Re-ranked by impact × likelihood:
- kept (5): which columns, date and number format, size limit, who may export, where the file goes;
- answered "fail with a readable error": malformed rows, exports above the limit, unsupported characters;
- dropped: scenarios with no user who hits them.
Result: 5 questions in one round, a two-day plan.
