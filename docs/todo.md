# TODO

Odhaczone pozycje są zrobione (`- [x]`). Źródła faktów: dokumentacja code.claude.com i platform.claude.com pobrana
2026-10-20.

## Przepisanie historii repo i usunięcie atrybucji — zapisane 2026-11-20
Prośba człowieka (2026-11-20). Pliki repo są już czyste (bez nazw kursu, szkolenia i przepisanych materiałów),
ale stare commity, tagi i PR-y nadal je zawierają. Kolejność: po scaleniu wszystkich partii czyszczenia i licencji,
najlepiej po zmianie repo na prywatne.
- [ ] **Kopia zapasowa:** `git clone --mirror` całego repo przed jakąkolwiek zmianą historii; przechowywana poza GitHubem.
- [ ] **Przepisanie historii** (`git filter-repo`): usunąć z wszystkich commitów treść i wzmianki o kursie, szkoleniu
  i przepisanych materiałach (stare wersje skilli, `hint.pl.txt`, CHANGELOG, `docs/`), z listą ścieżek i wzorców
  (`--replace-text`, `--path`) sprawdzoną najpierw na kopii.
- [ ] **Usunięcie atrybucji Claude z historii:** linie `Co-Authored-By: Claude …` i `Claude-Session: …` w wiadomościach
  commitów (`--message-callback`), a w opisach PR-ów i wydań: „Generated with Claude Code”, linki do sesji.
- [ ] **Usunięcie atrybucji w plikach repo:** wzmianki o udziale Claude jako autora lub współautora (np. przypisy,
  stopki, opisy „napisane przez Claude”). Odwołania funkcjonalne do Claude Code jako narzędzia, na którym działa
  fabryka, zostają.
- [x] **Nowe commity bez atrybucji:** wyłączyć dopisywanie atrybucji w ustawieniach Claude Code (`attribution`
  w `settings.json`) i w instrukcjach sesji, żeby nie wracała. Zrobione: `.claude/settings.json` `"attribution": false` (#363).
- [ ] **Skutki do obsłużenia:** zmienią się wszystkie SHA. Trzeba odtworzyć tagi i wydania (v1…v20+), zaktualizować
  odwołania do commitów w `docs/` i CHANGELOG. Stare commity nadal będą w refach PR-ów (`refs/pull/*`) i w cache
  GitHuba, więc do ich usunięcia potrzebne jest zgłoszenie do GitHub Support. Forki i klony zachowają starą historię.
  Na koniec force-push wszystkich gałęzi i tagów, za wyraźną zgodą człowieka.
- [ ] **Uwaga prawna:** usunięcie atrybucji nie zmienia tego, kto faktycznie tworzył kod. Ochrona fabryki opiera się
  na umowie licencyjnej i poufności, nie na wpisach w historii. Przed wykonaniem tego punktu warto skonsultować go
  z prawnikiem IP.

## Najpierw: jedno źródło decyzji — zapis decyzji z różnych narzędzi (F0, po resecie limitu, 2026-10-23)
Cel: decyzje podejmowane w różnych narzędziach (sesje Claude Code, tf, pdi, później inne) zapisywane w jednym
źródle prawdy, jako część większego workflow AI SDLC; tf musi umieć je wypchnąć i zapisać zgodnie ze wspólnym
kontraktem. Plan i polecenie startowe: `docs/plans/2026-10-23-integracja-pdi.md`. Kolejność: przed F1a rekonstrukcji i pozostałymi pozycjami.
- Wszystko w opcjonalnym trybie `modes/mode-pdi/` (rdzeń bez zmian); działa, gdy podłączony jest serwer MCP pdi.
- [x] **F0:** dziennik per zmiana — `decision_record.py change new CHG-n [--source PRB-n]` (skrypt trybu), `check` dla
  `docs/project/changes/*/`, szablony i skill w trybie; TDD, bramki, PR.
- [x] **F0b:** `decision add` / `decision sync` / `decision export` — zapis decyzji z dowolnego narzędzia, wypchnięcie
  do rejestru pdi przez MCP, kolejka bez połączenia; reguła w skillu trybu. Osobny PR po F0.

## Oś fabryki: od numeru zadania do wdrożenia — zapisane 2026-11-12
Dokument zbiorczy (w większości zbudowany; decyzje D1–D12 zapisane 2026-11-22):
`docs/plans/2026-11-12-os-fabryki-od-zadania-do-wdrozenia.md`. Łączy Talosa, dashboard, pdi, plany §9–10 z 2026-11-08,
politykę autonomii i propozycje tf-1…tf-13 w jeden przebieg `/tf <KEY>` z trybami Plan / zwykły / Auto, jednym
katalogiem zadania i prostotą dla użytkownika jako wymaganiem (W8).
- [x] **Plan zmian** (22 pozycje wg wielkości, kroki A–H, ocena skali): `docs/plans/2026-11-12-plan-zmian-os-fabryki.md`.
  Zrealizowany krokami A–H (plany `docs/plans/2026-11-1[34]-krok-*`, pomiary po krokach w `docs/evals/`, ostatni
  `2026-11-15-pomiar-po-kroku-h.md`).
- [x] **Decyzje D1–D12** (sekcja 15 dokumentu) — zapisane 2026-11-22 wg kodu za zgodą właściciela; D5, D8, D10, D12 odłożone.
- [x] **E0–E8** (sekcja 14) — każdy etap osobnym planem i PR, po decyzjach; E1 (`tf onboard`) nie zależy od D2–D12. Źródła: 14 artykułów claude.dev (S1–S14, sekcja 16 dokumentu).
  Sprawdzone 2026-11-22 w kodzie (etapy zrealizowane jako kroki C–H planu zmian):
  - E0 pomiar bazowy: `docs/evals/2026-11-13-pomiar-bazowy-e0.md` (#220, #221);
  - E1 `tf onboard` (#216, #219), `REVIEW.md` w `core-git-workflow/references/review-md.md`;
  - E2 katalog zadania i `task_state.py` (krok C); E3 `spec_check.py`, `trace_check.py`, ochrona w `guard_paths.py` (krok D);
  - E4 jedno wejście, waga, tryby (krok E; dziś `/tf` + `/tf-task`); E5 `events.jsonl`, kawałek zablokowany, przegląd
    z końcem, „Waiting for you” (krok F; mod odłożony, D9);
  - E6 zgłoszenie z Jiry skryptem (G1); E7 karta wdrożenia, test dymny po scaleniu, `tf task close` (G3, G4);
  - E8 `tf work --once` (#271), odcisk harnessu w `log_usage.py`, pasmo kosztu w `cost_stats.py`, przegląd instrukcji
    (#258), ostrzeżenie po aktualizacji fabryki (#267), powtórka pomiaru po kroku H.
  - [ ] Zostaje z E6–E7 (poza krokiem G, `krok-g-plan-realizacji.md` „Poza krokiem G”): `tf po setup` (wiedza
    z Confluence), obserwacja pipeline'u wydania w CI, zapadki jakości i zbiór „incydent → test recenzenta”, zapis do
    trackera.

## Poziomy izolacji (basic / sandbox / container) — zapisane 2026-11-22
Plan: `docs/plans/2026-11-20-poziomy-izolacji.md`. Decyzje właściciela (2026-11-22): D1 push tylko z komputera
człowieka, D2 na start tylko terminal, D3 stała lista + domeny projektu, D4 `sandbox` domyślnie, D5 Docker i Podman
(wykrywany).
- [x] I1 (2026-11-22): klucz `isolation` (domyślnie `sandbox`, także w `org_defaults.config`), `tf isolation [<poziom>]`
  i `install.py --isolation` z odmową w sesji agenta, poziom i luka w `tf isolation` i `tf doctor`
  (`core/tests/test_isolation.py`, `tests/test_isolation_install.py`).
- [x] I2 (2026-11-22): `tf code` i `tf work` podają `.tf/cache/session-settings.json` (ustawienia wtyczki + sandbox
  z szablonu dla `sandbox`/`container`, bez sandboxa dla `basic`) i `TF_ISOLATION`; układ domyślny — sandbox
  w `.claude/settings.local.json` (instalator dodaje tylko bez klucza `sandbox`, `tf isolation` zastępuje lub usuwa,
  `tf uninstall` usuwa niezmieniony); `tf isolation` mówi o braku bubblewrap na Linuksie i o sesji bez `tf code`.
  Pomiar (2026-11-22, za zgodą, 0,0067 USD, Claude Code 2.1.330, Linux z bubblewrap): projektowe `"enabled": false`
  nie wyłącza sandboxa podanego przez `--settings` (zapis do `~` odrzucony; bez `--settings` przeszedł).
  Otwarte: skill `core-agent-security` §4a nadal mówi „opt-in” — do I8.
- [x] I3 (2026-11-23): hook `isolation_notice` (SessionStart: poziom, czego nie chroni, luki), poziom na pasku stanu
  (`container`, `TF_ISOLATION`, sandbox z ustawień albo `⚠ no sandbox`), `guard_bash` i `guard_paths` odmawiają
  obniżenia poziomu z sesji (`tf isolation <poziom>`, `isolation.py set`, `--isolation`, klucz `isolation`, klucz
  `sandbox` w `.claude/settings*.json`, pliki ustawień sesji, szablon sandboxa); `core/tests/test_isolation_hooks.py`.
- [x] I4 (2026-11-23): obraz `tf-sandbox:<wersja>` (`core/factory/container/`: Dockerfile z bazą przypiętą
  digestem i Claude Code 2.1.330, `init_firewall.sh` — domyślnie DROP, dozwolone DNS i adresy z `TF_ALLOW_DOMAINS`,
  `entrypoint.sh` — zapora jako root, potem `node` bez uprawnień), `container.py` i `tf code --container` (albo poziom
  `container`): Docker albo Podman (`TF_CONTAINER_ENGINE`), montaż tylko projektu i woluminu `tf-claude-<projekt>`,
  system plików tylko do odczytu, `isolation_allow_domains`; w kontenerze bez sandboxa Bash (zmiana planu, opis
  w planie). Testy: `core/tests/test_isolation_container.py`, obraz w zadaniu CI `container`
  (`tests/test_container_image.py`).
- [x] I5 (2026-11-23, D1): w kontenerze `guard_bash` odmawia `git push` z instrukcją (commit tu, push z terminala
  człowieka), hook startu mówi o tym w kontenerze, a `tf code --container` po sesji podaje liczbę commitów
  czekających na push i polecenie.
- [x] I7 (2026-11-23): `isolation_min` w warstwach (najostrzejszy wygrywa), luka w `tf isolation` / `tf doctor` / na starcie
  sesji, `tf isolation <poziom>` poniżej minimum odmawia; opis managed settings w `org/README.md` (ścieżki
  [niezweryfikowane]). Bez sprawdzenia minimum w `install.py --isolation` (nakładka firmy może jeszcze nie być
  zainstalowana w chwili wyboru).
- [x] I8 (2026-11-23): `core-agent-security`, `references/permissions-and-production.md` §4a — poziomy izolacji zamiast
  „opt-in”, pomiar `--settings`, kontener, zmiana poziomu tylko w terminalu; bramka skilla w obszarze `all`.
- [ ] I6 odłożone (D2); I9 pomiar macOS (`scripts/sandbox_check.py`, uruchamia właściciel).

## Program AI: bramka ewaluacji i zatwierdzone modele — zapisane 2026-11-19
Plan: `docs/plans/2026-11-19-bramka-ewaluacji-i-zatwierdzone-modele.md` (źródło: pdi
`docs/plan-program-ai-wg-aplikacji.md` §2.1, zadania T4 i T6). Zasada z decyzji człowieka 2026-11-19: tylko to, co
rozszerza fabrykę i niczego w niej nie zmienia, dopóki ktoś tego nie włączy.
- [x] **Bramka ewaluacji dla CI** (`packs/pack-it/skills/ai-evals/scripts/eval_gate.py`): próg z rozrzutu 3–5
  przebiegów obecnej wersji, werdykt release / investigate / hold, budżet kosztu, raport. Bez modelu i bez sieci.
- [x] **Lista zatwierdzonych modeli** (`models_approved`): rozszerzenie `model_check.py`, odmowa w `profile.py`, hook
  `model_guard` przy delegacji; warstwy firma → zespół → projekt tylko zawężają. Bez listy zachowanie jak dotąd.
- [x] (2026-11-22: ostrzeżenie na starcie sesji, `model_guard.py --session`, testy MG-8…MG-11) **Model sesji wybrany ręcznie (`/model`)** jest poza kontrolą fabryki — to rola bramki modeli (pdi: DI Model
  Gateway). Do rozważenia: ostrzeżenie na starcie sesji, gdy `model` z ustawień jest spoza listy.
- [x] (2026-11-22: czyta, test MC-10) **`model_check.py` nie czyta identyfikatorów z warstwy firmy i zespołu** (kontrola nazw `claude-…` patrzy na
  silnik i projekt; lista zatwierdzonych już czyta wszystkie warstwy). Drobne, osobna zmiana.
- [x] (2026-11-23: zamiast osobnego polecenia `tf analyze run --fail-on <ważność>` — bramka CI, test A-4f) **`tf standard`** (jedno polecenie „czy repo spełnia standard”, wersja z 9.17) — odłożone: najpierw porównanie
  z `tf status`, `tf task check` i standardami firmowymi (`tf analyze`), żeby nie powstało drugie polecenie o tym samym.
- [ ] **Pola opisu modelu** (`provider`, `regions`, `data`, `contract`) są dziś tylko dla ludzi. Gdy powstanie
  rejestr AI (pdi: DI AI Registry), uzgodnić z nim format, zamiast rozwijać własny.

## Ustawienia firmy (nakładka firmowa) — na później, zapisane 2026-11-16
Stan: nakładka firmowa działa (`org_defaults`, zestaw w `org/`: generator, szablon, przewodnik `org/README.md`).
Decyzja człowieka z 2026-11-16: miejsce ustawień zostaje jak jest, wrócić później.
- [ ] **Gdzie leżą wygenerowane ustawienia firmy** — decyzja człowieka. Dziś (wariant B) paczka firmy żyje
  w osobnym repozytorium firmy i trafia do projektu przez `tf install --pack-dir … --add pack-<firma>`.
  - **Wariant A:** katalog `custom-settings/` w repozytorium fabryki, obok `packs/` i `modes/`. Zalety: jedno repo
    zamiast dwóch, instalator bierze ustawienia sam (bez `--pack-dir`), `tf update` przynosi je razem z fabryką,
    widać od razu, że to konfiguracja, a nie wiedza dziedzinowa. Wady: fabryka staje się specyficzna dla jednej firmy
    (trudniej ją udostępnić albo pobierać zmiany z innego źródła fabryki); każda zmiana standardów to commit i wydanie
    fabryki, choć rdzeń się nie zmienił.
  - **Wariant B (obecny):** osobne repozytorium firmy. Zalety: fabryka zostaje ogólna, firma zmienia standardy we
    własnym rytmie i uprawnieniach, kilka firm może używać tej samej fabryki. Wady: jedno repo więcej i jednorazowe
    `--pack-dir`.
  - **Rekomendacja:** A, gdy fabryki używa tylko jedna firma; B, gdy fabryka ma służyć wielu firmom.
  - **W obu wariantach format zostaje nakładką** (`pack.yaml`): instalacja, aktualizacja, audyt skilli, bramka i testy
    działają już dla tego formatu; własny format `custom-settings/` wymagałby zbudowania ich drugi raz.
  - **Zakres zmiany dla A:** instalator i sprawdzenia fabryki (CI, `tools/workspace.py`) traktują `custom-settings/`
    jak dodatkowe źródło nakładek, włączane domyślnie; generator `org/new_org_pack.py` dostaje opcję zapisu tam;
    `org/README.md` opisuje oba warianty; testy instalacji i aktualizacji z ustawieniami w `custom-settings/`.
- [x] **Generator standardów z dokumentów firmy z kontrolą cytatów skryptem** (zrobione 2026-11-16, `org/standards_from_docs.py`). Dziś `org/README.md` daje gotowe
  polecenie dla agenta, a cytaty sprawdza człowiek. Plan (wzorzec rekonstrukcji projektu z kodu): (1) dokumenty
  (eksport z Confluence: HTML, Word, PDF, Markdown; albo pobrane przez połączenie MCP z adresem i datą) do `sources/`;
  (2) skrypt dzieli je na sekcje po nagłówkach, usuwa duplikaty, zapisuje manifest z odciskami sekcji; (3) model
  przypisuje każde ustalenie do obszaru (UI, API, dane, wydania, wspólne) i rodzaju (sprawdzalne wzorcem →
  kandydat do `rules.yaml` z przykładem w `fixtures/`; wymaga oceny → `references/<obszar>.md`; ogólna wiedza →
  pominięte; sprzeczne → lista do decyzji); (4) skrypt generuje pliki, scenariusze na obszar i raport;
  (5) kontrola bez modelu: każdy cytat istnieje w źródle (jak `recon_check`), każdy wzorzec się kompiluje i przechodzi
  bramkę na przykładach; (6) odświeżanie tylko zmienionych sekcji z manifestu. Skill procesowy (np.
  `core-org-standards`) w zestawie `org/` albo w rdzeniu — do decyzji przy planie. Ryzyka: przeinaczone ustalenia
  (cytat obowiązkowy), zbyt szerokie wzorce (kandydaci z przykładem i zgodą człowieka), poufność dokumentów (treść
  idzie do modelu — polityka danych firmy).
- [ ] **Pomiar generatora na prawdziwych dokumentach firmy** — trafność przypisania obszaru i rodzaju, odsetek
  poprawnych cytatów, koszt; płatny, za zgodą człowieka i na dokumentach, które firma udostępni.

## Warstwy zespołu i preferencji osoby, wyłączanie skilli — na później, zapisane 2026-11-16
Cel człowieka: nad rdzeniem warstwy firmy, zespołu i osoby. Standardy firmy i zespołu obowiązują, a każdy developer
ustawia swój sposób pracy: jeden chce, żeby wszystko szło samo, drugi zatwierdza każdy krok, trzeci woli luźną
rozmowę z agentem. Do tego zespół wyłącza skille, których nie potrzebuje (backend bez Figmy, frontend bez AWS).
Stan dziś: warstwy `config_layers` to silnik ← organizacja (`org_defaults`) ← projekt. Skill wyłącza się tylko
w całej fabryce (`metadata.status`). Tryb zadania (`tf task mode <KLUCZ> plan|normal|auto`) ustawia się osobno dla
każdego zadania, bez domyślnego wyboru osoby. Prywatne pliki osoby już są: `.claude/settings.local.json`,
`CLAUDE.local.md`, `.claude/factory-settings.json`.

**Kolejność prac (ustalona przez człowieka 2026-11-16).** Zasada dla każdego punktu: co da się zrobić
deterministycznie (skrypt, reguła, test), robi skrypt; model tylko tam, gdzie potrzebna jest ocena albo wsparcie
człowieka, i z kontrolą wyniku skryptem.
1. [x] **Styl pracy i warstwa osoby** (zrobione 2026-11-16, `core/tests/test_work_style.py`).
   - [x] plik preferencji osoby (`~/.tf/preferences.yaml`) i nadpisanie w projekcie (`.tf/config/me.yaml`, zawsze
     w `.git/info/exclude`) jako ostatnia warstwa `config_layers` — skrypt;
   - [x] granice: osoba nie rozluźnia polityki autonomii ani sufitów firmy i zespołu — sprawdzenie w składaniu
     warstw (skrypt), z testem;
   - [x] trzy style (`autonomous`, `step-by-step`, `conversation`) jako gotowe wartości istniejących przełączników
     (domyślny tryb zadania, `loop.blocked_slices`, …) — dane w konfiguracji, polecenie `tf style <nazwa>`;
   - [x] zatrzymanie pętli `/tf` po każdym kawałku dla stylu `step-by-step` — stan w `run_state.py` (skrypt), model
     tylko pokazuje plan i diff i czeka na zgodę;
   - [x] styl `conversation`: zadanie kończy się na planie (domyślny tryb `plan` przy `tf task start`), kod dopiero po
     zmianie trybu przez człowieka, potem zgoda po każdym kawałku — wszystko w skryptach, bez instrukcji w prompcie.
     Pętla `/tf` i tak startuje tylko na polecenie człowieka; rozmowa z personą poza pętlą nie zmienia plików bez
     prośby tak jak dotąd;
   - [x] styl `conversation` ustawia tryb uprawnień Claude Code `plan` w `.claude/settings.local.json` projektu
     (`tf style`, także po `tf install` i `tf update`): rozmowa poza `/tf` też nie zmienia plików bez zgody. Trybu
     wybranego przez człowieka nie nadpisuje, zmiana stylu oddaje poprzedni (znacznik w `.claude/factory-settings.json`);
   - [x] `tf config show` z warstwą „osoba” i źródłem każdej wartości; opis w PRZEWODNIK i FAQ; mapa fabryki
     (`docs/mapa-fabryki.html`) — status „działa”.
2. [x] **Trafność podpowiedzi skilli** (zrobione 2026-11-16, `packs/pack-it/tests/test_hint_backend.py`) (przy okazji punktu 1, bez modelu: scenariusze `skill_hint --explain` w teście).
   - [x] walidacja DTO w repo Spring Boot bez podpowiedzi — słowa kluczowe w opisie `fw-spring-boot` (pack-it);
   - [x] obsługa błędów wg RFC 9457 podsuwa skill serwera MCP — doprecyzować opisy obu skilli;
   - [x] test regresji: zestaw poleceń backendu z oczekiwanym skillem (jak w pomiarze z 2026-11-16) w testach
     hooka, uruchamiany w CI bez modelu.
3. [x] **Warstwa zespołu** (zrobione 2026-11-16, `tests/test_new_org_pack.py` OP-17…OP-26).
   - [x] `org/new_org_pack.py <firma> --team <zespół>` → `pack-<firma>-<zespół>` z `requires` nakładki firmy
     (generator, skrypt);
   - [x] `config_layers`: silnik ← firma ← zespół ← projekt ← osoba; test kolejności i granic (`task.allowed_modes`
     to przecięcie warstw — wcześniej projekt mógł przywrócić tryb zabrany przez firmę; prefiksy trackera zespołu);
   - [x] standardy zespołu sprawdzane bez modelu (`rules.yaml`, semgrep) jak w nakładce firmy.
4. [x] **Generator standardów z dokumentów** (zrobione 2026-11-16: `org/standards_from_docs.py` split/check/apply,
   `tests/test_standards_from_docs.py`): podział (Markdown, HTML, Word, PDF), manifest i kontrola cytatów skryptem;
   model tylko przypisuje ustalenia do obszaru i rodzaju. Zostaje pomiar na prawdziwych dokumentach firmy (niżej).
5. [ ] **Decyzje człowieka:** `custom-settings/` czy osobne repo firmy; monorepo (najpierw sprawdzić w dokumentacji,
   czy Claude Code wczytuje skille z podkatalogów).

- [x] **Najpierw pomiar** (kolejność ustalona przez człowieka: zapis, potem pomiar). Na repo backendu z pełną nakładką
  IT: (1) bez modelu — ile kontekstu zajmuje lista skilli (opisy) i schematy narzędzi serwerów MCP, ile podpowiedzi
  `skill_hint` trafia w skille spoza dziedziny repo (np. `ux-*`, `ops-cloud-*` przy zadaniach backendu);
  (2) na modelu, za zgodą człowieka — czy wyłączenie zbędnych skilli zmienia trafność wyboru skilla i koszt sesji.
  Wynik decyduje, czy `skills_off` jest potrzebne, czy wystarczy wybór nakładek i wyłączenie MCP w `settings.json`.
  **Wynik części (1), 2026-11-16** (repo Spring Boot, `install.py --packs pack-it`, język pl; 20 poleceń backendu
  przez `skill_hint.suggest`; tokeny oszacowane jako znaki/3,5 [założenie: bez licznika tokenów]):
  - w liście 155 skilli, opisy ≈ 21,3 tys. znaków ≈ 6,1 tys. tokenów; 36 skilli spoza dziedziny repo (`fe-`, `ai-`,
    `pm-`, `data-`, `txt-`, `fw-`/`lang-` innych stacków) to 24,8% opisów. W cache to koszt pomijalny; problemem jest
    budżet listy skilli w Claude Code (~1% okna według opisu hooka `skill_hint`), w który przy oknie 200 tys. opisy
    się nie mieszczą [niezweryfikowane: liczba z opisu hooka];
  - w 12/20 poleceń obcy skill był w trójce rankingu; 3 z 17 podpowiedzi były obce (`fw-nestjs` przy walidacji DTO,
    `fw-angular` przy aktualizacji Spring Boot, `ai-mcp-server` przy RFC 7807);
  - po odjęciu obcych skilli: 0 obcych podpowiedzi, 2 nowe trafne (`be-messaging-outbox`, `ops-docker`), 1 trafna
    utracona (`be-api-design` przy RFC 7807), 1 nowa chybiona (`core-skill-authoring` przy audycie zmian) — wagi
    rzadkości słów zależą od całego indeksu;
  - **wniosek:** największy zysk bez żadnej konfiguracji daje pomijanie w `skill_hint` skilli `fw-`/`lang-`/`tool-`
    stacków, których `detect_stack` nie wykrył w projekcie. `skills_off` potrzebne dla wymiarów spoza stacku
    (`ai-`, `pm-`, `fe-` w repo backendu).
  **Wynik części (2), 2026-11-16** (ten sam repo; 18 zadań backendu, `claude -p` w trybie plan, pełne środowisko
  fabryki z hookami, `--setting-sources project,local`; trzy warianty: pełna instalacja 165 skilli, bez skilli innych
  stacków 154, bez wszystkich obcych 127; Haiku i Sonnet, po jednym przebiegu; koszt 25,00 USD):
  | model | wariant | właściwy skill | obcy skill | koszt / przebieg |
  |---|---|---|---|---|
  | Haiku | pełna | 18/18 | 1 | 0,248 USD |
  | Haiku | bez innych stacków | 17/18 | 0 | 0,222 USD |
  | Haiku | bez obcych | 17/18 | 0 | 0,221 USD |
  | Sonnet | pełna | 18/18 | 1 | 0,227 USD |
  | Sonnet | bez innych stacków | 18/18 | 0 | 0,242 USD |
  | Sonnet | bez obcych | 18/18 | 0 | 0,229 USD |
  - jedyny obcy skill w obu modelach to `fw-nestjs` przy walidacji DTO w repo Spring Boot — ten sam, którego
    podsuwa `skill_hint` (część 1); jedyny chybiony to Haiku przy podziale `OrderService` w obu okrojonych wariantach
    (jeden przebieg, w granicach rozrzutu); różnice kosztu ±10% przy jednym przebiegu to rozrzut, nie efekt;
  - **wniosek:** wyłączanie skilli nie poprawia trafności ani kosztu w stopniu wartym nowego mechanizmu. Robimy tylko
    filtr stacku w `skill_hint` (**zrobione 2026-11-16**: skille `fw-`/`lang-` spoza wykrytego stacku odpadają po
    rankingu, chyba że polecenie je wymienia; w repo Spring Boot 0 z 16 podpowiedzi z innego stacku, wcześniej 3 z 17;
    `CLAUDE_SKILL_HINT_STACK=0` wyłącza) (usuwa jedyny zaobserwowany błąd, bez konfiguracji). `skills_off` odkładamy; warstwy
    zespołu i osoby uzasadniają standardy i styl pracy, nie oszczędność kontekstu. Powtórzenie pomiaru nie jest
    potrzebne do tej decyzji.
- [x] **Warstwy:** silnik ← firma ← zespół ← projekt ← osoba. Zrobione: `core/factory/packs.py`, `org/new_org_pack.py --team` (#282, #283). Każdy czytelnik konfiguracji (build, hooki, `tf risk`,
  `tf work`, `tf config show`) składa je w tej kolejności; `tf config show` przy każdej wartości podaje warstwę.
  - **Zespół:** nakładka z tego samego szablonu co firmowa (`org/new_org_pack.py <firma> --team <zespół>` →
    `pack-<firma>-<zespół>`, `requires` nakładki firmy): standardy zespołu (reguły, obszary, semgrep), domyślne
    ustawienia, `settings.json` (np. wyłączone serwery MCP).
  - **Osoba:** plik poza repozytorium (np. `~/.tf/preferences.yaml`, wspólny dla wszystkich projektów osoby) i
    nadpisanie w projekcie (`.tf/config/me.yaml`, zawsze w `.git/info/exclude`, także przy `--shared`).
- [x] **Zasada warstw:** (zrobione z warstwami, #282, #283) niższa warstwa dodaje i zaostrza, nie rozluźnia tego, co wyższa zablokowała. Tak działa już
  polityka autonomii (`deny` firmy obowiązuje projekt). Firma albo zespół może dać **sufit** (np. „tryb Auto
  dozwolony”, „najwyżej X USD na przebieg”), a osoba wybiera w jego granicach. Skille bezpieczeństwa, rzetelności
  i TDD (`core-agent-security`, `core-grounding`, hooki `tdd_guard`, `guard_*`) wyłącza tylko firma.
- [x] **Style pracy osoby** (zrobione: `tf style`, `core/factory/config.yaml` sekcja stylów, #282) (preset, który ustawia kilka istniejących przełączników naraz):
  - **autonomous** — domyślny tryb zadania `auto` (w granicach sufitu), `loop.blocked_slices: true`, raport na końcu;
    wymaga limitów `work` i obowiązującej polityki autonomii;
  - **step-by-step** — tryb `normal` i nowy przełącznik zatrzymania pętli `/tf` po każdym kawałku (zgoda przed
    następnym), widoczny plan i diff każdego kroku;
  - **conversation** — persona odpowiada i proponuje, a pętlę `/tf` i zmiany w plikach uruchamia dopiero na prośbę;
    bez automatycznego startu przebiegu z numeru zadania.
  Preset to tylko domyślne wartości: każde zadanie nadal może dostać inny tryb (`tf task mode`).
- [ ] **`skills_off`** — odłożone po pomiarze z 2026-11-16 (bez zysku trafności i kosztu); w każdej warstwie: skill zostaje w instalacji i działa ręcznie (`/nazwa`), ale
  nie trafia do agentów ani katalogu — ten sam mechanizm co `drop_inactive` w `build.py`. Niższa warstwa może włączyć
  z powrotem skill wyłączony wyżej, chyba że wyższa go zablokowała.
- [ ] **Monorepo (później):** kilka zespołów w jednym repozytorium wymaga podziału po katalogach. Claude Code
  wczytuje `CLAUDE.md` z podkatalogów; czy tak samo skille z podkatalogów — sprawdzić w dokumentacji przed planem
  [niezweryfikowane].
- [x] (2026-11-23: `core/tests/test_config_layers.py`, CL-1…CL-6, 11/11 — zachowanie zgodne, bez poprawek kodu) **Testy:** składanie pięciu warstw, sufit firmy i zespołu nie do przekroczenia przez osobę, preset stylu
  zmienia tylko wartości domyślne, `tf config show` pokazuje źródło, plik osoby nigdy nie trafia do repozytorium.

## Luki z przeglądu agend szkoleń (AI, agenci, product engineering) — zapisane 2026-11-15
Przegląd 2026-11-15: przeszukanie skilli, hooków i skryptów po hasłach z agend szkoleń (mechanika LLM, sterowanie
kontekstem, systemy wiedzy, harnessy, workflowy, agenci, product engineering) oraz pytanie człowieka o Spec Driven,
analizę statyczną, piramidę testów, metody formalne, dokumentację i monitoring. Pokryte: spec-driven (`tf spec`,
`tf trace`, `qa-spec-first-testing`), analiza statyczna (`tool-semgrep`, `sec-variant-analysis`, `tf analyze`),
piramida testów (`eng-testing`), dokumentacja (`docs-tech-writing`), monitoring (`ops-observability`,
`ops-sre-incidents`, `control_band.py`). Przegląd był po słowach kluczowych z odczytem kluczowych skilli, bez oceny
jakości każdej treści. Decyzja człowieka: do planu trafiają wszystkie braki, także pokryte częściowo; kolejność —
K1, potem K2, dalej wg priorytetu. Skille wg `core-skill-authoring` (scenariusze ewaluacji przed treścią, bramka
`skill_gate.py`, ewaluacja na modelu tylko za zgodą), kod metodą TDD, każdy krok osobnym PR. Wersje narzędzi
i specyfikacji sprawdzić u źródła z datą przed wpisaniem do skilla.

Braki (brak pokrycia):
- [x] **K1: skill `qa-formal-methods` (`pack-it`)** (zrobione 2026-11-15: osobny skill wygrał z sekcją w `qa-spec-first-testing` — wczytanie 8/8 wobec 1/8, treść 8/8 wobec 6/8, bez skilli 4/8, koszt 3,57 USD: `docs/evals/2026-11-15-qa-formal-methods-sekcja-czy-skill.md`; przykład Z3 uruchomiony, TLA+ i Alloy bez uruchomienia — pobranie narzędzi zablokowane w sesji; odnośnik z `qa-spec-first-testing`, role qa-automation i solution-architect) — jedyna dziura z pytania wprost; dziś są tylko testy
  właściwości (Hypothesis w `tool-pytest`, fast-check) i niezmienniki w DDD. Treść: kiedy metoda formalna się opłaca
  (współbieżność, rozproszone protokoły, maszyny stanów, pieniądze i limity, uprawnienia), a kiedy nie; drabina
  kosztu: asercje i design by contract → testy właściwości → model checking (TLA+/PlusCal z TLC lub Apalache, Alloy)
  → weryfikacja programu (Dafny, solver SMT Z3) → dowód; specyfikacja formalna jako deterministyczna wyrocznia dla
  agenta (agent pisze model, checker szuka kontrprzykładu, kontrprzykład staje się testem `AC-n`); typowe pułapki
  (model rozjeżdża się z kodem, zbyt mała przestrzeń stanów daje fałszywe „OK”). Scenariusze ewaluacji: wyścig przy
  rezerwacji ostatniego miejsca, idempotentna płatność z ponowieniem, maszyna stanów sesji (np. OCPP).
  Odnośniki z `eng-testing`, `qa-spec-first-testing`, `arch-quality-attributes`, `ddd-tactical-design`.
- [x] **K2: system diff i warstwowy przegląd w `qa-change-review`** (zamknięte bez budowy 2026-11-15: luka niepotwierdzona — haiku i sonnet bez skilla wypisują zmiany systemowe 8/8 na małym diffie i 4/4 na 609-liniowym PR z szumem, 1,96 USD: `docs/evals/2026-11-15-k2-diff-systemu-luka.md`; wrócić przy prawdziwym przeoczeniu w przeglądzie albo PR większym niż kontekst) — przegląd mówi dziś, czy kod zgadza się
  z planem, ale nie, co zmiana zmienia w systemie. Raport „diff systemu” w stałych sekcjach: zachowanie (kryteria
  `AC-n` nowe, zmienione, usunięte), UX (ekrany, teksty, przepływy), dane (migracje, schematy, retencja), architektura
  (nowe zależności, moduły, granice), złożoność (przyrost kodu, nowe punkty konfiguracji), operacje (zmienne
  środowiskowe, flagi, zadania w tle, alerty, koszt). Część deterministyczna skryptem (migracje, manifesty
  zależności, pliki konfiguracji, nowe endpointy — z `git diff` i `code_graph.py`), część oceniana modelem. Warstwowy
  diff: kolejność czytania kontrakt → dane → logika → UI → testy, z osobnym werdyktem na warstwę. Sekcja trafia do
  opisu PR (sprawdzić zgodność z `pr_body` i testami `test_pr_body.py`).
- [x] **K3: code mode w `ai-agents` i `core-cost-control`** (zrobione 2026-11-15: punkt „Code mode” w kroku 4 `ai-agents`, scenariusz `code-mode-crm`; przed 3/5 i 4/5, po 5/5 w 4 przebiegach, 0,59 USD: `docs/evals/2026-11-15-k3-code-mode.md`; `core-cost-control` bez zmian) (pomiar 2026-11-15, `docs/evals/2026-11-15-luki-k3-k7.md`: katalog = bez skilli 14/18; jedyna powtarzalna luka — rozdzielenie odczytu od zapisu i zatwierdzanie akcji zapisu w kodzie agenta, limit czasu i kosztu; zakres zawężony do 2–3 zdań w `ai-agents`, sprawdzonych scenariuszem `gap-k3-code-mode-crm`) — agent pisze krótki program, który sam woła narzędzia
  lub API i filtruje wyniki, zamiast wielu wywołań narzędzi z pełnym wynikiem w kontekście. Kiedy (duże wyniki,
  pętle po wielu elementach, łączenie danych z kilku narzędzi), kiedy nie (pojedyncze wywołanie, akcje wymagające
  zatwierdzenia każdej z osobna); wymagania: piaskownica, limit czasu i budżetu, zwracany tylko wynik końcowy;
  związek z MCP (narzędzia serwera jako API w kodzie). Wzorce i nazewnictwo dostawców sprawdzić z datą
  [niezweryfikowane].
- [x] **K4: syntetyczni użytkownicy, nagrania i analiza zachowań (`ux-research-methods`, `tool-playwright`)** (zamknięte bez budowy 2026-11-15: luka niepotwierdzona, 17/18 z katalogiem i bez skilli, `docs/evals/2026-11-15-luki-k3-k7.md`) —
  persony z `pack-ux` jako agenci przechodzący przepływ w przeglądarce (Playwright) z celem i ograniczeniami persony;
  nagrania i ślady (trace, wideo, zrzuty) jako materiał do notatek wizualnych; analiza: gdzie agent utknął, wrócił,
  zgadywał. Granica: wynik syntetyczny to hipoteza do sprawdzenia na ludziach, nie zastępuje badań z użytkownikami.
  Scenariusz ewaluacji: formularz z mylącym polem, które syntetyczny użytkownik powinien wskazać.

Pokryte częściowo:
- [x] **K5: mechanika modelu jako referencja `ai-prompt-engineering/references/mechanika-modelu.md`** (zamknięte bez budowy 2026-11-15: luka niepotwierdzona, 16/18 z katalogiem i bez skilli, `docs/evals/2026-11-15-luki-k3-k7.md`; „J-space” nadal bez źródła) — dziś są
  tylko praktyczne konsekwencje rozproszone w `core-grounding`, `ai-prompt-engineering` i `core-cost-control`.
  Treść: tokenizacja (koszt, liczby, tekst polski zużywa więcej tokenów — zmierzyć), przewidywanie kolejnego tokenu
  i skąd biorą się konfabulacje, uwaga i pozycja instrukcji w długim kontekście („lost in the middle”), data
  odcięcia wiedzy (odnośnik do `core-grounding`), okno kontekstu i limit wyjścia, rozumowanie i effort, uogólnianie
  i skojarzenia jako mechanizm sterowania kontekstem (przestrzeń ukryta). Każda sekcja kończy się konsekwencją dla
  promptu, skilla lub agenta. Termin „J-space” z agendy — ustalić źródło i definicję przed wpisaniem
  [niezweryfikowane].
- [x] **K6: A2A w praktyce (`ai-agents`)** (zamknięte bez budowy 2026-11-15: luka niepotwierdzona, 22/22 z katalogiem i bez skilli, `docs/evals/2026-11-15-luki-k3-k7.md`) — mapa protokołów jest (`references/protocols-and-tracing.md` §1–2), brak
  procedury: wystawienie agenta przez A2A (Agent Card zgodna z tym, co agent naprawdę robi; uwierzytelnianie
  i autoryzacja), odkrywanie i wybór współpracownika po karcie, kontrakt przekazania (zakres, kontekst, właściciel,
  widoczność postępu, format wyniku, raport porażki — spiąć z `core-async-delegation`), testy interoperacyjności.
  Rozważyć deterministyczny walidator karty (schemat, deklarowane umiejętności a testy). Wersję A2A sprawdzić
  w repozytorium specyfikacji z datą.
- [x] **K7: skill `pm-release-learning` — pętla po wydaniu** (zamknięte bez budowy 2026-11-15: luka niepotwierdzona, 20/24 z katalogiem i bez skilli, braki rozproszone, `docs/evals/2026-11-15-luki-k3-k7.md`) — są elementy (`control_band.py`, `metric_watch.py`
  w `mode-pdi`, `pm-product-analytics`, `ops-sre-incidents`, `core-agent-retro`), brak procedury, która je łączy.
  Treść: sygnały (analityka, logi, incydenty, zgłoszenia wsparcia, język klienta, obserwowane zachowanie); zamierzony
  a faktyczny wynik (metryki z `intent.md`), tarcie, obejścia, regresje, skutki uboczne; synteza: grupowanie
  sygnałów, wykrywanie sprzeczności, przyczyna źródłowa, pewność i dowód; decyzja z listy: rozwijać, poprawić,
  uprościć, wycofać, zbadać, zatrzymać; wyjście: aktualizacja zgłoszeń, specyfikacji, ewaluacji, `lessons.md`
  i kontekstu agentów. Odnośnik z `core-delivery-lifecycle` („co po wdrożeniu”).
- [x] **K8: specyfikacja — przykłady negatywne i synchronizacja z główną specyfikacją** (zrobione 2026-11-15 w zakresie przykładów negatywnych: ostrzeżenie SPEC-009 w `tf spec check`, gdy żadne kryterium nie opisuje zachowania niedozwolonego — bez blokady etapu, bo nie każda historyjka ma przypadek negatywny; szablon `tf spec new` z kryterium negatywnym; kryteria negatywne to zwykłe `AC-n`, więc `tf trace` wymaga dla nich testu bez zmian w kodzie śladu. Synchronizacja z główną specyfikacją zostaje przy pozycji „OpenSpec: zmiana jako delta” w sekcji Spec Kit) — `spec.md` ma sekcje „Bez
  zmian” i „Poza zakresem”, ale nie ma miejsca na przykłady zachowania niedozwolonego. Dodać opcjonalną sekcję
  „Przykłady negatywne” (Zakładając / Gdy / Wtedy **nie** …) do szablonu `tf spec new` i reguł `spec_check.py`
  (puste przykłady jak SPEC-005; `tf trace` traktuje je jak kryteria z testem). Synchronizacja: domknąć istniejącą
  pozycję „OpenSpec: zmiana jako delta i archiwizacja do głównej specyfikacji” (sekcja Spec Kit) dla `tf spec`, nie
  tylko `mode-pdi` — przy zamknięciu zadania kryteria trafiają do globalnej specyfikacji modułu, rozjazd jest
  ustaleniem.
- [x] **K9: hasła w `tools/coverage_areas.json`** (zrobione 2026-11-15; dziury po zmianie: diff systemu, okno kontekstu, code mode — K2, K5, K3) — dopisać hasła, po których mapa pokrycia wykryje powyższe obszary
  (np. „metody formalne”, „tla+”, „diff systemu”, „code mode”, „a2a”, „po wydaniu”, „syntetyczny użytkownik”,
  „tokeniz”), żeby kolejny przegląd był powtarzalny bez ręcznego szukania. Mały krok, można razem z K1.
- [ ] **K10: metody formalne w wiedzy EV — przeniesione do `ev-intelligence`** (decyzja człowieka 2026-11-15:
  `pack-ev` wycofany z `tf`, wiedza EV scalana ze skillami `ev-*` w `dbqm45/ev-intelligence`, stan w
  `todo/tf-pack-ev/STATUS.md` tam). Zapis historyczny poniżej. Treść niezależna od miejsca: sekcja „model przed symulacją”
  w odpowiedniku `dom-ev-simulation-testing` z odnośnikiem do `qa-formal-methods` (przy `pack-ev` w `tf` sprawdzić
  zależność `pack-ev` → `pack-it` dla `refs`), tłumaczenie śladu TLC na oś czasu scenariusza `evtest`; scenariusz
  ewaluacji przed treścią, bramka. Pilot w kodzie `evtest` i uzasadnienie są w repo `dbqm45/ev-testing`:
  `docs/todo.md`, `docs/plans/2026-11-15-metody-formalne.md` (gałąź `claude/intelligent-ramanujan-rjm26k`).

## Luki katalogu i polityka autonomii (przegląd listy „Autonomous Full Stack Agent”) — zapisane 2026-11-09
Plan: `docs/plans/2026-11-09-luki-katalogu-i-autonomia.md`. Decyzja człowieka: najpierw sekcja A, potem B. Skille wg
`core-skill-authoring` (scenariusze przed treścią, bramka), kod metodą TDD, każdy krok osobnym PR.

Sekcja A — luki w katalogu:
- [x] **A1:** skill `pm-product-analytics` — plan śledzenia zdarzeń, instrumentacja, zgody RODO, lejki i retencja
  (bramka z ewaluacją: haiku 6/6, sonnet 6/6; bez skilla treść w 3 z 4 scenariuszy też przechodzi — luka mała).
- [x] **A2:** (A2a, A2b i A2c zrobione) wzorce aplikacji biznesowej w `pack-it` (bez osobnej nakładki, decyzja 2026-11-09): A2a skill
  `be-business-app-patterns` (uprawnienia na serwerze, audit log, soft delete, impersonacja, operacje masowe); A2b
  tabele danych i eksport w `fe-architecture` i `be-api-design`; A2c moduł `tf analyze` `authz`.
- [x] **A3:** `eng-repo-readiness` + Developer Experience (devcontainer, `docker compose` dev, `make`/`just`, czas
  od klonu do zielonych testów).
- [x] **A4:** mapa artefaktów (faza → artefakt → kto pisze → skill) w `core-delivery-lifecycle`; ERD w `be-database`.
- [x] **A5:** sekcja „ład danych” w `arch-privacy-compliance` (własność, klasyfikacja, inwentarz PII). Razem z modułem `tf analyze` `data-classification` (decyzja 2026-11-10; plan w A5).
- [x] **A6:** referencja formularzy (React Hook Form + schemat wspólny z serwerem) w `fw-react`.
- [x] **A7:** kolejne moduły `tf analyze` po jednym: `accessibility` (`pack-ux`), `tech-debt`, `i18n`, `observability` (`pack-it`); piętro 0, każdy z zestawami testowymi i bramką, sprawdzony na prawdziwym kodzie.
- [x] **Ewaluacja A3, A4, A5, A9 i zaostrzenie A2a** (2026-11-10, 6,13 USD, zgoda człowieka): `docs/evals/2026-11-10-podsumowanie.md` — A4, A5, A9 z wkładem +100%; A9 po poprawce wyboru skilla; A3 i A2a modele znają bez skilla — bez kolejnych rund strojenia, ewentualnie pomiar procedury przez flow-evals (decyzja człowieka).
- [ ] **Odłożone decyzje (2026-11-10, człowiek: „nie wiem”, limit tygodniowy; (1) rozstrzygnięte 2026-11-23: zostaje fail-open, decyzja właściciela; (3) A8 zmierzone 2026-11-23 za zgodą, haiku, 0,63 USD: `agent-zgaduje-zamiast-pytac` 2/2; `agent-pyta-o-dostepne-dane` 0/2 tylko przez brak wyzwolenia skilla — treść 5/5 grup w obu przebiegach, model zna temat bez skilla (jak A3/A2a); decyzja właściciela: zostaje bez strojenia; (2) scenariusze przebiegu dla A3/A2a rozpisane 2026-11-23: `docs/plans/2026-11-23-scenariusze-przebiegu-a3-a2a.md` — runner `--tasks` i scenariusze pilota gotowe 2026-11-23; pilot czeka na zgodę na koszt):** (1) `tdd_guard` przy własnym błędzie — rekomendacja: zostaje fail-open z wpisem w `.tf/logs/hook-errors.jsonl` i podsumowaniem w `tf doctor`; wrócić, gdy błędy `tdd_guard` zaczną się powtarzać; (2) pomiar procedury A3 i A2a ewaluacją przebiegu (flow-evals) — przy decyzji o pozostawieniu tych skilli; (3) płatne ewaluacje nowych scenariuszy (A8 i dalsze) — po odnowieniu limitu.
- [x] **A8:** `ai-agents` — wzorzec „pytanie o brakującą informację”: najpierw narzędzia i kontekst, potem pauza
  z konkretnym pytaniem do człowieka, zachowany stan i wznowienie (np. interrupt/resume w LangGraph); scenariusz
  ewaluacji, w którym agent ma zapytać, a nie zgadywać.
- [x] **A9:** przegląd specyfikacji przez panel 2–3 niezależnych recenzentów (przeciwnik, operator, wykonawca) przed
  planem w `core-delivery-lifecycle`; raport zbieżne / pojedyncze / rozbieżne, bramka: blokujące i poważne zamknięte śladem.

Sekcja B — architektura agenta i autonomia:
- [x] **B1:** (B1b `tf risk` i B1a polityka w `guard_bash` — zrobione) polityka autonomii `autonomy:` w `.tf/config/config.yaml` (poziomy `full` / `evidence` / `confirm` /
  `deny` dla typów operacji), egzekwowana hookiem, z triażem ryzyka zmian na podstawie diffu (auth, finanse, schemat,
  osłabione testy → człowiek; zależności i dokumentacja przy zielonych testach → automatycznie); najpierw plan kroku
  do akceptacji.
- [x] **B2:** mapa pokrycia generowana z katalogu (zamiast ręcznej macierzy wiedzy), raport informacyjny w CI.
- [x] **B3:** `tf metrics` — odsetek revertów, mediana czasu cyklu, czas przeglądu na PR; okres bazowy 4 tygodnie
  i pasma kontrolne; koszt przyjętej zmiany (z porzuconymi próbami) i pole przyczyny poprawki (luka specyfikacji /
  błąd agenta / zmiana wymagań / nieznana); przed B2.
- [x] **B4:** ewaluacje skilli mierzą wkład: ostrzeżenie w `skill_gate` dla scenariusza zaliczanego bez skilla,
  raport „wkład skilla na model” z istniejących wyników (wejście do core-cost-control); dziennik każdego
  uruchomienia na zbiorze zamkniętym (holdout).

## Prekontrola zlecenia przez Quorum (MCP ci_for_sdlc) — zapisane 2026-11-09
Cel (właściciel): gdy zlecam coś do zrobienia, Quorum (ci_for_sdlc) przez swój serwer MCP wykrywa niejasności,
sprzeczności i braki **zanim** persona zacznie pracę, a fabryka pokazuje je i pyta człowieka. Strona Quorum:
`TODO.md` w dbqm45/ci_for_sdlc („MCP: sprawdzenie zlecenia przed pracą”: narzędzie `check_task` nad `POST /api/check`
dla zlecenia bez klucza; dla TSK-n/CHG-n/klucza Jiry istniejące `get_item_readiness` i `list_decisions`).
- [ ] **Gdzie:** opcjonalnie, działa tylko gdy w sesji jest serwer MCP `ci-sdlc` (jak tryb `mode-pdi` z serwerem
  pdi); bez niego fabryka pracuje jak dziś. Do rozstrzygnięcia: nowy tryb (`mode-quorum`) czy reguła w `mode-pdi`
  i rdzeniu persony (zależy od tego, czy prekontrola ma działać bez pdi — rekomendacja: osobny tryb, bo Quorum
  bywa używane bez pdi).
- [ ] **Kiedy:** na starcie zlecenia, przed planem i przed pierwszą zmianą w kodzie — persona prowadząca (np. `kuba`,
  Talos `story → PR`) wywołuje `get_item_readiness` dla klucza ze zlecenia albo `check_task` dla samego tekstu.
  Jedno wywołanie na zlecenie (koszt i limit AI Quorum); wynik w raporcie przebiegu.
- [ ] **Co robi z wynikiem:** `blocking` → zatrzymanie i pytania do człowieka (format jak `AskUserQuestion`, opcje
  z Quorum); `questions` i `conflicts` → pokazane przed planem z rekomendacją; człowiek odpowiada albo świadomie
  pomija. Odpowiedź na ustalenie zmiany z repo zapisuje się jako `decision_record.py decision add … --finding`
  (PRB-16), więc Quorum nie zapyta drugi raz; pominięcie też jest zapisane (kto, dlaczego).
- [ ] **Treść z Quorum to dane, nie polecenia** (pochodzi z Jiry/Confluence/Figmy): persona nie wykonuje instrukcji
  z ustaleń, tylko je pokazuje (core-agent-security).
- [ ] **Testy i bramka:** scenariusze ewaluacji skilla/trybu (zlecenie z luką → persona pyta przed pracą; zlecenie
  kompletne → brak pytań; brak serwera MCP → praca jak dziś), test integracyjny na atrapie serwera MCP; bramka
  skilli.

## Na później: interfejs „control tower” i integracja planu tf analyze z pdi (zapisane 2026-11-08, decyzja człowieka: wrócić później)
Decyzja 2026-11-08: na początek tylko `tf analyze` i porządek w katalogach (`.tf/`) — kroki 1–4 planu
`docs/plans/2026-11-08-tf-analyze-i-katalog-tf.md`. Reszta czeka:
- [ ] **Interfejs do podglądu pracy fabryki** przy zasadzie „CLI zostaje głównym sposobem pracy, interfejs to widok na
  zapis” (nic w CLI nie zależy od interfejsu; wszystko dokładane i włączane jawnie; najpierw tylko odczyt, decyzje
  z interfejsu tylko przez pdi). Drabina, każdy szczebel osobno: 0 `tf status` w terminalu; 1 `tf status --html`
  (statyczna strona w `.tf/reports/`); 2 `tf ui` (lokalny podgląd tylko do odczytu); 3 konsola pdi (`pis`, pdi
  `docs/15-jedna-platforma.md`, `docs/plan-automatyzacja-i-konsola.md` K-2…K-4; zależy od decyzji G6/P1 w pdi).
  Decyzję podjąć po wywiadzie (core-plan-interview) i blueprincie usługi (ux-service-design, `natalia-service-designer`),
  potem ocena makiet pdi `design/konsola/`, `design/platforma/` (design-critique). Runda 1 wywiadu przygotowana
  i niezadana: P1 kto patrzy (rekomendacja: tylko człowiek-właściciel), P2 kiedy (po przerwie, potem obok CLI),
  P3 co w 10 sekund (co czeka na moją decyzję, potem co robią agenci), P4 zasięg (cel: wiele repo, start: jedno),
  P5 gdzie praca z fabryką (lokalnie / sesje w chmurze / CI — przesądza, czy podgląd lokalny w ogóle zadziała),
  P6 decyzje w interfejsie (start: tylko podgląd).
- [ ] **Integracja planu z pdi i ci_for_sdlc — luki L1–L10** (z przeglądu planu 2026-11-08): L1 dwa źródła prawdy
  (`.tf/register/` i `decisions.md` vs rejestr pdi — przy podłączonym pdi pdi jest źródłem, rejestr to kopia i kolejka
  wysyłki); L2 brak w kontrakcie pdi 0.10.0 typów dla pytań i blokad pętli (`question.raised`/`question.answered`,
  zmiana w 4 repo); L3 brak drogi powrotnej decyzji do sesji lokalnej (`work_events.py sync` przy starcie i w pętli);
  L4 tryb wykonania, gdy człowiek decyduje w przeglądarce (sesja lokalna vs faza w CI / sesja w chmurze); L5 PO
  dubluje ci_for_sdlc (Jira, Confluence, Figma, odpowiedzi z cytatem A2a — ci_for_sdlc jako `po-source`); L6 typy
  ustaleń `tf analyze` vs ci_for_sdlc (GAP, CONFLICT, AMBIGUITY, OUTDATED, MISSING_COVERAGE, DRIFT); L7 powiadomienia
  — pdi ma je już (F5), `notifier` „pdi”; L8 tożsamość decydującego (git config vs konto); L9 wspólna kolejność
  z krokami pdi (K-2, K-3, G6/P1, DA5); L10 hook startu sesji „co czeka na mnie / na człowieka / co wróciło”.
  Uwaga dla kroku 1 planu: format rejestru i ustalenia projektować tak, żeby dało się je później zmapować na kontrakt
  pdi (L1, L2, L6), bez integracji teraz.
- [ ] **Adaptery wychwytywania decyzji w pdi** dla Teams, Confluence, Miro (obok `/record-decision` i
  `/decisions-from` dla Slacka i transkrypcji): szkic z cytatem w skrzynce, zatwierdza człowiek — do TODO pdi przy
  powrocie do tematu.

## Plan 3.1.0 — nowe możliwości Claude Code i zalecenia z dokumentacji

### PR 1: generowani agenci, hooki, bezpieczeństwo, ewaluacje
- [x] **A. Zagnieżdżanie podagentów** (domyślnie 3 poziomy od Claude Code v2.1.219, `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`;
  fabryka ustawia 2): poprawiony `docs/insights.md`; wykonawca ma `Agent` i tabelę konsultantów innych nakładek;
  konsultanci z `disallowedTools: Agent`.
- [x] **B. Pola generowanych agentów:** `isolation: worktree` jako opcja persony (tylko wykonawcy, którzy edytują
  pliki; worktree odgałęzia się od gałęzi domyślnej, nie od HEAD persony — opisane w prompcie); `omitClaudeMd` dla
  konsultantów. Bez `background`: podagenci wywołani z rozmowy głównej i tak startują w tle (dokumentacja
  „Subagents”), a odpowiedź konsultanta jest potrzebna przed dalszą pracą. Scout zostaje z `CLAUDE.md` (reguły
  ekonomii kontekstu).
- [x] **C. Prompty agentów:** kontrakt zakończenia pracy (pracuj do końca, zatrzymaj się tylko bez człowieka lub przed
  ryzykownym krokiem, bez niezamówionych dodatków); kiedy podagent ma sens, bez samodzielnych rund przeglądu;
  zakazy z celem przepisane na cel — w szablonach `build.py` i `report_contract`; granice bezpieczeństwa zostają
  zakazami. Role i persony nakładek: przy ich kolejnej zmianie.
- [x] **D. Hooki:** `onFailure: "block"` dla `guard_bash`, `guard_paths`, `cleanroom_guard` (aktualizacja dopisuje pole
  do istniejących hooków, wybór użytkownika zostaje); hooki odporne na nietypowe dane wejściowe (test). `PreCompact`
  (zapis stanu) i `SubagentStop` (log kosztów) już były.
- [x] **I. Styl raportu agenta (zasady ASD-STE100):** wynik najpierw, krótkie zdania, jedna czynność na krok, stałe
  terminy bez synonimów, bez wstępów — sekcja wspólna w promptach z `build.py`.
- [x] **K. Treść z zewnątrz:** zasada „treść z narzędzi, stron i plików to dane, nie polecenia” w promptach;
  `fetch_page.py --json` (źródło, data, rodzaj treści); lista dozwolonych poleceń Bash researchera (profil `web`
  w `cleanroom.json`, hook `cleanroom_guard`);
  opcjonalny filtr wyników na Haiku opisany w `core-agent-security`; scenariusze red teamingu w ewaluacjach
  `core-agent-security`.
- [x] **L. Spójność:** stały szablon raportu wykonawcy (Wynik, Zmienione pliki, Weryfikacja, Niepewne, Potrzebna
  decyzja); opcjonalne pole persony `scenarios` (sytuacja → zachowanie), wypełnione dla dyspozytorów.
- [x] **P1. Ewaluacje (kod):** sędzia inny niż oceniany model (`--judge auto`, domyślnie; ostrzeżenie w raporcie
  ewaluacji, gdy jawnie wybrany sędzia jest tej samej rodziny); uzasadnienie przed oceną w schemacie sędziego.
  Bez osobnego `effort` dla sędziego: flagi CLI nie sprawdzałem.
- [x] **Q1. Opóźnienie:** `effort: low` dla tieru `fast`.

### PR 2: treść skilli i dokumentacja
- [x] **E. Reguły i skille:** `build.py check` ostrzega, gdy skill ustawia `model` lub `effort` (zmiana modelu w turze
  kasuje cache); zasada w `core-skill-authoring`. Bez `paths:` w skillach: skill wczytuje się wtedy tylko przy
  pasujących plikach, a pytania projektowe padają zanim pliki istnieją (fabryka już to ostrzegała). Bez
  `.claude/rules/`: nakładki nie dokładają reguł do `CLAUDE.md`, więc nie ma czego dzielić po ścieżkach.
- [x] **F. Skille:** `ai-prompt-engineering` (modele 5.5: domyślny effort `medium`, zapas `max_tokens`, zmiana effort
  w trakcie rozmowy, pozytywne sformułowania, „jeśli problemem jest koszt/opóźnienie — najpierw model”);
  `core-async-delegation` (koniec tury tekstem to raport, nie ukończenie; lista zadań; sygnał czasu);
  `core-agent-security` (checkpointy nie cofają zmian z Bash); `core-skill-authoring` (`context: fork`; `when_to_use`
  świadomie pominięte — dokleja się do opisu i zjada budżet listy skilli).
- [x] **H. `core-grounding`:** weryfikacja cytatami po napisaniu tekstu (usunięte twierdzenia jako `[]`); tryb
  „tylko z dostarczonych materiałów” (`sources_only_note`: konsultanci zawsze, role z `grounding: sources-only` —
  ddd-analyst, product-compliance, ai-governance, ev-compliance); best-of-N i iteracyjne doprecyzowanie dla decyzji
  trudnych do odwrócenia.
- [x] **I2. Procedury w duchu STE:** `docs-tech-writing` (STE100 dla dokumentacji po angielsku); uzgodnienie
  z `txt-polish-style` (w procedurach wygrywa stały termin).
- [x] **J. Forma wyniku:** `core-problem-routing` — tabela/diagram (Mermaid)/jednorazowy HTML/tekst; katalog
  `.claude/scratch/` w `.gitignore`; zasady bezpieczeństwa takich stron.
- [x] **M. Wyciek promptu:** zasada „bez sekretów w promptach” w `core-agent-security`; kolejność monitoring →
  utrudnianie w `sec-llm-security`.
- [x] **N. Wbudowany skill `claude-api`:** podział ról z `eng-llm-features` i `ai-prompt-engineering` (fakty o API
  Claude → `claude-api`); odesłania w opisach; usunięcie starzejących się faktów; `core-skill-authoring`: sprawdź
  skille wbudowane przed nowym skillem.
- [x] **P2. Ewaluacje (skille):** typ scenariusza `edge` w `core-skill-authoring`; kryteria SMART, sędzia inny niż
  model, rozumowanie przed oceną, przypadki brzegowe, liczba przypadków ponad ręczną ocenę w `ai-evals`.
- [x] **Q2. Opóźnienie:** lista kontrolna w `eng-llm-features` (pomiar bazowy i TTFT → model/effort → długość →
  cache → strumieniowanie). `ai-product-management` miał już TTFT (p50/p95 do pierwszego i ostatniego tokenu).
- [x] **G. Wydanie:** `workspace.py matrix` i `refs`, PR. Wersję i wpis CHANGELOG liczy workflow `release` z Conventional
  Commits po scaleniu (minor za każdy PR z `feat`).

## Talos — tryb „story → PR” na żądanie

Decyzje człowieka (2026-10-21): nazwa Talos; `--auto` pomija zatwierdzenie planu; jedna historyjka = jeden PR,
kawałek planu = osobny commit; katalog przebiegów zapisywany, ale ignorowany przez git; bez domyślnego budżetu —
zawsze najtańszy wystarczający model i najmniej pracy; `--budget` opcjonalny jako twardy STOP.

- [x] **T1. Raport przebiegu** `factory/run_report.py` (TDD): `start` zakłada `.claude/runs/<data>-<slug>/`
  (run.json, story.md, plan.md, parked.md); `finish` sumuje transkrypty sesji i podagentów od startu — czas, tokeny
  (wejście, wyjście, odczyt i zapis cache 5 min / 1 h), koszt wg cennika z `config.yaml`, modele i agenci — i pisze
  `report.md`. Liczy skrypt, nie model.
- [x] **T2. Ignorowanie** `.claude/runs/` (instalator: `info/exclude` i `.gitignore` trybu `--shared`).
- [x] **T3. Skill procesowy `core-story-run`** (tylko ręcznie): przyjęcie story, plan z pionowych kawałków (INVEST,
  każdy kawałek scalany i działający), pętla kawałka (test czerwony → kod → weryfikacja → przegląd zakresu → commit),
  przypadki brzegowe do `parked.md`, fazy warunkowe, STOP, PR, raport. Najpierw scenariusze ewaluacji.
- [x] **T4. Agent `talos`** (`claude --agent talos`, tylko ten tryb) i agent `scope-reviewer` (przegląd diffu względem
  planu w świeżym kontekście: kod spoza zakresu → wycofanie i wpis w `parked.md`). Talos czyta skill plikiem: skilla
  z `disable-model-invocation` nie da się wczytać przez `skills` (dokumentacja „Subagents”). Agenci sesji głównej
  (`main_only`) nie dostają `maxTurns` — jak persony.
- [x] **T5. Dokumentacja** (`docs/insights.md`), bramka skilla, `workspace.py matrix` i `refs`, PR.

## Tryby (`modes/`) — trzeci rodzaj elementu fabryki

Decyzje człowieka (2026-10-21): katalog `modes/` i identyfikatory `mode-*`; Talos jako `mode-talos`, instalowany
domyślnie; zmiana nazwy skilla jako MAJOR. Tryb to technicznie nakładka (ten sam `pack.yaml`, loader, instalacja
w `factory/packs/<id>/`) z polem `kind: mode`; różni się katalogiem źródłowym i przeznaczeniem: sposób pracy
włączany na żądanie (agent sesji głównej, skill procesowy, skrypty, testy, przewodnik).

- [x] **M1. Katalog `modes/`** w instalatorze, aktualizatorze, `tf list`, `tools/workspace.py` (refs, sync-gate,
  matrix) i CI; walidacja: `kind: mode` ↔ `mode-*` w `modes/`, nakładki `pack-*` w `packs/`.
- [x] **M2. Nowe domyślne przy aktualizacji:** domyślna nakładka lub tryb, których projekt nigdy nie dostał
  w ofercie, dochodzą przy `tf update`; świadomie usunięte nie wracają (manifest: `offered`).
- [x] **M3. `mode-talos`:** agent `talos`, skill `talos-story-run` (było `core-story-run`, wpis w `migrations.py`),
  `run_report.py` jako skrypt skilla, testy, scenariusze, przewodnik `GUIDE.md` (było `docs/talos.md`).
  W rdzeniu zostają `scope-reviewer` i ignorowanie `.claude/runs/`.
- [x] **M4. Zgodność wersji:** zakres `requires.core` nakładek obejmuje 5.x; dokumentacja (`insights.md`,
  `PUBLIC_API.md`), bramka, `matrix`, `refs`, PR jako MAJOR.

## Workflows (`.claude/workflows/*.js`) — audyt kodu i symulacja ES

Decyzja człowieka (2026-10-21): zacząć od workflows dla `eng-code-audit` i symulacji Event Stormingu.

- [x] **W1. Instalacja:** katalog `workflows/` nakładki lub trybu → `.claude/workflows/` (test instalatora).
- [x] **W2. `pack-it/workflows/code-audit.js`** (`/code-audit`; nazwa inna niż skill `/eng-code-audit`): argumenty = zakres zatwierdzony przez człowieka (data, wymiary,
  głębokość, limit wykonawców, moduły, wyłączenia); etapy: inwentarz (haiku) → przeglądy równoległe (wymiar →
  wykonawca, model wg głębokości) → scalenie i ranking w kodzie (bez modelu: duplikaty po `plik:linia`, ryzyko ×
  zasięg ÷ koszt, blokery, hipotezy bez dowodu) → raport. Wymiary bez zainstalowanych skilli pomijane z logiem.
  Test: skrypt uruchamiany w Node z atrapami `agent`/`parallel`/`pipeline` (bez modelu, bez kosztu).
- [x] **W3. Skill `eng-code-audit`:** po zatwierdzeniu zakresu uruchamiasz workflow; ręczny przebieg zostaje jako
  wariant bez workflow. Bramka skilla.
- [x] **W4. Symulacja ES:** ocena — workflow nie pasuje. Sesja jest interaktywna (człowiek prowadzi każdą rundę),
  a workflow nie przyjmuje danych w trakcie. Runda już wywołuje uczestników równolegle, a skrypt nie ma powłoki
  dla `es_sim.py`. Możliwe później, za zgodą: próba scenariusza (sprawdzenie nowego scenariusza automatem
  z gotowymi wypowiedziami facylitatora).
- [x] **W5. Dokumentacja** (`insights.md`, `PUBLIC_API.md`), matrix, refs, PR.

## Agent teams (`mode-team`) i przewodnik użytkownika

Decyzje człowieka (2026-10-21): agent teams jako tryb `mode-team`, opt-in (nie domyślny); przewodnik i FAQ
instalowane do projektu (`factory/`), bez README w korzeniu repo.

Fakty (code.claude.com/docs/en/agent-teams, odczyt 2026-10-21): eksperymentalne, włączane
`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` (`env` w ustawieniach); tylko sesja interaktywna (`-p` nie tworzy zespołu);
po włączeniu podagent nazwany przez Claude startuje jako członek zespołu; członek zespołu **nie dostaje `skills`
z pliku agenta**; jeden zespół na sesję, bez zagnieżdżania, bez wznawiania (`/resume`); 3–5 członków; koszt
liniowy i znacznie wyższy niż subagentów; uprawnienia jak u prowadzącego.

- [x] **A1. Przełącznik** `team_switch.py on|off|status` (TDD): zmienna w `env` w `.claude/settings.local.json`
  (osobista decyzja, także przy instalacji zespołowej); `off` usuwa wpis, reszta ustawień nietknięta.
- [x] **A2. Skill `team-session`** (tylko ręcznie, `/team-session`): bramka kosztu, zespół czy subagenci, skład
  z wykonawców persony, skille do wczytania w poleceniu startowym (bo `skills` nie działa), własność plików,
  wspólna lista zadań, zamknięcie i wyłączenie flagi; scenariusze, bramka.
- [x] **A3. `modes/mode-team/`**: `pack.yaml` (`kind: mode`, `default: false`), `settings.json` (uprawnienie
  skryptu), `GUIDE.md`, testy; CI matrix; `insights.md`, `PUBLIC_API.md`; PR.
- [x] **P1. Przewodnik i FAQ** w `core/guide/` → `factory/GUIDE.md`, `factory/FAQ.md` (test instalatora);
  treść ze stanu bieżącego (polecenia `tf`, persony, nakładki, tryby, workflows, koszty, hooki, aktualizacje);
  fakty sprawdzone w plikach; PR.

## Event Storming prowadzony przez fabrykę

Prośba człowieka (2026-10-21): fabryka ma umieć przeprowadzić Event Storming; wziąć z artykułów to, co pasuje,
bez budowania „super narzędzia”. Źródła:
- M. Bentley, „Building an Agentic AI Platform to Facilitate Event Storming Sessions” (Medium, 12.10.2026);
- JIN, „Domain-Driven Design: Using Event Storming and Context Mapping to Draw Precise Boundaries” (Medium, 10.05.2026).

Bierzemy:
- fazy z kryteriami wyjścia, a reguły tylko bieżącej fazy;
- facylitator pyta, nie podaje odpowiedzi: jedno pytanie albo jeden mały ruch na turę;
- tablica jako dziennik zdarzeń z cofnięciem;
- ekspert domeny tylko do odczytu i przegląd fazy w świeżym kontekście;
- bramka człowieka przy agregatach i mapie kontekstów (błędy modelu kumulują się w późnych krokach);
- typy subdomen i wzorzec na każdej strzałce mapy.

Nie bierzemy: autonomicznego zegara (30 s / 3 min), interfejsu tablicy ani konfiguracji agentów per tablica.

- [x] **E1. `ddd-event-storming/scripts/es_board.py`** (TDD), zero tokenów:
  - dziennik `board.jsonl` (append-only), polecenia `init`, `add`, `edit`, `remove`, `phase`, `undo`, `show`
    (Markdown wg `board-template.md` + Mermaid) i `check`;
  - `check` sprawdza strukturę według fazy: typy kartek dozwolone w fazie (mieszanie poziomów), zdarzenie bez
    wyzwalacza, komenda bez zdarzenia, polityka bez „kiedy”/„wtedy”, komenda bez agregatu, duży agregat, agregat
    bez kontekstu, kontekst bez typu subdomeny, relacja bez wzorca mapy, otwarte hot spoty.
- [x] **E2. `references/agent-phases.md`:** 5 faz (kontekst sesji, zdarzenia, komendy i polityki, agregaty, podział
  na konteksty i mapa). Dla każdej fazy: cel, dozwolone kartki, ruchy facylitatora, kryterium wyjścia, bramka
  człowieka, przegląd, typowe błędy. Do tego protokół tury.
- [x] **E3. `SKILL.md` §7** przepisany na prowadzenie sesji ze skryptem i kartami faz; ekspert domeny i przegląd
  jako wykonawcy tylko do odczytu; uprawnienie dla skryptu w `pack-it/settings.json`.
- [x] **E4.** Scenariusze ewaluacji, bramka skilla, `insights.md`, matrix, `refs`, PR.

## DDD — zaawansowane modelowanie (część 3)

Prośba człowieka (2026-10-21): zebrać zagadnienia DDD i uzupełnić skille DDD o brakujące
elementy na podstawie sprawdzonych źródeł (Evans 2003, Fowler „Analysis Patterns”, Arlow i Neustadt 2004,
PLoP, GoF, martinfowler.com).

Analiza luk: każdy temat programu porównany ze skillami, z dowodem `plik:linia`. Już pokryte i bez zmian:
- Being/Behaving/Becoming;
- Party z rolami i relacjami;
- model dostępności (Availability);
- oddzielenie złożonej logiki od CRUD;
- sagi;
- łańcuch zobowiązań (Chain of Responsibility).

Każda zmiana skilla zaczyna się od scenariusza ewaluacji (core-skill-authoring), a kończy bramką.
- [x] **D1. ddd-deep-modeling:** jedno źródło prawdy jako technika rozplątywania; ukryte powiązanie wiele do wielu
  (pojęcie do nazwania); status to nie mechanizm rozszerzania; dwa poziomy modelu (Knowledge i Operations Level).
- [x] **D2. ddd-tactical-design + `references/dynamic-rules.md`:**
  - polityki jako funkcje, ich kompozycja w łańcuchy i drzewa, fabryka polityk, dekorator polityki;
  - reguły zmienne w czasie (wersja polityki jako nowa klasa wybierana datą) i reguły zależne od historii zdarzeń;
  - scoring;
  - agregat jako maszyna stanów.
- [x] **D3. ddd-archetypes:**
  - `product.md`: kanał dystrybucji; PIM a Inventory; poczekalnia importu;
  - `document.md`: obieg a redagowanie dokumentu;
  - `agreement.md`: oferta to nie zamówienie, zakup to nie zamówienie;
  - `SKILL.md`: warstwy odpowiedzialności (Evans) z atrybucją.
- [x] **D4. eng-design-patterns:** Role Object i Extension Object (`references/beyond-gof.md`, wiersze w tabeli objawów).
- [x] **D5. be-api-design:** model dojrzałości Richardsona; dokument REST jako komenda.
- [x] **D6. arch-multi-tenancy:** wersja zachowania i API per najemca; wybór handlera komendy po tenantId.
- [x] **D7.** Bramki zmienionych skilli, `refs`, matrix, PR.

### Na później (decyzja człowieka)
- [x] Instalator przepisuje `tests/` → `.claude/tests/` także w przykładach skilli (np. komentarze ścieżek
  w `tool-pytest/references/examples.md`), gdzie chodzi o testy projektu, nie fabryki.
- [x] ~~Nakładki jako pluginy Claude Code (eksport).~~ **Decyzja człowieka (2026-10-21): nie robimy** — tryby
  i nakładki zostają instalowane przez `tf`. Ograniczenia: agenci z pluginu ignorują `permissionMode`, `hooks`,
  `mcpServers`, `initialPrompt`; plugin nie wczytuje `CLAUDE.md`; `settings.json` pluginu przyjmuje tylko `agent`
  i `subagentStatusLine`; nazwy z przedrostkiem (`pack-it:jan`); brak składania wkładów nakładek. Zależności:
  `dependencies` w `plugin.json` z zakresami semver rozwiązywanymi po tagach `<plugin>--v<wersja>`.
  Analiza: `docs/plugins.md` (2026-10-21) — rekomendacja: eksport `mode-talos`, nakładki później (tylko skille),
  rdzeń nie.
  - [ ] **Warunek ponownego rozważenia (zapisane 2026-10-29, artykuł „Stop Shipping Individual MCP Servers. Start
    Shipping Agent Plugins”, A. Tkachuk, 2026-08-30):** otwarta specyfikacja Agent Plugins 1.0 (sierpień 2026,
    Vercel, Amazon, Anysphere, Microsoft, OpenAI, Google) ma przenośny rdzeń tylko ze skilli i konfiguracji MCP;
    według artykułu obsługują ją VS Code / Copilot, Codex, Cursor, Kiro, a Claude Code ma własny format
    [niezweryfikowane — sprawdzić specyfikację i listę klientów z datą]. Wracamy do decyzji, gdy zespół używający
    fabryki pracuje też w Copilocie lub Codexie: eksport samych skilli nakładki (rdzeń nadal nie, bo `CLAUDE.md`,
    hooki i uprawnienia nie są przenośne) oraz `mode-pdi` jako pakiet „skill `pdi-decisions` + serwer MCP pdi”.
    Ten sam przegląd co dla każdej zależności (`core-agent-security`: plugin może uruchamiać lokalny MCP z
    uprawnieniami maszyny; zainstalowany ≠ autoryzowany ≠ włączony).
    Sprawdzone 2026-10-29 (anthropic.com/news, 2026-10-22): standard Agent Skills (nazwa, organizacja GitHub,
    agentskills.io) przekazany Agentic AI Foundation pod Linux Foundation — ta sama fundacja co MCP; ponad 70 platform
    (m.in. ChatGPT, Cursor, GitHub Copilot, VS Code), plan: wersjonowane wydania, proces propozycji, wytyczne
    bezpieczeństwa dla autorów i instalujących skille. To wzmacnia argument za eksportem samych skilli nakładek
    (format przenośny bez osobnego standardu pluginów) — warunek: zgodność ze specyfikacją (pozycja „Zgodność skilli
    ze specyfikacją Agent Skills” niżej) i wytyczne bezpieczeństwa AAIF, gdy się ukażą.
- [x] Agent teams (eksperymentalne, tylko sesje interaktywne) jako opcjonalny kanał rozmowy person — tryb `mode-team` (A1–A3).
- [x] Workflows (`.claude/workflows/*.js`) dla `eng-code-audit` i symulacji Event Stormingu — sekcja „Workflows”.
- [x] Target `managed-agents` (Claude Managed Agents, `ant apply`) w `build.py` — zrobione 2026-10-24: `core/factory/target_managed.py`, plan `docs/plans/2026-10-24-target-managed-agents.md`; pliki sprawdzone `ant apply --dry-run` (ant 2.3.0, bez konta).
- [x] Pomiar skilli na modelu (płatny, za zgodą człowieka), 2026-10-22: partie 1–6 (wszystkie scenariusze, Haiku,
  z porównaniem bez skilli), zaostrzenie kryteriów, poprawki opisów i treści, przegląd 143 scenariuszy
  nierozróżniających, skrócenie 26 skilli — wyniki i decyzje w `docs/evals/2026-10-22-pomiar-haiku.md`.
- [x] Izolacja przebiegu „bez skilli” w `core/tests/run_skill_evals.py` — zrobione 2026-10-23: przebieg bez skilli
  startuje z `--restricted` (dokumentacja CLI, odczyt 2026-10-23: narzędzia plikowe tylko w katalogach roboczych, bez
  Bash, bez ustawień użytkownika i projektu; Claude Code ≥ 2.1.248), a runner zapisuje ścieżki narzędzi plikowych
  i odczyt poza katalogiem testu oznacza jako błąd przebiegu (`outside_reads`); test z atrapą `claude`. Pierwotny opis: model w przebiegu bez skilli może czytać dysk
  poza katalogiem testu i znaleźć pliki fabryki (2 z 607 przebiegów w pomiarze 2026-10-22). Zrobić przed pomiarem na
  Sonnecie lub Opusie albo przed uruchomieniem pomiaru poza kontenerem z czystym dyskiem: odciąć przebieg od reszty
  dysku (np. osobny HOME i katalog roboczy, blokada odczytu poza workspace) i dopisać test, który to sprawdza (TDD).
- [x] `test_fetch_page` (render Chromium) przekraczał 60 s w CI — 5 jobów. Przyczyna (pomiar w PR #12): pierwszy
  start Chromium na runnerze trwa 16–27 s (zimny dysk), kolejne ok. 0,7 s, niezależnie od flag i D-Bus; pod obciążeniem
  zestawu testów pierwszy start przekraczał limit. Naprawa: krok „Rozgrzanie Chromium” w CI przed testami; timeout
  podaje teraz linię stderr przeglądarki.
- [x] Próba scenariusza symulacji ES: `es_probe.py` z gotowymi wypowiedziami facylitatora (`trial.json`), bez gospodarza;
  wersja pełna na scenariuszu weterynaria: 1,44 USD, 10/10 oczekiwań — `docs/evals/2026-10-25-es-proba-scenariusza/` (2026-10-25).

## Tłumaczenie treści fabryki na angielski

**Cel (decyzja właściciela, 2026-11-17):** jak w samym Claude — cała fabryka po angielsku (nazwy, klucze, wartości,
skille, persony, prompty, komunikaty, składnia planu i specyfikacji), a rozmowa w języku człowieka: piszesz po
polsku, odpowiedzi i dokumenty dla Ciebie są po polsku (`tf language`), model dostosowuje się sam. Jedna wersja
treści (angielska), bez równoległej polskiej.

- [x] Etap 1 — nazwy plików i katalogów (#286).
- [x] Etap 2a–2b — klucze metadanych skilli i modułów, poziomy ważności (#287); pytanie niżej o pola metadanych
  rozstrzygnięte: po angielsku.
- [x] Etap 2c — stan zadania, pętla, profile, kody STOP, migracja danych projektu (#288, wydanie 11.0.0).
- [x] Etap 2d — wymiary, głębokość i blokery audytu kodu (oraz nazwy plików `code-audit*.md`), pola wpisu dziennika
  decyzji pdi (`sent`, `date`, `by`, `kind`, `why`, … z migracją `decisions.md`), `description` zamiast `opis`
  (`control_band`, `metric_watch`, scenariusz ES; poprawka listy profili po #288), schemat przeglądu AI w CI
  (`verdict`, `findings`, `APPROVED|NEEDS_ATTENTION|REJECTED`, `critical|major|minor`), werdykty `readiness_check`
  i `tf onboard`, flaga `profile.py --team-only`.
- [x] Etap 2e — werdykty kontroli: `pr_budget` (`OVER`), `instructions_lint` (`OK|WARN|ERROR`, identyfikatory kontroli
  `length`, `blocks`, `intents`, `order`, `imports`, `stale`, klucze trybu `--root`), `claims_check`
  (`OK|WARNINGS|ERRORS`), `dossier_check` (`ERRORS`), `tf analyze` (`ERROR|NEEDS_FIX|OK`, bramka `FAILED`, rejestr
  `open|resolved` z migracją `items.jsonl`), `facts.py` (`confirmed|partial|unconfirmed|contradicted|skill-source`),
  rodzaje kart `recon_cards`. Flagi CLI były już po angielsku.
- [x] Etap 3a — plan i specyfikacja: kawałki `S<n>`, pola `files:`, `criteria:`, `verify:`, `after:` (`none`), `tier:`,
  stopka commita `Slice S<n>:`, katalog prób skanu `attempt-<k>`; specyfikacja `Given / When / Then`, sekcje
  `Acceptance criteria`, `Unchanged`, `Out of scope`, `Open questions`, znacznik `[blocking]`; status pliku zadania
  `draft|approved`, stan kawałka `unverified`, dowód śladu `no-test|no-evidence`. Skrypty przyjmują dawną składnię przez
  wydania 14.x; migracja przepisuje `spec.md`/`plan.md` otwartych zadań i przelicza skróty zatwierdzeń.
- [x] Etap 3b-1 — linie wyników skanu (`GATE S<n>: PASS|FAIL (…, attempt k/2)`, `COOLDOWN:`, `SCAN:`); raport
  rekonstrukcji: sekcje `Modules`, `Domains`, `Requirements`, `Rules`, `Standards`, `Risks`, `Questions`, `Not checked`,
  wiersze stacku `Language`, `Data`, `Tests`, `Configuration`; karty modułów (`<!-- card: … -->`, `Entry points`,
  `Dependencies`, `Data`, `Rules`, `Terms`, `Deviations`, `Unknowns`, `(confidence: …)`, `(details: …)`), `rules.md`
  (`Cross-cutting rules`). Polskie nagłówki przyjmowane przez 14.x (aliasy w `recon_check`, `recon_cards`,
  `recon_refresh`, `recon_export`).
- [x] Etap 3b-2 — dossier legacy po angielsku: sekcje indeksu, kart, oceny i rekomendacji, `State: green|yellow|red`,
  tabela `ID | Rule | Evidence | Confidence` (`test|code|to verify`), pola ustaleń (`Area`, `Category`, `Gap`, …)
  i rekomendacji (`Addresses`, `Decision`, …), kategorie i szczeble decyzji; dawne polskie nazwy przyjmowane, migracja
  przepisuje istniejące dossier; etykiety decyzji przeglądu `PENDING|FIXED|SKIPPED|RISK_ACCEPTED|REJECTED|LESSON`.
- [x] Etap 3b-3 — dziennik projektu: lekcje `**reguła** — Context: … · Instead: … · Applies to: …` pod nagłówkiem
  `## Execution and verification` (kategorie po angielsku), tagi banku dowodów `[mention]`, `[superseded by …]`,
  `[unverified]`, werdykty tabel weryfikacji słowem (`confirmed|partial|unconfirmed|contradicted`), nazwy plików
  w `docs/project/` (`plan-review`, `impl-review`, `operations-review`, `tech-debt`, `readiness`, `repo-readiness`,
  `legal-map`, `deep-dives`, `dry-run`, `language-<dokument>`). Dawne formy przyjmowane. Znaczniki
  `[założenie]`/`[niezweryfikowane]`/`[pytanie]` (core-grounding) — razem z etapem 4.
- [x] Po wydaniach 14.x — usunięcie dawnej składni z parserów (zrobione w 4k, #336; dawne formy czyta już tylko `migrations.py`) (`K<n>`, `pliki:`, Zakładając/Gdy/Wtedy, polskie
  nagłówki rekonstrukcji).
- [x] Język rozmowy bez ustawień (decyzja właściciela, 2026-11-17: „bez żadnej konfiguracji, jak w Claude”, #290):
  stała reguła rozmowy, język commitów z `git log`, bez `tf language`, `tf commit-language` i `--language`.
- [ ] Etap 4 — tłumaczenie treści: skille, persony, prompty, komunikaty po angielsku; język odpowiedzi wynika z rozmowy.
  Decyzje właściciela (2026-11-17): słowa kluczowe skilli PL+EN (podpowiedź bez modelu), tłumaczenie etapami w sesji
  (bez równoległych wykonawców). Metoda na partię: treść, description i catalog po angielsku (`Use when/for …`,
  `Not for …`), `keywords` po polsku i angielsku (wyrażenia z pytań), bramka (`skill_gate.py`: krok 3 trafność, krok 5
  rozpoznaje język), pomiar `tools/hint_holdout.py` przed i po partii. Punkt odniesienia (all, 2026-11-17): strojenie
  902/918, holdout 29/43.
  Zakres (decyzja właściciela, 2026-11-18: „Tłumaczymy wszystko”): całe repo, także `docs/`, komentarze w kodzie,
  komunikaty testów, persony i role, na koniec polskie aliasy w czytnikach. Wyjątki dla skuteczności: polskie prompty
  scenariuszy eval zostają, a obok dochodzą angielskie odpowiedniki (pokrycie obu języków); w pack-editorial-pl
  opisy i procedury po angielsku, reguły polszczyzny i przykłady zdań po polsku (to ich przedmiot); `hint.pl.txt`
  i polskie słowa kluczowe zostają z założenia.
  Skuteczność fabryki nie może spaść (właściciel, 2026-11-17). Każda partia przechodzi, zanim trafi do PR:
  1. `tools/translation_check.py <pliki>` — te same bloki kodu, `…`, liczby, odnośniki i struktura co przed
     tłumaczeniem (różnica = zgubiony albo dopisany fakt; zmiana treści to osobny commit, nie tłumaczenie);
  2. podpowiedzi: `python3 tools/hint_pl_index.py <skille>` (polski indeks `hint.pl.txt` z ostatniej polskiej
     wersji — decyzja właściciela 2026-11-17: polskie polecenia trafiają jak przed tłumaczeniem; hook dokłada go do
     treści, model go nie czyta), potem `hint_holdout.py` — strojenie i holdout nie niżej niż przed partią; bramka każdego skilla;
     to samo w instalacji `none` (sam rdzeń) i `test_skill_evals.py` tam — polecenia ogólne bez podpowiedzi
     (słowo pospolite w słowach kluczowych zyskuje wagę, gdy polska proza znika z innych skilli; 4b-2: „jaka wersja”);
     `skill_gate.py --hints` w każdej instalacji (all, pack-it, none, pozostałe nakładki): każdy scenariusz strojenia
     trafia — przesunięte wagi słów zrzucają pojedyncze skille niezmieniane w partii (4b-3: eng-clean-code, eng-testing);
  3. model (zgoda właściciela: próbka z partii, Haiku, ~2 USD): 3–5 skilli o największym ruchu, scenariusze przed
     i po tłumaczeniu (`run_skill_evals.py --models haiku`); spadek → poprawka przed PR;
  4. pełna macierz `workspace.py check` w CI.
  - [x] 4a — fabryka gotowa na angielską treść (reguły wyboru i granic w obu językach w `build.py`, `skill_audit`,
    `skill_hint`; język treści w bramce), pilot `core-stack-sync`, narzędzie `hint_holdout.py`.
  - [ ] 4b — rdzeń: pozostałe skille `core-*` i `tf`, cechy, `config.yaml` (prompty, notatki), przewodniki.
    - [x] 4b-1 (2026-11-17): `core-teaching-workspace`, `core-skill-composition`, `core-plan-interview`, `core-semver`.
      Podpowiedzi przed/po: partia 17/17 → 17/17 (plan-interview straciło trafienie „za dużo pytań” — słowa kluczowe),
      całość 902/918 · 29/43 bez zmian. Haiku przed/po (plan-interview, skill-composition): 8/8 → 8/8, ~$2,36.
      `translation_check`: blok bez języka to przykład wyjścia (proza). Uwaga przy łamaniu wierszy: nazwa nakładki
      i skill z niej muszą być w jednym wierszu (`workspace.py refs`).
    - [x] 4b-2 (2026-11-17): `core-factory-update` (+ przykłady), `core-agent-retro`, `core-source-research`,
      `core-problem-routing`. Podpowiedzi: po tłumaczeniu 18/23 (retro: okno i pamięć automatyczna; routing: decyzja
      trudna do odwrócenia; research: sprzeczne źródła, nieistniejące funkcje) → słowa kluczowe PL+EN → 23/23; całość
      902/918 · 29/43 bez zmian. Haiku przed/po (routing, research): 9/11 → 11/11 (jeden przebieg — „bez spadku”, nie zysk), $3,68 — ponad
      uzgodnione ~2 USD; kolejne partie: próbka ≤ 7 scenariuszy na stronę. Z katalogu `core-factory-update`
      zniknęła nieaktualna „zmiana języka pracy i commitów” (od #290 bez ustawień).
    - [x] (2026-11-22: `--decide` i `Rework-Cause:` już po angielsku; sygnał tieru zapisywany jako `too low`/`too high`,
      dawne wartości i klucze retrospektyw czytane dalej) składnia danych retrospektywy wciąż po polsku (etap 3): decyzje `--decide KLUCZ=tak|nie|później`,
      `Rework-Cause:` (`luka-specyfikacji|blad-agenta|zmiana-wymagan|nieznana` — też `metrics.py`), sygnał
      „Tier: za niski/za wysoki” w raportach wykonawców — angielskie wartości z aliasami, jak w 3a.
    - [x] 4b-3 (2026-11-17): `core-grounding`, `core-knowledge`, `core-conventional-commits` (+ referencje),
      `core-async-delegation` (+ referencje). `core-project-record` przesunięty: `project_record.py` czyta polskie
      nagłówki artefaktów (`## Przekazanie`, „Otwarte pytania”, tabela TL;DR) — najpierw zmiana składni z aliasami
      i migracją (jak 3a), potem tłumaczenie skilla i szablonów.
      Oznaczenia rzetelności po angielsku: `[assumption]`, `[unverified]`, `[question]`, `[checked: …]`, `[assessment]`;
      `claims_check`, `freshness`, `grounding_check` („(new)”, „(planned)”), `recon_check` (pack-it) przyjmują oba języki.
      Polski indeks podpowiedzi: po tłumaczeniu holdout partii spadł 6/8 → 2/8 (słowa kluczowe dały tylko 2/8) →
      `hint.pl.txt` dla 13 przetłumaczonych skilli (`tools/hint_pl_index.py`, test `tests/test_hint_pl_index.py`,
      hook: `core/tests/test_skill_hint_pl_index.py`); hook wycina też `## Sources`. Wynik: all 899/918 · 31/43 (przed
      partią 902 · 29; bez indeksu 900 · 25), none 167/175 · 16/16 (przed 169 · 15). Strata strojenia to pojedyncze
      no-trigger w niezmienionych skillach (przesunięte IDF), zysk holdoutu — polskie polecenia jak przed tłumaczeniem.
      Spis treści plików referencyjnych w języku pliku (`build.py`: „Contents” / „Spis treści”, oba rozpoznawane).
      Haiku: przed 11/11; po 5/6 (`wynik-skryptu-to-twierdzenie` bez wywołania skilla) + powtórka 2/2 → 7/8; $2,64.
      Treść: `core-conventional-commits` — opis commita w języku commitów repo (z `git log`, nowe repo: angielski), jak
      `commit_language` od #290 (wcześniej „po angielsku”).
    - [x] 3c — składnia dziennika projektu (2026-11-17): `project_record.py` czyta sekcje po angielsku i po polsku
      (`Handoff`/`Przekazanie`, `Open questions`/`Otwarte pytania`, punkt kontrolny `Next step`/`Następna czynność`,
      `Steps`/`Kroki`; obszary domeny `Evidence`/`Dowody`, `Named by the human: yes`/`Wskazany przez człowieka: tak`,
      `Candidates below the threshold`/`Kandydaci poniżej progu`), migawka punktu kontrolnego pisze
      `## Automatic state …`; `retro_data.py` — `Pitfalls and dead ends`; `requirements_lint` (pack-it) pomija
      `Handoff`, `Open questions`, `Constraints`, `Current system`, `For the stack decision`. Testy EN-1…EN-6, AR-7,
      lint (czerwone bez zmiany). Bez migracji istniejących artefaktów: to zapis historii projektu (zaakceptowane
      dokumenty), a parser rozpoznaje obie nazwy — migracja dopiero przed usunięciem polskich aliasów.
    - [x] 4b-4 (2026-11-17): `core-project-record` (SKILL, referencja, 22 szablony po angielsku, `hint.pl.txt`).
      Wypełniacze szablonów po angielsku (`<YYYY-MM-DD>`, `<who>`, `<goal>`, `<branch>`), `project_record.py` wypełnia
      oba warianty. W `templates/plan.md` nazwy kolumn tabeli pozycji i klucze `cel_sekwencji` / `glowne_ryzyko` bez
      zmian — czyta je `decision_record.py` (mode-pdi) i kontrakt pdi (REL-008 w ci_for_sdlc); zmiana dopiero razem
      z pdi. `requirements_lint` (pack-it): sekcje `Business rule` i `Out of scope` liczą się do gotowości.
      Prompty `build.py`, `core/CLAUDE.md`, przewodnik: nazwy sekcji `Handoff` / `Open questions`.
      Podpowiedzi bez zmian (all 900 · 31/43, none 167 · 16/16, `--hints` czysto we wszystkich instalacjach).
      Haiku przed/po: 5/5 → 5/5, $1,43.
    - [x] (2026-11-22: sprawdzone — nagłówki po angielsku, „Work in progress”, „Recent events”) nagłówki generowanego indeksu i raportu (`project_record.py`: „Praca w toku”, „Ostatnie zdarzenia”,
      „Decyzje”, „Otwarte pytania”) — razem z komunikatami skryptów.
    - [x] 4b-5 (2026-11-17): `core-git-workflow` (+ 3 referencje), `core-cost-control` (+ 3 referencje),
      `core-agent-instructions` (+ referencja). Hook `log_usage` czyta `Class:` (dawniej `Klasa:`) i `Tier: too low/too
      high` (zapis tą samą wartością co `za niski/za wysoki`; test w `test_cost`). `hint.pl.txt` ma linię `head:` —
      dawny opis i katalog z wagą opisu (wcześniej tylko treść); indeksy 17 skilli przebudowane. Podpowiedzi po
      partii jak przed nią: all 900 · 31/43, none 167 · 16/16, `--hints` czysto w 8 instalacjach (3 pojedyncze
      scenariusze — słowa kluczowe). Haiku przed/po: 5/6 → 5/6 (ten sam `diagnoza-przed-dzwignia`), $1,71.
      Zostaje: komunikaty `ai-review.yml` i `instructions_lint` po polsku (etap komunikatów).
    - [x] 4b-6 (2026-11-17): `core-agent-security` (+ 2 referencje), `core-skill-authoring` (+ 2 referencje; reguła:
      po tłumaczeniu `tools/hint_pl_index.py`). Audyt bez ustaleń wysokiej wagi (znaczniki `audit-ok` przy opisach
      ataków zostają). Podpowiedzi: all 900 · 31/43, none 168 · 16/16 (było 167), `--hints` czysto w 8 instalacjach
      (2 scenariusze bezpieczeństwa — słowa kluczowe). Haiku przed/po: 4/6 → 3/6 + powtórka `clickfix-base64` 2/2
      (pojedynczy przebieg bez słowa „ClickFix”); `wstrzykniecie-w-zgloszeniu` i `przyjecie-zmiany-holdout` padały
      przed tłumaczeniem; $1,87.
    - [x] 4b-7 (2026-11-17): `tf` (+ 6 referencji; SKILL.md 14996/15000 znaków, szczegóły podglądu i odłożonych
      do `modes-and-stops.md`). Naprawione stare rozjazdy skilla ze skryptami: skill kazał `zakres fail` i `pytanie …`,
      a `run_state.py` przyjmuje `scope`, `intake.py` — `question`; teraz komunikaty mówią `scope`, a `intake.py` ma
      aliasy `task`/`pytanie`/`quick` (test I-23b). `build.py` czyta tabelę „Who does what” i „Kto co robi”; etykiety
      kroków w `config.yaml` po angielsku. Podpowiedzi: all 900 · 31/43, none 168 · 16/16, `--hints` czysto w 8
      instalacjach. Haiku przed/po: 5/6 → 3/6; dwa nowe ✗ to za wąskie sprawdzenia (`nie zgaduję` łapane jako
      zgadywanie, `run_state.py park` zamiast słowa `parked`) — poszerzone, powtórka 4/4; `zwykla-implementacja-historyjki`
      pada tak samo przed i po (pusty projekt → odpowiedź bez `intake.py`); $3,03.
    - [x] 4b-8 (2026-11-17): `core-delivery-lifecycle` (+ 8 referencji). Kolumny planu cięć (`Odblokowuje`,
      `Wymagania`, `Wydanie`, `Flaga`…) zostają dosłownie — czyta je `decision_record.py` (mode-pdi); w YAML przykładu
      przetłumaczone tylko wartości, klucze bez zmian. Ścieżki mapy artefaktów bez zmian (`test_artifact_map` 7/7).
      Podpowiedzi: holdout all spadł 31 → 30 (`ho-zmiana-kontraktu-w-kroku` — reguła „zmiana kontraktu = stop” tylko
      w indeksie PL); słowa kluczowe z treści skilla (nie z promptu) → all 900 · 31/43, none 168 · 16/16, `--hints`
      czysto w 8 instalacjach. Bramka w instalacji all (w none `canary-rollback` pada też przed tłumaczeniem — sąsiad
      ops-release-engineering niezainstalowany). Haiku przed/po: 5/6 → 4/6 + powtórka `przeglad-specyfikacji-panel`
      2/2 (pojedynczy przebieg zakończony pytaniami o ścieżkę); `pasma-kontrolne` pada tak samo przed i po (model
      wybiera ops-sre-incidents); $2,29. SKILL.md 18065 znaków (> 15000, ostrzeżenie jak przed partią: 17023).
      **Poprawka hooka skill_hint (z CI tej partii):** treść przetłumaczonego skilla w indeksie to angielski +
      `hint.pl.txt`, a normalizacja wyniku liczyła długość sumy — średnia długość rosła z każdą partią (wyniki
      nieprzetłumaczonych skilli w górę: w pack-docs „Przetłumacz ten akapit na angielski” przekroczyło próg,
      7,98 → 8,07), a przetłumaczony skill tracił za „długą” treść. Teraz każda wersja językowa liczy się osobno,
      znormalizowana swoją długością, i wygrywa lepiej pasująca (polecenie jest w jednym języku); średnia z dłuższej
      wersji (test HP-6, HP-6b, HP-7). Po zmianie: all 901 · 32/43, none 168 · 16/16, `--hints` i test poleceń ogólnych
      czyste w 8 instalacjach; słowa kluczowe `eng-llm-features` z jego sekcji 10 (scenariusz na granicy: 4. miejsce
      z różnicą 1,3 pkt), słowo „plan rozjechał się z kodem” zawężone (łapało „rozjedzie się” w pytaniu o ACL).
    - [x] 4b-9 (2026-11-17): cechy rdzenia (9 plików) i teksty `config.yaml`, które czyta model: opisy i prompty agentów
      wspólnych, `routing` + `routing_notes`, `report_contract` (sekcje **Result/Changed files/Verification/Uncertain/
      To decide**, `Tier: too low/too high`), `work_contract`, `style_note`, `untrusted_note`, `grounding_note`
      (znaczniki `[unverified]`, `[assumption]`), `sources_only_note`, `language_note`, `commit_language`,
      `code_language_note`. Etykiety recenzenta zakresu jak w skillu tf: `[important]`/`[minor]`/`[pre-existing]`,
      `Verdict: OUT OF SCOPE / IN SCOPE`; panel: `Verdict: PASS/FAIL` (werdykt trafia do kodu argumentem
      `pass|fail`, tekst nie jest parsowany) — zlecenia panelu i komunikaty `run_state.py` z tymi samymi tokenami.
      `build.py` odsyła do sekcji „To decide”. Zostają po polsku: komentarze YAML (dokumentacja opiekunów), `facets`
      i `vocabulary` (skille fw-/lang- pokrywają pojęcia polskimi sekcjami — razem z pack-it), opisy profili kosztów
      (wypisuje je `profile.py` — etap komunikatów). Haiku przed/po (tf ×2, core-cost-control ×2, core-grounding ×2):
      4/6 → 5/6; `waga-pelna-panel-recenzentow` pada tak samo przed i po — panel jest tylko w `references/weight.md`,
      a model nie sięga po plik; $1,93.
    - [x] (2026-11-22: sprawdzone — szablony, `facets` i `vocabulary` po angielsku; ostatni polski przykład w opisie
      `build.py` przetłumaczony) szablony person i wykonawców w `build.py` (sekcje „Rola”, „Priorytety”, „Cechy”, „Granice”, „Konsultanci”,
      `COMPOSE_HINT`, tabela wymiarów) oraz `facets`/`vocabulary` — razem z sekcjami pojęć w skillach fw-/lang-.
    - [x] (2026-11-22: linia w §4 Finishing `tf-task/SKILL.md`; Haiku 1/2, było 0/2; scenariusz podaje katalog
      przebiegu, linia wymienia skład panelu — Haiku 2/2; razem 0,82 USD) tf: panel recenzentów przy wadze pełnej tylko w `references/weight.md` — jedna linia w SKILL.md (Finishing),
      żeby model nie pomijał `run_state.py panel` (scenariusz `waga-pelna-panel-recenzentow` pada przed i po 4b-9).
    - [x] 4b-10 (2026-11-17): przewodniki `core/guide/` (GUIDE, LOOP, FAQ, JEV, ONBOARDING) w całości po angielsku —
      także symbole zastępcze w poleceniach, komentarze w blokach kodu i przykłady (bez jednej polskiej litery; zostają
      tylko aliasy poleceń `zadanie`/`pytanie`/`szybko`, które skrypt przyjmuje). Napisy skryptów, które przewodniki
      cytują, też po angielsku: opis PR (`run_state.py pr-body`: Story, Slices, Criteria trace, How it was checked, Risk,
      How to roll back, Postponed for a decision, Assumptions, Run) z sekcjami `tf risk --md` i `tf trace --md`, cały
      podgląd `dashboard.html` (kolumny, lista „Waiting for you”, panel plików), katalog komunikatów STOP
      (`stop_messages.json` — wartości, klucze bez zmian), linie „waiting for you / question / recommended” w
      `tf status`, linia `Source: … · fetched:` w `ticket.md` (odczyt przyjmuje też `Źródło:`), sekcje „Security”
      i „Attempt n” w raporcie przebiegu (odczyt summary.md przyjmuje oba nagłówki), źródła w `tf config show`
      (factory/organisation/team/project/person — także sufiks warstwy `(person)`, po którym kod rozpoznaje preferencje),
      wartości `Rework-Cause` (`spec-gap`, `agent-error`, `requirement-change`, `unknown`; dawne polskie w starszych
      commitach liczone jako aliasy w `tf metrics` i retrospektywie). **Naprawiony błąd:** opis PR szukał wyniku skanu
      w `security/<kawałek>/proba-*`, a skan zapisuje `attempt-<k>` — każdy kawałek miał „brak wyniku” (test PB-24).
      Zostaje dosłownie: nagłówek `## Odłożone do decyzji` w raporcie przebiegu — pdi (`src/pdi/pr_loop.py`) czyta po
      nim odłożone sprawy z raportu cięcia (zmiana razem z repozytorium pdi, jak kolumny `plan.md`). Bez próbki Haiku:
      żaden skill nie odsyła modelu do przewodników; podpowiedzi all 901 · 32/43, `--hints` czysto, bramki tf,
      core-git-workflow, core-agent-retro przechodzą.
    - [x] dalsze partie: 4c (pack-docs, pack-ux, mode-team, mode-pdi, org).
  - [x] 4c — pack-docs, pack-ux, mode-team, mode-pdi, org (szablony).
    - [x] 4c-org (2026-11-22): `org/README.md` po angielsku (szablony `org/template*` były już po angielsku; pętla
      nazwana `/tf-task`, `model_guard` z ostrzeżeniem na starcie sesji). Zostają celowo po polsku: schematy JSON
      w mode-pdi (kopie kontraktu pdi — zmieniać tylko razem z pdi), aliasy czytników (`nagłówek`, kolumny
      `design.md`), polskie słowa kluczowe, nazwy polskich aktów prawnych i przykładowe aplikacje analizatora dostępności.
    - [x] 4c-1 (2026-11-18): `docs-tech-writing` (+ 6 referencji), rola `tech-writer` i wiersz routingu pack-docs,
      `team-session` i przewodnik mode-team; nazwy i pytania wymiarów (`facets`) rdzenia, pack-docs i mode-team po
      angielsku (pominięte w 4b-9); `content_language: en` w przetłumaczonych nakładkach i w szkielecie
      `workspace.py new-pack`. Polskie słowa kluczowe zostają, angielskie dochodzą; `hint.pl.txt` dla obu skilli.
      Podpowiedzi bez zmian: all 901/918 · 32/43, none 168/175 · 16/16, `--hints` czysto (all, none, pack-docs,
      mode-team). Haiku `docs-tech-writing` przed/po 3/3 → 3/3, 0,74 USD. `translation_check`: różnice tylko
      zamierzone (przykład polecenia `/team-session`, notacja `event [condition] / action`; blok kodu w SKILL.md to
      fałszywy alarm — wzmianka ```` ```bash ```` w środku zdania).
    - [x] 4c-2 (2026-11-18): pack-ux — `ux-information-architecture` (+ 3 referencje), `ux-research-methods`
      (+ 5 referencji, w tym szablony planu i raportu badania), `ux-content-design` (+ 3 referencje). Polskie słowa
      kluczowe zostają, angielskie dochodzą; `hint.pl.txt` dla trzech skilli. Polskie źródła i treści o polszczyźnie
      zostają nazwane po polsku (KPRM „Prosto i kropka”, indeksy Pisarka, UODO). Podpowiedzi identyczne jak przed
      partią (all 901/918 · 32/43), `--hints` czysto (all, pack-ux). Haiku przed/po (6 scenariuszy, 3 skille): 6/6 → 6/6,
      1,50 USD. `translation_check`: różnice tylko w nazwach kolumn szablonów (inwentarz, taksonomia, nuggets).
    - [x] 4c-3a (2026-11-18): pack-ux — `ux-service-design`, `ux-design-leadership`, `ux-accessibility` (po 2–3
      referencje). Polskie słowa kluczowe zostają, angielskie dochodzą; `hint.pl.txt` dla trzech skilli. Polskie akty
      prawne zostają nazwane po polsku (Dz.U., PFRON, „deklaracja dostępności”). Podpowiedzi: tuning 901/918 bez zmian,
      holdout 32/43 → 31/43 — jeden przypadek `core-agent-security` (serwer MCP do Jiry) spadł z 3. na 4. miejsce przy
      remisie 18,05 : 18,04 z `eng-llm-features` po przesunięciu IDF; holdoutu nie stroimy, do obserwacji przy 4c-3b.
      `--hints` czysto (all, pack-ux). Haiku przed/po (3 scenariusze): 3/3 → 3/3, 0,77 USD. `translation_check`: różnice
      tylko w nazwach kolumn szablonów i etykietach diagramu Mermaid.
    - [x] 4c-3b (2026-11-18): pack-ux — `ux-design-systems`, `ux-feature-design`, `ux-visual-design` (+ referencje),
      persona Natalia, 6 ról UX, `pack.yaml` (facet, konsultanci, `content_language: en`), tytuł i opis analizatora
      `accessibility`. pack-ux nie ma GUIDE. Tabela ramek w `figma-mcp.md` pokazana po angielsku (`Requirement | Journey
      | State | Frame | Notes`, `missing`, `n/a` — `design_check.py` czyta obie wersje); szablon `design.md` w mode-pdi
      zostaje na 4c-x. Podpowiedzi bez zmian względem 4c-3a (901/918 · 31/43; remis `core-agent-security` nadal),
      `--hints` czysto (all, pack-ux). Haiku przed/po (4 scenariusze): 3/4 → 3/4, 1,07 USD — `spec-faktury` pada na
      main i po zmianie tak samo (Haiku nie uruchamia skilla), do przejrzenia osobno.
    - [x] 4c-x (2026-11-18): mode-pdi — `pdi-decisions` SKILL, GUIDE, facet, `content_language: en`, szablony
      `intent.md`, `plan.md`, `design.md`, `decisions.md`, `REVIEW.md`, `release.yaml` po angielsku. Czytniki przyjmują
      obie formy (`# pl: sprzed 14.x`): `decision_record.py` (kolumny `Slice | Kind | Release | Flag | Value |
      Requirements | Unblocks | Verification`, `## Options considered`/`### Option`, `## Change targets`),
      `phase_run.py` (`## Gate questions`), `run_report.py` (kolumny `Flag`, `Value`). Sprawdzone w kodzie
      ci_for_sdlc (`connectors/repo.ts` przyjmuje angielskie kolumny i `Success metrics`) i w kontrakcie pdi
      (`conventions.design.columns.en`). Kryteria 5 scenariuszy eval przyjmują też angielskie nazwy formatów.
      Podpowiedzi bez zmian (901/918 · 31/43), `--hints` czysto (all, mode-pdi). Haiku przed/po (5 scenariuszy, te same
      kryteria): 3/5 → 3/5, 1,59 USD; te same 2 porażki na main i po zmianie (`faza-uruchomiona-przez-pdi`: Haiku
      proponuje `decision add`; `faza-design-tabela-ramek`: wybiera ux-feature-design) — do przejrzenia osobno.
    - [x] 4c-y (2026-11-18): mode-pdi — szablony workflow `sdlc-phase.yml`, `change-check.yml`, `metric-watch.yml`
      po angielsku (komentarze, opisy wejść, nazwy kroków, komunikat `::error::` braku verify.sh, commit fazy
      `docs(CHG-n): phase <faza> (pdi)`). Nazwy kroków czytają tylko testy tf (W-16, P-8, kroki z GH_TOKEN) —
      zaktualizowane; pdi ich nie parsuje (sprawdzone w `src/pdi`), a sekcję „Przewodnik dokończenia” w opisie PR
      pisze samo pdi. Zainstalowane już workflow w produktach działają dalej (nadpisuje je tylko `workflow install
      --force`). Bez próbki Haiku: SKILL.md bez zmian, szablony nie trafiają do modelu.
      Zostaje: szablony workflow `sdlc-phase.yml`, `change-check.yml`, `metric-watch.yml` (komentarze i nazwy kroków;
      P-8 i pdi czytają nazwę kroku N3 i sekcję „Przewodnik dokończenia”) — osobna partia 4c-y.
  - [x] 4d-arch-a (2026-11-18): pack-it — `arch-ai-solutions`, `arch-architect-practice`, `arch-eu-product-law`
    (+ referencje) po angielsku; polskie słowa kluczowe zostają, angielskie dochodzą; `hint.pl.txt`. Znaczniki źródeł
    `[unverified]`/`[secondary]`; kryteria 2 scenariuszy eval EU law przyjmują też angielskie znaczniki. Podpowiedzi
    bez zmian (901/918 · 31/43), `--hints` czysto (all, pack-it). Haiku przed/po (4 scenariusze): 4/4 → 4/4, 1,30 USD.
  - [x] 4d-arch-b (2026-11-18): pack-it — `arch-multi-tenancy`, `arch-privacy-compliance`, `arch-quality-attributes`
    (+ referencje) po angielsku; `hint.pl.txt`. Przykład w Pythonie (pseudonimizacja, retencja): zmienione tylko
    docstringi, 2/2 testy przechodzą; znacznik `-- pii: personal data` pasuje do analizatora data-classification;
    nazwy sekcji jak w szablonach rdzenia („Quality attributes”, „Decision drivers”). Podpowiedzi: tuning 901/918,
    holdout 31/43 → 32/43 (`ddd-tactical-design` +1), `--hints` czysto (all, pack-it). Haiku przed/po: 4 scenariusze
    4/4 → 3/4 (`klasyfikacja-danych`: Haiku nie uruchomił skilla), powtórka 2 scenariuszy × 2: 4/4 → 4/4; łącznie
    `klasyfikacja-danych` 3/3 → 2/3 — szum wyboru skilla, do obserwacji. 2,18 USD.
  - [x] 4d-arch-c (2026-11-18): pack-it — `arch-system-design`, `arch-tech-selection`, `arch-threat-modeling`
    (+ referencje) po angielsku; `hint.pl.txt`; prefiks `arch-` zamknięty. `quality_override: yes` (nikt go nie parsuje).
    Podpowiedzi bez zmian (901/918 · 32/43), `--hints` czysto (all, pack-it). Haiku przed/po (4 scenariusze): 3/4 → 3/4,
    1,07 USD; `model-webhook-upload` pada tak samo na main (brak ryzyka rezydualnego w odpowiedzi) — do przejrzenia.
  - [x] 4d-be-a (2026-11-18): pack-it — `be-api-design`, `be-billing-subscriptions`, `be-business-app-patterns`
    (+ referencje) po angielsku; `hint.pl.txt`. Podpowiedzi: tuning 901/918, holdout 32/43 → 31/43 — ten sam
    przypadek `ddd-tactical-design`, który w 4d-arch-b zyskał (remis wrażliwy na IDF), `--hints` czysto (all, pack-it).
    Haiku przed/po (4 scenariusze): 4/4 → 4/4, 0,95 USD.
  - [x] 4d-be-b (2026-11-18): pack-it — `be-auth-security`, `be-database`, `be-messaging-outbox` (+ referencje)
    po angielsku; `hint.pl.txt`. Przykłady w Pythonie outbox/inbox przetłumaczone i uruchomione (`OrderPlaced`,
    test duplikatu „ok”). `be-messaging-outbox` nie miał `keywords` — Haiku po zmianie raz nie uruchomił skilla
    (`odtworzenie-historii-skutki`), dodane słowa kluczowe PL+EN (replay, reset offsetu, odbudowa modelu odczytu):
    powtórka 2 scenariuszy × 2: 4/4. Podpowiedzi bez zmian (901/918 · 31/43), `--hints` czysto. Haiku przed/po
    (4 scenariusze): 4/4 → 3/4 → po poprawce 4/4, 1,48 USD.
  - [x] 4d-r1 (2026-11-18): pierwsza runda równoległa — `qa-` (8), `proc-` (8), `tool-` (7), `pm-` (5), `data-` (2):
    30 skilli (+ referencje) po angielsku, `hint.pl.txt`. Decyzja właściciela (2026-11-18): tłumaczą równolegli
    wykonawcy według jednej instrukcji (zakres, frontmatter, bloki kodu, znaczniki, samokontrola
    `translation_check`); jakość pilnuję sam: przegląd każdego zgłoszonego ✗ i próbki tekstu, bramki, holdout,
    `--hints`, Haiku po zmianie (1 scenariusz na skill, przed zmianą tylko dla porażek). Jedna runda = jeden PR.
    Przetłumaczone przykładowe teksty w kodzie (Playwright, Vitest, pytest, Semgrep) — żaden scenariusz ani
    projekt przykładowy od nich nie zależy. `proc-agile` stracił podpowiedź w `ciecie-historyjek` (900/918) —
    dodane słowa kluczowe PL+EN (pociąć historyjkę, cięcie pionowe): z powrotem 901/918 · 31/43.
    Haiku po zmianie: 25/27; `testy-z-kodu` 2/2 w powtórce (szum). `porownanie-grup-skosne` (data-analysis):
    przed 4/5, po 2/6 — model odpowiada z samego SKILL.md (bez referencji) i rzadziej wspomina korektę wielu
    porównań; dodany krótki wskaźnik w kroku 5 (wielkość efektu, korekta Holm/Benjamini-Hochberg — z
    `references/statistics.md`): 3/3. Koszt Haiku rundy: ok. 6 USD.
    Zostaje do dokończenia:
    - [ ] `qa-test-design/templates/test-strategy.md` jest po polsku; `references/project-test-strategy.md`
      celowo zachowuje polskie wartości stanów (zakończona, w realizacji…) — tłumaczyć razem.
    - [ ] `proc-requirements-shaping`: przykłady zachowują polskie nagłówki i linie briefu czytane przez
      `requirements_lint.py` (lint przyjmuje już angielskie) — przełączyć na angielskie przy usuwaniu aliasów.
    - [ ] nagłówek „## Brief dla wykonawcy” w `modes/mode-pdi/tests/test_triage_pdi.py` i
      `eng-code-audit/references/report-template.md` — skill `proc-issue-triage` ma już „Brief for the implementer”.
  - [x] 4d-r2 (2026-11-18): druga runda równoległa — `lang-` (6), `fw-` (6), `fe-` (5): 17 skilli (+ referencje)
    po angielsku, `hint.pl.txt`. Słownik pojęć kontraktu technologii (`core/factory/config.yaml` → `vocabulary`)
    po angielsku (value object, entity, aggregate…); `build.py check` przyjmuje polskie nazwy jako aliasy
    (`VOCABULARY_PL`, „pl: sprzed 14.x”) — 0 ostrzeżeń. Przykłady Go uruchomione po tłumaczeniu (`go test`),
    TypeScript skompilowany i uruchomiony; zdanie „pliki skopiowane bez zmian” zastąpione „kod z testowanego
    projektu; przetłumaczone tylko komentarze i komunikaty”. Spisy treści przeliczone `build.with_toc`.
    Bramki 17/17, podpowiedzi 901/918 · 31/43, `--hints` czysto, testy repo zielone. Haiku po zmianie 14/16:
    `modernizacja-typow` 2/2 w powtórce (szum); `bledy-walidacja-openapi` (fw-aspnet-core) pada tak samo na main
    (0/2) — model cytuje antywzorzec `Conflict(new ProblemDetails…)`, przed którym skill ostrzega.
    - [x] (2026-11-22: `none` łapie tylko użycie w kodzie — `return`/`=>` przed `Conflict(new ProblemDetails`; Haiku
      2026-11-22: 4/4, PL i EN) `bledy-walidacja-openapi`: niepożądany wzorzec trafia w cytat ostrzeżenia — zawęzić regex albo zmienić
      sformułowanie w skillu (przed tłumaczeniem też 0/2).
    - [x] (2026-11-23: sprawdzone — dane endoflife.date z repo endoflife-date/endoflife.date na GitHubie, typy `@angular/core` z npm: `endoflife.ai` → endoflife.date; `@Service` jest od Angular 22.0.0, nie ma go w 21.2.26; Spring Boot 3.5: bezpłatne wsparcie do 2026-06-30, płatne do 2032-06-30, ostatnia 3.5.16 z 2026-06-25 — zgodne z treścią) do sprawdzenia fakty ze źródła: `endoflife.ai` w fw-nestjs (pewnie endoflife.date), `@Service` jako
      dekorator Angulara w lang-typescript, wsparcie Spring Boot 3.5 do 2026-06-30 vs 3.5.16 w źródłach.
  - [x] 4d-r3 (2026-11-18): trzecia runda równoległa — `ops-` (22), `sec-` (13): 35 skilli (+ referencje) po
    angielsku, `hint.pl.txt`. Poprawki z raportów: w sec-llm-security oryginał nazywał bramkę „zawodzi otwarcie”,
    choć reguła opisuje fail-closed (nieczytelne = odmowa) — teraz „fails closed”; grupa Dependabota `drobne` →
    `minor-and-patch`. `skill_audit.py` nie rozpoznawał spisu „> **Contents:**”, który pisze `build.with_toc`
    (`^` bez `re.M`) — 88 fałszywych `ref-no-toc` w pack-it, po poprawce 3; test SA-TOC (EN/PL/brak).
    Podpowiedzi: nowe angielskie opisy przesunęły wagi i dwa scenariusze spoza rundy straciły podpowiedź
    (`ai-evals` `sedzia-llm-kalibracja`, `proc-safe` `czy-safe-pasuje`) — słowa kluczowe PL+EN: 902/918 · 31/43.
    Bramki 35/35, testy repo zielone. Haiku po zmianie 30/34; cztery porażki to brak wywołania skilla
    (`ops-docker` `hardening-runtime`, `ops-kubernetes` `config-rollout`, `ops-linux-networking` `dysk-inody`,
    `ops-secrets-identities` `wyciek-klucza-aws`) — na main też (7 z 8 przebiegów bez wywołania).
    - [x] (2026-11-22: opisy czterech skilli poszerzone o sytuację ze scenariusza; podpowiedzi 0 pominięć w `all`
      i `pack-it`; Haiku 2026-11-22, 2 powtórki, 1,87 USD za całą serię: `hardening-runtime`, `config-rollout`, `dysk-inody` 2/2;
      `wyciek-klucza-aws` 0/2, po wzmocnieniu opisu i słów kluczowych PL+EN 2/2 (0,20 USD)) cztery
      scenariusze ops- bez wywołania skilla (także przed tłumaczeniem) — skille bez `keywords`;
      sprawdzić słowa kluczowe PL+EN i opis pod polskie zgłoszenia.
  - [x] 4d-r4 (2026-11-18): czwarta runda równoległa — `eng-` (19), `ddd-` (13), `ai-` (13): 45 skilli (+ referencje)
    po angielsku, `hint.pl.txt`. Wszystkie skille pack-it są po angielsku. Stałe sekcje referencji `ddd-archetypes`
    (`reference_sections` w pack.yaml) po angielsku; `build.py check` przyjmuje też plik w całości z polskimi nazwami
    (`sections_pl`, „pl: sprzed 14.x”). Ciągi czytane przez skrypty zostały bajt w bajt (np. `pelna|oszczedna`,
    `=== POKAŻ DOSŁOWNIE ===` w ddd-es-simulation, statusy ROZWIĄZANE/NOWE/ZMIENIONE w eng-tech-debt-audit, „BRAK w
    kodzie”), z angielską glosą. Poprawki: ddd-es-simulation pokazywał `--scenario weterynaria`, a katalog to
    `veterinary` (polecenie z dokumentacji kończyło się „No scenario”); opis ai-mcp-server skrócony do ≤ 170 znaków;
    ucięte fragmenty spisów treści (eng-llm-features, trzy pliki fw-nextjs) usunięte. Podpowiedzi: słowa kluczowe PL+EN
    dla ddd-context-mapping, sec-zero-trust-identity, ddd-tactical-design (i tool-vitest w #329 — sprawdzane też w
    obszarze roboczym samego pack-it): 902/918 · 31/43, `--hints` czysto w `all` i `pack-it`. Bramki 45/45. Haiku po
    zmianie 39/43; powtórki przed/po dla czterech porażek: 3/8 → 5/8, `tdd-nowa-regula` (eng-testing) bez wywołania
    skilla po obu stronach.
    - [x] (2026-11-22: opis poszerzony o „kroki TDD dla nowej reguły”; Haiku 2026-11-22: 2/2)
      `tdd-nowa-regula`: skill eng-testing nie jest wywoływany (także przed tłumaczeniem) — słowa kluczowe/opis.
    - [ ] kontrola podpowiedzi przed PR w obu obszarach (`all` i sam `pack-it`) — IDF zależy od zestawu skilli.
  - [x] 4d… — pack-it partiami po prefiksach (`arch-`, `be-`, `fe-`, `ops-`, `sec-`, `qa-`, `ddd-`, `eng-`, `ai-`, `pm-`,
    `proc-`, `data-`, `fw-`, `lang-`, `tool-`, `ux-`).
  - [x] 4e (2026-11-18): reszta pack-it po angielsku — 21 person, 22 role, `pack.yaml` (wymiary, prompty agentów
    wspólnych, konsultanci; `content_language: en`), przykłady (shop-pricing, room-booking — README i eksport
    odtworzone przez `project_record.py index/report`), 7 analizatorów (opisy, docstringi), workflow code-audit.
    Nazwy sekcji zgodne z przetłumaczonymi skillami („Request / Mechanism / Basis”, „The facilitator's self-check”,
    „Decision gates”, „What was not checked”). Zostają po polsku, bo czyta je kod lub test: etykiety agentów workflow
    (`inwentarz`, `przegląd:`, `raport`, `weryfikacja:`) i prompt „Spróbuj obalić…” (test_workflows W-7…W-18),
    wzorce wykrywania analizatorów (`zł`, `hasło`, `dane osobowe`…), wejścia fixture'ów. Testy: shop-pricing vitest
    12 + 4 oczekiwane porażki, bramka analizatorów 7/7 (wynik bajt w bajt jak przed), test_workflows 20/20;
    `--hints` czysto w `all` i `pack-it`, 901/918 · 31/43.
    - [ ] etykiety i prompt weryfikacji w `workflows/code-audit.js` po angielsku razem z testami W-7…W-18.
  - [x] 4f (2026-11-18): pack-editorial-pl — opisy, procedury, persona, rola, cecha i `pack.yaml` po angielsku; normy
    RJP, przykłady zdań, pary błędne/poprawne i nazwy źródeł zostają po polsku (z angielską glosą). Kategorie raportu
    jak w `polish_lint.py` (SPELLING, PUNCTUATION…); `keywords` PL+EN w txt-polish-correctness (podpowiedzi 3/3);
    literówka „wcześej” → „wcześniej” w regule §18. Haiku 3/4, `komunikaty-ui` 2/2 przed i po (szum).
  - [x] 4g (2026-11-18): komentarze i docstringi w kodzie po angielsku — 132 pliki (core/factory, hooks, tools,
    scripts, core/skills, modes, org, .github, packs). Kontrola: AST bez docstringów identyczne dla 117 plików `.py`
    (własny skrypt, niezależnie od wykonawców), YAML — dane identyczne poza komentarzami w blokach `run:`. Zostają:
    literały, regexy, linie `pl: sprzed 14.x`, cytowane polskie dane. Ponowna bramka 21 skilli (skrypty w odcisku).
    Wykonawcy na Sonnecie (tańsze, praca mechaniczna).
    - [x] polskie napisy w szablonie `ai-review.yml` i komunikaty `echo` w workflow — w 4h.
  - [x] 4h (2026-11-18): napisy dla człowieka i komunikaty testów po angielsku — 175 plików (runnery ewaluacji,
    skrypty, workflow GitHub, szablon ai-review, testy core/modes/packs/repo). Etykiety i prompt weryfikacji
    workflow code-audit po angielsku razem z test_workflows. Zostają: aliasy i wzorce przyjmujące polski
    („pl: sprzed 14.x”), polskie dane testowe i fixture'y, formaty czytane przez inny program, prompty sędziego
    w `run_skill_evals.py` i `flow_evals_runner.py` (zmiana języka sędziego zmienia ocenianie). Kontrola: wszystkie
    testy repo i 8 obszarów roboczych CI zielone, ponowna bramka 7 skilli, 901/918 · 31/43.
    - [ ] prompty sędziego ewaluacji po angielsku — osobno, z kalibracją (te same scenariusze przed i po).
  - [x] 4i (2026-11-18): angielskie bliźniaki scenariuszy ewaluacji — jeden na skill (`<id>-en`, 165 plików; 11 bez
    scenariusza trigger, txt-polish-style pominięty — skill redaguje polski tekst). Grupy kontroli te same, polskie
    alternatywy zostają, dopisane angielskie. Podpowiedzi: 154/165 od razu; 11 skilli dostało angielskie słowa
    kluczowe (m.in. data-engineering, lang-typescript, ops-secrets-identities, ux-accessibility) — 165/165,
    1066/1083 · holdout 32/43 (było 31). Haiku na próbie 25 bliźniaków: 23/25; dwie porażki to znane już na
    polskich wersjach (`model-webhook-upload`, `config-rollout`).
    Słowa kluczowe EN także dla core-grounding (obszar mode-pdi) i ai-fine-tuning (obszar pack-it); `--hints` czysto
    we wszystkich 8 obszarach roboczych CI — od teraz sprawdzane we wszystkich, nie tylko w `all` i `pack-it`.
  - [x] 4j (2026-11-19): żywa dokumentacja po angielsku — README, `docs/` (RELEASING, inactive-skills, insights,
    new-pack, plugins, setup, mapa-fabryki.html), `core/factory/PUBLIC_API.md`. Decyzja: archiwa (`docs/evals`,
    `docs/plans`) zostają po polsku jako zapis historyczny — w obu katalogach krótki README po angielsku; także ten
    plik (`docs/todo.md`) i `CHANGELOG.md` zostają po polsku. Przy okazji: skill tf kazał przekazać linię `Waga: …`,
    a `run_report.py` od #308 wypisuje `Weight: …` — skill i test T-27 poprawione.
    - [x] (2026-11-22: żaden z plików nie wspomina już `mode-talos`) `docs/insights.md` i `docs/plugins.md` opisywały `mode-talos` (usunięty w 10.0.0) i liczby skilli sprzed
      zmian — zaktualizować treść (to nie tłumaczenie).
    - [ ] gdyby archiwa miały być po angielsku: `docs/evals` (47 plików) i `docs/plans` (40) — osobny krok.
  - [x] 4k (2026-11-19): usunięte polskie aliasy czytników (`pl: sprzed 14.x`) — decyzja właściciela: jednym krokiem.
    Migracja 19.0.0 (`migrations.migrate_v19`) przepisuje polskie formy na angielskie w plikach projektu, które czytały
    usunięte aliasy (punkty kontrolne `.tf/wip/`, decyzje retro, cache bazy wiedzy, tagi banku dowodów, blok fabryki
    w CLAUDE.md — przed przepisaniem bloku, więc komendy projektu zostają, własne skille i persony, `managed-agents/`,
    plan i artefakty pdi, rekonstrukcja pack-it); 16 nowych testów MV-18…33 i U-5. Zostaje polski kontrakt pdi
    `design.md` (forma zewnętrznego kontraktu, nie alias). Przy okazji: Talos usunięty z żywej dokumentacji, testów
    i przykładów (zostaje tylko to, co sprząta stare instalacje: `RETIRED_PACKS`, przemianowania, strażnik w
    test_tf_skill, wpis „Removed in 10.0.0” w PUBLIC_API); pasek stanu po angielsku (`context`, `cold`); trzy
    sprawdzenia w testach szukały polskich komunikatów, których narzędzia już nie wypisują (zawsze przechodziły) —
    poprawione na angielskie.
    - [x] aliasy bez znacznika — w 4l.
  - [x] 4l (2026-11-19): czytniki tylko po angielsku — reszta polskich form bez znacznika (sekcje rejestru projektu,
    raporty analyze, LESSON_HEADS, werdykty badań P/C/N/S, Given/When/Then w specyfikacji, MARK i aliasy recon,
    requirements_lint, dossier), wartości `Rework-Cause` i stopka `Kawałek` (historia sprzed zmiany liczona jako nieznana
    przyczyna), identyfikatory kawałków K<n> → S<n> (migracja otwartych zadań: plan, task.json, dowody, events, run.json,
    katalogi security; hash zatwierdzenia przeliczany, gdy się zgadzał) i nazwy zdarzeń hooków („session end”, „context
    compaction”; `settings_v19` przepisuje ustawienia użytkownika przed scaleniem — bez zdublowanego hooka, testy U-6/U-7).
    Migracja rozszerzona (MV-34…66). Przy okazji: panel plików nie pokazywał dowodów kawałków S (czytnik szukał tylko K).
    Zostają: LEGACY_GI (sprzątanie starych instalacji), polski kontrakt pdi `design.md`, obsługa polskich treści
    (historyjki, changelogi, własne skille po polsku, polish_lint, detektory), prompty sędziego ewaluacji.
    - [x] (2026-11-22: komunikaty `statusline.py` są po angielsku) `statusline.py` i część komunikatów `task_state.py`/`project_record.py` wciąż po polsku (testy je
      sprawdzają) — przełożyć razem z testami.
  - [x] komunikaty skryptów i hooków po angielsku (model przekazuje je człowiekowi w jego języku). Partie: M1 pętla tf,
    M2 hooki, M3–M4 silnik (`core/factory`), M5 skrypty pozostałych skilli rdzenia, M6 pack-it, M7 mode-pdi, M8 org,
    tools, editorial, ux. Docstringi i komentarze w kodzie to dokumentacja opiekunów — poza tym etapem.
    - [x] M1 (2026-11-17): skrypty skilla tf (`run_state`, `run_report`, `intake`, `plan_drift`, `security_scan`),
      `task_state.py` (`tf status`, `tf task …`) i `task_weight.py` — komunikaty, etykiety wyjścia (`Input/Key/Next`,
      `Next: S3`, `What happened/What is needed/Question/Then`), wartości JSON `intake` (`issue/cut/resume/file/content/
      none`, `task/question/quick`, `card/address/organisation`; polskie słowa na wejściu nadal działają), raport
      przebiegu z nagłówkiem „Postponed for a decision” (pdi czyta oba od pdi#181), etykiety wag `light/normal/full`.
      Odczyt starych danych przyjmuje polskie formy (`## Zamiar zmiany`, `Źródło:`, `powód:`/`waga`, `## Bezpieczeństwo`).
      **Naprawione błędy:** komunikaty podawały polecenia, które skrypt odrzucał — `--code pytanie` (×2),
      `--code srodowisko`, `step … kod run`, kody „testy/skan/pytanie” w limicie rund (test K-8/K-9 sprawdza odtąd każde
      `--code`/`step` w komunikatach); `task_weight` odcinał zamiar zmiany tylko pod polskim nagłówkiem (W-24b).
    - [x] M2 (2026-11-17): hooki `core/hooks` — blokady i prośby o zgodę (`guard_bash`, `guard_paths`, `cleanroom_guard`,
      `scan_secrets`), `quality_gate` (stan bramki w `tf doctor` i na starcie sesji), `tdd_guard`, `skill_hint` (treść
      podpowiedzi dla modelu), `jev_*`, `detect_stack`, `context_guard`, `skill_change_guard`, `project_record` (indeks
      `docs/project/README.md`, raport, punkty kontrolne, sprawdzanie dowodów), drobne. Klucze typów operacji bez
      zmian. Migawka punktu kontrolnego pisze `- Branch: … · last commit: …`, odczyt przyjmuje też polską linię; polskie
      argumenty zdarzeń z `settings.json` (`koniec sesji`, `kompaktowanie kontekstu`) zapisuje po angielsku.
      Skuteczność: holdout podpowiedzi 901/918 · 32/43 bez zmian; Haiku (plan-interview, skill-composition) 7/8, ~$1,85.
      Jedyny chybiony, `przesluchanie-bez-nadmiaru`, pada tak samo na `main` (2/2): odpowiedź jest trafna, ale
      sprawdzenie zna tylko słowa „przeinżynierowanie/nadmiar/minimalizm/YAGNI” — do przejrzenia przy 4c.
    - [x] M3 (2026-11-17): `build.py` — prompty generowanych person, wykonawców i konsultantów (sekcje `## Traits`,
      `## When you delegate`, `## Boundaries`, `## Report` …), katalog `.claude/catalog.md`, walidacja i komunikaty CLI,
      szkielet `new-skill` (`## Domain concepts in …`); kontrakt skilli technologicznych przyjmuje angielskie i polskie
      nagłówki (`Domain concepts`/`Pojęcia domenowe`, `Version-dependent`/`Zależne od wersji`). Znacznik generowanych plików
      `GENERATED by …` (`target_managed` rozpoznaje też stary). `skill_gate.py` (kroki bramki, stan, `--hints`; klucze
      wyniku płatnej ewaluacji `aborted`/`no_uplift`/`<model>_without_skills`, raporty `*-gate-<skill>.md`),
      `analyze.py` (raport modułu `Verdict:`/`## Recommended actions`/`## Analysis history`, scalanie czyta też stare
      polskie nagłówki — test A-6b), `onboard.py` (raport gotowości, propozycja zapisu; sekcja `### Commands` lub
      `### Komendy` w bloku fabryki). Skuteczność: holdout 901/918 · 32/43 bez zmian, `--hints` czyste; przebieg
      `N5-synth-repeated-q` na Haiku kończy się tak samo jak na `main` (`waiting_gate`, 0,24 USD każdy).
      Zostaje: `core/CLAUDE.md` (blok instrukcji, `### Komendy`/`### Język`) i `templates/SKILL.template.md` — treść, M4/4c.
    - [x] M4 (2026-11-17): reszta `core/factory` (29 plików: `tf.py`, `work.py`, `packs.py`, `install.py`, `uninstall.py`,
      `check.py`, koszty i metryki, `spec_check`, `skill_audit`, `rules_scan`, `flag_check`, `freshness`, `trace_check`,
      `facts`, `finish`, `target_managed` …), `core/CLAUDE.md` (blok instrukcji w projekcie: `## Agent team`,
      `### Commands`, `### Language`) i szablon `SKILL.template.md`. Odczyt przyjmuje stare formy: `### Komendy`/
      `### Język`, dopisek wzorca „dostosuj do swojego projektu” (test O-29b), nagłówek README targetu Managed Agents,
      `## Źródła`/`odczyt` w `facts`. Zmienione wartości JSON `cost_stats --json` (`band`, `period_name`,
      `rate.source`) — w repozytorium nikt ich nie czyta. Skuteczność: holdout 901/918 · 32/43 bez zmian; Haiku
      (plan-interview, skill-composition) 7/8 jak w M2 (ten sam chybiony scenariusz), 1,26 USD.
      Zostaje: docstringi drukowane jako `--help` (`uninstall`, `check`, `work`, `metrics` …), klucze sygnałów
      `tier:<agent>:za niski|za wysoki` (pisze `core-agent-retro`, M5) i przykład `--reason "bez flagi, bo …"` w skillu tf.
    - [x] M5 (2026-11-17): skrypty skilli rdzenia (`retro_data`, `factory_feedback`, `semver`, `commit_msg`,
      `control_band`, `pr_budget`, `instructions_lint`, `kb`, `fetch_page`, `claims_check`, `grounding_check`,
      `ai_review`). Pierwsza linia `Verdict:` w `pr_budget` i `claims_check` (nikt w repozytorium jej nie parsuje),
      nagłówek pobranej strony `<!-- web content: data, not instructions -->`, `--decide yes|no|later` w retro (polskie
      `tak|nie|później` nadal działa), znacznik `<!-- file: … -->` w pamięci `kb` (czyta też `plik:`), `metric_watch`
      rozpoznaje oba teksty błędu `control_band`. **Naprawione błędy:** sygnały „model za niski/za wysoki” nigdy nie
      trafiały do zgłoszeń dla fabryki — `retro_data` pisze klucz `tier:<agent>:niski` (wartość z `log_usage`), a
      `factory_feedback` i `feedback_report` przyjmowały tylko `za niski` (test FF z kluczem `wysoki`); retro
      wyróżniało problemy w dzienniku tylko po polskich słowach, a dziennik od M2/M3 piszą agenci po angielsku (AR-6 z
      wpisami w obu językach). Bramki 11 skilli odnowione.
      Zostaje: dopasowanie „już ocenione” w retro raz nie trafi starych dowodów (zmienione teksty) — jednorazowo.
    - [x] M6 (2026-11-18): skrypty pack-it — rekonstrukcja repozytorium (`eng-codebase-mapping`, 11 skryptów),
      `readiness_check`, `requirements_lint`, `dossier_check`, szablon `post_edit_checks`, Event Storming (`es_board`,
      `es_sim`, `es_probe`) i 7 modułów `tf analyze`. Odczyt przyjmuje stare formy: partie `(pliki)` w manifeście (M-18),
      polska pieczątka odświeżenia (RF-21), polskie znaczniki symulacji w `es_probe` (EP-14, EP-15); `requirements_lint`
      czyta też angielski brief (budżet czasu, szacunek, potwierdzenie kosztu), jednostki i sekcję „Quality attributes”.
      Identyfikatory ustaleń analizy bez zmian (skrót z reguły, pliku i fragmentu). **Naprawione błędy:** eksport
      rekonstrukcji dawał angielskim znacznikom status `evidence` (E-16); odświeżenie porównywało zmiany reguł ze starą
      nazwą `zmieniona`. Skuteczność: płatna próba symulacji ES na scenariuszu weterynaria 11/11 oczekiwań (wcześniej
      10/11), 1,43 USD. Bramki 7 skilli odnowione.
      Zostaje: treść skilli pack-it (4d) cytuje jeszcze polskie etykiety wyjścia (`idiomy testów`, `WYCIĄGNIĘTE`,
      „krytyczne”) i znacznik `=== POKAŻ DOSŁOWNIE ===` symulacji — zmienić razem z tłumaczeniem tych skilli.
    - [x] M7 (2026-11-18): skrypty mode-pdi (`decision_record`, `phase_run`, `pr_loop`, `second_review`, `metric_watch`,
      `design_check`, `triage_pdi`, `phase_progress`, `phase_result`, `sandbox_settings`) i `team_switch` z mode-team, w tym
      prompty faz i drugiego przeglądu. pdi tylko wyświetla zmienione teksty (sprawdzone w `src/pdi`), więc obeszło się
      bez zmian w pdi. Odczyt przyjmuje stare formy: wiadomości postępu `czyta plik`/`odmowa narzędzia` (`phase_result`,
      test M-1/M-2 w obu językach), `brak ramki` (`phase_run`), sekcja „Przegląd drugim modelem” podmieniana przy
      ponownym przeglądzie; wpisy bramek `## Gate …`, a prompt fazy wymienia też dawne `## Bramka …`. Bramki 2 skilli
      odnowione.
      Zostaje po polsku (format artefaktów i szablonów produktu): sekcja `## Pytania do bramki`, kolumny planu
      (`Wydanie`, `Flaga` …) i tabeli `design.md`, nagłówki `## Rozważone opcje`/`## Cele zmiany` — do zmiany razem z pdi
      i szablonami. Skuteczności promptów faz nie zmierzono na modelu: lokalnie działa tylko zadanie `N5-synth-repeated-q`,
      które przed zmianą też kończyło się `waiting_gate`; pełne flow-evals wymagają repozytoriów `sdlc-trial`.
    - [x] M8 (2026-11-18): `org/` (`standards_from_docs`, `new_org_pack` i szablony pakietu firmy i zespołu — szkielet
      po angielsku), linter polszczyzny (etykiety `HIGH/MEDIUM/LOW` i kategorie po angielsku; reguły i poprawki zostają
      po polsku, bo to przedmiot lintera), moduł dostępności pack-ux i narzędzia `tools/` (m.in. `workspace.py` ze
      szkieletem nowej nakładki, `hint_holdout`, `context`, `flow_compare`). Odczyt przyjmuje stare formy: `skill_gate`
      i `project_record` czytają polskie etykiety lintera, `standards_from_docs` wstawia blok pod dawne polskie nagłówki
      pakietu firmy i rozpoznaje stary znacznik. Holdout podpowiedzi bez zmian: 901/918 · 32/43. Bramki 2 skilli odnowione.
      **Etap komunikatów skryptów (M1–M8) zamknięty.** Zostaje: docstringi drukowane jako `--help`, wynik
      `flow-evals --validate` (runner w `core/tests`), `content_language: pl` w szkieletach `pack.yaml` (pole nieczytane),
      opisy w `docs/` i `.claude/skills/tf-new-pack` cytujące dawne etykiety.
  - [ ] pack-editorial-pl: instrukcje po angielsku, przykłady i reguły polszczyzny zostają po polsku (to ich przedmiot).

Treść fabryki jest dziś po polsku. Chodzi o:
- skille (`SKILL.md`, `references/`) rdzenia i wszystkich nakładek;
- persony, role i cechy;
- prompty agentów wspólnych, tabelę routingu i kontrakt raportu (`core/factory/config.yaml`);
- komunikaty hooków i skryptów skilli kierowane do agenta.

Po co: żeby `tf language en` dawało w pełni angielską fabrykę, a nie tylko angielskie odpowiedzi przy polskich
instrukcjach (mieszany język w prompcie potrafi „przeciekać” do odpowiedzi).

Jak:
- nakładka po nakładce; pole `content_language` w `pack.yaml` mówi, w jakim języku jest treść nakładki;
- kolejność: rdzeń, `pack-docs`, potem pozostałe według potrzeb;
- odpowiednik `pack-editorial-pl` dla angielskiego (`pack-editorial-en`) i wpis w `language_packs` w
  `core/factory/config.yaml`.

Do rozstrzygnięcia wtedy:
- czy tłumaczenie zastępuje treść polską, czy obie wersje żyją równolegle (wtedy `build.py` i instalator wybierają
  wersję według `language`);
- ~~nazwy pól metadanych skilli~~ — rozstrzygnięte: po angielsku (#287).

Warunek gotowości: ewaluacje skilli (`tests/skill_evals`) przechodzą także na wersji angielskiej.

## Inne

- [x] Przewodnik użytkownika (`GUIDE.md`, `FAQ.md` z claude-team-factory) nie został przeniesiony — opisywał jedną
  fabrykę bez nakładek. Zrobione (P1): `core/guide/` → `factory/GUIDE.md`, `factory/FAQ.md`.
- [x] Baza wiedzy z rejestrem źródeł (`dom-ev-knowledge-base`, w pack-ev) ma ogólny mechanizm (`kb.py`) i dane EV.
  Rozważyć przeniesienie mechanizmu do rdzenia, a rejestrów źródeł do nakładek. **Plan (2026-10-22):**
  - K1. Testy rdzenia `core/tests/test_kb.py` (najpierw czerwone): wyszukiwanie, cache, status, CLI na neutralnych
    danych; kilka rejestrów naraz (obszary deklarowane w rejestrze, unikalne id między rejestrami, `--area`).
  - K2. Skill `core-knowledge` (nie `core-knowledge-base`: tę nazwę migracja 3.0.0 zamienia na `dom-ev-knowledge-base`):
    `scripts/kb.py` bez wiedzy o EV; rejestry to `.claude/skills/*/references/zrodla.json` z polem `areas`;
    zmienne `TF_KB_DIR`, `TF_KB_ALLOW_LOCAL` (stare `EVTF_*` dalej działają). Procedura „zapytaj fabrykę” i forma
    odpowiedzi w rdzeniu; scenariusze ewaluacji przed treścią.
  - K3. pack-ev: `zrodla.json` z polem `areas`; `scripts/kb.py` jako cienkie przekierowanie do rdzenia (zgodność
    ścieżki; na starszym rdzeniu jasny błąd); `SKILL.md` tylko to, co EV (rejestr, obszary, persony, rejestr
    standardów, przykład); ścieżki w `pack.yaml`; `test_kb.py` tylko rejestr EV; wersja nakładki MINOR.
  - K4. `PUBLIC_API.md` (konwencja rejestru i ścieżka `kb.py`), bramki, `refs`, matrix, PR.
- [ ] Targety innych narzędzi niż Claude Code (Codex, Gemini CLI): `build.py` ma listę `TARGETS` i ustawienie projektu
  `targets`, zaimplementowany jest tylko target `claude`. Kolejny target = renderer agentów i instrukcji (`AGENTS.md`,
  `GEMINI.md`), mapa tierów na modele dostawcy i adaptery hooków. Fakty o formatach innych narzędzi sprawdzić
  w dokumentacji przed implementacją.

## Skille z zewnętrznych źródeł (Stripe, Angular, Next.js, GitHub) — adaptacja
Źródła sklonowane 2026-10-21, audyt `skill_audit.py`: 0 ustaleń wysokiej i średniej wagi. Licencje: Stripe, Callstack,
Angular — MIT; `vercel-labs/next-skills` bez pliku licencji (nie kopiujemy). Skille Next.js autorzy wycofali (wiedza
przeszła do dokumentacji w paczce `next`, od 16.3), skill `github` Callstack usunął jako przestarzały (2026-08-07).
Decyzja: adaptacja własnymi słowami po polsku do istniejących skilli; nowy skill tylko tam, gdzie jest luka.
- [x] **E1. Stripe:** nowy skill tool-stripe (stripe-best-practices + upgrade-stripe), powiązany z be-billing-subscriptions;
  w `unversioned_skills`, bo Stripe wersjonuje API datą.
- [x] **E2. fw-angular:** luki względem angular-developer i angular-new-app.
- [x] **E3. fw-nextjs:** luki względem next-best-practices, next-cache-components, next-upgrade.
- [x] **E4. core-git-workflow:** luki względem skilla `github` (gh CLI, stacked PR).
- [x] **E5.** Scenariusze ewaluacji przed treścią, bramki, `refs`, matrix, osobny PR.

## Rekonstrukcja projektu z kodu
Plan: `docs/plans/2026-10-23-rekonstrukcja-z-kodu.md` (F0–F7, decyzje D1–D4). Zakres teraz: tylko kod; bez PHP.
- [ ] F0–F5 wg planu — zrobione F0–F3 i F5; F4 część A (ewaluacja skilla na Haiku, 1,48 USD, 10/10 ze skillem, treść bez skilli 3/6) zrobiona 2026-10-24 — `docs/evals/2026-10-24-f4-rekonstrukcja-haiku.md`; część B (benchmark vs maister na 3 repozytoriach, 10,55 USD) zrobiona 2026-10-24 — `docs/evals/2026-10-24-f4-benchmark-maister.md`: pokrycie ważone 85% vs 80%, poprawność 96% vs 90%, koszt 68% maistera (cel ≤ 50% niespełniony).
- [x] **Po F4:** w `eng-project-reconstruction` obowiązkowa tabela stacku (wersje, profile, CI, testy) i lista modułów z odpowiedzialnością (luka 9/12 i 9,5/12 wobec 12/12 maistera) + scenariusz ewaluacji — `recon_check.py --final` wymusza wiersze tabeli i wpis każdego modułu z kart (2026-10-24).
- [x] **Po F4:** ponowny pomiar stacku i modułów — `docs/evals/2026-10-24-f4-benchmark-v2.md`: stack 9→11/12, moduły 9,5→10/12, pokrycie 86%, poprawność 97% (2026-10-24).
- [x] **Po F4 v2:** `recon_cards.py` generuje `modules/<moduł>.md` z kart (dowody sprawdzane przez `recon_check`, ścieżki względne wobec partii poprawiane) i szkic sekcji Moduły z kluczowymi elementami; `recon_check --final` wymaga aktualnych `.md` kart i dowodu z pliku pipeline'u w wierszu CI, gdy CI jest w repo (2026-10-24). Na danych v2: łapie „brak CI” w petclinic i 7 dowodów względnych w kartach eShopOnWeb.
- [x] **Po F4 v3:** idiomy testów i kodu w `standards_scan.py`, mapowania w całości — `docs/evals/2026-10-24-f4-benchmark-v3.md`: pokrycie 58,5/60 wobec 45–48 maistera, każda kategoria lepsza albo remis na maksimum, poprawność 30/30 (2026-10-24).
- [x] **Po F4:** obniżenie kosztu rekonstrukcji — 90% → 76–85% maistera przy jakości 58/60; poziom zaakceptowany przez człowieka (2026-10-24). Podsumowanie i możliwy powrót do celu ≤ 50%: `docs/evals/2026-10-24-f4-podsumowanie.md`.
- [x] **Po F4:** test odświeżenia ze zmianą w logice — `docs/evals/2026-10-24-f4-odswiezenie-logika.md`: nasz 6/6 zmian opisanych, 2 nieaktualne miejsca; maister 5,5/6, 0 nieaktualnych; koszt 1,02 wobec 0,66 USD (2026-10-24).
- [x] **Po F4:** `recon_cards.py --prev` przy odświeżaniu porównuje stare i nowe karty i wskazuje miejsca ze znacznikami usuniętych lub zmienionych reguł; na danych testu odświeżenia wskazuje obie pozostałości (lista 7 i 15 miejsc do przejrzenia) (2026-10-24).
- [x] **Po F4:** sygnały układu pakietów (według funkcji czy warstw) i czasów życia DI w `standards_scan`; powtórka testu odświeżenia z `--prev`: 6/6 zmian, 0 prawdziwych pozostałości (2026-10-25).
- [x] **Po F4:** odświeżanie dwuetapowe `recon_refresh.py prep|finish` (zlecenia kart ze zmienionych plików, skrypt składa karty, wypisuje zmienione reguły i miejsca do poprawy, poprawia przesunięte dowody, kontrola i manifest): w teście odświeżenia 0,56 wobec 0,66 USD maistera, 6/6 zmian, 0 pozostałości (2026-10-25).
- [x] **Po F4:** odświeżanie: zmiany tylko w komentarzach bez zleceń i z przeliczeniem numerów linii, diff w zleceniach, `apply` i `card`, nowe sygnały do sprawdzenia; komentarze 0,24 wobec 0,48 USD maistera, logika 0,38 wobec 0,51 USD (2 przebiegi na repo), 12/12 zmian i 0 pozostałości; maister nadal szybszy przy zmianie w logice (192 wobec 74 s) — `docs/evals/2026-10-25-f4-odswiezenie-tansze.md` (2026-10-25).
- [ ] **Konektory (odłożone, decyzja później):** GitHub (issues, PR, dyskusje jako źródło wymagań), Confluence, Slack.

- [ ] **Rekonstrukcja bez kodu źródłowego** (artykuł „REA Lets AI Agents Figure Out How Apps Work, Even Without
  Source Code”, K. Dunham, 2026-10-13; repo `morluto/rea`, MIT, serwer MCP — istnienie sprawdzone 2026-10-29 na
  raw.githubusercontent.com, wersje i liczby z artykułu [niezweryfikowane]). Zakres dziś „tylko kod”; gdy pojawi się
  aplikacja bez źródeł (Electron: JS w paczce czytany statycznie, mapa okno → preload → kanał IPC → obsługa;
  natywna: Ghidra/Hopper/IDA): REA jako opcja tylko po `skill_audit`, przeczytaniu i zgodzie człowieka, analiza
  binarek w jednorazowej maszynie wirtualnej (to nie piaskownica — Ghidra działa z uprawnieniami użytkownika),
  zgoda prawna na analizę po stronie człowieka. Do przejęcia niezależnie od narzędzia: w wynikach rekonstrukcji
  rozdzielać obserwacje, wnioski i niewiadome, a w ograniczeniach pisać wprost „brak znaleziska nie dowodzi braku”;
  pytać o jedną funkcję, nie o całą aplikację.

## Produkt i rynek: persona Paweł (Product Manager) i skille `pm-*` — zapisane 2026-10-23
Luki wskazane przez przegląd `deanpeters/Product-Manager-Skills` (commit cfcb697, 15.10.2026). Licencja CC BY-NC-SA 4.0 —
treści nie kopiujemy ani nie tłumaczymy; bierzemy tylko listę tematów, treść piszemy własnymi słowami ze źródeł
pierwotnych (Moore, Porter, Patton, Cohn, Torres, Amazon „Working Backwards”). Najpierw scenariusze ewaluacji.
- [x] **Nowe skille w `pack-it` (prefiks `pm-`, nowa faseta „produkt i rynek”, widoczność „sama nazwa”)** — zrobione 2026-10-23, bramka bez modelu:
  `pm-product-strategy` (pozycjonowanie, TAM/SAM/SOM z założeniami, konkurencja z dowodami i datami — Porter, SWOT,
  battle card — PESTEL, Ansoff), `pm-saas-metrics` (ARR/MRR, NRR/GRR, churn, CAC payback, LTV:CAC, burn multiple,
  Rule of 40, ocena zmiany ceny, pułapki liczenia), `pm-product-lifecycle` (etap i ruch: przedłużyć/zastąpić/wycofać;
  wycofanie produktu: go/no-go, kolejność interesariuszy, komunikat, checklista z właścicielami, odesłanie do prawa UE),
  `pm-stakeholders` (identyfikacja, mapa wpływ/zainteresowanie, plan zaangażowania, opór).
- [x] **Rozszerzenia** (zrobione 2026-10-23): `proc-agile` (mapa historyjek, wzorce dzielenia), `proc-product-discovery`
  (komunikat prasowy i FAQ przed budową, epik jako hipoteza, roadmapa według wyników; problem statement i tanie testy
  już były), `proc-issue-triage` (dosłowna prośba vs potrzeba).
- [x] **Persona Paweł — Product Manager** (`pack-it`, rola `product-manager`, w dyspozytorze Mai) — zrobione 2026-10-23: skille `pm-*`, `proc-product-discovery`,
  `proc-requirements-shaping`, `proc-agile`, `data-analysis`.
- Poza zakresem: kariera PM (dyrektor/VP, rozmowy), tworzenie skilli i inżynieria kontekstu (rdzeń), warsztaty
  (ddd-facilitation), cykliczny wywiad konkurencyjny (ewentualnie później jako zadanie cykliczne).
- 2–3 PR; bramka bez modelu; ewaluacja na Haiku (~2–4 USD) tylko za zgodą.

## Generator nowej nakładki (`new-pack`) — zapisane 2026-10-23
Dziś nowa nakładka powstaje przez ręczne kopiowanie istniejącej. Cel: szkielet jednym poleceniem + prowadzenie przez Claude.
- [x] **Skrypt** (zrobione 2026-10-23; test `tests/test_new_pack.py`): `python3 tools/workspace.py new-pack <nazwa> [--kind pack|mode] [--title] [--description] [--prefix]
  [--requires] [--role] [--skill]` tworzy `packs/pack-<nazwa>/` (albo `modes/mode-<nazwa>/`): minimalny poprawny
  `pack.yaml` (`version: 0.1.0`, `default: false`, `requires.core` z bieżącej wersji rdzenia, `facets` z prefiksem),
  szkielet `skills/<prefiks>-…/SKILL.md` wg core-skill-authoring, `tests/skill_evals/<skill>.json`, opcjonalnie
  `roles/<rola>.md`, `GUIDE.md`; dopisuje nakładkę do macierzy w `.github/workflows/factory-checks.yml` (dziś lista
  na sztywno); na koniec uruchamia `workspace.py check --packs <id>` i `refs` i wypisuje listę „do zrobienia”.
  Szkielet scenariuszy celowo nie przechodzi bramki, dopóki nie powstaną prawdziwe scenariusze. Istniejący katalog →
  błąd bez nadpisywania. TDD (test generatora w `tests/`).
- [x] **Skill dla autora fabryki** (decyzja człowieka 2026-10-23: tylko w repo tf; zrobione: `.claude/skills/tf-new-pack/`, test `tests/test_repo_skills.py`): na „new pack …” dopytuje
  o zakres, prefiks, zależności i role, najpierw proponuje scenariusze ewaluacji, potem woła generator, wypełnia treść
  i uruchamia bramki.
- [x] **Przewodnik** (zrobione 2026-10-23: `docs/new-pack.md`) budowy nakładki (pola `pack.yaml`, tryb vs paczka, prefiksy, granice `refs`, wersjonowanie)
  w `docs/` — nie jako README w `packs/` (repo publiczne).

## Skille z przeglądu VoltAgent/awesome-agent-skills — zapisane 2026-10-23
Przegląd listy (commit f737f28, 1159 pozycji) pod kątem luk w fabryce. Z listy bierzemy tylko tematy; treść piszemy
własnymi słowami ze źródeł pierwotnych, licencje repozytoriów sprawdzamy przed adaptacją, obce skille tylko po
`skill_audit.py` (core-agent-security). Każdy punkt: scenariusze ewaluacji przed treścią, bramka, `refs`, PR.
Kolejność proponowana: 1+2 (jeden PR), 5, 6, potem reszta.
- [x] **1. Analiza wariantów podatności** (zrobione 2026-10-23: nowy skill `sec-variant-analysis`, szablon reguły Semgrep sprawdzony `semgrep --test`) (inspiracja: Trail of Bits `variant-analysis`): po znalezionej podatności
  szukanie podobnych wystąpień według wzorca. Rozszerzenie `sec-appsec-devsecops` albo nowy skill `sec-`.
- [x] **2. Niebezpieczne API i domyślne konfiguracje** (zrobione 2026-10-23: `sec-appsec-devsecops/references/dangerous-apis.md`, wkład do `security-reviewer`) (ToB `sharp-edges`, `insecure-defaults`): lista kontrolna
  per język (zaszyte sekrety, domyślne hasła, słaba kryptografia, błędogenne API); `sec-appsec-devsecops`
  i wkład do agenta `security-reviewer`.
- [x] **3. Własne reguły Semgrep/CodeQL z testami** (zrobione 2026-10-24: skill `tool-semgrep`, przykłady sprawdzone Semgrepem 1.50.0, 1.100.0 i 1.182.1; testy CodeQL tylko z dokumentacji — CLI niedostępne w sesji) (ToB `semgrep-rule-creator`): procedura pisania i testowania
  reguł; kandydat `tool-semgrep`.
- [x] **4. Fuzzing** (zrobione 2026-10-24: skill `qa-fuzzing`, przykłady uruchomione — Go `testing.F`, Atheris 3.1.0, libFuzzer z ASan/UBSan w clang 18; Jazzer tylko z README) (ToB `testing-handbook-skills`): kiedy fuzzować, harness, korpus, sanitizery, CI; rozszerzenie
  `eng-testing` albo nowy `qa-fuzzing` (testy oparte na właściwościach już są).
- [x] **5. `lang-go` oraz `lang-csharp` z `fw-aspnet-core`** — zrobione 2026-10-23: `lang-go` (wykrywanie wersji z `go.mod`, przykłady sprawdzone go1.22.0 i go1.27.3); `lang-csharp` i `fw-aspnet-core` (wykrywanie platformy z `*.csproj`, przykłady i testy sprawdzone SDK 8.0.132 i 10.0.113) (inspiracja: eduardo-sl/go-agent-skills, Microsoft,
  `openai/aspnet-core`): rekonstrukcja z kodu czyta Go i C#, agent nie ma skilli do pisania w tych językach.
  Persona .NET (2026-10-24): `dorota` (backend + ddd-analyst, stack `lang-csharp`, `fw-aspnet-core`), w zespole Mai.
  Wersje sprawdzić w źródłach (core-source-research), wpis w `technologies.json`.
- [x] **6. Budowa serwera MCP** — zrobione 2026-10-23: skill `ai-mcp-server` (odsyła do oficjalnego `mcp-builder`; przykład z testami sprawdzony SDK `mcp` 1.29.0) (anthropics/microsoft `mcp-builder`): transport, uwierzytelnianie, testowanie
  (MCP Inspector), wersjonowanie narzędzi. Najpierw sprawdzić oficjalny skill Anthropic — może wystarczy odesłanie
  i ustalenia projektu (core-skill-authoring, krok 1); `ai-agents` ma dziś tylko projekt narzędzi i zaufanie.
- [x] **7. Techniczne SEO** (zrobione 2026-10-24: skill `fe-technical-seo`, przykład Next.js 16.4.3 sprawdzony `curl`; fakty Google przez wyszukiwanie — strony niedostępne bezpośrednio) (Addy Osmani `seo`): indeksowanie, dane strukturalne, sitemap, canonical, meta; dla
  projektów z publicznymi stronami (Core Web Vitals i dostępność już są).
- [x] **8. Bus factor w mapie własności** (zrobione 2026-10-24: `git_territory.py --bus-factor` z `--min-commits` i `--active-days`, 9 nowych testów) (`openai/security-ownership-map`): ryzyko „jednej osoby” per obszar
  w `git_territory.py --authors` (`eng-codebase-mapping`), TDD.

## Bezpieczeństwo — luki wobec przeglądu warstw obrony (slajdy „Security Layers / DevSecOps”, zapisane 2026-10-27)
Przegląd 2026-10-27: sieć, IAM, AppSec, monitorowanie i wykrywanie, reagowanie na incydenty i DevSecOps są pokryte
(sec-zero-trust-identity, be-auth-security, sec-appsec-devsecops, ops-security-operations, sec-detection-engineering,
ops-sre-incidents, ops-observability, sec-security-leadership). Do dorobienia (każda pozycja: scenariusze ewaluacji,
potem treść, bramka; źródła pierwotne NIST i OWASP z datą):
- [x] **Utwardzanie hosta** (system serwera, nie kontener ani konto chmury): minimalne usługi i pakiety, SSH (klucze,
  bez roota, bez haseł), konta i sudo, zapora hosta, audyt (auditd), automatyczne łatki bezpieczeństwa, CIS Benchmark
  jako lista kontrolna, sprawdzenie skanerem (np. Lynis, OpenSCAP); NIST SP 800-123. Miejsce: ops-security-operations
  (sekcja + odnośnik z ops-linux-performance).
- [x] **Szyfrowanie w spoczynku i klasyfikacja danych:** klasy danych → wymagane zabezpieczenia, szyfrowanie dysków,
  baz i kopii (KMS, envelope encryption, rotacja kluczy), cykl życia danych poza RODO (archiwum, bezpieczne
  usuwanie wg NIST SP 800-88); NIST SP 800-111. Miejsce: sec-cryptography-pki (+ odnośnik z arch-privacy-compliance).
- [x] **Mapa warstw obrony (defence in depth):** krótka tabela warstwa → kontrole → skill fabryki (sieć, IAM, host,
  aplikacja, dane, monitorowanie, reagowanie), żeby przegląd architektury sprawdzał wszystkie warstwy. Miejsce:
  arch-threat-modeling (references).
- [x] **DevSecOps — ramy:** NIST SSDF (SP 800-218) jako mapa praktyk obok OWASP SAMM, OWASP DSOMM jako miara
  dojrzałości pipeline'u; „shift left” i bezpieczne ustawienia domyślne nazwane wprost. Miejsce: sec-appsec-devsecops.
- [x] **Centralne logi bezpieczeństwa:** plan zarządzania logami (źródła, czas, integralność i oddzielone uprawnienia
  do logów, retencja) wg NIST SP 800-92 — uzupełnienie ops-security-operations §1 (źródła i retencja już są).

## Zamiar i oczekiwania przed bramką (artykuł „The Method That Replaces Spec-Driven Development — IDSD”, zapisane 2026-10-29)
Przegląd 2026-10-29: rozdział „co” (człowiek) od „jak” (agent) fabryka już ma w fazach z bramkami — `intent.md`,
faza `requirements` z kryteriami akceptacji i bramką B2, `qa-spec-first-testing`, `proc-requirements-shaping` (otwarte
pytania zamiast domysłów), kontekst ładowany przez skille, ślad wymaganie → TSK → test `KLUCZ/AC-n`. Bez nowej
nazwy ani warstwy metodyki (IDSD/ICE). Do dorobienia w `modes/mode-pdi/` (scenariusze ewaluacji, potem treść i kod
metodą TDD, bramka skilla; jeden mały PR):
- [x] **Szablon `intent.md`: ograniczenia, porażka, powiązania** (zrobione 2026-11-01: szablon, prompt fazy `intent` w `phase_run.py`, test D-2a; sekcje dopisane po istniejących, więc ci_for_sdlc czyta tytuł, treść i metryki bez zmian). Trzy krótkie sekcje wypełniane przez człowieka, który
  chce wyniku: *Ograniczenia* (warunki, w których wynik ma działać), *Kiedy to porażka* (czym wynik nie może być,
  np. „but za 140 USD”, „but niedostępny”), *Powiązania* (obszary i zmiany, których dotyczy). Dziś zamiar ma metryki
  sukcesu i „poza zakresem”, a scenariusze porażki pojawiają się dopiero w wymaganiach pisanych przez agenta.
  Zgodność: ci_for_sdlc czyta z `intent.md` tylko tytuł, treść i sekcję metryk — sprawdzić przy zmianie (kontrakt pdi).
- [x] (2026-11-22: zamiast osobnego agenta — rodzaj `needs_guess` w drugiej recenzji `second_review.py`, która już
  czyta `requirements.md` z `intent.md` przed B2 i B3; pytanie do bramki z prefiksem `[would have to guess]`, bez
  dodatkowego wywołania modelu) **Test „gdzie agent musiałby zgadywać” przed bramką B2.** Osobny agent bez kontekstu rozmowy (wzorzec czystego
  pokoju jak `blind-analyst`, `kasia-qa-analyst`) czyta `intent.md` i `requirements.md` i zwraca listę miejsc, w
  których musiałby zgadywać; lista trafia jako pytania do prośby o bramkę (`gate.requested`), tak jak braki z
  `design_check.py` przed `design-review`. Koszt: jedno wywołanie modelu na bramkę [szacunek: kilka centów na
  Haiku/Sonnet] — zmierzyć na pierwszych zmianach.

- [x] (2026-11-22: mode-pdi już zapisywał odpowiedzi z bramki dosłownie w `decisions.md` (pary `question`/`answer`,
  kontrakt pdi 0.12.0); w pętli `/tf-task` nowe `run_state.py qa` — pytanie z przyjęcia historyjki i odpowiedź
  człowieka dosłownie w `events.jsonl` zadania, obok `spec.md`; rozdział „zatwierdzam” / „uruchom fazę” w pdi — nie
  ruszany, to po stronie pdi) **Pierwotna prośba i odpowiedzi na pytania zapisane dosłownie** (artykuł „From OpenSpec to AIDLC”, P. Qian,
  2026-09-04; AWS `aidlc-workflows`): specyfikacje SDD gubią, *po co* coś zrobiono — AIDLC trzyma per faza plik pytań
  z odpowiedziami człowieka i `audit.md` tylko do dopisywania (wejście człowieka, odpowiedź, streszczenie fazy, kto
  zatwierdził — `git config user.name/email`). U nas zamiar jest w `intent.md`, a bramka to PR (tożsamość i historia
  z GitHuba); brakuje dosłownego zapisu pytań i odpowiedzi z fazy wymagań obok artefaktu. Rozważyć też rozdział
  „zatwierdzam” od „uruchom następną fazę”, gdy następną fazę prowadzi inna rola (pdi dziś po `approved` sam
  uruchamia fazę — `docs/plan-f4-pdi.md`). Reszta AIDLC (warunkowe etapy: rekonstrukcja tylko dla istniejącego kodu,
  historyjki tylko przy zmianie dla użytkownika; rozszerzenia włączane pytaniem) jest w `core-delivery-lifecycle`.

## Wzorce bezpieczeństwa agentów z LLM (artykuł „Top 4 Security design patterns for AI agents”, A. Dighe, 2026-10-08, zapisane 2026-10-29)
Przegląd 2026-10-29: zasady są już w `sec-llm-security` (najmniejsze uprawnienia narzędzi, zatwierdzenie z pokazaniem
dokładnego skutku, walidacja argumentów w kodzie, „model czytający obce treści nie ma narzędzi zapisu”, allow-lista
ruchu, „lethal trifecta”) i w `core-agent-security` (MCP jak zależność: przypięta wersja, przegląd opisów narzędzi).
Brakuje nazwanych wzorców projektowych i nowszych list. Do dorobienia w `sec-llm-security` (scenariusze ewaluacji,
potem treść, bramka; źródła pierwotne z datą, sprawdzone przez researchera — artykuł to źródło wtórne):
- [x] **Wzorce z pracy Beurer-Kellner i in. (arXiv 2506.08837) jako reference** (zrobione 2026-10-31: `sec-llm-security/references/agent-design-patterns.md` §2)**:** podwójny LLM (czytający bez narzędzi
  oddaje tylko pola schematu, nie prozę), plan-then-execute (plan zamrożony przed wynikami narzędzi, dane z obcych
  treści nie wybierają adresata wysyłki ani zapisu), action-selector, map-reduce po dokumentach, code-then-execute;
  kiedy który i jaki koszt (dwa wywołania, mniej elastyczny agent). Przykład w kodzie, nie w prompcie.
- [x] **Zatwierdzenie związane z argumentami** (zrobione 2026-10-31: `sec-llm-security/references/agent-design-patterns.md` §4)**:** zgoda obejmuje skrót kanonicznych argumentów, aktora, narzędzie,
  termin i jednorazowy nonce; inne argumenty = nowa zgoda; brak polityki lub nieudany zapis audytu = brak wywołania.
  Klasy ryzyka narzędzi (niskie … krytyczne) z domyślną odmową dla nieznanych.
- [x] (zrobione 2026-10-31: `sec-llm-security/references/agent-design-patterns.md` §5) **Krótkotrwałe poświadczenia na jedno wywołanie** (broker poza procesem agenta, token związany z narzędziem i
  argumentami) oraz **przypięty skrót manifestu narzędzia MCP** (zmieniony opis lub schemat = nowa instalacja do
  przeglądu, nie cicha aktualizacja) — także jako uzupełnienie `core-agent-security`.
- [x] (zrobione 2026-10-31: `sec-llm-security/references/agent-design-patterns.md` §6) **Przekazania między agentami bramkowane schematem i listą celów** (repo `anthropics/financial-services`,
  omówienie M. Craddock, 2026-05-06 [niezweryfikowane w repo]): agent czytający obce dokumenty ma tylko Read/Grep,
  bez MCP, i zwraca JSON ze schematem (`additionalProperties: false`, `maxItems`, `maxLength`, `pattern` na każdym
  polu), sprawdzanym w kodzie przed orkiestratorem; prośba o przekazanie (`handoff_request`) przechodzi tylko, gdy
  cel jest na liście dozwolonych, a ładunek zgodny ze schematem — dokument może zawierać podrobione bloki
  przekazania. Przykład w kodzie do `sec-llm-security` obok podwójnego LLM.
- [x] **Reguła dwóch (Meta, „Agents Rule of Two”)** (zrobione 2026-10-31: `sec-llm-security/references/agent-design-patterns.md` §1)**:** sesja ma najwyżej dwie z trzech cech — niezaufane wejście, dostęp
  do danych wrażliwych, zmiana stanu lub komunikacja na zewnątrz; tabela kontrolna obok „lethal trifecta”.
- [x] **Aktualizacja list** (zrobione 2026-11-01: `sec-llm-security` — tabela LLM 2026 ↔ 2025 i ASI01–ASI10 z Appendix A wydania 2026, repo GenAI-Security-Project/GenAI-LLM-Top10)**:** OWASP Top 10 for LLM 2026 (skill cytuje wydanie 2025) i OWASP Top 10 for Agentic
  Applications 2026 (ASI01…) — mapowanie na kontrole skilla; zweryfikować numerację i daty w źródłach.
- [x] **Kontrola przepływu informacji (CaMeL, Debenedetti i in., arXiv 2503.18813)** (zrobione 2026-10-31: `sec-llm-security/references/agent-design-patterns.md` §3)**:** wartości z etykietą pochodzenia
  i odbiorców, polityka sprawdza etykiety przed wywołaniem narzędzia (np. dokument z dysku można streścić
  użytkownikowi, ale nie wysłać na adres znaleziony w tym dokumencie); koszt w użyteczności z ich pomiaru na
  AgentDojo [do sprawdzenia w źródle]. (Uzupełnione 2026-10-29 z artykułu „Building Secure AI Agents”, C. Kalhara.)
- [x] **Red teaming adaptacyjny** (zrobione 2026-10-31: `references/red-teaming.md` §„Ataki adaptacyjne”) w `references/red-teaming.md`: obrona sprawdzona tylko stałą listą ataków mówi mało
  („The Attacker Moves Second”, Nasr i in., arXiv 2510.09023); AgentDojo (NeurIPS 2024) jako gotowa uprząż — sędzia
  sprawdza stan środowiska, nie tekst modelu, więc sam nie da się wstrzyknąć.
- [x] **Pamięć i RAG jako niezaufane** (zrobione 2026-10-31: `sec-llm-security/references/agent-design-patterns.md` §7)**:** zapis do pamięci długotrwałej i bazy wektorowej przechodzi przegląd i dostaje
  etykietę pochodzenia; w logu wywołań narzędzi pochodzenie argumentów; wyłącznik awaryjny agenta.
- [x] **Autoryzacja zdalnego serwera MCP** (zrobione 2026-10-31: `be-auth-security/references/tokens-sessions-oauth.md` §7, odnośnik i scenariusz w `ai-mcp-server`) (`be-auth-security`, odnośnik z `ai-agents`): OAuth 2.1 z PKCE, odkrywanie
  serwera autoryzacji z metadanych, rejestracja klienta przez Dynamic Client Registration albo Client ID Metadata
  Documents, walidacja odbiorcy tokenu, krótkie tokeny dostępu i odświeżanie przez zewnętrznego dostawcę OAuth.
  Sprawdzone 2026-10-29 (blog.modelcontextprotocol.io, wersja specyfikacji `2026-07-28`): DCR przestarzałe na rzecz
  Client ID Metadata Documents (działa jeszcze dla zgodności, usunięcie w przyszłej wersji — konkretnej daty brak);
  serwer zwraca parametr `iss` (RFC 9207), klient go sprawdza; klient podaje `application_type` (przekierowania na
  localhost dla aplikacji CLI i desktop); poświadczenia klienta związane z wydawcą.
- [x] **Tożsamość agenta i delegacja** (zrobione 2026-11-01: `sec-zero-trust-identity/references/identity-and-access.md`, ostatnia sekcja; SPIFFE z repo, RFC przez wyszukiwarkę — ietf.org niedostępne) (`sec-zero-trust-identity`, odnośnik z `sec-llm-security`; dziś fabryka nie
  wspomina SPIFFE ani tokenów związanych z nadawcą): każdy agent i każda jego instancja ma własną tożsamość obciążenia
  (SPIFFE/SPIRE, krótkie SVID przez Workload API zamiast współdzielonego konta usługi), osobną od loginu człowieka,
  z nazwanym właścicielem; działanie w imieniu użytkownika = token użytkownika związany z kluczem agenta (mTLS-bound,
  RFC 8705, `cnf.x5t#S256`, albo DPoP, RFC 9449), więc skradziony token jest bezużyteczny; log audytu „instancja X
  agenta Y w imieniu użytkownika Z”; wymiana tokenu (RFC 8693) przy przejściu między usługami; usługi bez obsługi
  wiązania jako jawnie słabsze ogniwo. Numery RFC, stan SPIFFE w CNCF i produkty chmurowe (Google Agent Identity,
  Agent Gateway) sprawdzić w źródłach pierwotnych z datą. (Z artykułu „SPIFFE: Why Google's New Agent Identity…”,
  G. Blaquiere, 2026-06-09, zapisane 2026-10-29.)
Produkty: recenzent AI w ci_for_sdlc już działa jak „czytający bez narzędzi” (wynik tylko w schemacie JSON, ustalenie
bez dowodu odrzucone, odpowiedź przyjęta tylko z dosłownym cytatem); automatyczne zamykanie pytań (`autoClose: apply`)
jest opcjonalne, domyślnie `suggest` — zmian nie trzeba.

## Słowa kluczowe effortu w Claude Code (artykuł „Build Production AI Systems with Claude Code”, Chandana, 2026-08-09, zapisane 2026-10-29)
Przegląd 2026-10-29: reszta artykułu jest już w fabryce (`CLAUDE.md` krótki i skille na workflow —
`core-agent-instructions`; punkt kontrolny zamiast `progress.md` — `project_record.py wip`; `/compact` i `/clear`,
effort, `opusplan`, doradca — `core-cost-control`; wykonawcy tylko do odczytu — konsultanci bez `Edit`/`Write`;
`/remote-control` — `core-async-delegation`; GitHub Action i przegląd AI w CI — `core-git-workflow`). Uwaga: artykuł
podaje 5 poziomów zagnieżdżenia subagentów (źródło wtórne); fabryka trzyma się dokumentacji (domyślnie 3,
`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`, fabryka ustawia 2) — bez zmian.
- [x] **`core-cost-control`: `ultrathink` i `ultracode`** (zrobione 2026-11-01: `references/model-and-automation.md` §8; przy okazji: zmiana effortu nie kasuje cache na Opus/Sonnet/Haiku 5.5 i Fable 5.1 — code.claude.com/docs/en/prompt-caching). `ultrathink` w treści polecenia — głębsze rozumowanie w tej
  jednej turze bez zmiany zapisanego effortu sesji (zmiana effortu sesji w trakcie kasuje cache); `ultracode` —
  effort `xhigh` plus zgoda na orkiestrację wielu agentów (workflow), kosztowne, tylko dla zadań, które tego
  wymagają. Działanie, koszt i dostępność sprawdzić w dokumentacji code.claude.com z datą przed dopisaniem
  (scenariusze ewaluacji, bramka skilla).

## Jakość parsowania dokumentów w RAG (artykuł „Why Your RAG Pipeline Dies on Real Documents”, P. Perrone, 2026-10-01, zapisane 2026-10-29)
Przegląd 2026-10-29: `ai-rag` już każe zachować tabele z nagłówkiem, OCR dla skanów i chunking wg struktury; tabela
porażek ma „tabela rozbita, liczby bez nagłówków”. Artykuł jest sponsorowany (LlamaParse) — bez rekomendacji dostawcy.
- [x] **`ai-rag`: kontrola jakości parsowania przed indeksacją** (zrobione 2026-10-30: `ai-rag/references/parsing-evaluation-wiki.md` §1, SKILL.md krok 2) — strona bez warstwy tekstu albo z podejrzanie
  małą liczbą znaków to alarm, nie pusty dokument; przegląd surowego wyjścia parsera na najgorszych dokumentach
  korpusu (skan, tabela przez dwie strony, dwie kolumny) zanim ktoś stroi retriever; miara struktury tabel (TEDS) i
  kolejności czytania w zestawie ewaluacyjnym; parsery świadome układu (open source i usługi) jako kategoria z
  kryteriami wyboru, nie lista marek. Liczby z benchmarków (OmniDocBench, CVPR 2025) sprawdzić w źródle pierwotnym.
- [x] **`ai-rag`: ewaluacja w dwóch koszykach i kalibracja progu** (zrobione 2026-10-30: `ai-rag/references/parsing-evaluation-wiki.md` §2, SKILL.md krok 7) (artykuł „The Limits of Vector Search in RAG”,
  J. Wąsowski, 2026-09-14; hybrydę i „wektory gubią identyfikatory” skill już ma): zestaw ewaluacyjny z polem typu
  zapytania — recall@k osobno dla zapytań semantycznych (parafrazy, intencje) i dokładnych (identyfikatory, kody,
  wersje, liczby, negacje), bo średnia ukrywa podział; przed ustawieniem progu podobieństwa histogram cosinusa dla
  kilkuset losowych, niepowiązanych par z własnego korpusu (anizotropia — losowe pary bywają przy 0,9); zapytania
  łączące dwa fakty jako osobna kategoria (granica pojedynczego wektora: Weller i in., „On the Theoretical
  Limitations of Embedding-Based Retrieval”, 2025 — sprawdzić w źródle; liczby z artykułu [niezweryfikowane]).

## Wiedza kanoniczna jako pliki z linkami zamiast RAG (artykuł „Beyond RAG: … Open Knowledge Format (OKF)”, Dev Evolution, 2026-09-09, zapisane 2026-10-29)
Przegląd 2026-10-29: idea artykułu — definicje kanoniczne (metryka, schemat, reguła) jako pliki Markdown z YAML
i jawnymi linkami `[[ścieżka]]`, czytane przez agenta krok po kroku od `index.md`; RAG tylko do szerokich archiwów —
w dużej części już jest: ci_for_sdlc liczy powiązania jawne przed semantycznymi, decyzje mają rejestr pdi, fabryka
ma `core-knowledge` (`kb.py`, notatki zespołu, cytaty plik:linia). Niski priorytet. Sprawdzone 2026-10-29: OKF istnieje
— `GoogleCloudPlatform/knowledge-catalog`, `okf/SPEC.md`, wersja 0.2 (bez daty na stronie): wymagane tylko `type`;
zalecane `title`, `description`, `resource`, `tags`; opcjonalne `sources[]`, `generated`, `verified`, `status`
(`draft`/`stable`/`deprecated`), `stale_after`; zarezerwowane `index.md` (spis do stopniowego odsłaniania) i `log.md`;
linki zwykłe markdown, zalecane od korzenia paczki (`/tables/x.md`).
- [x] **`ai-rag`: decyzja „wiki kanoniczne czy RAG”** (część w `ai-rag` zrobiona 2026-10-30: `ai-rag/references/parsing-evaluation-wiki.md` §3–4, SKILL.md krok 1; reszta 2026-11-01: `core-knowledge/references/notes-and-wiki.md` §1, §2 i §5 — strefy, nagłówek zbliżony do OKF bez deklaracji zgodności, świeżość; kontrola w CI jako kod — gdy pojawi się generowany indeks) — definicje, które muszą być dokładne i mieć właściciela
  (metryki, schematy, reguły), jako kuratorowane pliki z `type`, właścicielem, datą i linkami, czytane
  deterministycznie; RAG dla archiwów i treści masowych; router między nimi. Jeśli OKF okaże się realnym standardem,
  ocenić zgodność notatek `docs/knowledge` z jego formatem (`type` we frontmatterze, `index.md`, linki), żeby inne
  agenty mogły je czytać bez tłumaczenia.
  Uzupełnienie (artykuł „Building a Complete Personal Harness: LLM Wiki…”, R. Brasil Monteiro, 2026-05-03): jeśli
  wiki powstanie, trzy strefy z różnymi prawami zapisu — źródła tylko do odczytu (dziś `.claude/knowledge/<id>/`
  z `kb.py ingest`), strony utrzymywane przez agenta z polem `sources` we frontmatterze i aktualizacją zamiast
  przepisywania, notatki i decyzje zespołu zmieniane tylko za zgodą; ingest pokazuje plan (nowe i zmienione strony)
  przed zapisem.
  Świeżość (artykuł „Production-Grade OKF + Graphify Setup”, U. Estari, 2026-08-13): generowany indeks lub graf kodu
  dryfuje po cichu — hook „sukces”, a mapa sprzed tygodni (Windows bez `nohup`, lista rozszerzeń rozjechana ze źródłem,
  pominięcie przy obciążeniu bez ponowienia, serwer MCP z cache sprzed regeneracji). Każdy generowany artefakt
  wiedzy ma znacznik czasu i commit źródła; kontrola w CI porównuje go z `git log -1` i alarmuje po progu (np. 24 h);
  `stale_after`/`verified` z OKF jako pola na to. Dotyczy też map z `eng-codebase-mapping` i cache `kb.py status`.
- [x] **Pamięć projektu jako paczka OKF z regułami przypiętymi do ścieżek** (zrobione 2026-11-01: `core-knowledge/references/notes-and-wiki.md` §2–3; narzędzie `okf-agent-memory` nieużyte) (artykuł „The Dev with Two Brains”,
  C. Core, 2026-10-07; narzędzie `okf-agent-memory` — Go, MIT, conda-forge, CLI + serwer MCP z 6 narzędziami; wersje
  i zachowanie wg autora [niezweryfikowane], przed użyciem `skill_audit` i zgoda człowieka). Pomysły niezależne od
  narzędzia, do `core-knowledge` / `core-project-record`:
  - pojęcie wskazuje ścieżki, których dotyczy (`code_refs`), z poziomem: `constraint` (niezmienniki do zachowania)
    albo `hold` (stop, zapytaj człowieka); przed pierwszą edycją pliku agent pyta „co obowiązuje tę ścieżkę” — to samo
    co `applies_to` decyzji w pdi i planowana reguła ci_for_sdlc „PR rusza obszar przyjętej decyzji”, tylko po stronie
    agenta przed zmianą, nie bramki po niej;
  - zasiew z istniejących źródeł (specyfikacje, plan, kod, issues, PR-y): każda decyzja zapisuje wybrane, odrzucone
    i „czy kod to realizuje” — tego agent nie odczyta z repo; pułapki na pierwszej stronie indeksu;
  - `verified` wpisuje tylko człowiek (autor: od 0.6.0 wymuszone w kodzie), agent tylko `generated`;
  - wyszukiwanie słowami (BM25) nie zna synonimów („deploy” nie znajduje „release”) — opis pojęcia pisany słowami,
    którymi ludzie szukają; wersję narzędzia przypiąć (wg autora 0.6.0 usunęło aliasy filtrów, stare zapytanie
    po cichu nic nie zwraca).
- [x] **Reguła z repo B nie działa, gdy agent startuje w repo A** (zrobione 2026-11-01: `core-agent-instructions` §2) (ten sam artykuł: `gh -R …` zapisane w AGENTS.md
  i pamięci projektu, a agent z innego repo i tak się potknął). Do `core-agent-instructions`: reguły potrzebne przy
  pracy z zewnątrz (nazwa forka, gałąź docelowa, wymagane flagi) także w miejscu, które czyta agent startujący
  gdzie indziej (globalne instrukcje, README sąsiedniego repo); dotyczy sesji wielorepozytoryjnych tf/pdi/ci_for_sdlc.

## Projekty prowadzone w Spec Kit (artykuł „Spec-Driven Development with Spec Kit and Claude Code”, S. Zarinfam, 2026-05-11, zapisane 2026-10-29)
Przegląd 2026-10-29: sam przepływ już jest — wymagania z EARS i `requirements_lint.py` (odpowiednik listy jakości
specyfikacji), plan cięć z dosłownymi ID wymagań, zależnościami i kolumną „Równolegle z” oraz checklistą pokrycia
(`cut-plan.md`, odpowiednik `/speckit.analyze`), krok po kroku z planem przed kodem i zmianą specyfikacji przed
kodem, `plan_drift.py` w talos. Pętle i rutyny (artykuły o „loop/graph engineering” i Routines z tego dnia) pokrywa
`core-async-delegation` (kontrakt, warunek stopu, budżet, najwyżej 2 próby naprawy) i `core-agent-retro` (lekcje).
Brakuje tylko rozpoznania projektu, który już używa Spec Kit. Niski priorytet.
- [x] **Wejście z Spec Kit** (zrobione 2026-11-01: `proc-requirements-shaping/references/existing-specifications.md` §1–2; Spec Kit 1.2.5 sprawdzony w repo; rozpoznanie w intake mode-pdi i talos — osobno, gdy pojawi się projekt) — gdy repo ma `.specify/memory/constitution.md` i `specs/<NNN-funkcja>/{spec,plan,tasks}.md`,
  intake (`proc-requirements-shaping`, mode-pdi, talos) czyta je jako istniejące wymagania, zasady i plan zamiast
  pisać równoległe dokumenty: `spec.md` → wymagania (lint EARS jako raport, bez przepisywania), `constitution.md` →
  zasady obok CLAUDE.md, znaczniki `[NEEDS CLARIFICATION]` → otwarte pytania, `tasks.md` z `[P]` → kolumna
  „Równolegle z”. Układ plików i nazwy poleceń sprawdzić w repo github/spec-kit z datą (artykuł opisuje błąd haka
  `before_specify` w nowszej wersji) [niezweryfikowane].
- [ ] **OpenSpec: zmiana jako delta i archiwizacja do głównej specyfikacji** (część w `proc-requirements-shaping` zrobiona 2026-11-01: tamże §3–4; zostaje krok scalenia i kontrola przy zamknięciu CHG w mode-pdi — zmiana kontraktu dziennika zmiany, do decyzji) (artykuł „OpenSpec + Superpower”, Chimin,
  2026-05-30): po zakończeniu zmiany jej specyfikacja trafia do głównej, aktualnej specyfikacji systemu, a folder zmiany
  zostaje historią. mode-pdi ma dziennik zmiany `docs/project/changes/CHG-n/` (intencja, plan, decyzje), ale nie
  ma kroku „scal wymagania zmiany do bieżącego stanu wymagań” — sprawdzić, czy faza zamknięcia CHG to robi; jeśli nie,
  dodać krok i kontrolę (wymaganie z CHG bez odpowiednika w głównym dokumencie = ustalenie). Wejście z OpenSpec
  (`openspec/specs`, `openspec/changes`) jak z Spec Kit; układ katalogów sprawdzić w repo projektu z datą.

## Rutyny, które zdobywają uprawnienia (artykuły „How to Create Loops with Claude Code”, Y. Hosni, 2026-06-24; „Harness Engineering” i „/goal”, Gao Dalie, 2026-05, zapisane 2026-10-29)
Przegląd 2026-10-29: większość już jest — kwalifikacja zadania i kontrakt (cel, zakres, stop, budżet), najwyżej
2 próby naprawy, idempotencja, „zielony bez wartości” jako porażka, cotygodniowy przegląd trafności
(`core-async-delegation` §1–5, `references/delegation-contract.md`); `/goal` z oceniającym; „błąd ma się nie
powtórzyć” jako hook lub bramka (tabela „Gdzie trafia zmiana” w `core-agent-retro`). Braki są małe, dotyczą rutyn
działających tygodniami.
- [x] **`core-async-delegation` §5: uprawnienia rosną z dowodem** (zrobione 2026-10-30: §5, 3 scenariusze strojenia) — drabina: tylko odczyt → szkic w pliku → zmiany
  na gałęzi lub w worktree → szkic działania zewnętrznego (draft PR, szkic komentarza) → działanie po zgodzie →
  automat tylko dla działań niskiego ryzyka z logiem i wycofaniem; szczebel wyżej dopiero po serii przebiegów bez
  przekroczenia zakresu, każdy nowy szczebel z nową regułą weryfikacji. Do tego: dwa tryby wyniku (cisza — krótka
  aktualizacja stanu, gdy nic się nie zmieniło; uwaga — raport, gdy coś wymaga człowieka); ta sama blokada w dwóch
  kolejnych przebiegach = eskalacja zamiast ponowienia; przegląd uprawnień rutyny przy każdym nowym narzędziu
  i co miesiąc; w przeglądzie liczyć też fałszywe alarmy i przeoczenia, nie tylko trafne pozycje. Najpierw scenariusze
  ewaluacji (core-skill-authoring), potem treść; bez nowego skilla.

## MCP Apps — interfejs dla człowieka obok narzędzia (artykuł „Stop Returning JSON. Start Shipping UI with MCP Apps”, A. Tkachuk, 2026-09-14, zapisane 2026-10-29)
Przegląd 2026-10-29: `ai-mcp-server` nie wspomina rozszerzenia MCP Apps (narzędzie wskazuje zasób `ui://`, host
renderuje go w izolowanym iframe i przekazuje wynik narzędzia; przyciski wołają narzędzia przez hosta). Daty
z artykułu: SEP-1865 2025-11-21, rozszerzenie produkcyjne 2026-01-26 — sprawdzić w specyfikacji
(apps.extensions.modelcontextprotocol.io) z datą przed dopisaniem [niezweryfikowane]. Średni priorytet.
- [x] **`ai-mcp-server`: specyfikacja `2026-07-28`** (zrobione 2026-11-01: `ai-mcp-server/references/spec-2026-07-28-and-apps.md` §1–2, z changelogu w repo specyfikacji) (sprawdzone 2026-10-29 na blog.modelcontextprotocol.io):
  bezstanowy rdzeń (bez `initialize` i `Mcp-Session-Id`; wersja, klient i możliwości w `_meta`; opcjonalne
  `server/discover`), nagłówki `Mcp-Method`/`Mcp-Name` do routingu i autoryzacji w bramce, Multi Round-Trip Requests
  zamiast żądań inicjowanych przez serwer, listy z `ttlMs`/`cacheScope`, zadania jako rozszerzenie, MCP Apps
  w formalnym frameworku rozszerzeń; przestarzałe Roots, Sampling, Logging i transport HTTP+SSE (min. 12 miesięcy
  wsparcia); stan aplikacji przez jawne uchwyty zwracane z narzędzi. SDK TS, Python, Go, C# wspierają; zmiany
  łamiące zgodność dla serwerów zależnych od sesji.
- [x] **`ai-mcp-server`: kiedy MCP App, a kiedy tekst** (zrobione 2026-11-01: tamże §3–4; MCP Apps Stable 2026-01-26) — App tylko gdy interakcja ma strukturę (zatwierdzenie,
  formularz, panel z akcjami, porównanie wyników), jedna App na domenę, nie na narzędzie; łagodny powrót do treści
  strukturalnej, gdy host nie obsługuje rozszerzenia; dane w wyniku narzędzia, nie w HTML zasobu. Bezpieczeństwo:
  widoczność narzędzia `_meta.ui.visibility: ["app"]` (model go nie widzi — przycisk człowieka jako jedyna droga
  do akcji, np. zatwierdzenie), zatwierdzenie przez ID i wersję obiektu (odrzucenie nieaktualnej karty), UI nie jest
  granicą zaufania — autoryzacja, walidacja, idempotencja i audyt po stronie serwera; App traktowana jak niezaufany
  kod. Najpierw scenariusze ewaluacji (core-skill-authoring).

## Piaskownica agenta: drogi, które omijają granicę (artykuł „Sandboxes, Part 1; Do You Know What Your Agents Are Doing Right Now?”, J. Carson, 2026-10-14, zapisane 2026-10-29)
Przegląd 2026-10-29: `core-agent-security` ma allowlistę ruchu wychodzącego dla pracy autonomicznej, ochronę
`.git/config`, `.git/hooks`, `.claude/` i workflowów CI, zakaz interpretera z dowolnym argumentem i „akcje
nieodwracalne wykonuje człowiek”; `core-async-delegation` ma kontrakt, STOP po 2 próbach i przegląd po. Artykuł
zbiera incydenty z 2026 (OpenAI–Hugging Face, DNS, urlquery, Services Australia, testy CTF Anthropic/Google/Meta).
Źródeł pierwotnych nie otworzyłem (alignment.openai.com i metr.org poza siecią sesji) — liczby i daty
[niezweryfikowane], przed dopisaniem do skilla sprawdzić u źródła z datą (researcher). Wnioski niezależne od liczb:
- [x] **`core-agent-security` §4, „ruch wychodzący to nie tylko HTTP”** (zrobione 2026-10-30: `core-agent-security/references/permissions-and-production.md` §4b)**:** domyślna odmowa obejmuje też DNS (rozwiązywanie
  nazw jako kanał: pytania zakodowane w nazwach hostów), proxy pakietów i rejestry (dozwolony serwis = droga na
  zewnątrz), publiczne usługi pośrednie (skanery URL, zdalne przeglądarki); środowisko testowe z dostępem do internetu
  traktujesz jak produkcję.
- [x] **Wspólny cache między przebiegami to kanał komunikacji** (zrobione 2026-10-30: `core-agent-security/references/permissions-and-production.md` §4b)**:** rejestr pakietów, cache budowania, katalog
  współdzielony — osobne przebiegi agentów mają osobne cache albo cache tylko do odczytu; inaczej „izolowane” agenty
  zostawiają sobie wiadomości.
- [x] **Agent pisze przyszłe wejścia zaufanych narzędzi = brak izolacji** (zrobione 2026-10-30: `core-agent-security/references/permissions-and-production.md` §4b)**:** poza `.git/config` i hookami także lockfile,
  konfiguracja repo i edytora, ścieżka interpretera, pliki czytane przez CI lub narzędzie poza piaskownicą; lista
  „plików wykonywanych później przez kogoś innego” w ochronie ścieżek i w przeglądzie diffu.
- [x] **Zapis z przebiegu, którego agent nie przepisze** (zrobione 2026-10-30: `core-async-delegation` §6, `core-agent-security` §6)**:** log wywołań narzędzi i ruchu sieciowego zbierany poza procesem
  agenta (transkrypt agenta nie jest niezależnym dowodem); wyłącznik działający bez współpracy agenta; inwentarz
  przebiegów z właścicielem (kto uruchomił, co ma, jak zatrzymać) — w `core-async-delegation` §6 „Monitorowanie”.
- [x] **Zadanie niewykonalne → STOP i zgłoszenie, nie obejście** (zrobione 2026-10-30: `core-agent-security/references/permissions-and-production.md` §4b, `core-async-delegation` §4)**:** w poleceniu i w polityce wykonania jawna droga „nie da
  się w zakresie” jako poprawny wynik; agent, który mówi „to poza zakresem”, nie jest kontrolą — granica musi być
  w konfiguracji.
- [x] **Próba granicy z dowodem, która warstwa zatrzymała** (zrobione 2026-10-30: `core-agent-security/references/permissions-and-production.md` §4b; odnośnik w `ai-mcp-server` 2026-11-01: `references/spec-2026-07-28-and-apps.md` §5) (artykuł „How much access should an AI agent have?”,
  E. Bermudez, 2026-10-14): katalog roboczy to miejsce startu, nie granica; filtr ścieżek w narzędziu plikowym
  (rozwiązana ścieżka, `..`, dowiązania symboliczne — wzór: walidacja w serwerze MCP filesystem) działa tylko dla
  tego narzędzia, a Python lub Bash czyta obok niego. Do `core-agent-security` i `ai-mcp-server`: przed
  przyznaniem dostępu jedna operacja potrzebna i jedna wykluczona (plik-kanarek poza workspace), z poleceniem
  i wynikiem; w zapisie rozróżnić „agent odmówił”, „narzędzie odrzuciło” i „środowisko nie pozwoliło” — tylko
  trzecie jest granicą dla kodu generowanego. Ruch sieciowy sprawdzać osobną próbą do zabronionego hosta, nie
  z samego logu.

## Testy aplikacji z AI poza odpowiedzią modelu (artykuł „9 AI Application Failures That Aren't Model Problems”, S. Gundeti, 2026-10, zapisane 2026-10-29)
Przegląd 2026-10-29: `ai-evals` ocenia odpowiedzi modelu, `fe-architecture` ma 4 stany widoku (ładowanie, błąd,
pusto, dane), `be-auth-security` i `ai-rag` — uprawnienia i izolację najemców. Brakuje jednej listy kontrolnej awarii,
które nie są winą modelu. Średni priorytet; jako `references/` w `qa-test-design` (odnośnik z `ai-evals` i
`eng-llm-features`), najpierw scenariusze ewaluacji:
- [x] **Lista „aplikacja z AI poza modelem”** (zrobione 2026-10-30: `qa-test-design/references/ai-application-beyond-the-model.md`, odnośnik w `ai-evals`) z testem do każdej klasy: (1) UI pokazuje sukces mimo błędu API —
  wymuszenie 403/500/timeout/wygasłego tokenu i porównanie ekranu z odpowiedzią, akcja naprawcza pasuje do przyczyny;
  (2) długie zadanie agenta a zerwane połączenie — rozłączenie, zakończenie w tle, powrót: prawdziwy stan końcowy bez
  wiecznego „pracuję…”; (3) routing modeli — sesja przypięta do taniej trasy po pierwszej trywialnej wiadomości,
  wyłączony model nadal serwowany, fallback zgodny z polityką i widoczny; (4) kontrakt narzędzi — pusty,
  zniekształcony, zdublowany i za duży wynik narzędzia, przerwane oczekujące wywołanie (pytanie do użytkownika,
  a on pisze nową wiadomość), pętla bez postępu (podniesienie limitu rekursji to objaw, nie naprawa), wartości
  przepisywane przez model (URL, ID, tokeny) jako niezaufane; (5) text-to-SQL — nieistniejące kolumny, identyfikatory
  ze spacjami, trzy różne wyniki: puste trafienie / błąd zapytania / metryka niezdefiniowana (zero, które „wygląda
  jak fakt”); (6) integracje — konta osobiste i firmowe, odwołany token, lista dłuższa niż jedna strona, link do
  pliku otwarty spoza aplikacji, czyją tożsamością działa agent; (7) migracje — testy na kontach z danymi sprzed
  zmiany, nie tylko na świeżych; (8) izolacja — API wprost jako użytkownik o niskich uprawnieniach, pamięć i cache
  nie przekraczają granic użytkownika i najemcy, odebranie roli działa od razu; (9) koszty — uzgodnienie zużycia
  z surowymi rekordami dostawcy per wywołanie, tury dłuższe niż okno synchronizacji i sesje przez północ, zmiana
  cennika nie przepisuje historii. Przykłady z artykułu są uogólnione przez autora — traktować jako klasy awarii.

## Model architektury jako jedno źródło widoków (artykuł „How to automate your architecture diagrams”, IcePanel, 2026-07-13, zapisane 2026-10-29)
Przegląd 2026-10-29: `arch-architect-practice` ma C4, ADR i „diagram jako kod w repo, aktualizowany z kodem”,
`docs-tech-writing` — Mermaid i PlantUML C4. Brakuje rozróżnienia „model vs diagram” i kontroli dryfu. Artykuł jest
materiałem producenta (IcePanel: MCP i API do modelu, import JSON/YAML); dokumentacji docs.icepanel.io nie
otworzyłem — host poza siecią sesji [niezweryfikowane]. Niski priorytet, bez rekomendacji jednego produktu:
- [x] **`arch-architect-practice`: model jako źródło, diagramy jako widoki** (zrobione 2026-10-30: sekcja „Dokumentacja architektury”) — elementy i relacje C4 opisane raz
  w modelu tekstowym w repo (np. Structurizr DSL, LikeC4 albo eksport z narzędzia), widoki dla różnych odbiorców
  generowane z niego zamiast osobno rysowanych diagramów; zmiana w PR modyfikuje model, CI renderuje widoki.
  Kontrola dryfu w CI: relacje z modelu porównane z faktycznymi zależnościami (graf importów z
  `eng-codebase-mapping`, wywołania między usługami, IaC) — relacja w kodzie bez odpowiednika w modelu i odwrotnie
  to ustalenie do przeglądu. ADR wskazuje elementy modelu, których dotyczy (ten sam pomysł co `applies_to` w pdi).
  Agent czyta model (plik albo serwer MCP narzędzia), a nie obrazki diagramów. Wersje i formaty narzędzi sprawdzić
  z datą przed dopisaniem.

## Protokoły agentów i tracing w standardzie (artykuły „Agentic Communication Protocols”, 0s & 1s, 2026-05-28; „Observability for the Agentic Harness”, D. Biswas, 2026-08-04; „Harness Engineering … Live Examples”, V. Mysore, 2026-10, zapisane 2026-10-29)
Przegląd 2026-10-29: `ai-agents` ma MCP, tracing z identyfikatorem przebiegu i wznawianie, `ops-observability` —
OpenTelemetry; reszta harness engineering jest pokryta (`core-async-delegation`, hooki, recenzent). Fabryka nie
wspomina A2A ani ACP i nie wskazuje konwencji OTel dla wywołań modeli. Średni priorytet, w `ai-agents`:
- [x] **Mapa protokołów** (zrobione 2026-11-01: `ai-agents/references/protocols-and-tracing.md` §1–2; A2A 1.0.1, ACP v1 sprawdzone w repozytoriach)**:** MCP — agent ↔ narzędzia i dane; A2A — agent ↔ agent (Agent Card z umiejętnościami,
  punktem końcowym i uwierzytelnianiem; zadania z cyklem życia); ACP (Agent Client Protocol, Zed) — edytor ↔ agent
  kodujący przez JSON-RPC po stdio, z zatwierdzaniem zapisów w edytorze. Kiedy który, że się uzupełniają, oraz
  bezpieczeństwo: Agent Card i wyniki innego agenta to niezaufane wejście (patrz pozycja o protocol pivoting
  w sekcji wzorców bezpieczeństwa). Stan specyfikacji, wersje i opiekunów sprawdzić z datą [niezweryfikowane].
- [x] **Tracing wg OpenTelemetry GenAI semantic conventions** (zrobione 2026-11-01: tamże §3; status Development, repo `semantic-conventions-genai`)**:** jeden ślad na zadanie, wywołanie modelu i narzędzia
  jako span-y potomne, ponowienia jako nowe span-y w tym samym śladzie, `links` dla rozgałęzień; atrybuty modelu,
  tokenów, kosztu i wyniku guardrails; `trace_id` jako identyfikator korelacji między systemami. Z tych śladów
  ewaluacja offline (`ai-evals`) i koszt (`core-cost-control`, `ops-finops`). Stan konwencji (eksperymentalne?)
  sprawdzić w repo open-telemetry/semantic-conventions z datą.
- [x] **Końcowa kontrola „liczby z narzędzia”** (zrobione 2026-11-01: `ai-agents/references/executors-and-gates.md` §5) (z demo Mysore'a): przed oddaniem odpowiedzi kod porównuje liczby
  i identyfikatory w odpowiedzi z wynikami narzędzi (np. wynik oceny ryzyka, limit polisy) i odsyła modelowi
  konkretną rozbieżność; do tego pominięcie powtórzonych identycznych wywołań narzędzia i przypomnienie
  o nieużytych wymaganych narzędziach przed odpowiedzią. Uwaga z demo: reguła guardrails też ma fałszywe
  alarmy (dopasowanie podciągu „ind”) — testuj reguły na prawdziwym słownictwie modelu.
- [x] **Syntetyczna sonda end-to-end agenta** (zrobione 2026-11-01: `ops-observability` „Healthchecki”, odnośnik `ai-agents` §6) (artykuł „Running a Fleet of 33 AI Agents”, J. Hamidun): kontener „Up”
  i healthcheck „OK” nie dowodzą działania — wygasły token wpychał obsługę wiadomości w pustą gałąź przez 90 min.
  Co godzinę prawdziwe zapytanie przez cały potok z asercją niepustej, zgodnej ze schematem odpowiedzi w czasie SLA
  (`ops-observability`, odnośnik z `ai-agents`).

## Szum z wyjścia narzędzi i zatwierdzenie związane z dowodem (artykuły „Reduce Token Waste”, E. Gomziakov, 2026-06-25; „How to Verify AI-Generated Code … Accension”, Sourik, 2026-10, zapisane 2026-10-29)
- [x] **`core-cost-control`: szum z terminala** (zrobione 2026-10-30: §6; RTK i podobne bez rekomendacji) — wyjście testów, buildów, `git diff` i logów to główne źródło
  zbędnych tokenów; najpierw tanie środki bez nowych zależności: reportery „tylko błędy” (`--reporter=dot`,
  `pytest -q`, `--silent`), `head`/`tail`, zapis pełnego logu do pliku i czytanie fragmentu. Narzędzia pośrednie
  (RTK — sprawdzone 2026-10-29: hook PreToolUse przepisujący polecenia Bash, CLI Apache-2.0, silnik i proxy BUSL-1.1,
  filtruje z utratą treści, `rtk bypass`; Headroom, CodeGraph) tylko jako opcja po `skill_audit` i zgodzie człowieka,
  bo to obcy hook z dostępem do każdego polecenia; mierzyć koszt na udane zadanie, nie liczbę tokenów (cache,
  rozumowanie i ponowienia psują proporcję).
- [ ] **Zatwierdzenie bramki związane z dowodem (mode-pdi ↔ pdi):** `gate.requested` niesie dziś ścieżkę artefaktu
  i link do PR; dodać skrót treści artefaktu i SHA commita. Zatwierdzenie w pdi zapisuje ten skrót, a
  `phase_run.py` przed kolejną fazą sprawdza, czy artefakt się nie zmienił — inaczej „EVIDENCE_CHANGED” i ponowna
  prośba o bramkę (wzorzec z Accension: zgoda dotyczy dowodu, który człowiek widział). Zmiana kontraktu zdarzeń —
  osobna pozycja w `pdi/TODO.md`; TDD po obu stronach.

## Wzorce architektury frontendu — braki (artykuł „Every Frontend Architecture Pattern Explained”, T. Kanjariya, 2026-08-06, zapisane 2026-10-29)
Przegląd 2026-10-29: `fe-architecture` ma style (monolit modularny, micro-frontends z Module Federation 2.0, FSD),
modele renderowania per trasa (CSR/SSR/SSG/ISR/RSC, hydratacja) i BFF tylko jako miejsce sesji. Niski priorytet:
- [x] **BFF jako wzorzec** (zrobione 2026-10-30: `fe-architecture/references/architecture-styles.md`)**:** osobny cienki backend na klienta (web, mobile), własność zespołu frontendu, kształt danych
  pod jeden interfejs; kiedy nie (jeden klient = zbędny przeskok sieciowy); koszt: kolejny serwis i pojedynczy punkt
  awarii (źródła: Calçado 2015, Newman — sprawdzić).
- [x] **Obliczenia przy danych, nie przy użytkowniku** (zrobione 2026-10-30: `fe-architecture/references/rendering-models.md`; status produktów brzegowych bez wpisu)**:** SSR na brzegu bez bazy rozproszonej bywa wolniejszy niż render
  w regionie bazy; brzeg serwuje statyczną skorupę, dynamiczne części strumieniowane z regionu danych (Partial
  Prerendering). Status Vercel Edge Functions („deprecated” wg artykułu) sprawdzić w dokumentacji z datą
  [niezweryfikowane].
- [x] **Micro-frontends — typowa porażka i próg** (zrobione 2026-10-30: `architecture-styles.md`)**:** dryf współdzielonych zależności (dwie wersje frameworka na jednej
  stronie) → `singleton` i `strictVersion`/`requiredVersion` w federacji, kontrola wersji w CI; decyzja wg bólu
  wdrożeń między zespołami, nie złożoności aplikacji (heurystyka autora: < ~15 osób monolit modularny; 50+ i zespoły
  blokujące się przy wdrożeniach → micro-frontends) — jako heurystyka, nie reguła.

## Dyscyplina pomiaru w ewaluacjach (artykuł „Structuring 40 Million Documents into an Agentic Knowledge Graph”, F. Khan, 2026-08-26, zapisane 2026-10-29)
Przegląd 2026-10-29: `ai-evals` ma zbiory, graderów, kalibrację sędziego, pass@k i bramkę w CI. Artykuł to studium
porażek pomiaru (wszystkie liczby z jego repo, nie sprawdzone): sześć cichych błędów, z czego cztery poprawiły metrykę.
Średni priorytet, w `ai-evals` (reference „pułapki pomiaru”):
- [x] **Granice wyniku** (zrobione 2026-10-30: `ai-evals/references/measurement-pitfalls.md` §1)**:** ramię „ślepe” (bez kontekstu), „wyrocznia” (tylko złoty fragment) i stała klasa większościowa;
  wynik systemu interpretowalny tylko między nimi (u autora oba ramiona przegrywały ze stałą „tak”, co znaczyło, że
  zbiór i model nie rozróżniają architektur).
- [x] **Jedna zmienna naraz i przegląd stałych** (zrobione 2026-10-30: `ai-evals/references/measurement-pitfalls.md` §2)**:** każda stała w przetwarzaniu (obcięcie dokumentu, limit kandydatów,
  próg) to hiperparametr — przebieg z pozostałymi wartościami zamrożonymi; obcięcie do 1100 znaków kosztowało
  14 punktów, limit 120 kandydatów wyrzucał złoty dokument w 41% pytań. Ramiona porównawcze dostają te same stałe
  (wyrocznia czytała 4000 znaków, system 1100 — „luka rozproszenia” była w 84% artefaktem).
- [x] **Wybór konfiguracji na osobnym zbiorze** (zrobione 2026-10-30: `ai-evals/references/measurement-pitfalls.md` §3)**:** podział dobór/test, wynik raportowany tylko z testu; kontrola
  „przetasowane etykiety” pokazuje, ile daje sam wybór najlepszej z wielu konfiguracji (u autora 3,5 pkt na szumie).
  Siatka parametru, której optimum leży na krawędzi, jest za wąska.
- [x] **Etykieta z rozkładu, nie z regexa** (zrobione 2026-10-30: `ai-evals/references/measurement-pitfalls.md` §4)**:** decyzja klasyfikacyjna z prawdopodobieństw tokenów etykiet (suma
  wariantów pisowni), nie z parsowania wolnego tekstu; ta sama wartość daje pewność do abstynencji.
- [x] **Metryka składowa musi modelować to, co dzieje się dalej** (zrobione 2026-10-30: `ai-evals/references/measurement-pitfalls.md` §4)**:** gorsza precyzja groundera może dać lepszy system,
  gdy dalszy filtr odrzuca fałszywe trafienia — oceniać parę „pokrycie i przeciek na pytaniach kontrolnych”
  (pytanie z jednym pojęciem podmienionym na losowe), nie samą metrykę składnika.
- [x] **Niezmienniki dla struktur pochodnych** (zrobione 2026-10-30: `ai-evals/references/measurement-pitfalls.md` §5)**:** assert zgodności tablic równoległych plus niezależne przeliczenie
  ze źródła (u autora rozjechane tablice etykiet nie rzuciły błędu); cache kluczowany całym wejściem; walidator
  cytatów testowany na nawiasie z wieloma identyfikatorami.
- [x] **Cykl życia sędziego LLM** (zrobione 2026-10-30: `ai-evals/references/datasets-and-graders.md` §7) (Netflix Tech Blog, 2026-09-04; praca arXiv 2608.18300 — sprawdzić): skill ma już
  uzasadnienie przed oceną i okresową próbkę na dryf; brakuje: (1) zgodności uzasadnień, nie tylko etykiet —
  „dobra etykieta, zły powód” wykrywana porównaniem uzasadnienia sędziego z uzasadnieniem człowieka (meta-sędzia
  sprawdzony najpierw na ludziach), bo strojenie rubryki tylko na etykietach u autorów zdegradowało jedno kryterium;
  (2) każda etykieta „źle” w złotym zbiorze z pisemnym uzasadnieniem człowieka; (3) jeden sędzia na kryterium;
  (4) sędzia jako bramka i krytyk: uzasadnienie odrzucenia wraca do generatora, limit poprawek (u nich 3), po nim
  „nie pokazuj” zamiast „pokaż słabe”; (5) próg dryfu względem rozrzutu ludzi (sędzia nie gorszy niż średnia
  oceniających minus 2 odchylenia standardowe), stała warstwowana próbka tygodniowa; (6) zmiana rubryki tylko po
  zatwierdzeniu człowieka, poprzednia wersja do natychmiastowego wycofania; (7) przegląd ludzi wyłapuje też braki
  samej rubryki, nie tylko dryf sędziego.
Wniosek merytoryczny autora, do `ai-rag`: graf/ontologia do wyszukiwania i proweniencji, ale decyzja o odmowie
z kalibrowanej pewności modelu (AUROC 0,81), bo certyfikacja ścieżką w grafie przewidywała poprawność na poziomie
losowym (0,50) — jeden przypadek, nie reguła; sprawdzać na własnym zbiorze.

## Wzorzec „Counting House”: AI w obsłudze dużego wolumenu spraw (artykuł S. Yegge'a, 2026-10, zapisane 2026-10-29)
Przegląd 2026-10-29: pojedyncze elementy już są — `ai-evals` (złoty zbiór, zgodność ludzi jako sufit, kappa,
kalibracja sędziego, shadow), `ai-product-management` (koszt błędów w PRD), saga w `ddd-tactical-design`,
idempotencja w `be-messaging-outbox`. Brakuje złożenia ich w jeden wzorzec architektury. Średni priorytet, jako
reference w `arch-ai-solutions` (przykład domenowy w pack-ev: obsługa kierowców CPO/eMSP — zwroty, sesja nie startuje):
- [x] **Tabela polityki per intencja i progi autonomii** (zrobione 2026-10-31: `arch-ai-solutions/references/case-handling.md` §1)**:** off → shadow (model odpowiada równolegle, oceniany) →
  assist (podpowiedź dla człowieka) → contain (odpowiada klientowi) → transact (zmienia stan przez orkiestrator);
  awans intencji na wyższy próg dopiero po ewaluacji na złotym zbiorze z ocen ludzi i podpisach właścicieli
  (operacje, finanse, prawo). Ta sama logika co pozycja „Rutyny, które zdobywają uprawnienia”.
- [x] **Macierz pomyłek z kosztem zamiast trafności** (zrobione 2026-10-31: `arch-ai-solutions/references/case-handling.md` §2)**:** dla intencji łatwych do pomylenia koszt każdej komórki poza
  przekątną (pomyłka kierunku do kolejki ≠ pominięta pomoc dla pasażera); dla wypłat liczy się precyzja, dla spraw
  krzywdzących klienta czułość; porównanie z tą samą macierzą dla ludzi (koszt błędów + koszt pracy).
- [x] **Model proponuje, orkiestrator wykonuje** (zrobione 2026-10-31: `arch-ai-solutions/references/case-handling.md` §3)**:** model wydaje „intencję zapisu” (schemat), orkiestrator sprawdza
  uprawnienie na żywym systemie źródłowym (nie na cache, który czytał model), nadaje klucz idempotencji z pól
  żądania, zatwierdza automatycznie do progu z polityki, powyżej — człowiek; saga z akcjami kompensującymi i odczytem
  po zapisie; odmowa z kodem przyczyny trafia do właściwej kolejki ludzi. Model nie ma poświadczeń i nie widzi PII
  (bramka tokenizująca PII odwracalnie).
- [x] (zrobione 2026-10-30: `ai-evals/references/datasets-and-graders.md` §7 pkt 8) **Sędzia LLM dopuszczony tylko tam, gdzie zgadza się z ludźmi tak często jak ludzie między sobą**, nigdy nie
  strojony na złotym zbiorze; złoty zbiór i ewaluacje własnością firmy (to dźwignia zmiany modelu na tańszy).
Wzorzec opisany przez autora bez danych z wdrożeń (rozmowy z firmami) — traktować jako projekt do sprawdzenia, nie
wynik. Wątek „dobrostanu modelu” z artykułu pomijam; z niego tylko praktyczne: prawdomówny prompt bez gróźb
i fałszywej pilności, prawo do odmowy z kodem przyczyny i propozycją poprawki procedury.

## Znakowanie tekstu z AI i oszczędzanie tokenów w aplikacjach (artykuły „AI Text Has a Secret Signature”, Analyst Uttam, 2026-08-17; „Agentic AI: How to Save on Tokens”, I. Silfverskiöld, 2026-05-05, zapisane 2026-10-29)
Przegląd 2026-10-29: `ai-governance-compliance` ma obowiązek art. 50 AI Act (oznaczanie wyników syntetycznych
w formacie maszynowym) bez części technicznej; `arch-ai-solutions` ma prompt caching (stały prefiks), cache wyników
tylko dla odpowiedzi niezależnych od użytkownika, routing i fallback. Niski/średni priorytet:
- [x] **`ai-governance-compliance`, reference „znakowanie techniczne”** (zrobione 2026-11-01: `references/technical-tagging.md`; kodeks praktyk 2026-06-10 wg omówień, eur-lex i strona Komisji niedostępne z sieci sesji)**:** znak wodny w tekście (Kirchenbauer i in.,
  ICML 2023: zielona lista tokenów z ziarna poprzedniego tokenu, test z, wykrywalny od ~25 tokenów, nie działa dla
  tekstu o niskiej entropii i zapamiętanego), C2PA/metadane dla obrazów i wideo; ograniczenia: parafraza, wstawianie
  i usuwanie znaków, homoglify i znaki zerowej szerokości (detektor kanonizuje Unicode), kradzież i podrabianie znaku,
  „piggyback” — zmodyfikowana treść wciąż wykrywana jako z modelu. Wniosek do dokumentacji zgodności: znak wspiera
  wykrywanie masowe, nie przypisanie pojedynczego tekstu ani dowód; co konkretnie spełnia art. 50 ust. 2 (normy,
  kodeks praktyk) sprawdzić z datą [niezweryfikowane].
- [x] **`arch-ai-solutions`/`eng-llm-features`: koszt agenta z wieloma narzędziami** (zrobione 2026-11-01: `eng-llm-features` §4; nazwa mechanizmu u dostawcy i LLMRouterBench — do sprawdzenia) — leniwe ładowanie definicji
  narzędzi (wyszukiwarka narzędzi, `defer_loading` w API Anthropic — sprawdzić aktualną nazwę i warunki w
  dokumentacji, skill `claude-api`) zamiast setek definicji w każdym wywołaniu; kaskada „tani model najpierw,
  eskalacja przy niskiej pewności” jako alternatywa routera zgadującego trudność z promptu (wg LLMRouterBench,
  arXiv 2601.07206, wyuczone routery ledwie biją proste reguły i kNN — sprawdzić); deterministyczne wyniki narzędzi
  (SQL, wyszukiwanie) w zwykłym cache z TTL; stała część promptu przed zmienną, bez znaczników czasu w prefiksie.
  Mierzyć koszt na udane zadanie (tak jak pozycja o szumie z terminala).

## Zgodność skilli ze specyfikacją Agent Skills i „odśmiecanie architektury” (strona agentskills.io / repo agentskills/agentskills; artykuły „AI Agents (06): Agent Skills”, 0s & 1s, 2026-09-21; „AI-Generated Technical Debt: Architecture Garbage Collection”, L. Niessen, 2026-09-12; zapisane 2026-10-29)
Sprawdzone 2026-10-29 w `agentskills/agentskills`, `docs/specification.mdx` (agentskills.io poza siecią sesji):
wymagane `name` (1–64 znaki, małe litery, cyfry i myślniki, bez myślnika na początku/końcu i podwójnego, równe nazwie
katalogu) i `description` (1–1024 znaki); opcjonalne `license`, `compatibility` (1–500), `metadata` (mapa
string → string), `allowed-tools` (eksperymentalne); treść `SKILL.md` < 5000 tokenów i < 500 linii; odwołania
o jeden poziom od `SKILL.md`; walidacja `skills-ref validate ./skill`. Stan fabryki (skrypt jednorazowy, 209
skilli): nazwy i opisy zgodne, żaden `SKILL.md` nie przekracza 500 linii; wyjątki:
- [x] **`metadata.review` jest datą YAML, nie tekstem** (zrobione 2026-10-30: 209 skilli w cudzysłowie, zapis przez `freshness.py` i `build.py new-skill`, ostrzeżenie w `build.py check`) (wszystkie 209 skilli, np. `review: 2026-10-10` bez
  cudzysłowu) — specyfikacja wymaga wartości tekstowych; zapis w cudzysłowie w szablonie i w `build.py`/generatorze
  plus test w `skill_gate.py`; przy okazji sprawdzić `skills-ref validate` na kilku skillach (zmiana w `factory/` za
  zgodą człowieka). Klucze spoza specyfikacji (`argument-hint`, `disable-model-invocation`) to rozszerzenia Claude
  Code — zostają, sprawdzić, czy walidator je odrzuca.
- [x] **Odwołania zagnieżdżone** (sprawdzone 2026-11-01: wszystkie 64 pliki — `fe-architecture` 34, `eng-design-patterns` 22, `fe-web-platform` 8 — są wymienione z nazwy bezpośrednio w `SKILL.md` swojego skilla, więc „jeden poziom” jest spełniony; bez plików osieroconych; zmian nie trzeba)**:** 64 pliki w podkatalogach `references/*/` (np. `fe-architecture/references/components/`)
  — sprawdzić, czy prowadzi do nich bezpośredni link z `SKILL.md` (wtedy „jeden poziom” spełniony), czy łańcuch
  przez plik pośredni.
- [x] **`eng-tech-debt-audit`: odśmiecanie architektury jako rutyna** (zrobione 2026-11-01: sekcja „Odśmiecanie architektury jako rutyna”; ArchUnitPython i liczby prac — do sprawdzenia) — fabryka ma reguły granic
  (`ddd-legacy-modernization`: dependency-cruiser, import-linter, Tach, ArchUnit) i audyt długu; brakuje pętli:
  (1) testy architektury (warstwy, cykle, rozmiar pliku) w szybkich bramkach i w CI, uruchamiane przez agenta przed
  „gotowe”; (2) zapadka (ratchet) — próg startuje przy obecnym maksimum i tylko spada, wyjątki wąskie, z właścicielem
  i terminem; (3) rutyna co tydzień: jedno naruszenie → jeden mały PR refaktoryzacji, przegląd człowieka
  (`core-async-delegation` §5); (4) testy architektury, progi i listy wyjątków w ścieżkach chronionych (CODEOWNERS),
  bo agent optymalizujący „zielone CI” przesunie weryfikator zamiast kodu. ArchUnitPython jako opcja dla Pythona obok
  import-linter i Tach — sprawdzić projekt i wersję z datą. Liczby z prac „Debt Behind the AI Boom” (arXiv 2603.28592)
  i „More Code, Less Reuse” (MSR 2026) jako tło, do weryfikacji.

## Tożsamość encji: identyfikator pojęcia a identyfikator rzeczy (artykuł „The Spine of the Context Fabric: Concept IRIs and Instance IRIs”, S. Banerjee, 2026-10-13, zapisane 2026-10-29)
Przegląd 2026-10-29: niski priorytet; uzupełnia pozycję o wiedzy kanonicznej (OKF):
- [x] **Rozdział „co znaczy” i „która rzecz”** (zrobione 2026-11-01: `ddd-context-mapping`; pole `resource` w OKF — z pozycją o OKF)**:** pojęcia (klasy, właściwości, metryki) mają stały identyfikator
  w przestrzeni autorów słownika; rzeczy (dostawca, zamówienie) — identyfikator wybijany regułą z klucza biznesowego,
  jedna rzecz = jeden identyfikator mimo wielu rekordów w systemach (tablica mapowania kluczy); dane zostają u
  właścicieli, wspólna jest tylko tożsamość. W notatkach OKF pole `resource` niesie identyfikator pojęcia, a pliki
  generuje się ze słownika, nie pisze ręcznie. Dla `ddd-context-mapping`/`data-engineering`: reguła wybijania
  identyfikatorów w specyfikacji i wspólnej bibliotece, nie w jednym narzędziu.

## Od błędnego przykładu do chronionego testu akceptacyjnego (artykuł „Failing Example as the Start of a Spec”, J. Wąsowski, 2026-10-28, zapisane 2026-10-29)
Przegląd 2026-10-29: `qa-spec-first-testing` ma niezależną wyrocznię, clean-room, brzegi, testy właściwości
i oznaczanie testów charakteryzujących; `qa-test-design` — klasy i brzegi; `core-agent-security` — testy akceptacyjne
poza zasięgiem agenta; `tdd_guard` ostrzega przy osłabieniu testu; `tool-pytest` utrwala znalezione przypadki
w `@example`. Badań z artykułu (Tufano i in., arXiv 2608.17177; ImpossibleBench, arXiv 2510.20270) nie otworzyłem —
liczby [niezweryfikowane], przed wpisaniem do skilla sprawdzić u źródła. Braki:
- [x] **`qa-spec-first-testing`: zgłoszenie błędu zaczyna się od przykładu** (zrobione 2026-10-31: „Błąd zgłoszony — od przykładu do testu”) wejście / oczekiwane / faktyczne; z niego
  punkty ON, OFF i wewnątrz progu (99,99 · 100,00 · 100,01) i jeden kontrprzykład na regułę (kod promocyjny, zwrot),
  regułę słowami zapisuje się na końcu. Kontrprzykład bez jasnego „Then” to pytanie do biznesu, nie test. Jeden
  przykład przepuszcza implementację, która „zna odpowiedź” (`if total == 100`).
- [x] **Kontrakt przed testami** (zrobione 2026-10-31: `qa-spec-first-testing` pkt 5, jako opcja)**:** agent zapisuje warunki wejścia, wyjścia i przypadki nieokreślone, człowiek czyta go
  przed testami, testy powstają z kontraktu, nie z przeczytanego kodu (kod błędny dziś daje testy utrwalające błąd).
  Wg autora badanie Google: zysk istotny dopiero przy kilku niezależnych przebiegach, ok. +38% tokenów — więc jako
  opcja dla progów i reguł liczbowych, nie domyślny krok.
- [x] **Test właściwości nie zastępuje przykładu** (zrobione 2026-10-31: `qa-spec-first-testing` pkt 4)**:** losowanie w pełnym zakresie prawie nigdy nie trafia w próg
  (autor: 0/30 przebiegów bez `@example(100.00)`, 30/30 z nim); przykład z ticketu zostaje jako jawny przypadek
  w teście właściwości — ogólna zasada w `qa-spec-first-testing`, nie tylko w `tool-pytest`.
- [x] **Chronione scenariusze akceptacyjne egzekwuje CI, nie prompt** (zrobione 2026-10-31: `core-git-workflow`, „Pull request”)**:** do `core-agent-security` / `core-git-workflow`:
  CODEOWNERS tylko wskazuje recenzentów — wymuszenie daje ochrona gałęzi „Require review from Code Owners” i wymagany
  check; zmiana scenariuszy w osobnym PR niż kod (check w CI odrzuca PR, który zmienia oba); liczba chronionych testów
  nie spada — alarm pomocniczy, bo asercję da się osłabić bez zmiany liczby; zmiany w krokach (step definitions) też
  przez przegląd, bo scenariusz można „zazielenić” w adapterze.

## Ewaluacja na zapisanych śladach, rachunek za migrację runtime'u agenta i pętle (artykuły „Eval-Driven Development”, A. Punnen, 2026-08-18; „Managed Agent Runtime Lock-In”, J. Wąsowski, 2026-10-07; „Practical Loop Engineering”, A. Osmani, 2026-08-22; zapisane 2026-10-29)
Przegląd 2026-10-29: `ai-evals` ma reguły deterministyczne przed sędzią, osobną ocenę trajektorii (limity, zakazane
narzędzia), próbki z ruchu i pełny zestaw przy zmianie promptu lub harnessu; `arch-ai-solutions` — lock-in w wagach
i test wymiany w obu kierunkach; `core-async-delegation` — kontrakt, ≤2 próby na bramkę, oceniający `/goal` widzi tylko
transkrypt. Braki:
- [x] **`ai-evals`, „regresja ze śladów”** (zrobione 2026-10-30: `ai-evals/references/measurement-pitfalls.md` §7)**:** ślad z produkcji niesie wersję kontraktu (prompt + polityka ewaluacji:
  słowa wymagane, min. i maks. wywołań narzędzi i modelu, rubryka sędziego); nowe reguły deterministyczne puszcza się
  na zapisanych śladach bez ponownego uruchamiania agenta (tanio, powtarzalnie), a sędziego tylko na losowej próbce
  albo na śladach z negatywną opinią użytkownika. Dolny limit wywołań narzędzia („musiał wyszukać”) łapie odpowiedź
  „sprawdź w serwisach X” bez wyszukania.
- [x] **`arch-ai-solutions`, zarządzany runtime agenta** (zrobione 2026-11-01: `arch-ai-solutions/references/gate-and-reliability.md` §4) (Claude Managed Agents, OpenAI Agents API, Bedrock
  AgentCore — ceny i daty z artykułu [niezweryfikowane]): pętla jest „za darmo”, lock-in schodzi niżej — dialekt
  schematu narzędzi (zmiana nazw przez bramkę), format piaskownicy i płaszczyzna sterowania (obraz kontenera
  przenośny, identyfikatory środowiska i sesji nie), okablowanie MCP (auth, mapowanie nazw), semantyka stanu i sesji
  (wygaszenie po bezczynności kasuje pamięć procesu). Koszt migracji = rachunek za ewaluacje: regresja kontraktu
  narzędzi, trajektorii, stanu, polityki, środowiska oraz ponowne policzenie jakości i kosztu. Do ADR: stan biznesowy
  w systemie, który kontrolujesz, i przenośna definicja sukcesu (własny zestaw ewaluacji) zanim zaufasz śladom
  konkretnego runtime'u.
- [x] **`core-async-delegation`, warunek postępu w `/goal`** (zrobione 2026-10-30: §4 i §5)**:** obok limitu tur — „każda tura poprawia co najmniej jedną
  zmierzoną metrykę, dwie tury bez poprawy = STOP” i „to samo polecenie po raz trzeci bez zmiany wyniku = STOP”;
  przykład z liczbą z narzędzia (Lighthouse, liczba testów), nie „aż będzie dobrze”. Do tabeli trybów: `/loop` żyje
  w sesji i wygasa po 7 dniach (sprawdzone 2026-10-29: code.claude.com/docs/en/scheduled-tasks, sekcja
  „Seven-day expiry”), praca przeżywająca sesję → rutyna w chmurze.

Artykuł „The One-Sentence Answer That Ends a Line of Hostile Questioning” (M. B. Hazeldine, 2026-09-12) — bez wpisu:
„werdykt, jeden warunek, stop” fabryka już stosuje w raportach (linia werdyktu bramki, werdykt na początku raportu
ewaluacji); dotyczy wystąpień ustnych, a materiał kończy się reklamą płatnego kursu.

## Regresja przy powtarzających się kolumnach (artykuł „What “Singular Matrix” Really Means”, K. Nahar, 2026-10-20, zapisane 2026-10-29)
Przegląd 2026-10-29: `data-analysis` wspomina tylko „brak silnej współliniowości” w założeniach regresji. Brak:
- [x] **`data-analysis`, macierz niepełnego rzędu** (zrobione 2026-10-30: `references/statistics.md`, zachowanie bibliotek opisane ogólnie)**:** pułapka zmiennych zero-jedynkowych (wszystkie kategorie + wyraz
  wolny) i kolumna stała w danych to ten sam problem — dane nie rozróżniają współczynników. Biblioteki reagują różnie:
  numpy przerywa („Singular matrix”), statsmodels ostrzega i wybiera rozwiązanie o najmniejszej normie, scikit-learn
  według autora po cichu zwraca inne [niezweryfikowane — sprawdzić na wersjach z projektu]; przed interpretacją
  współczynników sprawdzić rząd macierzy i wskaźnik uwarunkowania (albo VIF), a naprawą jest zmiana danych lub
  usunięcie kolumny, nie zmiana biblioteki. W kodzie `solve`/`lstsq` zamiast `inv(A) @ b` (szybciej i dokładniej
  przy złym uwarunkowaniu).

## Nadmiar kodu: co działa poza tekstem reguł i diagnoza rachunku za agenta (artykuły „Fixing Over-Engineering in LLM Coding Agents”, F. Khan, 2026-10-12; „Your Claude Code Bill Demystified”, J. Wąsowski, 2026-10-09; zapisane 2026-10-29)
Przegląd 2026-10-29: `eng-design-principles` ma już drabinę minimalizmu (te same 7 szczebli), listę „nigdy nie
upraszczasz kosztem”, znacznik `debt:` i „pominąłem X, dodać gdy Y”; `core-cost-control` — cache i jego czas życia,
koszt rozwiązanego zadania, kaskadę modeli. Liczby z artykułów (jeden model, 34 zadania; benchmark Spotify liczony
znaki/4) [niezweryfikowane]. Braki:
- [x] **`eng-design-principles` / `qa-change-review`: same reguły w tekście prawie nie działają** (zrobione 2026-11-01: `eng-design-principles`, „Drabina minimalizmu”; hook przy osłabieniu zabezpieczeń — tylko na prośbę) — wg pomiaru autora
  wklejone reguły dały 0,98 kodu bazowego, a „krótko”/hasło 1,00 (terse zgubił też werdykt bezpieczeństwa); efekt dały
  dopiero: drabina, jednorazowe zatrzymanie pierwszego „gotowe”, gdy dodano kod bez żadnego sprawdzenia, i krytyk
  nadmiaru po zakończeniu z **blokadą edycji, która zmniejsza liczbę zabezpieczeń w pliku** (wzorce: zapytanie
  z parametrami, `compare_digest`, escapowanie, odrzucenie wejścia, sprawdzenie wygaśnięcia, alt). Do skilla: przegląd
  nadmiaru tnie strukturę, a cięcie zabezpieczenia wymaga osobnego uzasadnienia; do rozważenia jako hook fabryki
  (ostrzeżenie jak `tdd_guard` przy osłabieniu testu) — tylko na prośbę użytkownika (`.claude/hooks/`). Zasada
  wdrażania reguł z artykułu: element zostaje, jeśli ablacja pokazuje korzyść; remis = nie wchodzi.
- [x] **`core-cost-control`, diagnoza przed dźwignią** (zrobione 2026-10-30: §7)**:** problem kontekstu (te same pliki czytane w całości kilka razy,
  stosunek tokenów wejścia do wyjścia ~100:1 i więcej, częste kompaktowanie, niskie trafienia cache mimo stałego
  promptu, agent co sesję odkrywa, kto jest właścicielem czego) → inżynieria kontekstu; problem modelu (wysoki odsetek
  porażek klasy zadań mimo dobrego kontekstu, wiele tur do pierwszej poprawnej edycji) → zmiana modelu; problem pomiaru
  (subskrypcja vs API, benchmark vs produkcja, tokeny szacowane ze znaków) → najpierw liczniki dostawcy. Cache obniża
  cenę powtarzanego prefiksu, nie zdejmuje treści z okna (gnicie kontekstu zostaje).
- [x] (2026-11-22: hak `read_gate` — domyślnie ostrzeżenie dla agenta, `read_gate.mode: deny|off`, `max_lines: 350`;
  odczyt z zakresem, `head`/`tail` i `cat` w potoku przechodzą; streszczenie przez `scout` tylko jako podpowiedź, hak nie woła modelu) **Bramka na odczyt dużych plików** (Spotify: hook PreToolUse blokuje `Read` pliku > 350 linii i `cat`/`head`/`tail`
  na nim, kieruje do taniego modelu, który zwraca streszczenie; odczyt z `offset`/`limit` przechodzi; instrukcja
  w CLAUDE.md nie wystarczyła). Fabryka ma delegację czytania do `scout`; ocenić hook razem z pozycją o RTK wyżej
  — ograniczenia z artykułu: edycji i rozumowania nie delegować (numery linii w streszczeniu się przesuwają, tani
  model przeoczył błąd współbieżności). Zmiana `.claude/hooks/` tylko na prośbę użytkownika.

Artykuł „My Workflow with Claude: Spec-Driven Development with AgentSpec” (L. Uriel, 2026-06-17) — bez wpisu: kolejne
narzędzie SDD obok Spec Kit i OpenSpec (fazy brainstorm → define → design → build → ship i iterate), pokrywa je
`core-delivery-lifecycle` z bramkami i sekcja o Spec Kit wyżej; „pewność liczona z dowodów” bez opisu metody.

## Narzędzia zamiast ekranu dla agentów obsługujących programy (artykuł „Building Fast Computer Agents to Solve Complex Tasks”, F. Khan, 2026-10-07, zapisane 2026-10-29)
Przegląd 2026-10-29: `ai-agents` ma zatwierdzanie akcji nieodwracalnych i treść jako dane, ale nic o agentach
sterujących programami (computer use). Liczby autora (jedno stanowisko, Windows) [niezweryfikowane]. Brak:
- [x] **`ai-agents`, „podnoszenie interfejsu”** (zrobione 2026-10-30: `ai-agents/references/failures-and-patterns.md`)**:** zanim agent dostanie zrzuty ekranu, kolejność interfejsów: własny
  format pliku programu → wiersz poleceń (tryb bez okna) → skrypty/COM → oficjalne API → drzewo dostępności (nazwy
  kontrolek jako tekst) → piksele na końcu. Każda funkcja jako narzędzie z kontraktem: schemat, implementacja,
  **weryfikator** (odczyt wyniku z powrotem, np. ponowne otwarcie zapisanego pliku innym czytnikiem) i **skutek**
  (`local` / `outward` — wyjście do innych ludzi czeka na „tak”); wynik jako krótki JSON z listą sprawdzeń, odmowa
  narzędzia z powodem i wykonalną alternatywą. Dalej: lista narzędzi zawężana do grup pasujących do prośby (zamiast
  wszystkich schematów w każdym wywołaniu), łańcuch zależnych wywołań zaplanowany w jednym wywołaniu modelu
  z odwołaniami do wyników wcześniejszych kroków, udany przebieg kompilowany do nowego narzędzia z parametrami —
  odtwarzany tylko, gdy okno zgadza się z wyuczonym, wyłączany po 2 porażkach. Klasyfikator ryzyka akcji UI w kodzie
  (tekst na ekranie może nieść wstrzyknięcie). Sprawdzenia dowodzą liczb, nie sensu (autor: dwie pomyłki planu nie
  złapane przez żadne sprawdzenie).

## Utrata, duplikaty i ponowne przetwarzanie zdarzeń (artykuł „How to Handle Event Loss, Duplicate Events, and Reprocessing”, A. Kumar, 2026-09-10, zapisane 2026-10-29)
Przegląd 2026-10-29: `be-messaging-outbox` ma id nadawane przy zapisie, deduplikację atomową w tej samej jednostce
pracy co efekt. Braki:
- [x] **`be-messaging-outbox`: trzy osobne problemy, trzy naprawy** (zrobione 2026-10-30: §5) — utrata to trwałość po stronie producenta
  i brokera (w Kafce `acks=all`, `min.insync.replicas` > 1, producent idempotentny — ten ostatni nie zastępuje
  deduplikacji u konsumenta); duplikaty — konsument idempotentny, rekord deduplikacji z czasem życia dobranym do okna
  ponownych dostarczeń (nie rośnie bez końca); **celowe odtworzenie historii** (reset offsetu, nowa grupa
  konsumentów, odbudowa modelu odczytu) wymaga deterministycznej obsługi (bez bieżącego czasu i stanu innych usług
  w przejściu) i oddzielenia skutków zewnętrznych (e-mail, obciążenie karty) od odbudowy stanu — flaga „odtwarzanie”
  albo osobna ścieżka skutków; klucz idempotencji przekazany też do dostawcy płatności. Bez naturalnego id: nadaje go
  producent przy utworzeniu albo skrót niezmiennych pól / encja + wersja.

## Zmiany harnessu i skilli mierzone na odłożonym zbiorze (artykuł „AI Harness Evolution: AHE, Harness-R1, and Overfitting Without a Holdout”, J. Wąsowski, 2026-10-22, zapisane 2026-10-29)
Przegląd 2026-10-29: w sekcji „Dyscyplina pomiaru” są już podział na dobór i ocenę i test przetasowanych etykiet dla
ewaluacji produktowych; `core-skill-authoring` każe pisać scenariusze przed treścią. Liczby z prac (AHE 69,7 → 77,0%
na tych samych 89 zadaniach; Harness-R1 +8,9 pkt na 1270 odłożonych; krytyka arXiv 2607.12227: przy rozłącznych
zbiorach ok. +0,6 pkt) [niezweryfikowane]. Braki:
- [x] **Fabryka sama tuninguje na egzaminie** (zrobione 2026-11-01: `run_skill_evals.py --per-skill`, sekcja „Luka strojenie − holdout” w raporcie, reguła przyjęcia zmiany w `core-skill-authoring` krok 4; pomiar `docs/evals/2026-11-01-luka-strojenie-holdout-podsumowanie.md` — luka +15 pp, głównie nieuruchamianie skilli na nowych sformułowaniach)**:** opisy i treść skilli poprawiamy po pomiarze na tych samych scenariuszach
  (pomiar 2026-10-22: przegląd 143 nierozróżniających, skrócenie 26 skilli). Do `core-skill-authoring` i runnera
  ewaluacji: część scenariuszy każdego skilla odłożona (nie czyta ich autor zmiany), zmiana przyjęta, gdy poprawia
  zbiór roboczy i nie pogarsza odłożonego; w raporcie różnica „roboczy vs odłożony” jako sygnał uczenia się egzaminu.
  Płatny pomiar tylko za zgodą człowieka.
- [x] **Bramka zmiany harnessu (prompt, skill, hook, narzędzie), ręcznej lub z pętli** (zrobione 2026-10-30: `ai-evals/references/measurement-pitfalls.md` §9; reguła odłożonego zbioru dla skilli fabryki — `core-skill-authoring`, tf#104)**:** w PR przewidywanie (które
  przypadki mają przejść z porażki na sukces, co grozi regresją), wynik względem zamrożonej linii bazowej
  i odłożonego zbioru, potem wdrożenie albo wycofanie. Autor zmiany nie może jednocześnie zmieniać scenariuszy, na
  których jest oceniany (jak chronione testy akceptacyjne wyżej) — dotyczy też agentów poprawiających skille.
- [x] **Granica pętli samodoskonalenia** (zrobione 2026-10-30: `core-async-delegation` §5) (do `core-async-delegation`): pętla, która poprawia własny harness, nie ma
  zapisu do polityki uprawnień, piaskownicy, tożsamości ani zestawu ewaluacji (osobne repo / tylko odczyt); przykłady
  z artykułu: DGM usunął znaczniki wykrywania halucynacji z własnej funkcji nagrody i sfabrykował log testów.
- [x] **Manifest pary model + harness** (zrobione 2026-10-30 w `ai-evals`: `ai-evals/references/measurement-pitfalls.md` §6; `ai-mlops` — odnośnik do zrobienia przy jego przeglądzie) (do `ai-mlops` / `ai-evals`): wersja modelu, skrót promptu, wersja schematów
  narzędzi, odwołanie do polityki, skrót obrazu środowiska, wersja zestawu ewaluacji — wynik ewaluacji przypisany do
  pary, cicha zmiana modelu u dostawcy = nowa para do ponownego pomiaru.

Artykuł „The Economics of Agents: Token Accounting, Caching, and Routing” (S. Singhal, 2026-08-18) — mało nowego:
cache i stały prefiks, kaskada modeli, budżet i limit tur mają `core-cost-control`, `eng-llm-features` i
`ai-prompt-engineering`; ci_for_sdlc zapisuje tokeny cache i p95 czasu. Jedna pozycja:
- [x] **`eng-llm-features`, rachunek per zadanie** (zrobione 2026-10-30: §4)**:** w śladzie każdego wywołania pięć liczb (wejście, odczyt cache, zapis
  cache, wyjście, myślenie), w logu tokeny, a cena liczona przy odczycie; koszt na *ukończone zadanie* jako percentyle
  (p95/p99 to zwykle pętla ponowień, nie średnia); „efektywna cena wejścia” jako miara działania cache; praca
  asynchroniczna przez Batch API; wyniki (nie tylko prompty) cache'owane dla powtarzających się pytań.

## Diagnoza awarii z LLM wokół reguł deterministycznych (artykuł „Making Failure Diagnosis Reliable with Pensive AI”, Netflix Tech Blog, 2026-10, zapisane 2026-10-29)
Przegląd 2026-10-29: `ai-evals` ma bramkę w CI, próbki z ruchu i sędziego z kalibracją; `eng-llm-features` —
strukturyzowane wyjście i budżet. Liczby z artykułu (np. 321% więcej ręcznych przeglądów logów bez narzędzia,
obserwacja, nie przyczyna) [niezweryfikowane]. Braki, do `eng-llm-features` i `ai-evals`:
- [x] **Model wskazuje zakres, kod składa treść** (zrobione 2026-10-30: `ai-evals/references/measurement-pitfalls.md` §8, `eng-llm-features` §2)**:** wejście z ponumerowanymi liniami, model zwraca numer pierwszej
  i ostatniej linii fragmentu, a tekst odtwarza kod z własnej kopii — dwie liczby zamiast przepisywania śladu stosu
  (mniej tokenów wyjścia, krócej, treść bez halucynacji; zły zakres nadal możliwy, więc mierzony w ewaluacji).
- [x] **Reguły jako podłoga regresji i źródło etykiet** (zrobione 2026-10-30: `ai-evals/references/measurement-pitfalls.md` §8)**:** istniejące reguły (regex) działają zawsze, wynik LLM obok;
  ewaluacja sprawdza, czy to, co znalazła reguła, jest w wyniku LLM (sędzia „włączenie”), osobno precyzję każdego
  elementu i **szum na poziomie zbioru** — linie obecne w > ~30% wyników idą na listę wykluczeń (prompt ich nie usuwa).
- [x] **Niezmienne kopie wejść do ewaluacji** (zrobione 2026-10-30: `ai-evals/references/measurement-pitfalls.md` §7)**:** dane wejściowe produkcji (logi wygasające po 7–30 dniach) archiwizowane
  asynchronicznie bez nadpisywania, ewaluacje czytają archiwum — zmiana wyniku przypisana systemowi, nie źródłu.
  Ten sam zestaw ewaluacji lokalnie, na środowisku podglądu PR (progi blokują merge), po promocji (alarm do dyżurnego)
  i cyklicznie na produkcji (dryf).
- [x] **Wzorce wywołań** (zrobione 2026-10-30: `eng-llm-features` §10)**:** wspólny termin dla równoległych wywołań (spóźnione pomijane, odpowiedź na czas); kosztowna
  analiza na żądanie, cache po jednostce pracy (nie po użytkowniku) z warunkowym zajęciem „w toku” i porzuceniem po
  limicie czasu; strumień wysyła pełną dotychczasową odpowiedź w każdym zdarzeniu (klient bez składania tokenów);
  ocena 👍/👎 przypięta do id śladu, 👎 jako alert w godzinach pracy; nowy model danych obok starego pola, aż klienci
  przejdą (bez zmiany pola w miejscu). Klasyfikacja „czy ponawiać” wymaga wyższego progu niż ekstrakcja — koszt
  błędu niesymetryczny.

Bez wpisu: „The Beauty of Markov Chains” (E. Lombardi, 2026-10-18 — łańcuchy pochłaniające i PageRank, poza zakresem
skilli fabryki poza ogólnym `eng-algorithms-data-structures`) i „AI Agents (05): The Double Trouble of Monitoring”
(0s & 1s, 2026-09-20 — monitoring infrastruktury plus śladów agenta jest już w pozycji o OTel GenAI).

## Bramka przed narzędziem: pokrycie skutków, nie nazw narzędzi (artykuł „AI Agent Gate and Model Router: The System One (Jev) Model, LangChain Middleware, and Auto Mode”, J. Wąsowski, 2026-10-12, zapisane 2026-10-29)
Przegląd 2026-10-29: `core-agent-security` opisuje tryb `auto` (klasyfikator w tle), reguły deny działające w każdym
trybie i piaskownicę jako granicę; `sec-llm-security` — zatwierdzenie ze skutkiem. Sprawdzone 2026-10-29
(code.claude.com/docs/en/permission-modes): reguły deny blokują w każdym trybie, także `bypassPermissions`; sesje
w chmurze zatwierdzają edycje plików niezależnie od trybu. Liczby z artykułu (AmPermBench: 36,8% zmian stanu
— 93 z 253 — przez edycję plików w projekcie, poza klasyfikatorem; 81% niebezpiecznych akcji przeszło całość;
próg eskalacji auto mode 3 kolejne / 20 odmów; ceny i opóźnienia Jev) [niezweryfikowane]. Braki:
- [x] **`core-agent-security` / `sec-llm-security`, pokrycie bramki** (zrobione 2026-11-01: `core-agent-security/references/permissions-and-production.md` §4d)**:** bramka zdefiniowana listą skutków (zapis pliku
  poza bezpiecznym zakresem, sieć, sekrety, uruchomienie procesu), nie nazw narzędzi (`tools=["bash"]` przepuszcza
  ten sam skutek przez edycję pliku stanu — podmiana narzędzia). Trzy osobne liczby: pokrycie (odsetek zmian stanu,
  które w ogóle docierają do bramki), błędy klasyfikatora (FPR/FNR na tym, co ocenił), pominięcia od końca do końca;
  przed trybem blokującym tryb cienia i policzenie obejść. Kolejność warstw: reguły deny i piaskownica na skutek
  (nie tekst polecenia) → klasyfikator w szarej strefie → człowiek po serii odmów i dla legalnych akcji wysokiego
  ryzyka; akcje niszczące, finansowe, wyprowadzające dane i zmiany uprawnień nigdy tylko na klasyfikatorze.
  Bramka stoi najbliżej narzędzia, po każdym kroku, który może zmienić wywołanie (edycja przez człowieka po
  klasyfikacji = wywołanie bez oceny); licznik odmów z eskalacją, bo bramka bez niego uczy podmiany narzędzia.
- [x] **Próg jako polityka** (zrobione 2026-11-01: tamże §4d, z kartą warstwy decyzji)**:** próg klasyfikatora konfigurowalny i uzasadniony kosztem fałszywej blokady vs pominięcia,
  z liczbą bazową (0,1% groźnych wywołań przy FPR 0,4% → ok. 1 z 5 alarmów prawdziwy); co widzi sędzia (prośby
  użytkownika i ładunek wywołania, bez prozy agenta — inaczej da się go przekonać) i dokąd idą argumenty narzędzi
  (sekrety w argumentach wychodzą do dostawcy klasyfikatora). Karta warstwy decyzji z artykułu jako szablon do ADR.

## Wnioskowanie przyczynowe w analizie danych (artykuł „Causal Machine Learning: Moving Beyond Prediction to Real Decisions”, G. Nguyen, 2026-09-22, zapisane 2026-10-29)
Przegląd 2026-10-29: `data-analysis` ma zmienne zakłócające, paradoks Simpsona, „korelacja to nie przyczynowość”,
a w `references/time-series-and-econometrics.md` różnicę w różnicach i zmienne instrumentalne. Wielkość rynku
i odsetki z artykułu [niezweryfikowane]. Braki:
- [x] **`data-analysis` (lub `ai-research-methods`): przyczynowość krok po kroku** (zrobione 2026-10-30: `references/time-series-and-econometrics.md`) — najpierw graf przyczynowy (DAG)
  z ekspertem domeny: czynnik zakłócający kontrolujesz, mediatora i zderzacza (collider) nie (kontrola mediatora
  blokuje badany efekt, zderzacza — wprowadza obciążenie); potem metoda: wagi skłonności (propensity), zmienne
  instrumentalne, podwójne ML z cross-fittingiem, lasy przyczynowe; ATE („czy działa”) vs CATE/uplift („dla kogo”
  — zniżka dla tych, których zachowanie zmienia, nie dla tych, którzy i tak zostaną); na końcu **próby obalenia**
  (losowa wspólna przyczyna, placebo, podzbiór danych) — wynik zmieniony przez losową zmienną jest kruchy. Biblioteki:
  DoWhy (graf, identyfikacja, obalanie), EconML (CATE), CausalML (uplift) — wersje sprawdzić przed wpisaniem.
  Rozdział: model churnu mówi „kto odejdzie”, decyzja potrzebuje „czyje odejście zmieni rabat”.

Artykuł „Graph Engineering” (V. Amballa, 2026-10) — bez wpisu: praca jako jawny graf (węzły, krawędzie z bramkami
człowieka tam, gdzie ryzyko, stan współdzielony, punkty kontrolne) jest w `ai-agents` (workflow czy agent, trwały
stan, punkty zatwierdzenia) i w fazach pdi z bramkami; artykuł nie wnosi metody poza zasadą.

## Blokady optymistyczne i pesymistyczne, skill od wzorcowego wyniku (artykuły „When to Use Optimistic vs Pessimistic Locking”, A. Kovtun, 2026-10-14; „I Built a Claude Skill for PRD Writing… Started With the Output”, J. More, 2026-06-30; zapisane 2026-10-29)
- [x] **`be-database`, wybór blokady** (zrobione 2026-10-30: sekcja „Transakcje”; domyślne limity czasu baz z artykułu nie wpisane) (dziś jedna linia: `FOR UPDATE`, unikalne ograniczenia lub wersjonowanie;
  `SKIP LOCKED` przy kolejce): pytanie zerowe — czy jedno atomowe `UPDATE … SET x = x - 30 WHERE … AND x >= 30` albo
  ograniczenie (`UNIQUE`, `EXCLUDE`) usuwa okno między odczytem a zapisem; potem trzy pytania po kolei: czy okno mieści
  się w jednej krótkiej transakcji (nie — myślenie użytkownika, kilka żądań: wersja/ETag albo dzierżawa z wygaśnięciem
  w aplikacji), jak często piszący trafiają w ten sam wiersz (rzadko — optymistycznie z ograniczoną liczbą ponowień
  i jitterem; gorący wiersz — pesymistycznie), ile kosztuje utracona praca (efekt zewnętrzny, nieidempotentny — blokada
  przed pracą). Pułapki: zakleszczenia (stała kolejność blokowania), żadnych wywołań sieciowych pod blokadą wiersza,
  `NOWAIT`; wersja wiersza nie chroni przed write skew (reguła na kilku wierszach — Serializable albo blokada wspólnego
  rodzica); blokada w Redis tylko dla efektywności, dla poprawności tokeny ogrodzeniowe (Kleppmann). Wersje baz
  i domyślne limity z artykułu (MySQL 9.7 LTS, `innodb_lock_wait_timeout` 50 s, Postgres `deadlock_timeout` 1 s)
  sprawdzić przed wpisaniem.
- [x] **`core-skill-authoring`, specyfikacja wyniku przed przepływem** (zrobione 2026-10-30: Procedura krok 1)**:** skill z instrukcji krok po kroku daje płaski
  wynik; lepiej wziąć najlepszy istniejący artefakt (np. PRD, który przeszedł przegląd bez pytań) i wypisać decyzje,
  których ogólny szablon nie zna (kolejność sekcji pod czytelnika, nierówna głębia, język sekcji przypadków brzegowych
  pod QA, ograniczenia prawne wprost, metryka jako zachowanie) — to staje się treścią skilla i scenariuszami ewaluacji;
  plus 2–3 pytania, które skill zadaje przed pisaniem (w artykule: „co jedno musi być prawdą, żeby to był sukces?” —
  brak odpowiedzi = za wcześnie na specyfikację). Dotyczy też planowanych skilli `pm-*` (persona Paweł).

Bez wpisu: „Before You Blame the Model” (R. Ravishankar — wstęp serii o harnessie bez konkretów poza zapowiedziami:
projekt jako dane sprawdzane z buildem, bramka ewaluacji w ścieżce wydania — oba już w TODO) i „What is Loop
Engineering?” (A. Kokane, 2026-06-17 — `/goal`, `/loop`, pięć elementów pętli za A. Osmanim; ujęte wcześniej przy
„Practical Loop Engineering” i rutynach).

## Kontrakt zachowania przy zmianach w legacy i pomiar „harness: wynik czy koszt” (artykuły „Brownfield Spec and Preservation Contract”, J. Wąsowski, 2026-10-22; „When Agent Harness Moves the Result, and When It Only Moves the Cost”, J. Wąsowski, 2026-10-13; zapisane 2026-10-29)
Przegląd 2026-10-29: `eng-behavior-preserving-refactoring` ma zamrożony kontrakt i testy charakteryzujące przed
refaktorem (oznaczone, nie są specyfikacją); w TODO jest krok archiwizacji delty OpenSpec i chronione testy
akceptacyjne. Liczby z artykułów (2,66% agentowych PR z commitem cofającym, 29,6% „rozwiązanych” łatek innych niż
ludzka, METR: harness dostawcy nie lepszy od prostego, rozrzut tokenów na rozwiązane zadanie do 40×, słabszy model
29,2 → 78,0% dzięki korekcie zachowania) [niezweryfikowane]. Braki:
- [x] **Kontrakt zmiany w istniejącym systemie (`mode-pdi`, `eng-behavior-preserving-refactoring`)** (zrobione 2026-11-01: `eng-behavior-preserving-refactoring/references/change-contract.md`; pola w szablonie mode-pdi — razem z krokiem scalenia CHG, do decyzji)**:** sześć pól —
  warunek (kiedy zmiana działa), oczekiwany wynik (nie „błąd zniknął”), chronione zachowania, dozwolony zakres plików
  (wyjście poza = zgłoszenie), dowód naprawy (test czerwony na commicie bazowym, zielony po), dowód braku regresji
  (testy ochronne nagrane na commicie bazowym **przed** zmianą, osobnym etapem, zielone przed i po). Chronione
  zachowania z czterech źródeł w zasięgu zmiany (wywołujący/konsumenci — brak znalezionych to ograniczona wiedza,
  nie dowód; incydenty; często zmieniane pliki; testy charakteryzujące), każde z kolumną **decyzji**:
  zobowiązanie (chronić) / przypadek (wolno zmienić) / do decyzji właściciela — z nazwiskiem decydującego; zmiana
  zachowania widocznego dla konsumenta to już nie refaktor. Przy archiwizacji zatwierdzone gwarancje trafiają do
  delty jako ADDED (pierwszy zapis wymagania) z testem. Bez pełnej inwentaryzacji systemu na start.
- [ ] **Skille fabryki: wynik czy tylko koszt** (część B zrobiona 2026-11-01 na Haiku: `docs/evals/2026-11-01-luka-strojenie-holdout-podsumowanie.md` — przewaga skilli +50 pp na strojeniu, +14 pp na holdoucie, skill uruchomiony → 93% na holdoucie; nowe scenariusze strojenia innymi słowami (`gen-*`, 25 pytań od agenta bez dostępu do treści skilli) dla `core-delivery-lifecycle`, `eng-testing`, `core-agent-security`, `sec-llm-security`, `core-grounding` dopisane 2026-11-01 — hook nie łapał 14/25, po dopisaniu ogólnych sformułowań do `keywords` 25/25; ponowny pomiar 2026-11-01 (`docs/evals/2026-11-01-luka-po-poprawkach-podsumowanie.md`, 20,01 USD): holdout ze skillami 80→84%, luka +15→+10 pp, przewaga na holdoucie +14→+21 pp; uruchamianie poprawiło się tylko w `eng-testing` — pola `description` czterech skilli (`core-agent-security`, `core-grounding`, `core-delivery-lifecycle`, `sec-llm-security`) przepisane 2026-11-01 na język sytuacji użytkownika (`--hints` czyste, bramka OK); pomiar po tej zmianie 2026-11-02 (`docs/evals/2026-11-02-luka-po-opisach-podsumowanie.md`, 21,07 USD): nieuruchomione na holdoucie 12→10/56 (`core-delivery-lifecycle` 0→1/4, `sec-llm-security` 2→3/4, `core-agent-security` i `core-grounding` bez zmian 2/4), holdout ze skillami 84→80% (w rozrzucie), przewaga na holdoucie +20 pp — zmiana neutralna, opisy zostają; świeże pytania holdout dopisane 2026-11-02: 24 scenariusze `h2-*` (po 2 na każdy z 12 skilli), napisane przez agenta bez dostępu do repo i treści skilli, kryteria sprawdzone na wzorcowej dobrej i złej odpowiedzi, autor zmian skilli ich nie czytał; zostaje pomiar na nich (Haiku albo Sonnet, ok. 20–25 USD, decyzja człowieka) — wynik `h2-*` raportować osobno od starego holdoutu; część A zrobiona 2026-10-30: `docs/evals/2026-10-30-wynik-czy-koszt.md` — zamknięty zbiór 24 scenariuszy, Haiku 85% vs 50%, Sonnet 90% vs 58% pełnych odpowiedzi ze skillami / bez; przewaga nie maleje z mocą modelu. Zostało: część B — te same skille na scenariuszach strojenia, żeby zmierzyć zawyżenie wyniku, ok. 20 USD, po odnowieniu limitu tygodniowego; przyczyny słabego `core-grounding` i `core-delivery-lifecycle` — zbadane 2026-10-30 bez modelu: `core-grounding` nie był podpowiadany przy długich dokumentach i zużytej sesji (luka w opisie, dopisane 2 scenariusze strojenia i słowa; holdout „regulamin” teraz podpowiadany, „sesja” nadal nie — sprawdzić przebiegiem po odnowieniu limitu); `core-delivery-lifecycle` jest podpowiadany, ale model wybiera `core-async-delegation` — granica obu skilli przy „warunku końca kroku” — decyzja 2026-10-30: zostaje (stop agenta bez nadzoru → `core-async-delegation`), scenariusz holdout oznaczony w raporcie jako niejednoznaczny; dopisane 4 scenariusze holdout na reguły fabryki (`eng-testing`, `be-api-design`, `ai-evals`, `dom-ev-ocpp-16`) — do przebiegu na modelu; test „no-op” dla skilli bez przewagi zrobiony 2026-10-30 — wycięta tylko wiedza podręcznikowa: `be-api-design` −12% słów, `eng-testing` −5%, `ai-evals` −1%, `dom-ev-ocpp-16` bez zmian (fakty protokołu chronią przed zmyślaniem). Wniosek: skille są zwięzłe; brak przewagi na zamkniętym zbiorze wynika z tego, że jego pytania trafiły w ogólną część skilli, a nie w reguły fabryki — dopisać po jednym scenariuszu holdout na regułę specyficzną (np. TDD w fabryce, Problem Details i `Idempotency-Key`), zanim uznamy skill za zbędny) (protokół z artykułu do runnera ewaluacji): ta sama para „ze skillami /
  bez” na tym samym zestawie, raport rozdzielny — odsetek sukcesów, koszt łączny na rozwiązane zadanie (wszystkie
  próby, także porzucone, przez liczbę sukcesów), mediana tokenów udanych prób, pass@k z przedziałem, czas, rodzaje
  porażek; drugi przebieg na mocniejszym modelu (pomiar 2026-10-22 był tylko na Haiku) — jeśli przewaga skilli maleje
  z mocą modelu, inwestować w scenariusze ewaluacji, hooki i politykę uprawnień, nie w dłuższe treści. Ablacja
  pojedynczych elementów, bo składniki potrafią sobie szkodzić. Płatne — tylko za zgodą człowieka.

Bez wpisu: „The Harness Is the Product” (S. Singhal, 2026-08-10) — przegląd elementów harnessu (pętla, narzędzia,
kontekst, pamięć, uprawnienia, weryfikacja, obserwowalność, podagenci) pokrytych przez `ai-agents`,
`core-cost-control` i wcześniejsze pozycje TODO.

## Agent analityczny nad hurtownią: wnioski z case study (artykuł „Engineering Multi-Agent AI for a 100 GB Data Warehouse”, F. Khan, 2026-10, zapisane 2026-10-29)
Przegląd 2026-10-29: brak w fabryce wzorca „pytanie biznesowe → SQL” (text-to-SQL); części są w `ai-evals`
(bramka, linia bazowa z rozrzutem), `sec-llm-security` (walidacja argumentów w kodzie), `data-engineering`. Liczby
autora (jeden laptop, TPC-DS SF100, 102 pytania dev / 194 test, modele Qwen) [niezweryfikowane]. Wnioski warte
przeniesienia (do `ai-evals`, `eng-llm-features`, `sec-llm-security`, `data-analysis`/`data-engineering`; ewentualnie
nowy skill `ai-text-to-sql` wg `core-skill-authoring`, najpierw scenariusze):
- [x] **Cele zapisane przed pierwszym agentem** (zrobione 2026-10-31: `ai-evals/references/measurement-pitfalls.md` §12) (trafność, odsetek złych odpowiedzi wśród udzielonych raportowany
  razem z pokryciem, p50 i p95 czasu) i **użyteczność z karą**: +1 dobra odpowiedź lub słuszna odmowa, 0 odmowa,
  −2 pewna zła liczba — agent, który wszystkiemu odmawia, nie wygrywa. Każda zmiana jedna naraz, przyjęta tylko gdy
  użyteczność rośnie (albo stoi, a czas spada), z parowanym bootstrapem na tych samych pytaniach; odłożone **całe
  szablony** pytań, nie tylko instancje (u autora 85% na nowych szablonach vs 96% na znanych). Czas mierzony
  pojedynczym użytkownikiem i stoperem z pustym cache, nie tylko przy współbieżności ewaluacji.
- [x] **Podwójny zapis jako miara pewności** (zrobione 2026-10-30: `arch-ai-solutions` krok 9)**:** dwie niezależne drogi (model pisze SQL; drugi model wypełnia JSON
  z katalogu metryk, a kod kompiluje go do SQL regułami) — zgodność wyników = wysoka pewność (u autora 40/40
  zgodnych poprawnych), rozbieżność → krytyk, brak drugiej drogi → niższa pewność; prawie wszystkie błędy z pytań,
  gdzie odpowiedziała jedna droga. Do `arch-ai-solutions` jako wzorzec weryfikacji wyniku liczbowego.
- [x] **Mierz, zanim dołożysz** (zrobione 2026-10-30: `arch-ai-solutions` krok 9)**:** wyszukiwanie wartości do promptu (−2,0 pkt) i „zwiadowca schematu” wybierający
  5 tabel (−13,7 pkt; potrzebne tabele trafiał w 27% zapytań) pogorszyły wynik, gdy cały schemat mieścił się
  w prompcie; tańszy model napisał lepszy SQL niż droższe (porównanie kilku modeli na tym samym zestawie przed
  wyborem). Model pisze SQL, baza liczy — arytmetyka modelu bez myślenia była błędna.
- [x] **Ściany dla SQL od modelu** (zrobione 2026-10-30: `sec-llm-security/references/threats-and-controls.md`) (`sec-llm-security`): tryb tylko do odczytu nie wystarcza (SELECT czyta pliki,
  dołącza bazy, instaluje rozszerzenia — 5/11 ataków przeszło); strażnik tekstu (jedno SELECT, zakazane funkcje
  plikowe, koszt planu z własnym estymatorem wierszy, bo planer pomylił się 469 796×) + blokada w silniku (DuckDB:
  `enable_external_access = false`, wyłączone autoładowanie rozszerzeń, `lock_configuration = true`) + limit czasu
  i wierszy; przerwanie zapytania działa dopiero między krokami silnika (ogon czasu przez jedno utknięte zapytanie).
  Bramka wejściowa zawodzi otwarcie (nieczytelna odpowiedź = „odpowiadaj”), spekulacyjnie równolegle z drafami.
- [x] **Pułapki danych dla agenta** (zrobione 2026-10-30: `data-engineering`, sekcja „Dane dla agenta AI”) (`data-engineering` / `data-analysis`): klucze NULL w tabeli faktów, które inner
  join gubi po cichu (u autora 2,36% przychodu), niepełny ostatni rok w danych (spadek, który nie jest spadkiem),
  tabele z historią wersji (podwójne liczenie encji) — fakty mierzone z danych i wstawiane do słownika biznesowego
  w stałej kolejności (stały tekst = trafienia cache); „najlepszy sklep” bez definicji → pytanie, nie domysł.

## Typy pamięci agenta jako kontrakty (artykuł „AI Agent Memory Types: Semantic, Episodic, Procedural, Profile, Working”, J. Wąsowski, 2026-10-08, zapisane 2026-10-29)
Przegląd 2026-10-29: `ai-agents` nie rozróżnia typów pamięci długotrwałej. Wyniki porównań z artykułu (ENGRAM
77,55 → 46,56% po spłaszczeniu magazynów, preprint; pozostałe dwa nie testują typowania) [niezweryfikowane].
- [x] **`ai-agents`, pięć pytań zamiast jednego indeksu wektorowego** (zrobione 2026-10-31: `ai-agents/references/memory-and-durable-execution.md` §1)**:** robocza (bieżący kontekst składany z pozostałych,
  budżet tokenów i kolejność), semantyczna (co jest prawdą: źródło, data weryfikacji, konsolidacja zastępuje stary
  fakt), epizodyczna (co się stało: czas, kontekst, wynik; traci przydatność, nie prawdziwość), proceduralna (jak to
  robić: wersja, przegląd, wycofanie — zapis jak merge request, bo zły wpis zmienia zachowanie w wielu zadaniach),
  profil (kim jest użytkownik: krótki dokument zawsze w prompcie, łatka w miejscu). Rozdzielać fizycznie dopiero po
  objawie (przeterminowany fakt wraca jako bieżący, wpis tymczasowy konkuruje ze stałym) — często wystarcza pole
  typu i wygaśnięcia w jednym magazynie. W fabryce odpowiedniki: `docs/project/lessons.md` (semantyczna), dziennik
  i punkty kontrolne (epizodyczna), skille przez PR (proceduralna).

## Trwałe wykonanie agentów i refinement pod SDD (artykuły „Inngest vs Temporal vs DBOS vs LangGraph”, P. Perrone, 2026-09-22; „Refinement with AI: How to Prepare Requirements for Spec-Driven Development”, Pragmatic Coders, 2026-10-01; zapisane 2026-10-29)
Przegląd 2026-10-29: `ai-agents` każe projektować wznawianie od punktu kontrolnego, bez kryteriów wyboru narzędzia.
Sprawdzone 2026-10-29 w źródłach (raw.githubusercontent.com): Inngest — wynik kroku zapisywany po wykonaniu,
przy kolejnym wywołaniu SDK szuka go po skrócie nazwy kroku (`inngest/website`, how-functions-are-executed); DBOS —
punkty kontrolne kroków w Postgresie, jeden zapis na krok plus dwa na workflow (`dbos-inc/dbos-docs`, architecture).
Domyślny tryb `async` w LangGraph i szczegóły Temporal — [niezweryfikowane] (docs.langchain.com, docs.temporal.io
poza siecią sesji). Artykuł jest sponsorowany przez Inngest (autor to ujawnia).
- [x] **`ai-agents` / `arch-ai-solutions`, trwałe wykonanie** (zrobione 2026-10-31: `ai-agents/references/memory-and-durable-execution.md` §2)**:** zysk zależy od granic kroków, nie od narzędzia — jeden
  krok na każde kosztowne wywołanie modelu lub narzędzia (jeden krok na całą pętlę = kolejka z dodatkami); wszystko
  poza krokiem wykonuje się ponownie przy wznowieniu (Inngest: przy każdym kroku, Temporal: kod workflow musi być
  deterministyczny — zegar, losowość, HTTP tylko w aktywnościach). Pułapki ustawień: zapis punktu kontrolnego
  w tle może zgubić ostatni krok; wznowienie z tym samym wejściem nadpisuje stan; brak stałego id workflow = drugi
  przebieg obok pierwszego; zmiana nazwy kroku osieroca przebiegi w toku (wersjonowanie). Trwałość ≠ idempotencja
  (krok, który obciążył kartę i nie zdążył zgłosić sukcesu). Wybór: graf + checkpointer w Postgresie, gdy agent
  już jest grafem; stan w tej samej transakcji co dane → DBOS; dane kroków nie mogą opuścić sieci → bez usług
  hostowanych; brak zespołu platformowego → bez własnego klastra. Test odzyskiwania: `SIGKILL` w środku przebiegu
  i policzenie, co wykonało się ponownie — przed produkcją.
- [x] **`proc-requirements-shaping` / `core-delivery-lifecycle`, refinement pod SDD** (zrobione 2026-11-01: `core-delivery-lifecycle/references/ai-native-sdlc.md` §13)**:** u autorów refinement zajmował
  ok. 30% sprintu (prognoza do 50%) [niezweryfikowane]. Brakuje u nas dwóch kroków: przed implementacją wykonawca
  **opowiada rozwiązanie własnymi słowami** (problem, zachowanie, sposób, ryzyka, podjęte decyzje), a właściciel
  sprawdza zgodność z zamiarem — żeby człowiek nie był tylko przekaźnikiem między agentami; makiety z istniejących
  komponentów i systemu projektowego przed kodem jako test wspólnego rozumienia (sprawdzić, czy nie przemycają
  nowych decyzji produktowych). Przegląd historyjki przez agentów z kilku ról (deweloper, PO, interesariusz) jest
  w pozycji „gdzie agent musiałby zgadywać” wyżej.

## Model zastępczy i projekt odwrotny; miary autonomii agentów (artykuły „How I Recreated a Research Paper to teach an AI to Design Self-Rolling Tubes”, A. Janmohamed, 2026-10-22; „Agentic SDLC: Strategic Reading List”, A. Honchar, 2026-05-27; zapisane 2026-10-29)
Przegląd 2026-10-29: `ai-research-methods` ma wyciek przez wiele wierszy tej samej jednostki; brak wątku modelu
zastępczego (sieć zamiast wolnej symulacji) i optymalizacji na nim. Liczby z artykułów [niezweryfikowane].
- [x] **`ai-research-methods`, model zastępczy w pętli optymalizacji** (zrobione 2026-10-31: `references/optimization-and-hypotheses.md` §1)**:** (1) przykłady powstałe z augmentacji
  (odbicie, obrót) trafiają do tego samego zbioru co oryginał, inaczej test jest zawyżony; uśrednianie predykcji dla
  wersji symetrycznych w czasie testu jako tani zysk; (2) optymalizacja na modelu wyszukuje jego błędy na swoją
  korzyść — zwycięzca zawsze wygląda lepiej, niż jest (u autora 0,44 mm przewidziane vs 0,75 mm w symulatorze), więc
  wynik sprawdza się prawdziwym symulatorem/eksperymentem, a raport podaje obie liczby; (3) cel spoza zakresu danych
  treningowych (fizycznie niemożliwy) daje pewną, złą odpowiedź — najpierw policz granicę wykonalności, potem
  szukaj; (4) w algorytmie ewolucyjnym zbyt duża mutacja (20% zamiast 2%) zamienia przeszukiwanie w losowanie.
- [x] **`core-delivery-lifecycle` / `eng-continuous-delivery`, miary autonomii** (zrobione 2026-11-01: `ai-native-sdlc.md` §13)**:** obok DORA odsetek scalonych PR
  autorstwa agenta, godziny przeglądu człowieka na zmianę, czas zadania od początku do końca; wg autora, jeśli po
  ~6 miesiącach agentowe PR to < 5%, wąskim gardłem są specyfikacje, harness i struktura przeglądu, nie narzędzie
  (próg to opinia autora, nie pomiar). Pasuje do decyzji G7 „miary przepływu” w ci_for_sdlc/pdi.
  **Zastrzeżenie** (J. Wąsowski, „SDD Factory OKRs”, 2026-10-21): to miary aktywności — jako cel (KR) są
  podatne na Goodharta, bo agent wypełni każdy licznik; raportować je tylko w parze z miarą wyniku (odsetek
  defektów, które dotarły do użytkownika, koszt zmiany, czas inicjatywy od zamiaru do produkcji, ruch metryki
  biznesowej) — gdy poprawia się tylko jedna z pary, cel uznaje się za niespełniony; dane z systemów źródłowych
  (repo, CI, incydenty), nie z samooceny zespołu.

## Graf hipotez z werdyktami i granice izolacji worktree (artykuły „My AI Agent is in Top-0.04% of WorldQuant Challenge #2: Alpha Knowledge Graph”, A. Honchar, 2026-07-31; „Self-managing coding agents: git worktree, agent-owned context, and sandbox”, J. Wąsowski, 2026-06-01; zapisane 2026-10-29)
Przegląd 2026-10-29: `ai-research-methods` każe zapisać hipotezę falsyfikowalnie z kryterium porażki;
`core-cost-control` (`references/parallelism.md`) opisuje worktree i subagentów. Liczby z artykułów (ranking,
3 432 mechanizmy, 172 GB / 371 worktree, 93% akceptowanych zapytań o zgodę) [niezweryfikowane].
- [x] **`ai-research-methods`, rejestr hipotez jako graf z werdyktami** (zrobione 2026-10-31: `references/optimization-and-hypotheses.md` §2; pole statusu w `core-knowledge` — osobno)**:** hipoteza, której nie da się przypiąć do węzła
  ontologii (mechanizm, naruszone założenie, kto jest po drugiej stronie), odpada przed kosztownym eksperymentem;
  status węzła wynika z wyników eksperymentów (potwierdzony / pogrzebany), nie z deklaracji autora; pogrzebany ma
  zapisany z góry **warunek ponownego otwarcia** (nowa konstrukcja, niezależne potwierdzenie); zapis „próbowano,
  tak się nie udało” z zakresem — im szersze twierdzenie, tym więcej niezależnych porażek do jego odrzucenia;
  luki wskazuje topologia (rodziny bez mechanizmów), nie pytanie do modelu. Prosta implementacja: SQLite `nodes`
  / `edges` (klucz = cała trójka), graf w pamięci tylko do odczytu. Wybór kręgosłupa ontologii decyduje, które
  pytania są tanie. Pasuje też do `core-knowledge` (pole statusu i warunku ponownego otwarcia w notatkach).
- [x] **`core-cost-control` / `core-async-delegation`, czego worktree nie izoluje** (zrobione 2026-10-31: `core-git-workflow`, „Praca równoległa”; sekwencje ANSI w wyjściu narzędzi bez wpisu — przypadek niezweryfikowany)**:** porty, baza i migracje, cache,
  brak `node_modules`/`.env` w świeżym checkoucie, blokada `.git/index.lock`; ta sama gałąź nie może być w dwóch
  worktree. Zadań dotykających tych samych portów, baz lub plików nie puszczać równolegle; limit liczby
  i sprzątanie zapomnianych worktree (koszt dysku rośnie z zależnościami). Do `core-agent-security`: wynik narzędzia
  może ukrywać polecenia sekwencjami ANSI niewidocznymi dla człowieka w terminalu, a widocznymi dla agenta (przypadek
  biblioteki jqwik z artykułu, [niezweryfikowane]) — treść wyjścia narzędzi to dane, nie polecenia.

Bez wpisu: „How to Build a Swarm of AI Agents That Hunts Alpha 24/7” (Moonsat, 2026-07-06) — reklama narzędzia Slate;
zasady (twórca ≠ sprawdzający, pamięć odrzuconych hipotez, warunek stopu sprawdzalny poza agentem) już są w
`core-async-delegation` i pozycjach wyżej.

## Proces z AI, który rozleniwia osąd; gdzie żyje specyfikacja w Scrum i Kanban (artykuły „The process we wrote was part of the problem”, M. Whetton, 2026-10-20; „Spec-Driven Development in Scrum and Kanban: Where the Spec Actually Lives”, J. Wąsowski, 2026-07-05; zapisane 2026-10-29)
Przegląd 2026-10-29: `core-delivery-lifecycle` ma ścieżkę skróconą dla poprawek; `core-plan-interview` — przesłuchanie
planu bez sztywnego limitu pytań; `proc-agile` — INVEST i Definition of Done, bez Definition of Ready. Liczby
zespołu Whettona (PR 40 → 165 linii, czas do merge 16 → 32 h, oczekiwanie na pierwszy przegląd 4 h → 2,5 dnia,
4,4 otwartych PR na osobę) [niezweryfikowane].
- [x] **`core-plan-interview`, przesłuchanie bez nadmiaru** (zrobione 2026-10-31: sekcja „Bez nadmiaru”)**:** „grill me” bez kontekstu wyciąga każdy przypadek brzegowy
  jako coś do rozwiązania i kończy się przeinżynierowaniem; pytania szeregować wpływem i prawdopodobieństwem,
  a „po prostu zawiedź z czytelnym błędem” traktować jako pełnoprawną odpowiedź (powiązane z drabiną minimalizmu
  w `eng-design-principles`). Sygnał ostrzegawczy procesu: zaległości wygenerowanych zgłoszeń, których nikt nie
  zrobi, i opisy PR dłuższe niż ktokolwiek przeczyta.
- [x] **`core-delivery-lifecycle`, osąd nie może uciec do kroków** (zrobione 2026-11-01: `ai-native-sdlc.md` §13)**:** refinement kończy się zgłoszeniem napisanym przez
  człowieka dla człowieka (nie wygenerowanym opisem ani promptem); jeśli nikt w pokoju nie umie wyjaśnić, jak praca
  zostanie zrobiona, refinement nie jest skończony (łączy się z pozycją „opowiada rozwiązanie własnymi słowami”
  wyżej). Pogłębiony przegląd tylko powyżej progów (wielkość zmiany, obszar ryzyka) — wspólne testowanie albo
  przejście przez rozwiązanie z grupą; nie każdy PR. Miary do śledzenia: rozmiar PR, czas do pierwszego przeglądu,
  liczba otwartych PR na osobę — pasuje do G7 „miary przepływu” (ci_for_sdlc/pdi).
- [x] **`proc-agile`, specyfikacja w cyklu** (zrobione 2026-11-01: sekcja „Kanban”)**:** backlog i refinement na poziomie celu i zamiaru, kontrakt dojrzewa w
  sprincie (Scrum) albo przed punktem zobowiązania (Kanban, z limitem WIP na etapie analizy, żeby specyfikacje nie
  starzały się w kolejce); Definition of Ready jako umowa zespołu o jakości wejścia, nie bramka przeciw PO (uwaga
  M. Cohna). Trzy szczeble SDD (spec-first / spec-anchored / spec-as-source, B. Böckeler) — dobierać do problemu;
  mierzyć czas cyklu, odsetek przeróbek i stosunek linii Markdown do kodu, zamiast ufać odczuciu przyspieszenia.

Bez wpisu: „From Demo to Production: 5 Hard Lessons from Deploying AI Agents as an FDE” (A. Kokane, 2026-10) —
linia odcięcia przed budową, koszt na rozwiązane zadanie z czasem przeglądu człowieka, najprostszy kształt
orkiestracji, ślady od pierwszego dnia, złoty zbiór i wdrożenie etapami są już w `ai-product-management`,
`ai-evals`, `ai-agents` i pozycjach TODO wyżej.

## Ontologia obserwowalności i wiki z LLM w dwóch wersjach (artykuły „Ontology-Driven Observability: Building an End-to-End Knowledge Graph at Netflix Scale”, Netflix Tech Blog, 2026-10-16; „I Built Karpathy's LLM Wiki Twice”, L. Bernardo, 2026-05-17; zapisane 2026-10-29)
Przegląd 2026-10-29: `ops-sre-incidents` i `ops-observability` nie mają wątku łączenia danych z różnych narzędzi
(metryki, alerty, incydenty, wdrożenia, czat) przez wspólny model encji. Liczby Netflixa [niezweryfikowane].
- [x] **`ops-observability` / `ops-sre-incidents`, wspólny model encji dla dochodzenia** (zrobione 2026-10-31: `ops-observability`, „Agent AI i dochodzenie po incydencie”)**:** większość czasu analizy
  przyczyny (u Netflixa ok. 4 h) to odtwarzanie powiązań między narzędziami, które nazywają to samo inaczej
  (aplikacja / usługa / klaster). Zasady do skilla: tożsamość najpierw — encja powstaje tylko po walidacji
  w jednym autorytatywnym katalogu (bez ogólnego typu „usługa”, który znaczy cztery rzeczy); ontologia jako kod
  (PR, testy, wersje), pojęcia oddzielnie od instancji (por. pozycja o IRI wyżej); wyjście modelu ograniczone do
  wyliczeń i typów, więc z niedeterministycznych kroków powstaje deterministyczny zapis; wzbogacanie kolejne
  i „najlepsze możliwe” (wolne źródło degraduje graf, nie blokuje go); silnik korelacji **proponuje łańcuchy
  z dowodami i pewnością** (para „wdrożenie → błąd w logach” z wyższą wagą, okno czasu, odrzucenie poniżej
  progu), nie wydaje werdyktów; z kanału incydentu zapisywać rozumowanie (odrzucone hipotezy, co zadziałało, kto
  wiedział) — postmortem jako dane, nie tylko tekst. Zmiany proponowane przez agentów zatwierdza człowiek.
- [x] **Wiki z LLM: kod czy plik instrukcji** (zrobione 2026-11-01: `core-knowledge/references/notes-and-wiki.md` §4; lint struktury w `kb.py` — osobno, TDD, gdy wiki powstanie) (uzupełnienie pozycji o wiki kanonicznym): plik `AGENTS.md`
  z etapami wystarcza dla małej bazy (< ~200 dokumentów) i szukania kształtu; pipeline w kodzie, gdy korpus jest
  duży, wynik ma być powtarzalny, a wiki zasila dalszą automatykę — identyfikator strony jako skrót treści (zmiana
  nazwy pliku nic nie psuje), kontrakty typów między etapami, **lint struktury Markdown** przed zapisem (dwa H1,
  zepsuty frontmatter, martwe linki psują kolejne etapy po cichu), wyszukiwanie BM25 zamiast wektorów dla małej
  wiki. Dotyczy `kb.py` i notatek `docs/knowledge`.

Bez wpisu: „How to Create Loops with Claude Code” (Y. Hosni, 2026-06-24) — ten sam artykuł był już przeglądany;
wnioski są w sekcji „Rutyny, które zdobywają uprawnienia”.

## Brakujące decyzje w specyfikacji i harness 2026 (artykuły „SDD — Missing Spec Decisions: The Two-Implementations Technique and a Decision Register”, J. Wąsowski, 2026-10; „The Harness Is the Product: How Agents Are Actually Built in 2026”, A. Tkachuk, 2026-10-02; „What is AX Design?”, F. Lamenza, 2026-06-08; zapisane 2026-10-29)
Przegląd 2026-10-29: pozycja „gdzie agent musiałby zgadywać” (sekcja o zamiarze) szuka luk; rejestr decyzji
prowadzi pdi (`pdi-decisions`). Liczby z artykułów (EPIC: 11,8% vs 20,4% commitów naprawczych; produkty dots, Viktor,
Muse) [niezweryfikowane].
- [ ] **`proc-requirements-shaping` / `mode-pdi`, technika dwóch implementacji** (część w `proc-requirements-shaping` zrobiona 2026-11-01; zostaje spójność spec/plan/zadania w `mode-pdi` i pola w kontrakcie pdi)**:** dla zdania z przymiotnikiem jakości
  („szybko”, „bezpiecznie”, „odpornie”) naszkicować dwa rozsądne rozwiązania i sprawdzić, czy różnią się czymś
  widocznym dla użytkownika lub operatora — jeśli tak, specyfikacja milczy i brakuje decyzji. Pięć klas do pytania:
  skala, tryb wykonania (od razu / w tle), awaria i ponowienia, uprawnienia, migracja istniejących danych. Każda
  decyzja z wariantami, uzasadnieniem, **sposobem weryfikacji** (test, fitness function w CI, punkt przeglądu)
  i właścicielem (rola, nie „zespół”); odwracalność × zasięg: lokalne odwracalne decyduje agent z zapisem, szerokie
  proponuje agent, jednokierunkowe rozstrzyga właściciel przed kodem. Spójność spec / plan / zadania: każda decyzja
  w trzech artefaktach albo jawne „nie dotyczy” (cztery różne braki: brak decyzji, sprzeczność, zgodny błąd, ślad bez
  treści). Strona pdi: pola `verify` i `reversibility` w kontrakcie decyzji (dbqm45/pdi TODO).
- [x] **`ai-agents`, interfejs harnessu od strony modelu** (zrobione 2026-10-31: `ai-agents/references/executors-and-gates.md` §4)**:** operacja (jednostka intencji) realizowana przez narzędzie,
  narzędzie złożone (kod, deterministycznie) albo skill (instrukcje) — dojrzewa od skilla do narzędzia złożonego;
  skill odwołuje się do narzędzi po id, nie kopiuje ich schematów (jedno miejsce prawdy); mały zestaw prymitywów
  (`search_memory`, `list_capabilities`, `search_operations`, `load_operation`, `execute_operation`, `run_code`,
  `ask_human`), a zatwierdzenie wymusza harness, nie model; kanały (Slack, Teams, głos) jako adaptery
  normalizujące zdarzenie do jednej postaci — agent nie należy do kanału. Wybór kontekstu (pamięć, narzędzia) to
  często klasyfikacja, nie generowanie — tańszy selektor przed dużym modelem, mierzony na własnych danych.

Bez wpisu (poza powiązaniem): „What is AX Design?” — rola „detektywa” przed automatyzacją (proces taki, jak naprawdę
działa, z regułami w głowach ludzi; „czy w ogóle automatyzować”; jak poznać, że 10 000 przebiegów w nocy się udało)
pokrywa się z `ai-product-management` i `ux-service-design`; „enabler” (narzędzia i system projektowy czytelne dla
agenta) — z pozycjami o MCP wyżej.

## Agent proaktywny i klasy informacji wychodzącej (artykuły „Claude Duet: The AI That Messages You First”, U. Estari, 2026-10-22; „I Built a Stock Terminal That Decides in Under a Second. Just Jev, No LLM”, unicodeveloper, 2026-09-30; zapisane 2026-10-29)
Sprawdzone 2026-10-29 u źródła (claude.com/resources/articles/claude-duet, 2026-10-21, z dopiskiem z 2026-10-23):
Claude Duet — podgląd badawczy z listą oczekujących, dla Pro i Max w USA; poranny skrót i sprawdzanie podłączonych
aplikacji w ciągu dnia, wiadomość tylko gdy coś wymaga uwagi; własna maszyna wirtualna z przeglądarką; poświadczenia
obsługiwane jak w Claude Managed Agents (agent nie widzi haseł ani tokenów); akcje zatwierdza klasyfikator trybu
auto; **osobny klasyfikator i prompt bezpieczeństwa dla każdej wiadomości** — najściślejsza klasa (numery kart,
dokumenty tożsamości) odrzucana zawsze, inne wrażliwe (zdrowie, finanse osobiste) tylko na wyraźne polecenie
użytkownika. Wg artykułu Estariego (nie sprawdzone u źródła): wysłanie, płatność, podpis i usunięcie czekają na
zgodę, a handel papierami wartościowymi i przelewy między kontami są wyłączone nawet za zgodą [niezweryfikowane].
- [x] **`sec-llm-security` / `core-async-delegation`, polityka informacji wychodzącej dla agentów wysyłających
  wiadomości** (zrobione 2026-11-01: `sec-llm-security/references/agent-design-patterns.md` §8, wiersz „agent
  proaktywny” w `core-async-delegation` §2)**:** klasy danych z regułą per klasa — „nigdy” (karty, dokumenty tożsamości, sekrety), „tylko na wyraźne
  polecenie” (zdrowie, finanse osobiste), reszta; sprawdzenie każdej wiadomości wychodzącej osobnym klasyfikatorem
  poza głównym agentem, obok zatwierdzania akcji. Do tabeli trybów delegacji: agent proaktywny (skrót + sprawdzanie
  co kilka godzin zamiast ciągłego, bo koszt w limitach) — rytm i lista tematów ustawia użytkownik; lista akcji
  zakazanych nawet za zgodą.

Bez wpisu: „Jevinik” — wzorzec „zbierz dowody, zadaj pytania typowane, działaj” z modelem decyzyjnym zamiast LLM
(autor: ok. 40× szybciej przy podobnych prawdopodobieństwach, dwa tickery po dwa przebiegi [niezweryfikowane]) jest
w pozycji o wyborze kontekstu przez selektor (sekcja o harnessie wyżej); jakość decyzji zależy od świeżości
dowodów, a każdy dowód ma link i datę.

## Własność harnessu, oszczędne skille i SLO agenta (artykuły „Harness Ownership: Skills, Hooks, Instruction Files, And The Harness-Team Anti-Pattern”, J. Wąsowski, 2026-10-17; „His entire AI skills library loads in 660 tokens”, S. S., 2026-10-09; „I Built 15 SLOs for an AI Agent”, T. Deshpande, 2026-09-09; „SDD Factory OKRs”, J. Wąsowski, 2026-10-21; zapisane 2026-10-29)
Przegląd 2026-10-29: `core-skill-authoring` ma `disable-model-invocation` dla skilli procesowych; pozycja o OTel
GenAI jest w sekcji o protokołach. Liczby z artykułów (wielkość biblioteki skilli, badanie ETH Zurich o plikach
kontekstu +20% kosztu) [niezweryfikowane].
- [x] **`core-agent-instructions` / `core-skill-authoring`, mapa własności artefaktów harnessu w projekcie** (zrobione 2026-11-01: `core-agent-instructions` §2; liczenie użyć skilli z logów — osobno)**:**
  artefakt (plik instrukcji, skill, hook, kontrakt narzędzia, polityka uprawnień, sensor) → właściciel z domeny,
  której dotyczy (nie centralny „zespół harnessu”), test w CI, cykl przeglądu, kto zmienia kontrakt; skill nieużywany
  60–90 dni oznaczany do wycofania (fabryka ma logi hooków — można liczyć użycia); reguły dopisywane jak zapadka:
  tylko z prawdziwej porażki, po przeglądzie. Miara: odsetek artefaktów bez właściciela i bez testu.
- [x] **`core-skill-authoring`, mniej tokenów w skillach** (zrobione 2026-11-01: `references/skill-review.md` §„Odchudzanie”; pomiar kosztu opisów 209 skilli — osobno)**:** test „no-op” zdanie po zdaniu (czy zmienia zachowanie
  względem domyślnego — jeśli nie, usuń całe zdanie); instrukcje pozytywne zamiast zakazów (zakaz wnosi zakazane
  do kontekstu); słowa-pojęcia, które model już zna (np. zapachy kodu Fowlera po nazwie), zamiast definicji;
  skill-router wywoływany ręcznie, który dopiero ładuje cięższy. Dla fabryki: zmierzyć łączny koszt opisów
  wszystkich skilli widocznych w sesji (209 skilli) i rozważyć `disable-model-invocation` dla rzadko
  wywoływanych automatycznie; specyfikacja bez ścieżek plików i fragmentów kodu (starzeją się, agent i tak by
  za nimi szedł). Zmiany skilli — przez scenariusze ewaluacji i bramkę, płatny pomiar za zgodą.
- [x] **`ops-observability` / `ai-agents`, SLO agenta** (zrobione 2026-10-31: `ops-observability`, „Agent AI i dochodzenie po incydencie”)**:** z OTel „za darmo” tylko dostępność i opóźnienie wywołania;
  resztę dodaje aplikacja: stan końcowy zadania (w tym „słusznie odmówił” i „przekazał człowiekowi” — ani sukces,
  ani porażka), klasa zadania, liczba kroków, interwencja człowieka, wersja przy odczycie i zapisie pamięci roboczej
  (wykrywanie nieaktualnego odczytu). **Powód odrzucenia narzędzia zwraca serwer narzędzia** (zła struktura / zła
  wartość / błąd wewnętrzny): awaria narzędzia → alarm do właściciela zależności, błędne wywołanie przez agenta →
  zgłoszenie dla zespołu agenta. SLO liczone z jednego stabilnego rekordu emitowanego przez aplikację na koniec
  zadania, nie z backendu śladów (zmienia nazwy spanów i typy atrybutów). Nazwy atrybutów wg konwencji GenAI tam,
  gdzie istnieją (repo `semantic-conventions-genai` — sprawdzić wersję przed wpisaniem).

Bez wpisu: „Build a Second Brain in 15 Minutes” (R. Brasil Monteiro, 2026-07-19 — COG: braindump, dzienny skrót,
podział framework / treść przy aktualizacji, workery na tańszym modelu; pokryte przez pozycje o wiki i
`core-cost-control`) oraz powtórzony „Spec-Driven Development in Scrum and Kanban” (wpis wyżej).

## Bramka LLM, anatomia harnessu i reguły w kodzie (artykuły „Design an LLM Gateway: Routing, Fallbacks, and Token Cost Control”, A. Kumar, 2026-10-22; „The Anatomy of an AI Agent Harness”, D. Yadav, 2026-10-01; „The Complete Guide to Agent Harnesses (With Code)”, P. Perrone, 2026-08-21; zapisane 2026-10-29)
Sprawdzone 2026-10-29 u źródła: Anthropic Engineering „Effective harnesses for long-running agents” (2025-11-26 —
agent inicjujący środowisko + agent kodujący robiący przyrost w każdej sesji i zostawiający artefakty dla
następnej; kompaktowanie nie wystarcza: agent próbuje zrobić wszystko naraz i ogłasza koniec za wcześnie);
„Harness design for long-running application development” (2026-03-24 — planner, generator i ewaluator z kryteriami
zamieniającymi ocenę gustu na stopniowalne punkty); cennik cache (platform.claude.com, prompt-caching: odczyt
cache ok. 0,05–0,1 ceny wejścia zależnie od modelu, czas życia liczony od początku żądania). Liczby z preprintów
cytowanych przez Perrone (40× tokenów na rozwiązane zadanie, różnice pass rate 0–8 pkt) — jak w pozycji o
„harness: wynik czy koszt” [niezweryfikowane].
- [x] **`arch-ai-solutions`, bramka (gateway) przed modelami — uzupełnienia** (zrobione 2026-11-01: `arch-ai-solutions/references/gate-and-reliability.md` §1–2)**:** trasy jawne per funkcja
  (`funkcja → model, zapasowy`) z wyłącznikiem, zamiast „sprytnego” automatycznego routingu; **fallback tylko do
  modeli spełniających te same ograniczenia** (dane z modelu własnego nie mogą po cichu pójść do zewnętrznego
  dostawcy, słabszy model to cicha utrata jakości) i fallback produktowy („pokaż dane bez streszczenia AI”);
  limity w tokenach, nie tylko w żądaniach — rezerwacja `max_tokens` z góry i zwrot różnicy po odpowiedzi; budżet
  osobno od limitu: przy 80% alert, przy 100% polityka wybrana z góry przez właściciela (blokada / tańsza trasa /
  zgoda z alertem); strumieniowanie: rozliczenie po końcu strumienia, anulowanie wywołania u dostawcy po rozłączeniu
  klienta, odpowiedź przerwana w połowie oznaczona jako częściowa, bez cichego zszywania dwóch; logowanie treści
  promptów tylko po włączeniu dla trasy, z retencją; miara „odsetek fallbacków” jako wczesne ostrzeżenie.
- [x] **`ai-agents` / `core-async-delegation`, długie przebiegi w wielu oknach kontekstu** (zrobione 2026-10-31: `ai-agents/references/executors-and-gates.md` §3) (Anthropic, wyżej):
  pierwsza sesja przygotowuje środowisko i listę zadań, każda kolejna robi jeden przyrost i zostawia artefakty
  przekazania (postęp, stan testów); oddzielny ewaluator z jawnymi kryteriami; reguła końca sprawdzana przez test
  lub ewaluator, nie przez deklarację agenta. Recenzent tylko do odczytu (raport, nie poprawka — inaczej znika
  sygnał), narzędzia nieodwracalne z `dry_run` domyślnie włączonym; ścieżka rozwiązywana **przed** porównaniem
  z listą dozwolonych (lista zakazów łapie tylko przewidziane zapisy; `work/../secrets` przechodzi); reguła
  z promptu przeniesiona do hooka, gdy ma działać zawsze. Część jest już w `core-agent-security` — dopisać
  przykłady i test „lista zakazów vs `..`”.

## Wyrocznia poza kodem, raport „całe zadanie zaliczone” i wznowienie z punktu kontrolnego (artykuły „Harness Engineering for AI Coding Agents, From Prompts to Production-Ready Systems”, T. Ramchandani, 2026-10-16; „Harness Beyond Code: What Transfers from Coding Agents to Law, Support, and Research”, J. Wąsowski, 2026-10-20; zapisane 2026-10-30)
Przegląd 2026-10-30: przewodniki i czujniki, ograniczona pętla naprawy z eskalacją, uprawnienia w środowisku zamiast
w promptach, krótki punkt wejścia z mapą repozytorium i holdout dla zmian harnessu są już w skillach i wcześniejszych
pozycjach TODO. Eksperyment N. Jaina (model czołowy 10/10 z harnessem i bez, tańszy 3/10 → 10/10 z harnessem, mała
próba) wspiera pozycję „Skille fabryki: wynik czy tylko koszt”. Liczby z artykułów (CoreCraft v5 30,80% przy pełnej
rubryce, ClawBench do 33,3% wobec 65–75% w piaskownicach, Harvey 40,8 → 87,7% na 12 zadaniach, LAB 7–25% całych zadań
przy ponad 90% kryteriów, szum infrastruktury 6 pp w Terminal-Bench 2.0) [niezweryfikowane]. Braki:
- [x] **`project_record.py wip`, sprawdzenie zgodności przy wznowieniu** (zrobione 2026-10-30: `repo_drift` w hooku sesji, 3 testy w `test_project_record.py`): punkt kontrolny zapisuje gałąź i ostatni
  commit (`snapshot`), ale przy wznowieniu nic ich nie porównuje z bieżącym stanem. Przy wypisaniu aktywnego punktu
  (start sesji) porównać zapisaną gałąź i commit z `HEAD`: rozjazd (inna gałąź, commit nieznany w historii, nowe
  commity spoza punktu) → ostrzeżenie „stan repo różni się od punktu kontrolnego, przed kontynuacją uruchom testy
  i porównaj kroki z dowodem”. Streszczenie rozmowy nie jest mechanizmem odtwarzania stanu. Najpierw test.
- [x] **`ai-evals`, raport i dobór wyroczni** (zrobione 2026-10-31: `ai-evals/references/measurement-pitfalls.md` §10)**:** (1) główny sygnał gotowości to odsetek zadań zaliczonych w całości
  (wszystkie kryteria rubryki), średnia spełnionych kryteriów i rozrzut między powtórzeniami tylko obok, jako
  diagnostyka — raport wskazujący 8 z 10 ryzyk nie jest „w 80% użyteczny”; średnia może być nagrodą w treningu, nie
  miarą w raporcie. (2) Wyrocznię zastępczą dobierać do odwracalności działania: asercja deterministyczna w pętli
  (np. stan bazy po rozmowie, ostatnie żądanie zgodne ze schematem), rubryka i weryfikator faktów pośrodku, człowiek
  przed działaniem nieodwracalnym; przy pętli samodoskonalenia harnessu zamrożony zbiór testowy i wersjonowany
  sędzia, inaczej rosnący wynik to dopasowanie do rubryki. (3) Przy porównaniu harnessów lub modeli te same zasoby
  wykonania (CPU, pamięć, limity czasu) i powtórzenia — różnica wyniku może pochodzić z infrastruktury.
- [x] **`core-source-research` / `core-grounding`, liczba z „odciskiem”** (zrobione 2026-11-01: `core-source-research` §4)**:** cytowana liczba z benchmarku lub badania
  niesie identyfikator i wersję źródła (np. wersja preprintu — zaokrąglone zdania w streszczeniu zmieniają się między
  wersjami, tabela nie), nazwę metryki i status pomiaru: deklaracja firmy o własnym produkcie / pomiar twórcy
  benchmarku / pomiar niezależny. Wynik z piaskownicy nie przenosi się automatycznie na środowisko produkcyjne.
- [x] **`qa-test-design`, brzeg stronicowania i izolacji** (zrobione 2026-10-31: tabela technik)**:** heurystyka „liczba wyników równa limitowi strony → test
  musi sprawdzić następną stronę”; dane testowe z większą liczbą rekordów niż jedna strona, z rekordami drugiego
  najemcy i przypadkiem odmowy dostępu; oczekiwany zbiór wyliczony z niezależnie zasianych danych, nie z
  implementacji (asercja na całym zbiorze, nie na statusie i pierwszym wierszu).

Bez wpisu: powtórzony „I Built 15 SLOs for an AI Agent” (T. Deshpande — pozycja o SLO agenta w sekcji „Własność
harnessu…”).

## Kokpit fabryki: wskaźniki wyprzedzające i opóźnione (artykuły „SDD Factory Dashboard: The Leading and Lagging Indicators That Actually Matter”, J. Wąsowski, 2026-08-12; „Building an AI Agent from Scratch: No Magic, Just a Deterministic Loop”, S. Nes, 2026-05-04; zapisane 2026-10-30)
Przegląd 2026-10-30: `eng-continuous-delivery` ma cztery metryki DORA, a pozycja „miary autonomii” wyżej ma już
zastrzeżenie o Goodharcie i parę „miara aktywności + miara wyniku”. Liczby z artykułu (Faros +91% czasu przeglądu,
METR −19%, Peng +55,8%, DORA 2024: klaster „high” z gorszym CFR niż „medium”, rework rate dodany przez DORA w 2024)
[niezweryfikowane]. Braki:
- [x] **`eng-continuous-delivery` / `core-delivery-lifecycle`, kokpit zdrowia fabryki** (zrobione 2026-11-01: `eng-continuous-delivery`, „Kokpit zdrowia dostarczania”)**:**
  - wskaźniki opóźnione rozliczają, czyli wskaźnik nieudanych zmian (CFR), odsetek defektów u użytkownika, odsetek
    przeróbek (rework rate, piąta miara DORA — sprawdzić w raporcie) i realizacja zwrotu z inwestycji;
  - wskaźnik wyprzedzający trafia na kokpit tylko wtedy, gdy przewiduje któryś opóźniony: kolejka PR czekających na
    przegląd człowieka (liczba, wiek najstarszego) → CFR; dryf specyfikacji (kod odbiega od spec) → defekty u
    użytkownika; czas od ostatniej weryfikacji szablonu lub reguły z rzeczywistością → przeróbki;
  - każda miara prędkości w parze z miarą jakości, która ruszy się, gdy ktoś zacznie grać pierwszą;
  - mierzy się system, nigdy osobę;
  - trzy widoki z różną częstotliwością: zarząd kwartalnie (opóźnione i zwrot z inwestycji), kierownictwo miesięcznie
    (trendy obu rodzajów), lider zespołu co tydzień (pełny zestaw wyprzedzający z parami);
  - start od czterech liczb: kolejka przeglądu, dryf specyfikacji, CFR, defekty u użytkownika. Definicje „defektu”
    i „ucieczki” ustalić w organizacji przed pierwszym pomiarem.

Bez wpisu: „Building an AI Agent from Scratch” (S. Nes — pętla ReAct w 50 liniach, Ollama, MCP; pokryte przez
`ai-agents` i `eng-llm-features`). Repozytorium `sergenes/mini_agent` sprawdzone (README z listą części serii).
Z obserwacji autora: model bez wsparcia wywołań funkcji opisuje wywołania prozą, a pętla kończy się od razu bez
błędu. Pustą listę wywołań przy zadaniu wymagającym narzędzi warto traktować jako podejrzaną.

## Projekt systemu AI w produkcji: luki po przeglądzie (artykuły „AI System Design: A Practical Guide to Production AI”, P. Kashyap, 2026-10-17; „Harness Engineering vs. Loop Engineering vs. Graph Engineering in Agentic AI”, M. Ranjan, 2026-10; grafika „Layers of AI Agent Engineering”; zapisane 2026-10-30)
Przegląd 2026-10-30: `arch-ai-solutions` ma już pojemność z prawa Little'a, szablon kosztu tokenów z cache i bez,
budżet opóźnienia z czasem do pierwszego tokenu, cache wyników tylko dla odpowiedzi niezależnych od użytkownika
(klucz z wersją promptu, modelu i najemcą), fallback sprawdzany ewaluacją oraz idempotencję akcji. `ai-rag` ma
reindeksację przyrostową i usuwanie jako osobną ścieżkę. Warstwy prompt → kontekst → harness → pętla → graf oraz
zasada „najpierw jeden agent z mocnym harnessem” są w `ai-agents` i wcześniejszych pozycjach. Braki:
- [x] **`arch-ai-solutions` / `eng-llm-features`, reguły niezawodności i wycofania** (zrobione 2026-11-01: `arch-ai-solutions/references/gate-and-reliability.md` §2–3)**:**
  - **Ponowienia w jednej warstwie:** wspólny budżet czasu i prób na całe żądanie. Gdy każda warstwa (klient,
    bramka, orkiestrator, SDK) ponawia osobno, jedno żądanie mnoży wywołania dostawcy i pogłębia awarię.
  - **Strumień:** gdy klient się rozłączy albo anuluje, przerwać generowanie u dostawcy, bo tokeny nadal kosztują.
    Strumień przerwany przez błąd dostawcy kończy się jawnym zdarzeniem błędu, nie wygląda jak pełna odpowiedź.
    Komentarz typu „sprawdzam zgłoszenie” to nie wynik — wynik pokazuje się dopiero po odpowiedzi usługi.
  - **Unieważnianie cache wyników:** klucz albo metadane zawierają wersję dokumentów źródłowych. Zmiana lub
    usunięcie dokumentu unieważnia odpowiedzi z cache, które na nim powstały, tak samo jak fragmenty w indeksie.
  - Miary jakości cache: odsetek trafień, zaoszczędzony koszt i opóźnienie, incydenty nieaktualnej odpowiedzi.
  - **Wycofanie zmiany AI obejmuje całą konfigurację** (`ai-mlops`, LLMOps): prompt, model, definicje narzędzi,
    ustawienia wyszukiwania i rankingu oraz **wersję indeksu**. Bez migawki indeksu powrót do poprzedniego promptu
    nie przywraca poprzedniego zachowania. Warunki wycofania ustala się przed wydaniem: błędy, wynik ewaluacji,
    koszt, błędne akcje narzędzi.

Bez wpisu: „dług zrozumienia” z artykułu Ranjana (zespół rozumie coraz mniej kodu pisanego przez agentów). Pokrywa
go pozycja „`core-delivery-lifecycle`, osąd nie może uciec do kroków” (refinement nieskończony, dopóki nikt nie umie
wyjaśnić, jak praca zostanie zrobiona) oraz przegląd człowieka w `core-async-delegation`.

## Wielu wykonawców nad jednym zadaniem: własność, wersje i kontrakt dowodów (artykuły „Agent Harness Engineering: The Runtime Architecture Behind Reliable AI Agents”, S. J. Kar, 2026-08-14; „Seven Agent Design Patterns — and How to Combine Them”, X. Wang, 2026-10; zapisane 2026-10-30)
Przegląd 2026-10-30: następujące elementy są już w `ai-agents` i w pozycjach TODO:
- „kontekst to nie stan” i odtwarzanie kontekstu ze stanu;
- zapadka „porażka → brakująca kontrola”;
- weryfikacja zamiast deklaracji agenta;
- egzekwowanie na granicy zamiast instrukcji;
- trwałe wykonanie (sekcja „Trwałe wykonanie agentów”);
- wzorce workflow i agentów;
- przejścia grafu z obowiązkową weryfikacją.

Artykułów i obrazów z Medium nie dało się otworzyć (proxy 403), podobnie docs.temporal.io, docs.langchain.com
i agentskills.io. Braki:
- [x] **`ai-agents`, praca wielu wykonawców nad wspólnym stanem** (zrobione 2026-10-31: `ai-agents/references/executors-and-gates.md` §1)**:**
  - **Dzierżawa zadania z wygaśnięciem i biciem serca.** Wykonawca, który zniknął, traci zadanie, a inny wznawia
    je z trwałego stanu.
  - **Zakończenie i zapis sprawdzają bieżącego właściciela i wersję rekordu.** Spóźniony wykonawca nie nadpisze
    nowszego wyniku. Zapis całego rekordu ze starej kopii to utracona aktualizacja. Przed zapisem trzeba sprawdzić
    wersję, użyć transakcji albo zlecić scalanie jednemu koordynatorowi.
  - **Trzy różne operacje:** ponowienie (ta sama operacja jeszcze raz), wznowienie (z zapisanego stanu; najpierw
    sprawdzić, czy wersje dokumentów i konfiguracji nadal pasują do przyjętej pracy) i kompensacja (osobna operacja
    biznesowa, która też może zawieść). Żadna z nich nie jest uniwersalnym „cofnij”.
  - **Ukończenie jako predykat systemu,** nie zdanie modelu: wymagania spełnione, walidacja przeszła, artefakty są,
    polityki sprawdzone. Jawne wyjścia inne niż sukces: wyczerpany budżet, brak nowych dowodów, brak wymagania do
    wyjaśnienia. Wynik częściowy oznaczony jako „szkic z zastrzeżeniami”, nie jako zatwierdzony.
  - **Miara odzyskiwania:** ile ukończonej pracy wykonało się ponownie, czy zapisy zewnętrzne się zdublowały, czy
    przyjęte dowody nie zniknęły.
- [x] **`core-source-research` / agent `researcher`, kontrakt dowodu przy równoległych badaczach** (zrobione 2026-11-01: `core-source-research` §4; zmiana promptu agenta `researcher` w `factory/` — za zgodą)**:**
  - **Rekord dowodu:** id pytania, teza, źródło, wersja dokumentu, warunki ograniczające, otwarte kwestie.
  - **Brak informacji pozostaje brakiem,** nie zamienia się w odpowiedź przeczącą.
  - **Duplikat z ponowienia** nie liczy się jako niezależne potwierdzenie.
  - **Sprzeczne ustalenia zostają widoczne** i wracają do sprawdzenia, zamiast wygrywać tym, które brzmi
    pewniej.
  - **Recenzent dostaje dowody źródłowe i kryteria,** nie tylko gotową prozę. Zgoda drugiego agenta na tych samych
    źródłach nie jest niezależnym dowodem.

## Świadek każdego kroku: reguły według modalności, ocena klasyfikatorów decyzji i narzędzi kontekstu (artykuł „Grounded Reasoning For Agents: Ontologies, Decision Models And Every Way An Agent Can Reason”, A. Alcaraz, 2026-10-20; zapisane 2026-10-30)
Przegląd 2026-10-30. Co już jest:
- bramka zdefiniowana skutkami i próg jako polityka (sekcja „Bramka przed narzędziem”);
- kaskada modeli w `core-cost-control` i `arch-ai-solutions`;
- graf i ontologia do wyszukiwania i proweniencji w `ai-rag`;
- rola a typ (strona, rola, faza) w `ddd-archetypes`.

Sprawdzone 2026-10-30 w źródłach:
- `bcallender/agent-context-workshop` (README): agent z grafem i agent z grepem prawie remisują w pojedynczym
  przebiegu (21/30 vs 19/30). Graf wygrywa powtarzalnością (dobrze w każdym przebiegu: 19/30 vs 11/30), zużywa ok.
  3× mniej tokenów wejścia, a odsetek użycia grafu rośnie z 34% do 72% po podpowiedzi.
- `dogwood-policy/dogwood` (README i przewodnik `04-temporal-expressions.md`): składnia z Cedar plus warunki czasowe
  `formerly`, `previous` i `since` z obowiązkowym oknem. Okno ograniczone przez `max_window`, domyślnie 24h.
  Interpreter referencyjny, nie do produkcji.

Niedostępne przez proxy (403): arXiv, typesafe.ai, randalolson.com, docs.cedarpolicy.com, w3.org, huggingface.co,
hanxiao.io. Pozostałe liczby z artykułu [niezweryfikowane], w tym:
- OntoMetric: 83,3% → 19,44% błędów;
- EvoOntology: 64,6 / 69,5 / 81,8;
- JevAgentHarness: −19,0 pkt bez progu;
- kaskada Sena: 88,4% automatycznie.

Braki:
- [x] **`ai-agents` / `core-agent-security`, „kto jest świadkiem tego kroku?”** (zrobione 2026-10-31: `ai-agents/references/executors-and-gates.md` §2; reguły hooków jako predykaty nad logiem — zmiana hooków tylko na prośbę)**:**
  - Przegląd kroków agenta: krok, którego jedynym sprawdzeniem jest dalszy tekst tego samego modelu, jest przyjęty
    na wiarę.
  - Reguła trafia w miejsce zależne od modalności:
    - o stanie → schemat lub kształt sprawdzany przy zapisie;
    - o jednej akcji → polityka per żądanie (domyślnie odmowa, `forbid` wygrywa z `permit`);
    - o sekwencji akcji → reguła czasowa nad dziennikiem zdarzeń („zatwierdzenie w ciągu 1h przed sprzedażą”).
  - Werdykt bramki (wykonaj / odmów / eskaluj) ma być powtarzalny dla tego samego zapisanego stanu. Reguła tylko
    w prompcie albo werdykt zwracany wyłącznie agentowi niczego nie gwarantuje.
  - Log zapisuje, który świadek sprawdził krok.
  - Dla fabryki: hook `tdd_guard` jest właśnie regułą czasową („edycja kodu dozwolona, jeśli od ostatniej zmiany
    testu był czerwony przebieg”). Warto zapisać reguły hooków jako predykaty nad logiem hooków i testować je
    odtworzeniem zapisanych śladów (jak `dogwood replay`). Zmiana hooków tylko na prośbę człowieka.
- [ ] **`ai-evals` / `ai-fine-tuning`, ocena klasyfikatora decyzji** (część w `ai-evals` zrobione 2026-10-31: `ai-evals/references/measurement-pitfalls.md` §11; kod w `factory/jev_calibration.py` zrobiony 2026-11-01 — `fit_threshold` dla trasowania, `fit_band` dla sędziego, `--shuffle` test kolejności opcji, testy 15/15; zostaje płatny pomiar, gdy w środowisku będzie `TYPESAFE_API_KEY` — zmiana w `factory/` za zgodą człowieka) (LLM jako klasyfikator albo model decyzyjny):
  - Test kolejności i nazw opcji: przetasować i przemianować, policzyć zmiany odpowiedzi.
  - Próg dopasowany na własnych etykietach **osobno dla każdego punktu decyzji**, nigdy domyślne 0,5.
  - Kaskada mierzona względem samego drogiego modelu.
  - Szczególna ostrożność przy krokach nieodwracalnych: pewny błędny wybór na takim kroku to typowa porażka.
  - Przed przypisaniem zysku dostrajaniu — kontrola na zamrożonym modelu bazowym tym samym promptem, a nie od
    losowo zainicjalizowanej głowy.
  - Zbiór testowy rozdzielony po przypadku (ten sam dokument nie trafia na obie strony), najlepiej zamknięty.
    Publiczny benchmark się nasyca.
  - Zmiana słów w definicjach opcji to zmiana modelu: ponowny test.
  - Licencję sprawdzać w pliku wag, modelu bazowym i danych, nie na odznace repozytorium.
  - W fabryce dotyczy to `factory/jev_calibration.py`: podpowiedź skilli i sędzia z Jev, pas niepewności
    stały 0,30–0,70. Do dodania: próg dopasowany osobno dla trasowania i dla sędziego oraz test przetasowania
    kolejności opcji. Pomiar płatny, więc tylko za zgodą człowieka.
- [x] **`eng-codebase-mapping` / `ai-rag`, ocena narzędzi kontekstu (graf, indeks, mapa kodu)** (zrobione 2026-11-01: `eng-codebase-mapping`)**:**
  - Obok trafności w jednym przebiegu: powtarzalność (dobrze w każdym z N przebiegów), tokeny wejścia oraz **odsetek
    użycia** — czy agent w ogóle sięga po narzędzie.
  - Fabryka ma już `hint_report.py` („podpowiedziany, a nieużyty”), więc da się to policzyć dla skilli i map.
  - Warstwę wiedzy podawać przez narzędzia zwracające mały podgraf ze źródłami, nie wklejać do promptu (EvoOntology:
    wklejona warstwa gorsza niż jej brak [niezweryfikowane]).

## Pamięć automatyczna, która utrwala błąd (artykuły „Building the Harness Around AI Coding Tools” / „A Blueprint for Agentic Coding Tools”, I. Silfverskiöld, 2026-10; „Harness Engineering, Explained by Building One: An AI Agent Test Bench That Runs in Your Browser”, V. Mysore, 2026-10; zapisane 2026-10-30)
Przegląd 2026-10-30: fabryka ma już większość opisanych elementów:
- uprawnienia, piaskownicę i reguły deny (`core-agent-security`);
- krótki plik instrukcji jako indeks i reguły z `paths` (`core-agent-instructions`, w tym limity pamięci
  automatycznej 200 linii / 25 KB);
- scenariusze `trigger` i `no-trigger` z sąsiadem i porównanie ze skillem i bez niego (`core-skill-authoring`,
  `run_skill_evals.py`);
- deterministyczny oceniacz pokryty testami bez modelu (`test_skill_evals.py`);
- audyt obcych skilli (`skill_audit.py`);
- pozycje o `/goal` i `omitClaudeMd` w TODO;
- licznik podpowiedzi nieużytych (`hint_report.py`).

Wnioski z badań przytoczonych w artykule wspierają istniejącą pozycję „Skille fabryki: wynik czy tylko koszt”:
- SWE-Skills-Bench: 39 z 49 skilli bez zmiany wyniku, 3 szkodliwe;
- planowanie pomaga słabszym modelom, a mocniejszym głównie obniża koszt.

Liczby [niezweryfikowane]; artykułu z Medium nie dało się otworzyć (403). Brak:
- [x] **`core-agent-instructions` / `core-agent-retro`, przegląd pamięci automatycznej** (zrobione 2026-11-01: `core-agent-retro`, „Gdzie trafia zmiana”; skrypt przeglądu — osobno)**:** notatka w `MEMORY.md` i jej
  plikach pomocniczych może być błędna i wracać w każdej sesji. Poprawka człowieka bywa wtedy dopisana obok starej
  notatki zamiast ją zastąpić. Przegląd w retro:
  - **mechanicznie** (skrypt): odwołania do plików i ścieżek, których już nie ma; wiek pliku; rozmiar względem
    limitu ładowania;
  - **z człowiekiem**: sprzeczności z `docs/` i ADR. Poprawka zastępuje starą notatkę. Ustalenie, które ma
    obowiązywać zespół, przenieść do pliku instrukcji albo ADR; nie zostawiać go tylko w pamięci maszyny.

## Linki, których nie udało się otworzyć (przeglądy artykułów od 2026-10-29)
Host niedostępny z sieci sesji (`ENOTFOUND` albo proxy 403). Fakty zależne od nich są w pozycjach wyżej oznaczone
[niezweryfikowane]; po dodaniu hostów do dozwolonych w ustawieniach sieci środowiska można je sprawdzić.
- https://alignment.openai.com/misalignment-reports/an-agent-used-dns-to-reach-an-external-chatbot/ (sekcja o piaskownicy)
- https://metr.org/blog/2026-08-26-openai-hugging-face-incident-investigation/ (sekcja o piaskownicy)
- https://docs.icepanel.io/integrations/mcp-server (model architektury jako jedno źródło widoków)
- https://agentskills.io/ (specyfikacja Agent Skills — sprawdzona zamiast tego w repo `agentskills/agentskills` na GitHubie)
- https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/ (OWASP Top 10 for LLM 2026, sekcja o wzorcach bezpieczeństwa)
- https://docs.github.com/en/copilot/concepts/agents/copilot-memory (pamięć Copilota, artykuł A. Kokane o ADR)
- https://docs.langchain.com/oss/python/langgraph/durable-execution (tryby trwałości LangGraph, w tym domyślny `async`)
- https://www.inngest.com/docs/learn/how-functions-are-executed (sprawdzone zamiast tego w repo `inngest/website`)
- https://docs.dbos.dev/architecture (sprawdzone zamiast tego w repo `dbos-inc/dbos-docs`)
- https://docs.temporal.io/workflow-definition (determinizm kodu workflow w Temporal)
- https://www.pragmaticcoders.com/resources/product-health-checklist (Product Health Checklist — prawdopodobnie za formularzem; do oceny po wklejeniu treści)
- https://www.langchain.com/blog/the-anatomy-of-an-agent-harness (definicja harnessu, LangChain)
- https://research.trychroma.com/context-rot (badanie „context rot”, Chroma)
- https://prachub.com/resources/llm-gateway-system-design-interview-routing-rate-limits-fallbacks-and-cost-controls (bramka LLM)
- https://github.com/paoloap-py/agent-harness-guide (repo z przykładami warstw harnessu — 403 przez proxy GitHub dla tego repo)
- https://medium.com/@marvelous_catawba_otter_200/seven-agent-design-patterns-and-how-to-combine-them-d2168c875722 (obrazy artykułu; Medium 403)
- https://docs.temporal.io/activities, https://docs.langchain.com/oss/python/langgraph/persistence (proxy 403, 2026-10-30)
- arxiv.org (2610.21412, 2609.26550, 2610.18773, 2609.15779, 2512.01289, 2610.17205), docs.typesafe.ai, randalolson.com, docs.cedarpolicy.com, w3.org/TR/shacl, huggingface.co, hanxiao.io (artykuł A. Alcaraza; proxy 403, 2026-10-30)
- https://medium.com/data-science-collective/a-blueprint-for-agentic-coding-tools-c1e0e2ed797b (pełny artykuł I. Silfverskiöld; Medium 403, 2026-10-30)
Artykułów na medium.com i innych płatnych platformach nie pobierano (próba 2026-10-30: 403) — treść pochodziła z wklejek.
- Z przeglądu 2026-11-01 (pozycje „sprawdzenie w sieci”; fakty wzięte z repozytoriów na GitHubie albo z wyszukiwarki):
  - https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/ i https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/ (Agentic — **PDF przekazany 2026-11-01**, naniesione) (listy 2026; użyte repo GenAI-Security-Project/GenAI-LLM-Top10)
  - RFC 8705, 9449, 8693 — **przekazane przez człowieka 2026-11-01** (PDF); naniesione w `sec-zero-trust-identity`
  - https://docs.cloud.google.com/iam/docs/agent-identity-overview — **przekazane przez człowieka 2026-11-01**; naniesione
  - https://modelcontextprotocol.io/specification/2026-07-28/changelog — **przekazane przez człowieka 2026-11-01**, zgodne z repo; dopisane szczegóły (kody błędów, `inputRequests`, `iss`)
  - https://eur-lex.europa.eu/legal-content/PL/TXT/HTML/?uri=CELEX:32024R1689 (art. 50 ust. 2 i 7, art. 113 AI Act; data stosowania art. 50 — 2026-08-02 — potwierdzona już stroną Komisji)
  - https://digital-strategy.ec.europa.eu/policies/code-practice-ai-generated-content — **przekazane przez człowieka 2026-11-01** (strona o kodeksie; naniesione w `ai-governance-compliance/references/technical-tagging.md`). Zostaje: PDF samego kodeksu (sekcja 1, warstwy znakowania) i wytyczne do art. 50 (czy przyjęte, termin 2026-12-02)
  - https://a2a-protocol.org/latest/specification/ — **przekazane przez człowieka 2026-11-01**, naniesione; https://agentclientprotocol.com/ — **przekazane 2026-11-01**, naniesione;, https://opentelemetry.io/docs/specs/semconv/gen-ai/ (użyte repozytoria projektów)
  - arXiv 2301.10226 (Kirchenbauer i in.) — **przekazane przez człowieka 2026-11-01** jako PDF v4; naniesione (25 tokenów, z = 4, entropia, katalog ataków)
