# Data visualisation

## Choosing a chart for the question
| Question | Chart | Avoid |
|---|---|---|
| change over time | line (many series — at most a few, the rest grey) | bar for long series |
| comparing categories | horizontal bar, sorted | pie with many slices |
| part of a whole | a 100% stacked bar or a pie for 2–3 parts | a pie for comparing many wholes |
| distribution | histogram, density plot, box plot, violin (many groups) | the mean alone |
| relationship of two variables | scatter (with a trend line, transparency with many points) | a line for data without order |
| intensity in two dimensions | heatmap (day of week × hour) | a rainbow palette |
| process stages with drop-off | funnel (or a bar with the pass-through rate between stages) | a funnel without numbers |
| one number with context | a tile: value, change, reference (target, previous period) | a gauge |

## Rules
- **The title states the conclusion** ("Conversion fell in the mobile segment after 12 May"), not the topic ("Conversion").
- The Y axis of bar charts from zero; a truncated axis only for line charts and clearly marked. Identical scales for
  charts meant for comparison.
- Fewer elements: no 3D, shadows, needless grids; labels directly on the series instead of a legend where possible.
- Colour matters: one accent for what is important; palettes accessible to colour-blind people; colour never the only carrier
  of information (ux-feature-design: colour). Contrast and alternative text or a data table for charts in reports.
- Numbers with units and period; the source and date of the data under the chart.
- A chart lies through the choice of period, axis and aggregation — check whether another reasonable choice changes the conclusion.

## Tools
Python: matplotlib (full control), seaborn (statistical charts), Plotly (interactive). R: ggplot2 (the grammar
of graphics). BI: Power BI, Tableau, Looker, Metabase — dashboards with definitions of measures in a semantic layer and
data refresh. In a web application: a frontend chart library, data aggregated on the server side.

## Dashboard
It answers a few fixed questions of one recipient: the most important measures at the top (with a reference), details below,
only the necessary filters; every measure with a definition available on hover or in a dictionary. A dashboard nobody
opens for a month, remove.

## Sources
- E. Tufte, *The Visual Display of Quantitative Information*; C. Nussbaumer Knaflic, *Storytelling with Data*;
  F. Anscombe (1973)
- [roadmap.sh — Data Analyst](https://roadmap.sh/data-analyst) (charting, bar/line/pie/stacked/funnel charts,
  histograms, scatter plot, heatmap, matplotlib, seaborn, ggplot2, Power BI, Tableau)
Described in our own words.
