# FAQ

Codzienna praca: `.tf/factory/GUIDE.md`.

## Czym jest fabryka?
Zestaw do pracy z agentami Claude Code. Instaluje w projekcie persony (agentów, z którymi rozmawiasz), ich
wykonawców, skille z wiedzą i procedurami, hooki pilnujące zasad (TDD, sekrety, bezpieczne polecenia) i skrypty,
które robią mechaniczną pracę bez tokenów. Składa się z rdzenia, nakładek dziedzinowych (`pack-*`) i trybów pracy
na żądanie (`mode-*`).

## Jak dodać fabrykę do projektu?
W katalogu projektu uruchom `tf` (albo `python3 <fabryka>/core/factory/install.py`). Przy pierwszej instalacji
wybierasz język pracy, język commitów oraz nakładki i tryby.
- **Prywatnie** (domyślnie): nic nie trafia do repozytorium. Ustawienia są w `.claude/settings.local.json`, zasady
  w `CLAUDE.local.md`, a ścieżki fabryki w `.git/info/exclude`.
- **Zespołowo** (`--shared`): fabryka jest commitowana razem z projektem. Ustawienia są w `.claude/settings.json`,
  zasady w `CLAUDE.md`, do tego workflow CI.

Instalacja prywatna nie przechodzi przez `git clone`: każdy instaluje fabrykę sam, a CI i sesje w chmurze jej nie mają.
Repozytorium z `AGENTS.md` bez `CLAUDE.md` potrzebuje linii `@AGENTS.md` w `CLAUDE.local.md`. Oba tematy:
`.tf/factory/GUIDE.md`, sekcja „Instalacja prywatna i zespołowa”.

Potem uruchom raz `claude` w katalogu projektu i zaakceptuj zaufanie do folderu. Bez tego hooki i uprawnienia
nie działają.

## Jak zaktualizować fabrykę?
- `tf update --check` pokazuje, czy jest nowa wersja i co się zmieni, niczego nie zmieniając.
- `tf` (albo `python3 .tf/factory/update.py`) aktualizuje.

Po aktualizacji fabryka robi szybką kontrolę (skrypty silnika i hooki się kompilują, `build.py check` przechodzi) —
kilka sekund. Pełne testy fabryki przeszły w CI wydania; w projekcie uruchomisz je poleceniem
`python3 .tf/factory/update.py --full-check` (równolegle, kilka minut).

Przed aktualizacją skille nowej wersji przechodzą audyt narzędziem z wersji zainstalowanej. Pliki fabryki w
projekcie są jak `node_modules`: aktualizacja je nadpisuje, więc zmiany wprowadzasz w repo fabryki i aktualizujesz.
Twoje pliki (własne skille, persony, role, `CLAUDE.local.md`) zostają; w `.tf/config/config.yaml` zostają Twoje
ustawienia, a nowe klucze dochodzą na końcu. Powrót: `python3 .tf/factory/update.py --rollback`.

## Czy aktualizacje mogą działać same?
Tak: `python3 .tf/factory/update.py --auto on` (wyłączenie: `--auto off`). Automatycznie wchodzą tylko wydania PATCH
i MINOR. Wydanie MAJOR, które zmienia publiczne API fabryki, wymaga Twojej decyzji.

## Jak dodać albo usunąć nakładkę lub tryb?
- `tf add <id>` i `tf remove <id>`. Usunięte pliki trafiają do `.tf/backup/`.
- Lista dostępnych i zainstalowanych: `tf list`.
- Domyślna nakładka lub tryb, które pojawią się w nowej wersji, dochodzą przy aktualizacji raz. Usunięte przez
  Ciebie nie wracają.

## Jak dodać ustawienia firmy?
Standardy i domyślne ustawienia całej organizacji trzyma jedna **nakładka firmowa** we własnym repozytorium firmy.
Robisz ją raz, potem instalujesz w każdym projekcie. Pełny przewodnik, także generowanie z dokumentów firmy (np.
Confluence) skryptem `org/standards_from_docs.py`, który sprawdza cytaty bez modelu: `org/README.md` w repozytorium fabryki.
1. **Szkielet.** W klonie repozytorium fabryki (katalog wyniku musi leżeć poza nim):
   ```
   python3 org/new_org_pack.py <firma> --out <katalog> --title "Nazwa firmy"
   ```
2. **Uzupełnij pola `TODO`** (`grep -rn TODO <katalog>`; opis każdego pola: `README.md` w nakładce):
   - `pack.yaml` → `org_defaults.config`: operacje agenta blokowane w firmie (`autonomy.operations`, tylko
     zaostrzanie), ścieżki zawsze do przeglądu człowieka (`autonomy.triage`), limity `tf work` (`work`), profil
     kosztów, języki;
   - `pack.yaml` → `org_defaults.operations.tracker`: tracker, prefiksy kluczy zgłoszeń, pole Jiry z kryteriami;
   - reguły sprawdzalne wzorcem (`analyzers/<firma>-standards/rules.yaml`, z przykładami w `fixtures/`): działają
     bez modelu w `tf analyze`; reguły semgrep — `semgrep.yml`, używany w skanie pętli `/tf`;
   - skill standardów (`skills/<firma>-standards/`): tylko ustalenia wymagające oceny — najpierw scenariusze
     w `tests/skill_evals/`, potem treść;
   - `settings.json`: uprawnienia Claude Code dla całej firmy.
3. **Sprawdź** w repozytorium fabryki: `python3 tools/workspace.py check --packs pack-it,pack-<firma> --pack-dir
   <katalog>`.
4. **Opublikuj** katalog jako repozytorium git firmy (z tagami wersji `vX.Y.Z`).
5. **Zainstaluj w projekcie:** `tf install --pack-dir <adres repozytorium firmy> --add pack-<firma>`. `tf update`
   pobiera potem nowe wersje nakładki.

**Zespół** ma własną nakładkę ponad firmową: `python3 org/new_org_pack.py <firma> --team <zespół> --out <katalog>`
(standardy, reguły i prefiksy zgłoszeń zespołu; zakazy firmy tylko zaostrza). Instalacja w projekcie zespołu:
`tf install --pack-dir <repo firmy> --pack-dir <repo zespołu> --add pack-<firma>-<zespół>`.

Wartości firmy pokazuje `tf config show` (źródło „organizacja”, dla zespołu „zespół”). Projekt nadpisuje je w `.tf/config/config.yaml`
i `.tf/config/operations.json`; zakazu z polityki autonomii firmy nie rozluźni. Adresów i tokenów (Jira, Confluence)
nakładka nie zawiera: Jira bierze adres i dane dostępu ze zmiennych `JIRA_BASE_URL`, `JIRA_EMAIL`,
`JIRA_API_TOKEN` (albo `JIRA_TOKEN`), a dostęp do Confluence na żywo to połączenie (serwer MCP) w Claude Code.

## Jak ustawić swój sposób pracy z agentem?
`tf style autonomous` (agent idzie sam, raport na końcu), `tf style step-by-step` (zatwierdzasz plan i każdy kawałek
pracy) albo `tf style conversation` (zadanie kończy się na planie, a Claude Code startuje w trybie planowania, więc
także zwykła rozmowa nie zmienia plików bez Twojej zgody). Styl obowiązuje we
wszystkich Twoich projektach; tylko w bieżącym: `--here`. Nie trafia do repozytorium i nie zmienia pracy innych osób.
Granice ustala firma, zespół albo projekt: styl nie włączy trybu, którego nie dopuszczają (`task.allowed_modes`), ani
nie rozluźni zakazów polityki autonomii. Szczegóły: `.tf/factory/GUIDE.md`, sekcja „Co mogę ustawić”.

## Który model i ile to kosztuje?
- Role mają tiery: `fast` (Haiku), `std` (Sonnet), `deep` (Opus).
- Profil zespołu przestawia je jednym poleceniem: `python3 .tf/factory/profile.py oszczedny|zrownowazony|jakosc`.
- Koszt mierzysz poleceniem `python3 .tf/factory/cost_report.py --days 7`, a pasek stanu pokazuje koszt bieżącej sesji.

Funkcje płatne z natury (ewaluacje skilli na modelu, agent teams) uruchamiasz świadomie.

## Czym są hooki fabryki?
Skrypty uruchamiane przez Claude Code przy zdarzeniach, niezależnie od decyzji modelu:
- `guard_bash` — groźne polecenia powłoki;
- `guard_paths` — pliki z sekretami;
- `cleanroom_guard` — izolacja informacji między agentami;
- `tdd_guard` — kod dopiero po czerwonym teście;
- `quality_gate` — z `.claude/quality-gate.json` tura i podagent nie kończą się z czerwonymi testami (blokada
  testów: `test_lock.py`);
- `scan_secrets` — sekrety w zapisanych plikach;
- `skill_hint` — podpowiedzi skilli (bez frameworków i języków spoza stacku projektu);
- `context_guard` — ostrzeżenie o długim kontekście;
- `log_usage` — zapis zużycia;
- `update_notice` — informacja o nowym wydaniu.

Strażnicy blokują akcję także wtedy, gdy sam hook zawiedzie. Stan hooków: `python3 .tf/factory/hooks_status.py`.

## Dlaczego agent pyta o zgodę na polecenie?
Uprawnienia są celowo wąskie: agent bez pytania uruchamia tylko polecenia z listy `allow` w ustawieniach. Polecenie,
którego używasz często, dopisz do `allow` w `.claude/settings.local.json`. Zasady i tryby uprawnień opisuje skill
`core-agent-security`.

## Agent podał nieprawdziwy fakt — co robić?
Poproś o źródło. Zasada fabryki to fakt z pliku, polecenia albo źródła z datą, a czego nie sprawdzono — ze
znacznikiem [założenie]. Powtarzającą się pomyłkę zapisz w `docs/project/lessons.md`, żeby następne sesje jej
unikały.

## Co to jest `.tf/` i `tf analyze`?
`tf init` zakłada w projekcie katalog `.tf/` — jedno miejsce na wyniki pracy fabryki: `reports/` (raporty analiz),
`register/` (rejestr pracy), `cache/`, `logs/`, `runs/`, `backup/`; każdy katalog ma `README.md`, co w nim jest i czy
można go usunąć. W instalacji prywatnej cały `.tf/` jest w `.git/info/exclude`, w zespołowej do `.gitignore` trafiają
tylko katalogi odtwarzalne. `tf analyze` uruchamia moduły przeglądu (`tf analyze --list`) i dla każdego pisze
`.tf/reports/<moduł>.md` z listą działań do odhaczania; ponowna analiza zachowuje odhaczenia i notatki, oznacza
to, co wygląda na naprawione, i dopisuje nowe ustalenia na końcu. Na razie działają tylko skrypty (piętro 0), bez
modelu i bez kosztu; moduły dokładają nakładki albo własny katalog `.tf/analyzers/`.

## Jak odinstalować fabrykę?
`tf uninstall --dry-run` pokazuje, co zostanie usunięte i zmienione. `tf uninstall --yes` usuwa:
- pliki fabryki zapisane w manifeście (silnik, skille, hooki, testy) i pliki generowane (agenci, katalog);
- blok fabryki w `CLAUDE.local.md` albo `CLAUDE.md` oraz w `.git/info/exclude` albo `.gitignore`;
- wpisy fabryki w ustawieniach Claude Code (Twoje uprawnienia i hooki zostają) i tryb uprawnień ustawiony przez styl.

Twoje pliki zostają: własne skille, `.tf/config/`, wyniki pracy w `.tf/`. `--force` usuwa też je. `docs/project/`
i kodu projektu polecenie nigdy nie rusza. Przed zmianą zapisuje kopię w `~/.tf/backups/<projekt>-<data>.zip`
(przywrócenie: `unzip -o <plik> -d <projekt>`).

## Gdzie czytać dalej?
- `.claude/catalog.md` — persony, role i skille tej instalacji.
- `.tf/factory/packs/<id>/GUIDE.md` — przewodniki trybów (np. `mode-pdi`, `mode-team`).
- `.tf/factory/PUBLIC_API.md` — co jest publicznym API fabryki i jak są numerowane wersje.
- `.tf/factory/CHANGELOG.md` — co zmieniło się w kolejnych wersjach.
