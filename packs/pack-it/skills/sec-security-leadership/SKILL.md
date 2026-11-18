---
name: sec-security-leadership
description: Use for company security strategy and leadership as a CISO — strategy, budget, board report, culture, crisis and ransom, insurance, M&A.
metadata:
  review: "2027-04-17"
  catalog: "Use when you lead or build the security function at executive level (CISO, head of security, the first specialist in the company) — a strategy tied to business goals (current state, target state, a 1–3 year roadmap, NIST CSF 2.0 current and target profiles), budget and business case (control cost against risk reduction, priorities, cautious benchmarks), organization and operating model (team structure, RACI, the IIA 2020 three lines model), reporting to the board (KPI vs KRI, risk appetite, a one-page dashboard, the language of business impact), culture and awareness (training, phishing simulations, measuring behaviour), crisis management at board level (crisis team, decision log, communication with lawyers, the regulator, customers and the media, the ransom decision process, tabletop exercises), cyber insurance, vendor and supply chain risk at program level, security in mergers and acquisitions, AI risk in the organization. Output: a one-page strategy, a board report template, a draft crisis playbook. Not for the risk register, FAIR and vendor risk in detail (sec-risk-management), ISO 27001, SOC 2 and the control matrix (sec-governance-compliance), technical incident handling (ops-security-operations), NIS2, DORA and CRA (sec-eu-regulations) or the project plan (proc-project-planning). It is not legal or insurance advice."
  keywords: "CISO, szef bezpieczeństwa, dyrektor bezpieczeństwa, strategia bezpieczeństwa, strategia cyber, mapa drogowa bezpieczeństwa, budżet na bezpieczeństwo, uzasadnienie budżetu, CFO, raport dla zarządu, rada nadzorcza, pulpit dla zarządu, KPI, KRI, apetyt na ryzyko, trzy linie, model trzech linii, RACI, struktura zespołu bezpieczeństwa, kultura bezpieczeństwa, szkolenia z bezpieczeństwa, phishing symulacja, uświadamianie, kryzys, sztab kryzysowy, ransomware zarząd, okup, płacić okup, ćwiczenie tabletop, komunikacja kryzysowa, ubezpieczenie cyber, ryzyko dostawców program, łańcuch dostaw, fuzje i przejęcia, due diligence M&A, ryzyko AI w firmie, profil docelowy, head of security, security director, security strategy, cyber strategy, security roadmap, security budget, budget justification, board report, supervisory board, board dashboard, risk appetite, three lines, three lines model, security team structure, security culture, security training, phishing simulation, awareness, crisis, crisis team, ransomware board, ransom, pay the ransom, tabletop exercise, crisis communication, cyber insurance, vendor risk program, supply chain, mergers and acquisitions, AI risk in the company, target profile"
---

# Security leadership — strategy, board, crisis

**The agent's role:** it prepares drafts of the strategy, the report, the playbook and questions for the board. **Decisions (budget, risk
appetite, ransom, notifications, buying a policy) are made by people** with a mandate; legal and insurance matters — by a lawyer
and a broker. This is not legal or insurance advice. External numbers and facts: [unverified] until
you have a source (core-grounding).

Boundaries: the risk register, FAIR and vendor risk in detail — sec-risk-management; ISO 27001, SOC 2, the control matrix
— sec-governance-compliance; technical response — ops-security-operations; NIS2, DORA, CRA and notification deadlines —
sec-eu-regulations. Here: what leadership decides and says on the basis of all that.

## Procedure
1. **Business context.** Ask about 3–5 company goals for 1–3 years (growth, a new market, enterprise customers, acquisitions),
   the "crown jewels" (data, processes, systems without which the company stops) and past incidents. A strategy without business
   goals is a list of tools.
2. **Current and target state.** Assess yourself against NIST CSF 2.0 (six functions including Govern): **current profile** →
   **target profile** → gap analysis → action plan (the flow according to NIST SP 1301). "CSF compliant" does not exist; you say
   "target profile: …". Framework details: sec-governance-compliance.
3. **Strategy and roadmap.** 3–5 pillars, each with a business outcome, an initiative, a measure and an owner; the roadmap
   in stages (0–6, 6–18, 18–36 months), what we do **not** do. Deadline and cost as ranges (proc-project-planning).
   Template: `references/templates.md`.
4. **Budget and justification.** For every initiative: risk reduction (the loss distribution before and after — sec-risk-management),
   total cost (licences, people, maintenance), the "we do nothing" and "we insure" alternatives. Order by
   risk reduction per zloty and by requirements (customer, regulation). Benchmarks (% of the IT budget, headcount) only as
   a reference point with a source and a date, never as a justification.
5. **Organization and roles.** The three lines model (IIA 2020): the board is responsible for oversight, management (1st and 2nd line)
   for actions and risk management, independent internal audit provides assurance. Security usually
   supports the 1st line and is sometimes the 2nd line (risk oversight); it does not audit itself. RACI for decisions: who accepts
   risk, who declares a crisis, who contacts the regulator.
6. **Board report.** One page, the language of impact (money, downtime, customers, law), not of alerts.
   **KPI** (whether the program works) and **KRI** (whether risk is growing) separately, with a threshold and a trend; risks against the **appetite**
   approved by the board; at the end **decisions to be made**. Rhythm: quarterly plus events. Template:
   `references/templates.md`.
7. **Culture and awareness.** Measure behaviour (phishing report rate, time to report, repeated
   mistakes, MFA use), not attendance at training. Phishing simulations ethically: board and HR approval, no
   humiliation and no list of "culprits" by name, no topics that exploit stress (bonuses, layoffs, illness),
   teaching instead of punishment, an easy "report" button.
8. **Crisis.** Before an event: a crisis team with deputies, a mandate, a channel outside the attacked systems, a playbook
   (`references/crisis-and-insurance.md`), a tabletop exercise at least once a year. During an event: a decision
   log, a briefing rhythm, one voice outside, communication through a lawyer where confidentiality must be protected.
   **Ransom:** a board decision after the opinion of a lawyer (sanctions, notifications), law enforcement and a crisis adviser;
   payment does not guarantee recovering the data and does not close the matter.
9. **Cyber insurance.** What it covers, exclusions, limits, control requirements (MFA, backups, EDR), the choice of advisers
   imposed by the insurer, the notification deadline. A policy transfers the financial impact, not responsibility
   or reputation (risk details: sec-risk-management).
10. **Vendors, M&A, AI.** Vendors at program level: tiering by criticality, contract and monitoring rules,
    an exit plan, control of key 4th parties (technology — ops-supply-chain-security; assessment of a single vendor —
    sec-risk-management). M&A: before signing, a short assessment of the target (incidents, identity, technical debt,
    compliance), the "day 1" scope (MFA, logging, access), integration in a 100-day plan. AI: an inventory of use
    (including unofficial use), a policy for employees, a designated owner; legal obligations — ai-governance-compliance,
    application risks — sec-llm-security.

Output: `docs/project/security-strategy.md` (one-page strategy, roadmap, budget), `board-report.md`,
`crisis-playbook.md`; TL;DR and Handoff according to core-project-record. The first line:
`Security leadership: <company> — target profile <year>, decisions to be made: <n>`.

## Example
Input: "A software house, 600 people, 3 large enterprise tenders this year, no CISO, MFA only for administrators."
Output (a fragment of `security-strategy.md`):

```markdown
Security leadership: software house — target profile 2028, decisions to be made: 2
Business goals: win 3 enterprise tenders; zero production downtime >4 h.
Pillar 1 Identity: phishing-resistant MFA for 100% of privileged accounts within 6 months (outcome: a tender condition).
KRI: share of privileged accounts without MFA (threshold 0%), time to patch critical issues (threshold 7 days).
Budget: PLN 380–520 thousand/year [example]; "no change" alternative: risk of losing tenders worth PLN 12 million [example].
We do not do: our own SOC (an external service). Decisions: (1) a CISO position, (2) appetite: no critical risk >90 days.
```

## Checklist
- [ ] the strategy follows from business goals; current and target profile; a list of "what we do not do"
- [ ] budget: risk reduction, total cost, alternatives; benchmarks with a date, not as an argument
- [ ] report: one page, KPI and KRI separately, appetite, decisions to be made
- [ ] roles (RACI) for risk acceptance and crisis declaration; audit independent of security
- [ ] culture measured by behaviour; ethical phishing simulations
- [ ] a crisis playbook, exercised; the ransom decision in a process with a lawyer
- [ ] [unverified] on facts without a source

## Additional materials
- `references/templates.md` — one-page strategy, board report (KPI, KRI), RACI; read when writing the documents.
- `references/crisis-and-insurance.md` — crisis team, playbook, ransom, communication, tabletop, policy; read in a crisis.

## Sources
- NIST CSF 2.0 (February 2024) and NIST SP 1301, *Quick Start Guide for Creating and Using Organizational Profiles* (February 2024):
  current profile, target profile, gap analysis (search, accessed 2026-10-17; the documents were not opened).
- IIA, *The IIA's Three Lines Model* (July 2020; 2024 update to the standards glossary) — six principles, the roles of the governing
  body, management and audit (search, accessed 2026-10-17; the original was not opened).
- OFAC, *Updated Advisory on Potential Sanctions Risks for Facilitating Ransomware Payments* (21.09.2021): strict
  liability, mitigating factors (secondary sources, accessed 2026-10-17).
Described in our own words.
