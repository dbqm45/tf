---
name: data-analysis
description: Use when a question has to be answered with data — a drop or rise in a metric, segments, Simpson's paradox, hypothesis tests.
metadata:
  review: "2027-10-17"
  catalog: "Use when a question has to be answered with data — from the question and the decision through data acquisition, cleaning, descriptive and diagnostic analysis, statistics and hypothesis tests, visualisation to a report with conclusions and limitations; pandas, SQL, R, spreadsheets, machine learning basics. Not for data pipelines (data-engineering) or product A/B experiments (proc-product-discovery)."
  keywords: "porównanie grup, średnia czy mediana, rozkład skośny, test statystyczny, istotność, wielkość efektu, spadek konwersji, dane z eksperymentu, ile da rabat, efekt interwencji z danych historycznych, bez eksperymentu, wnioskowanie przyczynowe, uplift, CATE, wagi skłonności, model churnu a decyzja, Singular matrix, regresja liniowa, zmienne zero-jedynkowe, comparing groups, mean or median, skewed distribution, statistical test, significance, effect size, drop in conversion, experiment data, how much a discount will give, the effect of an intervention from historical data, without an experiment, causal inference, propensity weights, churn model and the decision, linear regression, dummy variables"
---

# Data analysis

An analysis ends with **a decision, or the lack of one with a justification**, not with a chart. Every number in a report has a source
and a way of calculating it that someone else can repeat.

Start with the simplest kind of analysis (descriptive → diagnostic → predictive → prescriptive) that answers
the question; every next one is more expensive.

## Procedure
1. **The question and the decision**: who will decide what on the basis of the result, what result would change the decision, the deadline.
   Pin down the measures ("active customer" = what exactly?) — definitions from the domain dictionary (ddd-facilitation) and written down.
2. **Data**: from where (a database via SQL — replicas or a warehouse, not production OLTP; an API; CSV files and spreadsheets; scraping
   only in line with the site's terms, `robots.txt`, with a rate limit and without personal data), for what period, with what
   delay and quality. Personal data: minimisation, pseudonymisation, access by consent (GDPR). Types of variables:
   nominal, ordinal, interval, ratio — they determine the permitted operations (an average of 1–5 ratings can be
   misleading; the median and the distribution are better).
3. **Cleaning** (recorded in a script, not by hand in a spreadsheet): types and formats (dates in UTC, numbers, character
   encoding), duplicates (by the business key), missing values (why is it missing? removal, filling with the median
   or a model, a separate "missing" category — the decision recorded, because it changes the result), wrong and outlying values (an
   entry error or a real extreme? IQR, z-score, a box plot), text normalisation (case,
   spaces, name variants). Count rows before and after every step.
4. **Exploration (EDA)**: distributions (a histogram, density), measures of location and spread, missing values, relationships between
   variables, a split by segments and time. You look for surprises and errors in the data before you start drawing inferences.
5. **Analysis**: aggregations and comparisons of segments, correlations, regression, statistical tests
   with an effect size and, for many comparisons, a correction (Holm, Benjamini-Hochberg) (`references/statistics.md`), predictive models only when needed (`references/machine-learning.md`:
   also MLOps and AI engineering), forecasts and causality from observational data
   (`references/time-series-and-econometrics.md`), experiment sensitivity and ratio metrics
   (`references/advanced-experiments.md`).
   Control for confounders and check Simpson's paradox (the trend as a whole is the reverse of that in the segments).
   The question "how much will an intervention give" without an experiment: a causal graph, a method, the effect for whom (CATE/uplift) and attempts
   to refute it (`references/time-series-and-econometrics.md`). "Singular matrix" in a regression = a data problem (the dummy-variable
   trap, a constant column), not a library problem (`references/statistics.md`).
6. **Visualisation** matched to the question (`references/visualization.md`).
7. **Report**: first the answer to the question and a recommendation, then the evidence, then the method; **limitations** (data
   quality, period, what cannot be established — correlation is not causation), uncertainty (intervals, not only a
   point), how to repeat the analysis (a script or notebook in the repo, the data version).

## Tools
- **SQL** for fetching and aggregating at the source (window functions, CTEs — be-database); **pandas** (or polars) in Python,
  **R** with dplyr and ggplot2; notebooks (Jupyter) for exploration, scripts and tests for repeatable analyses.
- **Spreadsheets** (Excel, Google Sheets) for small data and business recipients: pivot tables, `XLOOKUP` (instead of the
  older `VLOOKUP`/`HLOOKUP`, when the version allows), `IF`, text and date functions. Formulas instead of pasted
  values, so that the calculations can be checked.
- **BI** (Power BI, Tableau, Looker, Metabase) for reusable dashboards — the definitions of measures in one place
  (a semantic layer), not in every report separately.
- Big data and distributed processing: first check whether it is really needed (arch-quality-attributes,
  `data-architecture.md`).

## Rules
- You cross-check numbers against a second source or a checksum (e.g. the sum of revenue matches the accounting).
- You do not fit the analysis to the expected result; you write down hypotheses before checking.
- A result that contradicts expectations is first a suspicion of an error in the data, then a discovery.

## Checklist
- [ ] the question, the decision and the definitions of measures written down
- [ ] sources, period and data quality described; personal data minimised
- [ ] cleaning in a script with the row count after every step
- [ ] EDA before conclusions; segments and time checked
- [ ] report: answer, evidence, method, limitations, uncertainty, how to repeat it

## Sources
- D. Diez et al., *OpenIntro Statistics*; H. Wickham et al., *R for Data Science*; W. McKinney, *Python for Data Analysis*
- [roadmap.sh — Data Analyst](https://roadmap.sh/data-analyst)
Described in our own words.
