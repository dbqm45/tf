---
artifact: decisions
phase: plan
status: draft
version: 1
author: pdi
created: 2026-10-30
updated: 2026-10-31
inputs: []
change: CHG-1
source: PRB-1
source_reported_at: 2026-10-30
---
# Decyzje zmiany CHG-1

Wpisy dodaje `decision_record.py decision add CHG-1 …` (po zatwierdzeniu szkicu przez człowieka). `id` nadaje rejestr
pdi (`record_decision` przez MCP) i wpisuje `decision mark`; bez serwera pdi zostaje puste, a `sent: no` — wyślesz
później (`decision pending`). Nie wymyślaj numerów.

<!-- Wzór wpisu:
## <co zdecydowano, jedno zdanie>
- ref: CHG-1/Dn (nadaje decision add)
- id:
- sent: no
- date: RRRR-MM-DD
- by: <osoba lub rola, która zdecydowała>
- kind: product | technical | process | triage | intent | gate | other
- why: <1–5 zdań, tylko z rozmowy>
- source: claude-cli | claude-ai | slack | confluence | jira | manual
- drafted_by: ai | human
-->

## Bramka triage: approved
- ref: CHG-1/D1
- id: DEC-0001
- sent: yes
- date: 2026-10-30
- by: pdi
- kind: gate
- why: decyzja w skrzynce bramek pdi (DEC-0001); uzasadnienie w rejestrze pdi
- source: manual
- drafted_by: human

## Bramka B1: approved
- ref: CHG-1/D2
- id: DEC-0002
- sent: yes
- date: 2026-10-30
- by: pdi
- kind: gate
- why: decyzja w skrzynce bramek pdi (DEC-0002); uzasadnienie w rejestrze pdi
- source: manual
- drafted_by: human

## Bramka B2: approved
- ref: CHG-1/D3
- id: DEC-0003
- sent: yes
- date: 2026-10-30
- by: pdi
- kind: gate
- why: decyzja w skrzynce bramek pdi (DEC-0003); uzasadnienie w rejestrze pdi
- source: manual
- drafted_by: human

## Bramka B3: approved
- ref: CHG-1/D4
- id: DEC-0004
- sent: yes
- date: 2026-10-31
- by: pdi
- kind: gate
- why: decyzja w skrzynce bramek pdi (DEC-0004); uzasadnienie w rejestrze pdi
- source: manual
- drafted_by: human

## Bramka approve-for-implementation: approved
- ref: CHG-1/D5
- id: DEC-0006
- sent: yes
- date: 2026-10-31
- by: pdi
- kind: gate
- why: decyzja w skrzynce bramek pdi (DEC-0006); uzasadnienie w rejestrze pdi
- source: manual
- drafted_by: human
