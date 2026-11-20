---
name: arch-privacy-compliance
description: Use when a feature, integration, log, analytics or AI service touches personal data — GDPR inventory, legal basis, retention, erasure, DPIA, breaches.
metadata:
  review: "2027-05-20"
  catalog: "Use when designing or reviewing personal-data processing under GDPR (RODO) — the data inventory and data governance (owners, data classes, field markers, the data-classification analyzer), purpose and legal basis (Art. 6, Art. 9), privacy by design (minimisation, pseudonymisation), retention and automatic deletion, data-subject requests (erasure, export) including processors and backups, processors and transfers outside the EEA, security of processing, test data, DPIA, personal data breaches (72 hours), cookies and the Polish Electronic Communications Law, personal data sent to AI model providers, fines and pending law. Prepares drafts; legal decisions stay with a human and the DPO. Not for authentication and password storage (be-auth-security), the threat model (arch-threat-modeling), incident response (ops-security-operations), data pipelines and AI Act data management (data-engineering)."
  keywords: "RODO, GDPR, dane osobowe, dane wrażliwe, podstawa prawna, zgoda użytkownika, minimalizacja danych, retencja danych, okres przechowywania, usuwanie danych, prawo do bycia zapomnianym, żądanie usunięcia konta, eksport danych, DPIA, ocena skutków, inspektor ochrony danych, IOD, UODO, wyciek danych, naruszenie ochrony danych, zgłoszenie naruszenia, 72 godziny, baza testowa z prawdziwymi danymi, dane testowe, pseudonimizacja, anonimizacja, maskowanie danych w logach, dane w logach, analityka zachowań, cookies, ciasteczka, baner cookies, prawo komunikacji elektronicznej, PKE, podmiot przetwarzający, umowa powierzenia, transfer poza EOG, dane do modelu AI, dane klientów w promptach, dostawca AI trenuje na danych, klasyfikacja danych, które kolumny zawierają dane osobowe, właściciel danych, ład danych, inwentarz danych, rejestr czynności przetwarzania, kary RODO, personal data, legal basis, consent, data minimisation, retention period, right to erasure, delete my account, data subject request, DPIA, data protection officer, data breach, breach notification, test database with real data, pseudonymisation, PII in logs, cookie consent, ePrivacy, processor agreement, DPA, data transfer outside EEA, customer data to an AI provider, data classification, data owner, data governance, data inventory, record of processing"
---

# Personal data under GDPR — inventory first, decisions with a human

**Role split.** The agent builds the inventory, designs safeguards, drafts the DPIA and procedures, and flags every
decision that is legal in nature. A human with the DPO or a lawyer decides: the legal basis, whether a DPIA is required,
whether to notify a breach, the wording of clauses. Every answer ends with: *"This is not legal advice — confirm with
your DPO or lawyer."*

## Artefacts
- `docs/project/04-architecture/privacy.md` — purposes, bases, retention, processors, measures (template: core-project-record).
- `docs/project/04-architecture/data-inventory.md` — one row per confidential or personal field: data set, field, class,
  purpose, retention, owner, where else it lives (logs, backups, analytics, test environments, providers).
- The DPIA decision and its reasoning go to `decisions.md`.

## Procedure for a change that touches personal data
1. **Inventory before code.** Which data, whose (customers, employees, children), source, purpose, where it lands
   (database, logs, backups, analytics, queues, test environments, providers), who can read it. Mark the flows on the
   data-flow diagram (arch-threat-modeling). The inventory feeds the controller's record of processing (Art. 30).
2. **Owner and class.** Each data set has a business owner (decides purpose, access, retention, schema — an administrator is
   not the owner). The owner approves the class of each new personal field; the agent proposes it. Classes in order:
   public → internal → confidential → personal data → special categories (Art. 9) and children's data. The data set takes
   the class of its most sensitive field; copies inherit class and owner unless truly anonymised (record that as a decision).
   Requirements per class, inventory format and field markers: `references/data-governance.md`.
3. **Purpose and basis.** One basis per purpose from Art. 6(1): contract, legal obligation, vital interests, public task,
   legitimate interest, consent. Special categories also need an Art. 9 condition. Consent (Art. 7) is free, specific,
   documented and as easy to withdraw as to give. Behavioural analytics is a separate purpose with its own basis.
4. **Privacy by design and by default (Art. 25).** Only the fields the purpose needs; optional means really optional;
   narrowest visibility; shortest storage. Pseudonymise with a keyed HMAC, not a plain hash of an e-mail (a dictionary
   reverses it); keep the key in a secrets manager apart from the data (ops-secrets-identities). Pseudonymised data is
   still personal data for whoever holds the key. Prefer aggregates to raw events.
5. **Retention.** A period per category and purpose, enforced by a deletion job with a test; logs without personal data
   or with short retention; backups expire on a known cycle; encryption with crypto-erase (sec-cryptography-pki).
   Example table and a code sample: `references/gdpr-in-practice.md`.
6. **Data-subject rights (Art. 12–22).** Mechanisms for access/export, rectification, erasure, restriction, objection.
   Answer without undue delay, at most within **one month** (extendable by 2 more months with notice). Verify identity first.
7. **Processors and transfers.** Every provider processing on your behalf (cloud, mailing, analytics, support desk,
   AI API) needs an Art. 28 agreement and a place in the inventory. Outside the EEA (Chapter V, Art. 44–49): an adequacy
   decision or standard contractual clauses.
8. **Security (Art. 32).** Encryption at rest and in transit, least privilege, access log, backups with restore tests.
   No real personal data in test environments — synthetic or effectively anonymised data only.
9. **DPIA (Art. 35)** when high risk is likely; control questions in `references/gdpr-in-practice.md` §5.
10. **Cookies and device access** — consent rules (below).
11. **AI model providers** — sending personal data in a prompt is disclosure to a processor (below).

## Erasure request — the flow
1. Log the request (date, channel, verified identity) in a request register.
2. Check legal retention exceptions — e.g. invoices kept under accounting law: restrict that part instead of deleting it.
3. Erase the account, related records, files, search indexes and caches.
4. Send an erasure instruction to every processor holding the data (mailing tool, CRM, support desk) and collect confirmation.
5. Logs and backups expire on their cycle; the erased identifiers go on a list that is re-applied after any restore.
6. Reply to the person within the month and close the register entry.
An automated test proves that after deletion no table holds the person's data.

## Personal data breach (Art. 33–34)
- Notify the supervisory authority (in Poland: UODO) without undue delay and, where feasible, within **72 hours** of
  becoming aware, unless the breach is unlikely to result in a risk. The notification may be completed in stages.
- Notify the affected people when the risk to them is **high** (Art. 34): what happened, likely consequences, what you did,
  what they should do.
- Document every breach, including those not reported. A processor informs the controller without undue delay; the
  72-hour clock runs at the controller.
- Order of work: contain at once (close access, rotate keys, secure evidence) → within hours establish which data, whose,
  for how long, who accessed it, was it encrypted → before 72 h a risk assessment, decision and notification → people →
  register entry and a process fix. The agent gathers facts; the human decides. Timeline detail:
  `references/gdpr-in-practice.md` §4. Technical incident response: ops-security-operations.
- Case to learn from: UODO has fined both a controller and its processor for a test database left unsecured with real
  customer data [unverified: case number]. The fix is a breach procedure plus synthetic or pseudonymised test data.

## DPIA
Likely required for significant profiling, large-scale special categories, large-scale monitoring of public areas, and in
Poland for operations on the UODO list (M.P. 2019 item 666 — e.g. biometrics, location, innovative technology, combining
data sets). The agent drafts: description, purpose, necessity and proportionality, risks, measures. The controller and the
DPO decide. 2 "yes" answers to the control questions → put the question to the DPO.

## Cookies and device access
ePrivacy rules; in Poland the Electronic Communications Law (Prawo komunikacji elektronicznej, PKE, Dz.U. 2024 item 1221,
in force since 10 November 2024 — check the article and the competent authority in ISAP before citing). Storing or reading
non-essential data on a device needs prior consent; no pre-ticked boxes (CJEU C-673/17 *Planet49*, 2019); refusing must be
as easy as accepting. Analytics cookies are not essential.

## Personal data sent to AI model providers
A prompt with personal data is a disclosure to the provider, so the usual processor rules apply:
- minimise and pseudonymise before sending; send fields, not whole records;
- read the provider's **current** terms and data-usage policy in its official documentation and check: the service tier
  (consumer plans may use conversations for training by default, business and API plans usually do not), whether training
  use can be switched off, the processing region and EEA transfers, retention, the Art. 28 agreement;
- the same provider may have separate settings for its chat app, its API and its coding tool — check each one the team uses;
- record what you checked, with the date, in `privacy.md` — these policies change within months;
- no region choice, no EU representative, or storage in a country without an adequacy decision and without clauses →
  a transfer without a basis: stop and take it to a human and a lawyer.
AI Act obligations for training data: data-engineering.

## Fines (Art. 83)
Up to EUR 10 million or 2% of worldwide annual turnover; up to EUR 20 million or 4% for breaches of principles, legal
bases and data-subject rights — whichever is higher.

## Existing system without an inventory
1. A draft from code: `tf analyze --only data-classification` (schemas, migrations, models, personal data in logs and in
   analytics calls); finding `pii-field-unclassified` = a field with a personal-looking name and no class marker or inventory row.
2. Add fields with uninformative names; sample free-text and JSON columns (notes, metadata, payload) in production
   without copying the data out.
3. Owners approve the classes, then purposes and retention are added.
4. Fix personal data in logs and analytics first — they have the widest audience.

## Law to watch (as of 2026-11-20)
- EU–US Data Privacy Framework: adequacy decision of 10 July 2023, valid only for certified companies. The General Court
  dismissed the challenge in T-553/23 *Latombe* on 3 September 2025; an appeal is pending (C-703/25 P) [unverified].
- Digital Omnibus proposal COM(2025) 837 of 19 November 2025 (procedure 2025/0360(COD)): among others, breach notification
  only for high risk within 96 hours through a single entry point, cookie rules moved into the GDPR, EU-wide DPIA lists.
  It is a proposal — design for the 72-hour rule until it is in force.

## Example
**Situation:** "We add a phone number, booking history and behaviour analytics to a room booking app."
**Result:**
- Inventory rows: `users.phone` (personal, owner: product, purpose: booking reminders), `bookings.*` (personal, purpose:
  contract and accounting), `events.user_id` (personal, pseudonymised with HMAC, purpose: analytics).
- Bases: phone — contract if reminders are part of the service, otherwise consent (owner and DPO decide); history —
  contract plus legal obligation for accounting; analytics — consent, collected through the cookie banner (PKE).
- Minimisation: the phone is optional; analytics stores a pseudonym, not the e-mail.
- Retention: phone until account deletion; analytics events 13 months; application logs 30 days without payloads — a
  deletion job with a test.
- DPIA questions: no profiling with significant effect, no special categories → one "yes" at most; record the reasoning
  in `decisions.md`.
- *This is not legal advice — confirm with your DPO or lawyer.*

If the question gives no data, purposes or context ("is this GDPR compliant?"), ask for them; give no verdict.

## Sources
- Regulation (EU) 2016/679 (GDPR), Art. 5–9, 12–22, 25, 28, 30, 32–35, 44–49, 83 — EUR-Lex (accessed 2026-11-20).
- EDPB Guidelines 4/2019 on Article 25 Data Protection by Design and by Default, version 2.0 (2020).
- Commission Implementing Decision (EU) 2023/1795 (EU–US Data Privacy Framework), 10 July 2023; General Court T-553/23
  *Latombe*, 3 September 2025 — CURIA (accessed 2026-11-20).
- UODO list of processing operations requiring a DPIA, Monitor Polski 2019 item 666.
- Prawo komunikacji elektronicznej, Dz.U. 2024 item 1221 — ISAP (accessed 2026-11-20).
- CJEU C-673/17 *Planet49*, judgment of 1 October 2019.
- European Commission, Digital Omnibus proposal COM(2025) 837; OEIL procedure 2025/0360(COD) (accessed 2026-11-20).

Described in our own words; not legal advice.
