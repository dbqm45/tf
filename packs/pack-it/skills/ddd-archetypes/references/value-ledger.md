# Value ledger — balances that accumulate, get used and expire

## When it applies
- Signal: someone asks "how much X does S have — and why?" and the answer is a number with a history.
- If people instead ask "which status is it in?", a state machine fits better.
- Not only money: loyalty points, leave days, data allowances, API credits, stock units, prepaid hours, vouchers.

## Core shape
- **Transaction** at the centre: an atomic set of ≥2 **entries** on ≥2 accounts — all entries are posted or none.
- **Account**: an anchor for entries, never a big aggregate holding its whole history. It has an owner, a unit
  (EUR, point, day, credit) and a **balance policy**: no negative balance, unrestricted, or overdraft down to a limit.
  The policy may differ by initiator (a system correction may go below zero, a customer may not).
- Account kinds: asset, liability, revenue, expense; **source pools** (a promotion budget, the monthly allowance);
  memo / off-balance accounts that do not affect balances; virtual report accounts defined by a filter over entries.
- **Entry**: account, signed amount (or debit/credit), `recorded_at` (when written; immutable, now), `effective_at`
  (when it counts; may be earlier for a backdated correction), optional validity window (from / until), optional link to
  the entry it offsets.
- **Summary account**: groups other accounts for reporting and answers balance and statement queries over all their
  entries. Entries are posted only to leaf accounts. Grouping is a tree, or a graph without cycles when one account
  belongs to several reports — then an entry reachable twice is counted once.
- **Corresponding accounts**: two parties keep their own account of the same holding (our receivable, their payable;
  our record of a bank account, the bank's statement). They stay two accounts with their own entries and are
  **reconciled** — matched exactly or within a tolerance (dates, fees).
- **Posting rule**: a composable condition on an event, rules choosing target accounts, an amount computation, a priority.
  A new fee, levy or reserve is new configuration, not new code.

## Rules
- Double entry: for balance-sheet accounts debits and credits of a transaction net to zero.
- The balance is derived from entries; a cached snapshot (with the last entry id) is allowed for speed. Never write a
  balance column directly.
- The balance at instant T counts only entries effective by T and valid at T.
- A mistake is never edited or deleted: post a **reversing transaction** that mirrors the original and references it.
- Decide per transaction type whether it can be reversed (always / conditionally / never) and whether a reversal cascades
  into consumption that the reversed value funded.
- **Expiry** is a transaction into an expired / forfeited account, so analytics see the lost value — not a filter that
  silently hides entries.
- With several origins of the same value, the draw-down order is explicit: FIFO, LIFO, earliest expiry first, source
  priority, pro-rata or manual — usually a parameter.
- **Idempotency**: the source event id is stored on the transaction with a unique constraint, so the same event never
  accrues twice.
- Memo / tracking entries may be one-sided (they are excluded from the zero-sum check), but value never moves between a
  tracking account and a real one.
- Several reporting cuts for one entry (by customer and by cost type): prefer an attribute on the entry plus a report
  account defined by a filter; add real accounts only where the flow itself must be tracked (who still owes what).
- Specialise by domain names: stock is a *holding* per item × location and a *movement* is a balanced transaction whose
  entries all carry the same item; expected stock (ordered, not yet received) lives in parallel holdings.
- Optimistic version locking is needed only on accounts where a limit is enforced (no negative, overdraft).
- The ledger enforces structural numeric limits only; "may this person transfer days?" is authorisation outside.

## Decisions to settle
- Strictly append-only, or may unposted drafts be edited?
- Is backdating allowed, and how far back?
- Transfers between owners: direct, or through a transit account?
- Do pending or awaiting-approval states hold value, and on which account (a reserved / held account)?
- Integer or fractional units? Caps on accrual speed (max points per day)?
- Which reversals cascade; who bears a negative balance created by a reversal?

## Belongs elsewhere
- Computing the amount (fee, interest, discount) → price calculation; the ledger only posts the result.
- Exclusive use of a single item → resource holds (a counted divisible pool *is* a ledger).
- Who may post or transfer → authorisation / policy layer.

## Traps
- `points` column updated in place; corrections that overwrite; no answer to "why is my balance X".
- One account aggregate loading thousands of entries to post one more.
- Our record and the bank's (or partner's) record modelled as one account — differences cannot be reconciled or shown.
- Overlapping summary accounts summed by hand — shared entries counted twice.
- Expiry implemented as `WHERE expires_at > now()` — the lost value disappears from reports.
- A retried message accrues twice because there is no unique source event id.
- Only one timestamp — a backdated correction then falsifies "what did we show the customer last week".

## Worked example
Requirement: employees accrue 2.08 leave days a month, carry-over expires on 31 March, HR corrects mistakes.
- Accounts per employee: `leave-current`, `leave-carried` (unit: day, policy: overdraft to −2 when initiated by HR only).
  Counter accounts: `leave-entitlement`, `leave-taken`, `leave-forfeited`.
- Monthly accrual: *leave-entitlement → leave-current 2.08*, source event `accrual-2026-04-E117` (unique).
- New year: remainder *leave-current → leave-carried*, validity until 31 March; leave taken draws `leave-carried` first
  (earliest expiry first).
- 1 April: remainder of `leave-carried` → `leave-forfeited` (a transaction, visible in the HR report).
- HR finds a wrong accrual from February: a reversal with `effective_at = 2026-02-28`, `recorded_at = now`, linked to
  the original; the February balance as shown at the time stays reproducible.
