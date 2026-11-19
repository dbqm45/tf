# Crisis at board level, ransom, policy, M&A

Contents: 1. Crisis team · 2. Playbook (draft) · 3. The ransom decision · 4. Communication · 5. Tabletop · 6. Cyber insurance · 7. M&A and vendors · 8. Notifications and facts

## 1. Crisis team
The commander (usually the CEO or COO, not the CISO), the CISO/technical commander, legal, communications, HR, finance, a business
representative; deputies for every role; a secretary who keeps the decision log. The mandate recorded in advance: who declares a crisis,
up to what amount the team decides, what requires the board. An emergency channel outside the attacked infrastructure (a separate chat account,
phones, a printed contact list). Technical response details — ops-security-operations.

## 2. Crisis playbook (draft for `crisis-playbook.md`)
1. **Declaration criteria** and levels (1 incident, 2 serious, 3 crisis); who declares.
2. **The first 4 hours:** convening the team, halting informal communication, an order to freeze changes (no
   "cleaning" of systems), notifying the lawyer, the insurer and the crisis adviser from the policy.
3. **Rhythm:** briefings every 2–4 h, in each: facts (confirmed / unconfirmed), business impact, decisions, the next step.
4. **Decision log:** time (UTC and local), decision, who decided, information available at the time, alternatives, reason.
   The secretary keeps the log; the lawyer decides how to mark and store it (legal privilege) [unverified
   for the jurisdiction].
5. **External parties:** lawyer, forensics firm (preferably engaged in advance), insurer, law enforcement, regulator,
   customers, media, partners, employees.
6. **Board decisions:** ransom, notifications, shutting down services, public statement, resuming operations.
7. **Closure:** criteria for exiting the crisis, a post-event review (without looking for culprits) with actions and owners,
   a report to the board, an update of the strategy and the exercises.

## 3. The ransom decision (a process, not an opinion)
Paying is not recommended as the default path, but the decision belongs to the board. Order:
1. Establish whether restoring from backups is possible and how long it takes (restore time against tolerated downtime).
2. The lawyer's opinion: sanctions (in the USA OFAC — strict liability, mitigating factors are reporting to the authorities
   and cooperation; in the EU and Poland [unverified]), notification obligations, compliance with the policy, criminal risk and the liability
   of board members.
3. Reporting to law enforcement/CSIRT before any payment, if the law and the policy expect it.
4. The attacker's credibility: whether the claimed data (leak) really is in their hands, whether the decryptor works (a test on
   a small set by a specialized firm), whether payment will remove the leak — there is usually no guarantee.
5. Recording the decision in the log (who, on what basis, which opinions); you record a "we do not pay" decision the same way.
Payment is made only by a specialized intermediary designated with the lawyer; an IT employee does not do it.

## 4. Communication
One spokesperson, one source of facts. Order: the management board and supervisory board → legal and the regulator (according to deadlines) → employees →
affected customers and partners → media (a ready reactive statement). Content: what we know, what we do not know, what we are doing, what the
recipient should do (change passwords, stay alert); no speculation about the perpetrator and the cause, no promises that "the data is safe"
until that is confirmed. The lawyer checks the messages. Listed companies: disclosure obligations (e.g. Form 8-K
Item 1.05 in the USA — filing within 4 business days of determining materiality, according to secondary sources, accessed 2026-10-17
[unverified]); deadlines for NIS2, DORA and GDPR (RODO) — sec-eu-regulations and ops-security-operations.

## 5. Tabletop exercise
Once a year, with the board taking part; 2–3 hours, a scenario from the business (ransomware on the ERP on a Friday, a customer data leak,
an attack on a key vendor), injected "events" every few minutes (a journalist calls, a customer demands explanations, the policy
requires a notification). Assessment: are the roles and the mandate clear, does the log work, are the contacts up to date, did the ransom decision
follow the process. Output: a list of gaps with owners and deadlines; a rerun of the changed element.

## 6. Cyber insurance
Questions for the broker and the lawyer: scope (first-party costs: forensics, restoration, business interruption, notifications,
third-party liability, extortion), exclusions (war and state actions, underinvestment in
security, previously known gaps), limits and deductibles, control requirements (MFA, offline backups, EDR) and the consequence
of not meeting them, **truthfulness of the answers in the application** (untrue ones may void the cover), the notification deadline,
imposed advisory firms, the insurer's consent to a payment. A policy does not replace controls.

## 7. M&A and vendors
- **Before signing:** a request to the target about incidents from the last 3 years, certifications, identity and MFA, backups, technical debt,
  personal data and cross-border flows, code ownership and licences; the result as risks in the valuation model and clauses in the agreement
  (representations, indemnity).
- **Day 1:** connecting login and MFA, visibility in logs, cutting off unnecessary connections; full integration
  in a 100-day plan, without "plugging in blind" to the main network.
- **Vendors (program):** tiering by criticality, a contract standard (incident notification, audit, exit plan), an annual
  review for tier 1, a concentration map (one vendor, many services). Assessment of a single vendor: sec-risk-management.

## 8. Notifications and external facts
Notification deadlines and recipients depend on the jurisdiction and the sector; the skill does not determine them. The lawyer confirms them within the first
hour. The facts in sections 3 and 4 come from secondary sources (search 2026-10-17) and need checking in the original.
