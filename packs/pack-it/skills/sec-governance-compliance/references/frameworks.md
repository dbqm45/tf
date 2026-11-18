# Compliance frameworks — facts and pitfalls

State as of 2026-10-17. Secondary sources; before quoting in a contract or an offer check the text of the standard.

## ISO/IEC 27001:2022
- An information security management system (ISMS), certifiable by a certification body.
- Clauses 4–10 are mandatory (no exclusions): 4 context and scope, 5 leadership and policy, 6 planning
  (risk assessment, the treatment plan, objectives), 7 support (resources, competence, awareness, documented information),
  8 operation (carrying out the risk assessment and treatment), 9 evaluation (monitoring, internal audit, management
  review), 10 improvement (nonconformities, corrective actions).
- Annex A: 93 controls in 4 themes (organizational, people, physical, technological), replaced 114 controls
  in 14 domains from the 2013 edition. Control details: ISO/IEC 27002:2022.
- The Annex A controls are not a list "to tick off": they follow from the risk assessment (the process: **sec-risk-management**),
  and the **SoA** shows which ones you apply, why and whether they are implemented. An exclusion requires a justification.
- Amendment 1:2024 added climate change to clauses 4.1 and 4.2 as an issue relevant to the context.
- The transition period for the 2013 edition ended on 2025-10-31 (secondary sources) — the certificate must concern the 2022 edition.
- Pitfall: the certificate scope is written into the certificate; the customer reads the scope, not just the logo.

## NIST CSF 2.0
- A voluntary framework, without certification; released in February 2024; addressed to all organizations.
- Functions: Govern (new: strategy, roles, policies, the supply chain), Identify, Protect, Detect, Respond, Recover →
  categories → subcategories. Good for a conversation with the board and for a maturity self-assessment (current and target profile).
- Pitfall: "CSF compliant" does not exist as a status; you say "we assessed ourselves against CSF 2.0, target profile: …".

## SOC 2 (AICPA)
- A report by an independent auditor (CPA) on the controls of a service organization; not a certificate. Criteria: *2017 Trust
  Services Criteria with Revised Points of Focus – 2022* (the points of focus were changed in 2022, the criteria were not).
- Categories: Security (mandatory; the common criteria CC), Availability, Processing Integrity, Confidentiality, Privacy.
  You choose the scope of categories according to your promises to customers.
- **Type I**: whether the design of the controls is appropriate on a date. **Type II**: whether the controls operated effectively over a period
  (usually 6–12 months; the first report is sometimes shorter [unverified]). Enterprise customers usually demand Type II.
- The system description and the **complementary user entity controls (CUEC)** as well as the subservice organizations' controls (carve-out or inclusive)
  are read by the customer — they affect its vendor risk assessment.
- Pitfall: exceptions in the report do not invalidate it, but the customer reads them; missing evidence from the period is an exception.

## PCI DSS v4.0.1
- The PCI SSC Council's standard for entities that store, process or transmit card data or
  affect its security. v4.0.1 was published on 2024-06-11 as a limited revision of v4.0 (without new
  requirements); v4.0 was retired on 2024-12-31.
- The "future-dated" requirements from v4.0 became mandatory from 2025-03-31; the number of requirements differs between sources (51 or 52)
  [unverified — check the Summary of Changes].
- The validation level (QSA, SAQ, ROC/AOC) depends on the role and the volume, it is set by the acquirer or the card brand.
- Further changes: one source mentions a consultation on a revision in 2026 [unverified]; check pcisecuritystandards.org.
- Pitfall: the PCI scope is everything that touches card data; tokenization and segmentation reduce it most effectively.

## Other frameworks to recognize (without a description)
NIS2, DORA — EU law, interpreted by a lawyer; ISO 42001 and the AI Act — **ai-governance-compliance**; RODO (GDPR) —
**arch-privacy-compliance**; ISO 27017/27018 — extensions for the cloud and for personal data in the cloud (to 27001).
