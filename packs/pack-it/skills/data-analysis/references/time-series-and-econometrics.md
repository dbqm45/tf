# Time series, forecasting and econometrics

## Time series
- **A chart first**: trend, seasonality (daily, weekly, yearly), holidays and one-off events, level
  shifts (a new price list, a data collection failure). Decomposition into trend, seasonality and remainder.
- **Stationarity** (a constant mean and variance over time) — required by classical models: the ADF or KPSS test,
  differencing, a logarithm when the variance grows with the level. Autocorrelation functions (ACF, PACF) show the dependence
  on past values.
- **Models from the simplest** (each next one must beat the previous):
  1. naive (tomorrow = today) and seasonal naive (the same day a week ago) — **a mandatory baseline**;
  2. exponential smoothing (ETS, Holt-Winters) — trend and seasonality;
  3. ARIMA / SARIMA — autoregression, differencing, a moving average, with seasonality;
  4. regression with lag, calendar and external variable features (e.g. gradient boosting) — when there are many series
     and many factors.
- **Validation in time**: backtesting with a rolling origin (train up to day t, forecast t+1…t+h, move on),
  never a random split. Measures: MAE, MASE (a comparison with the naive model — scale-robust), sMAPE; MAPE fails with
  values close to zero.
- A forecast always with an **interval** (e.g. 80% and 95%) — decisions about stock and capacity depend on uncertainty,
  not on the point.

## Econometrics — causal relationships from observational data
- **Ordinary least squares regression**: a coefficient is the change in the outcome for a one-unit change in the variable,
  **with the others held constant**. Check the assumptions; with heteroscedastic residuals — robust standard errors;
  with grouped data (customers, shops) — clustered errors.
- **Endogeneity** (an explanatory variable depends on the outcome or on an omitted factor) gives biased results.
  Tools:
  - **difference-in-differences** — comparing the change in the group exposed to the intervention with the change in a control group, under
    the assumption of parallel trends before the intervention (check on a chart);
  - **fixed effects** — eliminating the constant characteristics of units in panel data;
  - **instrumental variables** — a factor affecting the outcome only through the studied variable (hard to justify);
  - **regression discontinuity** — a comparison just above and just below a threshold (e.g. the free-delivery threshold).
  When an experiment is possible, it is better than any of these methods (`advanced-experiments.md`).
- **Causality step by step (a decision from observational data):**
  1. **A causal graph (DAG)** with a domain expert. You control for a confounder; not for a mediator (it blocks the studied
     effect), nor for a collider (it introduces bias).
  2. **Method:** propensity weights, instrumental variables, double ML with cross-fitting, causal forests.
  3. **ATE or CATE:** "does it work on average" (ATE) versus "for whom does it work" (CATE, uplift). You give a discount to those whose
     behaviour it changes, not to those who will stay anyway or leave anyway. A churn model says "who will leave";
     the decision needs "whose leaving a discount will change".
  4. **Refutation attempts:** a random common cause, a placebo (a fake intervention), a data subset. A result that
     changes when a random variable is added is fragile.
  Libraries: DoWhy (graph, identification, refutation), EconML (CATE), CausalML (uplift) — you check the version and API before
  use (G. Nguyen, "Causal Machine Learning…", 2026-09-22).
- **Distribution fitting** (service times, order sizes — for simulation and capacity planning): maximum likelihood
  estimation, assessment with a quantile–quantile plot and a goodness-of-fit test; long-tailed distributions
  (log-normal, Pareto) instead of the normal for amounts and times.

## Sources
- R. Hyndman, G. Athanasopoulos, *Forecasting: Principles and Practice* (online edition); J. Angrist, J.-S. Pischke,
  *Mostly Harmless Econometrics*
- [roadmap.sh — AI and Data Scientist](https://roadmap.sh/ai-data-scientist) (econometrics, regression, time series,
  ARIMA, fitting distributions)
Described in our own words.
