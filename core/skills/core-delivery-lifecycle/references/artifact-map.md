# The artifact map

> **Contents:** Permanent files (the whole project) · 0. Reconstructing existing code (before changes in an… · 1. Intake, the phase plan and product discovery —… · 2. Domain — `02-domain/` · 3. Requirements — `03-requirements/` · 4. Architecture — `04-architecture/` · 5. Plan — `05-plan/` · 6–7. Delivery and release preparation — `06-delivery/` · 7–8. Reviews, release, observation — `07-review/` · 9. Maintenance — `08-operations/` · Outside `docs/project/` · How to use it

Where the result of every phase lies, who writes it, which skill leads the work and who reads it later. Paths are
relative to `docs/project/` (the project record, core-project-record) unless stated otherwise. A skill with a pack
works only when the pack is installed (`.claude/catalog.md`). The "Small project" column says when the artifact can be
skipped on the shortened path. You record a skip in one sentence in the phase's Handoff, so that the next persona does
not look for a file that does not exist.

The overriding rule: an artifact is written when someone will read it and make a decision based on it. An empty
template is not an artifact.

## Permanent files (the whole project)
| Artifact | Writes | Skill | Reads / what for | Small project |
|---|---|---|---|---|
| `journal.md` | every persona (appends) | core-project-record | the next session: what happened | always |
| `decisions.md` | a persona at a human's decision | core-project-record | everyone: the D-NNN decision register | always |
| `lessons.md` | a persona after a recurring trap | core-agent-retro, core-project-record | every session at the start | when there is a lesson |
| `questions.md` | the dispatcher, personas | core-problem-routing | the human: open questions | when there are questions |
| `wip/<nazwa>.md` | a persona on a task longer than a few steps | core-project-record | the same persona after a break | always on a long task |
| `archive/research/<RRRRMMDD>-<temat>.md` | a persona researching facts | core-source-research, core-knowledge | the author of the decision that rests on them | when sources were researched |
| `archive/retro/<RRRRMMDD>-retro.md` | a persona after a stage | core-agent-retro | the next stage | after every stage |
| `exports/report-<data>.md`, `exports/handoff-<data>-<temat>.md` | generated | core-project-record | people outside the repo, another agent | on request |

## 0. Reconstructing existing code (before changes in an unknown repo)
| Artifact | Writes | Skill | Reads / what for | Small project |
|---|---|---|---|---|
| `00-reconstruction/report.md`, `00-reconstruction/plan.md`, `00-reconstruction/manifest.json` | architect / analyst | eng-project-reconstruction (pack-it) | every persona before a change | skip in a new project |
| `00-reconstruction/domain.md`, `00-reconstruction/standards/INDEX.md` | as above | eng-project-reconstruction (pack-it) | the `/tf-task` loop before a story (the tf skill) | skip in a new project |

## 1. Intake, the phase plan and product discovery — `01-discovery/`
| Artifact | Writes | Skill | Reads / what for | Small project |
|---|---|---|---|---|
| `01-discovery/brief.md` | the dispatcher | core-plan-interview, core-problem-routing; proc-requirements-shaping (pack-it) | all phases: the problem, goal, scope, phase plan | always (can be short) |
| `01-discovery/project-plan.md` | the dispatcher / architect | proc-project-planning (pack-it) | the human: cost and deadline P50/P80, risks | skip without a budget and a deadline |
| `01-discovery/pre-flight.md` | the domain analyst | ddd-discovery-intake (pack-it) | the decision "whether to modularise" | skip with one module |
| `01-discovery/research-plan.md`, `01-discovery/research-report.md` | the UX researcher | ux-research-methods (pack-ux) | the product designer: what we know about users | skip without research |
| `01-discovery/service-blueprint.md` | the service designer | ux-service-design (pack-ux) | product and operations: the service backstage | skip without a multichannel service |
| `01-discovery/ux-maturity.md` | the design lead | ux-design-leadership (pack-ux) | management: UX maturity | rarely needed |

## 2. Domain — `02-domain/`
| Artifact | Writes | Skill | Reads / what for | Small project |
|---|---|---|---|---|
| `02-domain/glossary.md` | the domain analyst | ddd-event-storming, ddd-facilitation (pack-it); correction txt-polish-correctness (pack-editorial-pl) | everyone: the ubiquitous language | always, even 10 terms |
| `02-domain/corpus.md`, `02-domain/contradictions.md`, `02-domain/strategic-gaps.md` | the domain analyst | ddd-discovery-intake (pack-it) | the analyst: the bank of evidence and contradictions | when there are raw materials |
| `02-domain/strategic.md`, `02-domain/context-map.md` | the domain analyst | ddd-strategic-analysis, ddd-context-mapping (pack-it) | the architect: context boundaries | skip with one context |
| `02-domain/event-storming/<id>/` | the facilitator | ddd-event-storming (pack-it) | the analyst: events and processes | skip when the process is simple |
| `02-domain/concepts/<pojecie>.md` | the domain analyst | ddd-deep-modeling (pack-it) | the implementer: a difficult concept | only difficult concepts |
| `02-domain/archetypes/<archetyp>-<obszar>.md` | the domain analyst | ddd-archetypes (pack-it) | the architect, the implementer | when an archetype fits |
| `02-domain/archetypes/lookup-<data>.md` | the domain analyst | ddd-archetype-lookup (pack-it) | the analyst, the architect: where existing code would gain from an archetype, in which order | existing code only |
| `02-domain/algorithms.md` | the domain analyst | ddd-algorithm-recognition (pack-it) | the implementer: a hidden algorithmic problem | when there is one |
| `02-domain/connascence/<a>-<b>.md`, `02-domain/connascence/<a>-<b>.frame.md` | the domain analyst | ddd-connascence-analysis (pack-it) | the architect: the cost of coupling | in a dispute about boundaries |
| `02-domain/stress/<metryka>.md`, `02-domain/_blind/brief.md`, `02-domain/_blind/competitors.md` | the analyst + the blind analyst | ddd-model-stress-test (pack-it) | the architect: will the model withstand the requirements | skip |
| `02-domain/acl-<pakiet>.md`, `02-domain/distillation.md`, `02-domain/invariant-<nazwa>.md` | the domain analyst | ddd-legacy-modernization (pack-it) | the implementer during modernisation | legacy only |
| `02-domain/experiment-<nazwa>.md` | the AI researcher | ai-research-methods (pack-it) | the decision on the ML approach | ML research only |

## 3. Requirements — `03-requirements/`
| Artifact | Writes | Skill | Reads / what for | Small project |
|---|---|---|---|---|
| `03-requirements/requirements.md` | the analyst + the product designer | proc-requirements-shaping, qa-test-design, ai-product-management (pack-it) | the test designer (tests from the criteria), the architect, the implementer | always |
| `03-requirements/spec-review.md` | the reviewer panel | core-delivery-lifecycle (`references/spec-review.md`) | the human at the gate before the plan | skip on the shortened path |
| `03-requirements/ia-documentation.md` | the information architect | ux-information-architecture (pack-ux) | the UI designer, the frontend implementer | skip with a few screens |

## 4. Architecture — `04-architecture/`
| Artifact | Writes | Skill | Reads / what for | Small project |
|---|---|---|---|---|
| `04-architecture/stack-decision.md` | the solution architect | arch-tech-selection (pack-it) | the skeleton generator (eng-repo-readiness, pack-it), the implementer | always, briefly |
| `04-architecture/architecture.md` | the solution architect | core-project-record (template); arch-system-design (pack-it) | everyone: C4, the data and deployment strategy | one paragraph + a diagram |
| `04-architecture/design-<slug>.md` | the agent with the developer, stage by stage | tf-design | the developer, the `/tf-task` loop (the Handoff section as the story) | when the design was worked out in a session |
| `04-architecture/adr/NNNN-short-title.md` | the architect | core-project-record (the `adr` template); docs-tech-writing (pack-docs) | future authors of changes: why so | when the decision is costly to reverse |
| `04-architecture/erd.md` | the architect / the backend implementer | be-database (pack-it) | the implementer, the data analyst, the migration review | when there is a relational database |
| `04-architecture/threat-model.md` | the architect + security | arch-threat-modeling (pack-it) | the security-reviewer, the implementer | with sensitive data or internet access |
| `04-architecture/privacy.md`, `04-architecture/data-inventory.md` | the architect | arch-privacy-compliance (pack-it) | the human with the DPO, the implementer: field classes, retention | always with personal data |
| `04-architecture/<data>-legal-map.md` | the architect | arch-eu-product-law (pack-it) | the human with a lawyer | when the product falls under EU law |
| `04-architecture/compliance.md`, `04-architecture/risk-register.md`, `04-architecture/eu-cyber-regulations.md` | the security architect | sec-governance-compliance, sec-risk-management, sec-eu-regulations (pack-it) | management, the auditor | when there are formal requirements |
| `04-architecture/zero-trust.md`, `04-architecture/cloud-security-baseline.md`, `04-architecture/landing-zone.md` | the security / cloud architect | sec-zero-trust-identity, sec-cloud-security, ops-cloud-landing-zones (pack-it) | DevOps, security | skip outside a corporate cloud |
| `04-architecture/ai-architecture.md`, `04-architecture/ai-compliance.md` | the AI architect | arch-ai-solutions, ai-governance-compliance (pack-it) | the implementer of AI features, the human | only with an AI component |
| `04-architecture/codebase-map.md`, `04-architecture/legacy-dossier/README.md` | the architect | eng-codebase-mapping, eng-legacy-dossier (pack-it) | the implementer in unknown code | existing code only |
| `04-architecture/context-architecture.md` | the author of the agent instructions | core-agent-instructions | the author of CLAUDE.md / AGENTS.md | with large instructions |
| the API contract (OpenAPI) — **in the code repository**, next to the service, not in the record | the architect + the implementer | be-api-design (pack-it) | API clients, the contract test in CI | when there is an API for others |

## 5. Plan — `05-plan/`
| Artifact | Writes | Skill | Reads / what for | Small project |
|---|---|---|---|---|
| `05-plan/plan.md` | the architect + the test designer | core-delivery-lifecycle (`references/cut-plan.md`) | executors: slices in order | always |
| `05-plan/release.yaml` | the architect | core-delivery-lifecycle (`references/cut-plan.md`) | DevOps at the release, gates B5 | skip with one release without flags |
| `05-plan/test-plan.md`, `05-plan/test-strategy.md` | the test designer | qa-test-design, eng-local-quality-gates (pack-it) | the implementer, the change review | test-plan always; the strategy with many layers |
| `05-plan/migration-plan.md` | the cloud architect | ops-cloud-migration (pack-it) | DevOps, the human: waves and cutover | migration only |

## 6–7. Delivery and release preparation — `06-delivery/`
| Artifact | Writes | Skill | Reads / what for | Small project |
|---|---|---|---|---|
| `06-delivery/NNN-<slug>.md` | the step executor | core-project-record (the `delivery` template) | the review, the next step | always (the step report) |
| `06-delivery/NNN-behavior-contract.md` | the refactoring executor | eng-behavior-preserving-refactoring (pack-it) | the review: behaviour unchanged | refactoring only |
| `06-delivery/bootstrap-verification.md` | the skeleton executor | eng-repo-readiness (pack-it) | the human: does the skeleton work | a new project |
| `06-delivery/deploy-plan.md` | DevOps | ops-release-engineering (pack-it) | the human deploying | a simple deployment without stages |
| `README.md`, `CHANGELOG.md` — **in the repository root** | the implementer / tech writer | core-semver; docs-tech-writing (pack-docs) | users and newcomers | always |
| the runbook — **next to the service or in the operations documentation** | DevOps/SRE | ops-sre-incidents (pack-it); docs-tech-writing (pack-docs) | the on-call person | when the service has on-call |
| the "Change risk" section in the PR description | generated (`tf risk --md`) | core-git-workflow | the reviewer: what the human must see | every PR |

## 7–8. Reviews, release, observation — `07-review/`
| Artifact | Writes | Skill | Reads / what for | Small project |
|---|---|---|---|---|
| `07-review/<data>-readiness.md` | DevOps + security + the test designer | core-delivery-lifecycle (`references/production-readiness.md`) | the human at the release gate | always before production |
| `07-review/<data>-dry-run.md` | the dispatcher | core-delivery-lifecycle (`references/dry-run.md`) | the human: does the factory deliver | once |
| `07-review/<data>-<rodzaj>.md` (security, architecture, retro, tests) | the reviewer of that kind | security-reviewer; core-agent-retro | the human, the next phase | by risk |
| `07-review/<data>-repo-readiness.md` | the repo auditor | eng-repo-readiness (pack-it) | the human, the author of CLAUDE.md: fixes for agents | when taking over a repo |
| `07-review/<data>-code-audit.md`, `07-review/<data>-code-audit-inventory.md` | the audit team | eng-code-audit (pack-it) | the human: a ranking of problems | on request |
| `07-review/<data>-tech-debt.md` | the auditor | eng-tech-debt-audit (pack-it) | the human: debt priorities | on request |
| `07-review/<data>-deep-dives.md` | the architect | eng-module-depth (pack-it) | the implementer: shallow modules | on request |
| `07-review/<data>-plan-review-<krok>.md` | the change reviewer | qa-change-review (pack-it) | the executor before delivery | for a risky step |
| `07-review/<data>-facilitation.md` | the facilitation coach | ddd-facilitation (pack-it) | the facilitator | after a workshop |
| `07-review/<data>-language-<dokument>.md` | the editor | txt-polish-correctness (pack-editorial-pl) | the document's author | documents for people |

## 9. Maintenance — `08-operations/`
| Artifact | Writes | Skill | Reads / what for | Small project |
|---|---|---|---|---|
| `08-operations/<data>-<rodzaj>.md` (the periodic review from the `operations-review` template, patches, updates, retirements) | DevOps/SRE + the implementer | core-delivery-lifecycle (`references/maintenance.md`) | the human: what needs a decision | a review every quarter |

## Outside `docs/project/`
| Artifact | Writes | Reads / what for |
|---|---|---|
| `.tf/reports/<moduł>.md` and `.tf/register/items.jsonl` | `tf analyze` (scripts) | a persona at the review and the fix plan; ticks stay at a repeated analysis |
| `.tf/reports/metrics.md` | `tf metrics` | the human: the factory's effectiveness (reverts, cost per accepted change, causes of fixes) |
| `.tf/logs/` (`usage.jsonl`, `hook-errors.jsonl`) | hooks | `cost_report.py`, `tf doctor` |
| `docs/project/changes/CHG-n/` | modes with a change cycle (e.g. mode-pdi) | the mode's personas: the plan and decisions of one change |
| `docs/project/vendors/` | the hardware personas of a domain pack | onboarding of a device model |
| `CLAUDE.md` / `AGENTS.md` | the author of the instructions (core-agent-instructions) | every agent in every session |

## How to use it
- **A persona at the start of a phase** reads the rows of its phase and the Handoff of the previous one. A missing
  required file from the previous phase is a question for the human, not a reason to guess it.
- **A persona at the end of a phase** checks its rows: every artifact is saved or described in the Handoff as skipped,
  with a reason.
- **A new skill** saves its result in an existing phase directory and adds a row to this map. The factory repository's
  test (`tests/test_artifact_map.py`) checks that the directory exists and the artifact is in the map.
