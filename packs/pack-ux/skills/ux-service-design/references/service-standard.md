# Service standard and service prototyping

## Contents
1. GOV.UK Service Standard
2. Service prototyping
3. Boundaries

## 1. GOV.UK Service Standard
The UK government's standard for public services, 14 points. Titles (as per the search results and the model's
knowledge, accessed 2026-10-17; check the full list at gov.uk/service-manual/service-standard [unverified
for points 5–9 and 11–13]):
1. Understand users and their needs
2. Solve a whole problem for users
3. Provide a joined up experience across channels
4. Make the service simple to use
5. Make sure everyone can use the service
6. Have a multidisciplinary team
7. Use agile ways of working
8. Iterate and improve frequently
9. Create a secure service which protects users’ privacy
10. Define what success looks like and publish performance data
11. Choose the right tools and technology
12. Make new source code open
13. Use and contribute to open standards, common components and patterns
14. Operate a reliable service

What to use it for outside the public sector: points 2 and 3 as blueprint check questions ("do we solve the customer's whole
problem, also where our department ends?", "does a channel change lose the state?"), point 10 as a
model for metrics. Formal service assessments concern the UK administration; in another country the standard is a
model, not a requirement.

## 2. Service prototyping
| Method | What it tests | Cost | Note |
|---|---|---|---|
| Role-play / bodystorming | conversations, the layout of the place, handoffs | low | staff play the customer and the other way round |
| Concierge | whether the customer wants the result of the service | low, slow at scale | the customer knows a human does it |
| Wizard of Oz | whether the interaction with the "system" works | medium | the customer does not know; tell them after the session |
| Physical mock-up / paper form | layout, readability | low | |
| A pilot in one branch | the whole service on real traffic | high | a rollback plan first |
Choice: the cheapest method that settles the riskiest assumption (proc-product-discovery: assumption tests).

## 3. Boundaries
A question about a screen or a form state — ux-feature-design. A conversation with experts about domain events — ddd-event-storming.
The ethics of consents and manipulation — ux-feature-design (`content-and-ethics.md`).
