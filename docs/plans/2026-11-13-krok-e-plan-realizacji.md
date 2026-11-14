# Krok E: plan realizacji — jedno polecenie `/tf`, pętla w rdzeniu

Data: 2026-11-14 (zastępuje wersję z 2026-11-13, sprzed decyzji o przeniesieniu pętli do rdzenia). Podstawa:
`2026-11-12-plan-zmian-os-fabryki.md` (pozycje 9, 10, 12 i część 16) oraz
`2026-11-12-os-fabryki-od-zadania-do-wdrozenia.md` §1a, §4, §8 i §9. Status: plan zapisany przed kodem; każdy
kawałek to osobny PR, kod metodą TDD.

## Decyzje człowieka

| Kiedy | Decyzja |
|---|---|
| 2026-11-13 | **D2** — wejście `/tf`, wywoływane także zwykłym zdaniem. **D3** — wagę dobiera fabryka; podnieść można swobodnie, obniżenie wymaga potwierdzenia człowieka. **D12** — przypisanie modelu i effortu na krok teraz bez zmiany zachowania; zmiany przydziału dopiero po osobnym pomiarze. |
| 2026-11-14 | **Talos przestaje istnieć jako osobny byt**: pętla przechodzi do rdzenia, a stare nazwy są usuwane od razu, bez warstwy zgodności (właściciel ma jedną instalację) — to wydanie MAJOR. **Jedno polecenie `/tf`** dla zadania z trackera, cięcia pdi i treści wklejonej w czacie; bez drugiego polecenia i **bez nazwy narzędzia w poleceniu** (`/tf EBO-1236`, nie `/tf jira EBO-1236`) — fabryka sama ustala źródło. **Źródła zewnętrzne:** domyślnie wklejenie treści; gdy w sesji jest odpowiedni serwer MCP (Jira, Linear), fabryka może z niego skorzystać — sama niczego nie instaluje. **pdi** ma po zmianach działać tak dobrze jak dziś; dopasowanie po stronie wykonawcy. |

## Cel

Człowiek pisze w sesji `/tf EBO-1236`, `/tf TSK-57` albo po prostu „zrób eksport do CSV” i fabryka sama
rozpoznaje źródło i rodzaj prośby, dobiera wagę, prowadzi pętlę i zatrzymuje się tylko tam, gdzie potrzebny jest
człowiek — komunikatem w prostym języku, z jednym pytaniem i opcjami. Działa to w każdej instalacji fabryki, bez
dodatkowego trybu.

## Co zastajemy (przegląd repozytorium 2026-11-14, tylko odczyt)

- **Pętla jest w `modes/mode-talos/`:** skill `talos-story-run` (`disable-model-invocation: true`), skrypty
  `run_state.py`, `run_report.py`, `plan_drift.py`, `security_scan.py`, szablony `dashboard.html` i `verify.sh`,
  agent sesji głównej `talos` zdefiniowany w `pack.yaml`, pięć plików testów, uprawnienia w `settings.json` trybu.
  Sześciu pomocniczych agentów (`scout`, `quick-fixer`, `researcher`, `architect`, `security-reviewer`,
  `scope-reviewer`) jest już w rdzeniu.
- **Ścieżka `.claude/skills/talos-story-run/scripts/` jest publicznym API** (`PUBLIC_API.md`) i jest wpisana w szablon
  CI pdi (`change-check.yml`), który użytkownicy kopiują do własnych repozytoriów.
- **pdi zależy od Talosa tylko przez nazwy**, bez zależności w `pack.yaml`: `phase_run.py` (persona `talos`, polecenie
  `/talos-story-run <TSK> --auto --change …`), `pr_loop.py` (`--agent talos`), szablony i zmienna
  `TALOS_SEMGREP_CONFIG`. Testy pdi sprawdzają te nazwy wprost. Kontrakt pdi (`tools/pdi-contract.json`) Talosa nie
  wymienia.
- **Reguła `refs`** sprawdza tylko nazwy skilli: rdzeń nie może wymieniać skilli trybów; tryb może wymieniać skille
  rdzenia. Skill w rdzeniu o nazwie `tf` ją przechodzi.
- **Nazwa `tf` nie ma prefiksu wymiaru**: `build.py check` pomija taki skill z ostrzeżeniem, a `new-skill` odmawia.
- **Aktualizacja:** pliki, których fabryka już nie dostarcza, trafiają do `.tf/backup/`; mechanizmu aliasów poleceń
  nie ma. `migrations.py` poprawia nazwy tylko w plikach własnych użytkownika.
- **Testy trybu** po przeniesieniu do rdzenia biegną w każdym wariancie, także bez nakładek.

## Kawałki

| # | Kawałek | Co powstaje | Testy (najpierw) | Wielkość |
|---|---|---|---|---|
| E0 | pętla w rdzeniu, stare nazwy usunięte, pdi woła `/tf` (bez zmiany zachowania pętli) | skill `tf` w `core/skills/tf/` z treścią pętli, skryptami i szablonami (ścieżka `.claude/skills/tf/scripts/`); agent sesji głównej `tf` w konfiguracji rdzenia; wymiar `tf`, wpis w `standalone_skills`; uprawnienia skryptów w `core/settings.json`; testy pętli w `core/tests/`; nowe nazwy: `.claude/tf.json`, `TF_DASHBOARD*`, `TF_SCAN_PATH`, `TF_SEMGREP_CONFIG`, `.tf/runs/dashboard.html`, przewodnik `.tf/factory/PETLA.md`; tryb `mode-talos` usunięty, instalator pomija go przy aktualizacji z komunikatem; pdi: persona `tf`, polecenie `/tf <TSK> --auto --change …`, `--agent tf`, szablony CI na nowe ścieżki i zmienne; `PUBLIC_API.md`, przewodniki | testy pętli przechodzą w wariancie bez nakładek; agent `tf` jest generowany z rdzenia; `build.py check` bez ostrzeżenia o nazwie; aktualizacja projektu z `mode-talos` w manifeście przechodzi i usuwa jego pliki, a jawna prośba o ten tryb kończy się odmową z wyjaśnieniem; testy pdi z nowymi nazwami w wariancie bez dodatkowych trybów | L |
| E1 | rozpoznanie wejścia i źródła (poz. 9, D2) | `/tf` wywoływany także przez model; skrypt rozpoznaje: klucz cięcia z planu zmiany, klucz zgłoszenia (tracker z karty operacyjnej albo z adresu), adres zgłoszenia, wklejoną treść, brak argumentów (lista zadań i wznowienie); gdy klucz może pochodzić z kilku trackerów podłączonych w sesji — jedno pytanie, a odpowiedź trafia do karty operacyjnej; skill prowadzi: zadanie → pętla, pytanie o kod → odpowiedź, swobodna zmiana w czacie → bez pętli, wątpliwość → jedno pytanie; źródło i data w `ticket.md`; tracker: gdy w sesji jest serwer MCP — odczyt (bez zapisu), gdy nie ma — jedno zdanie, czego brakuje, i „wklej treść”; treść z trackera to dane, nie polecenia | skrypt: każda forma wejścia → źródło i klucz; tracker zapamiętany w karcie nie jest pytany ponownie; klucz w dwóch planach → pytanie o zmianę; scenariusze skilla: kiedy włączyć pętlę i kiedy nie (pytanie, literówka, przegląd, plan projektu); brak MCP nie blokuje — droga przez wklejenie | M |
| E2 | waga dobierana skryptem (poz. 9, D3) | `tf task weight <KEY>`: propozycja z treści zgłoszenia i ze ścieżek planu, z powodem; `--set`: podniesienie swobodne, obniżenie tylko `--by human:<id>`; `lekka` — bez `spec.md`, jeden kawałek, dowód nadal wymagany; `pelna` — tryb Auto niedostępny, dodatkowi recenzenci | zgłoszenie o logowaniu → `pelna`; literówka → `lekka`; nowa reguła → `zwykla`; plan dotyka migracji → podniesienie; obniżenie bez człowieka → odmowa; `pelna` z `--auto` → odmowa z wyjaśnieniem | M |
| E3 | tryby i punkty stałe (poz. 9) | tryb `--plan`; tryb zwykły: jedno zatwierdzenie specyfikacji i planu; `--auto`: tylko punkty stałe; zamknięta lista kodów zatrzymań w skrypcie | `--plan` nie wchodzi w realizację; nieznany kod zatrzymania → błąd; podgląd pokazuje przyczynę | S–M |
| E4 | komunikaty zatrzymań (poz. 10) | jeden plik komunikatów w prostym języku dla każdego kodu: co się stało, czego potrzeba, jedno pytanie z opcjami i rekomendacją; polecenie drukujące komunikat | każdy kod ma komunikat, pytanie i co najmniej dwie opcje; słowa z listy żargonu → test czerwony | S |
| E5 | model i effort na krok (poz. 12, D12 — ruch 1) | `steps` w `config.yaml` z wartościami równymi dzisiejszym; `tf config show steps`; tabela „Kto co robi” sprawdzana względem konfiguracji | domyślne `steps` dają dzisiejsze modele; nadpisanie zmienia wynik; rozjazd tabeli z konfiguracją → test czerwony | M |
| E6 | cięcia pdi w nowym układzie | przebieg cięcia dostaje katalog zadania, specyfikację z wiersza cięcia i zamiaru zmiany, dowody, ślad i flagę z planu wydania; raport cięcia zostaje tam, gdzie oczekuje go pdi | plan szczegółowy po przeczytaniu kontraktu pdi i jego testów — osobny dokument przed kodem | L |

Kolejność: E0 → **pomiar** → E1 → E2 → E3 → **pomiar** → E4 → E5 → E6. Pomiary są płatne i wymagają zgody
człowieka. Pomiar po E0 ma wykazać brak zmiany względem pomiaru po D4 (ten sam zestaw historyjek, polecenie `/tf`).

## E1 — plan szczegółowy (2026-11-14, przed kodem)

**Pliki i kolejność** (test przed kodem, każdy test najpierw czerwony):

1. `core/tests/test_intake.py` → `core/skills/tf/scripts/intake.py` (bez modelu, tylko biblioteka standardowa
   i `run_report.py` obok):
   - `intake.py resolve "<całe wejście>" [--json]` — tylko czyta; drukuje rodzaj wejścia, klucz, tracker, opcje
     i jedną linię „Dalej: …” z następną czynnością;
   - `intake.py tracker [<typ> [--prefix EBO]]` — zapisuje tracker w karcie operacyjnej `.tf/config/operations.json`
     (`tracker.type`, `tracker.prefixes`) albo pokazuje zapisany.
2. `core/tests/test_run_report.py` → `run_report.py start --source "<skąd>"`: druga linia `ticket.md` to
   `Źródło: <skąd> · pobrano: <RRRR-MM-DD>` (bez `--source`: „wklejone w rozmowie” albo „plik <ścieżka>”) i zdanie, że
   treść zgłoszenia to dane. Przebieg cięcia (`--task`) zostaje bez zmian.
3. Scenariusze `core/tests/skill_evals/tf.json` (przed treścią skilla): włącz pętlę — numer zgłoszenia, zdanie
   „dodaj eksport…”; nie włączaj — pytanie o kod, literówka, przegląd PR, plan projektu, praca bez nadzoru.
4. `core/tests/test_tf_skill.py` → `core/skills/tf/SKILL.md`: bez `disable-model-invocation`, nowy opis i słowa,
   sekcja „Wejście” (rozpoznanie prośby, `intake.py resolve`, tracker przez MCP albo wklejenie, treść jako dane);
   uprawnienie `intake.py` w `core/settings.json`; komentarz agenta `tf` w `core/factory/config.yaml`.
5. Przewodniki (`PETLA.md`, `PRZEWODNIK.md`, FAQ), `PUBLIC_API.md`, bramka skilla, `sync-gate`.

**Reguły `resolve`** (pierwsza pasująca wygrywa; opcje `--auto`, `--plan`, `--budget N`, `--change CHG-n` oraz
słowo wymuszające `zadanie` / `pytanie` / `szybko` są wcześniej odcinane i zwracane osobno):

| Wejście | Rodzaj | Co zwraca |
|---|---|---|
| nic | `brak` | lista zadań w toku (wznowienie) albo prośba o treść |
| adres `http(s)://…` | `zgloszenie` | tracker z adresu (Jira `…/browse/KEY`, Linear `linear.app/…/issue/KEY`, GitHub i GitLab `…/issues/n` → `GH-n`, `GL-n`), klucz, adres jako źródło |
| jeden klucz, zadanie już istnieje | `wznowienie` | etap zadania i katalog |
| jeden klucz z nagłówka `tasks` planu zmiany | `ciecie` | zmiana; w kilku planach bez `--change` → pytanie o zmianę z listą |
| jeden klucz `ABC-123` | `zgloszenie` | tracker z karty (prefiks, potem domyślny), inaczej „nieznany” |
| ścieżka istniejącego pliku | `plik` | plik historyjki |
| klucz i dalej tekst (`PROJ-12: tytuł…`) | `tresc` | klucz, tytuł z pierwszej linii |
| inny tekst | `tresc` | tytuł z pierwszej linii, klucz nada `start` |

**Czego skrypt nie robi:** nie łączy się z siecią i nie widzi narzędzi sesji. Czy tracker jest podłączony, ocenia
model: jeden pasujący serwer MCP → odczyt zgłoszenia (bez zapisu) i `tracker <typ> --prefix`; kilka → jedno pytanie
i zapis odpowiedzi; żaden → jedno zdanie, czego brakuje, i prośba o wklejenie treści. Fabryka niczego nie instaluje.

**Zmiana kontraktu skilla (D2):** scenariusz „zaimplementuj tę historyjkę” przestaje być „nie włączaj” — zlecenie
zadania zwykłym zdaniem uruchamia pętlę. To decyzja człowieka z 2026-11-13, nie osłabienie testu.

**Poza E1:** waga (E2), tryb `--plan` i lista zatrzymań (E3) — `resolve` tylko przekazuje opcję dalej; nowy układ
cięć (E6); zapis do trackera. SKILL.md ma już ponad 15 000 znaków (ostrzeżenie `build.py check` sprzed E1) —
części dotyczące tylko pdi przeniosę do `references/` razem z E6, żeby nie ruszać dziś ścieżki pdi.

## Ustalenia

- **Stare nazwy znikają od razu** (decyzja właściciela: jedna instalacja, bez warstwy zgodności). To zmiana
  niezgodna wstecz, więc wydanie MAJOR ze stopką `BREAKING CHANGE:`; skrypt wydania sam podnosi zakresy
  `requires.core` nakładek. Własne pliki projektu z nazwą `talos-story-run` poprawia `migrations.py`. Kto skopiował
  do swojego repozytorium szablon CI pdi, musi w nim zmienić ścieżkę skryptu skanu i nazwę zmiennej.
- **Bez nazwy narzędzia w poleceniu.** Źródło ustala fabryka: klucz z planu zmiany to cięcie; inny klucz to
  zgłoszenie z trackera — tego z karty operacyjnej, a gdy karta go nie zna, z jedynego podłączonego w sesji; przy
  kilku podłączonych fabryka pyta raz i zapamiętuje odpowiedź w karcie. Bez połączenia: „wklej treść”.
- **Skrypty pętli zostają skryptami skilla** (`.claude/skills/tf/scripts/`), a nie silnika `.tf/factory/`: zmienia się
  tylko nazwa katalogu, więc przeniesienie da się sprawdzić jako czystą zmianę ścieżek.
- **E0 nie zmienia zachowania pętli:** `tf` ma w tym kawałku nadal wyłączone wywołanie przez model i tę samą treść pętli.
  Wywołanie zwykłym zdaniem i rozpoznawanie wejścia wchodzą w E1, żeby pomiar po E0 porównywał to samo z tym samym.
- **Uprawnienia w rdzeniu:** skrypty pętli, `pr_budget.py` i `./verify.sh` trafiają na listę dozwolonych w każdej
  instalacji (dotąd tylko z trybem). To te same polecenia, nie nowe.
- **Tracker przez MCP:** czy serwer jest dostępny w sesji, ocenia model (skrypt nie widzi narzędzi sesji). Fabryka
  tylko czyta zgłoszenie; niczego w trackerze nie zmienia i niczego sama nie instaluje. Droga przez wklejenie treści
  działa zawsze.
- **Cięcie pdi to trzecie źródło zadania.** `/tf TSK-57` rozpoznaje klucz po nagłówku `tasks` planu zmiany — tak jak
  dziś robi to `run_report.py start --task`. W E0 przebieg cięcia zostaje wewnątrz bez zmian (jeden katalog `.tf/runs/cuts/…`);
  nowy układ dostaje w E6.
- **Gałęzie `story/<slug>` i stopki `Change:` / `Flag:`** zostają bez zmian — korzysta z nich pdi.
- **Waga `lekka`** korzysta z istniejącej reguły „zadanie bez `spec.md`”; osobnego pliku `task.md` nie wprowadzam.
- **D12, ruch 1** niczego nie zmienia w zachowaniu. Kroki w głównym kontekście nie zmieniają modelu w trakcie
  przebiegu, bo kasuje to cache — przypisanie dotyczy wykonawców uruchamianych osobno.
- **Poza zakresem kroku E:** zdarzenia i kawałek zablokowany zamiast STOP (pozycja 11), poziom `lead` (D10), zapis do
  trackera (komentarz, zmiana statusu), eskalacja modelu po porażce bramki.

## Do sprawdzenia przez właściciela

- [x] **Czy repozytorium `dbqm45/pdi` wpisuje u siebie nazwę agenta `talos` albo polecenie `/talos-story-run`.**
  Sprawdzone 2026-11-14 na commicie `873f7b2` (z 2026-10-30), wyszukiwaniem w całym repozytorium: w kodzie (`src/`),
  kontrakcie (`contract/`), integracjach, testach i konfiguracji nazw tych **nie ma**. Słowo „Talos” występuje tylko
  w 10 plikach dokumentacji (`docs/`) i w 4 makietach (`design/konsola/`, `design/platforma/`) — jako opis, nie jako
  wywołanie. Działanie pdi od tej zmiany nie zależy.
- [ ] **Do decyzji:** czy poprawić słowo „Talos” w tych 14 plikach repozytorium pdi (teksty i dane przykładowe
  makiet). To osobna zmiana w innym repozytorium; bez niej nic się nie psuje.
- [ ] **Po `tf update` u siebie:** zmienić nazwę `.claude/talos.json` na `.claude/tf.json` i zmienne `TALOS_*` na
  `TF_*` (jeśli ich używasz) oraz poprawić ścieżkę skryptu skanu i nazwę zmiennej w skopiowanym `change-check.yml`.

## Ryzyka

| Ryzyko | Ograniczenie |
|---|---|
| przeniesienie zmienia zachowanie pętli | E0 to zmiana ścieżek i nazw; te same testy w nowym miejscu; pomiar po E0 względem pomiaru po D4 |
| pdi przestaje działać | testy pdi aktualizowane tylko o nazwy; przebieg cięcia sprawdzony na plikach wyjściowych; repozytorium `dbqm45/pdi` sprawdzone — nazw w kodzie nie ma (sekcja „Do sprawdzenia przez właściciela”) |
| CI projektu ze starą ścieżką skryptu skanu | instrukcja migracji w opisie wydania (`BREAKING CHANGE:`); nowy szablon `change-check.yml` |
| skill włącza pętlę, gdy człowiek chciał tylko porozmawiać (E1) | scenariusze „nie włączaj się” w bramce skilla; wątpliwość → jedno pytanie; pomiar po E3 |
| treść z trackera zawiera polecenia | zgłoszenie jest danymi (`ticket.md`), nie instrukcją; reguła z `core-agent-security` |
| dobór wagi zaniża ryzyko | reguły ostrożne (wątpliwość → wyższa waga); ścieżki wrażliwe zawsze `pelna`; obniżenie tylko przez człowieka |
