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
- sent: yes
- date: 2026-11-05
- by: człowiek
- kind: gate
- why: brak E2E dla pokoju z 10 osobami i scenariuszy utraty sieci (PR #11); regresje realtime są wykrywane dopiero w produkcji
- source: manual
- drafted_by: ai

## Bramka B1 intent: approved
- ref: CHG-52/D2
- id: DEC-9004
- sent: yes
- date: 2026-11-05
- by: człowiek
- kind: gate
- why: Playwright z integracją Supabase Realtime w CI; scenariusze: 10 klientów, utrata sieci na 5/10/30s, powrót
- source: manual
- drafted_by: ai

## Bramka B2 requirements: approved
- ref: CHG-52/D3
- id: DEC-9005
- sent: yes
- date: 2026-11-05
- by: człowiek
- kind: gate
- why: wymagania pokrywają konsensus Risk Deck, obserwowalność (metryki per-klient), stany błędu (odrzucenie zapisu z sieci spiętego)
- source: manual
- drafted_by: ai
