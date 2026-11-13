# Pomiar po kroku D3: Talos ze specyfikacją i śladem kryteriów

Data: 2026-11-13. Powtórka pomiaru z `2026-11-13-pomiar-bazowy-e0.md` po kawałkach D1–D3 kroku D (tf#232–#235):
specyfikacja sprawdzana skryptem przed planem, ochrona specyfikacji, ślad kryterium → test → commit → dowód z zapisem
czerwonego testu. Ten sam zestaw: 3 historyjki × 5 powtórzeń, `claude -p "/talos-story-run … --auto --budget 3"
--model sonnet`, świeża kopia repozytorium testowego na każdy przebieg. Fabryka: `f5bdfaf` (wersja 9.31.0). Surowe
wyniki: `2026-11-13-pomiar-po-kroku-d3.jsonl`; poprzedni pomiar: `2026-11-13-pomiar-po-kroku-c.jsonl`. Za zgodą
człowieka; koszt 8,40 USD (suma `cost_usd` z pliku `.jsonl`) i 0,77 USD przebiegu próbnego.

## Wynik

| Historyjka | Koszt śr. (było → jest) | Czas śr. | Akceptacja | Specyfikacja | Ślad |
|---|---|---|---|---|---|
| S1 limit dobowy (1 kawałek) | 0,51 → 0,59 USD | 82 → 102 s | 5/5 | 5/5 bez błędów, po 3 kryteria | 5/5: każde kryterium ma test, zapis czerwonego testu i dowód |
| S2 abonament (2 kawałki) | 0,68 → 0,80 USD | 126 → 148 s | 5/5 | 5/5 bez błędów, po 4 kryteria | 5/5: każde kryterium ma test, zapis czerwonego testu i dowód |
| S3 niejasna (oczekiwany STOP) | 0,30 → 0,29 USD | 36 → 33 s | STOP 5/5, kod bez zmian | nie dotyczy | nie dotyczy |

- Łącznie 8,40 USD wobec 7,44 USD poprzednio (+13%; sumy `cost_usd` z obu plików `.jsonl`); historyjki z kodem są
  droższe o 16–18% i wolniejsze o 17–24% (średnie z tabeli wyżej).
- Zadanie doszło do etapu `pr` w 10 z 10 przebiegów S1 i S2 (poprzednio 9 z 10). Drzewo robocze czyste i
  `./verify.sh` zielony 15/15. Commit plików zadania zawsze na gałęzi historyjki (poprzednio raz na `main`).

## Co znalazł pomiar

1. **Identyfikatory kryteriów w testach dopisywane po fakcie** (S2, 4 z 5 przebiegów). Talos pisał testy bez `AC-n`,
   bramka śladu odrzucała etap `pr`, a on dopisywał identyfikatory osobnym commitem `test: tag … with AC ids`. Bramka
   działa, ale kosztuje to dodatkowe tury (średnio 31 wobec 14 poprzednio). Do poprawy w skillu: identyfikator
   w nazwie testu od pierwszej wersji testu.
2. **Odmowy uprawnień w jednym przebiegu** (S2, powtórzenie 5: sześć odmów — odczyt pliku i ręczne uruchomienie CLI).
   Przebieg i tak się zakończył poprawnie; przyczyny nie badano.
3. **STOP przed specyfikacją zostawia w repozytorium niewypełniony szablon `spec.md`** (S3, 5 z 5). To zgodne
   z projektem (szablon powstaje przy starcie), ale commit plików zadania niesie wtedy plik, który nie przechodzi
   sprawdzenia. Bez poprawki — do decyzji, czy szablon ma powstawać dopiero przy wypełnianiu.

## Ograniczenia

- Pięć powtórzeń na historyjkę i jedno małe repozytorium w Pythonie: rozrzutu między przebiegami nie szacowano,
  więc różnice kosztu rzędu kilkunastu procent są orientacyjne.
- Repozytorium testowe nie ma zdalnego źródła, więc push i otwarcie PR nie są sprawdzane.
- Ochrona specyfikacji (D2) nie była w pomiarze wyzwalana: żaden przebieg nie próbował zmienić `spec.md` w trakcie
  realizacji. Przebieg cięcia pdi (`--task`) nie był mierzony.
