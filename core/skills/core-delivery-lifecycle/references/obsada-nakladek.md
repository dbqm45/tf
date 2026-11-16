# Obsada faz — przykłady z nakładek

Uzupełnienie tabeli „Fazy” w SKILL.md. Rdzeń opisuje role i wymiary skilli; tu są przykłady, jak obsadzają je
konkretne nakładki. Obowiązuje tylko to, co jest zainstalowane — sprawdzasz w `.claude/catalog.md`. Obsadę
proponuje dyspozytor nakładki w planie faz; persony dobierasz do problemu, nie mechanicznie.

Wiersz = faza (numeracja jak w SKILL.md). Wiersz podaje nakładkę przy każdej personie i skillu. Nakładka domenowa
(także spoza repozytorium fabryki) opisuje swoją obsadę faz w przewodniku `.tf/factory/packs/<id>/GUIDE.md`.

- **0** — pack-it: Maja; proc-project-planning
- **1** — pack-it: proc-product-discovery · pack-ux: Natalia, ux-feature-design
- **2** — pack-it: Ewa; ddd-discovery-intake, ddd-event-storming, ddd-strategic-analysis, ddd-context-mapping
- **3** — pack-it: Ewa; ddd-tactical-design, qa-spec-first-testing, arch-quality-attributes · pack-ux: Natalia
- **4** — pack-it: Tomasz; arch-system-design, arch-tech-selection, arch-quality-attributes, arch-threat-modeling, arch-privacy-compliance, arch-architect-practice
- **5** — pack-it: Tomasz + Kasia; eng-continuous-delivery, qa-test-design, qa-change-review
- **6** — pack-it: Ola / Jan / Filip / Ada / Marek (wg stacku) + Kasia; lang-*, fw-*, be-*, fe-*, eng-testing, qa-change-review
- **7** — pack-it: Piotr + Kasia; ops-ci-cd, ops-docker, ops-kubernetes, ops-release-engineering, ops-observability, ops-sre-incidents, ops-supply-chain-security, ops-secrets-identities
- **8** — pack-it: Piotr; ops-release-engineering, ops-sre-incidents
- **9** — pack-it: Piotr + persona realizująca + Kasia; ops-sre-incidents, proc-issue-triage, eng-debugging, ops-dependency-upgrades, ops-supply-chain-security, qa-regression, ops-finops

Agent security-reviewer (faza 7) należy do rdzenia i jest dostępny bez nakładek.
