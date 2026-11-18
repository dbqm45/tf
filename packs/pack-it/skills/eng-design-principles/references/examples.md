# Examples of design principles

## 1. A review for excess (YAGNI, the minimalism ladder)
**Situation:** "Review the PR adding report export to CSV". The PR has 140 lines: a `ReportExporter` interface,
an `ExporterFactory` factory, a `CsvReportExporter` class and its own date formatting function.

**How:**
1. **The minimalism ladder:** is there a requirement *now*? Yes, but only CSV — a second format is not planned.
2. **YAGNI:** an interface with one implementation and a factory of one product are forbidden without a second case.
3. The "standard library" rung: `Intl.DateTimeFormat` does the date formatting.
4. Boundary: you do **not** simplify the input data validation and the write error handling.
5. Comments in the one-line format, the balance at the end; correctness assessed separately.

**Result:**
```text
L12: yagni interface ReportExporter (1 implementation, no plan for a second) → function exportCsv(rows)
L31: remove ExporterFactory → a direct call to exportCsv
L58: stdlib own formatDate() → Intl.DateTimeFormat("pl-PL")
L77: shorten manual comma joining → one escapeCsvField function used in map/join
Balance: −96 / +18 lines. Row validation (L90–L104) stays — trust boundary.
```
After the change:
```ts
const dateFormat = new Intl.DateTimeFormat("pl-PL");

function escapeCsvField(value: string): string {
  return /[",\n]/.test(value) ? `"${value.replaceAll('"', '""')}"` : value;
}

export function exportCsv(rows: { client: string; total: number; issuedAt: Date }[]): string {
  const lines = rows.map((r) => [r.client, r.total.toFixed(2), dateFormat.format(r.issuedAt)].map(escapeCsvField).join(","));
  return ["client,total,issuedAt", ...lines].join("\n");
}
```

## 2. DRY or KISS — two similar fragments
**Situation:** "The PR has two pairs of similar code. Should we extract shared functions?" Pair A: validation of the length of the product name
and the category name (both `1..80` characters). Pair B: a 10% discount from 500 PLN computed in the cart (frontend) and in the order service.

**How:**
1. The DRY check question: *the same business knowledge* or accidentally similar code?
2. Pair A — accidental similarity (the limits can drift apart independently): **KISS/YAGNI > DRY**.
3. Pair B — one pricing rule in two places: **DRY > KISS** for business knowledge.
4. **AHA / rule of three:** no third case for A, so no abstraction with flags.

**Result — the decision:**

| Pair | Decision | Justification (principle + cost) |
|---|---|---|
| A: name lengths | keep the duplicate | KISS: a shared function with a "field type" parameter is a wrong abstraction; duplication is cheaper |
| B: a 10% discount from 500 PLN | one source: `pricing.discountFor(total)`, the frontend fetches the result from the API | DRY: a rule in two places will drift apart at the first change of the threshold |

## 3. Tell, don't ask and the Law of Demeter
**Situation:** "Review the method for withdrawing from an account".
```ts
// before
type Balance = { getAmount(): number; setAmount(v: number): void };
type Account = { getBalance(): Balance };
declare const account: Account;
declare const amount: number;

if (account.getBalance().getAmount() >= amount) {
  account.getBalance().setAmount(account.getBalance().getAmount() - amount);
}
```

**How:**
1. **Law of Demeter:** `account.getBalance().getAmount()` — talking to a stranger object.
2. **Tell, don't ask:** the account itself can make the decision about a sufficient balance.
3. **Fail fast:** signal insufficient funds at once, not by silently skipping the withdrawal.
4. Getters for reading (a statement, presentation) stay — the rule does not tell you to remove all of them.

**Result:**
```ts
class InsufficientFunds extends Error {}

export class BankAccount {
  constructor(private balance: number) {}

  withdraw(amount: number): void {
    if (amount > this.balance) throw new InsufficientFunds(`Insufficient funds: ${amount} > ${this.balance}`);
    this.balance -= amount;
  }

  get currentBalance(): number {
    return this.balance; // a query for presentation — fine
  }
}
```
Review comment: "Demeter + tell, don't ask: the balance rule is outside the account, so every caller can skip it →
`account.withdraw(amount)`".
