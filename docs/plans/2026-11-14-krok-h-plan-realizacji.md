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
