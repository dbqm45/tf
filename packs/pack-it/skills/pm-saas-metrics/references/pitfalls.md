# Calculation pitfalls

- **Services in MRR** — implementations, training, one-off fees inflate MRR and understate churn. Outside MRR.
- **An annual prepayment as one month's MRR** — 12,000 PLN paid in January is 1,000 PLN of MRR for 12 months.
- **An average instead of cohorts** — an average churn mixes new customers (they leave more often) with old ones. Calculate
  cohort retention curves by start month and acquisition channel.
- **The churn denominator** — customers at the start of the period, without customers acquired during it (otherwise churn falls
  artificially during fast growth).
- **NRR with new customers** — that is already growth, not retention. NRR and GRR only on the cohort from the start of the period.
- **NRR without GRR** — an NRR of 115% can hide a GRR of 75%: a few large customers grow, many small ones leave.
- **CAC without full costs** — campaigns alone without sales salaries, commissions and tools understate CAC 2–3 times.
- **Blended CAC as paid** — organic customers lower CAC; campaign budget decisions on the CAC of the paid channel.
- **LTV from revenue, not from margin** — LTV calculated from revenue overstates the value by the cost of serving.
- **LTV at a churn of 0.5% a month** — 200 months of customer life is fiction; limit the horizon.
- **Mismatched periods** — CAC from a quarter with monthly churn and annual ARR; unify before comparing.
- **Burn multiple from one month** — calculate over a quarter or a year; a single month is noise.
