---
artifact: design
change: {CHG}
phase: design
status: proposed
version: 1
---

# Projekt zmiany {CHG}

Plik Figmy: <link do pliku> · tryb: dopasowanie ramek projektanta (szkic ramek przez agenta tylko na prośbę człowieka)

## Ramki per wymaganie i stan

Format z kontraktu pdi (`conventions.design`): stan z listy `idle`, `loading`, `processing`, `success`,
`validation_error`, `server_error`, `timeout`, `retry`, `empty`, `confirmation`, `session_expired`, `network_failure`,
`permission_denied`; ramka — link z `node-id`, `brak` (z pytaniem) albo `nie dotyczy` (z powodem). Każda historyjka:
co najmniej `idle`, `success` i stan błędu. Sprawdzenie: `design_check.py check {CHG}`.

| Wymaganie | Ścieżka | Stan | Ramka | Uwagi |
|---|---|---|---|---|
| US-? | <ścieżka> | idle | brak | <czego brakuje — pytanie do projektanta> |

## Przepływy

## Pytania do bramki
