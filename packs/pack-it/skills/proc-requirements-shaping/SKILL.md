---
name: proc-requirements-shaping
description: Use when turning an idea or a larger change into a requirements contract (PRD) — MVP within a time budget, FRs, stories with Given/When/Then, business rule, out of scope.
metadata:
  review: "2027-11-20"
  catalog: "Use when leading a question session turning an idea, or a larger change to an existing system, into a requirements contract without technical decisions — the problem and the person, access, the MVP within the agreed time budget (cuts, a recorded cost acknowledgement), FR-NNN requirements with a challenge each, US-NN stories with AC-n criteria in Given/When/Then and one action per story, the business rule in one sentence (the empty-CRUD question), quality requirements as externally visible behaviour (sketching alternative solutions), out of scope, open questions, greenfield vs brownfield delta, change mode (release.yaml mvp, R2), the requirements_lint.py lint, reading Spec Kit and OpenSpec specifications and merging change deltas. Not for deciding whether and what to build (proc-product-discovery), the mechanics of question rounds (core-plan-interview), acceptance criteria as tests (qa-spec-first-testing) or a sponsor's project plan (proc-project-planning)."
  keywords: "wymagania, spisz wymagania, PRD, dokument wymagań, wymagania na pierwszą wersję, mam pomysł na aplikację, z pomysłu do wymagań, zakres MVP, MVP za duże, czy zakres jest w porządku, budżet czasu, kilka tygodni po godzinach, wymagania funkcjonalne, FR, historyjka użytkownika, user story, kryteria akceptacji, Given When Then, Zakładając Gdy Wtedy, reguła biznesowa, reguła domenowa jednym zdaniem, pusty CRUD, dodaje przegląda edytuje usuwa, aplikacja to tylko CRUD, poza zakresem, otwarte pytania, wymagania niefunkcjonalne bez technologii, wyciek techniki do wymagań, Redis w wymaganiach, spinner w wymaganiach, szybko i niezawodnie, przymiotnik w wymaganiu, dwa rozwiązania wymagania, rozbić historyjkę, jedna akcja na historyjkę, zmiana w istniejącym systemie, delta wymagań, dziennik zmian, release.yaml, czy wymaganie jest wystarczające, zanim agent zacznie pisać kod, spec-kit, katalog .specify, spec.md plan.md tasks.md, pisać od nowa własny dokument wymagań, spisać wymagania do nowej funkcji w repo, OpenSpec, constitution.md, needs clarification, scalanie delty, nikt nie wie jak system działa dziś, requirements, write the requirements, PRD, MVP scope, MVP too big, time budget, functional requirements, user stories, acceptance criteria, business rule in one sentence, empty CRUD, out of scope, open questions, technology leak in requirements, fast and reliable, vague quality adjective, split a story, brownfield requirements, change delta, spec kit, openspec, merge spec delta"
---

# Requirements shaping — from an idea to a requirements contract

The agent leads the session; the human is the author. The value is in the order and shape of the questions. The result
is a contract **without technical decisions**, which architecture then consumes. Never add vision or rules the human did
not state; anything unanswered goes to "Open questions" with the person who can answer it. No idea described yet →
ask for the problem and the person first.

**Used for:** a new idea; a larger change before architecture and planning; the shortened path (one document replaces
lifecycle phases 1 and 3 — core-delivery-lifecycle); mini-sessions for later scope changes. A repository with `.specify/`
(Spec Kit) or `openspec/` (OpenSpec): read those as the existing requirements and add a delta —
`references/existing-specifications.md`.

**Output:** `docs/project/01-discovery/brief.md` and `docs/project/03-requirements/requirements.md` (templates:
core-project-record). A long session keeps a checkpoint in `.tf/wip/`.

## Before the first question
- **Time budget for the MVP** — the only "too big" threshold. The human sets it; ask at the start and record it in the
  brief: `- MVP time budget: <n> <unit>`. The number of user steps or integrations before first value is a signal for the
  conversation, not a threshold.
- **Mode** — git history or a lockfile → brownfield (a delta of an existing system); a manifest without history → ask;
  nothing → greenfield. Confirm with the human and record the project type in the brief.

## Session phases
Each phase: one open question → 3–5 grey areas offered as options with a recommendation and "I don't know" → confirmation
→ record. Rounds follow core-plan-interview; one round holds only questions that do not depend on each other.

1. **Problem** — the pain, a specific person (a role), the moment it happens, what it costs today. Challenge: "What would
   have to be true for this to be the wrong problem?"
2. **Access** — sign-in, a local profile, a key, or none; roles; who sees what.
3. **MVP** — the first flow as a numbered list, repeated back to the human, plus an estimate with its reasoning
   (`- MVP flow estimate: <n> <unit>`). Over budget → name the expensive elements and propose cuts: move an element out of
   scope; replace an integration with a manual step or a file import; one user instead of teams and roles; one platform.
   A longer schedule is allowed only as a conscious decision recorded in the brief:
   `- Cost acknowledged: <date>, <who> accepts <how much>`.
4. **Requirements** — `FR-NNN: <actor> can <capability>. Priority: must|nice`. Stories as `### US-NN: <title>` with
   "As a … I want … so that …" and at least one `- AC-n: Given … When … Then …`. One action per story: a conjunction
   between verbs, several actors, different actions across scenarios or a layer title (`BE:`, `API:`) → split it
   (proc-agile, map-and-split). Data variants go into Given, not into extra actions.
5. **Challenge each FR** (a separate round): "What would have to be true for this requirement to do harm?" Offer 2–4
   counterarguments from the domain plus "none"; record the answer below the FR.
6. **Business rule in one sentence** — a decision the application makes on its own. If the answer is only "add, view,
   edit, delete records", name it: **empty CRUD**, and offer rule shapes — recommendation, prioritisation,
   classification, validation, assessment or scoring, a state flow, a calculation. The human may keep CRUD on purpose →
   record "no domain rule" in the open questions.
7. **Quality and framing** — externally measurable behaviour, never the mechanism:
   - "a per-IP limit counted in Redis" → "one client cannot send more than 100 requests per minute; the excess gets a clear notice";
   - "show a spinner while saving" → "within 1 s the user sees that saving is in progress and cannot submit twice";
   - "credentials hashed with bcrypt" → "a database leak does not reveal credentials in readable form" (the mechanism goes
     to arch-threat-modeling).
   Also: product type, scale, schedule, out of scope (functional and quality). The human's technology preferences go to
   the separate section "For the stack decision" (arch-tech-selection).

**Vague quality adjectives** ("fast", "secure", "reliable"): sketch a pair of reasonable implementations; if a user or operator
would see a difference between them, the requirement is silent. Ask about five classes — scale, execution mode
(immediate or in the background), failure and retries, permissions, migration of existing data — and record for each
decision its verification (a test, a fitness function in CI, a review point) and its owner (a role). Who decides depends on
reversibility × reach: local and reversible → the agent decides and records it; broad → the agent proposes; one-way → the
owner decides before code. Worked example: `references/examples.md` §4.

## Brownfield — what changes per phase
- Problem: what exists, who uses it, what hurts, what must not break.
- Access: the current model and what changes in it.
- MVP: the smallest proof of improvement and its blast radius.
- Requirements: each FR gets `Change: new|changed|kept`.
- Business rule: one sentence about how the rule changes, or "no change to the domain rule" (skip for a purely technical change).
- Recording adds the sections "Current system" (technology names allowed — the lint skips it) and "Preserved behavior".
- **Change mode** (a project with a change log `docs/project/changes/CHG-n/`): the MVP outcome with a metric (threshold,
  horizon) goes to the `mvp` entry in `release.yaml`; the cut items go to the R2 line.
Example table and a waiting-list case: `references/examples.md` §1–2.

## Soft gate before recording
Access settled; a business rule or a conscious CRUD; the MVP within budget or the cost acknowledged; at least one item
out of scope; (brownfield) preserved behaviour recorded. The human may accept a gap → it goes to "Open questions" with the
addressee and "blocks: yes/no".

## Recording and the check
- **Brief:** problem, persona, goals with primary, secondary and guardrail measures, scope and out of scope, project type,
  time budget.
- **Requirements** (English template headings): Functional requirements (with the challenge), Business rule (the first
  line is one sentence), Stories (MVP), Quality attributes, Technical and organisational constraints, Out of scope (MVP),
  For the stack decision, Open questions, Handoff. No frameworks, vendors, schemas or protocols outside "Current system",
  "Constraints" and "For the stack decision".
- **Lint before recording:**
  `python3 .claude/skills/proc-requirements-shaping/scripts/requirements_lint.py docs/project/03-requirements/requirements.md --brief docs/project/01-discovery/brief.md`
  - readiness 0–4 (FR present, a Given/When/Then story, a one-sentence business rule, an out-of-scope item); below 2 → a warning;
  - exit code 1 = a technology leak, or an estimate over budget without a cost acknowledgement;
  - one story: `python3 .claude/skills/proc-requirements-shaping/scripts/requirements_lint.py --story docs/project/changes/<KEY>/ticket.md --strict`
    (rules AC-001…AC-004, AC-ID, STORY-001…003).
  Sample output: `references/examples.md` §5.
- **After recording, ask the human:** is there one specific user? does the flow fit the budget? is the rule a domain
  decision, not a description of a page? is out of scope explicit? are the open questions really open?

## Example
**Situation:** "Requirements for my recipe app: the user adds, views, edits and deletes recipes. That is all the logic."
**Result:**
- Named: this is empty CRUD — the app makes no decision of its own.
- Offered rule shapes: recommendation ("suggest three recipes from what is in the fridge"), validation ("a recipe cannot
  be published without quantities for every ingredient"), calculation ("scale quantities to the number of servings").
- The human picks scaling → Business rule: "The app scales every ingredient quantity proportionally to the chosen number
  of servings and rounds it to the unit's practical step."
- `FR-003: A cook can change the number of servings of a recipe. Priority: must`; challenge: "harm if rounding makes a
  baking recipe fail" → open question to the human: which units must not be rounded?
- Story `### US-03: Scale a recipe` with `- AC-1: Given a recipe for 4 servings with 200 g flour When the cook selects 6
  servings Then the recipe shows 300 g flour`.
More cases (brownfield, challenge round, paired implementations, lint output): `references/examples.md`.

## Sources
- Gherkin reference — Given/When/Then syntax, cucumber.io/docs/gherkin (accessed 2026-11-20).
- A. Mavin et al., "Easy Approach to Requirements Syntax (EARS)", IEEE RE 2009 (the `--ac-format ears` option).
- M. Cagan, *Inspired*, 2nd ed., 2018; M. Cohn, *User Stories Applied*, 2004.
- Story-shape rules and vocabulary: `scripts/story_shape_vocabulary.json` (pdi story-shape contract 0.4.0).
