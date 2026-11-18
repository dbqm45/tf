# Compliance: mapping controls onto frameworks and audits

The agent helps collect evidence and map controls. **It does not declare compliance** — that is the role of the auditor and the legal department.

## The frameworks you will meet most often
| Framework | What it is | Structure |
|---|---|---|
| **NIST CSF 2.0** (2024) | a voluntary cyber risk management framework | 6 functions: Govern, Identify, Protect, Detect, Respond, Recover → categories → subcategories |
| **ISO/IEC 27001:2022** | a certified information security management system (ISMS) | clauses 4–10 (management, risk, internal audit, improvement) + Annex A: 93 controls in 4 groups (organizational, people, physical, technological); the statement of applicability (SoA) |
| **SOC 2** (AICPA) | an auditor's report for the service's customers | Trust Services criteria: security (mandatory) + optionally availability, processing integrity, confidentiality, privacy. Type I — the design of controls on a date; type II — operation over a period (usually 6–12 months) |
| **PCI DSS 4.0** | requirements for payment card data | you reduce the scope with tokenization at the payment provider |
| **GDPR (RODO)**, **NIS2**, **DORA** (EU) | law: personal data; cybersecurity of essential and important entities; digital operational resilience of the financial sector | incident notification and risk management obligations — interpreted by the legal department |

## The mapping procedure
1. **A control register** (one list for the organization): ID, description, owner, how it works, evidence, frequency.
2. **Many-to-many mapping**: one control (e.g. "phishing-resistant MFA for all administrative accounts")
   meets requirements in several frameworks at once — do not keep separate lists per audit.
3. **Automatic evidence** where possible: policies as code and their results in CI, an export of the IAM configuration, CSPM findings,
   PR history with reviews (branch protection), deployment logs, scan reports, access review records. Evidence has a date
   and a source; screenshots only where there is no other way.
4. **Gaps** as tasks with an owner and a deadline; exceptions with risk acceptance (arch-threat-modeling) and a review date.
5. **Continuity**: a control that works only before the audit will not pass SOC 2 type II.

## Where the factory already supplies evidence
Branch protection and review (ops-ci-cd), dependency scans and SBOM (ops-supply-chain-security), the identity inventory
and rotation (ops-secrets-identities), IaC with a plan in the PR and drift detection, postmortems
and restore exercises (ops-sre-incidents), threat models (arch-threat-modeling), the decision log and ADRs
(core-project-record).

## Sources
- NIST Cybersecurity Framework 2.0 (02.2024); ISO/IEC 27001:2022; AICPA Trust Services Criteria
- [roadmap.sh — DevSecOps](https://roadmap.sh/devsecops) (audit & compliance mapping, SOC 2, ISO 27001, NIST)
Described in our own words.
