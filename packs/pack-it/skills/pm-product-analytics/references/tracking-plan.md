# Tracking plan

## The format of one event
| Field | Example | Notes |
|---|---|---|
| name | `invoice_sent` | `obiekt_czynność` (object_action), past tense, `snake_case`, English; no screen names or UI versions |
| question | "how many customers send their first invoice within 7 days" | what the event is for |
| source | server | server for business facts, client for UI behaviour |
| properties | `invoice_id` (string), `amount_band` (`<1k`, `1k-10k`, `>10k`), `is_first` (bool) | type and allowed values; ranges instead of exact amounts when they suffice |
| owner | the invoicing team | who is responsible for correctness |
| version | 2 (from 2026-11-09: `is_first` added) | a change of type or meaning = a new name |

## Naming rules
- One vocabulary of objects (`account`, `invoice`, `project`) and actions (`created`, `viewed`, `submitted`,
  `completed`, `failed`, `deleted`); a new action only when none fits.
- The result of a step as a property, not separate events: `payment_completed` with `status: failed` is not good —
  a separate `payment_failed` with `reason`, because the funnel counts successes.
- Common properties (`app_version`, `platform`, `plan`) are set by one layer, not by every call.

## Where to keep the plan
- A file in the repo (YAML or JSON) next to the code; from it types for the client and validation in CI or in the tool (an event
  schema), so that a typo in a name does not create a new event.
- A plan review on every change of events in a PR (like a database migration).

## Identity
- Before login: an anonymous ID from the tool or your own (random, without personal data).
- At registration and login: linking the anonymous ID with `user_id` once, in one place in the code.
- Logout: reset the identifier so that the next user on that device does not get someone else's history.
- Company accounts (B2B): additionally `account_id` or a group, to count a company's activity, not only a person's.
