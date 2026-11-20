# Examples of clean code

> **Contents:** 1. A function with a flag and `null` as a meaning · 2. A long `switch` on type · 3. A swallowed exception and `None` as an error

## 1. A function with a flag and `null` as a meaning
**Situation:** "Review `process()` — it is hard to read, and the tests pass".

**How:**
1. **Names:** `process` and `data` say nothing → a name from the domain language (`blockResource`).
2. **A flag parameter** `notify: boolean` → two functions (the command without and with a notification).
3. **`null` as a meaning** ("no owner = the system") → a separate function instead of `null` in the argument.
4. **An early return** instead of nesting.
5. Each step separately, tests green after each, a `refactor:` commit.

**Result:**
```ts
// before
declare const repo: { find(id: string): { blocked: boolean; by: string } | undefined; save(r: { blocked: boolean; by: string }): void };
declare function sendMail(to: string): void;

export function process(data: string, owner: string | null, notify: boolean): boolean {
  const r = repo.find(data);
  if (r) {
    if (!r.blocked) {
      r.blocked = true;
      r.by = owner === null ? "system" : owner;
      repo.save(r);
      if (notify) sendMail(r.by);
      return true;
    }
  }
  return false;
}
```
```ts
// after
type Resource = { blocked: boolean; by: string };
declare const resources: { find(id: string): Resource | undefined; save(r: Resource): void };
declare function sendMail(to: string): void;

export function blockResource(resourceId: string, ownerId: string): boolean {
  const resource = resources.find(resourceId);
  if (!resource || resource.blocked) return false;
  resources.save({ ...resource, blocked: true, by: ownerId });
  return true;
}

export function blockResourceBySystem(resourceId: string): boolean {
  return blockResource(resourceId, "system");
}

export function blockResourceAndNotify(resourceId: string, ownerId: string): boolean {
  const blocked = blockResource(resourceId, ownerId);
  if (blocked) sendMail(ownerId);
  return blocked;
}
```
Review note: the returned `boolean` stays, because `refactor:` does not change behaviour. I propose replacing `false` with an operation
result or an exception (separating the command from the query — CQS) in a separate PR after agreeing it with the callers.

## 2. A long `switch` on type
**Situation:** "The linter reports `complexity` 12 in `shipping_cost()`. The same `if` on the shipment type is also in two
other files".

**How:**
1. Cyclomatic complexity 12 > about 10 (McCabe's threshold) → split it.
2. The smell "`switch` on type in many places" → a policy/variants: one price table in one place.
3. An amount as a `float` is **primitive obsession** → grosze (PLN cents) in an `int` with the unit in the name.
4. Characterization tests before the change, then the steps: extract the table → replace the three places of use → remove the old branches.

**Result** (complexity 12 → 2; a new shipment type = a new row, without editing the function):
```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Tariff:
    base_grosze: int
    per_kg_grosze: int


TARIFFS: dict[str, Tariff] = {
    "letter": Tariff(base_grosze=500, per_kg_grosze=0),
    "parcel": Tariff(base_grosze=1200, per_kg_grosze=150),
    "pallet": Tariff(base_grosze=9000, per_kg_grosze=40),
}


def shipping_cost_grosze(kind: str, weight_kg: int) -> int:
    tariff = TARIFFS.get(kind)
    if tariff is None:
        raise ValueError(f"Unknown shipment type: {kind!r}. Allowed: {', '.join(TARIFFS)}")
    return tariff.base_grosze + tariff.per_kg_grosze * weight_kg
```

## 3. A swallowed exception and `None` as an error
**Situation:** "Importing the price list sometimes silently gives an empty result. Fix the error handling".

**How:**
1. **Errors:** `except Exception: return None` swallows the cause, and `None` pretends to be an error → an operation result.
2. The message says what happened and what to do, without sensitive data (without the whole line of the file).
3. **Comments:** the commented-out old parser removed (it is in the git history), only the *why* stays.

**Result:**
```python
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True)
class Parsed:
    prices: dict[str, Decimal]


@dataclass(frozen=True)
class ParseError:
    line_no: int
    message: str


def parse_price_list(lines: list[str]) -> Parsed | ParseError:
    prices: dict[str, Decimal] = {}
    for line_no, line in enumerate(lines, start=1):
        sku, _, raw = line.partition(";")
        try:
            prices[sku] = Decimal(raw)
        except InvalidOperation:
            # the supplier sends a decimal comma only in old files — we do not guess, we ask for a correct export
            return ParseError(line_no, f"Line {line_no}: the price is not a number. Export the price list with a decimal point.")
    return Parsed(prices)
```
