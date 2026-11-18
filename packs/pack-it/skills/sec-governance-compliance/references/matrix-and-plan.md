# The control matrix and the audit readiness plan

Contents: 1. The control matrix · 2. The readiness plan · 3. The course of audits · 4. The evidence register

## 1. The control matrix (one register per organization)
| ID | Control (how it works) | Owner | System | Frequency | Evidence (source, path) | ISO 27001 | SOC 2 | CSF 2.0 | PCI DSS | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| K-014 | A quarterly review of access to AWS, removal of excess access | CTO | AWS IAM | quarterly | an IAM export + a ticket | A.5.18 | CC6.2 | PR.AA | 7.2.4 | works, evidence |
[example: the control numbering and mappings are illustrative; verify them in the framework texts before use]

Rules: a control described with a verb and a frequency ("every quarter"), not with a slogan ("access management"); one
owner; the evidence points to a source from which you fetch it without asking a human; mapping to the framework requirements only after
formulating the control. No control for a requirement = a gap; a control without a requirement = a candidate for removal.

## 2. The audit readiness plan
| Stage | Result | Owner | Gate |
|---|---|---|---|
| Scope and motive | an approved scope, exclusions | CISO/the board | management's signature |
| Risks | the risk register, the treatment plan (sec-risk-management) | CISO | risk acceptances |
| Policies and standards | complete, approved, known to the teams | CISO | acknowledgements |
| Gaps | tasks with deadlines | control owners | no critical gaps |
| Evidence | automatic collection, a calendar of periodic controls | owners | a sample of evidence from 3 months |
| Internal audit | a report, nonconformities, actions | an independent auditor | major nonconformities closed |
| Management review | minutes (inputs and decisions) | the board | minutes signed |
| External audit | a dress rehearsal with the provider, a booked date | CISO | no open blockers |

Booking a date: choose the certification body or the audit firm in advance; the time depends on the scope.

## 3. The course of audits
- **ISO 27001**: stage 1 — a review of the documentation and readiness (scope, policies, SoA, risk assessment, internal audit,
  management review); stage 2 — checking the implementation with samples and interviews; major nonconformities block the certificate
  until they are closed; then surveillance audits and recertification [unverified: the frequency according to the body].
- **SOC 2**: choosing the categories, a readiness assessment, the observation period for Type II, sampling evidence from the period,
  a report with an opinion and a list of exceptions.
- **PCI DSS**: determining the level and form of validation with the acquirer, evidence per requirement, the AOC.
- **Conduct during the audit**: one person coordinates, the answers follow from the evidence, "I don't know, I'll check" instead of
  guessing; you do not correct evidence retroactively.

## 4. The evidence register
| Evidence | Control | Source | Collection | Date | Retention |
|---|---|---|---|---|---|
| An export of IAM users | K-014 | AWS CLI/API | automatic, quarterly | 2026-10-01 | 3 years |
[example]. Does the evidence contain personal data? Retention and access per arch-privacy-compliance.
