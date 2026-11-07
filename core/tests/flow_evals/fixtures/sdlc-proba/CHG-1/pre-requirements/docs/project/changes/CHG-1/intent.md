---
artifact: intent
phase: discovery
status: accepted
version: 1
author: pdi
created: 2026-10-30
updated: 2026-10-31
inputs: []
change: CHG-1
source: PRB-1
source_reported_at: 2026-10-30
---
# Zamiar zmiany CHG-1

## Problem

Odwiedzający stronę sdlc-sandbox nie widzi, kiedy strona była ostatnio wdrożona. Brak wskaźnika aktualności →
brak zaufania do wyświetlanych treści.

## Wybrany wariant

**Wariant A** — data wdrożenia w stopce za flagą `show_last_deployed` (decyzja CHG-1/D2).

## Metryki sukcesu

- data widoczna na stronie prod po wdrożeniu z flagą
- flaga działa globalnie (CHG-1/D2 answers)

## Poza zakresem

- commit hash (odrzucony w B1)
- meta-tag (odrzucony w B1)
