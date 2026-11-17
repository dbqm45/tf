# Staffing the phases — examples from the packs

A supplement to the "Phases" table in SKILL.md. The core describes roles and skill dimensions; here are examples of how
specific packs staff them. Only what is installed applies — you check it in `.claude/catalog.md`. The pack's dispatcher
proposes the staffing in the phase plan; you choose personas for the problem, not mechanically.

A row = a phase (numbering as in SKILL.md). The row gives the pack at every persona and skill. A domain pack (also from
outside the factory repository) describes its phase staffing in the guide `.tf/factory/packs/<id>/GUIDE.md`.

- **0** — pack-it: Maja; proc-project-planning
- **1** — pack-it: proc-product-discovery · pack-ux: Natalia, ux-feature-design
- **2** — pack-it: Ewa; ddd-discovery-intake, ddd-event-storming, ddd-strategic-analysis, ddd-context-mapping
- **3** — pack-it: Ewa; ddd-tactical-design, qa-spec-first-testing, arch-quality-attributes · pack-ux: Natalia
- **4** — pack-it: Tomasz; arch-system-design, arch-tech-selection, arch-quality-attributes, arch-threat-modeling, arch-privacy-compliance, arch-architect-practice
- **5** — pack-it: Tomasz + Kasia; eng-continuous-delivery, qa-test-design, qa-change-review
- **6** — pack-it: Ola / Jan / Filip / Ada / Marek (per stack) + Kasia; lang-*, fw-*, be-*, fe-*, eng-testing, qa-change-review
- **7** — pack-it: Piotr + Kasia; ops-ci-cd, ops-docker, ops-kubernetes, ops-release-engineering, ops-observability, ops-sre-incidents, ops-supply-chain-security, ops-secrets-identities
- **8** — pack-it: Piotr; ops-release-engineering, ops-sre-incidents
- **9** — pack-it: Piotr + the delivering persona + Kasia; ops-sre-incidents, proc-issue-triage, eng-debugging, ops-dependency-upgrades, ops-supply-chain-security, qa-regression, ops-finops

The security-reviewer agent (phase 7) belongs to the core and is available without packs.
