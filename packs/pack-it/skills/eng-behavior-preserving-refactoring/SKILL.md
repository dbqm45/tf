---
name: eng-behavior-preserving-refactoring
description: Use when restructuring code or switching its idiom without changing behaviour, or fixing legacy that others rely on — frozen contract, test layers, proof.
metadata:
  review: "2027-10-09"
  catalog: "Use when existing code changes shape (legacy cleanup, extracting a domain core, mutable aggregate → pure decide function, mass rewrite of calls) and you must prove behaviour stayed the same, or when a bug fix or small feature in a legacy module must not break callers you cannot see — the frozen behaviour contract, scenario/DSL/driver test layers, an assertion register, step commits, sentinel values for positional writes, ast-grep rewrites with counts, the six-field change contract. Not for small local refactorings of one function (eng-clean-code) or choosing test cases (qa-test-design)."
  keywords: "refaktoryzacja bez zmiany zachowania, refaktoryzacja legacy, przepisać na inny idiom, agregat na decider, funkcyjny rdzeń, udowodnić że zachowanie się nie zmieniło, testy związane z implementacją, zamrozić kontrakt, kontrakt zmiany, chronione zachowania, nie zepsuć innych systemów, poprawka w starym module, legacy fix, zakres plików, testy charakteryzujące, rejestr asercji, sterownik testów, DSL testów, zapis pozycyjny, kolumny w złej kolejności, wartownicy, masowa zmiana wywołań, ast-grep, zapis znika po refaktoryzacji, refactor without changing behaviour, behaviour-preserving refactoring, legacy refactoring, change the idiom, aggregate to decider, prove behaviour unchanged, behaviour contract, change contract, protected behaviours, don't break other systems, characterization tests, assertion register, test driver, positional write, sentinel values, mass rewrite of calls"
---

# Refactoring that provably keeps behaviour

Refactoring changes shape, never behaviour. The work is mostly about proving that second part: decide what is frozen, make the tests
independent of the implementation you are replacing, change code in small committed steps, and report what the proof does not cover.
When the change is *meant* to alter behaviour in a legacy module (a fix, a small feature), use the change contract instead
(`references/change-contract.md`).

## Procedure
1. **Baseline.** Run the existing suite on the base commit.
   - Red baseline → stop. Ask the human to fix it or to accept the listed failures as the baseline; do not refactor on red.
   - No tests on the path you will touch → write characterization tests first (qa-spec-first-testing), labelled as such, at a seam
     you can reach without editing the protected code (a public function, a facade, a database query). They freeze today's behaviour
     *including its bugs*: they are a reference point, not a specification.
2. **Freeze the behaviour contract** — three items, written down before any code moves:
   - **scenarios and assertions** in domain language (what the system must still do);
   - **the public contract**: signatures, events and DTOs, and the **kind of rejection** — an exception, an empty result and an error
     value are three different behaviours, even when they carry the same reason;
   - **the consistency boundary**: what is loaded and saved atomically, version/lock fields.
   Any change to these three is no longer a refactoring. Stop, name the change, get the human's explicit consent and record it in
   `decisions.md`. The contract goes to `docs/project/06-delivery/<step>-behavior-contract.md`
   (template: `.claude/skills/core-project-record/templates/behavior-contract.md`).
3. **Separate tests from the implementation** — four test layers:

   | Layer | Contains | Changes during the refactoring? |
   |---|---|---|
   | scenario | given / when / then in domain words | never |
   | DSL | domain verbs and observable facts (`placeOrder`, `orderWasRejected`) | never |
   | driver | translates DSL calls into calls of the system | yes — this is what you swap |
   | system under test | the code | yes |

   Drivers bind at the **domain level** (fast, depends on the idiom, proves nothing about equivalence), at the **application level**
   (a facade or use case — idiom-independent, this is where the proof happens) and optionally at the system level (HTTP, queue).
   Rules: no assertions in drivers; the driver is chosen in one place (a base class or fixture); scenarios never construct
   implementation types or read tables; bind to a facade that already exists — inventing one changes the contract.
4. **Work in steps, one commit each, no squash** (`test(scope): …` for test-only steps, `refactor(scope): …` for code):
   1. **Rewrite the tests** into scenario + DSL run through the application driver. Only tests change. Log every rewritten assertion
      in the **assertion register**: original → DSL form → what it no longer distinguishes → why that is acceptable. The domain driver
      and the application driver must agree on every scenario — that validates the rewrite itself.
   2. **Switch the implementation**: build the new idiom beside the old one and point the facade at it. A red scenario means the safety
      net worked: fix the code or the wiring, **never the test**. If it cannot be fixed, revert to the state after step 1 and report.
   3. **Retire the old code**: point the domain driver at the new core, delete the old implementation.
5. **Watch for the known traps**:
   - **Implicit persistence disappears.** ORM dirty-tracking saved the mutable aggregate for free; immutable state does not. The shell
     must save explicitly on every path that saved before.
   - **A hidden defect fixed by accident** (e.g. the new explicit save now persists something that was silently lost) is a behaviour
     change: name it and report it through the discrepancy protocol (qa-spec-first-testing), do not keep it quietly.
   - **Positional writes** (values matched to columns or fields by order): a write → read → compare round trip passes even with two
     columns swapped. Use sentinel values (`references/examples.md`, example 4).
   - **New guards land switched off** (or in warning mode); enabling them is a separate, reversible commit — per layer, with a listed
     and justified exception list.
6. **Choose the mode.**
   - **Economical** (default): proof only on paths the tests cover; list coverage gaps as a caveat.
   - **Strict** (money, permissions, core domain rules): additionally a mutation-testing threshold on the changed module and a
     before/after snapshot of outputs on a recorded input set.
7. **Report**: the frozen items, the assertion register, the step commits, coverage gaps, hidden defects found, consents obtained.

## Changing the idiom
Catalogue of idioms (anemic model + service, mutable rich aggregate, decider, strict event-sourced decider) and the recipe
aggregate → decider: `references/idioms.md`. A change of idiom needs a stated reason (testability, separating decisions from effects,
preparing for event sourcing). The strict decider usually needs richer events — a contract change, so consent first.

## Mass structural rewrites
For changing the shape of a call in many files use the `ast-grep` binary (on Linux `sg` is the group-switching command, not ast-grep):
dry-run with `ast-grep run -p '<pattern>' -r '<rewrite>' -l <lang> <dir>` (prints a diff, writes nothing), then `-i`/`--interactive`
or `-U`/`--update-all`; a repeatable rewrite is a YAML rule with `fix`, run by `ast-grep scan`. Record the counts in the commit
message (source pattern N → 0, target pattern 0 → N) and confirm every zero with `rg`: an invalid pattern also matches zero.
Details: `references/idioms.md`, section "Structural rewriting".

## A fix in legacy that others depend on
When behaviour *should* change but neighbours must not break, describe the task with the six-field change contract
(`references/change-contract.md`): condition, observable expected result, **protected behaviours** (from callers and consumers,
incidents, hot files from `python3 .claude/skills/eng-codebase-mapping/scripts/git_territory.py --hotspots`, characterization tests),
**allowed file scope**, proof of the fix (a test red on the base commit, green after) and proof of no regression (protective tests
committed on the base commit before the change). Each protected behaviour has a decision and an owner; open items block the start.

## Example
Input: "Rewrite the `Subscription` aggregate (mutable, saved by the ORM) into a decider, and while you are at it make `pause()` on a
cancelled subscription return `null` instead of throwing `SubscriptionClosed`."

Result:
- Baseline: 41 tests green on `a1c9e02`. Contract frozen: 9 scenarios, the `SubscriptionPaused`/`SubscriptionResumed` events unchanged,
  rejection = exception `SubscriptionClosed`, atomic save of the subscription with its `version` field.
- The `null` request **changes the kind of rejection** — it is a behaviour change, not part of the refactoring. Asked the human; recorded
  as a separate later change in `decisions.md` (consumer `billing-worker` catches the exception).
- Step commits: `test(subscriptions): run scenarios through SubscriptionFacade` (register: 3 assertions on private fields replaced by
  `subscriptionIsPaused()`, they no longer distinguish `pausedAt` precision — acceptable, no consumer reads it) →
  `refactor(subscriptions): decide() core behind the facade` (2 scenarios red: the shell did not save after `resume`; added explicit
  save) → `refactor(subscriptions): remove the mutable aggregate`.
- Report: economical mode, gap — the renewal path has no scenario; hidden defect — none.

More cases (rejection kind, register, red after the switch, sentinel values, mass rewrite): `references/examples.md`.

## Neighbours
Choosing what and how to refactor: eng-refactor-planning. Finding callers: eng-codebase-mapping. Characterization tests and the
discrepancy protocol: qa-spec-first-testing. Small refactorings inside a function: eng-clean-code. Test case selection: qa-test-design.
Recording requirements that a change adds: proc-requirements-shaping. Commits and branches: core-git-workflow.

## Sources
- M. Feathers, *Working Effectively with Legacy Code*, Prentice Hall, 2004 — seams and characterization tests.
- ast-grep documentation, "Command Line Reference" and "Rewrite Code" (ast-grep.github.io, accessed 2026-10-10); behaviour
  checked on ast-grep 0.50.0 (own run, 2026-10-10).
