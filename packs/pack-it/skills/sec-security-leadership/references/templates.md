# Templates: strategy, board report, RACI

Contents: 1. One-page strategy · 2. Board report · 3. KPI and KRI · 4. RACI · 5. Awareness

## 1. One-page strategy
```markdown
Security leadership: <company> — target profile <year>, decisions to be made: <n>
1. Business goals (3–5) and "crown jewels": <what must work, which data>
2. Current state: CSF 2.0 current profile by function (Govern … Recover), the 3 biggest gaps with evidence
3. Target state: the target profile in 3 years and why this level (customer, regulation, appetite)
4. Pillars (3–5): business outcome · initiative · measure with a threshold · owner
5. Roadmap: 0–6 / 6–18 / 18–36 months; dependencies; decision points
6. Budget: total cost (range) · risk reduction · "no change" and "insurance" alternatives
7. What we do not do and why · the main risks of the strategy
8. Decisions to be made by the board (with a deadline)
```
Rules: one A4 page, no technical jargon, every number with a range and a source. Review every year or after a major incident
or acquisition.

## 2. Board report (quarterly, 1 page + appendices)
1. **The verdict in one sentence** (e.g. "risk within appetite, one exceptional item for decision").
2. **Risks against appetite:** the 3–5 biggest in the language of impact (PLN, days of downtime, contracts); trend (↑ → ↓).
3. **KRI** with thresholds (see below) — only those that have crossed the threshold or are approaching it.
4. **Program KPI:** progress of the roadmap initiatives, budget spent, key deadlines.
5. **Events and lessons:** incidents relevant to the board, near misses, what was changed.
6. **Decisions to be made** and requests (budget, risk acceptance, mandate) — with a recommendation and the consequence of refusal.
7. **Changes in the environment:** customers, regulators, acquisitions, new technologies (including AI).

Risk appetite is **a statement approved by the board**, not by the CISO, e.g. "we do not accept a critical risk
for longer than 90 days without a plan; downtime of a revenue system over 4 h is outside tolerance". The wording and the acceptance
procedure — sec-risk-management.

Pitfalls: the number of blocked attacks as a success (it grows with noise); a colourful heat map without impact; 40 slides
of SOC metrics; surprising the board with bad news in the room — discuss it with the chair beforehand.

## 3. KPI and KRI
| | KPI | KRI |
|---|---|---|
| question | is the program doing what was planned | is risk growing |
| examples [example] | % of critical systems in EDR; initiatives on schedule; exercise coverage | privileged accounts without MFA; critical vulnerabilities >7 days on internet-facing assets; mean time to detect; expired risk acceptances |
| threshold and owner | target + owner | alert threshold + owner + action when crossed |
A metric without a threshold and an owner does not go into the report. Few numbers, a fixed definition, the same measure every quarter.

## 4. RACI (R does the work, A is accountable, C is consulted, I is informed) [example]
| Decision | Board | CISO | IT/product | Legal | Internal audit |
|---|---|---|---|---|---|
| risk appetite | A | R | C | C | I |
| risk acceptance above the threshold | A | C | R (owner) | C | I |
| crisis declaration | I | R | C | C | I |
| ransom decision | A | C | C | R (opinion) | I |
| contact with the regulator | A | C | I | R | I |
| independent program assessment | I | I | I | I | A/R |
One **A** per row. Internal audit does not belong to the CISO (independence according to the three lines model).

## 5. Awareness — behaviour measures
The share of employees reporting phishing (not only clicking), the time from receipt to report, repeat
clickers (support, not punishment), use of a password manager and MFA, the number of mistake reports made without fear of blame. Training short
and contextual (role: finance, developers, board), because each needs different scenarios. Simulations: approved by the board
and HR, compliant with labour law and data protection (consultation with a lawyer and the DPO [unverified] for the given jurisdiction),
aggregate results instead of names.
