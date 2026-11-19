---
name: sec-risk-management
description: Use for a security risk register, risk acceptance, vendor risk, FAIR or ISO 27005 — the process, appetite, treatment, KRIs.
metadata:
  review: "2027-04-17"
  catalog: "Use when a company runs an organizational information security risk process — context and criteria (ISO/IEC 27005:2022), identification by assets or by scenarios, qualitative analysis (a matrix) and quantitative analysis (FAIR: loss event frequency × loss magnitude, ranges, Monte Carlo), risk appetite and tolerance, treatment options (modification, retention with an owner and a deadline, avoidance, sharing and cyber insurance), the risk register, vendor risk (questionnaires, SOC 2 reports, contract clauses, monitoring), risk acceptance management, KRI reporting. Result: a risk register template and a risk acceptance record. Not for a feature threat model and design assessment (arch-threat-modeling), frameworks and audits (sec-governance-compliance), project risks (proc-project-planning) or incident handling (ops-security-operations). Not legal or insurance advice."
  keywords: "ryzyko bezpieczeństwa, rejestr ryzyk, akceptacja ryzyka, apetyt na ryzyko, tolerancja ryzyka, ISO 27005, analiza ryzyka, ocena ryzyka, ryzyko rezydualne, plan postępowania z ryzykiem, FAIR, ryzyko ilościowe, macierz ryzyka, KRI, ryzyko dostawcy, ocena dostawcy, vendor risk, due diligence, ankieta bezpieczeństwa dostawcy, ubezpieczenie cyber, polisa cyber, wyjątek od polityki, ile możemy stracić, właściciel ryzyka, security risk, risk register, risk acceptance, risk appetite, risk tolerance, risk analysis, risk assessment, residual risk, risk treatment plan, quantitative risk, risk matrix, vendor assessment, vendor security questionnaire, cyber insurance, cyber policy, policy exception, how much can we lose, risk owner"
---

# Information security risk management

**The agent's role:** it prepares the criteria, the register, the analyses, the treatment variants and draft records. **Risk acceptance,
the appetite and buying a policy are decided by a human** (the risk owner, the board); this is not legal or insurance advice.
Boundaries: the threat model of a specific feature and the assessment of its design — **arch-threat-modeling** (from there you take
threats as input to the register); frameworks, the SoA and audits — **sec-governance-compliance**; project risks (deadline,
budget) — **proc-project-planning**; an incident in progress — **ops-security-operations**. Artifact:
`docs/project/04-architecture/risk-register.md` (core-project-record).

## The process (per ISO/IEC 27005:2022, consistent with ISO 31000)
Context → risk assessment (identification, analysis, evaluation) → treatment → acceptance of the residual risk →
communication → monitoring and review. The process is cyclical; an input to the SoA in ISO 27001.

1. **Context and criteria.** The scope, the assets and their owners, legal and contractual constraints. Record **before the assessment**:
   the likelihood and impact scales (with thresholds in PLN, e.g. impact 3 = a loss of PLN 100–500 thousand [example]),
   the **appetite** (how much risk the company wants to carry in pursuing its goals, e.g. "no critical risk without a plan") and the **tolerance**
   (the acceptable deviation, the escalation threshold). The criteria are approved by the board; without them assessments are not comparable.
2. **Identification.** Two approaches, often combined:
   - **by assets** — asset × threat × vulnerability; complete, but tedious; good for an ISO 27001 scope;
   - **by scenarios** — "who/what → event → consequence" (ransomware in production, a compromised vendor account);
     faster and understandable for the board; good for FAIR.
   Sources: threat models, audit and test results, incidents, vendor risks, changes in the business. The record: cause →
   event → consequence, not "no patching".
3. **Analysis.** By default **qualitative**: a matrix (e.g. 5×5) with the explicit scales from step 1. **Quantitative (FAIR)** for the highest
   risks and budget decisions: risk = **loss event frequency × loss magnitude**; both factors as
   **ranges** (min, most likely, max) from calibrated expert estimates and data; **a Monte
   Carlo simulation** gives the distribution of the annual loss (e.g. the median and P90). You compare the distribution with the cost of the control and the appetite;
   the simulation result after implementing the control is the **residual risk** — call it that in the report.
   You do not replace the matrix entirely: you quantify only selected scenarios. Details: `references/analysis-and-procedure.md`.
4. **Evaluation.** Compare the risk with the criteria: above the tolerance → treatment is mandatory; within the appetite → it can be
   retained. Rank them; group risks of the same class, so that the register does not grow to hundreds of rows.
5. **Treatment** — one of the options (names from ISO 27005:2022):
   | Option | What | Condition |
   |---|---|---|
   | modification (mitigation) | a control lowers the likelihood or the consequence | a task, a deadline, an effectiveness test |
   | retention (acceptance) | a conscious agreement to the risk | an owner, a justification, **an expiry date**, a record |
   | avoidance | giving up an activity or a feature | a business decision |
   | sharing (transfer) | a vendor, a contract, **cyber insurance** | transfers the financial consequence, not the accountability or the reputational damage |
   After the choice calculate the **residual risk** and record it separately.
6. **Risk acceptance.** Only the risk owner with authority adequate to the level (e.g. medium — the area
   manager, high — a director, critical — the board). The risk is not accepted by whoever creates it, nor by the security team
   on behalf of the business. A risk above the tolerance is not accepted with a signature: it requires treatment or a board decision to change the
   tolerance. The acceptance is **time-limited** (usually ≤12 months [example]), with compensating conditions and a review
   trigger (a change of scope, an incident). Template: `references/register-and-acceptance.md`.
7. **Vendor risk** (third parties). Tiering by data access and criticality; proportionate due diligence:
   a questionnaire, a **SOC 2 Type II** report or an ISO 27001 certificate (check the scope, the period, the exceptions and the complementary
   user entity controls), evidence tests; contract clauses (incident notification within a deadline, the right to audit,
   subcontractors, the return and deletion of data, security requirements); **continuous monitoring** (a yearly review of reports,
   changes of ownership, incidents in the media). Personal data → a data processing agreement (arch-privacy-compliance). Details:
   `references/vendor-risk.md`.
8. **Monitoring and KRIs.** Early warning indicators with thresholds and an owner, e.g. the share of critical vulnerabilities
   past their deadline, exceptions without a valid acceptance, tier 1 vendors without a current assessment, restore time vs the target. A report for the board
   quarterly: the highest risks, changes, expiring acceptances, the KRI trend, decisions to be made.

## Example
Input: "The old partner portal has no MFA; the rollout is in 5 months. The sales director wants to accept the risk."

Result (an acceptance record, a fragment) [example]:
- R-017: takeover of a partner account → a leak of customer orders. Inherent: L4 × I4 = 16 (high).
- Option: modification (MFA by 2027-03-31) + temporary retention. Compensating controls: an attempt limit, an alert on a new device,
  blocking bulk export. Residual: L3 × I3 = 9 (medium).
- Accepted by: the sales director (the process owner, authorized for medium risks). Valid until 2027-03-31; before that
  a review after every incident on a partner account. Informed: the CISO, the legal department.
- Security objection: none; if the residual risk were high, the decision goes to the board.

## Checklist
- [ ] the criteria, the appetite and the tolerance approved before the assessment
- [ ] the risk as cause → event → consequence; sources: threat models, audits, vendors
- [ ] scales with thresholds; FAIR only for selected scenarios, with ranges
- [ ] every risk above the tolerance has a treatment option, a task and a deadline
- [ ] the residual risk recorded separately
- [ ] acceptance: an owner with authority, a justification, an expiry date, conditions
- [ ] vendors with a tier, evidence (SOC 2/ISO: scope and exceptions) and clauses
- [ ] KRIs with thresholds; a quarterly report for the board

## Additional materials
- `references/register-and-acceptance.md` — the risk register template (fields), the acceptance record, authority levels; read it when creating `risk-register.md`.
- `references/analysis-and-procedure.md` — scales, FAIR step by step, cyber insurance, KRIs; read it for a quantitative analysis and the report.
- `references/vendor-risk.md` — tiering, the questionnaire, reading a SOC 2 report, clauses, monitoring; read it when assessing a vendor.

## Sources
- ISO/IEC 27005:2022 *Information security risk management* (October 2022; adds the acceptance of residual risk,
  consistent with ISO/IEC 27001:2022 and ISO 31000:2018) — iso.org; per secondary sources (PECB, EVS), accessed 2026-10-17 [unverified at the source].
- FAIR — The Open Group, Open FAIR O-RT and O-RA; J. Freund, J. Jones, *Measuring and Managing Information Risk* (2014); per secondary sources, accessed 2026-10-17.
- AICPA, Trust Services Criteria (2017, points of focus 2022) — per secondary sources, accessed 2026-10-17.
Described in our own words; not legal advice.
