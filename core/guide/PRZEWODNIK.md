# Przewodnik: praca z zespołem agentów fabryki

Fabryka instaluje w projekcie zespół agentów Claude Code: persony (prowadzące rozmowę), ich wykonawców, agentów
wspólnych, skille z wiedzą i procedurami, hooki pilnujące zasad oraz skrypty, które robią mechaniczną pracę bez
tokenów. Ten plik opisuje codzienną pracę; odpowiedzi na częste pytania są w `.tf/factory/FAQ.md`.

## Zacznij tutaj
Cztery kroki od zera do pierwszego PR. Reszta tego pliku to szczegóły dla dociekliwych.

1. **Zainstaluj.** W katalogu projektu wpisz `tf`. Odpowiedz na pytania o język i nakładki.
2. **Przygotuj repozytorium.** `tf onboard --yes` wykrywa polecenia projektu, tworzy `verify.sh` (lint, typy, testy
   jednym poleceniem), włącza bramkę jakości i zapisuje raport gotowości w `.tf/reports/readiness.md`. Z `--verify`
   uruchamia weryfikację raz. `tf doctor` mówi, czy instalacja jest zdrowa i czy bramka działa.
3. **Zleć pierwsze zadanie.** Uruchom `claude` w katalogu projektu i wybierz sposób z tabeli poniżej.
4. **Przejrzyj wynik.** `tf risk` pokazuje, co w zmianie musi obejrzeć człowiek. Scalasz Ty, nie agent.

| Chcę… | Użyj | Co dostanę |
|---|---|---|
| zrobić zadanie z kryteriami akceptacji | `/tf <numer zgłoszenia albo treść>` albo zwykłe zdanie („zrealizuj EBO-1236”) | plan, testy, kod, commit na każdy kawałek, jeden PR |
| zapytać o kod albo nie wiem, od czego zacząć | `claude --agent maja` (nakładka `pack-it`) | odpowiedź albo dobór osób i podejścia |
| zrobić drobną zmianę | zwykła sesja `claude` | zmiana pod kontrolą hooków, bez planu |
| pracować w jednej roli (testy, UX, domena…) | `claude --agent <persona>` z `.claude/catalog.md` | rozmowa z personą i jej wykonawcami |
| przejrzeć repozytorium bez kosztu modelu | `tf analyze` | raporty w `.tf/reports/` |

Coś nie działa albo polecenie zostało zablokowane? Zapytaj w sesji: „co mnie zablokowało i co mogę zrobić?” —
agent wskaże plik, który podjął decyzję. Częste pytania: `.tf/factory/FAQ.md`.

## 1. Z czego składa się instalacja
| Element | Gdzie w projekcie | Co robi |
|---|---|---|
| rdzeń | `.tf/factory/`, `.claude/skills/core-*`, `.claude/hooks/`, `.claude/tests/` | budowa agentów, aktualizacja, koszty, zasady pracy, dziennik projektu |
| nakładki (`pack-*`) | `.tf/factory/packs/<id>/`, ich skille w `.claude/skills/` | wiedza dziedzinowa, role i persony (np. `pack-it`, `pack-ux`, `pack-ev`, `pack-docs`, `pack-editorial-pl`) |
| tryby (`mode-*`) | jak nakładki | sposób pracy włączany na żądanie: `mode-team` (agent teams), `mode-pdi` (cykl zmiany) |
| agenci | `.claude/agents/_generated/` | budowani przez `python3 .tf/factory/build.py` z rdzenia i nakładek — nie edytuj ręcznie |
| katalog | `.claude/catalog.md` | lista person, ról i skilli tej instalacji |
| ustawienia projektu | `.tf/config/` | `config.yaml`, własne persony, role i cechy — aktualizacja ich nie rusza |
| wyniki pracy | `.tf/reports/`, `.tf/register/`, `.tf/cache/`, `.tf/logs/`, `.tf/backup/` | raporty analiz i metryk, rejestr ustaleń, cache, zużycie (`usage.jsonl`), kopie sprzed aktualizacji; szkielet tworzy `tf init` |

Co jest zainstalowane: `tf list`. Stan instalacji: `tf doctor`.

## 2. Jak zacząć pracę
1. **Wybierz personę** z `.claude/catalog.md` i uruchom ją: `claude --agent <nazwa>` (np. `kuba` — product
   engineer, `ewa` — analityczka domeny, `kasia` — testy, `natalia` — UX). Persona rozmawia z Tobą i deleguje
   pracę swoim wykonawcom (`<persona>-<rola>`) oraz agentom wspólnym.
2. **Nie wiesz, kogo wybrać?** Dyspozytorka (`maja` w `pack-it`, `iwona` w `pack-ev`) rozpozna problem opisany
   zwykłym tekstem i dobierze persony, skille i podejście.
3. **Wpisz polecenia projektu** (test, lint, typy, build) w sekcji fabryki w `CLAUDE.local.md` (albo `CLAUDE.md`
   w instalacji zespołowej) — wykonawcy używają ich do weryfikacji.

Agenci wspólni, dostępni dla każdej persony:
- `scout` (tanie szukanie w kodzie);
- `quick-fixer` (drobne zmiany);
- `researcher` (aktualne fakty ze źródeł);
- `architect` (decyzje, tylko analiza);
- `security-reviewer` (przegląd zmian wrażliwych);
- `scope-reviewer` (czy diff nie wykracza poza plan);
- `specialist` (doraźna perspektywa skilli).

## 3. Przebieg projektu i dziennik
- **Dziennik projektu** w `docs/project/` (skill `core-project-record`): każda faza zostawia artefakt z TL;DR
  i sekcją „Przekazanie”, decyzje człowieka są zapisane, a następna sesja zaczyna od nich zamiast od czytania
  całego kodu.
- **Punkt kontrolny** przy dłuższym zadaniu: `python3 .claude/hooks/project_record.py wip start "<cel>"`. Po
  przerwie sesja zaczyna od niego i od `git status`.
- **Fazy od pomysłu do utrzymania** (persony, bramki, gotowość): skill `core-delivery-lifecycle`.
- **Plan przed kodem, potem TDD:** najpierw test, który nie przechodzi, potem kod. Hook `tdd_guard` blokuje kod
  produkcyjny bez czerwonego testu. Bramka jakości: plik `.claude/quality-gate.json` z poleceniem testów, np.
  `{"command": "npm test", "watch": ["src/", "test/"]}` — hook `quality_gate` nie pozwoli zakończyć tury z czerwonym
  buildem (opis w nagłówku `.claude/hooks/quality_gate.py`). Gdy bramka jest wyłączona (brak pliku, wyłącznik,
  zadeklarowana czerwona partia), `tf doctor` i start sesji mówią o tym jednym zdaniem.

## 4. Tryby i automaty na żądanie
| Co | Jak | Kiedy |
|---|---|---|
| pętla fabryki (w rdzeniu) | `/tf <zadanie>` albo `claude --agent tf` | jedno zadanie z kryteriami akceptacji → specyfikacja, plan z kawałków, commit na kawałek, dowody, jeden PR, raport kosztu; podgląd na żywo w `.tf/runs/dashboard.html`; przewodnik: `.tf/factory/PETLA.md` |
| Agent teams (`mode-team`, `tf add mode-team`) | `team_switch.py on`, nowa sesja, `/team-session <zadanie>` | role muszą rozmawiać ze sobą w trakcie; eksperymentalne i drogie; przewodnik: `.tf/factory/packs/mode-team/GUIDE.md` |
| Audyt kodu (`pack-it`) | po zatwierdzeniu zakresu: workflow `/code-audit` | pełny audyt w wielu wymiarach z rankingiem (skill `eng-code-audit`) |
| Symulacja Event Stormingu (`pack-it`) | `/ddd-es-simulation` albo `claude --agent es-host` | trening facylitacji z uczestnikami AI |

### Analiza projektu: `tf analyze`
Szybki przegląd repozytorium skryptami, bez modelu i bez kosztu tokenów. Każdy moduł analizy szuka jednej klasy
problemów; moduły dostarczają nakładki (`pack-it`, `accessibility` — `pack-ux`):

| Moduł | Czego szuka |
|---|---|
| `security` | sekrety w kodzie, pliki `.env` w repo, niebezpieczne API, wyłączony TLS, słaby skrót haseł, brak lockfile'a |
| `architecture` | cykle importów, zależności w obie strony między grupami modułów, huby (graf importów) |
| `authz` | endpointy zmieniające dane (POST/PUT/PATCH/DELETE) bez widocznego sprawdzenia uprawnień: Express, NestJS, Next.js, FastAPI, Spring |
| `data-classification` | pola z danymi osobowymi bez klasy w migracjach, schematach i modelach (szkic inwentarza danych), dane osobowe w logach i w analityce |
| `tech-debt` | TODO/FIXME bez zgłoszenia (z wiekiem z gita), pominięte testy bez powodu, wyciszone sprawdzenia, pliki powyżej 1000 linii |
| `observability` | usługa bez health checka i bez identyfikatora żądania, `console.log`/`print` zamiast loggera, połknięte błędy |
| `i18n` | tekst interfejsu poza tłumaczeniem (w projekcie z biblioteką tłumaczeń), daty bez locale, kwoty bez `Intl.NumberFormat` |
| `accessibility` (`pack-ux`) | obrazy bez `alt`, przyciski i linki bez nazwy, pola bez etykiety, kliknięcie bez klawiatury, `tabindex` > 0, brak `lang` |

- `tf analyze --list` pokazuje moduły i to, czy pasują do repo; `tf analyze` uruchamia wszystkie pasujące,
  `--only security,authz` wybrane, `--since <commit>` tylko pliki zmienione od commita, `--top N` skraca raport.
- Wynik: `.tf/reports/<moduł>.md` z listą działań (checkboxy), `.tf/reports/<moduł>.json` i przegląd
  `.tf/reports/README.md`. Każde ustalenie ma stałe `id`, więc ponowna analiza zachowuje Twoje odhaczenia, a rejestr
  `.tf/register/items.jsonl` pamięta stan ustaleń między przebiegami. Wyniki są cache'owane po commicie
  (`TF_ANALYZE_NO_CACHE=1` wyłącza).
- Ustalenie to heurystyka, czyli „sprawdź”, nie dowód: uprawnienie może sprawdzać warstwa, której skaner nie widzi
  (bramka sieciowa, globalny filtr). Fałszywe trafienie opisz w kodzie i odhacz w raporcie.
- Pełny audyt z modelem i rankingiem to osobna rzecz: workflow `/code-audit` (tabela wyżej).

### Ryzyko zmiany: `tf risk`
`tf risk [--base main]` ocenia diff bieżącej gałęzi względem bazy: poziom wysoki, średni lub niski i lista „co musi
zobaczyć człowiek” (plik, powód). Wysoki poziom dają m.in. uwierzytelnianie, płatności, schemat bazy, wdrożenie
i CI, specyfikacja oraz osłabione testy (usunięte asercje, pominięcia, skasowany test); nowy moduł bez ADR to punkt
„dowód” na liście. `--md` daje sekcję do opisu PR (pętla `/tf` dodaje ją sama), `--json` wynik dla skryptów. Triaż jest
doradczy i nigdy nie blokuje merge'a. Własne reguły (np. ścieżki cennika jako wysokie ryzyko) wpisujesz w
`autonomy.triage` w `.tf/config/config.yaml`.

## 5. Koszty
- **Profil zespołu:** `python3 .tf/factory/profile.py` pokazuje aktywny profil. Dostępne są:
  - `oszczedny` — bez Opusa;
  - `zrownowazony` — domyślny: Haiku do mechaniki, Sonnet na co dzień, Opus do drogich pomyłek;
  - `jakosc` — wyższy effort i doradca Opus.
- **Pomiar:** `python3 .tf/factory/cost_report.py --days 7` (zużycie per agent i model z `.tf/logs/usage.jsonl`);
  pasek stanu pokazuje koszt sesji i zapełnienie kontekstu.
- **Skuteczność fabryki:** `tf metrics [--weeks 4] [--revert-days 7] [--no-gh]` → `.tf/reports/metrics.md`
  i `metrics.json`: odsetek cofniętych zmian, zmiany przyjęte i oczekujące, koszt na przyjętą zmianę, mediana czasu
  PR (z `gh`, chyba że `--no-gh`) i przyczyny poprawek. Przyczynę poprawki fabryka dopisuje sama w commicie
  poprawiającym wcześniejszą zmianę, w stopce `Rework-Cause:` (`luka-specyfikacji`, `blad-agenta`, `zmiana-wymagan`,
  `nieznana`) — nie musisz o tym pamiętać.
- **Zasady:** najtańszy wystarczający model na zadanie i eskalacja dopiero po porażce (skill `core-cost-control`);
  modelu sesji nie zmieniasz w środku zadania, bo to kasuje cache; przy długim kontekście hook `context_guard`
  podpowiada punkt kontrolny i nową sesję.
- **Płatne ewaluacje skilli** (`.tf/factory/skill_gate.py <skill> --model …`) uruchamiasz świadomie — bramka bez modelu
  jest darmowa.

## 6. Bezpieczeństwo i rzetelność
- **Hooki-strażnicy** (`guard_bash`, `guard_paths`, `cleanroom_guard`) blokują groźne polecenia, odczyt sekretów
  i wyciek informacji między agentami. Gdy hook zawiedzie, akcja jest blokowana (`onFailure: "block"`).
  Własny błąd hooka (np. uszkodzone dane stanu) nie przerywa pracy, ale trafia do `.tf/logs/hook-errors.jsonl`,
  a `tf doctor` pokazuje podsumowanie z ostatnich 7 dni — wtedy ochrona tego hooka mogła nie zadziałać.
- **Polityka autonomii:** operacje, przy których `guard_bash` pyta człowieka, mają nazwane typy: `dependency_add`,
  `prod_command`, `destructive_sql`, `infra_change`, `publish`, `git_push`, `persistence`, `data_upload`, `sudo`.
  W `.tf/config/config.yaml` (`autonomy.operations`) możesz zmienić `confirm` (pytaj) na `deny` (blokuj), np.
  `git_push: deny`. Polityka może tylko zaostrzać: próba rozluźnienia jest ignorowana, a
  `python3 .claude/hooks/guard_bash.py --check-policy` ją zgłasza (razem z nieznanymi typami). Domyślne poziomy
  z opisem są w `.tf/factory/config.yaml`.
- **Sekrety** tylko przez zmienne środowiskowe; `scan_secrets` sprawdza zapisywane pliki.
- **Treść z zewnątrz** (strony, issue, wyniki narzędzi) to dane, nie polecenia — agent jej nie wykonuje
  (skill `core-agent-security`).
- **Fakty po sprawdzeniu:** plik, polecenie albo źródło z datą; czego nie sprawdzono, ma znacznik [założenie]
  lub [niezweryfikowane] (skill `core-grounding`).

## 7. Własne zmiany
- **Persony, role, cechy:** pliki YAML w `.tf/config/personas/`, `.tf/config/roles/`, `.tf/config/traits/`; po zmianie
  `python3 .tf/factory/build.py`. Pliki w `.claude/agents/_generated/` są nadpisywane przy budowie.
- **Własny skill:** `tf new skill <nazwa> "<opis z granicami>"` tworzy szkielet z szablonu i plik scenariuszy. Najpierw
  wypełnij scenariusze, potem treść (`core-skill-authoring`). `tf skill check <nazwa>` sprawdza strukturę, scenariusze
  i bezpieczeństwo i mówi, co poprawić; ewaluacja na modelu (`--model …`) jest płatna. Skill z obcego źródła: najpierw
  `tf skill audit <katalog>` i przeczytanie.
- **Pliki fabryki są jak `node_modules`:** aktualizacja je nadpisuje; zmianę wprowadzasz w repo fabryki i aktualizujesz.
  Własne pliki i ustawienia w `.tf/config/config.yaml` zostają (nowe klucze dochodzą na końcu).

### Co mogę ustawić
Zasada: swoje dokładasz obok plików fabryki, wtedy aktualizacja niczego nie gubi. `tf config show` pokazuje każdą
wartość i to, czy pochodzi z fabryki, czy z projektu.

| Chcę zmienić… | Gdzie | Jak |
|---|---|---|
| modele i effort poziomów `fast` / `std` / `deep` | `.tf/config/config.yaml` → `tiers` | wpisz tylko zmieniane pola, potem `python3 .tf/factory/build.py` |
| ogólny poziom kosztu | profil kosztów | `python3 .tf/factory/profile.py <profil>` |
| operacje, o które fabryka pyta albo które blokuje | `.tf/config/config.yaml` → `autonomy` | można tylko zaostrzyć (pytanie → blokada) |
| język rozmowy i commitów | ustawienia fabryki | `tf language <kod>`, `tf commit-language <kod>` |
| czy fabryka sama prowadzi flagi funkcji | `.tf/config/config.yaml` → `feature_flags.auto` | domyślnie `true`: fabryka pyta Cię o nazwę flagi, zakłada ją i pilnuje, żeby poza środowiskiem testowym była wyłączona; `false`: flagi dodajesz samodzielnie (w kodzie, w zewnętrznej usłudze), a fabryka ich nie zakłada i nie wymaga |
| polecenia weryfikacji projektu | `verify.sh`, `.claude/quality-gate.json` | `tf onboard --yes` albo ręcznie |
| wyłączenie bramki jakości u siebie | `.claude/settings.local.json` → `env` | `"QG_GATE_DISABLE": "1"` — `tf doctor` będzie o tym przypominać |
| własną personę, rolę, cechę | `.tf/config/personas/`, `roles/`, `traits/` | plik YAML, potem `python3 .tf/factory/build.py` |
| własny skill | `.claude/skills/<nazwa>/` | `tf new skill`, `tf skill check` |

## 8. Ściąga poleceń
| Polecenie | Co robi |
|---|---|
| `tf` | aktualizacja (albo instalacja, gdy fabryki nie ma) |
| `tf update --check` | czy jest nowa wersja i co się zmieni (nic nie zmienia) |
| `tf add <id>` / `tf remove <id>` | nakładka lub tryb |
| `tf language <kod>` / `tf commit-language <kod>` | język pracy / język commitów i PR |
| `tf list`, `tf doctor [--fix]` | co jest zainstalowane; stan instalacji i naprawy |
| `tf new skill <nazwa> "<opis>"`, `tf skill check <nazwa>`, `tf skill audit <katalog>` | własny skill: szkielet ze scenariuszami, bramka jakości, audyt bezpieczeństwa |
| `tf config show [<klucz>]` | konfiguracja po scaleniu i skąd pochodzi każda wartość |
| `tf spec new <KLUCZ>`, `tf spec check <KLUCZ>` | specyfikacja zadania (`spec.md`): szablon i sprawdzenie, czy kryteria mają Zakładając / Gdy / Wtedy, co zostaje bez zmian i czy nie ma pytań blokujących; z błędami zadanie nie przejdzie do planu |
| `tf task freeze <KLUCZ> <plik> --by human:<id>`, `tf task reopen <KLUCZ> <plik> --by human:<id> --reason "…"` | ochrona podstawy zadania: zamrożony plik (np. test akceptacyjny), zatwierdzony plik zadania i `spec.md` od etapu realizacji agent zmieni tylko za Twoją zgodą; `reopen` zdejmuje ochronę i zapisuje powód |
| `tf trace <KLUCZ> [--md]` | ślad: każde kryterium `AC-n` ze specyfikacji → test z tym identyfikatorem → czy hook TDD widział go jako czerwony → commit → dowód kawałka; kryterium bez testu blokuje przegląd; `--md` daje tabelę do opisu PR |
| `tf task flag <KLUCZ> set <flaga>`, `… none --reason "…"`, `… allow <środowisko> --by human:<id>`, `tf flag check <KLUCZ>` | flaga funkcji na historyjkę: nowe zachowanie jest za flagą włączaną tylko na środowisku testowym; włączenie gdzie indziej wymaga Twojej zgody. Plik flag i środowiska fabryka bierze z karty `.tf/config/operations.json` (zakłada ją `tf onboard`); bez niej mówi wprost, że flagę trzeba sprawdzić ręcznie |
| `tf task weight <KLUCZ>`, `… --set <waga> [--by human:<id> --reason "…"]` | waga zadania: lekka (drobna zmiana, bez specyfikacji, jeden kawałek), zwykła albo pełna (logowanie, płatności, migracje, sekrety — plan zatwierdzasz Ty przed kodem); fabryka dobiera ją sama i podaje powód, podnieść może każdy, obniżyć tylko Ty |
| `tf task mode <KLUCZ> [plan\|zwykly\|auto]`, `tf task approve <KLUCZ> plan.md --by human:<id>` | tryb zadania: Plan kończy na planie, zwykły wpuszcza kod po Twojej zgodzie na plan, Auto idzie bez zgody (nie przy wadze pełnej) |
| `tf status` | lista zadań: etap, ile kawałków ma aktualny dowód, które pliki trzeba odświeżyć |
| `tf task start <KLUCZ> --title "…"`, `tf task stage <KLUCZ> <etap>`, `tf task status <KLUCZ>` | jedno miejsce na zadanie: `docs/project/changes/<KLUCZ>/task.json` i indeks zadań `INDEX.md` |
| `tf onboard [--yes] [--verify] [--dry-run] [--json]` | przygotowanie repozytorium: wykrycie poleceń, `verify.sh`, raport gotowości, bramka jakości, polecenia w pliku instrukcji |
| `tf init` | szkielet `.tf/` na wyniki fabryki (raporty, rejestr, cache, logi) |
| `tf analyze [--only a,b] [--since <commit>] [--top N] [--list]` | analiza projektu modułami → `.tf/reports/<moduł>.md` |
| `tf risk [--base <gałąź>] [--md\|--json]` | triaż ryzyka zmiany na gałęzi (doradczy) |
| `tf metrics [--weeks N] [--revert-days N] [--no-gh]` | skuteczność fabryki → `.tf/reports/metrics.md` |
| `python3 .claude/hooks/guard_bash.py --check-policy` | sprawdzenie polityki autonomii z `.tf/config/config.yaml` |
| `python3 .tf/factory/update.py --rollback` | powrót do stanu sprzed ostatniej aktualizacji |
| `python3 .tf/factory/build.py` | przebudowa agentów i katalogu |
| `python3 .tf/factory/profile.py <profil>` | profil kosztów zespołu |
| `python3 .tf/factory/cost_report.py --days 7` | raport kosztów |
| `python3 .claude/hooks/detect_stack.py` | stack projektu i zgodność skilli z wersjami |
