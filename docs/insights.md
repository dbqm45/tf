# Insights

## Jak działa fabryka: rdzeń i nakładki

### Warstwy
- **Rdzeń** (`core/`) — mechanika: budowa agentów (`factory/build.py`), składanie konfiguracji (`factory/packs.py`),
  instalator i aktualizator (`install.py`, `update.py`), launcher `tf`, migracje (`migrations.py`), hooki
  (`core/hooks/`), skille praktyk `core-*`, cechy ogólne i agenci wspólni (`scout`, `researcher`, `architect`,
  `security-reviewer`, …). Rdzeń nie zakłada, że jakakolwiek nakładka jest zainstalowana.
- **Nakładki** (`packs/pack-*`) — wiedza dziedziny: skille, role, persony, cechy, agenci, konsultanci. Każda ma
  `pack.yaml` z własną wersją i zakresem wersji rdzenia (`requires.core`). Dziś: `pack-it`, `pack-ux`, `pack-docs`,
  `pack-editorial-pl`, `pack-ev`. Nowa dziedzina = nowy katalog `packs/pack-<nazwa>/` z `pack.yaml`.

### Źródło a projekt
Repozytorium to **drzewo źródłowe**. Instalator składa z niego projekt w **układzie instalacji**:

| Źródło | W projekcie |
|---|---|
| `core/factory/` | `factory/` |
| `core/skills/`, `packs/<id>/skills/` | `.claude/skills/` (jedno miejsce — tylko stąd czyta je Claude Code) |
| `core/hooks/`, `packs/<id>/hooks/` | `.claude/hooks/` |
| `core/tests/`, `packs/<id>/tests/` | `.claude/tests/` |
| `packs/<id>/{pack.yaml,roles,personas,traits,technologies.json}` | `factory/packs/<id>/` |
| `core/settings.json` + `packs/<id>/settings.json` | `.claude/settings.local.json` (albo `settings.json` w trybie `--shared`) |
| `core/cleanroom.json` + `packs/<id>/cleanroom.json` | `.claude/cleanroom.json` |

Agenci (`.claude/agents/_generated/`) i katalog (`.claude/catalog.md`) **nie są w repozytorium** — `build.py` buduje
je w projekcie po każdej instalacji i zmianie ustawień, z tego, co jest zainstalowane.

### Składanie (dziedziczenie)
`factory/packs.py` łączy `factory/config.yaml` rdzenia z `pack.yaml` zainstalowanych nakładek:
- **wymiary skilli** (prefiksy, np. `ddd-`, `dom-`) — rdzeń ma `core-`, `fw-`, `lang-`, `tool-`; nakładki dokładają
  swoje z `order` (kolejność łączenia skilli); ten sam prefiks w dwóch miejscach to błąd;
- **agenci wspólni, konsultanci, wiersze i akapity routingu** — rdzeń, potem nakładki;
- **`always_skills`** nakładki trafiają tylko do jej person; rdzenia — do wszystkich;
- **`contributes`** — wkład nakładki do person, ról i agentów *spoza* niej (np. `pack-docs` dokłada skill
  dokumentacji każdej personie, `pack-ux` dokłada skill dostępności roli `product-compliance` z `pack-it`,
  `pack-ev` dopisuje wskazówki do promptu `security-reviewer`). Wzbogaca ten, kto wnosi funkcję — nakładka
  przyjmująca nic o nim nie wie;
- **`contributes_when`** — warunek wkładu (np. `{language: pl}`); niespełniony → nakładka „uśpiona”: skille
  i persony zostają, ale jej agenci, routing i wkład znikają;
- **`optional_packs`** — odwołania do elementów tych nakładek są pomijane bez błędu, gdy ich nie ma (np. role UX
  odwołują się do skilli procesu z `pack-it`);
- **`requires.packs`** — twarda zależność; instalator dokłada wymagane nakładki sam;
- **dane nakładek** zamiast stałych w kodzie rdzenia: interwały przeglądu skilli (`freshness`), widoczność
  opisów (`skill_visibility`), rejestr technologii hooka `detect_stack` (`technologies.json`), profile clean-room,
  uprawnienia, wymagane sekcje plików referencyjnych (`reference_sections`).

Własne role, persony i cechy projektu (`factory/{roles,personas,traits}/`) mają pierwszeństwo przed nakładkami
o tej samej nazwie.

### Języki
- **Treść fabryki** jest po polsku (`content_language` w `pack.yaml`); tłumaczenie — `docs/todo.md`.
- **Język pracy** (`language`, domyślnie `pl`) — rozmowa i dokumentacja; **język commitów** (`commit_language`,
  domyślnie `en`) — commity, PR, CHANGELOG. Kod zawsze po angielsku.
- Ustawienia są w `.claude/factory-settings.json` (poza plikami fabryki, aktualizacje ich nie ruszają).
  `build.py` wkleja sekcję „Język” do każdego agenta, instalator i `tf language` — do bloku w CLAUDE.md.
- Język może wymagać nakładki (`languages.<kod>.pack` w konfiguracji rdzenia): `pl` → `pack-editorial-pl`.
- Instalator i `tf` komunikują się z człowiekiem po angielsku.

### Instalacja, aktualizacja i autokorekta
- `tf install` / `core/factory/install.py` — rdzeń zawsze; pierwsza instalacja pyta o język pracy, język commitów
  i nakładki (`--packs`, `--yes` bez pytań). Manifest `.claude/factory-manifest.json` zapisuje wersję, nakładki
  i skrót każdego pliku: pliki zmienione przez człowieka nie są nadpisywane (nowa wersja obok jako `*.factory-new`),
  pliki usunięte z fabryki lub z usuniętej nakładki idą do `.claude/factory-backup/`.
- `tf update` pobiera nową wersję ze źródła (katalog, .zip, git) i uruchamia **jej** instalator; `tf add`,
  `tf remove`, `tf language` przechodzą tą samą drogą.
- **Autokorekta:** po aktualizacji instalator stosuje `factory/migrations.py` (zmiany nazw w rdzeniu i nakładkach)
  do plików projektu, których fabryka nie instalowała (własne persony, role, nakładki, skille), i buduje agentów
  od nowa. `tf doctor` sprawdza zgodność wersji, wymagane nakładki, nakładkę języka i aktualność agentów;
  `tf doctor --fix` naprawia to, co da się naprawić samo.
- Instalacje `claude-team-factory` i `ev-team-factory` są migrowane: instalator dobiera odpowiadające im nakładki
  i podmienia stare bloki w CLAUDE.md i plikach ignorowania.

### Rozwój fabryki
- `python3 tools/workspace.py assemble|check --packs <wybór>` — projekt złożony z bieżących źródeł w `.work/`
  (testy i `build.py` działają w układzie instalacji, nie w drzewie źródłowym).
- `python3 tools/workspace.py matrix` — sam rdzeń, każda nakładka osobno i wszystkie razem (to samo robi CI).
- `python3 tools/workspace.py refs` — rdzeń nie wymienia elementów nakładek (chyba że linia nazywa nakładkę,
  np. „(pack-it)”), nakładka wymienia tylko elementy nakładek, od których zależy.
- `python3 tools/workspace.py sync-gate` — wyniki bramki jakości skilli z projektu roboczego z powrotem do źródeł.

## Konsultanci: jak zespoły z różnych nakładek pytają się nawzajem

### Ograniczenie, z którego to wynika

W Claude Code agenci nie rozmawiają ze sobą swobodnie:

- **Podagent nie może wywołać kolejnego podagenta.** Według dokumentacji Claude Code podagenci nie uruchamiają
  własnych podagentów. Wykonawca uruchomiony przez personę (np. `jan-backend`) nie zleci więc pracy innemu agentowi;
  robi to tylko sesja główna.
- **Sesje są od siebie odizolowane.** Persona uruchomiona jako `claude --agent jan` nie widzi rozmowy persony
  `claude --agent oskar`, nawet w tym samym repozytorium. Nie ma kanału, którym jedna sesja zada pytanie drugiej
  i dostanie odpowiedź.
- **Podagent nie widzi rozmowy, która go wywołała.** Dostaje tylko brief i zwraca jeden raport.

„Swobodna rozmowa” persony IT z personą EV nie jest więc możliwa. Możliwe jest coś węższego: **sesja główna
(persona) wywołuje wyspecjalizowanego podagenta z wiedzą innej dziedziny i dostaje od niego odpowiedź.**

### Mechanizm

1. **Konsultanci nakładki.** Każda nakładka deklaruje w `pack.yaml` (sekcja `consultants`) agentów do konsultacji:
   nazwę, opis, skille i tier. `factory/build.py` generuje z nich agentów:
   - tylko do odczytu (`Read`, `Grep`, `Glob`, `Skill`) — konsultant odpowiada, nie zmienia plików;
   - z wczytanymi skillami swojej dziedziny;
   - z kontraktem odpowiedzi: krótka odpowiedź, źródło (skill, plik, standard), czego nie wie, co wymaga decyzji
     człowieka.
2. **Generowany katalog „kogo zapytać”.** Do promptu każdej persony `build.py` wkleja tabelę konsultantów
   z **innych** zainstalowanych nakładek i dopisuje ich do listy agentów, których persona może wywołać
   (`Agent(...)` w nagłówku pliku agenta). Persona `jan` (pack-it) przy zainstalowanym pack-ev widzi np.
   `ev-consult-protocols`; bez pack-ev tego wiersza nie ma i nic się nie psuje.
3. **Wspólne skille.** Skille wszystkich zainstalowanych nakładek leżą w jednym `.claude/skills/`, więc persona może
   też sama wczytać skill innej dziedziny. Konsultant jest lepszy przy szerszym pytaniu: czyta wiele skilli i plików
   we własnym kontekście, a do persony wraca tylko odpowiedź (kontekst persony nie puchnie).
4. **Plik pytań do innej persony.** Gdy pytanie wymaga pracy innej persony w jej własnej sesji albo decyzji
   człowieka, persona zapisuje je w `docs/project/questions.md` (kto pyta, do kogo, pytanie, kontekst, termin).
   Druga persona odpowiada w tym pliku w swojej sesji. To kanał asynchroniczny, nie rozmowa na żywo.

### Kto może konsultować

| Kto | Może wywołać konsultanta? | Dlaczego |
|---|---|---|
| persona uruchomiona jako sesja (`claude --agent jan`) | tak | ma narzędzie `Agent` |
| wykonawca persony (`jan-backend`) | nie | podagent nie wywołuje podagentów; potrzebę konsultacji zgłasza w raporcie, a persona ją wykonuje |
| konsultant | nie | jest podagentem; jeśli pytanie wykracza poza jego dziedzinę, pisze to w odpowiedzi |

Typowy przebieg: `jan-backend` w raporcie pisze „potrzebna decyzja: jak liczyć kWh przy korekcie CDR”. Jan wywołuje
`ev-consult-business`, dostaje odpowiedź ze źródłem i przekazuje ją w kolejnym briefie wykonawcy.

### Koszty i granice

- Każde wywołanie konsultanta to nowy kontekst: wczytuje skille od zera. Persona pyta, gdy odpowiedź jest warta
  więcej niż samodzielne wczytanie jednego skilla.
- Opisy wszystkich agentów (także konsultantów) trafiają do kontekstu sesji. Każda nakładka dokłada więc kilka
  wierszy; dlatego konsultantów jest kilku na nakładkę (po obszarach), a nie po jednym na skill.
- Konsultant nie zastępuje persony innej dziedziny w dłuższej pracy (projekt, implementacja). Do tego służy osobna
  sesja tej persony i plik pytań.

### Inne narzędzia niż Claude Code

Lista targetów w `core/factory/build.py` (`TARGETS`, ustawienie projektu `targets`) pozwoli kiedyś generować pliki
dla innych narzędzi (np. Codex, Gemini CLI); dziś jest tylko target `claude`.
Tam, gdzie narzędzie nie ma podagentów, konsultacje przechodzą w tryb zastępczy: persona wczytuje skille innej
nakładki sama (pkt 3) albo korzysta z pliku pytań (pkt 4).
