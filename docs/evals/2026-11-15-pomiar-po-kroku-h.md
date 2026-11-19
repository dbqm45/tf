# Pomiar po kroku H: koniec kawałka jednym poleceniem, panel recenzentów, praca bez nadzoru

Data: 2026-11-15. Powtórka pomiaru z `2026-11-14-pomiar-po-kroku-g.md` po zmianach kroku H:
- `tick` wymaga zapisu przeglądu zakresu (tf#259);
- ostrzeżenie o braku zdalnego repozytorium (tf#269);
- `run_state.py done` (tf#270);
- `tf work --once` (tf#271).

Układ jak poprzednio: `claude -p "/tf … --auto --budget 3" --model sonnet`, świeża kopia repozytorium testowego na
każdy przebieg i instalacja z nakładką pack-it. Fabryka: `9879a14` (plik wersji 10.21.0), uruchomiona z osobnej kopii
roboczej. Surowe wyniki: `2026-11-15-pomiar-po-kroku-h.jsonl`.

**Różnica układu:** w serii po kroku G przełącznik `loop.blocked_slices` był włączony, tu ma wartość domyślną
(wyłączony). Dotyczy to głównie S4.

Za zgodą właściciela z 2026-11-15. Koszt:
- seria 20 przebiegów: 11,84 USD;
- dwa przebiegi pilotażowe `tf work --once`: 0,37 i 0,64 USD.

Razem 12,85 USD (sumy `cost_usd`). Żaden przebieg nie zakończył się błędem.

## Wynik

| Historyjka | Koszt śr. (po G → teraz) | Tury śr. (po G → teraz) | Czas śr. (po G → teraz) | Akceptacja |
|---|---|---|---|---|
| S1 limit dobowy (1 kawałek) | 0,64 → 0,63 USD | 17,8 → 15,2 | 113 → 113 s | 5/5 |
| S2 abonament (2 kawałki) | 0,84 → 0,80 USD | 28,8 → 18,2 | 165 → 154 s | 5/5 |
| S3 niejasna (oczekiwany STOP) | 0,29 → 0,29 USD | 14,6 → 15,0 | 34 → 37 s | STOP 5/5 z kodem `pytanie` |
| S4 paragon i zgubiony bilet | 0,64 → 0,65 USD | 17,4 → 12,6 | 119 → 125 s | 5/5 część jasna; kwota zgadnięta 0/5 |

- **Liczba tur** spadła tam, gdzie są kawałki do zamknięcia: S1 o 15%, S2 o 37%, S4 o 28%. W S3 kawałków nie ma i liczba
  tur się nie zmieniła.
- **Koszt** się nie zmienił: 11,84 wobec 12,03 USD, w granicach rozrzutu między powtórzeniami (0,04–0,15 USD na
  historyjkę). Mniej tur nie dało niższego kosztu, bo koszt przebiegu niesie głównie odczyt z cache (po kroku G:
  97% tokenów po stronie wejścia), a każda tura czyta ten sam kontekst [wniosek z danych, bez osobnego pomiaru].
- **Czas** jest w granicach szumu. S2 jest krótszy o 11 s.
- Drzewo robocze czyste, a `./verify.sh` zielony w 20/20 przebiegach. Ślad kryteriów jest poprawny w 19/20
  przebiegach; w S4-r4 ślad nie przeszedł przy zatrzymaniu z pytaniem.

## Co widać z kroku H

- **Zapis przeglądu zakresu:** wynik zapisany w 15/15 przebiegach z kawałkami (po kroku G: 7/15). `tick` i `done`
  nie przepuszczają kawałka bez zapisu.
  - W S1-r4 przegląd znalazł ustalenie `[ważne]`. Pętla zapisała je (`finding`), dała `zakres fail` i zamknęła
    kawałek w drugiej rundzie.
- **`run_state.py done`:** treść commita kawałka w 19 z 20 kawałków to dokładnie `Kawałek K<n>: <wartość
  z planu>`, tak jak ją składa `done`. To mocna przesłanka, że pętla użyła polecenia [wniosek pośredni:
  dziennik przebiegu nie zapisuje wywołań narzędzi, więc wprost tego nie widać].
- **Zatrzymania przed PR:** kod `srodowisko` we wszystkich 13 przebiegach, które doszły do `pr` (dwa S4 zatrzymały
  się wcześniej na pytaniu). Po kroku G w tym samym
  miejscu dwa razy wypadło `uprawnienia`, bo pętla próbowała wypchnąć gałąź bez zdalnego repozytorium. Tym razem
  0 takich przypadków. Odmowy uprawnień: 2 (obie w S2-r2), po kroku G było 5.
- **Modele:** w tej serii nie użyto Haiku. Po kroku G Haiku działał w S1, S2 i S4. Przyczyny nie sprawdzałem
  [niezweryfikowane]; skład tur i kosztu mógł się przez to zmienić.

## Pilotaż `tf work --once`

To samo repozytorium testowe i historyjka S1. Przebieg:
1. Zadanie założone przez `run_report.py start --key PILOT-1` i oznaczone `tf task mode PILOT-1 auto`.
2. Uruchomienie: `TF_WORK_AGENT="claude --model sonnet --output-format json" tf work --once --budget <USD>`.

- **Przebieg 1 (fabryka z tf#271, 0,37 USD, 19 tur):** pętla zatrzymała się na przyjęciu, z poprawnym blokiem STOP.
  Były dwa powody:
  - worktree nie dostał katalogu przebiegu `.tf/runs/<KEY>`, który git ignoruje;
  - w trybie `dontAsk` agent nie mógł zapisać pliku, bo ustawienia fabryki nie dopuszczają Edit i Write.

  Agent nie próbował obejść odmowy przez Bash. Poprawka: tf#272 (kopiowanie katalogu przebiegu, domyślny tryb
  `acceptEdits`).
- **Przebieg 2 (z poprawką, 0,64 USD, 15 tur, 113 s, 0 odmów):** zadanie doszło do etapu `pr`. Akceptacja
  spełniona: 45 / 44 / 53 zł. Pętla zatrzymała się na braku zdalnego repozytorium, zgodnie z założeniem.
  - Koszt i liczba tur są jak w zwykłym przebiegu S1 (0,63 USD, 15,2 tury).
  - Zostało jedno zjawisko: w worktree brakowało `verify.sh` z `tf onboard`, który przy instalacji prywatnej jest
    poza gitem. Pętla sprawdziła testy przez `test_lock.py`. Poprawka jest w tym samym tf#272: pliki wskazane przez
    polecenie bramki jakości są kopiowane.
- Blokady z przeglądów bezpieczeństwa nie zadziałały ani razu, bo nie było czego blokować: pliki sterujące agentem
  były takie same, MCP wyłączony, zmienne środowiskowe ograniczone.

## Wnioski

- Koniec kawałka jednym poleceniem zmniejszył liczbę tur, ale nie koszt. Zostaje, bo kawałek nie przechodzi już bez
  zapisu przeglądu, a krótsza pętla jest czytelniejsza. Dalszego obniżania kosztu przez cięcie tur nie planuję:
  wpływa na nie głównie cache.
- `tf work --once` po poprawce z tf#272 doprowadza zadanie niskiego ryzyka do PR bez nadzoru, za tyle samo co
  przebieg nadzorowany. Następny krok to próba w prawdziwym repozytorium ze zdalnym źródłem i tokenem przekazanym
  przez `TF_WORK_ENV_ALLOW`. Wymaga zgody właściciela.
