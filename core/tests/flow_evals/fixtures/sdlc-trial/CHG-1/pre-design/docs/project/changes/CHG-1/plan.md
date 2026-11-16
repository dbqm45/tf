---
artifact: plan
phase: plan
status: accepted
version: 1
author: pdi
created: 2026-10-31
updated: 2026-10-31
inputs: [requirements.md]
change: CHG-1
source: PRB-1
source_reported_at: 2026-10-30
---
# Plan zmiany CHG-1

## Cięcia

| TSK | Opis | Wydanie | Flaga |
|---|---|---|---|
| TSK-1 | Generowanie `config/build.json` w kroku wdrożenia | R1 | brak (budowa) |
| TSK-2 | Stopka pokazuje datę z `config/build.json` za flagą `show_last_deployed` | R1 | show_last_deployed |

## ADR

- `config/build.json` (nie env var), bo wymaga tylko jednego źródła prawdy i idzie z artefaktem wdrożenia (CHG-1/D4).
- Flaga `show_last_deployed` globalna (CHG-1/D2), bo mamy jeden rollout.
