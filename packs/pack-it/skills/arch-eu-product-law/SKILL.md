---
name: arch-eu-product-law
description: Use when the EU rules for a digital product with AI must be established — Data Act, PLD, obligations with deadlines.
metadata:
  review: "2027-01-18"
  catalog: "Use when you must establish which EU rules apply to building a digital product (SaaS, a web or mobile application, software with AI) and from when — qualifying questions (personal data, AI, a product with digital elements, switching providers, the financial sector, a service on the EAA list), a map of obligations with the act, article, application date and check date, the place in the code; topics without a separate skill: the Data Act (switching cloud and SaaS providers, switching and data transfer charges, data export), the PLD (liability for defective software). It routes to the neighbours: GDPR and DPIA → arch-privacy-compliance, NIS2, DORA and CRA → sec-eu-regulations, AI Act → ai-governance-compliance, EAA and WCAG → ux-accessibility. Outside the factory's scope (notes in references/outside-factory-scope.md): DSA, consumer law, KSeF, ViDA. It is not legal advice; a lawyer or the DPO makes the decisions."
  keywords: "które przepisy UE dotyczą, jakie przepisy nas dotyczą, mapa obowiązków prawnych, prawo UE dla SaaS, prawo UE dla oprogramowania z AI, zgodność produktu z prawem, Data Act, akt w sprawie danych, zmiana dostawcy chmury, zmiana dostawcy SaaS, przeniesienie danych do konkurencji, opłaty za eksport danych, egress, PLD, odpowiedzialność za produkt, wadliwe oprogramowanie, which EU rules apply, which regulations apply to us, map of legal obligations, EU law for SaaS, EU law for AI software, product legal compliance, switching cloud provider, switching SaaS provider, moving data to a competitor, data export charges, product liability, defective software"
---

# EU law for a digital product — a map of obligations

**The agent's role:** it prepares a preliminary map of the rules and obligations for the product, with the article, the deadline, the source
and the place in the code. **This is not legal advice** — the map goes to a lawyer or the DPO, who decides on the qualification.
Every fact has a check date; what was not confirmed in the text of the act, you mark [unverified] or [secondary].

**Scope:** the IT factory deals with law only within the scope of building software, also with AI. The DSA, consumer law
(withdrawal, the withdrawal button), KSeF and ViDA are outside the scope — the former notes are in
`references/outside-factory-scope.md`; you direct questions about them to a lawyer, accounting or the product owner.

## 1. Qualifying questions (first, before you list acts)
You take the answers from the project's code and documents (`scout`), you ask the human about the rest:

| # | Question | "Yes" brings in |
|---|---|---|
| Q1 | Do you process personal data? | GDPR → arch-privacy-compliance |
| Q2 | Does the product use or provide AI (chat, content generation, scoring)? | AI Act → ai-governance-compliance |
| Q3 | Do you sell software or a device installed at the customer's (not pure SaaS)? | CRA → sec-eu-regulations; PLD |
| Q4 | Are you a cloud or SaaS provider from which the customer can move to a competitor? | Data Act (switching providers) |
| Q5 | The financial sector or a critical service (NIS2)? | DORA, NIS2 → sec-eu-regulations |
| Q6 | Is the product a shop, banking, an e-book, tickets or another service on the EAA list? | EAA → ux-accessibility |

The PLD applies to practically all software placed on the market in the course of business (also SaaS).

## 2. Map of acts (as of 2026-10-18, PLD 2026-10-20, secondary sources — details in `references/acts-and-obligations.md`)

| Act | When it applies | Deadline | Skill |
|---|---|---|---|
| Data Act, Reg. (EU) 2023/2854 | a provider of data processing services (cloud, SaaS): switching providers, data export | application 12.09.2025 [unverified]; switching charges reduced to direct costs, from 12.01.2027 a ban (Art. 29) [secondary] | this one |
| PLD, Dir. (EU) 2024/2853 | software as a product, no-fault liability for damage | transposition by 9.12.2026; products placed on the market after that date; in PL draft UC163 (consultation closed 22.09.2026, risk of delay) [secondary] | this one |
| GDPR 2016/679 | personal data | from 25.05.2018 | arch-privacy-compliance |
| AI Act 2024/1689 after Reg. 2026/1744 | AI systems | per the skill; Art. 50 [unverified] | ai-governance-compliance |
| CRA 2024/2847, NIS2, DORA | products with digital elements; essential sectors; finance | CRA: reporting from 11.09.2026, the rest 11.12.2027 | sec-eu-regulations |
| EAA, Dir. 2019/882 | selected B2C products and services | from 28.06.2025 | ux-accessibility |

The table is a starting point, not a result: before the map is handed over, `researcher` checks every date and article an obligation
follows from in EUR-Lex or ISAP (`python3 .tf/factory/facts.py`, if the project keeps a fact base).

## 3. Procedure
1. **Qualification:** answers to Q1–Q6 with evidence (a file, a document) or from the human's answer.
2. **The role in each act:** provider, manufacturer, deployer, importer — the obligations depend on the role.
3. **Map of obligations:** one row = one obligation: act and article · obligation · from when · check date
   and source · place in the code or process (e.g. data export, AI information in the interface) · owner · status.
4. **Neighbours:** you only list GDPR, the AI Act, NIS2/DORA/CRA and the EAA and hand them to their skills — you do not repeat their content.
5. **Gaps in the code:** obligations that require features (data export in a portable format, information
   about switching providers) go as tasks to the backlog with an acceptance criterion.
6. **Questions for a lawyer:** uncertain qualifications (e.g. "are we a provider of a data processing service within the meaning of
   the Data Act?") you list separately; topics outside the factory's scope also go on this list.
7. Record: `docs/project/04-architecture/<date>-legal-map.md` (core-project-record) with a review date.

## Rules
- This skill's facts come from secondary sources: at the start of work remind the human to check them in EUR-Lex
  and ISAP (list: `docs/project/archive/research/20261018-prawo-ue-produkt.md`) and say which map items depend on them.
- A legal fact without a source and a date does not go into the map as certain; you mark a secondary source [secondary].
- A deadline that has already passed you describe as in force — with the question whether the product meets it.
- A directive works through a national law: give the transposition state in PL or [unverified].
- You check exemptions (microenterprises, small companies) in the text of the act, you do not assume them.
- The "law" dimension in a code audit (eng-code-audit) is performed by `maja-product-compliance` per this skill.

## Example
**Situation:** "A B2B SaaS from Poland: an AI assistant generates reports from customer data, customers can move data to another
provider. Which EU rules apply to us?"
**Result (an abbreviated map, not legal advice — for verification by a lawyer):**
- Q1 yes, Q2 yes, Q3 no (pure SaaS), Q4 yes, Q5 no, Q6 no [to be confirmed].
- Data Act (2023/2854): switching providers and data export from 12.09.2025 [unverified]; switching charges
  only direct costs, from 12.01.2027 a ban (Art. 29) [secondary].
- PLD (2024/2853): liability for defective software, also SaaS and an AI model in the product, for products
  placed on the market after 9.12.2026; in PL draft UC163 in progress [secondary]. In the code: a trace of versions and security
  updates, documentation in case of a presumption of defect.
- AI Act: the transparency obligation for AI-generated content (Art. 50) — deadline [unverified] → ai-governance-compliance.
- GDPR (customer data in prompts, the model processor) → arch-privacy-compliance.
- Gaps in the code: no full export of customer data in `app/settings/export` (a backlog task).

## Checklist
- [ ] Q1–Q6 answered with evidence or the human's answer
- [ ] the product's role in each act named
- [ ] every obligation: act, article, from when, check date, source, place in the code or process
- [ ] [unverified] / [secondary] where the act's text is missing; the transposition state of directives in PL
- [ ] GDPR, AI Act, NIS2/DORA/CRA, EAA handed to the neighbouring skills
- [ ] questions for a lawyer and backlog tasks listed; the disclaimer "not legal advice"

## Sources
The texts of the acts in EUR-Lex and ISAP could not be read in the session (proxy 403, 2026-10-18); dates and articles from commentaries
by law firms and industry sites, accessed 2026-10-18 — the list in `references/acts-and-obligations.md`. Described in our own words.
