# Krok H: bez nadzoru i higiena — plan realizacji

Data: 2026-11-14. Krok H planu zmian (`docs/plans/2026-11-12-plan-zmian-os-fabryki.md`, pozycje 19, 20 i 21; do
tego pozycja 29 i decyzje D10, D11, D13 z 2026-11-14). Efekt dla człowieka: **wyniki pomiarów i kosztów da się
porównać między wersjami fabryki, konfiguracja nie odwołuje się do starych modeli, a reguł w instrukcjach jest
tyle, ile trzeba.**

Kolejność: H20 → H21 → H29 → H11 → H19. Każdy kawałek to osobny PR. H19 (praca bez nadzoru) idzie ostatni, bo
dokłada autonomii, a pomiar po kroku G dopiero pokaże, jak pętla zachowuje się z nowymi poleceniami.

## Kawałki

| # | Kawałek | Co powstaje |
|---|---|---|
| H20 | odcisk harnessu, pasmo szumu, nazwy modeli (poz. 20) | niżej, szczegółowo |
| H21 | nadmiar reguł (poz. 21) | przegląd `CLAUDE.md` i skilli rdzenia; pięć kontroli w `tf doctor` — plan po H20 |
| H29 | ostrzeżenie po aktualizacji fabryki (poz. 29, D13) | `tf doctor` i `tf metrics` ostrzegają przy wzroście cofnięć i blokad hooków po aktualizacji i podają polecenie powrotu; fabryka sama się nie cofa — plan po H21 |
| H11 | panel recenzentów przy wadze pełnej (D11) | przegląd w kilku osobnych kontekstach uruchamiany skryptem, tylko przy wadze pełnej — plan po H29 |
| H19 | `tf work --once` (poz. 19) | praca bez nadzoru w osobnym worktree z limitem wydatku; pilotaż na zadaniach niskiego ryzyka — plan po pomiarze |

## H20 — plan realizacji (zapisany przed kodem)

**a) Nazwy i ceny modeli w jednym miejscu, sprawdzane w CI.**
- `core/factory/config.yaml` dostaje `models_current` (alias → identyfikator: `fable`, `opus`, `sonnet`, `haiku`),
  `models_legacy` (identyfikatory starsze, ale nadal dozwolone, np. `claude-haiku-4-5` w cenniku) i `models_checked`
  (data sprawdzenia). Źródło: skill `claude-api`, tabela modeli w stanie z 2026-11-03.
- Poprawki znalezione przy tym sprawdzeniu: `claude-fable-5-1` → `claude-fable-5-2` w `managed_agents.models`
  i w `target_managed.py`; ceny Fable 10/50 → 8/40 USD (odczyt cache 0,20); odczyt cache Sonneta 0,20 → 0,10 USD.
  Ceny zapisu cache (5 min) liczone jako 1,25 × wejście, jak dla pozostałych modeli [założenie].
- Nowy skrypt silnika `core/factory/model_check.py`: każdy identyfikator `claude-…` w konfiguracji fabryki (rdzeń
  i nadpisania projektu) i w kodzie silnika musi być w `models_current` albo `models_legacy`; aliasy w
  `managed_agents.models` muszą wskazywać na `models_current`. Data sprawdzenia starsza niż 90 dni to ostrzeżenie
  (nie błąd — CI nie może się zaczerwienić od samego upływu czasu). `tf doctor` pokazuje wynik; test repozytorium
  uruchamia go na rdzeniu.
- Testy: `core/tests/test_model_check.py` — nieznany identyfikator, alias na starszy model, stara data, czysta
  konfiguracja rdzenia.

**b) Odcisk harnessu w logu zużycia.** `log_usage.py` dopisuje do każdego wpisu `usage.jsonl` pole `harness`:
wersja Claude Code (z pola `version` transkryptu), wersja fabryki i nakładki (z `.claude/factory-manifest.json`) oraz
skrót z sum kontrolnych zainstalowanych plików (12 znaków SHA-256 z pola `files` manifestu). Bez manifestu pole ma
tylko to, co da się ustalić. Test: `test_cost.py` — wpis ma odcisk; zmiana jednego pliku w manifeście zmienia skrót.
`cost_report.py` i `tf metrics` nie zmieniają się w tym kawałku.

**c) Pasmo szumu w raportach ewaluacji.** `run_skill_evals.py` (z `--repeats`) liczy dla każdego ramienia odsetek
zaliczeń osobno w każdym powtórzeniu; pasmo szumu to rozpiętość tych odsetków. Raport pokazuje pasmo w protokole,
a w tabelach „Luka” i „Wkład skilla” oznacza różnicę mieszczącą się w paśmie jako „w paśmie szumu”. Mniej niż
5 powtórzeń → dopisek, że pasmo jest orientacyjne. Testy: `test_skill_evals.py`.

Kolejność: testy (czerwone) → a → b → c → przewodniki (`PRZEWODNIK.md`, `PUBLIC_API.md`) → pełne sprawdzenie.
Pełne sprawdzenie dopiero po zakończeniu serii pomiarowej po kroku G (żeby nie zakłócać jej czasów).

## H21 — plan realizacji (zapisany przed kodem)

- **Nieaktualne wpisy w plikach instrukcji:** `instructions_lint.py` dostaje kontrolę `nieaktualne`: ścieżki
  w `kodzie` (z `/`), których w repozytorium nie ma, `npm run <skrypt>` bez skryptu w `package.json`, `make <cel>`
  bez celu w `Makefile`. Werdykt UWAGA, nie BŁĄD. Pomijane: blok fabryki (`<!-- team-factory:begin/end -->`, wspólny
  dla wszystkich projektów), linie z zakazem („nie czytaj `dist/`” — taki katalog może nie istnieć), katalogi fabryki
  tworzone na żądanie (`docs/project/`, `.tf/`, `.claude/`), same nazwy plików, wzorce, adresy i opcje.
  Sprawdzone na pięciu repozytoriach tej sesji (tf, pdi, ci_for_sdlc i dwie starsze instalacje fabryki): po
  zawężeniu heurystyki zero fałszywych alarmów.
- **`tf doctor`** pokazuje kartę plików instrukcji projektu w jednej linii (kontrole z uwagami i polecenie
  szczegółów) — informacja, kod wyjścia bez zmian. To wpina pięć kontroli karty (`core-agent-instructions`) w doctora.
- **Przegląd treści rdzenia pod kątem nadmiaru reguł** (S6) — bez usuwania reguł bez pomiaru („reguła zarabia na
  miejsce pomiarem”, sekcja 1 dokumentu osi). Na tym etapie tylko karta kontroli dla `core/CLAUDE.md`; decyzje
  o skróceniu wymagają przebiegów bez reguły, więc wchodzą do kolejnego pomiaru.
- Testy: `test_instructions_lint.py` (nieaktualne, aktualne, `tf doctor`); scenariusz ewaluacji
  `nieaktualne-wpisy-po-refaktorze` przed zmianą treści skilla.

## Poprawki z pomiaru po kroku G (`docs/evals/2026-11-14-pomiar-po-kroku-g.md`)

- **`tick` wymaga zaliczonego przeglądu zakresu.** Ostatnia runda kawałka musi mieć zapis `zakres pass`; bez zapisu,
  z przeglądem w toku albo po `zakres fail` skrypt odmawia (kod 2) i podaje dokładne polecenie (zapis wyniku albo
  nowa runda). Przebiegi bez zadania (stary układ) bez zmian. Testy: `test_review_rounds.py` PR-10…PR-14; testy,
  które odhaczały kawałek bez przeglądu, zapisują teraz jego wynik (zmiana kontraktu, nie osłabienie testów).
- **Komunikat po zapisie ustalenia** nie każe od razu podawać kontroli: każe wycofać kod i zrobić nową rundę;
  kontrolę dopisuje się przy zamknięciu zadania.
- Scenariusz `przeglad-zakresu-etykiety` sprawdza też zapis wyniku przeglądu (przed zmianą treści skilla).
- Zmiana zachowania pętli: jedno polecenie więcej na kawałek tam, gdzie pętla je pomijała. Niezmierzone na
  przebiegach z modelem.

## H29 — plan realizacji (zapisany przed kodem; decyzja D13: tylko ostrzegać)

Mechanizm powrotu już jest: przed każdą aktualizacją `update.py` robi kopię w `.tf/backup/<data>-v<wersja>/`
(`backup.json`), a `update.py --rollback` ją przywraca. Brakuje sygnału, że po aktualizacji coś się pogorszyło.

- **Dziennik blokad hooków.** `hook_errors.py` dostaje `record_block(hook, decyzja)`: wpis w
  `.tf/logs/hook-blocks.jsonl` (czas, hook, `deny` albo `ask`), bez treści polecenia ani pliku. Wołają go hooki,
  które blokują: `tdd_guard`, `guard_paths`, `guard_bash`, `cleanroom_guard`, `scan_secrets`.
- **`metrics.py --after-update [--json]`:** ostatnia kopia z `.tf/backup/` wyznacza chwilę aktualizacji i wersję
  sprzed niej. Porównuje okno po aktualizacji (do 14 dni) z oknem tej samej długości przed nią:
  - odsetek cofnięć z gita — ostrzeżenie przy wzroście o co najmniej 15 punktów i co najmniej 5 rozstrzygniętych
    zmianach w obu oknach;
  - blokady hooków na dzień — ostrzeżenie przy co najmniej 5 blokadach po i co najmniej dwukrotnym wzroście;
  - błędy hooków — ostrzeżenie przy co najmniej 3 po i ponad dwukrotnym wzroście.
  Mniej danych → „za mało danych”, bez ostrzeżenia. Ostrzeżenie podaje gotowe polecenie powrotu
  (`python3 .tf/factory/update.py --rollback`) i mówi wprost, że fabryka sama się nie cofa.
- **`tf doctor`** pokazuje ostrzeżenie (informacja, kod wyjścia bez zmian); **`tf metrics`** — sekcję w raporcie.
- Testy: `core/tests/test_update_health.py` (repozytorium git z datami commitów, kopia z `.tf/backup/`,
  dzienniki hooków); `test_cost.py` albo testy hooków — wpis blokady bez treści.
- Pliki: `core/hooks/hook_errors.py`, pięć hooków, `core/factory/metrics.py`, `core/factory/tf.py`, przewodniki.

## H11 — plan realizacji (zapisany przed kodem; decyzja D11: panel jako przepływ skryptu, tylko waga pełna)

Dziś przy wadze pełnej przegląd `security-reviewer` jest obowiązkowy tylko w treści `references/waga.md`.
Pomiar po kroku G pokazał, że kroki opisane prozą pętla pomija (zapis przeglądu zakresu: 7/15), więc panel pilnuje
skrypt.

- **Panel:** `security-reviewer` (istnieje) i nowy `spec-reviewer` — w świeżym kontekście sprawdza diff reguła po
  regule: każde kryterium `AC-n` (spełnione / niespełnione / nie da się sprawdzić, z dowodem plik:linia i testem) oraz
  każdą regułę „Bez zmian” ze `spec.md`. Tylko odczyt. `architect` zostaje jak dziś (przy decyzji trudnej do
  odwrócenia), bez wymogu skryptu.
- **Zapis werdyktu:** `tf task review <KEY> <recenzent> pass|fail [--note "…"]` → `reviews` w `task.json` (werdykt,
  commit `HEAD`, czas, uwaga). Pętla woła to przez `run_state.py panel <katalog> --record <recenzent> pass|fail`.
- **Bramka:** etap `pr` (i dalsze) zadania o wadze pełnej wymaga werdyktu `pass` od obu recenzentów, wydanego dla
  bieżącego commita — zmiana kodu po przeglądzie wymaga przeglądu od nowa. Odmowa podaje polecenie panelu.
  Waga lekka i zwykła bez zmian. Cięcia pdi o wadze pełnej też przechodzą panel (przegląd bezpieczeństwa i tak
  zostawał).
- **`run_state.py panel <katalog>`** drukuje skład panelu z gotowym zleceniem dla każdego recenzenta (co dostaje,
  w jakim formacie odpowiada) i polecenie zapisu werdyktu; pokazuje też werdykty już zapisane.
- Treść: `references/waga.md` punkt 2 (bez zmiany `SKILL.md` — jest na granicy limitu; odmowa etapu `pr` mówi pętli,
  co zrobić). Scenariusz ewaluacji przed zmianą treści.
- Testy: `core/tests/test_panel.py`; agent `spec-reviewer` w `config.yaml` i w narzędziach agenta `tf`.
- Koszt: dwa przeglądy w osobnych kontekstach przy zadaniu o wadze pełnej (rzadkim). Niezmierzone na modelu.

## Koniec kawałka jednym poleceniem — plan realizacji (zapisany przed kodem; zgoda człowieka 2026-11-15)

Po zaliczonym przeglądzie zakresu pętla robi dziś trzy do czterech wywołań: zapis wyniku przeglądu (`step … zakres
pass`), `git add` i `git commit` z treścią i stopkami, `tick` i często `next`. Każde to osobna tura modelu
z pełnym kontekstem. Pomiar po kroku G: zapis przeglądu był pomijany (7/15). Jedno polecenie zmniejsza liczbę tur
i nie da się w nim pominąć zapisu. Szacunek oszczędności: około 2 tury na kawałek [szacunek, do sprawdzenia
w następnym płatnym pomiarze].

- **`run_state.py done <katalog> K<n> --message "<typ>(<zakres>): <opis>"`** po kolei:
  1. sprawdza aktualny dowód kawałka (`verify`); bez niego odmawia i niczego nie zapisuje;
  2. sprawdza format tytułu commita (Conventional Commits); zły → odmowa przed zapisem;
  3. zapisuje `zakres pass` dla bieżącej rundy kawałka (ostatnia runda w `run.json`, bez rundy — R1);
  4. robi commit **tylko plików z dowodu** (po nazwie): tytuł z `--message`, w treści `Kawałek K<n>: <wartość
     z planu>` (gdy go nie ma), stopki `Change: <TSK>` (przebieg cięcia) i `Flag: <klucz>` (flaga zadania albo
     cięcia), gdy ich nie ma; pliki już zatwierdzone → bez commita, z informacją;
  5. odhacza kawałek (`tick`) i drukuje `Dalej: …` jak `next`.
  Odmowa commita (hook `commit-msg`, brak repozytorium) → kod ≠ 0, kawałek nieodhaczony, wyjście gita w odpowiedzi.
- Przegląd z ustaleniem **ważnym** zostaje jak dziś (`finding`, `step … zakres fail`, nowa runda); `tick` i `step`
  zostają dla zgodności.
- Treść: `SKILL.md` krok 4–5 — `done` zamiast opisu commita i `tick` (limit 15000 znaków: zamiana, nie dopisek).
  Scenariusz ewaluacji przed zmianą treści.
- Testy: `core/tests/test_slice_done.py` (repozytorium git, przebieg z zadaniem, dowód, flaga, druga runda,
  ponowienie, plik spoza kawałka zostaje niezatwierdzony).

## H19 — plan realizacji (zapisany przed kodem; zgoda człowieka 2026-11-15, bez płatnych uruchomień do czasu pomiaru)

`tf work --once` bierze jedno zadanie, które człowiek oznaczył do pracy bez nadzoru, i prowadzi je pętlą `/tf`
w osobnym worktree, z twardym limitem wydatku. Nie scala, nie wdraża; wynik to gałąź z PR albo blok STOP.

- **Które zadanie:** tylko zadanie z trybem `auto` (`tf task mode <KEY> auto` — decyzja człowieka jest zgodą na
  pracę bez nadzoru), otwarte, bez blokady i bez wagi `pelna` (pilotaż na niskim ryzyku: waga pełna wymaga panelu
  i człowieka). Kolejność: najstarsze `created`. `--key <KEY>` wskazuje zadanie wprost (te same warunki).
- **Blokada zajęcia:** `.tf/locks/<KEY>.json` tworzony atomowo (`O_CREAT|O_EXCL`) z `pid`, `host`, `at`; drugi
  `tf work` pomija zajęte zadanie. Blokada starsza niż `work.lock_hours` (domyślnie 6) z martwym procesem na tym
  samym hoście → przejęta z ostrzeżeniem. Zwolnienie zawsze w `finally`.
- **Worktree:** `.tf/worktrees/<KEY>` na gałęzi `story/<key>` od gałęzi bazowej (`--base`, domyślnie bieżąca);
  zadanie z istniejącym worktree nie jest brane samo (po STOP czeka na człowieka); wznowienie w nim tylko przez
  `--key`. Brudne drzewo robocze nie blokuje (worktree jest osobny). Przy instalacji prywatnej pliki fabryki są
  w `.git/info/exclude`, więc worktree dostaje kopię plików z manifestu, `.tf/config/` i folderu zadania.
- **Uruchomienie:** `claude -p "/tf <KEY> --auto --budget <USD>" --max-budget-usd <USD> --permission-mode
  <tryb>` w worktree (flagi sprawdzone w `claude --help`, Claude Code 2.1.325, 2026-11-15). Limit `--budget`
  wymagany (albo `work.budget_usd` w konfiguracji); bez niego odmowa. Tryb uprawnień domyślnie `dontAsk` (narzędzie
  spoza listy dozwolonych w `.claude/settings.json` jest odrzucane, nie czeka na człowieka); `work.permission_mode`
  zmienia go w konfiguracji projektu. Polecenie agenta można podmienić zmienną
  `TF_WORK_AGENT` (testy używają fałszywego agenta).
- **Po przeglądzie bezpieczeństwa (security-reviewer, 2026-11-15):** klucz zadania to nazwa folderu, a `key`
  w `task.json` musi się z nią zgadzać (inaczej cudzy `task.json` wskazałby worktree poza `.tf/worktrees`);
  z manifestu kopiowane są tylko ścieżki `.claude/` i `.tf/factory/`, bez symlinków i bez wyjścia poza katalogi;
  tryb uprawnień tylko `dontAsk` albo `plan`; łączny limit zadania `work.task_budget_usd` (domyślnie 20 USD, suma
  limitów z dziennika); limit jednego przebiegu najwyżej 500 USD; przejęcie martwej blokady przez `rename` (wygrywa
  jeden proces); znaki sterujące z tytułu usuwane; `--base` zaczynające się od `-` odrzucane. Zostaje opisane
  w przewodniku: hooki z `.claude/settings.json` gałęzi i zmienne środowiskowe człowieka trafiają do agenta.
- **`--dry-run`:** pokazuje wybrane zadanie, worktree i polecenie, niczego nie tworzy (bez kosztu).
- **Wynik:** jedna linia i wpis `.tf/logs/work.jsonl` (`key`, `started`, `ended`, `exit`, `stage` zadania po
  przebiegu, koszt z raportu, gdy jest). Kod wyjścia: 0 — przebieg zakończony (PR albo STOP), 3 — nie ma zadania,
  inne — błąd agenta.
- Treść: `PRZEWODNIK.md` (sekcja „Praca bez nadzoru”), `PUBLIC_API.md`, usage `tf.py`. Skill `tf` bez zmian.
- Testy: `core/tests/test_work_once.py` — wybór zadania (tryb, waga, zamknięte), blokada (dwa równoległe
  zajęcia → jedno), blokada martwa, worktree i gałąź, `--dry-run` bez skutków, brak limitu → odmowa, zwolnienie
  blokady po błędzie agenta, dziennik.
