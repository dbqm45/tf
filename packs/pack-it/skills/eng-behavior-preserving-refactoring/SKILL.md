---
name: eng-behavior-preserving-refactoring
description: Use for refactoring without changing behaviour (legacy, another paradigm) — a frozen contract, equivalence.
metadata:
  review: "2027-10-09"
  catalog: "Use for refactoring that changes the shape or idiom of code without changing behaviour (legacy, extracting the domain core, a paradigm change, e.g. a rich aggregate → a decider) — a frozen contract, four-layer tests, switching the test level, an assertion register, proof of preserved behaviour. Not for small refactorings (eng-clean-code) or designing test cases (qa-test-design)."
  keywords: "poprawka w starym module, naprawić błąd w legacy, nie zepsuć innych systemów, chronione zachowania, kontrakt zmiany, refaktoryzacja legacy, fix in an old module, fix a bug in legacy, do not break other systems, protected behaviours, change contract, legacy refactoring"
---

# Refactoring with proof of preserved behaviour

Goal: change **how** the code works without changing **what** it does. Proof: **the same, unchanged scenarios** pass before and after
the change, run at a level independent of the idiom being changed.

## Precondition
Tests exist and are green (that is the reference point). Red → stop. No tests → first characterization tests
(qa-spec-first-testing — marked as such), only then the refactoring. You add a characterization test where
the behaviour is visible without editing the protected code (a seam: a public function, a facade, a database query), and in this order:
first a test of the existing path, then the edit. Choosing WHAT to refactor and by which path: eng-refactor-planning.

## What we freeze (the behaviour contract — `docs/project/06-delivery/<step>-behavior-contract.md`)
1. **Scenarios and assertions** in the domain language.
2. **The public contract:** operation signatures, returned events and DTOs, **the kind of rejection** — an exception, an empty result and a result
   with an error are DIFFERENT behaviours.
3. **The consistency boundary:** what is loaded and saved atomically, where the locks/versions are.
Every change to any of these three requires a human's explicit consent and an entry in `decisions.md` — that is no longer refactoring.
A change in legacy that **should** change behaviour (a fix, a small feature) while the rest stays: a change contract
(the condition, the result, protected behaviours with a decision, the file scope, proof of the fix and of no regression) —
`references/change-contract.md`.

## Tests in four layers
| Layer | Does it change during refactoring? | Role |
|---|---|---|
| **Scenario** (given/when/then) | no | behaviour in the domain language |
| **DSL** (domain verbs, observable facts) | no | the test's vocabulary — without implementation types |
| **Driver** | yes | translates the DSL into system calls at the chosen level |
| **System** (SUT) | yes | the code being changed |
Driver binding levels: **domain** (the fastest, dependent on the idiom — does not prove equivalence) · **application** (a facade /
a use case — contractual, independent of the idiom; **you prove at this level**) · **system** (HTTP/queue — optional).
Rules: a driver without assertions; the driver choice in one place (the scenario's base class/fixture); a scenario does not create
implementation types and does not look into database tables; the driver binds to an **existing** facade — do not invent a new one.

## Steps (a separate commit for every step that changes code — core-git-workflow; do not squash)
1. **Lift** — rewrite the existing tests into scenarios + DSL and run them through the application driver. You change only tests
   (`test(scope): …`). Record every rewritten assertion in the **assertion register**:
   | Original assertion | Assertion in the DSL | What it no longer distinguishes | Why that is acceptable |
   Agreement between the domain and application drivers on the same scenarios checks the fidelity of the rewrite.
2. **Swap** — the new idiom next to the old one, the facade switched to the new code. A red test = the safety net worked: you fix the code
   or the wiring, **never the test**. It cannot be made green without editing the test → go back to the state after step 1 (git) and report.
3. **Lower** — the domain driver switched to the new core (the fast tests come back), remove the old code.

## Pitfalls
- **Implicit persistence** (an ORM saving changed entities by itself): after moving to immutable state the save disappears — the shell must
  save explicitly. Check every save path.
- **A hidden defect:** if the new implementation fixes a bug along the way (e.g. an added save) — name it and report it per the
  discrepancy protocol (qa-spec-first-testing); it is a behaviour change.
- Changing the kind of rejection (exception → empty result) "because it is nicer" breaks the contract.
- Characterization tests also lock in bugs — do not treat them as a specification.
- **A round-trip test does not protect a positional write:** when the write is positional (an array of columns, arguments) and the read is by
  name, a "write → read → compare" test stays green with swapped columns, and comparing types per
  index lets through a swap of adjacent fields of the same type. Use **sentinel values**: every field gets
  a unique value, the write goes through the production path, the read through a raw query by name, an assertion per name
  (`references/examples.md`, example 4).
- **The mechanism green, enforcement separately:** a new validation or guard comes in turned off (or in warning
  mode); turning it on is a separate, reversible commit (e.g. per layer, with a list of exceptions with a justification).

## Modes
- **Economical** (default): proof only on covered paths; coverage gaps listed in the summary as a caveat.
- **Strict** (critical logic): additionally a mutation testing threshold on the changed module and a characterization snapshot before/after.

## Summary (in the step report)
what was frozen · the assertion register · the step commits · coverage gaps · hidden defects found · consents to contract changes.
The catalogue of idioms and transition recipes: `references/idioms.md`.

## Example
**Situation:** the aggregate `Reservation` (the ORM saves by itself) is to become a decider; 14 domain tests green.
**Result:** the contract freezes the scenarios, `confirm(id, at)`, the event `ReservationConfirmed` without new fields
and the exception `ReservationExpired`. Commits: (1) `test:` scenarios + DSL through the facade, the assertion register
(`getStatus() === CONFIRMED` → `thenReservationIsConfirmed()`, does not distinguish the enum — the status is visible in the DTO);
(2) `refactor:` `decide(state, command)` next to the old code, the shell saves explicitly; (3) the domain driver on
`decide`, the old aggregate removed. Gap: cancellation without a test (economical mode).
More examples: `references/examples.md`.

## Sources
- The 10xDevs course, ed. 3 (2026), module 4, lessons 3–4 (seams and characterization tests, positional write and a guard,
  rewriting with ast-grep) — training material (accessed 2026-10-09); described in our own words.
- M. Feathers, *Working Effectively with Legacy Code* (2004) — seams and characterization tests.
