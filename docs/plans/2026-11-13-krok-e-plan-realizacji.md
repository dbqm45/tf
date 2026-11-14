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
| E6 | cięcia pdi w nowym układzie | przebieg cięcia dostaje katalog zadania, specyfikację z wiersza cięcia i zamiaru zmiany, dowody, ślad i flagę z planu wydania; raport cięcia zostaje tam, gdzie oczekuje go pdi | plan szczegółowy: `docs/plans/2026-11-14-krok-e6-ciecia-pdi-plan.md` (klucz zadania cięcia `<CHG>-<TSK>`, kawałki E6a–E6c) | L |

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

**Odstępstwa od planu w trakcie (2026-11-14):** linia źródła w `ticket.md` psuła kontrolę kształtu historyjki
w pack-it (aktor rozpoznawany tylko na początku opisu) — poprawione w `requirements_lint.py` z testem; `tf onboard`
uzupełnia sekcję flag w karcie operacyjnej, która już istnieje (kartę może wcześniej założyć zapis trackera);
treść zgłoszenia pobraną z trackera pętla dopisuje do `ticket.md` po `start`, a nie przez plik pośredni, żeby nie
zostawiać nieśledzonych plików przed startem.

**Poza E1:** waga (E2), tryb `--plan` i lista zatrzymań (E3) — `resolve` tylko przekazuje opcję dalej; nowy układ
cięć (E6); zapis do trackera.

**SKILL.md pętli skrócony** (prośba właściciela, 2026-11-14): z 24 749 do 14 859 znaków, poniżej limitu 15 000
z `build.py check` (po kompaktowaniu Claude Code przywraca tylko początek dłuższego skilla). Szczegóły są w czterech
plikach `core/skills/tf/references/`: `wejscie.md` (rodzaje wejścia, tracker), `ciecia-pdi.md` (przebieg cięcia
i poprawki z pętli PR), `flaga-funkcji.md`, `bezpieczenstwo.md` (karencja wersji, skan). `intake.py` przy cięciu
i prompt poprawek `pr_loop.py` wskazują `ciecia-pdi.md` wprost. Test `T-20` pilnuje limitu, `T-21` — że każdy plik
jest wymieniony w SKILL.md. Kolejne kawałki (E2–E4) dopisują szczegóły do `references/`, nie do SKILL.md.

## E2 — plan szczegółowy (2026-11-14, przed kodem)

**Pliki i kolejność** (test przed kodem):

1. `core/tests/test_task_weight.py` → `core/factory/task_weight.py` (reguły propozycji, bez modelu) i polecenie
   `tf task weight <KEY> [--apply | --set <waga>] [--by <kto>] [--reason "…"] [--json]` w `task_state.py`.
2. Bramki w `task_state.py stage`: waga `pelna` — etap `realizacja` dopiero po zatwierdzeniu `plan.md` przez człowieka
   (`tf task approve <KEY> plan.md --by human:<id>`); waga `lekka` — plan ma najwyżej jeden kawałek.
3. `core/tests/test_run_state.py` → `run_state.py weight <katalog>` (pętla stosuje propozycję i drukuje skutki);
   przy wadze `lekka` etap `plan` przebiegu nie wymaga `spec.md`.
4. `core/tests/test_tf_skill.py` → jedna linia w SKILL.md i `references/waga.md`; przewodniki, `PUBLIC_API.md`.

**Reguły propozycji** (ostrożne: wątpliwość → wyższa waga; każda propozycja ma powód zwykłym zdaniem):

| Waga | Kiedy |
|---|---|
| `pelna` | treść zgłoszenia mówi o logowaniu, hasłach, uprawnieniach, płatnościach, fakturach, migracji lub schemacie bazy, danych osobowych, sekretach albo wdrożeniu; albo plan wymienia ścieżkę z kategorii wysokiego ryzyka triażu (`autonomy.triage.high`: auth, płatności, schemat, wdrożenie) |
| `lekka` | treść mówi o literówce, nazwie, komentarzu, dokumentacji albo tekście; nie ma kryteriów akceptacji; jest krótka; plan (jeśli jest) ma jeden kawałek i najwyżej 2 pliki |
| `zwykla` | wszystko inne |

**Kto zmienia wagę:** pierwszy przydział robi fabryka (`--apply`). Potem podnieść może każdy; obniżenie wymaga
`--by human:<id>` i powodu. `--apply` po planie tylko podnosi — propozycja niższa niż obecna waga nic nie zmienia.
Historia zmian zostaje w `task.json` (`weight_log`).

**Skutki wagi:** `lekka` — bez `spec.md` (a więc bez flagi i śladu kryteriów), jeden kawałek, dowód weryfikacji
nadal wymagany. `pelna` — plan zatwierdza człowiek przed realizacją, więc przebieg z `--auto` zatrzymuje się blokiem
STOP z wyjaśnieniem; przegląd `security-reviewer` obowiązkowy (reguła w skillu, skrypt jej nie wymusza).

**Ustalenia w trakcie (2026-11-14):**
- Wagę przydziela `run_report.py start` (linia `Waga: …` z powodem), a etapy `intake` i `plan` ponawiają przydział —
  pętla nie musi pamiętać o osobnym poleceniu; `run_state.py weight <katalog>` zostaje do podglądu i podniesienia.
- Decyzja człowieka o wadze jest trwała: po `--set … --by human:<id>` skrypt wagi już nie zmienia, tylko pokazuje
  swoją propozycję. Waga podana wprost przy `tf task start --weight` też nie jest obniżana.
- Zatwierdzenie `plan.md` nie liczy odhaczeń kawałków (`- [x] K1`): bez tego pierwsze odhaczenie unieważniałoby
  zgodę człowieka i blokowało etap `pr`. Nowy albo zmieniony kawałek nadal wymaga ponownej zgody.
- Słowa wrażliwe dobrane ostrożnie pod fałszywe trafienia: „sesja ładowania”, „płatna godzina” i „token” nie
  podnoszą wagi; historyjki pomiarowe S1–S3 dostają wagę zwykłą (sprawdzone testem i ręcznie na ich treści).

**Poza E2:** tryb `--plan` i lista kodów zatrzymań (E3), komunikaty zatrzymań (E4), waga dla cięć pdi (E6 — przebieg
cięcia nie ma zadania, więc nie ma wagi).

## E3 — plan szczegółowy (2026-11-14, przed kodem)

**Pliki i kolejność** (test przed kodem):

1. `core/tests/test_task_mode.py` → `tf task mode <KEY> [plan|zwykly|auto]` i bramka etapu `realizacja`
   w `task_state.py` (rozszerzenie bramki wagi z E2).
2. `core/tests/test_run_state.py` → `run_state.py`: `stage … --plan | --auto` zapisuje tryb zadania, `mode <katalog>
   [tryb]`, `approve <katalog>` (zgoda człowieka na plan), `stage … needs --needs stop --code <kod>` z zamkniętą listą
   kodów, kod i jego opis na podglądzie.
3. `core/tests/test_tf_skill.py` → jedna linia w SKILL.md i `references/tryby-i-zatrzymania.md`; przewodniki,
   `PUBLIC_API.md`.

**Tryby** (wybiera człowiek w poleceniu; skrypt pilnuje wejścia do etapu `realizacja`):

| Tryb | Polecenie | Wejście do realizacji |
|---|---|---|
| Plan | `/tf KEY --plan` | odmowa — przebieg kończy się na planie; realizacja po osobnym poleceniu `/tf KEY` (tryb zmienia `mode`) |
| zwykły (domyślny) | `/tf KEY` | po zgodzie człowieka na plan (jedna zgoda obejmuje specyfikację — plan ma ją w wejściach) |
| Auto | `/tf KEY --auto` | bez zgody, chyba że waga jest pełna (wtedy STOP, jak w E2) |

- Zgodę zapisuje `run_state.py approve <katalog>` (pod spodem `tf task approve <KEY> plan.md --by human:<id>`,
  identyfikator z `git config user.name`); w trybie Auto polecenie odmawia, bo nie ma człowieka.
- Wymóg zgody dotyczy zadań z zarejestrowanym planem (zakłada go pętla). Zadanie prowadzone ręcznie przez `tf task`
  bez zarejestrowanego `plan.md` działa jak dotąd — poza wagą pełną, która zgody wymaga zawsze.

**Zamknięta lista kodów zatrzymań** (`--needs stop --code <kod>`; nieznany kod albo brak kodu → kod wyjścia 2
z listą; komunikaty dla człowieka dopisze E4):

| Kod | Kiedy |
|---|---|
| `pytanie` | brakuje informacji, bez której nie da się zacząć (kryteria, pytanie `[blokuje]`) |
| `podzial` | zadanie za duże albo łączy kilka akcji — propozycja podziału |
| `zrodlo` | nie ma treści zadania albo dostępu do zgłoszenia |
| `zgoda-na-plan` | plan czeka na człowieka (waga pełna z `--auto`, koniec trybu Plan) |
| `testy` | testy albo weryfikacja czerwone po dwóch próbach naprawy |
| `skan` | skan bezpieczeństwa blokuje po dwóch próbach |
| `budzet` | przekroczony `--budget` |
| `srodowisko` | repozytorium nie jest gotowe: niezacommitowane zmiany, brak zdalnego repozytorium, brak narzędzia |
| `zaleznosc` | nowa zależność albo karencja wersji wymaga decyzji |
| `kontrakt` | zmiana kontraktu albo decyzja biznesowa: publiczne API, schemat danych, migracja |
| `uprawnienia` | operacja zastrzeżona dla człowieka: produkcja, publikacja, flaga poza środowiskiem testowym |

**Zmiana kontraktu testów:** przebiegi testowe, które wchodziły w pętlę kawałka bez `--auto` i bez zgody na plan,
dostają zgodę albo `--auto` — to nowa reguła trybu zwykłego, nie osłabienie.

**Ustalenia w trakcie (2026-11-14):**
- Kod zatrzymania obowiązuje także przebieg cięcia pdi (ten sam blok STOP); trybu i zgody na plan cięcie nie ma.
- `intake.py resolve` przy wznowieniu zadania z trybu Plan podaje polecenie ustawienia trybu z polecenia człowieka.
- SKILL.md ma po E3 14 985 znaków (limit 15 000) — kawałki E4 i E5 dopisują treść tylko do `references/`.

**Poza E3:** treść komunikatów i pytań dla każdego kodu (E4); zatrzymania z `autonomy.operations` wykrywane hookiem
(są już w `guard_paths` i polityce autonomii); wygaszanie zgody po nowych commitach.

## E4 — plan szczegółowy (2026-11-14, przed kodem)

**Pliki i kolejność** (test przed kodem):

1. `core/tests/test_stop_messages.py` → `core/skills/tf/templates/stop_messages.json`: dla każdego kodu z listy
   `STOP_CODES` cztery pola — `co` (co się stało, jedno zdanie), `potrzeba` (czego fabryka potrzebuje od człowieka),
   `pytanie` (jedno pytanie) i `opcje` (2–3 opcje, każda ze skutkiem; dokładnie jedna rekomendowana).
2. `core/tests/test_run_state.py` → `run_state.py`: `message <kod>` drukuje komunikat; `stage … needs --needs stop
   --code <kod>` po zapisie zatrzymania drukuje ten sam komunikat z powodem przebiegu; podgląd pokazuje „czego
   potrzeba” i pytanie z opcjami zamiast samego powodu.
3. `core/tests/test_tf_skill.py` → `references/tryby-i-zatrzymania.md`: pętla pokazuje człowiekowi wydrukowany
   komunikat (w rozmowie pytanie zadaje narzędziem z opcjami), nie własny opis. SKILL.md bez zmian (limit znaków).

**Reguły komunikatów** (dokument osi §1a, reguły 2–4):
- prosty język: bez słów z budowy fabryki — test ma listę (`tier`, `hook`, `bramka`, `kawałek`, `triaż`, `harness`,
  `slice`, `gate`, `artefakt`, `STOP`) i jest czerwony, gdy któreś wystąpi w komunikacie;
- pytanie ma stały kształt: jedno zdanie, 2–3 opcje, przy każdej skutek, jedna rekomendacja;
- każdy komunikat kończy się tym, co fabryka zrobi po odpowiedzi.

**Jedno źródło:** lista kodów zostaje w `run_state.py` (`STOP_CODES`), a test pilnuje, że plik komunikatów ma
dokładnie te same kody. Krótki opis kodu na podglądzie pochodzi z pola `co`.

**Poza E4:** tłumaczenie komunikatów na inne języki; komunikaty odmów skryptów (`✗ …`) — są pisane dla agenta.

## E5 — plan szczegółowy (2026-11-14, przed kodem)

Decyzja D12, ruch 1: przypisanie modelu i effortu do kroku trafia do konfiguracji **z dzisiejszymi wartościami** —
zachowanie się nie zmienia. Zmiana przydziału to osobna decyzja po osobnym, płatnym pomiarze.

**Pliki i kolejność** (test przed kodem):

1. `core/tests/test_steps.py` → klucz `steps` w `core/factory/config.yaml` (krok → opis, wykonawca, tier) oraz
   w `build.py`: `apply_steps` (tier kroku staje się tierem jego wykonawcy przy budowaniu agentów), sprawdzenia
   w `build.py check` (nieznany wykonawca albo tier, ten sam wykonawca z dwoma tierami, tabela w skillu niezgodna
   z konfiguracją).
2. `tf config show steps` — tabela: krok, kto, tier, model i effort po nałożeniu profilu kosztów.
3. Tabela „Kto co robi” w `core/skills/tf/SKILL.md` zgodna z `steps` (kolumna „Kto” nazywa agenta); przewodnik
   („Co mogę ustawić”), `PUBLIC_API.md`.

**Kroki i dzisiejsze wartości** (z `shared_agents` w konfiguracji rdzenia, odczyt 2026-11-14):

| Krok | Wykonawca | Tier |
|---|---|---|
| fakty o repozytorium | `scout` | fast |
| wersje, dokumentacja zewnętrzna | `researcher` | fast |
| plan, test, kod | `tf` (sesja główna) | std |
| zmiana mechaniczna ze specyfikacją | `quick-fixer` | fast |
| przegląd zakresu kawałka | `scope-reviewer` | std |
| decyzja trudna do odwrócenia | `architect` | deep |
| auth, sekrety, IaC, CI | `security-reviewer` | deep |

**Ustalenia:** tier kroku nadpisuje tier wykonawcy tylko dla agentów wymienionych w `steps`; projekt zmienia przydział
w `.tf/config/config.yaml` (`steps: {przeglad: {tier: deep}}`) i przebudowuje agentów. Model sesji głównej bez
`claude --agent tf` nadal wybiera człowiek — fabryka go nie przełącza w trakcie zadania (reguła o cache).

**Poza E5:** zmiana wartości domyślnych, eskalacja modelu po porażce bramki, poziom `lead` (D10), effort rozdzielony
od tieru.

## Pomiar po E0 i E1 (2026-11-14)

Jedna seria po obu kawałkach (decyzja właściciela: pomiar po zakończeniu E1), raport
`docs/evals/2026-11-14-pomiar-po-kroku-e1.md`: 8,12 USD wobec 8,58 USD po D4, akceptacja 10/10, STOP 5/5, czas
krótszy o 16–23% (średnie `wall_s` z plików `.jsonl` obu pomiarów). Cztery obserwacje poprawione w treści skilla (zadanie zakładane zawsze przed pytaniami, przegląd zakresu
zawsze przez `scope-reviewer`, zakaz łączenia poleceń wprost, identyfikatory kryteriów od pierwszej wersji testu);
ich skuteczność sprawdzi pomiar po E3. Kolejność dalej: E2 → E3 → **pomiar** → E4 → E5 → E6.

## Pomiar po E2 i E3 (2026-11-14)

Raport `docs/evals/2026-11-14-pomiar-po-kroku-e3.md` (fabryka `744e1bb`, bez E4): 8,93 USD wobec 8,12 USD (+10%),
akceptacja 10/10, STOP 5/5; czasów nie da się porównać, bo w trakcie serii maszyna była obciążona innymi pracami.
Trzy z czterech poprawek z poprzedniego pomiaru zadziałały (ślad po STOP 5/5, przegląd zakresu 10/10, zero poleceń
złożonych); czwarta nie (identyfikator kryterium dopisywany osobnym commitem, nadal 3/5). Dwie nowe poprawki w tym
samym PR co raport: kody zatrzymań wymienione wprost w SKILL.md (pętla zgadywała kod w 8 z 15 przebiegów) oraz
ostrzeżenie `run_state.py verify` o teście bez `AC-n`. Ich skuteczność i wpływ E4 pokaże kolejny pomiar — nie jest
zaplanowany; przypada naturalnie po E6 albo wcześniej na życzenie właściciela.

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
  **Korekta z 2026-11-14:** pierwsze sprawdzenie (commit `873f7b2` z 2026-10-30) dotyczyło starej gałęzi lokalnej
  kopii, nie `main`, i jego wniosek był błędny. Na `main` (`74d201a`) słowo „Talos” jest w 42 plikach (ok. 290
  wystąpień, policzone `git grep -i talos`), także w kodzie i testach. Jedna zależność jest funkcjonalna:
  `src/pdi/phase_sandbox.py` rozpoznawał skaner pętli po ścieżce `.claude/skills/talos-story-run/scripts/security_scan.py`,
  więc z fabryką 10.x obraz fazy nie dostałby semgrepa i faza realizacji zatrzymałaby się na skanie (wniosek z kodu,
  nieodtwarzany na żywym przebiegu). Polecenia `/talos-story-run` ani agenta `talos` kod pdi sam nie wywołuje — robi
  to tryb pdi fabryki, poprawiony w E0.
- [x] **Poprawka w `dbqm45/pdi`** (decyzja właściciela z 2026-11-14: poprawić słowo „Talos”): gałąź
  `claude/rename-talos-to-tf` (pdi#180) — pdi rozpoznaje skaner tylko w ścieżce `.claude/skills/tf/…` (decyzja
  właściciela: bez ścieżki zgodności, pdi wymaga produktu na fabryce 10.0.0 lub nowszej), a nazwa w dokumentach,
  makietach, komentarzach i testach zmienia się na „agent tf” / `/tf`. Po zmianie `git grep -i talos` w pdi nie
  zwraca nic (decyzja właściciela: usunąć także wzmiankę z README). Scalenie PR w pdi należy do właściciela.
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
