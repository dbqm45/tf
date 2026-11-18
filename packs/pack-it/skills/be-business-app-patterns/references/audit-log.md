# Audit log

## What to record in one entry
| Field | Example | Notes |
|---|---|---|
| when | `2026-11-09T18:20:00Z` | the server time, UTC |
| who | `user_id`, role | with impersonation also `actor_id` (who really acted) |
| from where | IP, client (web, API, background job), `request_id` | for correlation with the application logs |
| what | `order.status_changed`, `order_id` | an event type from a dictionary, not free text |
| change | `{"status": ["new", "paid"]}` | the old and new value of only the changed fields |
| reason | "refund at the customer's request", a ticket number | required for sensitive operations |

## Writing
- In the same transaction as the data change (an audit table in the same database) or through an outbox
  (be-messaging-outbox), when the audit goes to a separate system — never "afterwards", because a failure between the writes loses the entry.
- Append only: the application has no `UPDATE`/`DELETE` permissions on the audit table; for high requirements a hash
  chain or a WORM store.
- Writing in the service layer (one place), not in controllers; changes from background jobs and data migrations too.

## Personal data and retention
- Do not record sensitive values in full (passwords, tokens, card numbers never; personal data only when the purpose
  requires it) — instead of the value the information "field changed".
- The retention period set with the purpose (disputes, settlements, legal requirements); a data erasure request also covers
  the audit — pseudonymizing entries instead of deleting the history, if the audit must stay.

## Reading
- An object history view for the user (who changed my order) and search for an auditor; access to
  the full audit only for designated roles, and reading the audit is itself audited.
