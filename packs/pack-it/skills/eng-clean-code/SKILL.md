---
name: eng-clean-code
description: Use for code readability — names, functions, comments, error handling, smells, small refactorings.
metadata:
  review: "2027-10-09"
  catalog: "Use when writing, reviewing and refactoring code in any language — naming, functions, comments, error handling, code smells and safe refactorings in small steps. Not for architectural principles (eng-design-principles) or the idioms of a specific language (lang-*)."
  keywords: "null jako znaczenie, zwracanie null, czytelność, nazwy zmiennych, długa funkcja, refaktoryzacja, Optional, Null Object, czysty kod, połknięty wyjątek, pusty catch, błąd tylko zalogowany, sukces mimo błędu, clean code, swallowed exception, empty catch, log and continue, null as meaning, returning null, readability, variable names, long function, refactoring, error only logged, success despite an error"
---

# Clean code and refactoring

## Names
- A name says **what and what for**, in the language of the domain (ubiquitous language): `blockResource`, not `process`, `handleData`, `doStuff`.
- No abbreviations and no noise (`Manager`, `Helper`, `Util`, `Data`, `Info`) — if only such a name fits, the responsibility is unclear.
- Booleans as questions (`isAvailable`, `hasRole`); collections in the plural; units in the name when the type does not carry them.

## Functions
- They do one thing at one level of abstraction; length is a signal, not a rule (> ~30 lines → check).
- Few parameters (≤ 3); more → a parameter object / a value object. No flag parameters (`save(true)`) → two functions.
- Separate commands (they change state) from queries (they return data) — CQS.
- An early return instead of deep nesting.
- **Cyclomatic complexity** (the number of independent paths: 1 + decision points `if`, loops, `case`, `&&`, `||`, `?:`):
  above about 10 per function (McCabe's threshold) — split it. Ways: guard clauses, extracting a function, a table or a map
  instead of a long `switch`, polymorphism instead of a `switch` on type repeated in many places. In the linter: the ESLint rule
  `complexity` (default threshold 20 — set it lower) or cognitive complexity from SonarJS (default 15), in Java Sonar
  or Checkstyle `CyclomaticComplexity`. The number of test cases grows together with the complexity (qa-test-design).
- **Do not pass `null`** as a meaning ("no customer", "use the default"): a separate function or an overload, an empty
  object (Null Object), an empty collection instead of `null`, an optional type. In TS `strict` (including `strictNullChecks`),
  `null`/`undefined` checked once at the boundary (API input, a database read), in Java `Optional` only as a return type.

## Comments
- The code says *what*, the comment *why* (a decision, a constraint, a link to an ADR/issue). We delete commented-out code.
- Document the public API (the contract, exceptions, units).

## Errors
- Do not swallow exceptions; do not return `null` as an error signal — an optional type or an operation result.
- An error message says what happened and what to do; without sensitive data.
- An error of an operation with a side effect (a write, a payment, a send) does not end with a success response; logging is not
  handling. `catch → log → return ok` is a **swallowed error** — the client thinks it succeeded (OWASP Top 10:2025, A10
  Mishandling of Exceptional Conditions; diagnosis: eng-debugging).

## Smells → refactorings (in small steps, tests green after each)
| Smell | Refactoring |
|---|---|
| long function | extract a function; replace a loop with a pipeline |
| a repeated business rule | move it to one place (a value object, a policy) |
| a long parameter list, data clumps | a parameter object / a value object |
| primitive obsession (an amount as a number) | a value object |
| `switch` on type in many places | polymorphism / variants / a policy |
| feature envy (a method uses another object's fields) | move the method |
| shotgun surgery (one change → many files) | gather the responsibility in one module |
| a state flag field | a state machine / separate concepts |
| a recurring structural problem (factories, variants, layers, notifications) | a design pattern — its lighter form first |
| dead code | delete it (the history is in git) |

## How to refactor
1. Characterization tests, if they are missing. 2. One step at a time. 3. The refactor in a separate commit (`refactor:`), without a change in behaviour.
4. First make the change easy, then make the easy change.

## Example
**Situation:** a review of `process(data, owner: string | null, notify: boolean)` — nested `if`s, `null` means "the system".
**Result:** a name from the domain `blockResource(resourceId, ownerId)`; the flag → a separate `blockResourceAndNotify`; `null` →
`blockResourceBySystem(resourceId)`; an early return instead of three levels of `if`. Each step separately, tests green,
a `refactor:` commit; you propose changing the returned `boolean` to an operation result (CQS) in a separate PR.
More examples: `references/examples.md`.

## Sources
- The 10xDevs course, ed. 3 (2026), module 3, lesson 5 (swallowed errors) — training material (accessed 2026-10-09).
- OWASP Top 10:2025, category A10 (the name as in arch-threat-modeling).
Described in our own words.
