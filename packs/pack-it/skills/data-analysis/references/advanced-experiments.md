# Experiments: power, sensitivity and ratio metrics

The basics of an A/B test (the hypothesis, the randomisation unit, pitfalls, ethics): proc-product-discovery,
`experiments-and-release.md`. Here — how to detect a smaller effect with the same traffic and how not to make a statistical mistake.

## Probability and sampling — the minimum
- **The central limit theorem**: the mean of a large sample has a distribution close to normal, even when the data are not
  normal — which is why the t-test works for means. With very skewed data (revenue, where a few customers
  make up most of it) a "large sample" must be really large; otherwise the intervals are too optimistic.
- Randomisation at the level of the unit you analyse (the user), and independence of units. Network effects
  (two-sided markets, social features) break independence → randomisation by clusters or regions.

## The minimum detectable effect (MDE) and power
- The MDE is the smallest effect the test will detect with a given power (e.g. 80%) at a given significance level, variance
  and sample size. The MDE grows with the metric's variance and shrinks with the square root of the number of units: four times more
  traffic = a twice smaller MDE.
- Calculate the MDE **before** the test. If the real effect of the change is smaller than the MDE, the test will settle nothing —
  change the metric, lengthen the test or apply variance reduction.

## Variance reduction
- **CUPED**: an adjusted metric `Y' = Y − θ·(X − mean of X)`, where X is the same (or a correlated) metric of
  the user from the period **before** the experiment, and θ = cov(X, Y) / var(X). The variance falls by a factor of (1 − R²)
  — at R² = 0.4 it is as if traffic grew about 1.66 times. It introduces no bias, because X does not depend on the assignment
  to a group.
  - The variable X must come from before exposure (the feature under test cannot change it).
  - New users without history: X = the mean (or a separate indicator), the adjustment then works less well.
  - The gain depends on the metric — for some metrics almost none; check on historical data.
- **CUPAC**: instead of a single metric from the past — the prediction of a model built on many pre-experiment features as the variable X.
- **Stratification**: randomisation or analysis in strata (country, platform, segment), so that differences between strata do not
  increase the variance.
- **Heavy tails**: truncating or winsorising extreme values (a threshold set before the test) or a rank
  transformation — otherwise a few atypical users decide the result.

## Ratio metrics
- When the unit of analysis differs from the unit of randomisation — CTR per session, revenue per order, time on page —
  observations within one user are not independent. An ordinary t-test at the session level understates the variance
  and gives false "significant" results.
- Calculate the ratio as a ratio of sums per group (the sum of clicks / the sum of sessions) and the variance with the **delta method** (an approximation of
  the variance of a ratio of two means with the covariance of numerator and denominator) or a **bootstrap over users**.
- Also check the numerator and denominator separately — a ratio can rise because the denominator fell (fewer sessions), which can be bad
  news.

## Sources
- A. Deng et al., "Improving the Sensitivity of Online Controlled Experiments by Utilizing Pre-Experiment Data" (2013)
  — CUPED; [Microsoft Research — Deep Dive Into Variance Reduction](https://www.microsoft.com/en-us/research/articles/deep-dive-into-variance-reduction/)
- [Booking.com — How Booking.com increases the power of online experiments with CUPED](https://booking.ai/how-booking-com-increases-the-power-of-online-experiments-with-cuped-995d186fff1d);
  DoorDash — CUPAC; Netflix — stratification; A. Deng et al. — the delta method for ratio metrics (2018)
- R. Kohavi, D. Tang, Y. Xu, *Trustworthy Online Controlled Experiments*; [roadmap.sh — AI and Data Scientist](https://roadmap.sh/ai-data-scientist)
Described in our own words.
