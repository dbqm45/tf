---
artifact: decisions
phase: plan
status: draft
version: 1
author: pdi
inputs: []
change: CHG-SD2
source: PRB-SD-11
source_reported_at: 2026-11-05
---
# Decyzje zmiany CHG-SD2

## Bramka triage: approved
- ref: CHG-SD2/D1
- id: DEC-SD-0003
- wyslano: tak
- kiedy: 2026-11-05
- kto: człowiek
- rodzaj: gate
- dlaczego: brak E2E dla pokoju z 10 osobami i scenariuszy utraty sieci (PR #11); regresje realtime są wykrywane dopiero w produkcji
- zrodlo: manual
- szkic: ai

## Bramka B1 intent: approved
- ref: CHG-SD2/D2
- id: DEC-SD-0004
- wyslano: tak
- kiedy: 2026-11-05
- kto: człowiek
- rodzaj: gate
- dlaczego: Playwright z integracją Supabase Realtime w CI; scenariusze: 10 klientów, utrata sieci na 5/10/30s, powrót
- zrodlo: manual
- szkic: ai

## Bramka B2 requirements: approved
- ref: CHG-SD2/D3
- id: DEC-SD-0005
- wyslano: tak
- kiedy: 2026-11-05
- kto: człowiek
- rodzaj: gate
- dlaczego: wymagania pokrywają konsensus Risk Deck, obserwowalność (metryki per-klient), stany błędu (odrzucenie zapisu z sieci spiętego)
- zrodlo: manual
- szkic: ai
