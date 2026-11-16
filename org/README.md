# Ustawienia firmy (nakładka firmowa)

Standardy i domyślne ustawienia jednej organizacji dla wszystkich jej projektów z fabryką. Robisz je raz, potem
zmieniasz rzadko. Ten katalog nie trafia do projektów: to zestaw do przygotowania paczki firmy.

| W katalogu | Co to jest |
|---|---|
| `new_org_pack.py` | generator: kopiuje szablon do repozytorium firmy i wstawia nazwę, prefiks i wersję rdzenia |
| `template/` | szablon paczki `pack-<firma>` z polami `TODO` |
| `template-team/` | `pack.yaml` i `README.md` nakładki zespołu (`--team`); resztę plików bierze z `template/` |
| `README.md` | ten przewodnik |

## Co ustawia paczka firmy
| Część paczki | Co robi w każdym projekcie |
|---|---|
| `pack.yaml` → `org_defaults.config.autonomy.operations` | blokuje operacje agenta w całej firmie (`deny`); projekt nie może tego rozluźnić |
| `pack.yaml` → `org_defaults.config.autonomy.triage` | ścieżki, które `tf risk` zawsze oznacza do przeglądu człowieka |
| `pack.yaml` → `org_defaults.config.work`, `default_profile`, języki | limity `tf work`, profil kosztów, język pracy i commitów |
| `pack.yaml` → `org_defaults.config.task.allowed_modes` | tryby zadania dozwolone w firmie; styl pracy osoby (`tf style`) wybiera tylko spośród nich |
| `pack.yaml` → `org_defaults.operations.tracker` | tracker, prefiksy kluczy zgłoszeń, pole Jiry z kryteriami (bez adresu i tokenu) |
| `analyzers/<firma>-standardy/rules.yaml` | standardy sprawdzane **bez modelu** (`tf analyze`): zakazane API i importy, wymagane nagłówki, nazwy plików |
| `semgrep.yml` | reguły semgrep w skanie każdego kawałka pętli `/tf` |
| `skills/<firma>-standardy/` | standardy wymagające oceny: `SKILL.md` to spis, ustalenia obszarów (UI, API, dane, wydania) w `references/` — agent czyta tylko obszar swojego zadania |
| `settings.json` | uprawnienia Claude Code dla całej firmy |

Paczka **nie zawiera** adresów ani tokenów (Jira bierze je ze zmiennych `JIRA_BASE_URL`, `JIRA_EMAIL`,
`JIRA_API_TOKEN` albo `JIRA_TOKEN`) ani połączeń z narzędziami (Confluence i Jira na żywo to serwery MCP
w konfiguracji Claude Code).

## Jak wygenerować — krok po kroku
1. **Szkielet** (w klonie repozytorium fabryki):
   ```
   python3 org/new_org_pack.py acme --out ~/repos/acme-factory --title "ACME"
   ```
2. **Uzupełnij pola `TODO`** (`grep -rn TODO ~/repos/acme-factory`), w tej kolejności:
   1. `pack.yaml` → `org_defaults`: polityka autonomii, ścieżki do przeglądu, limity, tracker;
   2. `rules.yaml` — każde ustalenie, które da się zapisać wzorcem (z przykładem naruszenia w
      `fixtures/naruszenia/` i kodem zgodnym w `fixtures/czyste/`);
   3. scenariusze `tests/skill_evals/<firma>-standardy.json` — pytanie na obszar;
   4. pliki obszarów `references/<obszar>.md` — tylko ustalenia wymagające oceny; spis w `SKILL.md`;
   5. `semgrep.yml` i `settings.json`, jeśli firma ich potrzebuje.
3. **Sprawdź** (w repozytorium fabryki):
   ```
   python3 tools/workspace.py check --packs pack-it,pack-acme --pack-dir ~/repos/acme-factory
   ```
   Dopóki scenariusze mają `TODO`, nie przejdzie tylko bramka skilla. Po uzupełnieniu w przestrzeni roboczej:
   `python3 .tf/factory/skill_gate.py acme-standardy` i
   `python3 tools/workspace.py sync-gate --out <przestrzeń> --pack-dir ~/repos/acme-factory`.
4. **Opublikuj** katalog jako repozytorium git firmy z tagiem `v0.1.0`.
5. **Zainstaluj w projekcie:** `tf install --pack-dir <adres repozytorium firmy> --add pack-acme`.
   Wartości firmy pokazuje `tf config show` (źródło „organizacja”), reguły — `tf analyze --only acme-standardy`.

## Jak wygenerować z dokumentów firmy (np. Confluence)
Gdy standardy są już opisane, nie przepisujesz ich ręcznie: dajesz dokumenty agentowi i sprawdzasz wynik.
1. **Dokumenty do katalogu.** Eksport stron z Confluence (HTML, Word, PDF) albo pliki Markdown do
   `~/repos/acme-factory/zrodla/`. W sesji z połączeniem z Confluence (serwer MCP) agent może je pobrać sam — wtedy
   zapisuje kopię z adresem i datą pobrania. Katalog `zrodla/` nie wchodzi do paczki: dodaj go do `.gitignore`,
   jeśli dokumenty są poufne.
2. **Polecenie dla agenta** (sesja Claude Code w katalogu paczki, po kroku 1 z listy wyżej):
   > Przeczytaj dokumenty w `zrodla/` i rozdziel każde ustalenie firmy według obszaru (UI, API, dane, wydania,
   > wspólne) i rodzaju: (a) sprawdzalne wzorcem → reguła w `analyzers/acme-standardy/rules.yaml` z przykładem
   > naruszenia w `fixtures/naruszenia/` i oczekiwanym ustaleniem w `expected.json`; (b) wymaga oceny → plik obszaru
   > w `skills/acme-standardy/references/`; (c) ogólna praktyka, którą zna każdy model → pomiń. Każde ustalenie
   > podaj z cytatem i źródłem (plik, sekcja, data). Sprzeczności między dokumentami nie rozstrzygaj — wypisz je.
   > Na końcu zapisz raport `zrodla/RAPORT.md`: co trafiło gdzie, co pominięto i dlaczego, sprzeczności.
3. **Przegląd człowieka.** Przeczytaj `zrodla/RAPORT.md` i rozstrzygnij sprzeczności. Sprawdź, że cytaty są
   w dokumentach. Reguły z `rules.yaml` traktuj jak kandydatów: każda musi przejść bramkę modułu na przykładach
   (`python3 .tf/factory/analyze.py gate --module acme-standardy` w projekcie z paczką).
4. Dalej kroki 3–5 z listy wyżej.

Koszt to jednorazowe przetworzenie dokumentów przez model; zależy od ich objętości [założenie: nie mierzono].
Automat z kontrolą cytatów skryptem (jak `recon_check` w rekonstrukcji projektu) jest planowany — do tego czasu
cytaty sprawdza człowiek.

## Nakładka zespołu
Gdy zespoły w firmie pracują inaczej (np. backend ma własne zasady API i migracji, a frontend bibliotekę komponentów),
każdy zespół dostaje nakładkę ponad firmową:
```
python3 org/new_org_pack.py acme --team backend --out ~/repos/acme-backend-factory --title "ACME Backend"
```
Powstaje `pack-acme-backend`, który wymaga `pack-acme`. Ma ten sam układ co nakładka firmy, ale w `pack.yaml` sekcję
`team_defaults` (zamiast `org_defaults`) i prefiks skilli `backend-`. Wpisujesz tylko to, czym zespół różni się od firmy.
- **Kolejność warstw:** silnik ← firma ← zespół ← projekt ← osoba. `tf config show` pokazuje źródło każdej wartości.
- **Granice:** zespół, projekt i osoba tylko zaostrzają politykę autonomii firmy; dozwolone tryby zadania
  (`task.allowed_modes`) to przecięcie warstw — nikt niżej nie przywróci trybu, który firma zabrała. Inne wartości
  (limity `tf work`, profil kosztów, języki) zespół zmienia dla swoich projektów.
- **Tracker:** prefiksy zgłoszeń zespołu zastępują prefiksy firmy; typ i pola przychodzą z firmy.
- **Sprawdzenie:** `python3 tools/workspace.py check --packs pack-it,pack-acme,pack-acme-backend --pack-dir
  ~/repos/acme-factory --pack-dir ~/repos/acme-backend-factory`.
- **Instalacja w projekcie zespołu:** `tf install --pack-dir <repo firmy> --pack-dir <repo zespołu> --add
  pack-acme-backend` (nakładka firmy dochodzi sama). W projekcie może być najwyżej jedna nakładka zespołu.

## Zmiany później
Zmiana standardów to zmiana w repozytorium firmy: popraw pliki, podbij `version` w `pack.yaml` według SemVer (nowa
reguła albo obszar — MINOR, usunięcie albo zmiana nazwy skilla — MAJOR), sprawdź (krok 3), dodaj tag. Projekty
dostają zmianę przy `tf update`. Ponowne generowanie nie jest potrzebne: generator robi tylko pierwszy szkielet
i odmawia zapisu do istniejącego katalogu.
