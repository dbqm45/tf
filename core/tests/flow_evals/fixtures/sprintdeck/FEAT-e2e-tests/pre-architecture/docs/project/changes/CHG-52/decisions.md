---
artifact: decisions
phase: plan
status: draft
version: 1
author: pdi
inputs: []
change: CHG-52
source: PRB-51
source_reported_at: 2026-11-05
---
# Decyzje zmiany CHG-52

## Bramka triage: approved
- ref: CHG-52/D1
- id: DEC-9003
- wyslano: tak
- kiedy: 2026-11-05
- kto: człowiek
- rodzaj: gate
- dlaczego: brak E2E dla pokoju z 10 osobami i scenariuszy utraty sieci (PR #11); regresje realtime są wykrywane dopiero w produkcji
- zrodlo: manual
- szkic: ai

## Bramka B1 intent: approved
- ref: CHG-52/D2
- id: DEC-9004
- wyslano: tak
- kiedy: 2026-11-05
- kto: człowiek
- rodzaj: gate
- dlaczego: Playwright z integracją Supabase Realtime w CI; scenariusze: 10 klientów, utrata sieci na 5/10/30s, powrót
- zrodlo: manual
- szkic: ai

## Bramka B2 requirements: approved
- ref: CHG-52/D3
- id: DEC-9005
- wyslano: tak
- kiedy: 2026-11-05
- kto: człowiek
- rodzaj: gate
- dlaczego: wymagania pokrywają konsensus Risk Deck, obserwowalność (metryki per-klient), stany błędu (odrzucenie zapisu z sieci spiętego)
- zrodlo: manual
- szkic: ai
