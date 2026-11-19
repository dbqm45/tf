# Reporting playbook: one incident, many clocks

Contents: principles · timeline · template · pitfalls. Response technique — `.claude/skills/ops-security-operations/SKILL.md`.
GDPR (when to notify, the content of the notification) — `.claude/skills/arch-privacy-compliance/SKILL.md`. Not legal advice.

## Principles
1. **One person is responsible for the clocks** (the reporting coordinator), with a deputy; the lawyer and the DPO in the first hour.
2. **Hour 0** is the moment of becoming aware; record who established it, when and on what basis. Classification (significant? personal
   data? a product?) must not delay the first signal — report with a reservation and correct it.
3. **One timeline, one source of facts**, from which the content is copied into every report, so that the reports do not
   contradict each other. Different recipients want different fields, the facts are the same.
4. **You send as much as you have.** You supplement the missing elements in the next stage, you do not wait for full knowledge.
5. **Recipients and channels prepared before the incident** (forms, accounts, certificates for the platforms), also outside working hours.

## Timeline [example]
| Time | Action | Owner |
|---|---|---|
| T0 | detection, recording the hour, preliminary classification per the decision table | coordinator |
| T0+4 h | DORA: initial notification, if classified as major (cap 24 h) | financial entity |
| T0+24 h | NIS2 early warning; CRA early warning (product) | coordinator |
| T0+72 h | NIS2 notification; GDPR Art. 33 to UODO; CRA notification; DORA intermediate report (72 h from the initial one) | coordinator, DPO |
| after the fix | CRA final vulnerability report within 14 days | PSIRT |
| ~1 month | NIS2, CRA incident, DORA final reports | coordinator |

## Notification template (common core)
Who reports and contact · hour of detection and of becoming aware · what happened (facts, no speculation) · affected systems, services,
products and versions · personal data (categories, number — an estimate) · cross-border impact · suspicion of an unlawful act ·
measures taken · indicators (IOCs, if safe to share) · status and the next report · who has already been notified.

## Pitfalls
- The GDPR clock of the controller vs the processor: the processor notifies the controller; the controller counts the 72 h from its own awareness.
- An ICT provider must give the customer time for its clock — agree in the contract on notification times much shorter than 24 h.
- A report to an authority does not release you from notifying customers, the insurer and contract parties (contractual penalties).
- Supplementing reports with contradictory numbers; version the content and note changes in findings.
- Practise with a tabletop once a year; measure the time from T0 to each report.
