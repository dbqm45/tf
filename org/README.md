# Ustawienia firmy (nakładka firmowa)

Standardy i domyślne ustawienia jednej organizacji dla wszystkich jej projektów z fabryką. Robisz je raz, potem
zmieniasz rzadko. Ten katalog nie trafia do projektów: to zestaw do przygotowania paczki firmy.

| W katalogu | Co to jest |
|---|---|
| `new_org_pack.py` | generator: kopiuje szablon do repozytorium firmy i wstawia nazwę, prefiks i wersję rdzenia |
| `template/` | szablon paczki `pack-<firma>` z polami `TODO` |
| `template-team/` | `pack.yaml` i `README.md` nakładki zespołu (`--team`); resztę plików bierze z `template/` |
| `standards_from_docs.py` | standardy z dokumentów firmy: podział na sekcje, kontrola przypisania i cytatów, pliki nakładki |
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
Gdy standardy są już opisane, nie przepisujesz ich ręcznie. Wszystko, co da się sprawdzić, robi skrypt
`org/standards_from_docs.py`; model tylko przypisuje ustalenia do obszaru i rodzaju (krok 3), a skrypt sprawdza wynik.
1. **Dokumenty do katalogu** `~/repos/acme-factory/zrodla/`: eksport z Confluence (HTML), Word (`.docx`), PDF (przez
   `pdftotext`) albo Markdown. W sesji z połączeniem z Confluence (serwer MCP) agent może je pobrać sam — wtedy zapisuje
   kopię z adresem i datą pobrania. Katalog `zrodla/` nie trafia do projektów; dodaj go do `.gitignore` repozytorium
   firmy, jeśli dokumenty są poufne.
2. **Podział na sekcje (skrypt):**
   ```
   python3 org/standards_from_docs.py split ~/repos/acme-factory
   ```
   Sekcja to tekst pod jednym nagłówkiem, z pełną ścieżką nagłówków (`zrodla/sekcje.jsonl`); sekcje o tej samej treści
   są oznaczone jako duplikaty. Skrypt zapisuje też `zrodla/ZADANIE.md` — polecenie dla agenta z formatem wyniku
   i listą sekcji do pokrycia.
3. **Przypisanie (model):** w sesji Claude Code w katalogu nakładki: „Wykonaj zrodla/ZADANIE.md”. Agent zapisuje
   `zrodla/przypisanie.json`: każde ustalenie z obszarem (UI, API, dane, wydania, wspólne), rodzajem (`wzorzec` — reguła
   z przykładem naruszenia i kodem zgodnym; `ocena` — do pliku obszaru), dosłownym cytatem i sprzecznościami; ogólną
   praktykę wpisuje do `pominiete` z powodem.
4. **Kontrola (skrypt, bez modelu):**
   ```
   python3 org/standards_from_docs.py check ~/repos/acme-factory
   ```
   Odrzuca: cytat, którego nie ma w sekcji; sekcję bez ustalenia i bez powodu pominięcia; nieznany obszar; sprzeczność
   bez pary; regułę, która się nie wczytuje albo nie wykrywa swojego przykładu naruszenia (lub wykrywa kod zgodny);
   przykłady, przez które bramka modułu reguł przestałaby przechodzić. Błędy poprawia agent w `przypisanie.json`.
5. **Pliki nakładki (skrypt):**
   ```
   python3 org/standards_from_docs.py apply ~/repos/acme-factory
   ```
   Ustalenia do oceny trafiają do `references/<obszar>.md` (wspólne — do `SKILL.md`) z cytatem i źródłem, wzorce do
   `rules.yaml` z przykładami w `fixtures/`, a `zrodla/RAPORT.md` zbiera sprzeczności, pominięte sekcje i duplikaty.
   Skrypt zmienia tylko bloki `z-dokumentow` — ręczne ustalenia i reguły zostają. Bez zaliczonej kontroli nic nie zapisuje.
6. **Przegląd człowieka:** `zrodla/RAPORT.md` — rozstrzygnij sprzeczności i przejrzyj przypisanie obszarów. Cytaty
   sprawdził już skrypt. Potem scenariusze w `tests/skill_evals/` i kroki 3–5 z listy wyżej.

**Gdy dokument się zmieni:** `split` pokazuje nowe, zmienione i usunięte sekcje od ostatniego `apply`, a `ZADANIE.md`
wymienia tylko je — agent przypisuje tylko zmiany, `check` wskazuje ustalenia, których cytat zniknął ze źródła.

Koszt modelu to jedno przypisanie sekcji (krok 3); zależy od objętości dokumentów [założenie: nie mierzono na
dokumentach firmy]. Ten sam proces działa dla nakładki zespołu (`--team`).

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
