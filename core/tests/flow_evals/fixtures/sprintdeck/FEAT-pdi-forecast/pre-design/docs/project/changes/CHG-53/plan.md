---
artifact: plan
status: accepted
inputs: [requirements.md]
change: CHG-53
---
# Plan CHG-53

## Cięcia

| TSK | Opis | Wydanie | Flaga |
|---|---|---|---|
| TSK-A | Integracja mcp__pdi__forecast_report w panelu planu | R1 | pdi_forecast_ui |
| TSK-B | Mapowanie wierszy szacunków na forecast_id, komentarz w PR | R1 | pdi_forecast_ui |

## ADR

- Źródło prawdy prognoz: pdi `forecast.schema.json`; w sprintdecku tylko renderowanie.
- Flaga `pdi_forecast_ui` globalna (na start off na prod).
