---
name: qa-formal-methods
description: Use for formal verification — when it pays off, Z3, TLA+/TLC, Alloy, a counterexample as an AC-n test, model limits.
metadata:
  review: "2027-11-15"
  catalog: "Use when examples and random generation are not enough as an oracle — concurrency and retries, protocols and state machines, combinatorial rules with a limit; choosing the rung (contracts, property tests, the Z3 SMT solver, TLA+/TLC or Alloy model checking, Dafny), a counterexample as an acceptance test with AC-n, model limits in the report, the model next to the code. Not for designing aggregates and their invariants (ddd-tactical-design) or Hypothesis syntax (tool-pytest)."
  keywords: "weryfikacja formalna, metody formalne, zweryfikować formalnie, TLA+, PlusCal, TLC, Alloy, Z3, solver SMT, model checking, udowodnić, że żadna kombinacja, wyścig przy rezerwacji, podwójna rezerwacja, protokół synchronizacji, kontrprzykład, poprawność protokołu, projekt protokołu, przeploty, blokada optymistyczna, ponowienie po timeoucie, formal verification, formal methods, verify formally, SMT solver, prove that no combination, race on booking, double booking, synchronization protocol, counterexample, protocol correctness, protocol design, interleavings, optimistic locking, retry after timeout"
---

# Formal methods as an oracle

Concurrency and retries, protocols and state machines, combinatorial rules with a limit: the oracle is a solver
(Z3) or a model checker (TLA+/TLC, Alloy), not random generation. Not a whole module — 1–3 properties with the highest cost of failure.

## Procedure
0. **The cheapest rung that expresses the property:** contracts and assertions → property tests (Hypothesis, fast-check)
   → the Z3 solver → model checking (TLA+/TLC, Alloy) → Dafny. Go higher only when the lower one cannot express the property
   or does not hit the threshold or interleaving. A team without experience starts with property tests and Z3.
1. A property with an `AC-n` criterion; the model only from the state and steps that concern it; the tool looks for the negation.
2. **A counterexample → an acceptance test with `AC-n`** (red before the fix, visible in `tf trace`); the fix first
   in the model, then in the code.
3. You report "no counterexample" **with the model limits** (number of processes, number range, depth) — it is not proof
   for production. Amounts in grosze or with rounding as in the code.
4. The model in the repository next to the code; a protocol change without a model change is a finding in review.

## Example
Three models that were run, with results: `references/formal-methods.md`.
- **Z3, discount rules:** `sat` → a cart of PLN 0.50 with a PLN 20 loyalty discount gives a negative price; with the limit in the code `unsat`.
- **TLA+/TLC, a retry after a lost response:** a trace of 6 states ends with two reservations for one client;
  with an idempotency key no violation in 382 states (2 clients, 3 seats, 1 retry).
- **Alloy, permissions through nested groups:** a subgroup of another tenant gives access to someone else's invoice; with a rule
  for subgroups `UNSAT` in scope 4.
Every counterexample has a ready `AC-n` test and a report with the model limits.

## Sources
- Z3 (`z3-solver` 4.15.4), TLA+ (`tla2tools.jar` from release v1.8.0, TLC rev bc1b506), Alloy 6.2.0 — examples
  run 2026-11-15; versions and commands in `references/formal-methods.md` §Sources.
Described in our own words.
