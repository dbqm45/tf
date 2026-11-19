---
artifact: brief
phase: discovery
status: accepted
version: 1
author: user
created: 2026-09-27
updated: 2026-09-27
inputs: []
---
# Brief: Room and desk booking

## TL;DR
A company (300 people, a hybrid work model) books rooms and desks in a spreadsheet — double bookings happen. Goal: a web application
for self-service bookings with an integration with the Microsoft 365 calendar. Success: 90% of bookings self-service within 3 months,
zero double bookings. Constraints: MVP in 3 months, a team of 2 × TypeScript/Angular + 1 × Java, Azure hosting in the EU.

## Problem and context
Bookings in a shared Excel spreadsheet; conflicts and "dead" bookings (nobody came).
## Users and stakeholders
Employees (they book), reception/facility (manages the resources, blocks them for maintenance), IT (operations).
## Goals and success measures
| Goal | Measure | Target value |
|---|---|---|
| Self-service | % of bookings through the application | 90% after 3 months |
| No conflicts | double bookings | 0 |
## Scope
- In scope: booking rooms and desks for time slots, maintenance blocks, releasing unclaimed bookings, Microsoft SSO (Entra ID), writing to the M365 calendar.
- Out of scope: cost settlement, a native mobile application.
## Constraints
MVP in 3 months; a team of 2 × TS/Angular, 1 × Java (Spring); Azure hosting, data in the EU; a low operations budget.
## Project type
greenfield

## Open questions
- [ ] Do desks have assigned zones/permissions? → facility

## Handoff
- **For:** tomasz (solution architect)
- **Task:** a recommendation of the stack and the architecture style (04-architecture/stack-decision.md)
- **Read:** TL;DR, Scope, Constraints and the requirements (03-requirements)
- **Done when:** stack-decision.md has the status proposed and passes project_record.py check
