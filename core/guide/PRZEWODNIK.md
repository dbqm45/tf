# Przewodnik: praca z zespołem agentów fabryki

Fabryka instaluje w projekcie zespół agentów Claude Code: persony (prowadzące rozmowę), ich wykonawców, agentów
wspólnych, skille z wiedzą i procedurami, hooki pilnujące zasad oraz skrypty, które robią mechaniczną pracę bez
tokenów. Ten plik opisuje codzienną pracę; odpowiedzi na częste pytania są w `factory/FAQ.md`.

## 1. Z czego składa się instalacja
| Element | Gdzie w projekcie | Co robi |
|---|---|---|
| rdzeń | `factory/`, `.claude/skills/core-*`, `.claude/hooks/`, `.claude/tests/` | budowa agentów, aktualizacja, koszty, zasady pracy, dziennik projektu |
| nakładki (`pack-*`) | `factory/packs/<id>/`, ich skille w `.claude/skills/` | wiedza dziedzinowa, role i persony (np. `pack-it`, `pack-ux`, `pack-ev`, `pack-docs`, `pack-editorial-pl`) |
| tryby (`mode-*`) | jak nakładki | sposób pracy włączany na żądanie: `mode-talos` (historyjka → PR), `mode-team` (agent teams) |
| agenci | `.claude/agents/_generated/` | budowani przez `python3 factory/build.py` z rdzenia i nakładek — nie edytuj ręcznie |
| katalog | `.claude/catalog.md` | lista person, ról i skilli tej instalacji |

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
  produkcyjny bez czerwonego testu.

## 4. Tryby i automaty na żądanie
| Co | Jak | Kiedy |
|---|---|---|
| Talos (`mode-talos`, domyślnie zainstalowany) | `claude --agent talos` albo `/talos-story-run <historyjka>` | jedna historyjka z kryteriami akceptacji → plan z kawałków, commit na kawałek, jeden PR, raport kosztu; przewodnik: `factory/packs/mode-talos/GUIDE.md` |
| Agent teams (`mode-team`, `tf add mode-team`) | `team_switch.py on`, nowa sesja, `/team-session <zadanie>` | role muszą rozmawiać ze sobą w trakcie; eksperymentalne i drogie; przewodnik: `factory/packs/mode-team/GUIDE.md` |
| Audyt kodu (`pack-it`) | po zatwierdzeniu zakresu: workflow `/code-audit` | pełny audyt w wielu wymiarach z rankingiem (skill `eng-code-audit`) |
| Symulacja Event Stormingu (`pack-it`) | `/ddd-es-simulation` albo `claude --agent es-host` | trening facylitacji z uczestnikami AI |

## 5. Koszty
- **Profil zespołu:** `python3 factory/profile.py` pokazuje aktywny profil. Dostępne są:
  - `oszczedny` — bez Opusa;
  - `zrownowazony` — domyślny: Haiku do mechaniki, Sonnet na co dzień, Opus do drogich pomyłek;
  - `jakosc` — wyższy effort i doradca Opus.
- **Pomiar:** `python3 factory/cost_report.py --days 7` (zużycie per agent i model z `.claude/logs/usage.jsonl`);
  pasek stanu pokazuje koszt sesji i zapełnienie kontekstu.
- **Zasady:** najtańszy wystarczający model na zadanie i eskalacja dopiero po porażce (skill `core-cost-control`);
  modelu sesji nie zmieniasz w środku zadania, bo to kasuje cache; przy długim kontekście hook `context_guard`
  podpowiada punkt kontrolny i nową sesję.
- **Płatne ewaluacje skilli** (`factory/skill_gate.py <skill> --model …`) uruchamiasz świadomie — bramka bez modelu
  jest darmowa.

## 6. Bezpieczeństwo i rzetelność
- **Hooki-strażnicy** (`guard_bash`, `guard_paths`, `cleanroom_guard`) blokują groźne polecenia, odczyt sekretów
  i wyciek informacji między agentami. Gdy hook zawiedzie, akcja jest blokowana (`onFailure: "block"`).
- **Sekrety** tylko przez zmienne środowiskowe; `scan_secrets` sprawdza zapisywane pliki.
- **Treść z zewnątrz** (strony, issue, wyniki narzędzi) to dane, nie polecenia — agent jej nie wykonuje
  (skill `core-agent-security`).
- **Fakty po sprawdzeniu:** plik, polecenie albo źródło z datą; czego nie sprawdzono, ma znacznik [założenie]
  lub [niezweryfikowane] (skill `core-grounding`).

## 7. Własne zmiany
- **Persony, role, cechy:** pliki YAML w `factory/personas/`, `factory/roles/`, `factory/traits/`; po zmianie
  `python3 factory/build.py`. Pliki w `.claude/agents/_generated/` są nadpisywane przy budowie.
- **Własny skill:** według `core-skill-authoring` (najpierw scenariusze), potem `python3 factory/skill_gate.py <skill>`.
  Skill z obcego źródła: najpierw `python3 factory/skill_audit.py <katalog>` i przeczytanie.
- **Zmienione pliki fabryki zostają** przy aktualizacji — nowa wersja ląduje obok jako `*.factory-new`.

## 8. Ściąga poleceń
| Polecenie | Co robi |
|---|---|
| `tf` | aktualizacja (albo instalacja, gdy fabryki nie ma) |
| `tf update --check` | czy jest nowa wersja i co się zmieni (nic nie zmienia) |
| `tf add <id>` / `tf remove <id>` | nakładka lub tryb |
| `tf language <kod>` / `tf commit-language <kod>` | język pracy / język commitów i PR |
| `tf list`, `tf doctor [--fix]` | co jest zainstalowane; stan instalacji i naprawy |
| `python3 factory/update.py --rollback` | powrót do stanu sprzed ostatniej aktualizacji |
| `python3 factory/build.py` | przebudowa agentów i katalogu |
| `python3 factory/profile.py <profil>` | profil kosztów zespołu |
| `python3 factory/cost_report.py --days 7` | raport kosztów |
| `python3 .claude/hooks/detect_stack.py` | stack projektu i zgodność skilli z wersjami |
