---
name: proc-requirements-shaping
description: Use when an idea must become requirements (PRD) — an MVP within a budget, an empty CRUD, a business rule.
metadata:
  review: "2027-10-10"
  catalog: "Use when an idea or a larger change to an existing system must be turned into a requirements contract (PRD) before the architecture — a phased question session (problem, access, MVP, FR requirements, a challenge for every requirement, a business rule in one sentence, framing and 'out of scope'), the 'MVP too big' threshold as the time budget from the brief, detecting an empty CRUD, quality requirements without a mechanism, open questions instead of guesses, greenfield and brownfield mode (delta), the requirements_lint.py script. Not for deciding whether and what is worth building (proc-product-discovery), the mechanics of question rounds (core-plan-interview), acceptance criteria as tests (qa-spec-first-testing) or a project plan with cost for the sponsor (proc-project-planning)."
  keywords: "PRD, wymagania produktu, spisz wymagania, dokument wymagań, zakres MVP, pierwsza wersja, za duże MVP, pusty CRUD, reguła biznesowa, kształtowanie zakresu, wymagania funkcjonalne, FR, historyjki, poza zakresem, wymagania zmiany, mam pomysł na aplikację, product requirements, to nie są wymagania, przepisać wymagania, wymaganie z technologią, wymagania jakości, recenzent PRD, szybko i niezawodnie, przymiotnik w wymaganiu, wymaganie jakościowe niejasne, czy wymaganie jest wystarczające, zanim agent zacznie pisać kod, spec kit, .specify, constitution.md, openspec, delta specyfikacji, scalenie wymagań zmiany, jak system ma działać dziś, stare zmiany, dokument wymagań zmiany, write down the requirements, requirements document, MVP scope, first version, MVP too big, empty CRUD, business rule, scope shaping, functional requirements, stories, out of scope, change requirements, I have an app idea, these are not requirements, rewrite the requirements, requirement with a technology, quality requirements, PRD reviewer, fast and reliable, adjective in a requirement, vague quality requirement, is the requirement sufficient, before the agent starts writing code, specification delta, merging change requirements, how the system should work today, old changes, change requirements document"
---

# Shaping requirements (PRD) — from an idea to a contract

The agent **leads the conversation but is not the author**. It does not add vision, requirements or rules that the human did not
state. The value of this skill is the order and shape of the questions. A question without an answer goes to the "Otwarte pytania" section (Open questions)
with an addressee — never into the body as a guess. The result is a contract without technical decisions, which the
architecture uses (B2 in core-delivery-lifecycle).

## When
- An idea for a product or a larger change to a working system, before an architecture or a plan exists.
- On the shortened path (core-delivery-lifecycle) this session replaces phases 1 and 3 in one document.
- At every later larger change of scope, run a **mini-session** of this procedure for the delta alone.
- The repo already has specifications (`.specify/` from Spec Kit, `openspec/` from OpenSpec) → you read them as existing requirements
  and add a delta, instead of writing a parallel document; merging a change's delta into the current state of the requirements:
  `references/existing-specifications.md`.

Whether it is worth building at all (outcome, opportunities, experiments) — proc-product-discovery first.

## Setting: the MVP time budget
The only "MVP too big" threshold is the **time budget from the brief**, not a constant from this skill. At the start of the session ask
the human and record it in `01-discovery/brief.md`, in the "Constraints" section:
```
- MVP time budget: 3 weeks               # set by the human (e.g. 4 weeks after hours, 2 team sprints)
- MVP flow estimate: 5 weeks             # after phase 3, with a justification
- Cost acknowledged: 2026-10-10, the product owner accepts 5 weeks   # only when the estimate > the budget
```
Give both values in the same convention (working days, weeks, months). The number of user steps
and the number of integrations before the first value are **signals for a conversation**, not thresholds.

## Mode
Check the repository: git history or a lockfile → **brownfield** (requirements as a delta); a manifest alone with no
history → ambiguous, ask; nothing → **greenfield**. Confirm with the human and record it in the brief
("Typ projektu", project type). The brownfield differences in each phase: `references/examples.md`.

## Session phases
Each phase: one open question → 3–5 **grey areas** as options with a recommendation (plus "I don't know") →
confirmation → recording. You run the question rounds per core-plan-interview (only independent questions in one round).

1. **Problem.** The pain, a specific person (a role, not "users"), the moment it hurts, and the cost today.
   The challenge: "what would have to be true for this to be the wrong problem to solve?".
   Brownfield: what exists, who uses it, what hurts and **what must not break**.
2. **Access.** Login, a local profile, a key or none; roles and who sees what.
   Brownfield: the current access model and whether the change touches it.
3. **MVP.** The first flow step by step, repeated back to the human as a numbered list, and an estimate.
   An estimate above the time budget → **name the expensive elements** and propose cuts:
   - remove element X from the first version (to "Poza zakresem", out of scope);
   - replace an integration with a manual action or a file import;
   - one user instead of teams and roles;
   - one platform instead of web and a mobile app.
   A longer schedule is allowed only as a conscious decision: a "Cost acknowledged" line with a date and a person.
   Brownfield: the smallest change that proves an improvement and the blast radius (what else it touches).
   Change mode (the log `docs/project/changes/CHG-n/`): the MVP outcome with a metric (threshold, horizon) goes to `mvp`
   in the change's `release.yaml`, and the cuts from "out of scope for the MVP" go to the R2 line.
4. **Requirements.** Each in the format `FR-NNN: <actor> can <capability>. Priority: must|nice`
   (brownfield additionally `Change: new|changed|kept`). Each story `US-NN` has at least one
   scenario `AC-n` in Given/When/Then (Polish keywords: Zakładając, że / Gdy / Wtedy) and **one action**: a verb with an object
   in the When step, and data variants go to Given. More actions (a conjunction between verbs, several actors,
   different actions in the scenarios) or a title that starts from a layer (BE:, API:) → a split before recording per proc-agile
   (`.claude/skills/proc-agile/references/map-and-split.md`):
   ```
   ### US-02: A customer applies a discount code
   As a customer I want to use a discount code so that I pay less.
   - AC-1: Given the code DISCOUNT10 is active
     When the customer applies the code DISCOUNT10
     Then they see the price reduced by 10%
   ```
5. **A challenge for every FR** (a separate round). For each requirement: "what would have to be true for this
   requirement to do harm?" — 2–4 counterarguments from the domain, "no counterargument" as the last option. Record the result
   under the requirement (a "Challenge" column or line).
6. **A business rule in one sentence** — a decision the application makes on its own and that distinguishes it from a list
   of records. When the answer comes out as "the user adds, edits and deletes records", call it plainly an
   **empty CRUD** and show the shapes of a rule to choose from:
   a recommendation · prioritization · classification · validation · assessment (scoring) · a state flow · a calculation.
   The human may consciously stay with CRUD — then record "no domain rule" under "Otwarte pytania" (Open questions).
   Brownfield, a purely technical change (migration, performance): record "no change to the domain rule" and skip this test.
7. **Quality requirements and framing.** Quality as a property measurable from the outside, without a mechanism:
   | Instead of (a mechanism) | Write (the behavior) |
   |---|---|
   | "a per-IP limit in Redis, server-side" | "one client cannot send more than 100 requests per minute; the excess gets a clear message" |
   | "a spinner while saving" | "within 1 s the user sees that saving is in progress and cannot submit it a second time" |
   | "passwords in bcrypt" | "a database leak does not reveal passwords in plain form" (the mechanism: arch-threat-modeling) |
   Plus the product type, scale, schedule and **"Poza zakresem"** (out of scope) — functional and quality (e.g. "no
   offline mode"). Record the human's technology preferences in a separate block "Do decyzji o stacku" (For the stack decision)
   (arch-tech-selection), not in the requirements.

## The soft gate (before recording)
Check and name every gap together with its consequence:
- [ ] access established;
- [ ] a business rule in one sentence (or a consciously recorded CRUD);
- [ ] the MVP flow within the time budget or "Cost acknowledged" recorded;
- [ ] "Poza zakresem" has at least one item;
- [ ] (brownfield) it is recorded which behavior stays unchanged.
The human may accept a gap — it then goes to "Otwarte pytania" with an addressee and the note "blocks: yes/no".

**The two-implementations technique** for a sentence with a quality adjective ("fast", "secure", "reliable"):
sketch two reasonable solutions and check whether they differ in anything visible to a user or an operator. If
they do, the specification is silent and a decision is missing. You ask about five classes: scale, execution mode (immediately / in the background), failure
and retries, permissions, migration of existing data. Each decision has options, a justification, a **way
of verifying** (a test, a fitness function in CI, a review point) and an owner (a role, not "the team"). Reversibility ×
reach: local and reversible the agent decides with a record, broad the agent proposes, one-way the
owner decides before code.

## Recording
- `01-discovery/brief.md` (a template in core-project-record): the problem, persona, goals with a measure (**primary**,
  **secondary**, **guardrail** — what must not get worse), scope and "Poza zakresem", project type, time budget.
- `03-requirements/requirements.md`: the sections "Functional requirements" (FR with the challenge), stories, "Reguła
  biznesowa" (the first line = one sentence), quality attributes, access, "Poza zakresem", "Do decyzji o stacku".
  Brownfield additionally: "Obecny system" (Current system) and "Preserved behavior"; the content describes the delta.
- No frameworks, vendors, database schema or protocols in the requirements — they belong to the architecture.
- Before recording, **run** the check (readiness 0–4, technique leakage, the MVP threshold from the brief):
  `python3 .claude/skills/proc-requirements-shaping/scripts/requirements_lint.py docs/project/03-requirements/requirements.md --brief docs/project/01-discovery/brief.md`
  Code 1 = technique leakage or an estimate above the budget without a cost acknowledgment; readiness < 2 is a warning.
  The shape of stories (AC-001…004, STORY-001…003, missing `AC-n`) gives warnings with the `US-NN` and the rule; `--strict`
  turns them into code 1. A single story is checked by `--story <file>`.
- A session longer than one conversation: a checkpoint in `.tf/wip/` with the progress of the phases (core-project-record).

## Check after recording (ask the human)
Is this one specific user? Will the flow fit in the time budget? Is the rule a domain decision,
not a description of a screen? Is "Poza zakresem" explicit? Are the open questions really open?

## Example
**Input:** "A flashcard app with AI — I paste notes, I get flashcards for review. I have 3 weeks after hours."
**Result (a fragment of `requirements.md`):**
```
## Functional requirements
- FR-001: A learner can paste text of up to 10 thousand characters and get flashcard suggestions. Priority: must
  Challenge: suggestions from a long text are too generic → a length limit and a source preview on the flashcard.
- FR-002: A learner can accept, edit or reject each suggestion. Priority: must
## Business rule
A flashcard suggestion enters the deck only after the learner accepts it, and accepted ones enter the review schedule.
## Out of scope
- PDF import · deck sharing · a custom review algorithm
## Guardrail goals
- the source text does not remain in the logs
```
The estimate "login + a mobile app" came out at 6 weeks against a budget of 3 → cuts: web only, a local profile
instead of accounts. Check with the script: readiness 4/4, no leakage. More (brownfield, challenges): `references/examples.md`.

## Checklist
- [ ] the MVP time budget set by the human and recorded in the brief; the estimate next to it
- [ ] the mode (greenfield / brownfield) confirmed
- [ ] each FR in the `FR-NNN` format with a priority and the result of the challenge
- [ ] each `US-NN`: ≥ 1 scenario `AC-n` in GWT and one action (more → a split)
- [ ] a business rule in one sentence or a consciously recorded empty CRUD
- [ ] quality requirements as externally visible behavior; technique in "Do decyzji o stacku"
- [ ] "Poza zakresem" non-empty; gaps in "Otwarte pytania" with an addressee
- [ ] `requirements_lint.py --strict` ends with code 0 (or the human accepted the named warnings)

## Sources
- The 10xDevs course, ed. 3 (2026), prework (lessons 4.1–4.3) and module 1, lesson 1 (scope shaping and the PRD) — training
  material (accessed 2026-10-09). The course gives inconsistent MVP thresholds (once about a week and 4 actions, once 3 weeks
  and 6 actions) — replaced here by the setting from the brief.
- M. Cagan, *Inspired* (2018) — requirements as a problem and an outcome, not a list of features; Mike Cohn, *User Stories Applied*
  (2004); Gherkin Given/When/Then — cucumber.io/docs/gherkin (accessed 2026-10-10); the story shape rules
  and the vocabulary — the pdi contract 0.4.0 (`contract/fixtures/story-shape/`, 2026-10-25).
Described in our own words.
