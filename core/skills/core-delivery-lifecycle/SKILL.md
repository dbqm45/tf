---
name: core-delivery-lifecycle
description: Use when you ask about a project's stage, readiness before code or a release, approving a transition — phases, gates.
metadata:
  review: "2027-10-09"
  catalog: "Use when a project is to go from an idea to software ready for deployment — the order of phases, the personas and skills of the phases, entry and exit criteria, gates approved by the human, the definition of \"production ready\", maintenance after the release (patches, updates, retiring features, metric control bands), the delivery process with AI agents (the artifact loop, a plan before the code, evaluations of the agent configuration, an AI review of the PR, stage measures), the shortened path for small projects and a dry run. Not for the content of a single phase (dimension skills from the packs: domain, architecture, tests, operations — the list in .claude/catalog.md)."
  keywords: "przegląd specyfikacji, czy specyfikacja ma dziury, sprawdzenie wymagań przed planem, panel recenzentów specyfikacji, mapa artefaktów, jakie dokumenty w której fazie, gdzie zapisać dokument, plan cięć, kolejność cięć, fundament, od czego zacząć realizację, gwiazda przewodnia, cykl życia oprogramowania, SDLC, AI-native, proces z agentami AI, przebudować proces wytwarzania, przeglądy nie nadążają, pętla, metryki procesu, pasma kontrolne, Western Electric, AI-DLC, od pomysłu do produkcji, utrzymanie po wydaniu, refinement z agentami, opis zadania wygenerowany przez AI, odsetek PR napisanych przez agentów, miary autonomii agentów, pół roku pracy z agentami, na jakim etapie jesteśmy, co musi być gotowe przed kodowaniem, co ma być gotowe przed wydaniem, kto zatwierdza przejście dalej, gotowe do wydania, co po wdrożeniu, kiedy projekt jest skończony, praca etapami z agentem, kiedy człowiek sprawdza agenta, czy spełnia to co zamawiał klient, warunki przed wydaniem, podzielić pracę agenta na etapy, patrzeć agentowi na ręce, zadania po kolei zamiast wszystkiego naraz, zmiana kontraktu w trakcie kroku, plan niezgodny z zastanym kodem, nie dokręcaj kodu kolejnymi poleceniami, stan końcowy się zmienia, specification review, does the spec have holes, a panel of spec reviewers, artifact map, which documents in which phase, where to save a document, cut plan, slice order, foundation, where to start delivery, north star, software development lifecycle, process with AI agents, rebuild the delivery process, reviews cannot keep up, process metrics, control bands, from idea to production, maintenance after release, share of PRs written by agents, agent autonomy measures, which stage are we at, what must be ready before coding, what must be ready before release, who approves moving on, ready for release, what after deployment, when is the project finished, working in stages with an agent, when does the human check the agent, does it meet what the client ordered, split agent work into stages, a contract change during a step, the plan no longer matches the code"
---

# The delivery cycle — from an idea to production

The working model: **agents lead and execute, the human approves and is accountable.** The factory takes a project
through all the phases, but at the gates (B1–B6) it stops for the human's decision. The gates are mandatory, not a
courtesy. The agent does not set `accepted` and does not deploy to production itself (core-project-record).

Every phase ends with an artifact in `docs/project/` (core-project-record), not just an answer in the conversation.
Every phase can be a separate session of a different persona. The next session starts with
`python3 .claude/hooks/project_record.py status`, the TL;DR and the Handoff section.

## Who leads
- **The start**: the pack's dispatcher (a persona with `dispatcher: true`, e.g. pack-it: `claude --agent maja`). It
  interviews (core-plan-interview), assesses the scale and the risk, chooses the path (full or shortened) and records
  the phase plan with personas in `01-discovery/brief.md` (the "Phase plan" section). Without a dispatcher: core-problem-routing.
- **The phases**: the human starts the persona named in the Handoff of the previous phase. The persona does the tasks
  itself (core-cost-control §0).
- **The human**: the product owner and the approver. Answers open questions, accepts at the gates, provides accounts,
  secrets and access, starts the production deployment.

## Phases
The table gives roles and skill dimensions; the installed packs provide the personas and skills (`.claude/catalog.md`).
You choose the staffing for the problem; a question outside its own field the persona asks a consultant from another pack.

| # | Phase | Directory | Role | Skill dimension | Output ("done" criterion) |
|---|---|---|---|---|---|
| 0 | Intake and phase plan | `01-discovery/` | dispatcher | core-problem-routing, core-plan-interview, project planning | a brief with the problem, goal, users, scope and "out of scope", constraints (budget, deadline, regulations), the path and the phase plan; with a budget and a deadline a project plan (`project-plan.md`: cost and deadline as P50/P80 ranges, milestones, a risk register) |
| 1 | Product discovery | `01-discovery/` | product/UX designer | product discovery, feature UX design | hypotheses and success metrics, flows and states, mock-ups of key screens, product risks; what to check with real users |
| 2 | Domain | `02-domain/` | domain analyst | domain: Event Storming, strategic split, context map | a glossary, events and processes, contexts and the context map, contradictions and questions for the expert |
| 3 | Requirements | `03-requirements/` | domain analyst + product/UX designer | tactical model, spec-first tests, quality attributes | requirements with acceptance criteria (examples), quality requirements as scenarios, priorities; personal data listed at the requirements it concerns |
| 4 | Architecture | `04-architecture/` | solution architect | architecture: system, stack, quality attributes, threats, privacy | the stack decision, the architecture document (C4), ADRs, the threat model, estimates, the data, deployment and observability strategy; with personal data `privacy.md` (inventory, legal bases, retention, the DPIA decision) |
| 5 | Plan | `05-plan/` | solution architect + test designer | continuous delivery, test design, plan review | vertical slices in order (an end-to-end skeleton as the first step) per `references/cut-plan.md` (foundations with the `Odblokowuje` field, the north star, blocking unknowns); the release plan `release.yaml` (R1 = MVP with an outcome and a metric, lines R2…, flags with rollout stages and a removal date); a test plan with risks, executors |
| 6 | Delivery | `06-delivery/` | implementer per stack + test designer | language, framework, server and UI, tests; core-git-workflow, change review | for every step: code, tests, review, step report; the CI pipeline green from the first step |
| 7 | Release preparation | `06-delivery/`, `07-review/` | DevOps/SRE + security-reviewer + test designer | operations: CI/CD, containers, IaC, releases, observability, supply chain, secrets | environments as code, deployment to the test environment, security review, regression and performance tests, a runbook, the readiness review (`references/production-readiness.md`) |
| 8 | Release and observation | `07-review/` | **the human** deploys; DevOps/SRE prepares and observes | operations: releases, SRE; core-semver | a gradual deployment through the stages from `release.yaml` (every move to the next flag stage is gate B5) with SLO gates, observation after the release, removing flags by `remove_by`, a retrospective and lessons |
| 9 | Maintenance | `08-operations/` | DevOps/SRE + implementer + test designer | SRE, triage, debugging, dependency updates, regression, costs | a periodic maintenance review (`operations-review.md`), bug fixes with a regression test, security patches on time, updates before the end of support, retiring features, costs |

Example (pack-it): Maja → Natalia (pack-ux) → Ewa → Tomasz → Tomasz + Kasia → the executor per stack + Kasia → Piotr.
Staffing with skills: `references/pack-staffing.md` (a domain pack: its `GUIDE.md`).

Documentation is written along the way: the README and how to run it from phase 6, the runbook in phase 7
(pack-docs: docs-tech-writing). Language correction before handing to people (pack-editorial-pl: Stefan, txt-polish-correctness).

## Working with agents — a loop, not a line
When agents write code in hours, planning, review, deployment and maintenance become the slow parts — that is where you
improve the process (`references/ai-native-sdlc.md`, based on the Anthropic playbook and AWS AI-DLC):
- **Every stage ends with an artifact in the repository**, and the next one starts by reading it. The chain: brief
  (intent) → requirements and architecture (specification) → plan → diff with tests → PR with review findings → a
  maintenance record that comes back as a new change brief. The sequence of commits is the audit trail.
- **Nothing without an accepted plan:** a delivery step starts with a plan in plan mode (files, order, tests), recorded
  in the step report before the code; a deviation = an update of the plan in the same commit.
- **The agent checks its own work** with one verification command before a human sees it; a bug fix starts with a red
  test that the agent does not weaken (`tdd_guard`, rules A–C).
- **Evaluations of the agent configuration** (real tasks with an expected result) at every change of `CLAUDE.md`,
  skills, hooks and the model; every incident adds a scenario.
- **The agent does everything up to the production gate and nothing past it:** an AI review of the PR per `REVIEW.md`;
  the human approves merging and deployment, the agent does not approve its own code.
- **Maintenance through control bands** (`scripts/control_band.py`): deterministic detection, a graded reaction
  (a record → a read-only diagnosis → a PR or an approved runbook).
- **An agent mistake repeated a second time** → the fix goes into `CLAUDE.md` (with the human's consent).

## Human gates
| Gate | After phase | The human approves | Without approval |
|---|---|---|---|
| **B1** Scope | 0–1 | the problem, goal, success metrics, scope and "out of scope", budget | further work only as `draft` |
| **B2** Requirements | 3 | requirements and acceptance criteria, quality requirements, priorities | the architecture marked "based on a proposal" |
| **B3** Architecture | 4–5 | the stack, key ADRs, the threat model, the maintenance cost, the plan | delivery does not start (except a skeleton to verify a risk, with consent) |
| **B4** Readiness | 7 | the result of the readiness review, risks accepted consciously, the decision "we release / we do not release" | no release |
| **B5** Release | 8 | starting the production deployment, every move to the next rollout stage from `release.yaml` (the exit criterion met and the minimum time passed) and a possible rollback | the agent only prepares |
| **B6** Maintenance | 9 (periodically) | fix priorities, patch deadlines, updates to perform, features to retire, the maintenance budget | proposals wait; critical patches per the arrangement with the human |

Between the gates the human answers open questions. The agent does not guess business or legal decisions; it records
them as a question with an addressee. Every change of an accepted artifact is a new version and a new acceptance.

## Phase 9 — maintenance
A release does not end the project. Maintenance is a steady rhythm, not a reaction to failures:
- **The cycle:** a maintenance review every week or every sprint (`08-operations/<data>-operations-review.md`, the
  `operations-review` template) — SLOs and incidents, issues by severity, patches, updates, costs, features to retire.
  You check metrics (the 5xx rate, test failures, PR cycle time) with control bands:
  `python3 .claude/skills/core-delivery-lifecycle/scripts/control_band.py metryka.csv --baseline 30 --side upper`.
  The human approves the review's decisions (**B6**).
- **Issues:** review and categories; a bug → the cause → a red regression test → the fix → a release as in phases
  7–8, at the scale of a fix (the shortened path; B4 and B5 stay).
- **Security patches:** a critical vulnerability in a component exposed to the outside has a fast path with an exception
  from the cooldown (the supply-chain skill). The human sets the deadline.
- **Dependency updates:** minor ones regularly, major ones before the end of support, one at a time and with a plan.
  The agent does not bump dependencies unasked — the maintenance review contains proposals for approval.
- **Retiring features and the end of life of the system:** the human's decision; the course in `references/maintenance.md`.

## The shortened path (a small project, low risk)
Criteria: one team, a few screens or endpoints, no sensitive data and no regulations, an easy rollback.
Phases 0–1 together in one brief, phase 2 skipped (the glossary in the brief), 3–5 in one document (requirements with
examples + a short architecture + the plan), gates B1+B2+B3 as one acceptance. **B4 and B5 always stay**, and the
readiness review in the shortened version (the sections marked "minimum" in `production-readiness.md`).

## Rules of the course
- **The skeleton first**: the first delivery step goes through all the layers and the pipeline up to the test
  environment. Deployment problems come out in the first week, not in the last.
- **The risk first**: the least certain elements (an external integration, performance, a new technology) you check
  with a prototype before B3 or in the first steps.
- **Tests from the requirements**: test cases from the acceptance criteria are written before the code or in parallel
  (the test designer in a clean room), not from the code.
- **A measurable end of a step**: a delivery step ends with a command that gives a "passes / fails" result (tests from
  the acceptance criteria, build, lint). For a longer step the human can set `/goal` with such a condition,
  e.g. `/goal step 3 tests pass (npm test exits with code 0), other tests unchanged, or stop after 30 turns`.
  The judging model sees only the conversation, so the agent shows the command's output instead of writing "it works".
  After it passes comes a review in a fresh context (`/code-review` or security-reviewer), because the author does not
  judge their own work.
- **No silent scope changes**: a new requirement during delivery goes back to phase 3 as a new version.
- **A contract change during a step = stop.** A small difference (another file name, another export) you adjust and
  record in "Deviations". When the end state or the contract surface changes (the assumed model is missing, two
  authentication paths instead of one, a product decision is needed, 10 modules instead of 3 files), stop and show
  "Expected / Found / Why it matters" with a choice: adjust and continue · skip · stop and fix the plan.
  Do not tighten the code with further commands.
- **A step plan sized to the risk:** the more files and the higher the risk, the more careful the plan and its review
  (the change-review skill); a simple change with a clear scope is plan → delivery, without research as a ritual.
- **Cost**: cheap models for searching and mechanical changes, expensive ones for architecture and the security review.
  At the end of a stage: cost and time from `.tf/factory/cost_stats.py`, causes and proposed changes from core-agent-retro.
- **The state always in files**: an interrupted session leaves `draft` and the Handoff. `project_record.py report` gives
  the human one file with the project's state.

## What the factory will not do by itself
Business, legal and risk decisions; tests with real users; creating accounts, domains, payments and contracts;
providing secrets; penetration tests without written consent to the scope; the production deployment; bumping
dependencies unasked. All of this is in the phase plan as tasks for the human with a deadline.

## More
- The artifact map (phase → file → who writes → skill → who reads, what to skip in a small project): `references/artifact-map.md`.
- The definition of "production ready" and the readiness review: `references/production-readiness.md`.
- A dry run on a small project (how to check whether the factory delivers): `references/dry-run.md`.
- Retiring features and shutting down the system (phase 9): `references/maintenance.md`.
- The specification review before the plan (a panel of 2–3 independent reviewers, a gate): `references/spec-review.md`.
- The cut plan — the order of items, foundations, unknowns, self-check: `references/cut-plan.md`.
- The AI-native loop: artifacts, measures of every stage, evaluations, PR review, control bands, the source of truth,
  managed settings, AI-DLC, refinement with the solution told back and autonomy measures paired with an outcome measure:
  `references/ai-native-sdlc.md`.

## Checklist
- [ ] the path (full or shortened) and the phase plan recorded in the brief after phase 0
- [ ] every phase finished with an artifact with a TL;DR, open questions and a Handoff
- [ ] gates B1–B6 approved by the human and recorded in `decisions.md`
- [ ] an end-to-end skeleton as the first delivery step
- [ ] a readiness review before the release, risks accepted explicitly
- [ ] an agent retrospective (core-agent-retro) and lessons after the release
- [ ] after the release: a periodic maintenance review with the human's decisions (B6)

## Sources
- Factory conventions: core-project-record
- Google SRE — Production Readiness Review; J. Humble, D. Farley, *Continuous Delivery*; A. Cockburn — walking skeleton
- GOV.UK Service Manual — the live and retirement stages (shutting down a service)
- The 10xDevs course, ed. 3 (2026), module 2, lessons 1–2 (the cut plan, stopping the implementation) — training material (accessed 2026-10-09)
- Anthropic, "The AI-Native SDLC Playbook" (21.08.2026) and the Anthropic Academy course; AWS, "AI-Driven Development Life Cycle" (31.07.2025)
Described in our own words.
