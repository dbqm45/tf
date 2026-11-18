---
name: sec-eu-regulations
description: Use for EU cyber requirements — NIS2 (KSC), DORA, Cyber Resilience Act; scope, obligations, incident reporting deadlines, one incident and many reports.
metadata:
  review: "2027-01-17"
  catalog: "Use when you must establish whether and how a company is subject to EU cybersecurity regulations — NIS2 (Directive (EU) 2022/2555, in Poland the amendment of the Act on the National Cybersecurity System): essential and important entities, the size-cap rule, management body accountability (Art. 20), risk management measures (Art. 21), incident reporting (Art. 23: 24 h, 72 h, a month), penalties; DORA (Regulation (EU) 2022/2554) for the financial sector: ICT risk, incident classification and reporting, resilience testing with TLPT, the register of information on ICT providers; the Cyber Resilience Act (Regulation (EU) 2024/2847) for products with digital elements: manufacturer obligations, vulnerability handling, reporting actively exploited vulnerabilities, the CE marking; the interface with Art. 33 GDPR and sectoral rules, one incident and several clocks, one reporting playbook with a decision table. Result: an applicability assessment and an obligations matrix with reporting clocks. Not for GDPR and DPIA (arch-privacy-compliance), the AI Act (ai-governance-compliance), ISO 27001 and SOC 2 (sec-governance-compliance), the technical handling of an incident (ops-security-operations) or strategy and conversations with the management board (sec-security-leadership). Not legal advice."
  keywords: "NIS2, dyrektywa NIS2, KSC, krajowy system cyberbezpieczeństwa, podmiot kluczowy, podmiot ważny, DORA, odporność operacyjna, TLPT, rejestr informacji, dostawca ICT, Cyber Resilience Act, CRA, produkty z elementami cyfrowymi, znak CE, zgłoszenie incydentu, zgłaszanie incydentów, early warning, CSIRT, ENISA, odpowiedzialność zarządu, regulacje UE, czy podlegamy NIS2, jeden incydent wiele zgłoszeń, termin zgłoszenia, playbook zgłoszeń, kary NIS2, komu zgłosić incydent, komu i kiedy zgłosić, zgłosić do UODO i CSIRT, ransomware obowiązek zgłoszenia, fintech instytucja płatnicza, DORA i RODO jednocześnie, kilka zgłoszeń, obowiązek zgłoszenia do regulatora, NIS2 directive, national cybersecurity system, essential entity, important entity, operational resilience, register of information, ICT provider, products with digital elements, CE marking, incident notification, incident reporting, management body accountability, EU regulations, are we subject to NIS2, one incident many reports, reporting deadline, reporting playbook, NIS2 penalties, who to report an incident to, who to report to and when, report to UODO and CSIRT, ransomware reporting obligation, fintech payment institution, DORA and GDPR at the same time, several reports, obligation to report to the regulator"
---

# EU cybersecurity regulations (NIS2, DORA, CRA)

**The agent's role:** it prepares a preliminary applicability assessment, an obligations matrix with reporting clocks and a draft reporting
playbook. **This is not legal advice.** National law and the guidelines of supervisory authorities take precedence over this
skill; a lawyer decides the scope, the classification and the reports. Check every article and date in EUR-Lex (EU acts)
and ISAP/Dziennik Ustaw (the Polish legal database and journal of laws; Polish acts). Artifact: `docs/project/04-architecture/eu-cyber-regulations.md`.
GDPR and DPIA — **arch-privacy-compliance**; the AI Act — **ai-governance-compliance**; ISO 27001, SOC 2 —
**sec-governance-compliance**; technical incident handling — **ops-security-operations**; a conversation with the management board
and the programme — **sec-security-leadership**; the risk register — **sec-risk-management**.

## Procedure
1. **Facts about the company.** Countries of operation (EU/EEA, also customers), sector and subsector (NACE), headcount, turnover
   and balance sheet total (with linked enterprises), the role in the chain (service provider, manufacturer, ICT provider for
   banks), whether you place products with software on the EU market. Without this, the assessment is guesswork.
2. **Applicability — check in this order:**
   1. **DORA** (finance): if you are a financial entity under Art. 2, DORA is lex specialis with respect to NIS2
      (Art. 21 and 23 of NIS2 do not apply), but you are subject to the GDPR. An ICT provider for such entities is subject to it contractually.
   2. **NIS2:** medium and large enterprises (the size-cap rule: ≥50 people or turnover/balance sheet total >EUR 10 million)
      from the sectors of Annex I (high criticality) or II (other critical sectors). **Essential** — a large entity
      from Annex I and, regardless of size, among others qualified trust service providers, TLD registries, DNS. **Important** —
      the rest. Size-independent exceptions and national extensions — only according to the national act (step 5).
   3. **CRA:** a product with digital elements (hardware or software, connected to a device or a network) placed
      on the EU market. Role: manufacturer, importer, distributor, open source steward. SaaS services as such are out of scope,
      unless it is remote data processing necessary for a function of the product.
   4. **GDPR Art. 33** always applies when a breach concerns personal data — regardless of the other acts.
3. **Obligations** — the matrix in `references/obligations-matrix.md`. Summary:
   - **NIS2:** the management body approves the measures and oversees them, is liable for infringements and undergoes training (Art. 20);
     a minimum of 10 groups of measures (Art. 21(2): among others risk analysis, incident handling, business continuity,
     supply chain security, vulnerability handling, cryptography, access control, MFA, training);
     reporting (Art. 23).
   - **DORA:** an ICT risk management framework, classification and reporting of major incidents, resilience testing (at
     least annual; TLPT at least once every 3 years for designated entities), ICT third-party risk and the register of
     information, oversight of critical ICT providers.
   - **CRA:** security by design and by default, vulnerability handling and updates (support period usually ≥5 years),
     technical documentation, SBOM, conformity assessment and the CE marking, reporting.
4. **Reporting clocks** (table below) and **one playbook**: one event results in several reports to different recipients.
   Keep one timeline and one decision table (step 6), not separate procedures per act.
5. **Poland (NIS2).** Check the text of the act in ISAP; status as of 2026-10-17 (secondary sources, see Sources): the act of 2026-01-23
   amending the KSC act (the Act on the National Cybersecurity System, ustawa o krajowym systemie cyberbezpieczeństwa) (Dz.U. 2026 item 252) entered into force on 2026-04-03. The application for entry in the list of essential
   and important entities — deadline 2026-10-03 (**already passed** — check the consequences and the catch-up procedure in the act); implementing
   the obligations by 2027-04-03, the next stage by 2028-04-03 [unverified — from an announcement of the Ministry of Digital Affairs (Ministerstwo Cyfryzacji)].
   The President's application to the Constitutional Tribunal regarding some provisions (among others high-risk vendors, security
   orders, penalties) [unverified]. The amount of penalties and the exact reporting deadlines under the KSC: [unverified].
6. **Reporting decision table** (insert your own roles, recipients and contact numbers):
   | Question about the event | If yes | Clock, recipient |
   |---|---|---|
   | Does it concern personal data and is there a risk to people? | GDPR | 72 h from becoming aware, UODO (the Polish DPA); the individuals without undue delay when the risk is high |
   | A financial entity, a major ICT incident? | DORA | initial notification shortly after classification, no later than 24 h from detection; further stages per the table |
   | Essential or important, a significant incident? | NIS2 | 24 h early warning, 72 h notification, a month final report, CSIRT/authority |
   | Manufacturer: an actively exploited vulnerability or a severe product incident? | CRA | 24 h, 72 h, 14 days after the fix or a month, the ENISA platform |
   | A contract or a sectoral regulator (e.g. KNF, a customer) | contract, guidelines | per the document; check, do not guess |
   Every "yes" row opens a separate clock. The clocks start from different events (becoming aware, classification,
   availability of a fix) — record the starting event and the hour. Report on what you know; supplement in later stages.
7. **Result:** facts about the company → applicability per act with a justification → the obligations matrix (owner, evidence, deadline,
   status) → the clock table and the playbook → gaps → decisions for the lawyer. At the top: "A preliminary working assessment, not legal
   advice; approved by: [lawyer/DPO]".

## Reporting clocks — status as of 2026-10-17
| Act | First signal | Second stage | Final report | Clock start |
|---|---|---|---|---|
| NIS2 Art. 23 | 24 h early warning | 72 h incident notification | a month after the notification | becoming aware of a significant incident |
| GDPR Art. 33 | 72 h (one notification, supplemented in stages) | — | — | becoming aware of the breach |
| DORA (ITS 2025/302, RTS 2025/301) | 4 h from classification, no later than 24 h from becoming aware | intermediate report 72 h from the initial notification | a month from the intermediate report | classification as major; sources differ on the start of the clock [unverified] |
| CRA Art. 14 | 24 h early warning | 72 h notification | vulnerability: 14 days after a fix is available; incident: a month after the 72 h notification | becoming aware |

CRA: the reporting obligations from 2026-09-11 (also for products already on the market), most of the rest from 2027-12-11;
reports through the ENISA platform (Single Reporting Platform), which also reaches the CSIRT coordinator. DORA applies from
2025-01-17. Transposition and national deadlines: NIS2 — 2024-10-17 (Poland late, until 2026-04-03).
The Digital Omnibus (2025-11-19) proposes a single reporting point for NIS2, GDPR, DORA and others — it is a **proposal**, not adopted
[unverified]; do not plan changes on it.

## Example
Input: "A Polish SaaS provider for banks, 120 people, turnover EUR 25 million, also releases a mobile app. A leak of the bank's
customers' data through a vulnerability in our API." [example]

Result (excerpt):
- NIS2: B2B ICT services (Annex I) and medium size → preliminarily an important entity; confirm the qualification under the KSC and the entry in the list.
- DORA: not a financial entity, but an ICT provider — the obligations follow from the contracts with the banks (DORA Art. 30),
  and the incident must reach the banks in time for them to report their own.
- GDPR: probably a processor — notifies the controller (the bank) without undue delay; the 72 h applies to the controller.
- CRA: the mobile app is a product with digital elements; an actively exploited vulnerability → 24 h on the ENISA platform.
- Clocks: hour 0 = becoming aware; +24 h NIS2 and CRA, +72 h both notifications and the controller's GDPR notification. One timeline.

## Checklist
- [ ] the facts about the company (sector, size, countries, role, products) recorded
- [ ] applicability per act, in the order DORA, NIS2, CRA, GDPR, with a justification
- [ ] the obligations matrix with an owner, evidence, a deadline
- [ ] the starting event and the recipient for every clock; one incident timeline
- [ ] the national status (KSC) checked in ISAP; contradictions marked [unverified]
- [ ] the "not legal advice" note and the approver; a playbook exercise (tabletop)

## Additional materials
- `references/obligations-matrix.md` — obligations, penalties and evidence per act, sectors and the size-cap rule; read when building the matrix.
- `references/ticket-playbook.md` — a draft playbook with a timeline and a notification template; read when designing the procedure.

## Sources
- Directive (EU) 2022/2555 (NIS2), Regulation (EU) 2022/2554 (DORA), Regulation (EU) 2024/2847 (CRA) —
  eur-lex.europa.eu; article numbers and penalties from own knowledge, not confirmed at the source in the session [unverified at the source].
- Poland: Dz.U. 2026 item 252 (ELI eli.gov.pl/eli/DU/2026/252), an announcement of the Ministry of Digital Affairs of 2026-04-02 on gov.pl,
  Forsal 2026-04-04, Clifford Chance 2026-03, Osborne Clarke; accessed 2026-10-17 (search results, not the text of the act).
- CRA, reporting: the European Commission's page on CRA reporting (digital-strategy.ec.europa.eu) and law firm commentaries
  (McCann FitzGerald, 2026-09), accessed 2026-10-17 (summaries from search).
- DORA, reporting: delegated and implementing regulations (EU) 2025/301 and 2025/302; ESAs operational instructions
  (esma.europa.eu, 2026-09), accessed 2026-10-17 — sources differ on the start of the clock.
- Digital Omnibus (Commission, 2025-11-19), a single reporting point: Taylor Wessing, Conventus Law, Council document
  WK 3735/2026, accessed 2026-10-17 — a proposal in progress.
Described in our own words; not legal advice.
