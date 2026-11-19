---
name: ai-governance-compliance
description: Use for the compliance of an AI system with the AI Act — role, risk class, obligations and deadlines, NIST AI RMF, ISO 42001, an AI policy, incidents.
metadata:
  review: "2027-01-17"
  catalog: "Use when you must establish what the AI Act (Regulation (EU) 2024/1689) and AI governance frameworks mean for a system or a company — an inventory of AI systems, the role (provider, deployer, importer, distributor, Art. 25), the risk class (prohibited practices, high risk under Annex III and products, transparency under Art. 50, minimal risk, general-purpose AI models), obligations per role (risk management, data, technical documentation, record-keeping, human oversight, conformity assessment, registration, post-market monitoring, serious incidents, AI literacy, FRIA), the application dates taking the Digital Omnibus into account, NIST AI RMF and the generative AI profile (AI 600-1), ISO/IEC 42001 and its relation to 27001, impact assessment, model and dataset cards, the basics of fairness and bias, the AI incident process, an AI use policy for employees, the interface with the GDPR (Art. 22). Not for the GDPR, DPIA and retention (arch-privacy-compliance), the threat model (arch-threat-modeling), quality measurement and evaluation (ai-evals), the security of the agent's work (core-agent-security) or AI product strategy (ai-product-management). It is not legal advice."
  keywords: "AI Act, akt o sztucznej inteligencji, rozporządzenie o AI, zgodność AI, system wysokiego ryzyka, praktyki zakazane, dostawca AI, podmiot stosujący, deployer, provider, ocena zgodności, znak CE, NIST AI RMF, ISO 42001, 42001, zarządzanie AI, AI governance, polityka AI, polityka użycia AI, regulamin AI dla pracowników, rejestr systemów AI, FRIA, ocena wpływu na prawa podstawowe, karta modelu, model card, stronniczość, bias, fairness, incydent AI, kompetencje AI, AI literacy, Digital Omnibus, model ogólnego przeznaczenia, GPAI, etyka AI, odpowiedzialna AI, czy nasz system podlega AI Act, znak wodny, watermark, oznaczanie treści ai, c2pa, content credentials, kodeks praktyk oznaczania, art. 50 ust. 2, treści generowane przez ai, artificial intelligence act, AI regulation, AI compliance, high-risk system, prohibited practices, AI provider, conformity assessment, CE marking, AI policy, AI use policy, AI rules for employees, register of AI systems, fundamental rights impact assessment, AI incident, general-purpose AI model, AI ethics, responsible AI, does our system fall under the AI Act, labelling AI content, labelling code of practice, Art. 50(2), AI-generated content"
---

# AI compliance and governance (AI Act, NIST, ISO 42001)

**The agent's role:** it prepares the inventory, a preliminary classification, the obligations matrix and the list of evidence, and also points out
the decisions. **This is not legal advice.** The role, the risk class, the exceptions and the notifications are decided by a human with a lawyer
or the data protection officer (DPO). Artifact: `docs/project/04-architecture/ai-compliance.md`.
GDPR, DPIA, retention — **arch-privacy-compliance**; security threats — **arch-threat-modeling**; quality
measurement — **ai-evals**; product strategy — **ai-product-management**; instructions from content — **core-agent-security**.

## Procedure
1. **Inventory.** For each AI system (your own, bought, built into SaaS, "shadow" AI used by
   employees): the purpose, the model and the provider, the input and output data, who uses it, whom the decisions concern, the market (the EU?),
   the owner. Without the inventory the rest is guesswork.
2. **Scope and role** (Art. 2–3, 23–25). Establish it separately for each system:
   - **provider** — develops the system or model, or places it on the market under its own name and trademark;
   - **deployer** — uses the system in a professional activity;
   - **importer** and **distributor** — the supply chain into the EU;
   - the role **changes** (Art. 25): a deployer becomes a provider when it puts its own trademark on the system, substantially
     modifies it or changes its intended purpose (e.g. fine-tuning for credit scoring). Record the basis.
   - The regulation also covers providers outside the EU if the output of the system is used in the EU. "We are not in the EU" does not
     close the matter.
3. **Risk class** — check in this order:
   1. **Prohibited practices** (Art. 5, from 2025-02-02): e.g. subliminal manipulation, social scoring, emotion recognition
      at work and in schools, untargeted scraping of facial images. A hit = stop and escalate to a lawyer.
   2. **High risk** (Art. 6): a system as a safety component of a product covered by the law in Annex I, or
      a case from **Annex III** (among others recruitment and the management of workers, education, credit scoring,
      access to essential services, law enforcement, migration, the administration of justice). The exception in Art. 6(3) (a system
      without a material influence on the outcome of a decision) requires a documented assessment and registration; profiling of persons excludes it.
   3. **Transparency** (Art. 50): a chatbot (inform people that they are interacting with AI), synthetic content (marking
      in a machine-readable format; layers, the code of practice of 2026-06 and the limits of watermarking:
      `references/technical-tagging.md`), deepfakes, emotion recognition. It can overlap with class 2.
   4. **Minimal risk** — no obligations beyond literacy (Art. 4); codes of conduct are voluntary.
   5. **General-purpose model** (GPAI, Art. 51–55) — a separate axis for the model provider: technical documentation,
      a copyright policy, a summary of the training data; with systemic risk additionally evaluation and reporting
      incidents. An integrator of someone else's model is usually not a GPAI provider, but can be the provider of a system.
4. **Obligations per role** — the matrix in `references/matrix-and-evidence.md` (provider of a high-risk system: Art. 9–15, 17, 43,
   47–49, 72–73; deployer: Art. 26–27; everyone: Art. 4). For each row: the owner, the evidence, the deadline, the status.
   A deployer of a high-risk system assigns human oversight (Art. 26(2)): trained persons with the competence
   and the authority to challenge and reject the system's output.
5. **Deadlines** (as of 2026-10-17): check the table below and **the date for your system**. When planning, give the date
   with a source footnote; conflicting ones — both variants with [unverified].
6. **Voluntary frameworks.** NIST AI RMF 1.0 (Govern, Map, Measure, Manage) and the AI 600-1 profile organize risks;
   ISO/IEC 42001:2023 is a certifiable AI management system (a structure like ISO 27001, they can be combined into one
   management system). They do not replace the AI Act, but they provide evidence. Details: `references/frameworks-and-practice.md`.
7. **Practice:** impact assessment (fundamental rights), model and dataset cards, a bias test, the AI incident process,
   an AI use policy for employees — patterns in `references/frameworks-and-practice.md`.
8. **The interface with the GDPR.** A solely automated decision with a significant effect (Art. 22 GDPR) and a DPIA — assess them in arch-privacy-compliance.
   A deployer of a high-risk system uses the provider's instructions for the DPIA (Art. 26(9) AI Act).
9. **Result** into `ai-compliance.md`: inventory → role → class with a justification → obligations matrix → gaps and evidence →
   decisions for the human → deadlines. At the top: "Wstępna klasyfikacja robocza, nie porada prawna; zatwierdza: [prawnik/IOD]"
   (a preliminary working classification, not legal advice; approved by: [lawyer/DPO]).

## Application dates — as of 2026-10-17
| Date | What | Status |
|---|---|---|
| 2024-08-01 | entry into force of Regulation (EU) 2024/1689 | certain |
| 2025-02-02 | prohibitions (Art. 5) and AI literacy (Art. 4) | certain |
| 2025-08-02 | GPAI obligations, governance, penalties | certain |
| 2026-08-02 | general application, including Art. 50; Art. 50(2) for systems already on the market by 2026-12-02 | Art. 50 from 2026-08-02 confirmed (the Commission's page on the code, 2026-11-01); 2026-12-02 [unverified] |
| 2026-12-02 | a new prohibition (intimate content without consent, CSAM) | [unverified] |
| 2027-12-02 | high risk under Annex III (was 2026-08-02) | [unverified] |
| 2028-08-02 | high risk under Annex I, products (was 2027-08-02) | [unverified] |

The postponements are introduced by the "Digital Omnibus on AI", Regulation (EU) 2026/1744, published 2026-07-24, in force from
2026-07-27 — according to secondary sources (law firms); EUR-Lex was unavailable in the session. The change also softened Art. 4: an obligation
"to take measures supporting" literacy instead of ensuring its level. Before quoting, confirm the text
in EUR-Lex (OJ L 2026/1744).

## Example
Input: "A company from Warsaw buys a SaaS tool for ranking CVs (a provider from the USA) and adds its own recruitment chatbot
on a model API."

Result (excerpt) [example]:

| System | Role | Class | Justification | Main obligations |
|---|---|---|---|---|
| CV ranking | deployer | high risk (Annex III, employment) | assessment and selection of candidates; profiling excludes the exception in Art. 6(3) | the provider's instructions, human oversight, logs ≥6 months, informing candidates, literacy; the decision on FRIA and DPIA — lawyer/DPO |
| Recruitment chatbot | provider of the system (its own product on someone else's model) | transparency (Art. 50) | communicates with people | the information "you are talking to AI"; if the chatbot assesses candidates, the class rises to high risk |

Deadlines: Art. 50 from 2026-08-02 (confirmed on the Commission's page); high risk under the Omnibus from 2027-12-02 [unverified]; Art. 4 already now.

## Checklist
- [ ] an inventory of AI systems, also those built into SaaS and "shadow" AI
- [ ] the role per system, with a possible Art. 25 and a justification
- [ ] the risk class checked in order: prohibitions, high risk, Art. 50, minimal, GPAI
- [ ] an obligations matrix with an owner, evidence and a deadline
- [ ] deadlines verified in EUR-Lex; conflicting ones marked [unverified]
- [ ] an AI use policy, literacy (Art. 4), the AI incident process
- [ ] the GDPR interface (Art. 22, DPIA) handed over to arch-privacy-compliance
- [ ] the "not legal advice" note and the approver (lawyer/DPO)

## Additional materials
- `references/matrix-and-evidence.md` — the obligations matrix by role, the list of evidence, penalties; read it when creating `ai-compliance.md`.
- `references/frameworks-and-practice.md` — NIST AI RMF, AI 600-1, ISO 42001 vs 27001, impact assessment, cards, bias, incident, policy; read it when implementing AI governance.

## Sources
- Regulation (EU) 2024/1689 (AI Act) — eur-lex.europa.eu; article numbers from the text of the regulation known
  from our own knowledge, not confirmed at the source in the session [unverified at the source].
- Regulation (EU) 2026/1744 (Digital Omnibus on AI) — dates from law firms (White & Case, Lewis Silkin, Freshfields,
  Gibson Dunn) and the artificialintelligenceact.eu site, accessed 2026-10-17; the commentaries differ on Art. 50(2).
- NIST AI RMF 1.0 (NIST AI 100-1, January 2023) and AI 600-1 Generative AI Profile (July 2024) — nist.gov, secondary sources, accessed 2026-10-17.
- ISO/IEC 42001:2023 — iso.org [unverified in the session].
Described in our own words; it is not legal advice.
