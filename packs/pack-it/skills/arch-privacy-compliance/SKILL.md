---
name: arch-privacy-compliance
description: Use when a system processes personal data (GDPR) — legal bases, minimization, retention, DPIA, processors.
metadata:
  review: "2027-04-09"
  catalog: "Use when a system processes personal data — a new feature, an integration, analytics, logs, sending data to external services (also AI) — in design and review: a data inventory (input to Art. 30) and data governance (owner, classes, field tagging), the purpose and legal basis, privacy by design and by default (minimization, pseudonymization), retention and deletion, fulfilling data subjects' rights (access, erasure, portability) also in backups, logs and at processors, data processing agreements and transfers outside the EEA, the impact assessment (DPIA), personal data breaches (72 hours), cookies. Not for authentication and passwords (be-auth-security), the threat model (arch-threat-modeling), responding to a security incident (ops-security-operations) or data management in pipelines and the AI Act (data-engineering). It is not legal advice."
  keywords: "RODO, GDPR, dane osobowe, ochrona danych, prywatność, UODO, IOD, inspektor ochrony danych, DPIA, ocena skutków, prawo do usunięcia, bycia zapomnianym, retencja danych, zgoda, cookies, ciasteczka, umowa powierzenia, wyciek danych, naruszenie ochrony danych, pseudonimizacja, anonimizacja, pod kątem RODO, zgodnie z RODO, analityka zachowań użytkowników, żądanie usunięcia danych, ład danych, klasyfikacja danych, klasy danych, właściciel danych, inwentarz danych osobowych, które kolumny zawierają dane osobowe, data governance, personal data, data protection, privacy, DPO, data protection officer, impact assessment, right to erasure, right to be forgotten, data retention, consent, data processing agreement, data leak, personal data breach, pseudonymization, anonymization, GDPR compliant, user behaviour analytics, data deletion request, data classification, data classes, data owner, personal data inventory, which columns contain personal data"
---

# Personal data protection (GDPR) in a project

**The agent's role:** it prepares the data inventory, the safeguards design, a draft impact assessment and procedures, and
points out the decisions to be made. **Legal decisions** — the basis of processing, whether a DPIA is required, whether to report
a breach, the wording of clauses — are made by a human with the data protection officer (DPO) or a lawyer. This is not legal
advice. Artifact: `docs/project/04-architecture/privacy.md` (template in core-project-record).

## Rules
1. **The inventory before the code.**
   - List: what data, whose (customers, employees, children), from where, what for, where it lives — the database, **logs, backups,
     analytics, test environments, queues, external providers** — and who has access.
   - Mark the flows on the data flow diagram from arch-threat-modeling.
   - This is input to the record of processing activities (Art. 30), kept by the controller.
   - **Data governance:** every data set has a business owner. Every field has a class: public, internal, confidential,
     personal data or special categories. The class determines access, encryption, masking in logs
     and outside production, and retention. You keep the field inventory in `docs/project/04-architecture/data-inventory.md`,
     and you also mark the class next to the field in the code. In an existing system a draft inventory comes from
     `tf analyze --only data-classification`. The requirements table, the inventory format and the order of clean-up:
     `references/data-governance.md`.
2. **A purpose and a legal basis for every purpose** (Art. 5–6):
   - the bases of Art. 6(1): a contract, a legal obligation, a legitimate interest, consent and others;
   - special categories of data (health, biometrics for identification, opinions and others of Art. 9) require an additional
     condition;
   - consent (Art. 7) only where it fits: freely given, specific, documented and possible to withdraw as easily
     as it was given;
   - behaviour analytics is usually a separate purpose with a separate basis.
3. **Privacy by design and by default** (Art. 25):
   - collect only the fields needed for the purpose; an optional field is really optional;
   - by default the narrowest visibility and the shortest storage;
   - pseudonymization — an identifier with an HMAC key instead of an email in analytics and logs;
   - aggregates instead of raw events.
   - Pseudonymized data is still personal data for whoever has the key.
4. **Retention:**
   - a storage period for every category and purpose;
   - **automatic deletion** (a retention job with a test), not "we will clean up some day";
   - logs without personal data or with a short retention;
   - backups expire in a known cycle;
   - encryption at rest matched to the data class and deletion by destroying the key (crypto-erase):
     sec-cryptography-pki (data at rest).
5. **Data subjects' rights** (Art. 12–22):
   - mechanisms in the system: data export (access, portability), rectification, erasure, restriction, objection;
   - an answer without undue delay, **at the latest within a month** (an extension by two months in justified cases,
     with information to the person);
   - erasure covers the copies at **processors** (an erasure instruction) and logs;
   - in **backups** the data expires with the backup cycle, and after a backup is restored you apply the erasure again
     (a list of erased identifiers);
   - before releasing data you verify the identity.
6. **Processors and transfers:**
   - every provider that processes data on your behalf (cloud, mailing, analytics, customer service,
     **an AI model API**) needs a data processing agreement (Art. 28) and an entry on the list;
   - a transfer outside the EEA (Chapter V) requires a basis: an adequacy decision or standard contractual
     clauses;
   - USA: the EU–US Data Privacy Framework (decision of 10.07.2023) covers only certified companies; the EU General Court dismissed
     the action against this decision on 3.09.2025 (T-553/23), and the appeal (C-703/25 P) is pending — follow the outcome.
7. **Security** (Art. 32):
   - encryption at rest and in transit, least privilege, a log of access to data, backups and restore
     tests (be-auth-security, ops-secrets-identities, ops-sre-incidents);
   - **test environments contain no real personal data** — only synthetic or effectively
     anonymized data;
   - an example from practice: UODO (the Polish DPA) fined a controller and a processor for an unsecured test database
     with real data.
8. **Data protection impact assessment (DPIA, Art. 35):**
   - required with a likely high risk, among others with profiling with significant effects, special
     categories on a large scale and monitoring public areas on a large scale;
   - in Poland also for the operations on the list of the President of UODO (M.P. 2019 item 666), e.g. biometric or location data,
     innovative technologies, combining data sets;
   - the agent prepares a draft: description, purpose, necessity, risks and measures; the controller decides with the DPO.
9. **Personal data breach** (Art. 33–34):
   - a notification to the supervisory authority (in Poland UODO) **without undue delay, where feasible within 72 hours** of becoming aware, unless the breach
     is unlikely to result in a risk;
   - with a high risk, notifying the persons;
   - you document every breach, also unreported ones;
   - a processor notifies the controller without undue delay;
   - the agent stops the leak and secures the evidence (ops-security-operations), prepares the facts for the notification,
     and a human decides on the notification;
   - the procedure with a timeline: `references/gdpr-in-practice.md`.
10. **Cookies, analytics SDKs and access to the device (the Electronic Communications Law, not only the GDPR):**
    - apart from strictly necessary ones, consent is needed before writing;
    - no pre-ticked consents (CJEU, Planet49, C-673/17);
    - refusal as accessible as consent;
    - in Poland the rules on access to the device are in the Electronic Communications Law (Prawo komunikacji elektronicznej), in force from 10.11.2024
      [the article number and the supervisory authority — check in ISAP before citing].
11. **Data in prompts to AI models** is a transfer of data to the provider:
    - you minimize and pseudonymize before sending;
    - you check the data processing agreement, the processing region and the retention at the provider;
    - you check the **service tier**: consumer apps may use conversations for training by default (at some
      providers also on a paid consumer plan), while the API and business plans usually do not by default; the setting for
      a coding tool is sometimes separate from the chat setting. You check the state of a specific provider's policy in its
      current terms and record it with a date — policies change within months;
    - a provider without a region choice and without a representative in the EU, storing data in a country without an adequacy
      decision, means a transfer outside the EEA without an Art. 45 basis — it requires a human's decision and a lawyer's assessment;
    - obligations from the AI Act: data-engineering (`.claude/skills/data-engineering/references/quality-management-and-compliance.md`).
12. **Fines** (Art. 83): up to EUR 10 million or 2% of worldwide turnover, and for breaching the principles, bases and data subjects' rights up to
    EUR 20 million or 4% (whichever is higher).

## Changes in the law — as of 2026-10-03
- The **Digital Omnibus** package (the Commission's proposal COM(2025) 837 of 19.11.2025) proposes among others:
  - notifying the authority only of high-risk breaches, within 96 hours, through a single entry point;
  - moving the cookie rules into the GDPR;
  - EU-wide lists of operations requiring a DPIA;
  - clarifying the definition of personal data.
- This is a **proposal in progress** (the Council without a mandate in June 2026, Parliament at the committee stage). Until it is adopted
  and enters into force the current rules apply — do not design for 96 hours.

## Checklist
- [ ] a data inventory (with logs, backups, tests, providers) and the flows on the diagram
- [ ] the owner and class of every data set; personal fields marked in the code and in `data-inventory.md`
- [ ] a purpose and a legal basis for every purpose — approved by a human/the DPO
- [ ] minimization and pseudonymization in the design; no real data in tests
- [ ] retention periods and automatic deletion with a test
- [ ] handling of data subjects' rights, including erasure at processors and after a backup restore
- [ ] a list of processors with data processing agreements and the basis for transfers outside the EEA
- [ ] the DPIA decision recorded in `decisions.md`; a breach procedure with roles and 72 hours

## Sources
- Regulation (EU) 2016/679 (GDPR) — eur-lex.europa.eu (Art. 5–7, 9, 12–22, 25, 28, 30, 32–35, 44–49, 83)
- EDPB: guidelines 4/2019 (Art. 25, version 2.0 of 20.10.2020), 9/2022 (breach notification, version 2 of 2023),
  01/2025 (pseudonymization, consultation), opinion 08/2024 ("consent or pay") — edpb.europa.eu
- UODO: the list of operations requiring a DPIA (M.P. 2019 item 666); decisions and announcements 2025–2026 — uodo.gov.pl
- EU General Court T-553/23 Latombe (3.09.2025), appeal C-703/25 P; CJEU C-673/17 Planet49 — curia.europa.eu
- Digital Omnibus: procedure 2025/0360(COD) (oeil.europarl.europa.eu), joint EDPB-EDPS opinion 2/2026
- Electronic Communications Law (Prawo komunikacji elektronicznej), Dz.U. 2024 item 1221 (in force from 10.11.2024)
- The 10xDevs course, ed. 3 (2026), module 1, lesson 3 (data and code at model providers) — training material (accessed 2026-10-09).
Accessed 2026-10-03. Described in our own words; not legal advice.
