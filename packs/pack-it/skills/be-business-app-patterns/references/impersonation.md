# Impersonation (support acts as the user)

Measured on the factory's task scenarios (2026-11-23): models design this well without the skill, so only the
decisions that are easy to skip are kept.

- Prefer a read-only view of the account or screen sharing; impersonate only when that is not enough.
- A separate permission and a reason (ticket number) at the start; a session issued by the server, never the
  customer's password or token.
- Both identifiers — `user_id` (on whose behalf) and `actor_id` (who acts) — in every audit entry; a short limit
  (e.g. 30 min) and a visible banner; the customer notified afterwards.
- Refused on the server in this mode: password, email, MFA, payment methods, data export, account deletion.
- Tests: a forbidden operation is refused, the audit entry has both identifiers, the session expires, a user without
  the permission cannot start it.
