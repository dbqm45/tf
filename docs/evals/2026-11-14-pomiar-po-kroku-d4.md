# Pomiar po kroku D4: flaga funkcji, szablon specyfikacji na żądanie

Data: 2026-11-14. Powtórka pomiaru z `2026-11-13-pomiar-bazowy-e0.md` po kawałku D4 kroku D (tf#236): flaga funkcji na
zadanie z przełącznikiem `feature_flags.auto`, szablon `spec.md` zakładany dopiero przez pętlę, wzmocnione zdanie
o identyfikatorach kryteriów w testach. Ten sam zestaw: 3 historyjki × 5 powtórzeń,
`claude -p "/talos-story-run … --auto --budget 3" --model sonnet`, świeża kopia repozytorium testowego na każdy
przebieg. Fabryka: `ff2b08c` (wersja 9.32.0; trzy ostatnie przebiegi przy tym samym kodzie i commitach samych
dokumentów). Surowe wyniki: `2026-11-14-pomiar-po-kroku-d4.jsonl`; poprzedni pomiar:
`2026-11-13-pomiar-po-kroku-d3.jsonl`. Na sygnał człowieka; koszt 8,58 USD (suma `cost_usd` z pliku `.jsonl`)
i 0,63 USD przebiegu próbnego. Restart kontenera przerwał serię po 12 przebiegach; trzy brakujące (piąte powtórzenia)
uruchomiono osobno.

## Wynik

| Historyjka | Koszt śr. (było → jest) | Czas śr. | Akceptacja | Specyfikacja i ślad | Flaga |
|---|---|---|---|---|---|
| S1 limit dobowy (1 kawałek) | 0,59 → 0,60 USD | 102 → 116 s | 5/5 | 5/5: 3 kryteria, każde z testem, zapisem czerwonego testu i dowodem | 5/5 „bez flagi” z powodem |
| S2 abonament (2 kawałki) | 0,80 → 0,81 USD | 148 → 170 s | 5/5 | 5/5: 4 kryteria, każde z testem, zapisem czerwonego testu i dowodem | 5/5 „bez flagi” z powodem |
| S3 niejasna (oczekiwany STOP) | 0,29 → 0,30 USD | 33 → 38 s | STOP 5/5, kod bez zmian | `spec.md` nie powstaje (5/5) | nie dotyczy |

- Łącznie 8,58 USD wobec 8,40 USD poprzednio (+2%; sumy `cost_usd` z obu plików `.jsonl`). Czas dłuższy o 14–15%
  (średnie z tabeli wyżej) przy tym samym koszcie; przyczyny nie badano.
- Zadanie doszło do etapu `pr` w 10 z 10 przebiegów S1 i S2. Drzewo robocze czyste i `./verify.sh` zielony 15/15.

## Co potwierdził, a czego nie sprawdził

1. **Szablon specyfikacji na żądanie działa:** po STOP przed specyfikacją w katalogu zadania nie ma `spec.md`
   (S3, 5 z 5; poprzednio zostawał niewypełniony szablon).
2. **Identyfikatory kryteriów w testach — poprawa częściowa.** Dodatkowy commit z dopisaniem `AC-n` wystąpił
   w 2 z 5 przebiegów S2 (poprzednio w 4 z 5). Średnia liczba tur nie spadła (36 wobec 31), bo doszły kroki flagi.
3. **Reguła flagi była ćwiczona tylko w gałęzi „bez flagi”.** Repozytorium testowe nie ma mechanizmu flag, więc
   pętla za każdym razem zapisała powód jej braku (10 z 10). Zakładania flagi, testów w obu stanach i kontroli
   diffu pliku flag ten pomiar nie sprawdza.
4. **Odmowy uprawnień:** 2 (S2, ręczne uruchomienie CLI projektu `python3 -m parking.cli …`); przebiegi skończyły
   się poprawnie.

## Ograniczenia

- Pięć powtórzeń na historyjkę i jedno małe repozytorium w Pythonie: rozrzutu między przebiegami nie szacowano.
- Repozytorium testowe nie ma zdalnego źródła (push i PR niesprawdzane) ani pliku flag.
- Tryb `feature_flags.auto: false`, ochrona specyfikacji (D2) i przebieg cięcia pdi nie były mierzone.
