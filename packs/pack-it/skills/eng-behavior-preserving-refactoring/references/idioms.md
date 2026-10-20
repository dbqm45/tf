# Idiomy implementacji logiki domenowej i przejścia między nimi

## Katalog
| Idiom | Rozpoznasz po | Kiedy dobry | Kiedy szkodzi |
|---|---|---|---|
| **Model anemiczny + serwis** | encje z samymi polami, logika w serwisach | CRUD, proste walidacje | reguły rozproszone po serwisach, powtarzane `if` |
| **Bogaty agregat (mutowalny)** | prywatny stan, metody komend sprawdzają niezmienniki, mutują stan i zwracają/rejestrują zdarzenia; ORM zapisuje zmiany | konkurencja o zasoby, dużo reguł, zespół zna OOP | trudniej testować bez infrastruktury; efekty uboczne wymieszane z decyzją |
| **Decider (funkcyjny rdzeń, imperatywna powłoka)** | niezmienny stan; `decide(stan, komenda) → decyzja` (nowy stan i/lub zdarzenia albo odrzucenie); I/O tylko w powłoce | testowalność, czyste reguły, perspektywa event sourcingu | prosty CRUD; zespół bez doświadczenia FP |
| **Decider ścisły (event-sourced)** | `decide(stan, komenda) → zdarzenia` + `evolve(stan, zdarzenie) → stan` | event sourcing, audyt | wymaga zdarzeń niosących pełny stan zmiany — często zmienia kontrakt zdarzeń |

Zmiana idiomu nie jest celem samym w sobie — uzasadnij ją (testowalność, rozdzielenie decyzji od efektów, przyszły event sourcing).

## Przepis: bogaty agregat → decider (wariant bez zmiany kontraktu zdarzeń)
1. Stan staje się niezmienny (rekord/obiekt tylko do odczytu); **pole wersji** do blokady optymistycznej przechodzi bez zmian.
2. Każda komenda dostaje własny typ (najlepiej zamknięty zbiór — unia/sealed).
3. Używaj **istniejących** zdarzeń bez nowych pól.
4. Warunki odrzucenia przenieś **dosłownie**, zachowując rodzaj odrzucenia.
5. Rdzeń jest czysty: bez repozytorium, zegara (czas jako parametr komendy), publikatora.
6. Powłoka (serwis aplikacyjny): **wczytaj → decyduj → zapisz (jawnie!) → publikuj**, w tej samej granicy transakcji co wcześniej.
7. Sterownik domenowy testów przepnij na `decide`.
Wariant ścisły (`evolve`) — tylko za zgodą, bo zwykle wymaga wzbogacenia zdarzeń (zmiana kontraktu).
Składnia w konkretnym języku: lang-* (np. unie/sealed, rekordy).

## Przepisanie strukturalne ast-grepem (zmiana kształtu wywołań w wielu miejscach)
- Podgląd bez zapisu: `ast-grep run -p '<wzorzec>' -r '<cel>' -l <język> <katalog>` wypisuje diff i niczego nie
  zmienia; `-i` (`--interactive`) zatwierdzasz zmianę po zmianie, `-U` (`--update-all`) stosujesz wszystkie.
- Powtarzalne przepisanie: reguła YAML z polem `fix`, uruchamiana `ast-grep scan`; reguła trafia do repo razem
  z commitem.
- W opisie commita liczba dopasowań: wzorzec źródłowy przed = N, po = 0; wzorzec docelowy po = N. Zera potwierdzasz
  `rg`, bo wzorzec niebędący poprawnym kodem w danym języku też daje zero.
- W przeciwieństwie do `sed` ast-grep odróżnia `save(` od `saveMultiple(` i pomija komentarze oraz stringi
  (sprawdzone na ast-grep 0.50.0, 2026-10-10). Uruchamiaj binarkę `ast-grep` — na Linuksie `sg` to zwykle polecenie
  zmiany grupy.

