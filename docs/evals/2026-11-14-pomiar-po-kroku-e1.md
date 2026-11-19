# Pomiar po kawałkach E0 i E1: pętla w rdzeniu jako `/tf`, rozpoznanie wejścia

Data: 2026-11-14. Powtórka pomiaru z `2026-11-14-pomiar-po-kroku-d4.md` po dwóch kawałkach kroku E naraz: E0 (tf#237 —
pętla przeniesiona do rdzenia jako `/tf`) i E1 (tf#238 — rozpoznanie wejścia skryptem `intake.py`, `/tf` wywoływane
także przez model, źródło w `ticket.md`, `SKILL.md` skrócony z 24 749 do 14 838 znaków ze szczegółami w `references/`).
Ten sam zestaw: 3 historyjki × 5 powtórzeń, `claude -p "/tf … --auto --budget 3" --model sonnet`, świeża kopia
repozytorium testowego na każdy przebieg, instalacja z nakładką pack-it. Fabryka: `2ed9d98` (plik wersji 10.0.0;
wydanie 10.1.0 powstało z tego samego kodu po serii). Surowe wyniki: `2026-11-14-pomiar-po-kroku-e1.jsonl`; poprzedni
pomiar: `2026-11-14-pomiar-po-kroku-d4.jsonl`. Za zgodą człowieka z 2026-11-14; koszt 8,12 USD (suma `cost_usd`
z pliku `.jsonl`) i 0,55 USD przebiegu próbnego.

Pomiar nie rozdziela E0 od E1: obie zmiany weszły przed serią, więc różnicy nie da się przypisać jednej z nich.

## Wynik

| Historyjka | Koszt śr. (było → jest) | Czas śr. | Akceptacja | Specyfikacja i ślad | Flaga |
|---|---|---|---|---|---|
| S1 limit dobowy (1 kawałek) | 0,60 → 0,55 USD | 116 → 90 s | 5/5 | 5/5: 3 kryteria, każde z testem, zapisem czerwonego testu i dowodem | 5/5 „bez flagi” z powodem |
| S2 abonament (2 kawałki) | 0,81 → 0,80 USD | 170 → 143 s | 5/5 | 5/5: 4 kryteria, każde z testem, zapisem czerwonego testu i dowodem | 5/5 „bez flagi” z powodem |
| S3 niejasna (oczekiwany STOP) | 0,30 → 0,28 USD | 38 → 31 s | STOP 5/5, kod bez zmian | `spec.md` nie powstaje (5/5) | nie dotyczy |

- Łącznie 8,12 USD wobec 8,58 USD poprzednio (−5%; sumy `cost_usd` z obu plików `.jsonl`). Czas krótszy o 16–23%
  (średnie `wall_s` z tabeli); przyczyny nie badano.
- Zadanie doszło do etapu `pr` w 10 z 10 przebiegów S1 i S2. Drzewo robocze czyste i `./verify.sh` zielony 15/15.

## Co potwierdził

1. **Przeniesienie pętli i nowe wejście nie pogorszyły wyniku:** akceptacja 10/10, STOP 5/5, specyfikacja i ślad
   kryteriów 10/10 — jak w pomiarze po D4.
2. **Rozpoznanie wejścia działa bez nadzoru:** `intake.py resolve` wywołano w 13 z 15 przebiegów (transkrypty
   przebiegów); w dwóch pozostałych pętla założyła zadanie od razu. `ticket.md` ma linię `Źródło: wklejone w rozmowie`
   w 14 z 14 założonych zadań.

## Co wyszło do poprawy (poprawione w tym samym PR co raport)

1. **STOP przed założeniem zadania — 1 z 5 przebiegów S3.** Pętla zadała pytania o kryteria, zanim wywołała
   `run_report.py start`: w repozytorium nie został żaden ślad (brak `ticket.md` i raportu kosztu). Poprzednio zadanie
   powstawało 5/5. Poprawka w skillu: gdy treść jest, zadanie zakłada się zawsze, a pytania o kryteria należą do
   etapu przyjęcia.
2. **Przegląd zakresu pominięty — 2 z 10 przebiegów S1 i S2** (poprzednio 0 z 10). Sesja główna uznała, że mały diff
   może przejrzeć sama, bez agenta `scope-reviewer`. Poprawka: przegląd zawsze robi `scope-reviewer`.
3. **Odmowy uprawnień: 5 wobec 2.** Trzy to `git push` w repozytorium testowym bez zdalnego źródła, dwie to
   polecenia złożone (łączenie poleceń przez `;`). Poprawka: reguła „jedna czynność na polecenie” znów mówi wprost,
   czego nie łączyć. Odmowy `git push` zostają — to cecha repozytorium testowego.
4. **Dodatkowy commit z dopisaniem `AC-n` do testów — 3 z 5 przebiegów S2** (poprzednio 2 z 5). Przy skracaniu
   skilla wypadło zdanie, że dopisywanie identyfikatorów po fakcie kosztuje commit; wróciło.

Skuteczności tych czterech poprawek pomiar nie potwierdza — weszły po serii. Sprawdzi je następny pomiar
(po kawałku E3 według planu kroku E).

## Obserwacje bez zmian w kodzie

- Stan pętli kawałka (`run_state.py step`) pętla zgłaszała rzadko — tak samo jak w poprzednim pomiarze (0–3 różne
  zgłoszenia na przebieg wobec 1–5; policzone wyszukiwaniem w transkryptach, więc orientacyjnie). Podgląd na żywo
  pokazuje przez to etapy przebiegu, a rundy kawałka tylko częściowo. Temat należy do pozycji „zdarzenia” planu osi.
- Agent `scout` nie był używany w żadnym przebiegu S1 i S2 ani teraz, ani poprzednio (repozytorium testowe jest małe).

## Ograniczenia

- Pięć powtórzeń na historyjkę i jedno małe repozytorium w Pythonie: rozrzutu między przebiegami nie szacowano,
  więc różnice 1–2 przebiegów na 5 mogą być przypadkowe.
- Repozytorium testowe nie ma zdalnego źródła (push i PR niesprawdzane) ani pliku flag.
- Wejście przez numer zgłoszenia, adres, tracker (MCP) i klucz cięcia pdi nie było mierzone — każdy przebieg
  dostawał treść historyjki wprost. Pokrywają je testy skryptu `intake.py`, nie przebieg na modelu.
- Wywołanie pętli zwykłym zdaniem (bez `/tf`) i scenariusze „nie włączaj się” nie były ćwiczone na modelu.
