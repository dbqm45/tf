---
name: eng-refactor-planning
description: Użyj, gdy z długu trzeba wybrać, co i jak refaktoryzować — ranking opcji i sprawdzenie jego liczb w kodzie, Strangler, Mikado, plan.
metadata:
  przeglad: "2027-10-09"
  katalog: "Użyj, gdy z listy długu, ryzyk lub hotspotów trzeba wybrać, co refaktoryzować, do jakiego docelowego kształtu i jaką odwracalną ścieżką — klasyfikacja kandydatów, trzy perspektywy (obecny kształt w archetypach Transaction Script / Table Module / Domain Model, intencja z historii gita i ADR, wykonalność), dopasowanie skali (zostaje / osłona zamiast przebudowy / przebudowa), Strangler Fig, Branch by Abstraction, Mikado, ranking 2–3 opcji z odrzuconymi, weryfikacja liczb ast-grepem z potwierdzeniem zer przez rg, decyzja człowieka i plan faz. Nie do samego audytu długu (eng-tech-debt-audit), dowodu zachowania przy wykonaniu (eng-behavior-preserving-refactoring) ani przeprojektowania pojęć domeny (ddd-legacy-modernization)."
  slowa: "co refaktoryzować, plan refaktoryzacji, plan refaktoru, opcje refaktoryzacji, ranking refaktoryzacji, refactor opportunities, od czego zacząć refaktor, zrefaktoruj moduł, przepisać od zera, strangler fig, branch by abstraction, mikado, odwracalna ścieżka, docelowy kształt modułu, świadome ograniczenie, przypadkowa złożoność, guard zamiast przebudowy, archeologia gita, git log -L"
---

# Od długu do planu refaktoryzacji

„Zrefaktoruj ten moduł” to zlecenie bez celu (jaki kształt na końcu?), bez historii (co jest dziwactwem, a co
decyzją nośną?) i bez drogi odwrotu (40 plików naraz nie zweryfikujesz po kawałku). Agentowi zlecasz więc **opcje
z rankingiem**, a refaktor zaczyna się od decyzji człowieka. Wejście: raport długu (eng-tech-debt-audit), analiza
przepływu (`.claude/skills/eng-codebase-mapping/references/analiza-przeplywu.md`) albo lista hotspotów.

## Etapy (każdy w osobnej sesji, intencja zapisana na górze kroku — core-project-record)
**eksploracja → lektura człowieka → decyzja i plan → realizacja.** Eksploracja tylko czyta i kończy się raportem.
Nie zmienia kodu i nie kończy się pytaniem „czy zatwierdzasz?”, bo to wymusza decyzję bez lektury. Intencja
kroku: co badamy, czego na tym etapie nie robimy (zmian, decyzji), kto i kiedy decyduje.

## 1. Lista problemów i klasyfikacja (na początku raportu, do audytu przez człowieka)
- Wypisz **każdy** problem z wejścia, niezależnie od etykiety (dług, ryzyko, hotspot, znalezisko). Ustalenia wejścia
  traktujesz jako zebrane dowody — nie wyprowadzasz ich od nowa.
- **KANDYDAT** = naprawa zmienia strukturę kodu. Reszta (brak testu, luka w dokumentacji) nie jest kandydatem, ale
  zostaje jako wejście do oceny wykonalności i kosztu.
- Prawdziwa naprawa to przeprojektowanie pojęć biznesowych, nie struktury? → zatrzymaj się przy tym kandydacie
  i odeślij do ddd-legacy-modernization.

## 2. Trzy perspektywy na kandydata (trzech wykonawców równolegle, tylko odczyt)
Każde twierdzenie z etykietą evidence / inference / unknown i `plik:linia`. Brak danych = `unknown`, nie domysł.
- **a) Obecny kształt:** gdzie żyje logika, jak mieszają się odpowiedzialności, jakie abstrakcje już są. Teza
  w języku archetypów: **Transaction Script** (procedura na żądanie) · **Table Module** (jedna instancja na tabelę)
  · **Domain Model + Service Layer** (dane i zachowanie razem, cienka warstwa operacji). To spektrum, nie ranking —
  np. „przerośnięty Transaction Script: 180 linii walidacji, liczników i transakcji w jednej funkcji; logika
  potrzebuje modelu za warstwą usług”.
- **b) Intencja (historia):** najpierw ADR i dokumenty projektowe, potem archeologia gita —
  `git log -L :<funkcja>:<plik>`, `git blame -w -C <plik>`, opisy commitów i PR. Werdykt: **świadome ograniczenie**
  (decyzja nośna) / **przypadkowa złożoność** / `unknown`. Liczba commitów naprawczych dla mechanizmu też jest
  dowodem (np. 0 poprawek przez 6 lat). Złożoność istotna (z natury problemu) zostaje — można ją najwyżej lepiej
  ułożyć; usuwasz przypadkową.
- **c) Wykonalność:** istniejąca czy nowa abstrakcja, zasięg zmiany z raportu wejściowego (brak → `python3
  .claude/skills/eng-codebase-mapping/scripts/code_graph.py <repo> --impact <plik>`: pliki w 1. i 2. kroku i testy;
  liczby potwierdź `rg`), istniejące osłony
  i testy (sprawdź konfigurację CI, nie tylko katalog testów), pierwszy krok-prerekwizyt.

## 3. Dopasowanie skali (right-sizing)
| Werdykt | Ruch |
|---|---|
| mały moduł, prosta logika | **zostaje** Transaction Scriptem |
| świadome ograniczenie | **osłona zamiast przebudowy**: tani, deterministyczny test, reguła lintera albo walidacja w generatorze; kształt bez zmian, odwracalne jednym revertem |
| przypadkowa złożoność, której koszt rośnie (hotspot: złożoność × częstość zmian) | **przebudowa** odwracalną ścieżką (§4) |
Bez tego filtra powstają wzorce wszędzie i wartość nigdzie. Kolejność spłaty: najpierw dług o najwyższych
„odsetkach”, czyli ten, który spowalnia bieżące zmiany.

## 4. Odwracalne ścieżki
- **Strangler Fig:** nowy kod rośnie na brzegach starego, zachowanie przenosisz kawałkami, stare wygaszasz; w każdej
  chwili działa całość. Do wymiany podsystemu lub punktu wejścia.
- **Branch by Abstraction:** abstrakcja nad punktem styku → stara implementacja za nią → nowa obok → przełączenie
  (flaga, konfiguracja) → usunięcie starej. Główna gałąź przez cały czas nadaje się do wydania; bez długiej gałęzi.
- **Mikado:** spróbuj docelowej zmiany, zapisz, co pękło (graf prerekwizytów), **cofnij**, rozwiązuj od liści do
  korzenia; każdy liść to mały, osobno odwracalny commit. Odpowiedź na „wszystko zależy od wszystkiego”.
- **Przepisanie od zera — nie:** gubi wiedzę zaszytą w poprawkach; tanie generowanie kodu tego nie zmienia.
Szczegóły kroków, test charakteryzujący i przykłady grafów: `references/sciezki-i-weryfikacja.md`.

## 5. Raport eksploracji — sekcja „Opcje refaktoryzacji (ranking)”
- **2–3 najmocniejsze opcje**, każda: obecny → docelowy kształt · dlaczego to miejsce (koszt długu vs koszt zmiany)
  · zasięg · szkic odwracalnej ścieżki · pierwszy prerekwizyt.
- **Rozważone i odrzucone** — każda z jednym zdaniem powodu (np. „świadome ograniczenie → osłona”).
- **Weryfikacja twierdzeń strukturalnych**, na których stoi ranking („54 metody”, „4 wywołania”, „nadpisuje A,
  ale nie B”), w osobnym przebiegu:
  1. każde twierdzenie → wzorzec `ast-grep run -p '<wzorzec>' -l <język> --json=stream` (binarka `ast-grep`;
     `sg` na Linuksie to zwykle polecenie zmiany grupy, nie ast-grep);
  2. **każde zero z ast-grepa potwierdź zwykłym `rg -n '<tekst>'`** — zero może znaczyć zły wzorzec (np. w Go
     samo wywołanie bez kontekstu funkcji nie parsuje się i daje 0 trafień bez błędu);
  3. poprawki w miejscu ze śladem: „5 (raport: 4)”; tabela twierdzenie → werdykt (potwierdzone / doprecyzowane /
     obalone) → dowód `plik:linia` → metoda;
  4. rankingu ani werdyktów intencji przy tym **nie zmieniasz** — rozbieżność dopisujesz „do decyzji na etapie
     planowania”.

## 6. Decyzja i plan
- Rozmowa wg core-plan-interview; **pierwsze pytanie: „którą opcję realizujemy?”** — akceptacja rankingu to jawna
  decyzja. Nowy dowód znaleziony przy planowaniu (np. luka okazała się żywym błędem) to osobne pytanie, nie cichy
  dopisek do planu.
- Wąski wycinek: jedna opcja + ewentualnie tania osłona. Plan ma własności:
  - test charakteryzujący przed dotknięciem niepokrytego kodu, w miejscu, gdzie zachowanie widać bez edycji
    chronionego kodu (eng-behavior-preserving-refactoring);
  - fazy = osobne odwracalne commity, od najtańszej i najbardziej samodzielnej (osłona najpierw);
  - każda faza z kryteriami weryfikacji automatycznej i ręcznej;
  - **mechanizm ląduje na zielono, egzekwowanie włączasz osobnym commitem** (np. walidacja domyślnie wyłączona,
    potem włączana per warstwa, z listą wyjątków z uzasadnieniem);
  - sekcja „Czego NIE robimy”.
- Kilka opcji wartych realizacji na tygodnie → kampania faz (każda z własnym krokiem: eksploracja → plan →
  realizacja), a nie jeden wielki plan. Plan przegląda świeży kontekst przed realizacją.

## Przykład
**Wejście:** raport długu modułu zapisu wiadomości — 4 kandydatów. **Wynik eksploracji:**
- Faworyt z audytu „pozycyjne tablice 18 kolumn w dwóch funkcjach” → `git log -L` pokazuje commit z 2020 r.:
  celowa zamiana zapisu refleksyjnego na wsadowy INSERT dla szybkości importu; 0 poprawek kolejności w historii →
  **świadome ograniczenie → osłona**: test z wartościami-wartownikami, jeden commit `test:`, kod nietknięty.
- Ranking #1: ręczne warstwy dekorujące interfejs `Store` — metody nienadpisane przechodzą cicho niżej (zapis
  wsadowy omija indeksowanie wyszukiwarki) → walidacja kompletności w generatorze warstw, domyślnie wyłączona,
  włączana per warstwa. Weryfikacja: „interfejs ma 54 metody” → potwierdzone (ast-grep); „4 wywołania
  `SaveMultiple`” → 5 (raport: 4), piąte w teście — dopisane „do decyzji na etapie planowania”.
- Odrzucone: „podział `post.go` (3957 linii)” — przypadkowa złożoność, ale plik rzadko zmieniany; czeka.
- Plan (po decyzji człowieka): faza 1 osłona tablic, faza 2 walidacja w generatorze (wyłączona), faza 3 włączenie
  dla dwóch warstw; „Czego nie robimy”: podział `post.go`, zmiana kształtu zapisu wsadowego.

## Checklista
- [ ] lista problemów i klasyfikacja KANDYDAT / wejście na początku raportu
- [ ] każdy kandydat: kształt w archetypach, werdykt intencji z dowodem (ADR / commit / PR) albo `unknown`
- [ ] right-sizing zastosowany; świadome ograniczenia dostały osłonę, nie przebudowę
- [ ] ranking 2–3 opcji + odrzucone z powodem; liczby zweryfikowane ast-grepem, zera potwierdzone `rg`
- [ ] decyzję podjął człowiek; plan: charakteryzacja, fazy-commity, weryfikacja, egzekwowanie osobno, „czego nie robimy”

## Źródła
- Kurs 10xDevs, ed. 3 (2026), moduł 4, lekcja 4 (refaktoryzacja z agentem) i prompty do niej (eksploracja opcji,
  weryfikacja ast-grepem) — materiał szkoleniowy (dostęp 2026-10-09); opisane własnymi słowami.
- M. Fowler, *Patterns of Enterprise Application Architecture* (2002) — archetypy logiki; F. Brooks, „No Silver
  Bullet” (1986) — złożoność istotna i przypadkowa; M. Fowler, [Strangler Fig Application](https://martinfowler.com/bliki/StranglerFigApplication.html)
  i [Branch By Abstraction](https://martinfowler.com/bliki/BranchByAbstraction.html); O. Ellnestam, D. Brolund,
  *The Mikado Method* (Manning, 2014); M. Feathers, *Working Effectively with Legacy Code* (2004) — szwy i testy
  charakteryzujące (atrybucje za lekcją, dostęp 2026-10-09).
- ast-grep 0.50.0 (`ast-grep run --help`, sprawdzone 2026-10-10): `-p`, `-l`, `-r`, `-i`, `-U`, `--json`; brak
  dopasowań → kod wyjścia 1; `/usr/bin/sg` w Ubuntu pochodzi z pakietu `login` (zmiana grupy) — sprawdzone 2026-10-10.
