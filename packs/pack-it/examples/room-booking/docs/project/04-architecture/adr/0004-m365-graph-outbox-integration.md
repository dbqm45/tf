---
artifact: adr
phase: architecture
status: accepted
version: 1
author: tomasz-solution-architect
created: 2026-09-27
updated: 2026-09-27
inputs: [docs/project/03-requirements/requirements.md, docs/project/04-architecture/stack-decision.md]
---
# 0004. M365 integration: Microsoft Graph, application permissions, outbox, one-way synchronisation

## Context
H1 requires an entry of the room booking in the M365 calendar. Booking consistency (ADR-0002) must not depend on the availability
of an external API. We do not know yet whether the rooms are resource mailboxes (room mailbox) in Exchange and whether people book them
directly in Outlook — then two sources of truth arise (an open question for IT).

## Decision
**[proposal, conditional — depends on IT's answer]**
- The source of truth about availability is the application. Synchronisation **one way**: application → M365 calendar (creating, changing, cancelling an event).
- The booking and the domain event are saved in one transaction (Spring Modulith Event Publication Registry, JDBC = outbox); the `calendarsync` module sends to Graph asynchronously with retries. A Graph failure does not roll back the booking; the UI shows the synchronisation state.
- The application permission `Calendars.ReadWrite` granted through **Exchange Online RBAC for Applications** with the scope limited to the group of employees and the room mailboxes (no tenant-wide permission in Entra). The application authenticates to Graph with a Managed Identity or a certificate in Key Vault.
- If the rooms are resource mailboxes: direct bookings in Exchange must be blocked (the mailbox booking policy) or the decision about the source of truth goes back to the user.

## Options considered
- Graph, application permissions + outbox (chosen) — pros: the booking is independent of Graph, retries, it also works for background jobs (no-show release cancels the event); cons: needs the M365 administrator's consent and the RBAC for Applications configuration.
- Delegated Graph (On-Behalf-Of) synchronously in the request — pros: works on behalf of the user, narrower permissions; cons: the booking depends on Graph at the 9:00 peak, background jobs (no-show) have no user token.
- An iCalendar (.ics) invitation by email — pros: no calendar permissions; cons: the user must accept it, no automatic cancellation on a no-show, weaker UX. The fallback option if IT does not give consent.
- Exchange as the source of truth for rooms — rejected at first: the "0 double bookings" guarantee would move outside our database and outside the (H,H) scenario.

## Consequences
- Eventual consistency between the application and Outlook (seconds–minutes) — acceptable, because the application decides about availability.
- Needed: an application registration in Entra, the administrator's consent, the RBAC scope in Exchange (spike S3), a test on a developer tenant (S2).
- The first vertical slice (H6 + H1) can be built without synchronisation — we add `calendarsync` after S2/S3.
