---
name: eng-legacy-dossier
description: Użyj przy opisie lub audycie architektury kodu legacy przed refaktorem — as-is, reguły, ocena z dowodami, roadmapa.
metadata:
  przeglad: "2027-10-17"
  katalog: "Użyj, gdy trzeba opisać i wytłumaczyć istniejący kod (legacy) przed poprawkami i refaktorem — teczka systemu: karty modułów z odpowiedzialnością, wejściami i wyjściami, reguły biznesowe wydobyte z kodu z dowodem plik:linia i pewnością, dane i integracje, kluczowe przepływy, słownik kod ↔ biznes, pytania do ludzi, stan modułów i kandydaci do refaktoru; tryb audytu architektury (np. Angular w monorepo Nx): Architecture Inventory (as-is), Assessment (ustalenia z dowodem, kategorie, mocne strony) i Recommendations & Roadmap (decyzja od „bez zmian” do przeprojektowania, priorytet, weryfikacja); skrypt sprawdza kompletność teczki i dowody. Nie do samej mapy struktury i punktów wejścia (eng-codebase-mapping), oceny długu (eng-tech-debt-audit), wyboru refaktoryzacji (eng-refactor-planning) ani analizy binariów bez źródeł."
  slowa: "legacy, stary system, stary kod, kod zastany, opisz system, opisz kod, dokumentacja legacy, brak dokumentacji, nikt nie wie jak działa, wytłumacz moduły, co robi ten moduł, reguły biznesowe w kodzie, przejmujemy system, onboarding do systemu, teczka systemu, przed refaktorem, przed poprawkami, posegregować kod, zrozumieć system, audyt architektury, ocena architektury, stan obecny, as-is, architecture inventory, assessment, rekomendacje zmian, roadmapa, granice bibliotek, monorepo"
---

# Teczka systemu legacy — opisać, posegregować, wytłumaczyć

Cel: dokument, po którym osoba bez znajomości systemu wie, **co** robi każda część, **dlaczego** (reguły biznesowe)
i **gdzie** to jest w kodzie — a zespół ma gotowe wejście do poprawek i refaktoru. Teczka opisuje stan obecny,
niczego nie zmienia w kodzie. Każde twierdzenie o zachowaniu ma dowód `plik:linia` albo pewność „do weryfikacji”
(core-grounding) — opis „z pamięci ogólnej” jest gorszy niż brak opisu, bo wprowadza w błąd przy refaktorze.

## Procedura
0. **Zakres i mapa.** Ustal z człowiekiem system lub katalog i zapisz commit HEAD. Jeśli nie ma
   `docs/project/04-architecture/codebase-map.md`, zrób najpierw mapę wg **eng-codebase-mapping** (inwentarz,
   warstwy, punkty wejścia, strefy ryzyka) — teczka korzysta z niej, nie powtarza jej.
1. **Podział na moduły** z mapy (warstwy, legenda modułów). Moduł = część z jedną odpowiedzialnością biznesową,
   nie katalog. Kolejność opisu: rdzeń i strefy ryzyka najpierw, peryferia na końcu albo jedną linią w indeksie.
2. **Karta modułu** `modules/<moduł>.md` wg `references/szablon.md`:
   - **Po co** — 1–2 zdania językiem biznesu, bez nazw klas;
   - **Odpowiedzialności, Wejścia i wyjścia** (endpointy, zdarzenia, pliki, zadania cykliczne), **Dane** (tabele,
     encje: kto pisze, kto czyta), **Zależności** (do i od modułu) — z grafu, nie z pamięci: dla Pythona i TS/JS
     `python3 .claude/skills/eng-codebase-mapping/scripts/code_graph.py <repo> --focus <ścieżka modułu>` (importy
     wychodzące i przychodzące z rodzajem); DI, kolejki, rejestry i wywołania po nazwie graf pomija — do Pytań;
   - **Reguły biznesowe** — tabela `ID | Reguła | Dowód | Pewność`. Regułę piszesz jako zdanie dla biznesu
     („Faktura po 30 dniach jest przeterminowana”), nie jako opis kodu. Pewność: `test` (jest test, który jej
     pilnuje), `kod` (wynika wprost z kodu), `do weryfikacji` (wnioskowana, sprzeczna lub bez dowodu — trafia też do
     Pytań). Gdzie szukać reguł: `references/szablon.md` § Skąd brać reguły;
   - **Pułapki** — zachowania zaskakujące: efekty uboczne, stan globalny, magiczne stałe, zależność od kolejności,
     ta sama reguła w kilku miejscach (często inaczej);
   - **Testy** — co jest pokryte, czego brakuje dla reguł z tabeli;
   - **Stan** w nagłówku: `zielony` (zrozumiały, przetestowany), `żółty` (działa, ale ryzykowny w zmianie),
     `czerwony` (niezrozumiały lub bez testów przy krytycznych regułach) — zawsze z powodem.
3. **Przepływy (3–5 kluczowych)** w indeksie: krok po kroku przez moduły z plikami, diagram sekwencji (Mermaid).
   Pogłębienie jednego przepływu: `.claude/skills/eng-codebase-mapping/references/analiza-przeplywu.md`.
4. **Słownik** kod ↔ biznes: nazwa w kodzie, pojęcie biznesowe, uwaga o rozjeździe (`Doc` = faktura, ale też
   korekta). Rozjazdy modelu i niezmienniki pogłębia **ddd-legacy-modernization**.
5. **Stan i kandydaci do refaktoru** — tabela modułów ze stanem i listą kandydatów (co, dlaczego, dowód). Teczka
   kończy na kandydatach: ocenę wagi i wysiłku robi **eng-tech-debt-audit**, wybór i plan **eng-refactor-planning**,
   wykonanie z zamrożonym zachowaniem **eng-behavior-preserving-refactoring**.
6. **Sprawdzenie** — **uruchom** `python3 .claude/skills/eng-legacy-dossier/scripts/dossier_check.py
   docs/project/04-architecture/legacy-dossier` (z katalogu repozytorium). Pierwsza linia: `legacy-dossier-check: OK`
   albo `BŁĘDY` z listą: brakujące sekcje i karty, powtórzone ID, dowód wskazujący nieistniejący plik lub linię.
   Błędy poprawiasz przed oddaniem; liczba reguł „do weryfikacji” idzie do TL;DR.

Wynik: `docs/project/04-architecture/legacy-dossier/README.md` (indeks) + `modules/*.md`; TL;DR i Przekazanie wg
core-project-record. Duży system: najpierw indeks i karty rdzenia, reszta w kolejnych sesjach (punkt kontrolny).

## Tryb: audyt architektury (Inventory → Assessment → Recommendations)
Gdy celem jest **ocena** architektury i plan zmian, a nie tylko opis — np. Angular w monorepo Nx po kilku zespołach.
Kolejność jest twarda: najpierw stan obecny z dowodami, ocena dopiero potem, rekomendacje na końcu.
1. **Zakres i kryteria** — które aplikacje i biblioteki (współdzielone oceniasz razem z konsumentami), czy także
   build, testy, CI; checklista obszarów z pytaniem na każdy. Zapis w `assessment.md` § Zakres i metoda, Kryteria oceny.
2. **Architecture Inventory (as-is)** = indeks i karty z procedury wyżej; modułem jest aplikacja lub biblioteka.
   Bez ocen. Nx i Angular: `references/nx-angular.md` (polecenia, inwentarz bibliotek, zależności, routing, stan, API).
3. **Assessment** (`assessment.md`) — ustalenia `ARCH-NNN`: stan obecny / oczekiwany / luka, dowód, wpływ i
   **kategoria**: potwierdzony problem · ryzyko · niespójność · możliwość poprawy · preferencja. Fakt (jest import)
   oddzielasz od interpretacji (to szkodzi — wymaga uzasadnienia). Osobna sekcja **Mocne strony** — co zachować.
4. **Recommendations & Roadmap** (`recommendations.md`) — `REC-NNN` do ustaleń: decyzja na najniższym szczeblu,
   który rozwiązuje problem (bez zmian → dokumentacja → konfiguracja → refaktoryzacja przyrostowa → strukturalna →
   przeprojektowanie), priorytet P1–P3, wysiłek, ryzyko, sposób weryfikacji; docelowe zasady (obowiązkowe /
   zalecane / zależne od kontekstu); roadmapa w fazach; kryteria sukcesu.
5. **Sprawdzenie** — ten sam `dossier_check.py`: pilnuje dowodów potwierdzonych problemów, rekomendacji dla każdego
   z nich i blokuje refaktoryzację strukturalną uzasadnioną samą preferencją.

Szablony, kryteria (clarity, consistency, coupling, cohesion, testability, enforceability) i harmonogram:
`references/audyt-architektury.md`. Głęboka ocena długu w skali repo — eng-tech-debt-audit; wybór wariantu
refaktoryzacji — eng-refactor-planning.

## Zasady
- **Czytelnik nie zna systemu.** Najpierw „co i po co”, potem „jak”; krótkie zdania, nazwy plików w `kodzie`.
- **Fakt albo pytanie.** Nie zgadujesz intencji autora; sprzeczność kod ↔ test ↔ komentarz opisujesz i pytasz.
- **Bez ocen ludzi** i bez „to jest źle napisane” — opisujesz zachowanie i ryzyko zmiany.
- **Koszt:** szeroki skan robią narzędzia (eng-codebase-mapping). Karty niezależnych modułów można zlecić
  równolegle wykonawcom tylko do odczytu, z briefem: zakres plików, szablon, polecenie sprawdzenia (core-cost-control §0).
- **Teczka to nie refaktor.** Nie poprawiasz kodu „przy okazji” — kandydaci trafiają do sekcji 5.

## Przykład
Wejście: „Opisz moduł faktur w starym systemie (Java), przed zmianą zaokrągleń.”
Wynik (fragment `modules/faktury.md`):

```markdown
<!-- legacy-dossier:module -->
# Moduł: faktury
Stan: żółty — zaokrąglenie kwot w dwóch miejscach, różnymi metodami

## Reguły biznesowe
| ID | Reguła | Dowód | Pewność |
|---|---|---|---|
| R-FAK-01 | Kwotę brutto zaokrągla się do 2 miejsc „połówkowo w górę” | src/billing/Invoice.java:142 | test |
| R-FAK-02 | PDF pokazuje kwotę zaokrągloną „bankowo” — może różnić się o 1 grosz | src/pdf/PdfExporter.java:57 | kod |
| R-FAK-03 | Faktura po 30 dniach jest przeterminowana (dni kalendarzowe?) | — | do weryfikacji |

## Pułapki
- Ta sama kwota liczona w `Invoice.total()` i `PdfExporter.render()` (R-FAK-01 vs R-FAK-02).
```

W indeksie: kandydat „jedno miejsce zaokrągleń” z dowodem obu linii → eng-tech-debt-audit; pytanie
„dni kalendarzowe czy robocze?” → Pytania otwarte.

## Checklista
- [ ] zakres i commit HEAD zapisane; mapa (eng-codebase-mapping) istnieje albo powstała pierwsza
- [ ] każdy moduł z indeksu ma kartę; „Po co” językiem biznesu; Stan z powodem
- [ ] każda reguła: zdanie dla biznesu, dowód `plik:linia` lub „do weryfikacji” + pytanie
- [ ] 3–5 przepływów, słownik z rozjazdami, kandydaci do refaktoru z dowodem (bez zmian w kodzie)
- [ ] `dossier_check.py` → `legacy-dossier-check: OK`; liczba reguł „do weryfikacji” w TL;DR

## Materiały dodatkowe
- `references/szablon.md` — szablon indeksu i karty modułu, skąd brać reguły biznesowe; czytaj przy pisaniu teczki.
- `references/audyt-architektury.md` — tryb audytu: etapy, szablony ustalenia i rekomendacji, kategorie, priorytety.
- `references/nx-angular.md` — inwentarz i analiza monorepo Nx z Angularem; czytaj przy audycie takiego repo.

## Źródła
- Feathers, *Working Effectively with Legacy Code* (2004) — testy charakteryzujące jako dowód obecnego zachowania.
- Evans, *Domain-Driven Design* (2003) — język wszechobecny; słownik kod ↔ biznes.
