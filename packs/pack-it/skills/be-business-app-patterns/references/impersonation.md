# Impersonation (support acts as the user)

## First: whether less is enough
- A read-only view of the customer's account or screen sharing by the customer often solves the problem without
  acting on their behalf.

## If impersonation
- A separate permission (not every support role), a reason or a ticket number required at the start; for sensitive
  accounts the customer's consent.
- A session with two identifiers: `user_id` (on whose behalf) and `actor_id` (who acts) — both in every audit
  entry and in the logs.
- A banner in the interface for the whole duration and an end button; a short time limit (e.g. 30 min).
- Forbidden in impersonation mode: changing the password, email, MFA, payment methods, data export, deleting the account,
  financial operations — checked on the server by `actor_id`.
- Never through the customer's password or their token; a session issued by the server on the basis of the support permission.
- A notification to the customer (an email or an entry in the account history) that support had access.

## Tests
- A forbidden operation returns a refusal in impersonation mode; the audit entry has both identifiers; the session expires after
  the limit; a user without the permission will not start impersonation.
