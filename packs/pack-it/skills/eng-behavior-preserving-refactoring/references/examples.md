# Behaviour-preserving refactoring — worked cases


## 1. A "nicer" rejection is a contract change
Request: "While moving `Booking` to a decider, return `Result.empty()` instead of throwing `SlotTaken`."
- Today the caller sees an exception; afterwards it would see an empty value. Both carry "slot taken", but a caller that relies on
  `catch (SlotTaken)` now continues silently. The **kind of rejection** is part of the frozen public contract.
- Answer: do the idiom change with the exception kept; propose the new rejection form as a separate change, ask for consent,
  record it in `decisions.md` with the consumers that must adapt.

## 2. Rewriting tests and the assertion register
Starting point: 23 tests construct `Invoice` directly and assert on private fields. They would all break on the new idiom.
After the rewrite each test is a scenario using DSL verbs, run through the application driver (`InvoicingFacade`).

| Original assertion | DSL form | No longer distinguishes | Why acceptable |
|---|---|---|---|
| `assertEquals(Status.ISSUED, invoice.status)` | `invoiceIsIssued("F/7")` | internal enum vs derived state | consumers see only the issued fact |
| `assertEquals(3, invoice.lines.size())` | `invoiceHasLines("F/7", 3)` | — | identical |
| `verify(repo).save(invoice)` | `invoiceCanBeLoaded("F/7")` | how many times save ran | double save is not observable |

The same 23 scenarios run once with the domain driver (old aggregate) and once with the application driver; both green = the rewrite
kept the meaning. One commit: `test(invoicing): scenarios through InvoicingFacade`.

## 3. Red after switching the implementation
After `refactor(invoicing): decide() core behind the facade`, the scenario "a corrected invoice keeps its number" turns red.
- Do not touch the scenario. First suspect: **implicit persistence**. The old aggregate was mutated inside a unit of work and the ORM
  flushed it; the new shell returns a new state and nobody saves it on the correction path.
- Fix: explicit `repository.save(newState)` in the shell on that path, within the same transaction as before.
- If the cause cannot be found in reasonable time: `git revert` back to the state after the test rewrite and report what failed.

## 4. A positional write guarded by sentinel values
Situation: `export_settlement()` builds an `INSERT INTO settlement_rows (...) VALUES (...)` from two parallel lists — `COLUMNS`
(14 names) and `values` (14 values appended in a loop). Reports read the table by column name. The refactoring will replace the
lists with a dataclass.

Why a round trip is not enough: a test that writes a row, reads it back **through the same mapping** and compares objects stays green
when `gross_amount` and `net_amount` swap places, because both write and read are wrong in the same way. Comparing types per index
also misses it: both are decimals.

The guard:
1. Give every field a **unique sentinel value**: numbers as distinct primes (`net_amount=101.00`, `gross_amount=103.00`,
   `vat_amount=107.00`, `quantity=11`), free text as unique tokens (`"memo-S1"`), constrained fields as a valid but unique
   member (`currency="CHF"` where nothing else in the row could be CHF), dates on distinct days.
2. Write through the **production path** (`export_settlement()`), not through a test helper.
3. Read with a **raw query by column name** (`SELECT net_amount, gross_amount, ... FROM settlement_rows WHERE id = ?`).
4. Assert **per name**: `row["gross_amount"] == 103.00`. A deliberate equal pair (e.g. `created_by == updated_by` on insert) is
   documented as an exception in the test.
Commit the guard on the base commit as `test(settlement): sentinel values per column`, see it green, then refactor; a swapped
column now fails with the column name in the message.

## 5. A mass rewrite of calls with counts
Goal: `notify(user, msg)` → `notify(Notification(user, msg))` in about 80 files.
```bash
ast-grep run -p 'notify($U, $M)' -l python src/                  # count: 212 matches
ast-grep run -p 'notify($U, $M)' -r 'notify(Notification($U, $M))' -l python src/   # diff only
ast-grep run -p 'notify($U, $M)' -r 'notify(Notification($U, $M))' -l python -U src/
ast-grep run -p 'notify($U, $M)' -l python src/                  # 0
rg -n 'notify\([^N]' src/                                        # confirms the zero; also shows comments/strings
```
Commit message: `refactor(notifications): wrap notify arguments — notify($U, $M) 212 → 0, notify(Notification(...)) 0 → 212`.
`notify_all(` is not touched (ast-grep matches the identifier, not a prefix); hits that `rg` still shows in docstrings are reviewed by hand.

## 6. A red baseline
The suite on the base commit has 3 failures in the late-fee test file. Refactoring now would make it impossible to tell old failures from
new ones. Stop and ask: fix them first, or record them as the accepted baseline (names and messages) in the report. If `late_fee()`
has no tests at all, start with characterization tests; a quirk such as "a fee of exactly 30 days counts as late" is frozen as it is
and reported as a possible defect, not silently fixed.
