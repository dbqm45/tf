# Examples of refactoring with proof of preserved behaviour

> **Contents:** 1. Rich aggregate → decider · 2. Legacy without tests and a hidden defect · 3. A red test after switching the facade · 4. Coupled column arrays — a guard instead of a rebuild

> **Table of contents:** 1. Rich aggregate → decider · 2. Legacy without tests and a hidden defect · 3. A red test after switching the facade · 4. Coupled column arrays — a guard instead of a rebuild

## 1. Rich aggregate → decider
**Situation:** "Rewrite the aggregate `Reservation` as a decider so the rules can be tested without a database. The behaviour must stay
the same." The domain tests (14) are green, the ORM saves changed entities by itself.

**How:**
1. **Precondition:** 14 tests green — that is the reference point.
2. **The contract** in `docs/project/06-delivery/03-behavior-contract.md`: the scenarios, the signature
   `ReservationService.confirm(id, at)`, the event `ReservationConfirmed` without new fields, **the kind of rejection** (the exception
   `ReservationExpired`), the consistency boundary: one aggregate per transaction, the `version` field.
3. **Lift** (`test(reservation): …`): scenarios + DSL, an application driver calling the existing facade;
   the assertion register for every rewritten assertion.
4. **Swap** (`refactor(reservation): …`): `decide` next to the old aggregate, the shell *load → decide → save explicitly →
   publish* (the recipe from `idioms.md`), the facade switched.
5. **Lower:** the domain driver on `decide`, the old aggregate removed.

**Result** — the core after the change (rejection conditions moved verbatim, time as a command parameter):
```ts
type State = { readonly id: string; readonly status: "pending" | "confirmed"; readonly expiresAt: Date; readonly version: number };
type Confirm = { readonly kind: "confirm"; readonly at: Date };
type ReservationConfirmed = { readonly type: "ReservationConfirmed"; readonly reservationId: string; readonly at: Date };

class ReservationExpired extends Error {}

export function decide(state: State, cmd: Confirm): { state: State; events: ReservationConfirmed[] } {
  if (state.status === "confirmed") return { state, events: [] }; // as in the old aggregate: idempotent, without an event
  if (cmd.at > state.expiresAt) throw new ReservationExpired(state.id); // kind of rejection unchanged
  return {
    state: { ...state, status: "confirmed" },
    events: [{ type: "ReservationConfirmed", reservationId: state.id, at: cmd.at }],
  };
}
```
The assertion register (excerpt):

| Original assertion | Assertion in the DSL | What it no longer distinguishes | Why that is acceptable |
|---|---|---|---|
| `expect(res.getStatus()).toBe(Status.CONFIRMED)` | `thenReservationIsConfirmed()` | the internal enum | the status is visible through the facade in the DTO |

Summary: 3 commits (lift, swap, lower), a coverage gap — the cancellation path without a test (economical mode).

## 2. Legacy without tests and a hidden defect
**Situation:** "Clean up `late_fee()` — 60 lines of nested `if`, nobody knows what it does. There are no tests."

**How:**
1. **Precondition not met** → first characterization tests (qa-spec-first-testing), marked as such.
2. The contract: input `days_late`, `is_member`, result `int` in grosze, no exceptions for `days_late <= 0` (returns 0).
3. Refactoring into a table of thresholds; the characterization tests unchanged and green.
4. **The "hidden defect" pitfall:** for `days_late == 30` the old code returns the rate of the lower threshold (`<` instead of `<=`).
   You do not fix it silently — characterization tests also lock in bugs, so you report the discrepancy to a human.

**Result:**
```python
# after the change — identical behaviour, including the threshold of 30 (reported as a possible defect)
_RATES = [(7, 100), (30, 250)]  # (up to how many days, exclusive; grosze per day)
_MAX_RATE = 500


def late_fee(days_late: int, is_member: bool) -> int:
    if days_late <= 0:
        return 0
    rate = next((r for limit, r in _RATES if days_late < limit), _MAX_RATE)
    fee = days_late * rate
    return fee // 2 if is_member else fee
```
The entry in the summary: "hidden defect found: 30 days charged at the rate of 500 instead of 250 — preserved; decision in `decisions.md`".

## 3. A red test after switching the facade
**Situation:** after the "swap" step the scenario "a confirmed reservation blocks the time slot" is red.

**How:**
1. A red test = the safety net worked; you do **not** edit the test.
2. You check the **implicit persistence** pitfall: the old aggregate was saved by the ORM by itself, the new shell does not call `save`.
3. You fix the shell's wiring (an explicit save in the same transaction), the scenario goes back to green.
4. If it could not be made green without editing the test — `git` back to the state after the "lift" step and a report.

**Result** — a fix in the shell, not in the test:
```ts
interface Repo { load(id: string): Promise<State>; save(s: State, expectedVersion: number): Promise<void> }
interface Bus { publish(e: ReservationConfirmed[]): Promise<void> }
declare function inTransaction<T>(fn: () => Promise<T>): Promise<T>;

export async function confirm(repo: Repo, bus: Bus, id: string, at: Date): Promise<void> {
  const events = await inTransaction(async () => {
    const before = await repo.load(id);
    const { state, events } = decide(before, { kind: "confirm", at });
    await repo.save(state, before.version); // was missing: the ORM no longer saves the immutable state by itself
    return events;
  });
  await bus.publish(events);
}
```

## 4. Coupled column arrays — a guard instead of a rebuild
**Situation:** saving a post builds an INSERT from two arrays (column names and values) — 18 items whose order
must match in two functions; the read maps by name. `git log -L` shows that the shape was introduced deliberately
(a batch INSERT for import speed), and the history has no fix of the order. The decision (eng-refactor-planning):
the shape stays, a guard is added.
**Why a round-trip test is not enough:** swapping `channel_id` and `user_id` (both text) gives a record that after the read
"looks correct" in a test that compares the saved object with the one read back through the same (wrong) path.
**Result:** one commit `test(store): guard the column order of the post write`, the production code untouched.
```ts
// TS — sentinel values: every field unique, the read through raw SQL by column name
it("batch write puts every value into the column of the same name", async () => {
  const sentinel = Object.fromEntries(POST_COLUMNS.map((c, i) => [c, `${c}__s${i}`]));  // e.g. "user_id__s3"
  await store.saveMultiple([postFrom(sentinel)]);                                        // the production positional path
  const [row] = await db.query(`SELECT ${POST_COLUMNS.join(", ")} FROM posts WHERE id = $1`, [sentinel.id]);
  for (const c of POST_COLUMNS) expect(row[c]).toBe(sentinel[c]);                        // assertion per name
});
```
```java
// Java (JUnit 5) — the same for numeric fields: consecutive prime numbers instead of repeated values
@Test
void batchInsertPutsEachValueIntoColumnOfTheSameName() {
  Map<String, Object> sentinel = Sentinels.forColumns(PostColumns.ALL);  // a unique value per column
  store.saveMultiple(List.of(Posts.from(sentinel)));
  Map<String, Object> row = jdbc.queryForMap("SELECT * FROM posts WHERE id = ?", sentinel.get("id"));
  PostColumns.ALL.forEach(c -> assertEquals(sentinel.get(c), row.get(c), c));
}
```
Fields with constraints (an enum, a foreign key) get a valid but unique value from the allowed set; if two fields
must have the same value, the test describes that explicitly as an exception.
