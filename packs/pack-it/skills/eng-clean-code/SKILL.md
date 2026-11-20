---
name: eng-clean-code
description: Use when writing, reviewing or refactoring code for readability — names, functions, complexity limits, null as meaning, swallowed errors, smell-to-refactoring map.
metadata:
  review: "2027-10-09"
  catalog: "Use when you write, review or refactor code for readability in any language — names from the domain, short functions on one level of abstraction, flag parameters, cyclomatic complexity thresholds and their enforcement in a linter, null passed or returned as a meaning, comments that say why, error handling without swallowed exceptions or success after a failure, a map from code smells to small safe refactorings and the order of work (characterization tests first, structure changed apart from behaviour). Not for architectural principles (eng-design-principles) or the idioms of a specific language (lang-*)"
  keywords: "czysty kod, czytelność kodu, nazewnictwo, nazwa zmiennej, długa funkcja, za długa metoda, za dużo parametrów, parametr flaga, boolean w parametrze, złożoność cyklomatyczna, McCabe, eslint complexity, złożoność kognitywna, zagnieżdżone ify, ogromny switch, mnóstwo ifów, wczesny powrót, klauzula strażnicza, null jako znaczenie, zwraca null, przyjmuje null, null oznacza domyślny, Optional, strictNullChecks, Null Object, komentarze w kodzie, zakomentowany kod, połknięty wyjątek, połknięty błąd, pusty catch, błąd tylko zalogowany, sukces mimo błędu, zwraca ok mimo błędu, komunikat błędu, zapach kodu, code smell, obsesja typów prostych, martwy kod, duplikacja reguły, przegląd czytelności, clean code, readability, naming, long function, too many parameters, flag argument, cyclomatic complexity, cognitive complexity, nested ifs, guard clause, early return, null as meaning, returns null, null object, swallowed exception, empty catch, error only logged, success despite error, error message, code smell, primitive obsession, dead code, feature envy, shotgun surgery"
---

# Clean code — readable code and small safe steps

The goal is code that the next person (or agent) changes without fear. Every rule below exists to shorten the time
from "what does this do" to "I can change it safely". Judge a piece of code by that, not by counting rules.

## Procedure
1. **Read before judging.** Find the domain words (tickets, schema, UI labels) and the callers of the code.
2. **Name the problems** using the sections below; for each one say what it costs the reader.
3. **Check the safety net.** No tests around the code → write characterization tests first (pin today's
   behaviour, including the odd parts), then refactor. Without them you do not change structure.
4. **Small steps, green after each.** One refactoring at a time (rename, extract, move), tests after each.
5. **Commit structure separately from behaviour.** A refactoring goes into its own `refactor:` commit with no change of
   behaviour; the fix or feature follows in a separate commit. "Make the change easy, then make the easy change."
6. **Changes of an API shape** (a boolean result becomes a result type, null becomes an optional) go into a separate PR
   agreed with the callers.

## Names
- A name says what the thing is and, where it is not obvious, why it exists — in the domain's vocabulary
  (`overdueInvoices`, not `list2`).
- Noise words (`Manager`, `Helper`, `Util`, `Data`, `Info`, `Processor`) usually hide an unclear responsibility —
  ask what the class really decides.
- Booleans read as questions (`isExpired`, `hasAccess`); collections in plural; a unit in the name when the type does not
  carry it (`timeoutMs`, `priceMinor`).
- One concept, one word across the module (not `client`/`customer`/`buyer` for the same thing).

## Functions
- One function does one thing on one level of abstraction. About 30 lines is a prompt to look again, not a hard rule.
- At most ~3 parameters; more, or the same group travelling together → a parameter object or a value object.
- A boolean flag parameter (`render(doc, true)`) means two functions: `renderDraft(doc)`, `renderFinal(doc)`.
- Command/query separation: a function either changes state or returns information, not both.
- Prefer early returns (guard clauses) to deep nesting; the happy path reads top to bottom.

## Complexity
- Cyclomatic complexity = 1 + the number of decision points (`if`, `else if`, loops, `case`, `catch`, `&&`, `||`, `?:`).
- Split above about **10** — the threshold McCabe proposed in 1976 and still the common default for review.
  Each decision point is also one more test case to cover (qa-test-design).
- Remedies, cheapest first: guard clauses; extract a function per branch group; a lookup table or map instead of a
  long `switch` on data; polymorphism (or a strategy/policy object) when the same type switch repeats in several places.
- Enforce it in the linter, not in review comments:
  - ESLint core rule `complexity` — default maximum **20**; set it lower, e.g. `"complexity": ["error", 10]`;
  - SonarJS `cognitive-complexity` — default threshold 15 (it also punishes nesting);
  - Java: Checkstyle `CyclomaticComplexity`; Python: Ruff/flake8 `C901` (`max-complexity`).
  On an existing codebase start at today's maximum and lower the limit step by step, so CI is not red on day one.

## Null
- Do not use null to carry meaning ("no customer", "use the default", "not loaded yet"). Callers forget the check,
  and the meaning lives only in someone's head.
- Instead:
  - a separate function or overload for the "default" path (`priceFor(customer)` and `listPrice()`);
  - a Null Object / Special Case (`NoDiscount` with `apply(x) = x`) when callers would otherwise branch on null;
  - an empty collection instead of null for "nothing found";
  - an optional type (`Optional<T>`, `T | undefined` with the compiler checking it, `Option`) when absence is a real answer.
- Check null and undefined **once, at the boundary** (API input, database read, a third-party response) and keep the
  inside of the module null-free.
- TypeScript: `strict` (or at least `strictNullChecks`) in the TypeScript config. Java: `Optional` only as a return type,
  never as a field or parameter.

## Comments
- The code says *what*; a comment says *why*: a decision, a constraint, a workaround with a link to the issue or ADR.
- Delete commented-out code — git keeps the history.
- Document the contract of a public API: inputs, units, errors thrown, side effects.
- A comment explaining a confusing block is a hint to rename or extract instead.

## Errors
- **No swallowed errors.** An empty `catch`, a `catch` that only logs, or a `catch` that returns a default hides the failure
  from the caller, the user and monitoring.
- **Logging is not handling.** `catch → log → return success` is still a swallowed error: the log line is read later, if
  ever, while the caller already acted on a false "OK".
- An operation with a side effect (a write, a payment, a message sent, a file stored) must never report success after it
  failed. Either handle the failure for real (retry with a limit, compensation, a fallback that is correct for the
  business) or let it propagate: rethrow, return an error/result value, or map it to a 5xx at the HTTP boundary.
- Handle errors in one place per layer — typically a boundary or middleware that turns exceptions into a response and a
  log entry with context. Inner code throws or returns errors; it does not decide how the user sees them.
- Do not use null as an error signal; use an exception or a result type (`Result<T, E>`, `{ ok: false, error }`).
- Messages say what happened and what the reader can do, without sensitive data (no SQL, stack traces, tokens or
  personal data in what the user sees; details go to the log with a correlation id).
- This class of defect is in OWASP Top 10:2025 as **A10 Mishandling of Exceptional Conditions** — cite it in a review
  when "it is only a log level" is the argument.
- Finding the cause of an error that was already swallowed: eng-debugging.

## Smells → refactorings
| Smell | Refactoring |
|---|---|
| long function | extract functions, or a pipeline of named steps |
| the same business rule in several places | one place: a value object, a policy, a function |
| long parameter list, data clumps | parameter object |
| primitive obsession (money as float, ids as strings) | value object (money in minor units with currency) |
| the same type switch in many files | polymorphism, a strategy/policy, or a table |
| feature envy (a method uses another object's data) | move the method to the data |
| shotgun surgery (one change touches ten files) | gather the responsibility in one module |
| a status flag field steering behaviour | a state machine or separate concepts |
| a recurring structural problem | a design pattern, the lightest form first |
| dead code | delete it |

## Example
Review comment on a payment handler:

```ts
async function capture(orderId: string) {
  try { await psp.capture(orderId); }
  catch (e) { logger.info("capture failed", e); }
  return { status: "captured" };
}
```

Answer: this is a swallowed error — the client gets "captured" although no money moved, and the log line is not
handling (OWASP Top 10:2025 A10). Remove the `catch` here and let the payment error reach the HTTP middleware, which
returns 502 with "Payment could not be captured, try again or use another card" and logs the provider code with the
correlation id. If the caller must branch on failure, return `{ ok: false, reason: "declined" | "provider_down" }`
instead. Add a test with a failing provider first; do the change in its own commit.

More worked cases (flag + null split, type switch → table, parser with a result type): `references/examples.md`.

## Checklist
- [ ] names from the domain, no noise words, booleans as questions, units where the type is silent
- [ ] no flag parameters; ≤ ~3 parameters; early returns instead of nesting
- [ ] complexity ≤ ~10 per function, enforced by a linter rule
- [ ] no null carrying meaning; null checked once at the boundary; strict null checks on
- [ ] no swallowed errors, no success after a failed side effect; messages actionable and free of sensitive data
- [ ] characterization tests before structural changes; refactoring in a separate `refactor:` commit

## Sources
- OWASP Top 10:2025, A10 "Mishandling of Exceptional Conditions" (owasp.org/Top10, accessed 2026-10-09).
- ESLint rule `complexity`, default maximum 20 (eslint.org/docs/latest/rules/complexity, accessed 2026-10-09).
- SonarJS rule `cognitive-complexity`, default threshold 15 (github.com/SonarSource/SonarJS, accessed 2026-10-09).
- Checkstyle `CyclomaticComplexity` check (checkstyle.org, accessed 2026-10-09).
- T. J. McCabe, "A Complexity Measure", IEEE Transactions on Software Engineering, 1976 (threshold of about 10).
