# Enterprise architecture and management frameworks — an overview

Frameworks give a shared vocabulary and process in large organizations. The agent does not implement frameworks — it helps translate the team's work
into the language the organization expects (e.g. TOGAF artifacts, ITIL processes), and the other way round.

## Enterprise architecture
| Framework | What it is | When it is useful |
|---|---|---|
| **TOGAF** (The Open Group; 10th edition from 2022, modular) | an architecture development method (ADM): the preliminary phase and vision → business, information systems (data and applications) and technology architecture → opportunities and solutions → migration planning → implementation governance → change management; requirements management at the centre | the organization runs EA by TOGAF; the project must be placed in the portfolio and pass architecture governance |
| **ArchiMate** (The Open Group) | an enterprise architecture modelling language: the business, application and technology layers, motivation and strategy, the relations between them | models for EA and architecture governance; for development teams C4 is usually enough |
| **Zachman** | a taxonomy (a matrix of what/how/where/who/when/why questions × perspectives), not a method | organizing existing documentation |
| **IAF** (Capgemini) | a framework covering the business, information, information systems and infrastructure domains, at several levels of abstraction | organizations working in this methodology |
Shared artifacts worth knowing: a business capability map (what the organization can do, independent of the systems),
an application map with a lifecycle (invest / maintain / retire), architecture principles, a roadmap and transition
architectures. Business capabilities map well onto DDD subdomains (ddd-strategic-analysis).

## Business analysis
**BABOK** (IIBA) — the business analyst's body of knowledge: analysis planning, elicitation and collaboration with stakeholders,
requirements lifecycle management, strategy analysis, requirements analysis and definition, solution evaluation. Counterparts
in the factory: ddd-discovery-intake, ddd-facilitation, proc-product-discovery, qa-test-design (acceptance criteria).

## Service and project management
| Framework | What it is | Touchpoint with the factory |
|---|---|---|
| **ITIL 4** | IT service management practices: among others incident, problem and change management (in ITIL 4: change "enablement"), service level, release management | incidents and postmortems (ops-sre-incidents) = incident and problem; SLA and SLO; a standard change = an automated deployment with gates (ops-release-engineering) |
| **PRINCE2** | a project management methodology: the business case, stages, roles, management by exception | the project log and acceptances (core-project-record) as evidence of the stages |
| **PMI / PMBOK** | a standard of project management knowledge (principles, performance domains, predictive, agile and hybrid approaches) | the plan, risks and stakeholders; check the edition used in the organization |
| **RUP** | an iterative process (inception, elaboration, construction, transition) with an emphasis on architecture early | historical; the idea "architectural risks first" lives on in spikes and skeletons |
| **Scrum, Kanban, XP, SAFe, LeSS** | agile work frameworks and their scaling | proc-agile, proc-safe; XP — engineering practices (TDD, continuous integration, pair programming) |

## How to work with this
- Find out which framework, and to what extent, the organization really uses (often "TOGAF" means only a document template
  and an architecture board).
- Map the factory's existing artifacts onto the required ones (ADR → decision register, threat model → risk assessment, postmortem →
  problem record), instead of creating parallel documents.
- Frameworks are a means: when the process starts requiring documents nobody reads, propose a lighter form with the same
  goal.

## Sources
- The Open Group: TOGAF Standard 10th Edition, ArchiMate Specification; IIBA: BABOK Guide; AXELOS/PeopleCert: ITIL 4,
  PRINCE2; PMI: PMBOK Guide
- [roadmap.sh — Software Architect](https://roadmap.sh/software-architect) (enterprise architecture, TOGAF, BABOK, IAF,
  ITIL, PMI, PRINCE2, RUP, SAFe, LeSS, XP)
Described in our own words.
