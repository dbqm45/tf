---
artifact: requirements
phase: requirements
status: accepted
version: 1
author: user
created: 2026-09-27
updated: 2026-09-27
inputs: [docs/project/01-discovery/brief.md]
---
# Requirements: Room and desk booking

## TL;DR
6 MVP stories. Key attributes: no double bookings under concurrency, M365 SSO, 99.5% availability during working hours.

## Stories (MVP)
| ID | As … I want … so that … | Acceptance criteria | Priority |
|---|---|---|---|
| H1 | employee — book a room for a time slot | Given the room is free When I book Then a booking and an entry in M365 | H |
| H2 | employee — book a desk for a day | as H1 | H |
| H3 | facility — block a resource for maintenance | a blocked resource cannot be booked | H |
| H4 | system — release a booking without a check-in after 15 min | the resource returns to the pool | M |
| H5 | employee — see the availability calendar of resources | a day/week view | H |
| H6 | employee — sign in with the company account | Entra ID SSO | H |
## Quality attributes (scenarios — input for the architecture)
| Attribute | Scenario | Priority |
|---|---|---|
| Consistency | 50 people book the same room at the same time at 9:00 → exactly 1 success, the rest get a clear refusal, 0 double bookings | H,H |
| Security | sign-in only with a company Entra ID account; data in the EU | H,M |
| Availability | 99.5% during 7:00–19:00 | M,M |
| Modifiability | a new resource type (e.g. a parking space) in ≤ 2 working days | H,M |
## Technical and organisational constraints
Azure (EU), a TS/Angular + Java team, MVP in 3 months.
## Out of scope (MVP)
Settlements, a native application.

## Open questions
- [ ] Booking limits per person? → facility

## Handoff
- **For:** tomasz (solution architect)
- **Task:** the stack and the architecture style
- **Read:** TL;DR, Quality attributes, Constraints
