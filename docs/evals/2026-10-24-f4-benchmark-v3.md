# F4 (część B, v3): pomiar po kartach w Markdownie, kontroli CI i idiomach standardów — 2026-10-24

Decyzja człowieka (2026-10-24): powtórzyć test i celować w wynik lepszy od maistera, nie równy. Poprzednie pomiary:
`2026-10-24-f4-benchmark-maister.md` (v1) i `2026-10-24-f4-benchmark-v2.md` (v2). Dane: `docs/evals/2026-10-24-f4b/v3/`.

## Co się zmieniło od v2
- **PR #66:**
  - `recon_cards.py` zamienia karty modułów na `modules/<moduł>.md` z dowodami;
  - `recon_check --final` wymaga aktualnych plików `.md` kart;
  - wiersz CI musi wskazać plik pipeline'u, gdy taki jest w repo.
- **Ten PR:**
  - `standards_scan.py` liczy idiomy testów (rodzaj testu na warstwę, biblioteki dublerów, struktura przypadków,
    buildery) i idiomy kodu (np. `ctx` jako pierwszy argument, `AsReadOnly`, `Guard.Against`, `@InitBinder`,
    `redirect:`);
  - skill ocenia idiomy w obrębie miejsca, którego dotyczą, i wypisuje mapowania w całości.

## Warunki
Jak w v1 i v2: te same repozytoria, commity, skrypt, model i limit. Dokumenty maistera z v1 oceniono po raz trzeci,
ślepo, tym samym promptem. Klucz A/B jest w `v3/verdicts/klucz-AB.json`: nasz skill był w B w go-clean-arch
i petclinic, a w A w eShopOnWeb. Różnica wobec v2: oceniający dostali też `modules/*.md`, czyli karty w Markdownie,
które są teraz częścią dokumentacji. Karty JSON nadal pominięto.

## Wyniki
| | Nasz v1 | Nasz v2 | **Nasz v3** | maister (3 oceny) |
|---|---|---|---|---|
| Pokrycie ważone (z 60) | 51 (85%) | 51,5 (86%) | **58,5 (98%)** | 48 / 47 / 45 (75–80%) |
| Stack (z 12) | 9 | 11 | **12** | 12 / 12 / 12 |
| Moduły (z 12) | 9,5 | 10 | **12** | 12 / 12 / 10,5 |
| Reguły (z 15) | 14 | 13 | **15** | 5,5 / 5 / 5 |
| Standardy (z 15) | 13 | 12 | **14** | 14 / 13,5 / 13,5 |
| Inne (z 6) | 5,5 | 5,5 | **5,5** | 4,5 / 4,5 / 4 |
| Poprawność w próbie | 27/28 (96%) | 29/30 (97%) | **30/30 (100%)** | 26/29, 24/29, 25/29 (83–90%) |
| Koszt | 4,07 USD | 4,34 USD | 5,38 USD | 6,01 USD |
| Czas | 18,3 min | 18,8 min | 22,8 min | 26,0 min |

- **Według repozytoriów** (v3, w nawiasie maister w tej ocenie):
  - go-clean-arch 20 (18);
  - spring-petclinic 19 (16);
  - eShopOnWeb 19,5 (11).
- **Oceny surowe v3:** tak 57, częściowo 3, nie 0, błędnie 0.
- **`recon_check --final`:** wszystkie trzy raporty przechodzą. CI jest opisane poprawnie w każdym repozytorium,
  także w petclinic, gdzie v2 się mylił.

## Ocena celu „lepiej niż maister”
| Kategoria | Wynik | Lepiej? |
|---|---|---|
| Stack | 12 wobec 12 | remis na maksimum (więcej się nie da) |
| Moduły | 12 wobec 10,5–12 | lepiej albo remis na maksimum |
| Reguły | 15 wobec 5–5,5 | tak, wyraźnie |
| Standardy | 14 wobec 13,5–14 | tak albo remis, zależnie od oceny maistera |
| Inne | 5,5 wobec 4–4,5 | tak |
| Pokrycie łącznie | 58,5 wobec 45–48 | tak, o 10,5–13,5 punktu |
| Poprawność | 100% wobec 83–90% | tak |
| Koszt | 90% kosztu maistera | taniej, ale cel ≤ 50% nadal niespełniony |

## Zastrzeżenia
- **Rozrzut oceniających:** te same dokumenty maistera dostały 48, 47 i 45 punktów, więc różnice do ok. 3 punktów to
  szum. Przewaga v3 (10,5–13,5 punktu) jest wyraźnie większa.
- **Pobłażliwość oceniającego:** oceniający go-clean-arch sam zaznaczył, że fakt G20 (ryzyka) ocenił u nas łagodnie.
  Przy ścisłej ocenie nasz wynik to 58 zamiast 58,5.
- **Zmiana zestawu plików:** w v3 oceniający widzieli też `modules/*.md`. To dokumentacja, którą skill teraz tworzy,
  więc porównanie jest uczciwe. Część wzrostu w modułach wynika jednak z tego, że karty stały się czytelne, a nie
  z lepszej analizy.
- **Koszt:** wzrósł o 24% wobec v2 (5,38 wobec 4,34 USD). Najwięcej urosło petclinic (111 tur wobec 77). Jeden
  przebieg na repozytorium, a koszt jednego repozytorium wahał się już o 47% między przebiegami.

## Pozostałe luki (1,5 punktu)
- **petclinic C3:** standard package-by-feature nie jest nazwany wprost.
- **petclinic O2:** brak wtyczki GraalVM i testu I18nPropertiesSyncTest.
- **eShopOnWeb E17:** brak czasów życia DI (Scoped, Singleton, Transient).

Dwie pierwsze dałoby się złapać skanem bez modelu: układ pakietów według funkcji albo warstw oraz `AddScoped`,
`AddSingleton` i `AddTransient`.

## Dalsze kroki
1. Koszt: cel ≤ 50% maistera. Kandydaci: mniej tur głównego modelu (petclinic 111), limit kart dla małych
   repozytoriów, synteza standardów z sygnałów skanu bez ponownego czytania plików.
2. Test odświeżenia ze zmianą w logice.
3. Opcjonalnie: sygnały układu pakietów i czasów życia DI w `standards_scan`.
