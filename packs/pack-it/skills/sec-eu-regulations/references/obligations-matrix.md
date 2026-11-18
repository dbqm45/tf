# NIS2, DORA, CRA obligations matrix

Contents: NIS2 · DORA · CRA · Penalties · Evidence. All article numbers and amounts: own knowledge, not confirmed in the session
in EUR-Lex [unverified at the source]. Not legal advice; the national act and the authorities' guidelines take precedence.

## NIS2 (Directive (EU) 2022/2555)
| Topic | Content | Evidence |
|---|---|---|
| Scope (Art. 2–3) | medium and large entities from Annex I (energy, transport, banking, financial market infrastructure, health, water, digital infrastructure, B2B ICT service management, public administration, space) and Annex II (postal services, waste, chemicals, food, manufacturing, digital providers, research) | a qualification analysis, the entry in the list |
| Essential vs important | essential: large from Annex I and the size-independent exceptions; important: the rest. The difference is mainly supervision (essential ones also ex ante) and the upper penalties | the justification of the class |
| Management body (Art. 20) | approves the measures from Art. 21, oversees, is liable for infringements, training | minutes, training lists |
| Measures (Art. 21(2)) | risk analysis and policies; incident handling; continuity (backups, crisis management); the supply chain; security in acquisition, development and maintenance, including vulnerability handling; assessment of effectiveness; hygiene and training; cryptography; human resources, access control, assets; MFA and secure communications | policies, registers, tests |
| Reporting (Art. 23) | a significant incident: 24 h early warning (whether an unlawful act is suspected, cross-border impact), 72 h notification with an assessment, an intermediate report on request, a final report a month after the notification, a progress report for an ongoing incident | the playbook, the register of notifications |
| Penalties (Art. 34) | essential up to EUR 10 million or 2% of turnover; important up to EUR 7 million or 1.4% of turnover (whichever is higher); the national act may set its own caps | — |
Nationally (PL): the KSC act after the amendment (Dz.U. 2026 item 252) — check in ISAP the list, the deadlines, the national penalties, the role of the CSIRTs
(NASK, GOV, MON) and the authorities competent for the sector [unverified].

## DORA (Regulation (EU) 2022/2554, from 2025-01-17)
| Pillar | Content |
|---|---|
| ICT risk management (Chapter II) | a framework approved and overseen by the management body, identification of assets, protection, detection, response and recovery, backups, learning |
| Incidents (Chapter III) | a process, classification by criteria (clients, data losses, duration, geographical spread, criticality of services, economic impact), reporting of major incidents: initial, intermediate, final; voluntary notification of significant cyber threats |
| Resilience testing (Chapter IV) | a testing programme at least once a year; TLPT (threat-led penetration testing) at least every 3 years for designated entities; RTS (EU) 2025/1190 [unverified] |
| ICT third-party risk (Chapter V) | a strategy, the register of information on contractual arrangements (first submission to the authorities 2025-04-30), mandatory contractual clauses (Art. 30), exit strategies, oversight of critical ICT providers by an ESA (Lead Overseer) |
| Information sharing | voluntary sharing of information on cyber threats |
Penalties: set by the member states and the supervisory authorities; for critical ICT providers, periodic penalty payments by the ESA [unverified].

## CRA (Regulation (EU) 2024/2847)
| Topic | Content |
|---|---|
| Dates | in force 2024-12-10; the provisions on conformity assessment bodies from 2026-06-11 [unverified]; reporting (Art. 14) from 2026-09-11; most obligations from 2027-12-11 |
| Manufacturer | essential requirements (Annex I): security by design and by default, no known exploitable vulnerabilities when placed on the market, security updates, SBOM, a coordinated vulnerability disclosure policy; risk assessment; technical documentation; a support period of at least 5 years, unless the product is used for less time |
| Conformity assessment | categories: default (self-assessment), important (class I and II), critical; the CE marking and the EU declaration of conformity |
| Reporting (Art. 14) | an actively exploited vulnerability and a severe incident affecting the security of the product: 24 h, 72 h, final report (vulnerability: 14 days after the fix; incident: a month), through the ENISA platform to the CSIRT coordinator and ENISA |
| Importer, distributor | verify the manufacturer's conformity, the marking, cooperation with the authorities |
| Open source | a steward with lighter obligations; OSS components in a product remain the manufacturer's responsibility (due diligence) |
Penalties: up to EUR 15 million or 2.5% of turnover (infringement of the essential requirements), lower thresholds for the rest [unverified at the source].

## Evidence (common)
A register of assets and providers, policies approved by the management body, management body training, an incident register with a timeline, tabletop
minutes, test reports, contracts with clauses (NIS2 supply chain, DORA Art. 30), SBOM and a vulnerability policy (CRA).
Mapping to ISO 27001 — `.claude/skills/sec-governance-compliance/SKILL.md`.
