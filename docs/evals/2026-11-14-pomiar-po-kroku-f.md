# Pomiar po kroku F: lista „Czeka na Ciebie”, etykiety przeglądu, limit rund, kawałek zablokowany

Data: 2026-11-14. Powtórka pomiaru z `2026-11-14-pomiar-po-kroku-e3.md` po wszystkim, co weszło od tamtej serii:
kody zatrzymań wprost w SKILL.md i ostrzeżenie `verify` (tf#243), komunikaty zatrzymań (E4), przydział kroków (E5),
cięcia pdi jako zadania (E6) i krok F (tf#247–#250). Ten sam zestaw: 3 historyjki × 5 powtórzeń,
`claude -p "/tf … --auto --budget 3" --model sonnet`, świeża kopia repozytorium testowego na każdy przebieg,
instalacja z nakładką pack-it. Fabryka: `f6565fb` (plik wersji 10.8.1) z jednym dodatkowym commitem `230b0ce`, który
zmienia tylko skrypt pomiarowy (opcja ustawień projektu), uruchomiona z osobnej kopii roboczej. **Przełącznik
`loop.blocked_slices` był włączony** w każdym przebiegu. Surowe wyniki: `2026-11-14-pomiar-po-kroku-f.jsonl`.

Za zgodą człowieka z 2026-11-14. Koszt: 9,00 USD za 15 ważnych przebiegów, 0,18 USD za 3 przebiegi przerwane błędem
dostępu, 0,81 USD za przebieg próbny i 0,07 USD za sprawdzenie dostępu — razem 10,06 USD (sumy `cost_usd`).

## Wynik

| Historyjka | Koszt śr. (E1 → E3 → teraz) | Czas śr. (E1 → E3 → teraz) | Akceptacja | Specyfikacja i ślad | Flaga |
|---|---|---|---|---|---|
| S1 limit dobowy (1 kawałek) | 0,55 → 0,62 → 0,61 USD | 90 → 109 → 114 s | 5/5 | 5/5: 3 kryteria, każde z testem, zapisem czerwonego testu i dowodem | 5/5 „bez flagi” z powodem |
| S2 abonament (2 kawałki) | 0,80 → 0,85 → 0,87 USD | 143 → 160 → 166 s | 5/5 | 5/5: 4 kryteria, każde z testem, zapisem czerwonego testu i dowodem | 5/5 „bez flagi” z powodem |
| S3 niejasna (oczekiwany STOP) | 0,28 → 0,31 → 0,32 USD | 31 → 38 → 42 s | STOP 5/5 z kodem `pytanie` | `spec.md` nie powstaje (5/5) | nie dotyczy |

- Łącznie 9,00 USD wobec 8,93 USD po E3 i 8,12 USD po E1 (sumy `cost_usd` z plików `.jsonl`).
- Zadanie doszło do etapu `pr` w 10 z 10 przebiegów S1 i S2. Drzewo robocze czyste i `./verify.sh` zielony 15/15.
  Odmów uprawnień: 0 w 15 przebiegach.
- Waga zwykła 15/15; tryb Auto zapisany w `task.json` 14/15 (w jednym przebiegu S3 zatrzymanie nastąpiło przed
  zapisem trybu).
- Ta seria biegła sama — w jej trakcie na maszynie były tylko drobne prace (edycja dwóch plików, przeszukanie
  transkryptów). Czasy są więc porównywalne z serią po E1, która też biegła sama: wzrost o 27% (S1), 16% (S2) i 36%
  (S3). Przyczyny nie rozłożyłem; przebieg ma dziś więcej poleceń skryptów niż po E1 (waga, tryb, komunikaty).

## Poprawki z poprzedniego pomiaru

| Poprawka | Po E3 | Teraz |
|---|---|---|
| kod zatrzymania podany bez zgadywania (lista w SKILL.md) | zgadywanie w 8/15 przebiegów | 0/15 |
| czytanie pliku z listą kodów (`references/tryby-i-zatrzymania.md`) | 7/15 | 0/15 |
| identyfikator kryterium w teście od pierwszej wersji (ostrzeżenie `verify`) | dodatkowy commit w 3/5 przebiegów S2 | 0/5 (trzy commity w każdym: dwa kawałki i pliki zadania) |
| przegląd zakresu przez `scope-reviewer` | 10/10 | 10/10 |
| komunikat zatrzymania ze skryptu (E4) | nie mierzone | wydrukowany w 15/15 przebiegów |

Mimo usunięcia zbędnej tury ze zgadywaniem kodu koszt nie wrócił do poziomu po E1 (8,1 USD) — został na poziomie
po E3. Czego dokładnie przybyło, nie ustaliłem.

## Co widać z kroku F

- **Etykiety przeglądu (F2) zadziałały w jednym przebiegu.** W S1-r1 recenzent oznaczył ustalenie jako `[ważne]`
  (usunięta asercja testu limitu przy końcu doby) i dał werdykt „SPOZA ZAKRESU”; pętla zrobiła drugą rundę i przegląd
  przeszedł (`run.json`: rundy `fail`, `pass`). W pozostałych 9 przebiegach S1 i S2 była jedna runda.
- **Limit rund (F2) nie został dotknięty** — żaden kawałek nie doszedł do trzeciej rundy.
- **Kawałek zablokowany (F3) nie został użyty ani razu.** Polecenie `block`: 0 wywołań; dopisek `po:` w planie: 0 z 10
  planów; `events.jsonl`: 0 plików. W tym zestawie nie ma pytania w trakcie kawałka: S1 ma jeden kawałek, w S2 drugi
  zależy od pierwszego, a w S3 pytanie dotyczy całego zadania (STOP przy przyjęciu — przeszedł poprawnie 5/5).
  Pomiar pokazuje więc tylko, że **włączony przełącznik niczego nie psuje**; nie pokazuje, czy blokowanie działa
  z modelem.

## Co wyszło do sprawdzenia

1. **Rozpoznanie wejścia pominięte w 3 z 15 przebiegów** (`intake.py resolve`; po E3 było 15/15). Przebiegi mimo to
   skończyły się poprawnie. Przyczyny nie znam.
2. **Wynik przeglądu zakresu niezapisany dla drugiego kawałka w 3 z 5 przebiegów S2** — `scope-reviewer` był
   wywołany, ale w `run.json` etap `zakres` został bez stanu. Podgląd pokazuje wtedy przegląd jako nieuruchomiony.
3. **Błąd dostępu w trakcie serii:** piąte powtórzenie wszystkich trzech historyjek zakończyło się błędem 403
   („organization has disabled Claude subscription access for Claude Code”) po 5–9 sekundach. To nie błąd fabryki;
   przy ponownym sprawdzeniu po zakończeniu serii dostęp działał i te trzy przebiegi powtórzyłem. Wiersze nieudane są w pliku `.jsonl`
   z `is_error: true`; wyniki wyżej liczą tylko 15 ważnych.

## Wniosek

- Zmiany od E3 nie pogorszyły wyniku: akceptacja 10/10, STOP 5/5, koszt bez zmian (+0,8%).
- Trzy poprawki z poprzedniego pomiaru są potwierdzone liczbami (tabela wyżej).
- Przełącznik `loop.blocked_slices` zostaje **domyślnie wyłączony**: ten zestaw nie sprawdza tego, do czego służy.
  Żeby ocenić F3, potrzebna jest historyjka z pytaniem w trakcie jednego kawałka i z kawałkiem od niego niezależnym
  — to nowy element zestawu i nowy płatny pomiar (osobna zgoda).

## Ograniczenia

- Pięć powtórzeń na historyjkę i jedno małe repozytorium w Pythonie: rozrzutu między przebiegami nie szacowano.
- Jedna seria z włączonym przełącznikiem: wpływu F3 nie da się oddzielić od wcześniejszych zmian (E4, E5, E6, F1,
  F2); serii z wyłączonym przełącznikiem na tym samym stanie fabryki nie było.
- Repozytorium testowe nie ma zdalnego źródła, więc każdy przebieg S1 i S2 kończy się zatrzymaniem z kodem
  `srodowisko` zamiast otwarciem PR.
- Tryb zwykły, tryb Plan, waga lekka i pełna, wejście przez numer zgłoszenia, cięcia pdi i lista „Czeka na Ciebie”
  nie były mierzone — pokrywają je testy skryptów.
- Liczby z transkryptów (rozpoznanie wejścia, czytane pliki, etykiety) policzone wyszukiwaniem tekstu, orientacyjnie.
