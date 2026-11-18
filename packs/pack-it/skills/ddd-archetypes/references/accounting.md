# The Accounting archetype — mapper (value, accounts, entries, transactions)

> **Contents:** Fit test · Model (the essence) · Questions · Mapping steps · Decisions to check (R/A/X) · Result format · Patterns and pitfalls · Quality check · Example (shortened)

It turns requirements in which something **accumulates or is consumed** into an accounting model: accounts, transactions, entries, reversals,
validity periods and the settlement order. The value does not have to be money: points, leave days, a data limit, API credits,
items in a warehouse, hours in a package. The effect: every balance can be **explained, reversed without losing history, audited
and analysed**. The common protocol (questions, "It depends", the R/A/X check, recording): `SKILL.md` → "Mapper — the common protocol".

## Fit test
**The core question:** *can you ask "how much X does subject S have?" and get a meaningful number with a transaction history?*
Yes → the archetype probably fits. The natural question is "what state is X in?" → that is a state machine, not a ledger.

| Signal in the requirements | Fits? |
|---|---|
| "earns / spends / accrues / consumes N units" | ✅ |
| "the balance cannot drop below zero", a limit, a pool | ✅ |
| "grant / refund / expire / transfer / correct" | ✅ |
| "where did this balance come from?", settlements, reversal | ✅ |
| "a ticket goes: open → assigned → closed" | ❌ a state machine |
| "a document has versions / diffs / branches" | ❌ a version graph |
| "follows / stops following" | ❌ a relationship graph (→ Party) |
| "a response within 1 h" (SLA) | ❌ a time constraint on an event, not a value |
| "slot free / taken / blocked" | ⚠️ borderline |

**Borderline cases:**
- *Appointments/slots* — can the same unit be **partially** consumed? Binary free/taken → state (→ Availability).
  Numeric capacity ("a room for 10 people, 7 taken") → a value → fits (often together with Availability).
- *Permissions / flags* — on/off, nothing accumulates → state.
- *Position in a queue* — order, not a balance → Waitlist.

## Model (the essence)
- **Account** — the place where value lives; a type, a unit, a balance policy, a version (optimistic locking). The balance **results
  from the entries** — adding an entry does not require loading the whole history.
- **Account types:** assets (the subject's value), liabilities/obligations (value owed, pending), revenue, expenses, **pools**
  (sources of value: a promotion, a monthly allocation) and **off-balance** (informational, conditional, forecasts — with no effect on the balance).
- **Entry** — a charge (debit) or a credit to one account: an amount in the canonical unit, **two times**:
  `created` (always now, not editable) and `effective_from` (the moment effective for the balance — may be earlier for a backdated
  correction), optionally a validity period and a link to the entry it settles.
- **Transaction** — an atomic set of entries with a type; ≥ 2 entries on ≥ 2 accounts; for balance-sheet accounts **sum = 0**
  (double entry). It writes all entries at once or none. The transaction is in the centre — not "one big account with a list of operations".
- **Reversal** — mistakes are not edited or deleted: a reversing transaction (mirror entries) with a reference to the original.
- **Allocation** — settling entries against each other: FIFO, LIFO, source priority, proportionally, manually.
- **Projection account** — a virtual account defined by a filter (e.g. "all overdue receivables") — a report without
  moving value.
- **Posting rules** — a reaction to events/entries: a qualification condition (composable and/or/not), the choice of target accounts
  (by tags), a calculator creating the transaction; rule priority. A new financial effect (commission, tax, provision) = configuration.

## Questions
**A — standard decisions** (ask only about unsettled ones; each may have the answer "yes for some cases"):
- An **append-only** ledger, or do you allow editing/deleting entries in some cases?
- Does the value **expire**? Which entries, after what time, calendar-based or rolling?
- Can any account / transaction type go **below zero**? (it may depend on the account or the initiator)
- Is **backdated** posting allowed (`effective_from ≠ created`)?
- Can value be **transferred** between subjects?
- **Units:** one or several? Are they convertible (1 GB = 1024 MB, currencies)?

**B — gaps** (examples; look on your own for what the archetype can do and the requirements do not say):
- the order of consuming sources (promotional vs bought vs earned)? · a balance limit or an accrual rate limit? · different validity per source?
- distinguishing "earned" vs "granted by an admin" (analytics, policies)? · **cascading reversals** (also reverse consumption
  paid for with the reversed value)? · audit/export/GDPR? · protection against **double accrual** of the same event
  (idempotency)? · a "pending approval" state — where does the value live in the meantime?

## Mapping steps
1. **Value** — what accumulates/is consumed? A name (`LEAVE_DAYS`, `POINTS`) and **the canonical unit**; with many units —
   conversion factors; entries always in the canonical unit.
2. **Accounts** — all the places where value lives: different owners, different sources of the same value, contra accounts
   for double entry. Name `{owner}_{value}_{purpose}`. For each: type, unit, **balance policy**:
   `block` | `allow` | `overdraft_to: N`.
3. **Transaction types** — from the domain verbs (grant, buy, consume, refund, expire, transfer, correct) and periodic jobs
   (monthly reset, expiry). For each: the triggering event, the flow direction, the initiator (user/system), reversibility.
4. **Entries** — debit/credit pairs for each transaction; sum = 0; the rule for `effective_from`.
5. **Reversals** — for each type: always / conditionally (window, sufficient balance) / never (e.g. expiry); mirror entries
   + a reference to the original; possible cascades.
6. **Validity** — for pools with a deadline: `valid_from`, `valid_to`, what happens on expiry (an expiring transaction to an "expired" account).
   The balance is computed only from entries valid at the given moment.
7. **Allocation** — when the subject has several sources of the same value: the consumption order and its justification.
8. **Posting rules** — automatic effects of events (commission, tax, bonus) as rules, not an `if` in transactions.

## Decisions to check (R/A/X)
the balance policy of each account (and per initiator) · expiry (which entries, calendar/rolling, what happens on expiry) ·
the allocation order · the transfer model (directly / through a transit account; who initiates) · reversal rules (who, in what window) ·
backdated posting · the pending state and where the value lives in it · an administrative correction (does it break the constraints) ·
append-only · whole vs fractional units · limits · edge cases (what about value "in transit" when it expires or a reset happens).

## Result format
```markdown
# Accounting model: <area>
## Value              — name, description, canonical unit, conversion factors
## Concept mapping    — | Domain concept | Archetype element | Justification |
## Unmapped concepts
## Accounts           — | Account | Type | Unit | Balance policy | Description |
## Transactions and entries
### <transaction>  — Trigger · Reversible: yes/no/conditionally (condition)
| # | Account | Debit/Credit | Amount | effective_from | Notes |
## Validity           — | Account | Valid from | Valid to | On expiry |
## Allocation         — consumption order with justification
## Reversals          — | Transaction | Reversal trigger | Reversible? | Condition |
## Posting rules      — condition → accounts → calculator
## Decisions (R/A/X)  — | Decision | Source |
## Notes              — assumptions (X), edge cases, variable policy parameters
```

## Patterns and pitfalls
- **The transaction in the centre**, accounts as reference points — it scales better than an account aggregate with a list of operations.
- A balance as a column updated with `UPDATE` loses history; a balance from entries (with a cache/snapshot for performance) does not.
- "May employee X hand over Y days?" (active? annual limit? HR approval?) — **outside the ledger**; the ledger only records
  and guards structural constraints (balance ≥ 0).
- A variable policy ("premium: points valid for 365 days, the rest 90") → the ledger gets a ready `valid_to`.
- Idempotency: the identifier of the source event on the transaction + uniqueness → no double accrual.
- Expiry is a **transaction** (to an "expired" account), not a silent filter — otherwise analytics will not show how much value was lost.
- Amounts as Quantity/Money (an integer in the smallest unit) — `quantity-money.md`.
- Concurrency: a version on an account with the `block` policy; accounts with `allow` do not need to lock.

## Quality check
- [ ] every transaction has ≥ 1 debit and ≥ 1 credit; balance-sheet accounts sum to zero
- [ ] every account in the entries is defined and has a balance policy and a unit
- [ ] every entry has the semantics of `created` and `effective_from` described
- [ ] every reversible transaction has a reversal mechanism; irreversible ones are named
- [ ] accounts with a deadline have validity rules; the allocation covers all combinations of sources
- [ ] the mapping table and "Unmapped concepts" present; answers/assumptions reflected in the model; no material (X)

## Example (shortened)
**Input:** "An employee gets 26 days of leave per year. Unused days carry over to the next year and are lost on 30 September.
A manager can grant a day off for overtime."

```markdown
## Value — LEAVE_DAYS (day; canonically half a day = 0.5 → unit: half a day, integers)
## Accounts
| employee_leave_current | assets | half a day | block | current year pool |
| employee_leave_carried | assets | half a day | block | carried over from the previous year |
| employee_leave_overtime | assets | half a day | block | days for overtime |
| company_allocation | pool | half a day | allow | the counter side of allocations |
| leave_used | expenses | half a day | allow | analytics |
| leave_lost | expenses | half a day | allow | expiry analytics |
## Transactions: annual_allocation (1 January, system; irreversible — a correction with a separate transaction) ·
   carry_over_to_new_year (31 December: current → carried, valid_to 30.09) · day_for_overtime (manager; reversible until
   used) · usage (approved request; reversible when the leave is cancelled) · expiry (30.09, system; irreversible)
## Allocation — 1. carried (expires earliest) 2. overtime (A: "overtime first or current?" — It depends → parameter
   `source_order` from the HR policy) 3. current
## Decisions — half a day as the minimum (X → asked, A) · balance never < 0 (R?: missing → A) · cancelling leave after its date (X → hot spot)
```
