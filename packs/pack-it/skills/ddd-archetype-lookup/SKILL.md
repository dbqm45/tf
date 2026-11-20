---
name: ddd-archetype-lookup
description: Use when existing code should be searched for places where a business archetype applies — money, balances, parties, bookings, prices, addresses.
argument-hint: "[path] [--include-tests]"
metadata:
  review: "2027-11-20"
  catalog: "Use when an existing repository or module should be checked for places where a business archetype (ddd-archetypes) would fix or simplify the model — a deterministic scan of code signals (money in float or double, currency as a free string, a balance or points column updated in place, role flags such as isSupplier, hand-written interval overlap checks and booking flags, waiting order by creation time, hard-coded discount rates, loose address columns, branches on a product type literal) and of domain vocabulary per archetype, then a fit verdict per candidate read in the code (apply, already modelled, not a fit, ask), a ranking with an order of change and a report in docs/project/02-domain/archetypes/. Not for modelling one requirement or area with an archetype (ddd-archetypes), mapping unfamiliar code in general (eng-codebase-mapping), a technical debt audit (eng-tech-debt-audit), a multi-dimension code audit (eng-code-audit), model↔code divergences of a known domain (ddd-legacy-modernization) or reviewing one pull request (qa-change-review)."
  keywords: "gdzie użyć archetypu, gdzie w projekcie pasuje archetyp, przeszukaj projekt pod kątem archetypów, archetypy w istniejącym kodzie, wyszukaj archetypy, sprawdź kod pod kątem archetypów, zapachy modelu domeny, pieniądze we float, kwota jako double, waluta jako string, saldo aktualizowane w miejscu, punkty w kolumnie, flagi isCustomer isSupplier, ręczne sprawdzanie nakładania rezerwacji, kolejka po dacie utworzenia, rabat zaszyty w kodzie, adres w kolumnach, if na typie produktu, które moduły przerobić na archetypy, archetype lookup, find archetypes in the code, where can we use an archetype, scan the project for archetypes, archetype opportunities, archetype smells in existing code, float money in the codebase, balance updated in place, role flags, hand-written overlap check, hard-coded discount, address columns, primitive obsession in the domain"
---

# Archetype lookup — where in this code would an archetype help?

A business archetype (the catalogue in ddd-archetypes) pays off where the code already fights the problem it solves:
money in `double`, a balance column updated in place, a company with `isSupplier` and `isCustomer`, a hand-written
overlap check. This skill finds such places in **existing** code, judges each one in the code and ranks them. It does
not design the new model — that is ddd-archetypes, one candidate at a time.

Script: `python3 .claude/skills/ddd-archetype-lookup/scripts/archetype_scan.py` (`py` on Windows). Standard library
only, no network, reads only. Run it, do not read it. It returns **candidates**, never verdicts: a regex cannot tell a
`Money` value object from a loose `amount: number`.

## Procedure
1. **Scope.** The path from the argument, otherwise the repository root. Large repository (>2,000 code files) → scan
   the domain modules first (`--root src/orders`), not generated or vendored code.
2. **Scan.** `archetype_scan.py --root <path>` (`--json` when you need every finding, `--include-tests` only on request).
   - First line `Archetype scan: <n> code files, <m> findings, <k> archetypes`, then one section per archetype:
     signal → remedy, evidence `file:line`, then vocabulary files (files using the archetype's words).
   - Exit 1 with 0 code files → say there is no code in scope, ask for the right path (without a human: stop with
     `Archetype lookup: 0 candidates — no code in scope`). Exit 1 with code → step 4 on vocabulary alone is pointless;
     report "no archetype signals" and what was scanned.
3. **Verdict per signal, read in the code.** For each archetype with findings open 2–3 evidence lines with their context
   (Read with a line range) and answer the archetype's signal question from the router table in
   `.claude/skills/ddd-archetypes/SKILL.md`. One verdict per candidate:
   - **apply** — the smell is real and the signal question says yes; name the concrete risk (rounding drift, lost history, double booking);
   - **already modelled** — the code has the model (a `Money` type, an entry table, a hold with a database guard); cite it;
   - **not a fit** — the match is technical or local (a cart line quantity, a retry queue ordered by time); one-line reason;
   - **ask** — only the business can say (is the order by time a fairness rule or an accident?).
4. **Vocabulary-only archetypes.** Open the top file of each. Keep it as an **opportunity** only when the code shows the
   problem shape (a number with a history, a price from rules, a resource held for an interval) and no model for it;
   otherwise drop it. Never report an archetype you did not see in a file.
5. **Rank.** Order by risk of the current code × reach (files touched) ÷ effort (S/M/L). Money and ledgers usually first —
   errors there are silent and costly; party roles last — the widest migration. Archetypes compose (money under prices and
   ledgers): say which change unblocks which.
6. **Write** `docs/project/02-domain/archetypes/lookup-<YYYY-MM-DD>.md` (or the project's domain folder). An existing file →
   ask: overwrite, save as `-v2`, or abort; without a human → `-v2`.
7. **Hand over.** End with the next step for the top candidate: `/ddd-archetypes <archetype> <area>` (models it from the
   requirements); a migration of existing data → eng-refactor-planning. Do not start either yourself.

### Result format
```
Archetype lookup: <n> candidates (<a> apply, <m> already modelled, <x> not a fit, <q> ask) | scope: <path>
## Candidates
| # | Area | Evidence | Archetype | Verdict | Why (risk now) | Effort |
## Order of change     numbered, with what each step unblocks
## Questions for the business     only the "ask" verdicts
## Not examined        skipped paths, tests (unless --include-tests), languages without signals
```
Scanner details (signal ids, counts) stay in the report's appendix, not in the summary for the human.

## Example
Input: `/ddd-archetype-lookup src` in a Django shop. Scan: `412 code files, 23 findings, 5 archetypes`.

Output (shortened):
- `Archetype lookup: 6 candidates (3 apply, 1 already modelled, 1 not a fit, 1 ask) | scope: src`
- 1 · giftcards/gateway.py:257 `card.balance_amount -= charged` · value ledger · **apply** — no entry history; a refund
  or a double callback cannot be explained or reversed · M.
- 2 · orders/api.py:88 `amount: float` + `currency: str` · quantity and money · **apply** — float at the API edge,
  rounding differs from the `Decimal` in the model · S.
- 3 · checkout/pricing.py:41 `total * 0.92` · price calculation · **apply** — a promotion only a deploy can change · M.
- 4 · prices/money.py · quantity and money · **already modelled** — `Money(Decimal, currency)` exists; item 2 should use it.
- 5 · warehouse/allocate.py:329 `available_in_stock -= reserved` · value ledger · **not a fit** — a local calculation, not a stored balance.
- 6 · waitlist/tasks.py:30 `.order_by("created_at")` · waiting list · **ask** — do regular customers go first?
- Order: 2 (reuses item 4, unblocks 3) → 3 → 1 (needs opening entries for existing cards).
- Next: `/ddd-archetypes value-ledger gift cards`.

## Sources
- M. Fowler, *Analysis Patterns: Reusable Object Models* (Addison-Wesley, 1997): ch. 2 Accountability (party,
  organization hierarchies, accountability), ch. 3 Observations and Measurements (quantity, conversion ratio), ch. 5
  Referring to Objects (object merge — one real party recorded twice), ch. 6 Inventory and Accounting (account,
  transactions, posting rules), ch. 8 Planning, ch. 9 Trading (contract, quote), § 15.3 Historic Mapping (values valid
  in time).
- M. Fowler, *Patterns of Enterprise Application Architecture* (Addison-Wesley, 2002) — the Money pattern: never a
  floating-point type for money.
- M. Fowler, *Refactoring*, 2nd ed. (Addison-Wesley, 2018), ch. 3 — the smells behind the signals: primitive obsession
  (float money, currency string), data clumps (address columns), repeated switches (type branches).
- J. Arlow, I. Neustadt, *Enterprise Patterns and MDA: Building Better Software with Archetype Patterns and UML*
  (Addison-Wesley, 2003) — the term "archetype pattern"; D. C. Hay, *Data Model Patterns* (Dorset House, 1996).
- ISO 4217 currency codes and minor units (iso.org, accessed 2026-11-20).

Described in our own words; the signals and the scanner are the factory's own.
