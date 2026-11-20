---
name: core-delivery-lifecycle
description: Use when taking a project from idea to production and maintenance with AI agents — phases 0-9, human gates B1-B6, artifacts, cut plan, readiness, measures.
metadata:
  review: "2027-11-20"
  catalog: "Use when you need to know which stage a project is at, what must exist before coding or a release, who approves moving on, how to run AI agents in phases with personas, what happens post-deployment, where each project document goes (artifact map), how to order delivery (cut plan, release lines, flags), how to review a spec with a panel, run a factory dry run or build an AI-native loop (plan before code, agent evals, AI PR review, control bands, paired measures). Not for the content of one phase (pack dimension skills), an end-of-stage agent retrospective (core-agent-retro), a canary rollback (ops-release-engineering) or one incident (ops-sre-incidents)."
  keywords: "na jakim etapie jesteśmy, fazy projektu, etapy projektu, cykl życia projektu, od pomysłu do produkcji, od pomysłu do wdrożenia, kto zatwierdza dalszy krok, kto odbiera, bramki człowieka, akceptacja etapu, co musi być gotowe przed kodem, zanim programiści ruszą, gotowość do wydania, przegląd gotowości, kryteria wydania, makiety i połowa backendu, agenci AI prowadzą projekt, praca z agentami w etapach, kiedy człowiek patrzy agentowi na ręce, kto wdraża na produkcję, po wdrożeniu, projekt naprawdę skończony, utrzymanie po wdrożeniu, łatki bezpieczeństwa, aktualizacje zależności, wycofywanie funkcji, ścieżka skrócona, mały projekt, które etapy pominąć, plan faz, walking skeleton, plan cięć, cięcia pionowe, fundamenty, niewiadome blokujące, gwiazda przewodnia, od którego cięcia zacząć realizację, plan wydania, linie wydania, MVP, release.yaml, wdrażanie za flagą, przegląd specyfikacji, dziury w specyfikacji, próba fabryki, dry run, kod od agentów szybszy niż przeglądy, plan przed kodem, ewaluacje agenta, REVIEW.md, pasma kontrolne, pogorszenie metryk produkcji, udział agentów w pull requestach, refinement z agentami, refinement kończy się opisem z AI, sukces mierzony odsetkiem agentów, budżet artefaktów w PR, mapa artefaktów, gdzie zapisać dokument, dokumenty fazy architektury, project phases, who approves the next stage, idea to production, release readiness, human gates, shortened path, which stages can be skipped, share of PRs by agents"
---

# Delivery lifecycle with AI agents — phases, gates, artifacts

Agents lead and execute; the human is the product owner, approves at fixed gates and stays accountable. Every phase
ends with a file in `docs/project/…`, not a chat message. This skill says **which phase, what it produces, who
approves**; the content of a phase lives in the packs' dimension skills.

## Operating rules
- Gates are mandatory. An agent never marks an artifact as accepted and never deploys to production; it prepares, the
  human approves.
- Each phase may be a separate session or persona. A new session starts from `python3 .claude/hooks/project_record.py
  status`, the TL;DR and the Handoff of the last artifact; `project_record.py report` summarises the record.
- Open business or legal questions get an addressee and a date — never a guess.
- A change to an accepted artifact is a new version with a new acceptance; decisions go to `decisions.md`, progress to
  the journal.
- Human-only work (accounts, secrets, domains, contracts, payments, real-user tests, legal and business decisions, pen
  tests with written scope consent, the production deployment, unrequested dependency bumps) goes into the phase plan as
  dated tasks for the human.

## Start: choose the path and write the phase plan
1. The pack's dispatcher persona (`dispatcher: true`, e.g. `claude --agent maja` in pack-it) interviews the human, estimates
   scale and risk and picks the **full** or **shortened** path. Without a dispatcher: core-problem-routing.
2. It writes `01-discovery/brief.md` with a **Phase plan** section: phases, the persona for each, the gates, the human's
   tasks. With a budget or a deadline also `01-discovery/project-plan.md` (P50/P80 ranges of cost and date, milestones,
   risk register; proc-project-planning).
3. The human starts the persona named in the last Handoff; personas do their own tasks (core-cost-control §0).
   Staffing with skill names: `references/pack-staffing.md`.

## Phases
| # | Phase | Main outputs | Directory | Gate |
|---|---|---|---|---|
| 0 | Intake | brief with phase plan; project plan with P50/P80 when needed | `01-discovery/` | — |
| 1 | Product discovery | hypotheses, success metrics, user flows, mock-ups, product risks | `01-discovery/` | B1 |
| 2 | Domain | glossary, domain events, bounded contexts, context map, contradictions | `02-domain/` | — |
| 3 | Requirements | acceptance criteria as examples, quality attributes as scenarios, priorities, personal data flagged; spec review | `03-requirements/` | B2 |
| 4 | Architecture | stack decision, C4, ADRs, threat model, estimates, data/deploy/observability strategy, privacy doc for personal data | `04-architecture/` | — |
| 5 | Plan | cut plan (walking skeleton first), `release.yaml`, test plan | `05-plan/` | B3 |
| 6 | Delivery | per step: code, tests, review, step report `06-delivery/NNN-<slug>.md`; CI green from step one | `06-delivery/` | — |
| 7 | Release preparation | environments as code, security review, regression and performance tests, runbook, readiness review | `06-delivery/`, `07-review/` | B4 |
| 8 | Release and observation | human deploys, staged rollout with SLO gates, flags removed by date, retro and lessons | `07-review/` | B5 |
| 9 | Maintenance | periodic operations review, fixes, patches, updates, retirements | `08-operations/` | B6 |

Pack-it staffing: Maja → Natalia → Ewa → Tomasz → Tomasz + Kasia → executors + Kasia → Piotr.

## Human gates
| Gate | After | The human approves | Without approval |
|---|---|---|---|
| B1 Scope | 0–1 | problem, goal, success metrics, scope and out-of-scope, budget | further work is only a draft |
| B2 Requirements | 3 | requirements, acceptance criteria, priorities | architecture is marked "based on proposal" |
| B3 Architecture | 4–5 | stack, key ADRs, threat model, maintenance cost, the plan | no delivery, except a risk-checking skeleton with consent |
| B4 Readiness | 7 | readiness review result, consciously accepted risks, release or no release | no release |
| B5 Release | 8 | start of production deployment; each move to the next rollout stage once its exit criterion is met and the minimum time has passed; rollback | the agent only prepares |
| B6 Maintenance | 9, periodic | fix priorities, patch deadlines, updates, retirements, budget | proposals wait; critical patches follow the prior arrangement |

## Shortened path
Allowed when: one team, a few screens or endpoints, no sensitive data or regulation, easy rollback.
- Phases 0–1 merge; phase 2 is skipped (a short glossary goes into the brief); phases 3–5 are one document.
- B1, B2 and B3 become one acceptance. **B4 and B5 always stay**, with a minimum readiness review (the points marked
  "minimum" in `references/production-readiness.md`).

## Delivery rules
1. **Walking skeleton first:** the thinnest flow through every layer and the pipeline, deployed to a test environment,
   before any feature depth.
2. **Risk first:** prototypes and spikes for the riskiest assumptions before B3.
3. **Tests come from acceptance criteria**, written before or alongside the code by a test designer who does not see
   the implementation (qa-spec-first-testing).
4. **Every step ends with a pass/fail command** whose output the agent shows as evidence in the step report.
5. **The author does not judge their own work:** review in a fresh context — `/code-review`, the security-reviewer agent
   for risky areas.
6. **No silent scope change:** a new requirement during delivery goes back to phase 3 as a new requirements version.
7. **Replan when reality contradicts the plan.** If an assumption the plan rests on is false (a module, interface,
   data shape or permission model missing or different), the agent stops coding, writes in the step report what the
   plan assumed, what it found and what that changes, offers options and waits for the human; the plan is updated
   first. A small difference that touches no interface or end state goes under **Deviations** and work goes on.
8. **Plan effort scales with risk:** each step report starts with a **Step plan**; a one-line change needs one line, a
   migration or security change needs alternatives and a rollback.
9. **Cheap models** for search and mechanical edits, strong ones for architecture and security; **state lives in
   files**; end-of-stage cost and causes: `.tf/factory/cost_stats.py`, core-agent-retro.

## Phase 5: cut plan and release plan
`05-plan/plan.md` orders the work into **foundations** `F-NN` (enabling work that must name what it unblocks) and
**vertical slices** `S-NN` (a result a user can see, tied to a requirement ID). The first slice is the thinnest end-to-end
flow (**North star**); items depending on an open question with blocks=yes are **blocked**; never "the whole data model
first". Release lines (R1 = MVP with an outcome metric) and flags with rollout stages go to `05-plan/release.yaml`
(or `changes/CHG-n/release.yaml`); phase 8 follows those stages and every stage move is B5. Method, column names,
statuses and self-check: `references/cut-plan.md`.

## Reviews and readiness
- **Spec review** after phase 3, before the cut plan, when agents will build it, the change is large or touches
  permissions, money, data or schema: 2–3 reviewers in fresh contexts (adversary, operator, executor), findings with
  severity; the gate passes when blocking and serious ones are closed with a trace. Report `03-requirements/spec-review.md`;
  method `references/spec-review.md`.
- **Readiness review** before B4: `07-review/<date>-readiness.md`, each point met (with evidence: a CI run link, report,
  command output) / not met / risk accepted (who, fix-by date). "Tests pass" without CI evidence is an assumption.
  Verdict ready / ready with accepted risks / not ready. Checklist: `references/production-readiness.md`.
- **Dry run** of the factory on a small real project: `07-review/<date>-dry-run.md`, `references/dry-run.md`.

## Phase 9: maintenance
- A periodic operations review (weekly or per sprint, template `operations-review`) in
  `08-operations/<date>-operations-review.md`: SLOs, incidents, issues by severity (proc-issue-triage), patches,
  dependency updates (ops-dependency-upgrades), costs, retirements. Metrics go under control bands.
- Bug: cause → red regression test → fix → release on the shortened path.
- A critical vulnerability in an exposed component gets a fast path exempt from the dependency cooldown
  (ops-supply-chain-security); the human sets the deadline. Minor updates regularly, majors before end of support, one at
  a time; the agent only proposes.
- Retiring a feature is the human's decision based on usage data: announce it with a date and a transition path,
  deprecate in a minor version, remove in a major one, delete code and data per the retention policy. Shutting down the
  whole system is a mini-project with B1 and B5 (data export/archive/delete, user notice, infrastructure and cost).
  More: `references/maintenance.md`.

## AI-native loop
When agents code faster than people review, test and deploy, rebuild controls as artifacts, hooks and agent review
layers, with a human on critical code: intent → spec → plan → diff + tests → PR + review → maintenance record →
new brief; nothing is implemented without an accepted plan; the agent verifies itself with one command; configuration
changes (CLAUDE.md, skills, hooks, model) are evaluated on real cases; AI review follows `REVIEW.md`, a human merges;
autonomy measures are reported only next to outcome measures. Detail: `references/ai-native-sdlc.md`.

Scripts (run them, do not read them):
- `python3 .claude/skills/core-delivery-lifecycle/scripts/control_band.py metric.csv --baseline 30 --side upper` —
  Western Electric rules on a metric (`--column C`, `--side both|upper|lower`, `--format json|text`): a point beyond 3σ →
  **act** (PR or approved runbook); 2 of 3 beyond 2σ on one side → **diagnose** read-only; 4 of 5 beyond 1σ or 8 in a row
  on one side of the mean → **log**. Exit 2 on bad data (e.g. zero baseline deviation).
- `python3 .claude/skills/core-delivery-lifecycle/scripts/pr_budget.py --base main [--json]` — whether artifacts drown the
  code in a PR (defaults: artifacts ≤50% of added lines, one artifact ≤600 lines, a plan ≤300; config
  `.claude/pr-budget.json`). First line `Werdykt: OK | OVER`, exit 1 when over.

## Where documents go
Every artifact, its directory, author persona and what a small project may skip: `references/artifact-map.md`
(e.g. `04-architecture/stack-decision.md`, ADRs, `threat-model.md`, `privacy.md`, `erd.md`; the OpenAPI contract lives in
the code repository).

## Example
"Small internal report builder, three screens, one team, no sensitive data, easy rollback — what can we skip?" →
shortened path: one brief covers phases 0–1 with a glossary, one document for requirements, architecture and plan, a
single B1–B3 acceptance; delivery starts with a walking skeleton; **B4** (minimum readiness review with CI evidence) and
**B5** (the human deploys) stay.

"Mock-ups, half a backend, the client changes requirements weekly — where are we?" → code was started before B2: delivery
(6) is running without accepted requirements (3) and architecture (4). Freeze new features, write the current
requirements as version 1, the product owner approves B2, then B3; each later change is a new requirements version.

## Checklist
- [ ] path chosen; brief with Phase plan, personas, gates, the human's dated tasks; every phase ends with a file
- [ ] gates B1–B3 (or one combined acceptance) passed before delivery; B4 and B5 never skipped
- [ ] walking skeleton first; every step ends with a pass/fail command and its output
- [ ] plan contradictions stopped the step and updated the plan; small ones logged as Deviations
- [ ] readiness review with evidence per point; the human deployed; flags have owners and removal dates
- [ ] maintenance: periodic operations review, control bands, retirements decided by the human

## Sources
- A. Cockburn, *Crystal Clear* (2004) — walking skeleton; J. Humble, D. Farley, *Continuous Delivery* (2010).
- Google, *Site Reliability Engineering* (2016) — production readiness, SLOs; GOV.UK Service Manual, live and retirement
  phases [unverified: page titles].
- Anthropic, "The AI-Native SDLC Playbook" (2026-08-21); AWS, "AI-Driven Development Life Cycle" (2025-07-31).
- Western Electric, *Statistical Quality Control Handbook* (1956) — control chart rules.
