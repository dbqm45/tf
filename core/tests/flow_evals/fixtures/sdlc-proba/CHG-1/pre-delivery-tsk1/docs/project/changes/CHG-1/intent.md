---
artifact: intent
phase: discovery
status: proposed
version: 1
author: pdi
created: 2026-10-30
updated: 2026-10-30
inputs: []
change: CHG-1
source: PRB-1
source_reported_at: 2026-10-30
---
# Zamiar zmiany CHG-1

## Problem

Odwiedzający stronę sdlc-sandbox nie widzi, kiedy strona była ostatnio wdrożona. Strona nie pokazuje żadnego
wskaźnika aktualności, więc odwiedzający nie wie, czy to, co widzi, jest już nową wersją. Skutek: brak zaufania
do wyświetlanych treści, pytania na czacie przy każdym wdrożeniu. Obejście: pytanie do zespołu na czacie.
Częstość: przy każdym wdrożeniu. Źródło: zgłoszenie PRB-1.

## Warianty

| Wariant | Opis | Za | Przeciw | Koszt |
|---|---|---|---|---|
| A: Data wdrożenia w stopce za flagą | Data z `config/build.json` w stopce strony; dostęp przez flagę `show_last_deployed` | Widoczna bez narzędzi deweloperskich; flaga umożliwia rollout; bezpośrednio odpowiada na problem | Wymaga wygenerowania `config/build.json` w kroku wdrożenia (nowy artefakt); zmienia wygląd UI | 2 cięcia (~4 h) |
| B: Data w meta-tagu lub nagłówku HTTP | Data wdrożenia jako `<meta name="deployed-at">` lub nagłówek `X-Deployed-At` | Brak zmian w widocznym UI; prosta implementacja | Widoczna tylko przez narzędzia deweloperskie — nie rozwiązuje problemu zaufania dla zwykłego odwiedzającego | 1 cięcie (~1 h) |
| C: Commit hash w stopce | Skrócony hash ostatniego commita w stopce (z pliku lub zmiennej środowiskowej przy wdrożeniu) | Jednoznaczna identyfikacja wersji; łatwa do porównania z repo | Mało czytelna dla niedewelopera; nie odpowiada na pytanie „kiedy?"; nie rozwiązuje problemu zaufania | 1 cięcie (~1 h) |

## Wybrany wariant

**Wariant A** — data wdrożenia w stopce za flagą `show_last_deployed`.

Bezpośrednio odpowiada na potrzebę odwiedzającego: data jest widoczna bez narzędzi deweloperskich.
Flaga daje kontrolę nad stopniowym wdrożeniem. Warianty B i C nie rozwiązują problemu zaufania
dla zwykłego odwiedzającego — wymagają narzędzi deweloperskich albo znajomości systemu kontroli wersji.
Wyższy koszt wariantu A jest uzasadniony tym, że jako jedyny rozwiązuje problem.

## Metryki sukcesu

- Po wdrożeniu R1 na prod z włączoną flagą `show_last_deployed`: data wdrożenia jest widoczna w stopce
  strony — weryfikowalna testem manualnym (`APP_ENV=prod`, żądanie GET `/`).
- Guardrail: brak rollbacków spowodowanych tą zmianą w tygodniu po R1 (`rollbacks = 0`).

## Poza zakresem

- Historia wdrożeń (więcej niż jedno ostatnie wdrożenie).
- Godzina wdrożenia (tylko data).
- Powiadomienia push ani e-mail o nowym wdrożeniu.
- Commit hash ani wersja semantyczna w widoku strony.
- Środowisko testowe — flaga na `test` jest opcjonalna dla dewelopera, nie jest częścią R1.

## Pytania do bramki

- [właściciel] Czy `config/build.json` powinien być gitignorowany i generowany wyłącznie przez skrypt
  wdrożenia (`uv run sdlc deploy`), czy dopuszczalne jest commitowanie go z datą budowania lokalnego
  jako placeholdera?
