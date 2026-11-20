---
name: ddd-legacy-modernization
description: Use when working code no longer matches how the business works — language drift, a core rule guarded just by the UI, a library leaking through every layer.
metadata:
  review: "2027-11-20"
  catalog: "Use when checking whether existing code (post-MVP or legacy) reflects the domain and planning the fix without writing production code — three diagnoses: A language drift (a glossary with document and code locations, the BRAK w kodzie marker, subdomains, aggregate candidates, model ↔ code divergences, a ranking), B the most valuable, weakest-guarded rule moved into a guardian aggregate (named domain error, one transaction, a thin server route, before/after, legal and illegal sequences), C the leakiest dependency isolated behind an anti-corruption layer (value object, port, adapter) with a completion check by rg and a CI rule. Not for expert workshops (ddd-facilitation, ddd-event-storming), modelling from scratch (ddd-tactical-design), relations between contexts (ddd-context-mapping) or purely structural refactoring (eng-refactor-planning)."
  keywords: "legacy, stary kod, modernizacja legacy, kod nie odwzorowuje domeny, kod rozjechał się z biznesem, słowo znaczy trzy rzeczy, pojęcia z PRD nie mają odpowiednika w kodzie, rozjazd model kod, destylacja domeny, słownik z kodu, homonimy w kodzie, dane w niemożliwym stanie, skrypty naprawcze, reguła sprawdzana tylko w UI, walidacja tylko na froncie, endpoint ufa danym z żądania, niezmiennik, który niezmiennik naprawić najpierw, agregat strażnik, błąd domenowy, przeciek biblioteki, typy biblioteki w schemacie bazy i API, wymiana biblioteki to projekt na sprint, odizolować bibliotekę w działającej aplikacji, warstwa antykorupcyjna w legacy, tylko adapter importuje pakiet, import-linter, czy już DDD w prototypie, legacy modernization, code does not reflect the domain, model vs code drift, domain distillation, same word means three things, PRD concept missing in code, impossible data states, rule enforced just in the UI, endpoint trusts request data, invariant to fix first, guardian aggregate, named domain error, library types leak everywhere, replace a library, isolate a dependency, package imported outside the adapter, enforce in CI"
---

# Legacy modernization — does the code match the business?

Refactoring asks *how to change code safely*. This skill asks *whether the code says what the business means* — and plans
the fix. It produces diagnoses and plans, not production code; the implementation follows ddd-tactical-design and
eng-behavior-preserving-refactoring.

**Too early?** On a prototype before the product is validated, do not model; model when it starts to hurt.

**Signals that it hurts:** one word for several things (three different `Account`s); an entity from the PRD that exists in
the code only as a loose id next to rows; rescue scripts for data in "impossible" states; a rule enforced only in the UI;
a library whose replacement would take a whole sprint.

**Never assume** an entity, a rule or a leak in advance. Discover them from the documents and the code, and quote the
`file:line` you actually read.

## Step 0 — shared context
- Read the PRD, the stack decision, the README and the change history in `docs/project/`. No requirement documents →
  work from the README and the code, and record that as a constraint of the diagnosis.
- Find where the logic lives (API, services, domain, UI, persistence) and list the dependencies from the manifest.
  A code map (eng-codebase-mapping) shortens this.

## A. Language drift → `docs/project/02-domain/distillation.md`
1. **Glossary table:** term | definition | where the documents say it (`file:line`) | where the code has it (`file:line`,
   or the marker `BRAK w kodzie` when the term has no counterpart). All names of one thing across database, UI, API and
   speech go in one row.
2. **Subdomains:** core / supporting / generic, each justified by the product's goals (ddd-strategic-analysis).
3. **Aggregate candidates:** each with the rule it should protect (quoted) and its status — **enforced** (guarded on the
   server), **declared** (written in a document, not guarded), **ignored** (the code contradicts it).
4. **Model ↔ code divergences** — the most valuable part: *the document says X / the code does Y / evidence*.
5. **Ranking:** business value of the area × risk from weak enforcement; item 1 goes to B or C.
New glossary entries go to `glossary.md` as proposals for the human to accept (ddd-facilitation).

## B. A rule guarded only by hope → `docs/project/02-domain/invariant-<name>.md`
1. **List the "always true" rules:** X exists only as a result of Y; A becomes B only when C; Z happens all-or-nothing;
   D is never saved.
2. **Rank them** on three questions: how close to the core is the rule; how many files and layers touch it; how strongly is
   it enforced (enforced / declared / violable). Choose the most valuable, weakest-guarded rule — often not the one the
   team suspected.
3. **Diagnose every layer:** the rule missing, inconsistent between layers, the UI as the only guard, an endpoint trusting
   numbers from the request, an error logged and swallowed.
4. **Design** (ddd-tactical-design):
   - the aggregate root is the only place that enforces the rule; its methods check preconditions;
   - an illegal operation raises a **named domain error** (fail fast — never log and continue);
   - a repository loads and saves the whole aggregate; an all-or-nothing rule = one transaction;
   - the API route is thin: parse → call the method → map the domain error to a response (e.g. 409 Conflict);
   - enforcement moves from the client to the server; the UI may still warn early.
5. **Before / after** for each place the rule lives today; phases test-first (eng-behavior-preserving-refactoring);
   test cases for legal and illegal sequences.

## C. The leakiest dependency → `docs/project/02-domain/acl-<package>.md`
1. **Signals:** the same package imported in API, UI and services; its types in domain signatures, DTOs or responses; the
   same conversion repeated; an SDK used on both sides of the client/server boundary.
2. **List every file that knows the dependency:** `rg -l "from '<pkg>'"` plus a structural search (ast-grep) for dynamic
   imports and `require`.
3. **Rank the leaks:** layers and files reached; what replacing it would cost today; whether the documents promised it
   would be replaceable (a broken promise is the strongest signal). Pick the worst. Look especially for a server-only
   library pulled into the client bundle.
4. **Design:**
   - a domain value object is the only place that knows the dependency's shape (persistence mapping, conversion to and from
     the library's type);
   - a narrow port in the domain's language; an adapter that wraps the library; the UI receives domain data;
   - decisions that depend on the library's contract come from its documentation and live in the ACL, not in the API.
5. **Proof:** a "knows today / knows after" list of files. **Done** = a search for the package name returns only files in
   the adapter directory, locked by a CI rule (dependency-cruiser `forbidden`, ESLint `no-restricted-imports`, ArchUnit,
   import-linter or Tach for Python). Commands and rule templates: `references/rule-templates.md`.

Document templates for A, B and C: `references/document-templates.md`.

## Next
The outputs feed planning: core-plan-interview turns them into a phased plan; hot spots from an Event Storming session
(ddd-event-storming) are further candidates. The cycle: find the drift → secure the rule → isolate the dependency → plan.

## Example
**Situation:** a field-inspection app, 2 years old. The PRD says "an inspection can be closed only when every checklist
item is marked passed or failed"; the code calls the thing `visit` (database), `job` (API), `audit` (UI) and "inspection"
(PRD), and a library for recurring schedules leaks everywhere.
**Result:**
- A: one glossary row *Inspection* with four names; `InspectionTemplate` from the PRD → `BRAK w kodzie`; divergence:
  "PRD: closed only when complete / code: `PATCH /jobs/:id` sets `closed=true` with open items (`api/jobs.ts:88`)".
- B: the rule is guarded only by a counter in `ChecklistFooter.tsx:41` and the endpoint trusts `openItems` from the
  request → aggregate `Inspection` with `markItem()` and `close()`; `close()` raises `InspectionHasOpenItems`; one
  transaction; the route maps the error to 409. Test cases: close with 0 open items, close with 1 open item, mark after close.
- C: the recurrence library's `RRule` type sits in the schema, API responses and UI props (9 files, 3 layers),
  while the stack decision promised it is replaceable → value object `RecurrencePattern`, port `ScheduleExpander`, adapter
  in `src/schedule/adapter/`; done when `rg -l "from 'rrule'" src/` lists only that directory; a dependency-cruiser
  `forbidden` rule in CI.

If asked for production code for the aggregate, give the plan and pseudocode and hand implementation to ddd-tactical-design.

## Sources
- Tool syntax and versions: `references/rule-templates.md` (dependency-cruiser, ESLint, ArchUnit, import-linter, Tach, Nx
  documentation, checked on the dates given there).
