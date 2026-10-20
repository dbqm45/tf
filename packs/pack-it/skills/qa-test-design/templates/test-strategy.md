---
artifact: test-strategy
phase: plan
status: draft
version: 1
author: <agent>
created: <RRRR-MM-DD>
updated: <RRRR-MM-DD>
inputs: [docs/project/03-requirements/requirements.md]
---

# Strategia testów projektu

## TL;DR
<!-- 3–5 zdań: profil bazy testów, top 3 ryzyka, bieżąca faza, najbliższa bramka. -->

## Wejścia
- Profil bazy testów: `brak` | `rzadki` | `znaczący` — <uzasadnienie jednym zdaniem>
- Gorące miejsca (git, ostatnie 30 dni, zakres zaakceptowany przez człowieka): <katalog — liczba commitów> | pominięte (< 5 commitów)
- Wywiad: W1 … · W2 … · W3 … · W4 … · W5 …

## Mapa ryzyk
| # | Ryzyko (scenariusz awarii) | Wpływ | Prawdopodobieństwo | Źródło (bez plik:linia) |
|---|---|---|---|---|
| 1 | | wysoki/średni/niski | wysoki/średni/niski | |

Monitoring zamiast testu: <ryzyka wysoki wpływ × niskie prawdopodobieństwo>
Wyniki kontroli: <usunięte lub przeformułowane ryzyka>

## Odpowiedź na ryzyko
| Ryzyko | Co udowodni ochronę | Założenie do podważenia | Kontekst do ustalenia w kodzie | Najtańsza warstwa (hipoteza) | Antywzorzec |
|---|---|---|---|---|---|
| #1 | | | | | |

## Fazy wdrażania
| # | Faza | Jaką ochronę udowadnia | Ryzyka | Rodzaje testów | Stan | Folder zmiany |
|---|---|---|---|---|---|---|
| 1 | | | #1 | | nie rozpoczęta | |
<!-- Stany: nie rozpoczęta → otwarta → zbadana → zaplanowana → w realizacji → zakończona -->

## Bramki jakości
| Bramka | Warstwa (edycja / commit / push / CI) | Wymagana od | Co łapie |
|---|---|---|---|
| | | od fazy N | |

## Przepisy
- Testy jednostkowe: TBD — faza N (ochrona przed <zachowanie>)
- Testy integracyjne: TBD — faza N
- E2E: TBD — faza N

## Czego świadomie nie testujemy
| Co | Powód | Kiedy ponownie ocenić |
|---|---|---|

## Świeżość
- Przegląd strategii: <RRRR-MM-DD>
- Narzędzia i wersje (sprawdzone: <RRRR-MM-DD>):

## Przekazanie
<!-- Co następna faza/osoba musi wiedzieć; otwarte pytania do człowieka. -->
