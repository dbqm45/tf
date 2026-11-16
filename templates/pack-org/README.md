# Nakładka firmowa {{TITLE}} (`pack-{{FIRMA}}`)

Standardy, zasady i domyślne ustawienia {{TITLE}} dla każdego projektu, w którym działa fabryka tf. Trzymaj ten
katalog we własnym repozytorium firmy, nie w repozytorium fabryki.

## Co uzupełnić
Wszystkie miejsca do zmiany mają znacznik `TODO`. Lista: `grep -rn TODO .`

| Plik | Co wpisać |
|---|---|
| `pack.yaml` → `description` | jedno zdanie po angielsku (pokazuje je `tf list`) |
| `pack.yaml` → `org_defaults.config.autonomy` | które operacje agenta blokować w całej firmie (`deny`); organizacja może tylko zaostrzać |
| `pack.yaml` → `org_defaults.config.autonomy.triage` | ścieżki, które w firmie zawsze ogląda człowiek (`tf risk`) |
| `pack.yaml` → `org_defaults.config.work` | limity wydatku pracy bez nadzoru (`tf work --once`) |
| `pack.yaml` → `org_defaults.operations.tracker` | tracker, prefiksy kluczy zgłoszeń, pole z kryteriami akceptacji |
| `skills/{{PREFIX}}standardy/SKILL.md` | reguły firmy, których model nie zna sam: nazwy, progi, zakazy, kto zatwierdza |
| `tests/skill_evals/{{PREFIX}}standardy.json` | 2 prawdziwe pytania z pracy w firmie i 1 pytanie spoza firmy — **przed** treścią skilla |
| `settings.json` | uprawnienia Claude Code dla całej firmy (`allow`, `deny`); dopisywane do ustawień projektu |

Więcej skilli: kolejny katalog `skills/{{PREFIX}}<nazwa>/` z plikiem scenariuszy w `tests/skill_evals/`. Własne role
i persony: `roles/`, `personas/` (format jak w nakładkach fabryki).

## Czego tu nie wpisujesz
- **Adresów i tokenów** (Jira, Confluence, chmura). Adres Jiry i dane dostępu są tylko w zmiennych środowiska
  (`JIRA_BASE_URL`, `JIRA_EMAIL` z `JIRA_API_TOKEN` albo `JIRA_TOKEN`).
- **Połączeń z narzędziami** (Confluence, Jira na żywo, Slack). To połączenia (serwery MCP) w konfiguracji Claude Code
  albo w ustawieniach zarządzanych przez organizację, nie w fabryce.
- **Ogólnej wiedzy**, którą model zna sam — nic nie dodaje, a zajmuje kontekst w każdej sesji.

## Sprawdzenie
W repozytorium fabryki:
```
python3 tools/workspace.py check --packs pack-it,pack-{{FIRMA}} --pack-dir <ten katalog>
```
Bramka skilla nie przejdzie, dopóki scenariusze mają `TODO`. To oczekiwane. Po uzupełnieniu, w przestrzeni roboczej:
`python3 .tf/factory/skill_gate.py {{PREFIX}}standardy`, potem
`python3 tools/workspace.py sync-gate --out <przestrzeń> --pack-dir <ten katalog>`.

## Instalacja w projekcie
```
tf install --pack-dir <ten katalog albo adres repozytorium git> --add pack-{{FIRMA}}
```
Fabryka zapamiętuje źródło, więc `tf update` pobiera nową wersję nakładki sama. Wartości z `org_defaults` widać w
`tf config show` jako „organizacja”. Projekt nadpisuje je w `.tf/config/config.yaml` (polityki autonomii nie da się
rozluźnić) i w `.tf/config/operations.json`.

## Wersje
Zmianę opisz w commicie i podbij `version` w `pack.yaml` według SemVer: nowy skill albo reguła — MINOR, usunięcie
albo zmiana nazwy skilla — MAJOR.
