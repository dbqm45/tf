# Pomiar bazowy osi fabryki (E0) — 2026-11-13

Pliki: `docs/evals/2026-11-13-pomiar-bazowy-e0.jsonl` (surowe wyniki, 16 wierszy: 1 próba i 15 przebiegów),
`docs/evals/2026-11-13-pomiar-bazowy-e0/` (repozytorium testowe, historyjki, skrypt pomiaru).

Cel: punkt odniesienia dla planu `docs/plans/2026-11-12-plan-zmian-os-fabryki.md` (krok A). Mierzymy drogę od
instalacji fabryki do gałęzi z zielonymi testami na stanie `main` po krokach A i B (commit `06dc908`,
rdzeń 9.22.0). Po kroku E i na końcu planu ten sam pomiar powtarzamy i porównujemy.

## Wniosek

Na małym repozytorium fabryka robi dobrze opisane zadanie bez nadzoru w ok. 1–2 minuty za ok. 0,5 USD i poprawnie
odmawia zadania bez kryteriów. Do gałęzi z zielonymi testami wystarczają trzy polecenia człowieka. Słabym punktem
są pytania o zgodę: w każdym przebiegu fabryka 2–3 razy prosiła o zgodę na własne czynności, a do PR nie doszła.

## Jak mierzono

- **Repozytorium:** mała aplikacja w Pythonie (opłata za parking), 7 testów, bez zależności, bez lintu i typów.
- **Droga:** świeża kopia → `install.py --packs pack-it,mode-talos` → `tf onboard --yes --verify` → Talos bez nadzoru
  (`claude -p "/talos-story-run <treść historyjki> --auto --budget 3"`, tryb `acceptEdits`, model Sonnet).
- **Historyjki:** S1 lekka (zmiana limitu dobowego, 3 kryteria), S2 zwykła (zniżka abonamentowa, 4 kryteria, zmiana
  w dwóch plikach), S3 celowo niejasna (jedno zdanie bez kryteriów — poprawny wynik to zatrzymanie z pytaniami).
- **Powtórzenia:** 5 na historyjkę, kolejno, każde na świeżej kopii.
- **Ocena:** `./verify.sh` po przebiegu oraz sprawdzenia akceptacji ukryte przed agentem (w skrypcie pomiaru, nie
  w repozytorium). Koszt to `total_cost_usd` z wyniku `claude -p` — równowartość wg cennika API.

## Wyniki

| Historyjka | Zaliczone | Koszt USD: mediana (zakres) | Czas s: mediana (zakres) | Tury (zakres) | Odmowy uprawnień: mediana (zakres) | Commity |
|---|---|---|---|---|---|---|
| S1 lekka | 5/5 | 0,45 (0,44–0,51) | 74 (66–100) | 7–14 | 3 (2–3) | 1 w każdym |
| S2 zwykła | 5/5 | 0,60 (0,55–0,61) | 125 (109–134) | 8–47 | 2 (2–13) | 2 w każdym |
| S3 niejasna | 5/5 zatrzymań | 0,26 (0,26–0,32) | 28 (24–45) | 1–13 | 2 (0–3) | 0 w każdym |

„Zaliczone” dla S1 i S2 oznacza: ukryte sprawdzenia akceptacji przechodzą, `./verify.sh` zielone, drzewo robocze
czyste. Dla S3: brak zmian w kodzie i komunikat STOP z pytaniami do człowieka.

Łączny koszt serii: 6,65 USD; z próbą 7,06 USD. Instalacja trwała ok. 2 s, a `tf onboard` poniżej 1 s (mediany
z `install_s` i `onboard_s` w pliku wyników); po `tf onboard` drzewo robocze było czyste w 15/15 przebiegach.

### Polecenia człowieka

Do gałęzi z zielonymi testami: 3 polecenia — `tf` (instalacja), `tf onboard --yes --verify`, `claude` z treścią
historyjki. Cel z dokumentu osi (najwyżej 3 polecenia do pierwszego PR) nie jest jeszcze spełniony, bo PR wymaga
czwartego kroku: zdalnego repozytorium i zgody na `git push`. Stanowisko pomiarowe nie ma zdalnego repozytorium,
więc każdy przebieg S1 i S2 kończył się komunikatem STOP na etapie PR.

### Skąd odmowy uprawnień

W trybie bez nadzoru odmowa oznacza pominięty krok; w sesji z człowiekiem ta sama sytuacja to pytanie o zgodę.
Razem 44 odmowy w 15 przebiegach (pole `permission_denials` w wynikach `claude -p`):

| Przyczyna | Liczba | Przykład |
|---|---|---|
| polecenie złożone z kilku czynności w jednej linii | 25 | `sed -i … plan.md; python3 …/run_state.py step …` |
| `risk_triage.py` nie jest na liście dozwolonych poleceń | 17 | `python3 .tf/factory/risk_triage.py --md` |
| sprawdzenie zdalnego repozytorium | 1 | `git remote -v; gh auth status` |
| inne pojedyncze polecenie | 1 | `python3 -m parking.cli 180 --subscriber` |

Skutek drugiej przyczyny: ocena ryzyka zmian nie wykonała się w żadnym przebiegu S1 i S2, a Talos zapisał to
w raporcie jako krok niewykonany.

### Odłożone sprawy

W S2 Talos zapisał w `parked.md` od 0 do 3 spraw spoza kryteriów (np. jak liczyć pierwszą godzinę przy postoju
wielodobowym) zamiast rozszerzać kod. W S1 i S3 nic nie odłożył.

## Pasmo szumu

Zmianę w kolejnym pomiarze traktujemy jako rzeczywistą dopiero poza zakresami z tabeli: dla kosztu poniżej 0,44
albo powyżej 0,51 USD w S1 i poza 0,55–0,61 USD w S2; dla czasu poza 66–100 s w S1 i 109–134 s w S2. Liczba tur
i odmów ma duży rozrzut (w S2 od 8 do 47 tur i od 2 do 13 odmów), więc pojedynczy przebieg nic o nich nie mówi.

## Czego ten pomiar nie pokazuje

- **Małe repozytorium.** Kilka plików bez zależności; koszt i czas na prawdziwym projekcie będą wyższe.
- **Brak lintu i typów.** `verify.sh` uruchamiał tu same testy.
- **Bez PR i wdrożenia.** Droga kończy się na commicie.
- **Jeden model.** Wszystkie przebiegi na Sonnecie, z opcją `--auto`.
- **Kolejność test → kod.** Raporty przebiegów deklarują czerwony test przed kodem, ale skrypt pomiaru tego nie
  sprawdza [niezweryfikowane].
- **Test laika.** Wymaga osoby, która nie zna fabryki; nie został wykonany.

## Co z tego wynika dla planu

1. Dopisać `risk_triage.py` do dozwolonych poleceń trybu Talos — mała poprawka, usuwa 17 z 44 odmów.
2. W skillu Talosa zastąpić polecenia złożone pojedynczymi wywołaniami skryptu stanu — to 25 z 44 odmów; pasuje do
   pozycji 4 planu (skrypt stanu zadania).
3. Etap PR potrzebuje jasnego wejścia: zdalne repozytorium i zgoda na wypchnięcie (pozycje 9 i 17 planu).
4. Cel „najwyżej 3 polecenia do PR” mierzyć ponownie po kroku E.

## Jak powtórzyć

Płatne — tylko za zgodą człowieka. `LIMIT=15 docs/evals/2026-11-13-pomiar-bazowy-e0/batch.sh` uruchamia całą serię
i zatrzymuje się po przekroczeniu limitu w USD; pojedynczy przebieg:
`python3 docs/evals/2026-11-13-pomiar-bazowy-e0/e0_run.py S1 1`.
