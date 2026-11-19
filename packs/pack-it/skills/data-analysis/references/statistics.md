# Statistics for an analyst

## Descriptive statistics
- **Location**: the mean (sensitive to extreme values), the median (robust — for salaries, times, order amounts
  usually better), the mode (for categorical data).
- **Spread**: the range (min–max, sensitive to extremes), the interquartile range (IQR = Q3 − Q1), the variance
  and standard deviation; percentiles (p50, p90, p95, p99) — for response times and amounts more important than the mean.
- **Distribution shape**: skewness (right-skewed — a long tail of large values, typical of amounts and times), kurtosis
  (the heaviness of the tails), multimodality (several humps = usually several populations — separate the segments). Always look at
  the histogram, not only at the numbers.
- **Outliers**: outside [Q1 − 1.5·IQR, Q3 + 1.5·IQR] or |z| > 3 (for distributions close to normal).
  You remove only errors; real extremes you analyse separately and report.

## Inference
- **Sample and population**: a result from a sample has uncertainty — give a **confidence interval** (e.g. 95%), not the number alone.
- **A hypothesis test**: the null hypothesis (no effect), a significance level set before the test (usually α = 0.05),
  a test statistic, the p-value = the probability of obtaining such or a more extreme result **if the
  null hypothesis were true** (not the probability that the hypothesis is true).
- Choosing a test:
  | Situation | Test |
  |---|---|
  | means of two groups, a distribution close to normal | Student's t (Welch's variant for unequal variances) |
  | two groups, a skewed distribution or a small sample | Mann-Whitney |
  | more groups | ANOVA (or Kruskal-Wallis) and post hoc comparisons |
  | proportions, contingency tables | chi-square or a test for proportions |
  | the same group before and after | a test for dependent samples (paired t, Wilcoxon) |
- **Significance is not size**: with a large sample a small effect of no business importance can be "significant". Report
  the effect size (a difference with an interval, Cohen's d) and practical importance.
- **Multiple comparisons**: with many tests some will come out "significant" by chance — a correction (Bonferroni, Holm,
  Benjamini-Hochberg) or hypotheses set in advance. Searching the data until something turns up (p-hacking) gives false
  discoveries.
- Controlled experiments (A/B) — proc-product-discovery, `experiments-and-release.md`.

## Relationships
- **Pearson correlation** (linear, sensitive to extremes), **Spearman** (monotonic, on ranks). A value from −1
  to 1; always with a scatter plot — completely different arrangements of points can have the same coefficient (Anscombe's quartet).
- **Correlation is not causation**: a confounder, reverse direction, chance, sample selection. Causation
  is established by an experiment or a careful causal method (e.g. difference-in-differences), not by correlation alone.
- **Linear regression**: the effect of variables on the outcome while controlling for the others; check the assumptions (linearity, residuals with no
  pattern, no strong multicollinearity) and do not extrapolate beyond the range of the data.
- **A rank-deficient matrix ("Singular matrix"):** the dummy-variable trap (all categories + an intercept)
  and a constant column in the data are the same problem — the data do not distinguish the coefficients. Libraries react differently
  (an error, a warning and a minimum-norm solution, silently different results); check on the project's versions. Before
  interpreting the coefficients you check the rank of the matrix and the condition number (or VIF). The fix is a change of data:
  removing one category (a base category, `drop_first`) or the constant column, not changing the library. In code
  `solve`/`lstsq` instead of `inv(A) @ b` — faster and more accurate with poor conditioning.

## Sources
- D. Diez, M. Çetinkaya-Rundel, C. Barr, *OpenIntro Statistics*; ASA Statement on p-Values (2016)
- [roadmap.sh — Data Analyst](https://roadmap.sh/data-analyst) (central tendency, dispersion, distribution shape,
  outliers, hypothesis testing, correlation, regression)
Described in our own words.
