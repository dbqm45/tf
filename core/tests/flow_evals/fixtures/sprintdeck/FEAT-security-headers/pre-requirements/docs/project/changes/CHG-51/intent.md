---
artifact: intent
phase: discovery
status: accepted
version: 1
author: pdi
created: 2026-11-04
updated: 2026-11-04
inputs: []
change: CHG-51
source: PRB-50
source_reported_at: 2026-11-04
---
# Zamiar zmiany CHG-51

## Problem

Publiczna aplikacja sprintdeck (team.sprintdeck.app) nie wysyła nagłówków bezpieczeństwa — brak Content Security
Policy, X-Content-Type-Options, X-Frame-Options, Referrer-Policy. Bez CSP strona jest podatna na XSS i clickjacking;
skaner bezpieczeństwa (PR #10) oznacza to jako blocker przed udostępnieniem publicznego linku.

## Wybrany wariant

**Wariant A** — middleware Next.js w `middleware.ts` ustawia nagłówki na każdą odpowiedź; CSP strict z nonce
per-request. Decyzja CHG-51/D2 (DEC-9002).

## Metryki sukcesu

- https://securityheaders.com daje ocenę A lub lepszą
- test E2E w Playwright potwierdza obecność nagłówków
- brak regresji wizualnej (nonce poprawnie propagowany do inline-skryptów)
