# Ścieżki refaktoryzacji, archeologia intencji i weryfikacja liczb

## 1. Archeologia intencji
| Pytanie | Polecenie | Uwagi |
|---|---|---|
| kto i dlaczego nadał funkcji obecny kształt | `git log -L :<funkcja>:<plik>` | historia samej funkcji z diffami; dla dokładnego wykrywania funkcji ustaw sterownik diff w `.gitattributes` (np. `*.go diff=golang`, `*.java diff=java`, `*.py diff=python`) |
| historia zakresu linii | `git log -L <od>,<do>:<plik>` | gdy funkcja nie jest rozpoznawana |
| skąd pochodzą linie (z przeniesieniami) | `git blame -w -C -C <plik>` | `-w` ignoruje białe znaki, `-C` śledzi kod przeniesiony z innych plików |
| czy mechanizm się psuł | `git log --oneline --grep='fix' -- <plik>` + lektura opisów | 0 poprawek przez lata to dowód stabilności decyzji |
| opis decyzji poza commitem | numer PR z opisu commita → `gh api repos/<o>/<r>/pulls/<nr>` | czytaj „dlaczego”, nie tylko „co” |

Werdykt zapisujesz z dowodem: `świadome ograniczenie — commit 27d536b (2020-03): wsadowy INSERT dla szybkości
importu; 0 poprawek kolejności kolumn w historii pliku`. Bez dowodu: `unknown` + pytanie do zespołu (kto pamięta).

## 2. Strangler Fig
1. Wybierz szew wejściowy (router, fasada, kolejka), przez który przechodzi ruch do starego kodu.
2. Nowa implementacja obsługuje najpierw mały, dobrze przetestowany wycinek zachowania; szew kieruje tam tylko ten
   wycinek.
3. Porównuj wyniki (równoległe uruchomienie lub testy charakteryzujące), przenoś kolejne wycinki.
4. Gdy stary kod nie dostaje ruchu — usuń go osobnym commitem.
Pasuje do: wymiany podsystemu, punktu wejścia, integracji. Ryzyko: dwa systemy żyją długo → data wygaszenia w planie.

## 3. Branch by Abstraction
1. Wprowadź abstrakcję (interfejs, port) nad miejscem, gdzie klienci używają starego kodu; stara implementacja za nią.
2. Przepnij klientów na abstrakcję — commit po commicie, zachowanie bez zmian.
3. Zbuduj nową implementację obok; testy kontraktowe abstrakcji przechodzą dla obu.
4. Przełącz (flaga lub konfiguracja, najlepiej per klient lub per środowisko).
5. Usuń starą implementację i — jeśli nie jest już potrzebna — samą abstrakcję.
Główna gałąź cały czas nadaje się do wydania; zamiast długiej gałęzi masz serię małych PR.

## 4. Mikado
1. Zapisz cel jako korzeń grafu (np. „zapis przez `PostRepository` zamiast bezpośrednich zapytań”).
2. Spróbuj zrobić cel wprost, z limitem czasu (np. 15 min). Zapisz każdy błąd kompilacji lub testu jako węzeł-prerekwizyt.
3. **Cofnij wszystko** (`git restore .` / `git reset --hard` na gałęzi roboczej — za zgodą, gdy są niezacommitowane zmiany człowieka).
4. Wybierz liść (prerekwizyt bez własnych prerekwizytów), zrób go, zacommituj, sprawdź testy.
5. Wróć do kroku 2 dla rodzica. Kończysz, gdy korzeń da się zrobić bez błędów.
Graf trzymasz w kroku projektu (Mermaid `flowchart BT`), węzły odhaczasz wraz z commitami.

## 5. Osłona zamiast przebudowy
Świadome ograniczenie zostaje, ale ryzyko „łatwo o tym zapomnieć” zamieniasz w „nie da się tego popsuć”:
- test, który zawodzi przy rozjechaniu (np. dwie tablice kolumn muszą mieć tę samą kolejność → test z wartościami-
  wartownikami, `.claude/skills/eng-behavior-preserving-refactoring/references/przyklady.md`);
- reguła lintera lub ast-grepa w CI (wzorzec zabroniony poza jednym plikiem);
- walidacja w generatorze kodu (np. dekorator musi nadpisać wszystkie metody interfejsu albo jawnie je wymienić
  na liście wyjątków).
Osłona to czysty dodatek: jeden commit `test:` albo `build:`, odwracalny revertem.

## 6. Weryfikacja twierdzeń ast-grepem
| Twierdzenie | Wzorzec (sprawdzone na ast-grep 0.50.0) | Potwierdzenie zera |
|---|---|---|
| „`save` wołane w 4 miejscach” (TS) | `ast-grep run -p '$S.save($$$A)' -l ts --json=stream src \| wc -l` | `rg -n '\.save\(' src` |
| „`SaveMultiple` wołane w 4 miejscach” (Go) | `ast-grep run -p 'func _() { $S.SaveMultiple($$$A) }' --selector call_expression -l go .` | `rg -n 'SaveMultiple\('` |
| „interfejs ma 54 metody” (Go) | `ast-grep run -k method_elem -l go <plik>` (jedna linia na metodę interfejsu) | `rg -c` po sygnaturach w pliku |
| „warstwa X nie nadpisuje `Delete`” (Go) | `ast-grep run -p 'func ($R $T) Delete($$$A) $$$RET' -l go <katalog-warstwy>` | `rg -n 'func \(.*\) Delete\(' <katalog>` |
- **Pułapka cichego zera:** wzorzec musi być poprawnym kodem w danym języku. W Go samo wyrażenie
  `$S.SaveMultiple($$$A)` nie parsuje się na poziomie pliku i zwraca 0 trafień bez błędu — potrzebny kontekst
  (`func _() { … }`) i `--selector`. Podejrzane zero sprawdzisz przez `--debug-query=ast` (węzły `ERROR` = zły wzorzec)
  i zawsze przez `rg`.
- ast-grep pomija komentarze i literały tekstowe i odróżnia `Save(` od `SaveMultiple(`; `rg` łapie wszystko — różnica
  między wynikami to informacja (wystąpienia w komentarzach, testach, kodzie generowanym).
- Brak dopasowań kończy `ast-grep` kodem 1 — w skryptach nie traktuj tego jako awarii.
- Wynik zapisuj z wersją narzędzia i commitem, na którym liczono.

## 7. Szablon raportu eksploracji (`docs/project/<krok>/research.md`)
```markdown
---
status: exploration
last_updated: <data>
tags: [refactor-opportunities]
verified_at_commit: <sha lub „—”>
---
# Opcje refaktoryzacji: <obszar>
**Intencja:** co badamy · czego NIE robimy (zmian, decyzji) · kto decyduje i kiedy
## Lista problemów i klasyfikacja
| # | Problem (źródło) | KANDYDAT / wejście | Uzasadnienie |
## Kandydaci
### K1: <nazwa>
- Obecny kształt (evidence/inference/unknown, plik:linia) · teza archetypu
- Intencja: świadome ograniczenie / przypadkowa złożoność / unknown — dowód
- Wykonalność: abstrakcja, zasięg, osłony i testy (CI), prerekwizyt
## Opcje refaktoryzacji (ranking)
1. … obecny → docelowy · dlaczego · zasięg · ścieżka · prerekwizyt
## Rozważone i odrzucone
## Weryfikacja twierdzeń (ast-grep)
| Twierdzenie | Werdykt | Dowód | Metoda |
## Decyzje człowieka (wypełnia etap planowania)
```
