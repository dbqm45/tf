---
artifact: plan
phase: plan
status: accepted
version: 1
author: pdi
created: 2026-11-05
updated: 2026-11-05
inputs: [requirements.md]
change: CHG-3
source: PRB-15
source_reported_at: 2026-11-04
---
# Plan zmiany CHG-3

## Cięcia

| TSK | Opis | Wydanie | Flaga |
|---|---|---|---|
| TSK-A | Fundament modułu płatności | R1 | brak |
| TSK-B | Integracja z providerem | R1 | payments_v2 |

## Wymogi bezpieczeństwa

Każde cięcie przechodzi przez `security_scan.py` (semgrep) — Z8c-2. Blokada: brak skanera w obrazie fazy
(symptom PRB-29).
