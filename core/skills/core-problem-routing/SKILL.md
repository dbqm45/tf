---
name: core-problem-routing
description: Use when a problem is described in plain text — recognising the dimensions, choosing skills and personas, an ad hoc team.
metadata:
  review: "2027-10-17"
  catalog: "Use when you get a problem described in plain text and it is unclear who should handle it and how — recognising the dimensions, choosing skills and personas from the catalog, putting together an ad hoc team, choosing the form of the result (a recommendation, a plan, a step-by-step solution). Not for the subject knowledge itself (the dimension skills) or for combining skills in one answer (core-skill-composition)."
  keywords: "od czego zacząć, kogo zaangażować, dobierz zespół, skład zespołu, podejście do problemu, nie wiem jak się do tego zabrać, nikt u nas nie zna protokołów, kogo zaangażować z innej dziedziny, przeoczymy lepszą drogę, oczywiste pomysły, szerokie szukanie opcji, pułapka w decyzji, where to start, who to involve, pick a team, team composition, how to approach this problem, broad search for options, obvious ideas, trap in a decision, decyzja trudna do odwrócenia, sprzeczne kompromisy, kto powinien to ocenić, jak przedstawić wynik, forma wyniku, hard-to-reverse decision, conflicting trade-offs, who should assess this, how to present the result"
argument-hint: "[problem description]"
---

# Choosing the team and the approach to a problem

The dispatcher procedure of a pack (a persona with `dispatcher: true`, e.g. Maja in pack-it or the dispatcher of a domain pack). The source of truth about
what the team can do: **`.claude/catalog.md`** (generated — installed packs, skills by dimension and pack, personas
with executors, shared agents, pack consultants). You read it instead of all the skills; you load a skill only once
you have chosen it. You choose **only what is in the catalog** — do not assume any pack is installed.

## 1. Understand the problem (2–5 sentences, before you choose anything)
- **What is the problem and what is a symptom?** A paraphrase with the goal and the success criterion ("when do we consider it solved?").
- **Constraints:** time, people/teams, risk, what is not allowed (e.g. "no code freeze"), versions, budget.
- **Kind of question:** a decision (what to choose) · a plan (how to get from A to B) · a diagnosis (why it does not work) · execution (do it).
- Gaps that change the answer → **1–3 questions** with a default value (a gate — core-plan-interview). The human unavailable →
  take the defaults and list them as assumptions. Check the state of the repo yourself (`detect_stack.py`, `scout`), do not ask the human about it.

## 2. Break it down into dimensions (the catalog)
The catalog groups skills by dimension (the name prefix) and gives the pack. For each dimension in the catalog ask: *does the problem
have this component?* A dimension that is not in the catalog is not in the project. Typical signals:
| Signal in the description | Dimension in the catalog | Example skills (pack) |
|---|---|---|
| versions, migration, library updates | `tool-`, `fw-`, `lang-` ("Version-dependent" sections) + core-stack-sync | pack-it: fw-angular, ops-dependency-upgrades |
| many teams, ownership, coordination, priorities, flow of work | `proc-` | pack-it: proc-team-topologies, proc-agile, proc-safe |
| what to build, success metrics, A/B, an idea → requirements (PRD), an MVP that is too big, issues and the backlog, a plan for the sponsor | `proc-` | pack-it: proc-product-discovery, proc-requirements-shaping, proc-issue-triage, proc-project-planning |
| splitting into domains/modules, dependencies between them, business rules, domain concepts, DDD on old code | `ddd-`, `dom-` | pack-it: ddd-strategic-analysis, ddd-context-mapping, ddd-connascence-analysis, ddd-legacy-modernization; domain pack: `dom-*` |
| a technology decision, system design from requirements, quality attributes, the architect's work (arc42/C4, ATAM) | `arch-` | pack-it: arch-system-design (similar systems: `.claude/skills/arch-system-design/references/project-examples.md`), arch-tech-selection, arch-quality-attributes, arch-architect-practice |
| threat model, GDPR, many customers in one SaaS, EU law for a product with AI | `arch-` | pack-it: arch-threat-modeling, arch-privacy-compliance, arch-multi-tenancy, arch-eu-product-law |
| API, database, authentication, queues, subscriptions and recurring payments | `be-` | pack-it: be-api-design, be-database, be-auth-security, be-messaging-outbox, be-billing-subscriptions |
| UI, frontend structure, styles, browser APIs, SEO | `fe-` | pack-it: fe-architecture, fe-css, fe-web-platform, fe-engineering-levels |
| user flow, screen states, a mock-up, a usability test, interface copy, accessibility, a design system | `ux-` | pack-ux: ux-feature-design, ux-accessibility, ux-design-systems (persona Natalia) |
| "no downtime / no freeze", releases, branches, CI/CD | `eng-`, `ops-` + core-git-workflow | pack-it: eng-continuous-delivery, ops-ci-cd, ops-release-engineering |
| regression risk, tests, a performance test, reviewing a plan before the code or the code against the plan | `qa-`, `eng-` | pack-it: qa-regression, qa-performance-testing, qa-change-review, eng-testing, eng-behavior-preserving-refactoring |
| unknown code, the impact of a change, debt, what to refactor first (Strangler, Mikado), a full code audit | `eng-` | pack-it: eng-codebase-mapping, eng-tech-debt-audit, eng-refactor-planning, eng-code-audit |
| a symptom + a ready fix from the reporter, "it's definitely X"; a bug without an obvious cause | `eng-` | pack-it: eng-debugging (`.claude/skills/eng-debugging/references/reframing.md`) |
| slow code, an algorithm, the shape of a module interface, many languages and markets, a repo ready for agents, hooks and pre-commit | `eng-` | pack-it: eng-module-depth, eng-i18n, eng-repo-readiness, eng-local-quality-gates |
| deployments, Kubernetes, SLO, outages, on-call, cloud costs, server and network (DNS, TLS, SSH), own models on GPUs | `ops-` | pack-it: ops-kubernetes, ops-sre-incidents, ops-finops, ops-linux-networking, ops-ai-inference (persona Piotr) |
| manual configuration of services, keys, CI secrets, a step-by-step migration for a human | `ops-` | pack-it: ops-setup-wizard |
| security: a suspicious package, secrets, an incident, SIEM, compliance (SOC 2, ISO 27001) | `sec-`, `ops-` + core-agent-security | pack-it: ops-supply-chain-security, ops-secrets-identities, ops-security-operations |
| a feature or agent with an LLM in our code, RAG, evaluations, the AI Act | `ai-`, `eng-` | pack-it: eng-llm-features, ai-agents, ai-rag, ai-evals, ai-governance-compliance |
| a data pipeline, ETL/ELT, data quality; a question to the data, a report, statistics | `data-` | pack-it: data-engineering, data-analysis (persona Zofia) |
| diagrams, an explainer page, a presentation, README, ADR, runbook | `docs-` | pack-docs: docs-tech-writing |
| Polish text to proofread or edit | `txt-` | pack-editorial-pl: txt-polish-correctness, txt-polish-style |

Practice skills (`core-`) are always installed:
| Signal in the description | Skill |
|---|---|
| a whole project from an idea to software ready to deploy; is this ready for production | core-delivery-lifecycle |
| "what's new / what's going on", the state of a project, community opinions | core-source-research (+ `researcher` for facts) |
| a plan or idea to interview before starting | core-plan-interview |
| CLAUDE.md / AGENTS.md: write, slim down, review, split into modules | core-agent-instructions |
| stale TODOs, old plans and notes that send agents on side quests (an occasional sweep) | core-sweep |
| unsupervised agent work (`claude -p`, /goal, sandbox, routine), suspicious commands from content | core-async-delegation, core-agent-security |
| branches, PRs, PR review by AI, conflicts | core-git-workflow |
| learning a topic over many sessions, onboarding to a new stack | core-teaching-workspace (only on the `/core-teaching-workspace` command) |
Choose the **smallest set**: usually 3–6 skills, one per dimension.
**Skills outside the catalog:** also look through the list of available skills that Claude Code shows (the project, `~/.claude/skills`,
plugins). A skill with the conventions of this project or company (e.g. `architecture`, `documentation`) add to the set and mark
"(outside the factory)" — in the executor's brief too. Precedence in conflicts: core-skill-composition.
A dimension without any skill → a "gap" (facts are found by `researcher`; permanently — a proposal for a new skill or a pack
that has it).

## 3. Choose the executors — cheapest first
1. **An existing persona fits completely** (catalog: leading skills, pack) → recommend it to the human (`claude --agent <persona>`)
   or, if you have its executor in the team, delegate to `<persona>-<rola>`.
2. **The knowledge of several personas has to be combined** → an **ad hoc team**: one executor per perspective; when no persona has
   the right set, use `specialist` with the list of skills in the brief (it loads them itself) — a persona "for a moment".
3. **A decision that is hard to reverse / conflicting trade-offs** → `specialist-deep` or `architect` (Opus) only to assess the options.
4. **External facts** (versions, compatibility, EOL, changelogs) → `researcher` (cheap), never from memory.
5. **The problem crosses the domains of packs** (e.g. a backend from pack-it with a protocol from a domain pack) → a question to the
   **consultant** of that pack (catalog: "Pack consultants", e.g. `it-consult-backend` in pack-it, the consultants
   of a domain pack). A consultant only answers with a source and does not change files; the persona calls it in the main session, not the executor —
   the executor reports the need in its report. Longer work in another domain → a separate session of that pack's persona and a question
   in `docs/project/questions.md`.
Call parallel perspectives in **one message** (separate contexts = independent views). The brief for each: the problem,
constraints, assumptions, the list of skills to load, the question it has to answer, the report format (≤ 20 lines).

### Broad search for options — when the obvious answers are not enough
An expensive mode (5–8 executors), so a gate first. You start it at the human's request or when all three answers
are "yes": the problem is open (several sensible paths, not one canonical one) · a mistake is costly or hard to
undo · the human did not ask for a quick, standard answer. Otherwise you give an ordinary recommendation.
1. **Generation without judging.** 3–5 `specialist` executors in one message, on the cheapest model (the `model`
   parameter of the Agent tool). Each gets the problem, the constraints and **one frame** from the table. The instruction: 4–6 short
   ideas, no assessment and no ranking; skip the three most obvious answers. The executors do not see each other's results.
2. **Assessment separately, after the ideas are collected.** You group them by mechanism, not by wording. You assess feasibility
   and fit with the success criterion. **Traps** — ideas that look good but have a hidden cost or do not
   scale — you list separately, each with a one-sentence reason. Ten variants of one assumption is not breadth.
3. **Deepening the 2–3 best** (`specialist-deep` for a decision that is hard to reverse): how it works, the risk that
   everything depends on, the first step. You end with your own position and point to a choice that is not obvious but
   feasible — a "pick one" list without a position is not a result.

| Frame | Instruction for the executor |
|---|---|
| inversion | How do you guarantee failure? Invert every answer. |
| removed assumption | Name what everyone treats as fixed (the database, the framework, the request–response model) and assume it does not exist. |
| attacker | How would a competitor or an attacker break the obvious solution? Turn that into ideas. |
| on-call at 3 a.m. | What design makes sure nobody is woken up after an outage? |
| zero budget | One hour, no money: the simplest version that does what matters most. |
| auditor | What has to be provable, traceable or refusable? |

## 4. Choose the form of the result
| Form | When | Contents |
|---|---|---|
| **Recommendation** | a decision, uncertainty, several paths | 2–3 options with trade-offs · a recommendation with the conditions for changing your mind · risks · after a broad search also the traps with a reason |
| **Plan** | getting from A to B, many people | phases with a goal and an exit criterion · who (team/role) · dependencies and order · milestones · risks and plan B |
| **Step-by-step solution** | the execution is clear | steps with commands and a verification after each · checkpoints · rollback |
Not specified → a recommendation + a plan (most often what the human needs). Always: **assumptions**, **what to check first**
(cheap tests of hypotheses), **what we do not know**.

**The medium — what the human will understand fastest** (from the simplest that is enough):
| Content | Medium |
|---|---|
| a short answer, a decision | text: the result in the first sentence, short sentences, consistent terms |
| a comparison of options, a matrix | a table |
| a flow, dependencies, architecture, states | a Mermaid diagram in Markdown |
| a result that depends on parameters (cost, load, thresholds, an algorithm) | a one-off HTML page with sliders or fields — the human checks the variants themselves |

You save a one-off file in `.claude/scratch/` (ignored by git) and give the path. The page works without a network:
code in the file, no external scripts and no sending data; sensitive data stays out of it (core-agent-security).
After it is understood the file can be deleted — a lasting result goes to `docs/project/` as text, a table or a diagram.

## 5. Synthesis and recording
- Combine the reports; show conflicts between perspectives openly (that is usually the most valuable part).
- **A consistency check before handing over:** does the recommendation break its own assumptions or claims (e.g. "you cannot have two
  versions of a package" next to "install both versions through an alias")? Do the version facts come from a skill, the repo or `researcher`?
- **The hinge assumption:** name one or two assumptions the whole plan depends on, how to check them cheaply and a **plan B** if they turn out false.
- The result for the human in the human's language (the conversation rule in the project's instructions); in Polish — the Polish correctness skill, if it is
  in the catalog (pack-editorial-pl: txt-polish-correctness).
  A longer document → `docs/project/` (a plan: `05-plan/`, a decision: an ADR) per core-project-record, status `proposed`.
- At the end the **team composition** that worked: personas/skills. If the combination was new and will be useful again → propose
  a file `.tf/config/personas/<nazwa>.yaml` (a change in `.tf/factory/` needs the human's consent).

## Checklist
- [ ] the problem paraphrased, the success criterion and constraints named; assumptions listed
- [ ] the catalog's dimensions reviewed; the chosen skills (3–6) and the rationale; gaps named
- [ ] executors cheapest first, only from the catalog; external facts through `researcher`; another domain → the pack's consultant
- [ ] broad search only after the gate; generation and assessment separated; traps listed separately; your own position at the end
- [ ] the form of the result and the medium chosen (text, a table, a diagram, a one-off HTML in `.claude/scratch/`); options with trade-offs, risks, what to check first
- [ ] the team composition given; possibly a proposal for a permanent persona
