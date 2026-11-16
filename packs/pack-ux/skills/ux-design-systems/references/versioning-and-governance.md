# Wersje, wycofywanie, współtworzenie, metryki

Reguły numerów (co to major, minor, patch, wersje przedpremierowe): core-semver. Tu: zastosowanie do systemu.

## Co jest publicznym API systemu
Komponenty (nazwy, propsy, zdarzenia, sloty), nazwy i typy tokenów, klasy i atrybuty `data-*` dokumentowane jako
publiczne, struktura DOM tylko jeśli jest dokumentowana (inaczej zastrzeż, że jest wewnętrzna).

## Klasyfikacja zmian
| Zmiana | Bump |
|---|---|
| nowy komponent, nowy wariant, nowa opcjonalna właściwość, nowy token | minor |
| poprawka błędu, dostępności, wartości tokenu bez zmiany znaczenia | patch |
| zmiana wartości tokenu widoczna dla użytkowników końcowych (kolor marki, odstęp) | minor, w changelogu osobny wpis „wygląd”; zespoły z testami zrzutowymi dostają ostrzeżenie |
| usunięcie lub zmiana nazwy komponentu, propsa, tokenu; zmiana domyślnego zachowania | major |
| zmiana wymaganej wersji frameworka | major |
- Regułę dla zmian samego wyglądu ustal raz i zapisz; wiele systemów traktuje je jako minor, inne jako major.

## Polityka wycofywania (deprecation)
1. Ogłoszenie: oznaczenie w kodzie (adnotacja `@deprecated`, ostrzeżenie w konsoli w trybie deweloperskim),
   w Storybooku, w changelogu i w tokenach (`$description`, `$deprecated` jeśli wspierane).
2. Następca i przewodnik migracji w tym samym wydaniu; **codemod** dla mechanicznych zmian (rename propsa, import).
3. Okres przejściowy: co najmniej 2 wydania minor lub ustalony czas (np. 6 miesięcy), podany z góry.
4. Usunięcie wyłącznie w major, z listą w notatce wydania i licznikiem pozostałych użyć (z metryk adopcji).
5. Wyjątek bezpieczeństwa lub dostępności: skrócony termin, ogłoszony z uzasadnieniem.

## Changelog
Jeden plik, wpisy per wydanie: Dodano, Zmieniono, Wycofano, Usunięto, Naprawiono, **Migracja** (kroki) i dla
tokenów — stara i nowa nazwa. Generowany z commitów (core-conventional-commits) i uzupełniany ręcznie o migrację.

## Współtworzenie
- Droga: zgłoszenie z dowodem potrzeby (zrzuty, linki do użyć) → przegląd zespołu systemu wg kryteriów →
  priorytet → projekt → implementacja → przegląd dostępności → wydanie. W GOV.UK Design System kryteria to
  „przydatne wielu zespołom” i „unikalne” (nie powiela istniejącego); na etapie propozycji wystarczą dowody potrzeb,
  bez gotowego projektu ani kodu.
- Modele: scentralizowany (zespół systemu robi wszystko), federacyjny (zespoły produktowe współtworzą, zespół
  systemu przegląda), hybrydowy. Przy ≥ 4 zespołach zwykle federacyjny; zależy od dojrzałości [założenie].
- Definicja ukończenia komponentu: kod, Figma, historyjki, dokumentacja, testy dostępności i zrzutowe, wpis
  w changelogu, przegląd projektowy i inżynierski.

## Zarządzanie
Rola właściciela systemu, przegląd tygodniowy zgłoszeń, kwartalna mapa drogi, kanał wsparcia z czasem
odpowiedzi, otwarty rejestr decyzji (ADR; docs-tech-writing). Konflikty rozstrzyga właściciel wg kryteriów, nie głośność.

## Metryki adopcji
| Metryka | Jak liczyć | Uwaga |
|---|---|---|
| pokrycie komponentami | użycia komponentów systemu / wszystkie elementy UI (analiza kodu) | najważniejsza |
| pokrycie tokenami | wartości z tokenów / wszystkie wartości kolorów i odstępów w CSS | linting |
| odłączenia i obejścia | instancje odłączone w Figmie; nadpisania stylów | sygnał brakującego wariantu |
| aktualność wersji | zespoły na wersji bieżącej lub poprzedniej / wszystkie | dla polityki wycofywania |
| czas do wdrożenia funkcji | z systemem vs bez [założenie, wymaga pomiaru początkowego] | |
Metryka bez decyzji, którą wspiera, jest dekoracją; ustal próg i właściciela, zanim zaczniesz zbierać.
