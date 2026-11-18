# Risk analysis, FAIR, insurance and KRIs

Contents: 1. Qualitative scales · 2. FAIR step by step · 3. Cyber insurance · 4. KRIs · 5. The boundary with the threat model

## 1. Qualitative scales
A 1–5 scale works only with **definitions**: impact 1 = a loss < PLN 10 thousand, 3 = PLN 100–500 thousand, 5 = > PLN 5 million or
the loss of a licence [example; the thresholds are set by the board]; likelihood 1 = less often than once in 10 years, 3 = once in 1–3
years, 5 = more than once a year. Score = L × I; thresholds: 1–6 low, 7–14 medium, 15–25 high [example]. The matrix's weaknesses:
compression of scores, no adding up of risks, subjectivity — which is why for decisions about money you use FAIR.

## 2. FAIR step by step
1. **Scenario**: the asset, the threat (who/what), the type of loss (confidentiality, integrity, availability), the scope.
2. **Loss event frequency (LEF)** = the frequency of attempts × the share that succeeds (vulnerability). A range,
   e.g. 0.05–0.5 per year, most likely 0.15 [example]; data: own incidents, industry reports, an expert.
3. **Loss magnitude (LM)**: primary losses (response, downtime, recovery) and secondary ones (fines, notifications, loss of
   customers, legal costs). Each category as a range (min, most likely, max).
4. **A Monte Carlo simulation**: thousands of draws from the ranges (e.g. a triangular or PERT distribution) → the distribution of the annual loss;
   you report the median, the mean and P90, not a single number. Tools: a spreadsheet, Python (e.g. the pyfair library).
5. **Decision**: compare the distribution before and after the control with the cost of the control and the appetite; the difference is the value of the control.
6. **Calibration**: train the experts in giving 90% ranges; record the assumptions, because the result is only as good as the data.
You do not calculate FAIR for every risk — only for the highest and disputed ones. You enter the result into the register next to the matrix score.

## 3. Cyber insurance (risk sharing)
It transfers part of the financial consequence (response costs, downtime, third-party claims — depending on the policy), it does not remove
the cause. Check with a broker and a lawyer: the sums and sub-limits, the **exclusions** (e.g. war, failing to meet the minimum
controls), the deductible, the required controls (MFA, offline backups, EDR) and whether they match reality at the time of the application
(untrue answers may void the cover), the discovery and notification period, the insurer's choice of advisers.
The register row has the "sharing" option with the policy number and the expiry date. Market conditions change — [unverified] in the session.

## 4. KRIs (key risk indicators)
| KRI | Green / red threshold [example] | Owner |
|---|---|---|
| critical vulnerabilities past the SLA deadline | 0 / >3 | CISO |
| overdue risk acceptances | 0 / >0 | CISO |
| tier 1 vendors without an assessment <12 months | 0 / >1 | procurement |
| share of privileged accounts with MFA | 100% / <98% | IT |
| a successful restore test in the last 6 months | yes / no | SRE |
Rules: a KRI predicts (a leading indicator), has a threshold and an action when it is exceeded; do not report a number without a trend.

## 5. The boundary with the threat model
**arch-threat-modeling** assesses a specific design (DFD, STRIDE, controls in the backlog) and gives a list of threats with a score.
This skill takes from it the risks relevant to the organization, aggregates them in one register with one set of criteria, sets
the owners, the appetite and the acceptances, and reports to the board. A low technical score in the threat model may be high
organizationally (a critical asset, many features affected) — recalculate it according to the organization's criteria.
