---
name: ddd-legacy-modernization
description: Use for DDD on existing code — a glossary and model↔code divergences, an aggregate from an invariant, an ACL.
metadata:
  review: "2027-10-09"
  catalog: "Use when in working code (after the MVP, legacy) you must check whether it reflects the domain and plan a modernization — distilling a glossary from documents and code with a table of model↔code divergences, subdomains, aggregate candidates with the invariant's status; choosing an invariant (coreness × smearing × enforcement) and designing a guardian aggregate; detecting a leaking dependency and designing an ACL (a value object, a narrow port, an adapter) with a checkable criterion \"the package only in the adapter directory\" enforced by a dependency-cruiser / ESLint / ArchUnit rule. The result is diagnoses and plans, not production code. Not for a workshop with experts (ddd-facilitation, ddd-event-storming), designing a model from scratch (ddd-tactical-design), relationships between contexts (ddd-context-mapping) or refactoring the structure without changing the concepts (eng-refactor-planning)."
  keywords: "legacy DDD, DDD w istniejącym kodzie, modernizacja legacy, kod nie odpowiada domenie, destylacja domeny, słownik z kodu, rozjazd model kod, PRD a kod, to samo słowo znaczy kilka rzeczy, niezmiennik tylko w UI, reguła rozsmarowana, agregat strażnik, przeciekająca zależność, biblioteka wszędzie, typy biblioteki w API, ACL dla biblioteki, wymiana biblioteki, izolacja zależności, DDD in existing code, legacy modernization, code does not match the domain, domain distillation, glossary from code, model code divergence, PRD vs code, the same word means several things, invariant only in the UI, smeared rule, guardian aggregate, leaking dependency, library everywhere, library types in the API, ACL for a library, replacing a library, dependency isolation"
---

# DDD on existing code — distillation, invariant, ACL

Refactoring asks "how to change the code safely". This skill asks **"does the code match how the business works"**.
The product is three diagnoses with plans — not production code. You **do not assume** the names of entities, invariants or leaks
**up front**: you discover them from documents and code, quoting the `file:line` you actually checked.

## When (signals that the domain hurts)
- the same word means several things (three different "Account"s: a profile, a bank account, a ledger account);
- an entity from the PRD has no counterpart in the code or lives as a loose identifier next to rows;
- data regularly falls into an "impossible" state and a script rescues it;
- replacing one library is a sprint-long project.
Before product validation (MVP) it is usually too early — the knowledge of the domain is still shallow; you model when it hurts.

## Step 0 — context (shared by A–C)
The PRD, the stack decision, the README, the change history in `docs/project/`. No requirements documents → the README + the code, recorded
as a constraint. Establish where the logic lives (API / service / domain / UI / persistence) and the list of dependencies from the manifest.
A code map (eng-codebase-mapping) shortens this step.

## A. Domain distillation → `docs/project/02-domain/distillation.md`
1. **Glossary:** term · definition · source (the document's `file:line`) · where in the code (`file:line`) or
   **"BRAK w kodzie"** (missing in the code). All the names of the same entity (database, UI, API response, the team's speech) in one row.
2. **Subdomains** core / supporting / generic with a justification in the product goals (ddd-strategic-analysis).
3. **Aggregate candidates** + the invariant (a quote) + status: **enforced / declared / ignored**.
4. **Model ↔ code divergences** (the most valuable part): the document says X · the code does Y · evidence.
5. **Ranking:** value (how core the invariant is) × risk (how weakly it is enforced) → #1 for further work.
New glossary entries go into `glossary.md` as **proposals** for a human's acceptance (ddd-facilitation).

## B. Invariant → guardian aggregate → `docs/project/02-domain/invariant-<name>.md`
1. A list of "always true" rules from documents and code: "X arises only from Y", "A→B requires C", "Z is atomic",
   "D is never saved".
2. Three axes for each: **coreness** (the product goals) · **smearing** (how many files and layers) ·
   **enforcement** (enforced / declared / violable). Choose the most core and the most weakly
   enforced — often not the one you suspect.
3. **Diagnosis** with `file:line` in all layers: where the rule is missing, where it is inconsistent, where the UI is
   the only guardian, where an endpoint trusts the data from the request, where an error is logged and swallowed.
4. **Design** (ddd-tactical-design): the aggregate root as the **only** place of enforcement; methods with
   preconditions; an illegal operation throws a **named domain error** (fail-fast, not "log it and carry on");
   the repository loads and saves the whole; an invariant requiring atomicity → one transaction; a thin API route:
   parse the input → the aggregate method → map the error to a response; enforcement moves from the client to the server.
5. **Before/after** for every current place of the rule, phases (test-first, eng-behavior-preserving-refactoring),
   test cases of legal and illegal operations.

## C. A dependency leak → ACL → `docs/project/02-domain/acl-<package>.md`
1. **Leak signals:** the same package in the API + UI + service; library types in domain signatures or in DTOs
   and responses; the same conversion of a library object in several places; an SDK called on both sides of the
   client/server boundary. For each dependency: **all** the files that know it (`rg -l "from '<package>'"`,
   ast-grep for dynamic imports).
2. **Axes:** the number of layers and files · the cost of replacing it today · whether the documents declared replaceability. A divergence
   between intent and code ("it was meant to be replaceable") is the strongest signal. Choose the worst leak.
3. **Diagnosis:** duplicates, boundary leaks, especially **a server library in the client bundle**.
4. **Design:** a domain value object as the only place of knowledge about the dependency's shape (mapping from and to
   persistence, conversion from and to the library type) · **a narrow port** in the domain language · **an adapter** wrapping
   the library. The rest of the code knows only the port; the UI gets domain data, not the library object. Decisions that depend on
   the library's contract you settle from its documentation and encode in the ACL, not in the API.
5. **Proof of isolation:** a "knows today / knows after the refactor" list.
6. **Completion criterion (checkable with a command):** searching for the package name returns **only the files of the adapter
   directory**. You lock it in with a CI rule — dependency-cruiser `forbidden`, ESLint `no-restricted-imports`, ArchUnit;
   ready templates: `references/rule-templates.md`.

## Next
The A–C artifacts are the input for planning a step (core-plan-interview → a plan with phases). Hot spots from Event Storming
(ddd-event-storming) are candidates for the next steps. The cycle: discover → name the divergences → secure the invariant →
isolate the dependency → plan. Templates of the A–C documents: `references/document-templates.md`.

## Example
**Situation:** a flashcard app after the MVP; the PRD describes a "generation session" with a life cycle.
**Result:**
- A: in the code a session is only a loose identifier next to the proposal rows (the entity is MISSING); a proposal has four names
  in four layers. Divergence: the PRD says "a session is finalized after all proposals are resolved" — the code allows
  saving flashcards without resolving the rest (`src/api/flashcards.ts:41`).
- B: invariant #1 (core, guarded only by a counter in the UI) → the aggregate `GenerationSession` with `accept()`,
  `reject()`, `finalize()`; `finalize()` with an unresolved proposal throws `SessionHasUnresolvedProposals`;
  saving in one transaction; the API route only maps the error to 409.
- C: the `Card` type of the review scheduling library in the database schema, in the API response and in the component props
  (7 files, 3 layers; the PRD declared a replaceable algorithm) → the value object `ReviewSchedule`, the port `Scheduler`,
  the adapter `src/scheduling/adapter/`. Criterion: `rg -l "from 'ts-fsrs'"` returns only the adapter files; a
  `forbidden` rule in dependency-cruiser in CI.

## Checklist
- [ ] nothing assumed up front; every term with a quote and a status in the code (`file:line` or "BRAK w kodzie")
- [ ] a model ↔ code divergence table; glossary entries as proposals
- [ ] the choice of the invariant and the leak justified on the axes, with a diagnosis in all layers
- [ ] the design: the only place of enforcement, a named error, a transaction, a thin route; port + adapter + value object
- [ ] the ACL criterion checkable with a command and locked in with a rule; plans without production code

## Sources
- The 10xDevs course, ed. 3 (2026), module 4, lesson 5 (legacy modernization with DDD) and three prompts for it (distillation,
  invariant → aggregate, ACL) — training material (accessed 2026-10-09); described in our own words.
- E. Evans, *Domain-Driven Design* (2003) — aggregate, Anti-Corruption Layer, ubiquitous language.
- Rule syntax checked 2026-10-10: dependency-cruiser 18.5.0 (`forbidden` with `from.pathNot` / `to.path`),
  ESLint 9.39.1 (`no-restricted-imports` in the flat configuration with an exception for the adapter directory).
