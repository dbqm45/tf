# Pomiar po kawałkach E2 i E3: waga zadania, tryby, kody zatrzymań

Data: 2026-11-14. Powtórka pomiaru z `2026-11-14-pomiar-po-kroku-e1.md` po trzech zmianach: czterech poprawkach skilla
z poprzedniego pomiaru (tf#239), wadze zadania (E2, tf#240) oraz trybach, zgodzie na plan i kodach zatrzymań (E3,
tf#241). Ten sam zestaw: 3 historyjki × 5 powtórzeń, `claude -p "/tf … --auto --budget 3" --model sonnet`, świeża
kopia repozytorium testowego na każdy przebieg, instalacja z nakładką pack-it. Fabryka: `744e1bb` (plik wersji 10.2.0),
uruchomiona z osobnej kopii roboczej, żeby późniejsze zmiany (E4) nie weszły do pomiaru. Surowe wyniki:
`2026-11-14-pomiar-po-kroku-e3.jsonl`; poprzedni pomiar: `2026-11-14-pomiar-po-kroku-e1.jsonl`. Za zgodą człowieka
z 2026-11-14; koszt 8,93 USD (suma `cost_usd` z pliku `.jsonl`) i 0,64 USD przebiegu próbnego.

Kawałek E4 (komunikaty zatrzymań) nie był mierzony — wszedł po serii.

## Wynik

| Historyjka | Koszt śr. (było → jest) | Czas śr. | Akceptacja | Specyfikacja i ślad | Flaga |
|---|---|---|---|---|---|
| S1 limit dobowy (1 kawałek) | 0,55 → 0,62 USD | 90 → 109 s | 5/5 | 5/5: 3 kryteria, każde z testem, zapisem czerwonego testu i dowodem | 5/5 „bez flagi” z powodem |
| S2 abonament (2 kawałki) | 0,80 → 0,85 USD | 143 → 160 s | 5/5 | 5/5: 4 kryteria, każde z testem, zapisem czerwonego testu i dowodem | 5/5 „bez flagi” z powodem |
| S3 niejasna (oczekiwany STOP) | 0,28 → 0,31 USD | 31 → 38 s | STOP 5/5, kod bez zmian | `spec.md` nie powstaje (5/5) | nie dotyczy |

- Łącznie 8,93 USD wobec 8,12 USD poprzednio (+10%; sumy `cost_usd` z obu plików `.jsonl`).
- **Czasów nie da się porównać:** w trakcie tej serii na tej samej maszynie biegły inne prace (testy i lint innego
  repozytorium), a poprzednia seria biegła sama. Wzrost czasu o 11–25% (średnie `wall_s`) może w całości z tego
  wynikać.
- Zadanie doszło do etapu `pr` w 10 z 10 przebiegów S1 i S2. Drzewo robocze czyste i `./verify.sh` zielony 15/15.
- Każde zadanie dostało wagę zwykłą i tryb Auto zapisany w `task.json` (15/15) — nowe bramki nie zatrzymały żadnego
  przebiegu.

## Poprawki z poprzedniego pomiaru

| Poprawka | Było | Jest |
|---|---|---|
| zadanie zakładane zawsze przed pytaniami (STOP zostawia ślad i raport) | 4/5 przebiegów S3 | 5/5 |
| przegląd zakresu zawsze przez `scope-reviewer` | 8/10 przebiegów S1 i S2 | 10/10 |
| bez poleceń złożonych | 2 odrzucone polecenia złożone | 0 (jedyna odmowa to `git push` bez zdalnego repozytorium) |
| identyfikator kryterium w teście od pierwszej wersji | dodatkowy commit w 3/5 przebiegów S2 | bez zmiany: 3/5 |

Rozpoznanie wejścia (`intake.py resolve`) wywołano w 15 z 15 przebiegów (poprzednio 13).

## Co wyszło do poprawy (poprawione w tym samym PR co raport)

1. **Zgadywanie kodu zatrzymania — 8 z 15 przebiegów.** Pętla wpisywała własny kod (`no-ac`, `no-remote`, `access`,
   `push`, `questions`), dostawała odmowę z listą i dopiero wtedy podawała właściwy — jedna zbędna tura. W pozostałych
   7 przebiegach najpierw czytała plik z listą kodów. Lista stała tylko w `references/`. Poprawka: jedenaście kodów
   jest wymienionych wprost w sekcji „Blok STOP” w SKILL.md.
2. **Identyfikator kryterium dopisywany osobnym commitem — nadal 3 z 5 przebiegów S2.** Samo zdanie w skillu nie
   pomogło. Poprawka w skrypcie: `run_state.py verify` ostrzega, gdy test kawałka nie ma `AC-n` (albo wśród plików
   kawałka nie ma testu), czyli zanim kawałek zostanie zapisany commitem.

Skuteczności obu poprawek ten pomiar nie potwierdza — weszły po serii.

## Skąd wzrost kosztu

Nie został rozłożony na przyczyny. Z transkryptów widać trzy rzeczy, które dokładają tur albo tekstu: odmowa
i powtórzenie przy zgadniętym kodzie zatrzymania (8 przebiegów), czytanie plików `references/` o trybach i o fladze
(odpowiednio w 7 i 6 przebiegach — policzone wyszukiwaniem w transkryptach, orientacyjnie) oraz dłuższe wyniki
poleceń (waga, tryb). Pierwszą usuwa poprawka 1; czy koszt wróci do 8,1 USD, pokaże następny pomiar.

## Ograniczenia

- Pięć powtórzeń na historyjkę i jedno małe repozytorium w Pythonie: rozrzutu między przebiegami nie szacowano.
- Repozytorium testowe nie ma zdalnego źródła, więc każdy przebieg S1 i S2 kończy się zatrzymaniem z kodem
  `srodowisko` (albo `uprawnienia`) zamiast otwarciem PR.
- Tryb zwykły (zgoda człowieka na plan), tryb Plan, waga lekka i pełna oraz wejście przez numer zgłoszenia nie były
  mierzone — każdy przebieg miał `--auto` i treść historyjki wprost. Pokrywają je testy skryptów.
- Komunikaty zatrzymań z E4 i ich pokazywanie człowiekowi nie były mierzone.
