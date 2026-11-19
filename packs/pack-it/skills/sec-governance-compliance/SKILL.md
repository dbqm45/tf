---
name: sec-governance-compliance
description: Use for ISO 27001, SOC 2, NIST CSF or PCI DSS — choosing frameworks, scope, a control matrix, evidence, internal and certification audits.
metadata:
  review: "2027-04-17"
  catalog: "Use when a company must demonstrate security through frameworks or an audit — choosing a framework by motive (customer, regulation, sector), ISO/IEC 27001:2022 (clauses 4–10, Annex A, the Statement of Applicability), NIST CSF 2.0 (six functions with Govern), SOC 2 (Trust Services Criteria, Type I and II), PCI DSS v4.0.1, defining the scope, mapping one control onto many frameworks, the hierarchy of policies and standards, collecting evidence and continuous compliance, the internal audit, the course of a certification audit, typical gaps. Result: a control matrix and an audit readiness plan. Not for RODO (GDPR) and DPIA (arch-privacy-compliance), the AI Act (ai-governance-compliance), the risk process and risk acceptance (sec-risk-management), handling incidents and vulnerabilities (ops-security-operations) or a threat model (arch-threat-modeling). Not legal advice or a conformity assessment."
  keywords: "ISO 27001, 27001, ISMS, SZBI, deklaracja stosowania, SoA, Załącznik A, SOC 2, SOC2, typ II, Trust Services Criteria, NIST CSF, CSF 2.0, PCI DSS, certyfikacja, certyfikat bezpieczeństwa, audyt bezpieczeństwa, audyt zewnętrzny, audyt wewnętrzny, gotowość do audytu, macierz kontroli, mapowanie kontroli, polityka bezpieczeństwa, dowody dla audytora, ciągła zgodność, compliance, kwestionariusz klienta, wymóg klienta enterprise, framework bezpieczeństwa, statement of applicability, Annex A, Type II, certification, security certificate, security audit, external audit, internal audit, audit readiness, control matrix, control mapping, security policy, evidence for the auditor, continuous compliance, customer questionnaire, enterprise customer requirement, security framework"
---

# Compliance frameworks and security audits (ISO 27001, SOC 2, NIST CSF, PCI DSS)

**The agent's role:** it prepares the choice of frameworks, the scope, the control matrix, the list of evidence and the readiness plan. **It does not
determine compliance** — the auditor does that, and a lawyer interprets the law. This is not legal advice. Artifact:
`docs/project/04-architecture/compliance.md` (core-project-record). RODO (GDPR) — **arch-privacy-compliance**; the AI Act and ISO 42001 —
**ai-governance-compliance**; the risk process and acceptances — **sec-risk-management**; incidents and vulnerabilities —
**ops-security-operations** (its `.claude/skills/ops-security-operations/references/compliance.md` is a summary; here is the full procedure).

## Procedure
1. **A motive, not a fashion.** Record who demands what: a customer (a contract, a questionnaire), a regulation (NIS2, DORA — a lawyer), a sector
   (payment cards), the board (putting things in order). The motive points to the framework:
   | Motive | Usually | Note |
   |---|---|---|
   | customers in the EU and tenders, a certificate | ISO 27001 | a certificate from an accredited body |
   | SaaS customers from the USA | SOC 2 | an auditor's report, not a certificate |
   | you process or affect card data | PCI DSS | a contractual obligation towards the acquirer/the brands |
   | no requirement, you want to put things in order | NIST CSF 2.0 | voluntary, without certification |
   Do not collect frameworks "just in case": one framework as the backbone, the rest through mapping (step 5).
2. **The scope** — the cheapest lever. Record: products and services, locations, systems, people, vendors in the chain,
   exclusions with a justification. A scope too narrow will not meet the customer's expectations, one too broad multiplies the evidence. For PCI
   reduce the scope with tokenization and segmentation.
3. **The backbone framework** — facts and pitfalls in `references/frameworks.md`. A summary of the state as of 2026-10-17:
   - **ISO/IEC 27001:2022** — clauses 4–10 (context, leadership, planning with risk assessment, support, operation,
     performance evaluation with the internal audit and the management review, improvement) plus **Annex A: 93 controls
     in 4 themes** (organizational 37, people 8, physical 14, technological 34). The controls are chosen by the risk assessment;
     the **Statement of Applicability (SoA)** lists every control: applied / not, the justification, the status.
   - **NIST CSF 2.0** (February 2024) — six functions: Govern, Identify, Protect, Detect, Respond, Recover; Govern is new.
   - **SOC 2** — Trust Services Criteria: Security mandatory, optionally Availability, Processing Integrity,
     Confidentiality, Privacy. **Type I** — the design of the controls on a date; **Type II** — effectiveness over a period (usually 6–12 months).
   - **PCI DSS v4.0.1** — the only version in force; the future-dated requirements apply from 2025-03-31.
4. **The document hierarchy**: a policy (what and why, approved by the board, 1–2 pages) → a standard (mandatory
   parameters, e.g. MFA for privileged accounts) → a procedure (how, step by step) → evidence (a record of execution). A policy
   without a standard and evidence is decoration; a procedure without a policy has no mandate.
5. **The control matrix** — one register for the organization, not a list for the audit. Fields: control ID, a description of how it works,
   owner, system, frequency, evidence (source, path), **many-to-many mapping** (A.5.15, CC6.1, CSF PR.AA,
   PCI 8.x). One control "phishing-resistant MFA for administrators" satisfies several frameworks. Template: `references/matrix-and-plan.md`.
6. **A gap analysis** against the backbone framework: for each control a status (works and there is evidence / works without evidence /
   to be implemented / not applicable). A gap is a task with an owner and a deadline; an exception goes to risk acceptance
   (**sec-risk-management**), it is not skipped "quietly".
7. **Evidence and continuous compliance.** Evidence has a date, a source and an author; automatic evidence (an IAM export, CI results, PR history,
   scans) beats a screenshot. A control that works only before the audit will not pass SOC 2 Type II or a surveillance audit.
   The schedule: access reviews, restore tests, training, vendor reviews — a calendar with an owner.
8. **The internal audit and the management review** before the external one: independent of the control owner, according to
   the audit programme plan; findings as nonconformities with corrective action. ISO requires both.
9. **The external audit** — its course and preparation in `references/matrix-and-plan.md`: ISO — stage 1 (documentation) and stage 2
   (implementation), then surveillance audits in the certification cycle [unverified: the cycle length and frequency are set by the body];
   SOC 2 — the observation period, then the report; PCI — the assessment (a QSA or a self-assessment according to the level).
10. **The result** in `compliance.md`: motive → scope → framework → matrix → gaps → readiness plan (date, owners, evidence)
    → decisions for a human. At the top: "Working preparation, not a conformity assessment; approved by: [CISO/auditor]".

## Typical gaps
A scope without vendors · policies copied from a template and unknown to the teams · an SoA without justifications · evidence collected
in the audit week · no control owner · access reviews "done", without a record · the internal audit
performed by the author of the control · exceptions without an expiry date · compliance confused with security (the control exists on paper).

## Example
Input: "A B2B SaaS (40 people, AWS). Two customers from the EU demand ISO 27001, one from the USA SOC 2. A year to act."

Result (a fragment) [example]:
- Motive: customer contracts. Backbone: ISO 27001 (a certificate for the EU), SOC 2 Type II through mapping, not a separate project.
- Scope: product X, the AWS prod and staging accounts, the engineering and support team; out of scope the office (remote work, justified).
- Matrix: K-014 "AWS access review every quarter" → A.5.18, CC6.2, PR.AA; evidence: an IAM export + a ticket with a signature; owner: the CTO.
- Plan: m1 scope and risks; m2–4 gaps and policies; m5–6 evidence collected automatically; m7 internal audit and management
  review; m8 stage 1 and 2; SOC 2 Type I in m8, the Type II period from m9.

## Checklist
- [ ] the motive and the backbone framework recorded; the other frameworks through mapping
- [ ] the scope with exclusions and vendors; approved by management
- [ ] the hierarchy: policy → standard → procedure → evidence
- [ ] a control matrix with an owner, evidence and mapping; an SoA with justifications (ISO)
- [ ] gaps as tasks; exceptions to risk acceptance
- [ ] a calendar of periodic controls and automatic evidence
- [ ] an independent internal audit; a management review
- [ ] the statement "not a conformity assessment, not legal advice" and the approver

## Additional materials
- `references/frameworks.md` — ISO 27001, NIST CSF 2.0, SOC 2, PCI DSS: structure, versions, dates, pitfalls; read it when choosing and for the gap analysis.
- `references/matrix-and-plan.md` — the control matrix template, the audit readiness plan, the course of audits; read it when creating `compliance.md`.

## Sources
- ISO/IEC 27001:2022 and Amendment 1:2024 (climate) — iso.org; control counts per secondary services (Sprinto, Presencis), accessed 2026-10-17 [unverified at the source].
- NIST Cybersecurity Framework 2.0 (February 2024) — nist.gov/cyberframework; six functions per secondary sources, accessed 2026-10-17.
- AICPA, *2017 Trust Services Criteria with Revised Points of Focus – 2022* — aicpa-cima.com; per secondary sources, accessed 2026-10-17.
- PCI SSC, PCI DSS v4.0.1 (published 2024-06-11) — pcisecuritystandards.org; dates per secondary sources, accessed 2026-10-17.
Described in our own words; not legal advice.
