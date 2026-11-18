# Voluntary frameworks and the practice of AI governance

## NIST AI RMF 1.0 and the AI 600-1 profile
- **AI RMF 1.0** (NIST AI 100-1, January 2023), voluntary. Four functions:
  - **Govern** — policies, roles, culture, accountability, oversight of suppliers;
  - **Map** — the context of use, stakeholders, possible harms, the system boundaries;
  - **Measure** — metrics, tests, bias assessment, monitoring (tools: ai-evals);
  - **Manage** — risk priorities, response, withdrawal, incidents.
- **Generative AI Profile (NIST AI 600-1, July 2024)** — adds to the four functions actions for risks specific
  to generative AI (secondary sources speak of 12 categories, among others confabulation, data privacy, intellectual
  property, harmful content, the supply chain) [unverified at the source, accessed 2026-10-17].
- Use: you fill the AI Act obligations matrix with actions from the functions; it is not a certificate or proof of compliance.

## ISO/IEC 42001:2023 and ISO/IEC 27001
- 42001 is a standard for an **AI management system** (AIMS), certifiable by external bodies. It shares the
  high-level structure with management standards (context, leadership, planning, support, operation,
  evaluation, improvement), so it combines with 27001 into one management system, with one management review
  and internal audit [unverified at the source].
- 27001 protects information (confidentiality, integrity, availability); 42001 adds AI risks: the impact on people, transparency,
  human oversight, the model life cycle, suppliers. The scopes complement each other, they do not replace each other.
- A 42001 certificate does not give a presumption of conformity with the AI Act, unless the Commission designates a harmonized standard
  [unverified — check the state of harmonized standards in the Official Journal of the EU (Dz.Urz. UE)].

## Impact assessment (AI impact / FRIA)
A description of the system and its purpose; whom it concerns (vulnerable groups); fundamental rights that may suffer (non-discrimination, privacy,
due process); the frequency and duration of use; measures of oversight and appeal; a response plan. Art. 27 requires a FRIA only in the listed
cases, but the same tool serves voluntarily for any high risk. DPIA — arch-privacy-compliance.

## Model and dataset cards
- **Model card:** the purpose and limits of use, the version, the training data (source, period, licences), metrics broken down by
  subgroups, known limitations and errors, risks, a contact, the review date.
- **Dataset card (datasheet):** why it was created, its composition, the collection method, annotations, preprocessing, consents
  and legal bases, biases, maintenance.

## Bias and fairness — the basics
1. Name the protected groups and the harm (denial of service, worse quality, stereotypes).
2. Choose a metric consistent with the goal: demographic parity, equal opportunity, calibration within groups. Metrics can be
   mutually contradictory — the choice and the justification are recorded by the human responsible for the product.
3. Measure on subgroups and cross-sections (ai-evals); large differences in errors are a finding.
4. Measures: data, thresholds, human review, appeal. Repeat after a change of the model or the data.
5. For fairness use sensitive data only with a legal basis — check in arch-privacy-compliance.

## The AI incident process
Detection (complaints, monitoring, online evaluations) → severity assessment (harm to people, a breach of the law, systemic nature) →
containment (disabling the feature, withdrawing the model, manual mode) → a human's decision on notification (Art. 73 AI Act,
GDPR Art. 33 with personal data, the provider/recipients according to contracts) → root cause and fix → an entry in the register and lessons.
Security incidents (e.g. prompt injection) are handled by ops-security-operations.

## AI use policy for employees
- Permitted tools and service tiers (business, not consumer); a ban on pasting personal data, secrets
  and code into unapproved tools.
- The human is responsible for the result; verification of facts and code; marking synthetic content when Art. 50 requires it.
- A ban on decisions about people (recruitment, work assessment, credit) without the approval of the compliance owner.
- Reporting new tools to the inventory, and incidents; training (Art. 4); a review every six months.
- Instructions from content and agent tools: core-agent-security.
