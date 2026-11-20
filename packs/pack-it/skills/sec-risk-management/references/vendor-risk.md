# Vendor risk (third-party risk)

Contents: 1. Tiering · 2. Due diligence · 3. Reading a SOC 2 report · 4. Contract clauses · 5. Monitoring · 6. Exit

## 1. Tiering
| Tier | Criterion | Depth |
|---|---|---|
| 1 | access to sensitive/personal data at large scale, or an outage stops the business | a full questionnaire, a SOC 2 Type II report or ISO 27001, a contract review, a yearly review |
| 2 | limited access to data, an outage is a nuisance | a short questionnaire, a certificate or a report |
| 3 | no access to data, replaceable | a self-declaration, standard terms |

## 2. Due diligence
A proportionate questionnaire (standard industry formats instead of 300 home-made questions [unverified: the choice depends on the company]).
Areas: security management, access and MFA, encryption, backups and continuity, vulnerability management,
incidents and notification, subcontractors, data location, data deletion. An answer without evidence carries less weight.
Result: the vendor assessment, gaps, purchase conditions, risks for the register (the owner on the business side).

## 3. Reading a SOC 2 report
Check: the type (II for tier 1), the **period** (current, without a long gap until today — a "bridge letter" fills the gap), the Trust
Services categories (whether they cover what you care about), the **system scope** (whether it concerns the service you are buying),
the **opinion** (unqualified or qualified), the **exceptions** and management's response, the **complementary user entity
controls (CUEC)** — these are your obligations, and the use of subservice organizations (carve-out). The report is confidential; protect it
with a non-disclosure agreement. An ISO 27001 certificate: the scope, the SoA (ask for the version), the certification body, the validity.

## 4. Contract clauses
Security requirements (an annex) · incident notification within an agreed deadline · the right to audit or to reports ·
management of subcontractors and consent to changes · data location and transfer · the return and deletion of data on
exit · continuity and RTO/RPO · liability and insurance · a data processing agreement, when there is personal data
(arch-privacy-compliance). The content of the clauses and the liability are reviewed by a lawyer.

## 5. Continuous monitoring
A yearly (tier 1) review of reports and certificates, a validity calendar; tracking the vendor's incidents and changes of
ownership; a change in the scope of use → a new assessment; results into the KRIs (vendors without a valid assessment). A vendor with a critical
finding: a remediation plan with a deadline or a risk acceptance (register-and-acceptance.md).

## 6. Exit from a vendor
A replacement plan for tier 1 before the contract: a data export in a usable format, a transition period, a confirmation of deletion.
