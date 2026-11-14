# Zasady przeglądu PR

Szablon z tf (mode-pdi, pętla PR N2; wzór: `core-git-workflow/references/review-md.md`). Czyta go przegląd AI PR-ów
cięć (`pr_loop.py review`) i człowiek jako checklistę. Dopasuj zakres do produktu, a zmianę tego pliku
przejdź tak jak zmianę kodu — przez PR.

## Zakres
Przeglądaj zmiany kodu, testów i konfiguracji w diffie PR. Pomijaj: kod generowany, lockfile, zmiany samego
formatowania i wszystko, co sprawdza CI (lint, typy, pokrycie, skan bezpieczeństwa z `change-check.yml`).

## Przebiegi
1. **Błędy i logika** — warunki brzegowe, obsługa błędów, zgodność z testami i kryteriami cięcia.
2. **Bezpieczeństwo** — autoryzacja, walidacja wejścia, sekrety, dane osobowe w logach.
3. **Zgodność** — z planem cięcia (`docs/project/changes/CHG-n/plan.md`), wymaganiami (`requirements.md`) i
   decyzjami zmiany (`decisions.md`); to, co plan wyłączył („Poza zakresem”), nie jest brakiem.

## Waga ustaleń
- **Krytyczne** (`critical`) — blokuje scalenie (błąd danych, luka bezpieczeństwa, złamanie kontraktu).
- **Ważne** (`important`) — do poprawy w tym PR.
- **Drobne** (`minor`) — najwyżej 3 na PR; trafiają do listy w PR, bez poprawki.
Przy każdym ustaleniu: plik i linia, co jest nie tak, dlaczego, propozycja poprawki. Najwyżej 10 ustaleń.
Uwaga, która wymagałaby zmiany decyzji zmiany, ma odwołanie do niej (np. `CHG-4/D2`) — rozstrzyga człowiek.

## Czego nie robisz
Nie zatwierdzasz PR i nie oceniasz stylu, który pilnuje formatter. Pytania o wymagania kierujesz do człowieka.
