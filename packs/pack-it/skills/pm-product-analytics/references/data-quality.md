# Event data quality

## A mismatch between analytics and the database — check in order
1. **Definition** — are you counting the same thing: test accounts, deleted accounts, signups through the API or an import, invited
   users.
2. **Time zone and window** — the tool in UTC or the project's zone, the database in another; month boundaries shifted.
3. **Event source** — a client event: ad blockers, no consent, the tab closed before sending,
   a mobile app without network. Typically a few to a dozen or so percent lower than in the database.
4. **Identity** — duplicates after a wrong `identify` (one person as two), two people merged into one after a shared
   device.
5. **Non-human traffic** — bots and automated tests inflate client events.
6. **Delay** — data from the last hours or days has not arrived yet (queues, batch processing).
Result: a table of cause → estimated impact → how to check → fix. Move the key business facts to the server.

## Instrumentation tests
- An e2e or integration test captures the events sent and checks the name and properties against the plan.
- Schema validation (a tool or your own) rejects or flags events outside the plan.
- A daily report: the number of key events against the database, an alert on a deviation above a set threshold.
