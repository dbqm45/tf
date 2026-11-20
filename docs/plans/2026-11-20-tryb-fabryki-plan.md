# Tryb fabryki: fabryka działa tylko w sesji fabryki

Data: 2026-11-20. Prośba właściciela: gdy pracujesz zwykłym Claude Code, nic z fabryki nie może działać:
- żaden hook fabryki się nie uruchamia;
- skille, agenci i reguły fabryki nie przykrywają Twoich własnych skilli;
- pasek stanu fabryki się nie pokazuje.

Fabryka działa wtedy, gdy ją uruchamiasz. Decyzje właściciela:
- druga droga: launcher lokalnie, a w chmurze włączenie w ustawieniach środowiska;
- zgoda na sprawdzenie flag;
- bez przełączania trybu w trakcie sesji (`/tf on|off` odłożone).

## Stan dziś (`main` 1e65c4e, wersja 20.6.0)

W każdej sesji w katalogu projektu, także zwykłej, działają:
- **hooki fabryki:** wszystkie ~30 wpisów z `core/settings.json` w `.claude/settings.local.json` (instalacja prywatna)
  albo w `.claude/settings.json` (zespołowa);
- **pozostałe ustawienia fabryki:** zmienne `env` (model podagentów, limity), pasek stanu oraz reguły `deny` i `ask`;
- **skille fabryki:** 22 z rdzenia i do kilkuset z nakładek, w `.claude/skills/` razem z Twoimi. Ich opisy są
  w kontekście każdej sesji i konkurują z Twoimi przy wyborze skilla;
- **agenci fabryki** w `.claude/agents/_generated/`;
- **reguły fabryki** w bloku `<!-- team-factory:begin -->` w `CLAUDE.md`.

Instalator nie nadpisuje plików, których fabryka nie zainstalowała. Twoje skille zostają, ale działają obok fabryki.

## Co sprawdziłem (2026-11-20, Claude Code 2.1.325, model haiku, łącznie ok. 0,06 USD)

| Sprawdzenie | Wynik |
|---|---|
| hook z pliku podanego w `--settings` | działa tylko w sesji z flagą (zwykła sesja: 0 wywołań, z flagą: 1) |
| skill z lokalnej wtyczki (`--plugin-dir`) | widoczny tylko z flagą, jako `<wtyczka>:<skill>`; działa |
| Twój skill z `.claude/skills/` przy wtyczce | widoczny obok, bez kolizji nazw |
| reguły z `--append-system-prompt-file` | model je zna tylko z flagą |
| hook `SessionStart` z wtyczki z `additionalContext` | treść trafia do kontekstu, więc reguły fabryki może podać hook wtyczki |
| hook `PreToolUse` z wtyczki (`${CLAUDE_PLUGIN_ROOT}`) | działa |
| agent z wtyczki | rejestruje się jako `tf:<agent>`; skill wołający `echo-checker` trafił do `tf:echo-checker` |
| `/tf` przy wtyczce `tf` ze skillem `tf` | działa bez przedrostka; `/run` zderzył się z wbudowanym skillem (stąd nazwa `tf`) |
| wtyczka włączona przez ustawienia (`extraKnownMarketplaces` z katalogiem i `enabledPlugins`) | działa — droga dla chmury |

Niesprawdzone:
- czy ten sam wpis działa z `~/.claude/settings.json` w kontenerze chmurowym tak samo jak z `--settings`
  [założenie: to ten sam mechanizm ustawień];
- czy wtyczka może sama ustawić `env`, pasek stanu i uprawnienia [niezweryfikowane]. Dlatego zostają w osobnym
  pliku ustawień sesji fabryki.

## Docelowy układ

- **`.tf/plugin/`: lokalna wtyczka `tf`.** Zawiera:
  - `skills/`: skille rdzenia i nakładek;
  - `agents/`: generowani agenci, dotąd `.claude/agents/_generated/`;
  - `hooks/hooks.json` i skrypty hooków, dotąd `.claude/hooks/`, z `${CLAUDE_PLUGIN_ROOT}` zamiast
    `${CLAUDE_PROJECT_DIR}/.claude/hooks`;
  - `RULES.md`: reguły fabryki, dotąd blok w `CLAUDE.md`, podawane przez hook `SessionStart`;
  - `.claude-plugin/plugin.json`.
- **`.tf/plugin/session-settings.json`:** `env`, pasek stanu i uprawnienia fabryki (`allow`, `ask`, `deny`).
- **`.tf/marketplace/`:** katalogowy marketplace z jedną wtyczką, dla chmury.
- **Zostaje bez zmian:** Twoje `.claude/skills/`, `.claude/agents/`, `.claude/settings*.json` i `CLAUDE.md`.
  Instalator usuwa z nich tylko to, co sam tam kiedyś wpisał: wpisy hooków fabryki, jej `env`, pasek stanu
  i blok w `CLAUDE.md`. Wszystko trafia do `.tf/backup/`, a `update.py --rollback` przywraca poprzedni stan.

**Jak uruchamiasz fabrykę:**
- **Lokalnie:** `tf code [argumenty claude]`, czyli `claude --plugin-dir .tf/plugin --settings
  .tf/plugin/session-settings.json …`, np. `tf code --continue`. Zwykły `claude` nie widzi niczego z fabryki.
- **W chmurze:** `tf cloud-setup` drukuje skrypt startowy środowiska. Skrypt wpisuje do `~/.claude/settings.json`
  kontenera marketplace, włączenie wtyczki i ustawienia sesji fabryki. Środowisko z tym skryptem to środowisko
  fabryki, a bez niego zwykłe.
- **Bez nadzoru i pomiary:** `tf work --once` i `e0_run.py` wołają agenta z tymi samymi flagami.

**Ścieżki w treści:** źródło fabryki dalej używa `.claude/skills/…` i `.claude/hooks/…`. To 532 miejsca w 256
plikach, więc nie przepisuję źródła. Instalator przepisuje ścieżki w instalowanych plikach tekstowych, tak jak
dziś `retarget()` robi to dla testów:
- `.claude/skills/` → `.tf/plugin/skills/`;
- `.claude/hooks/` → `.tf/plugin/hooks/`;
- `.claude/agents/_generated/` → `.tf/plugin/agents/`.

Hooki, które przeglądają skille (`skill_hint`, `skill_change_guard`, `log_usage`), czytają oba miejsca: skille
fabryki i Twoje.

## Kawałki (każdy osobny PR, TDD)

| # | Co | Testy |
|---|---|---|
| T1 | instalator: opcja `--layout plugin` buduje `.tf/plugin/` (skille, agenci, hooki, `RULES.md`, `session-settings.json`, `plugin.json`) i przepisuje ścieżki; domyślnie układ jak dziś | instalacja do katalogu tymczasowego: w `.claude/` nie ma nic z fabryki, a `.tf/plugin/` ma komplet; pełne `workspace.py check` na układzie wtyczki |
| T2 | `tf code`: launcher z flagami; `tf doctor` sprawdza układ i mówi, jak uruchomić fabrykę | test polecenia i jego argumentów, bez wywołań modelu |
| T3 | hooki i skrypty czytają skille z obu miejsc; reguły z `RULES.md` przez hook `SessionStart` | testy hooków na obu układach |
| T4 | `tf work`, `e0_run.py` i podgląd na nowym układzie; `tf cloud-setup` | testy `tf work` z fałszywym agentem; sprawdzenie flag w poleceniu |
| T5 | przełączenie domyślnego układu na wtyczkę; `update.py` przenosi istniejące instalacje (kopia w `.tf/backup/`, powrót `--rollback`) | aktualizacja instalacji 20.6.0: Twoje skille i `CLAUDE.md` bez zmian poza blokiem fabryki; powrót przywraca stan |
| T6 | płatny pomiar S1–S4 na nowym układzie (zgoda właściciela przed uruchomieniem) | akceptacja i koszt jak w pomiarze po kroku H |

Do T5 nic się nie zmienia u użytkowników, bo nowy układ jest tylko opcją.

## Ryzyka

- **Nazwy agentów z przedrostkiem `tf:`.** Treść skilli mówi „scope-reviewer”. W próbie model sam wybrał
  `tf:echo-checker`, ale w pętli trzeba to potwierdzić pomiarem (T6). Zapasowo instalator przepisze nazwy agentów
  w treści na `tf:…`.
- **Ścieżki przepisywane przy instalacji.** Pełne `workspace.py check` na układzie wtyczki (T1) jest warunkiem
  scalenia.
- **Instalacja zespołowa (`--shared`).** Zespół commituje `.tf/plugin/` i każdy uruchamia `tf code`. Kto uruchomi
  zwykły `claude`, pracuje bez fabryki, zgodnie z założeniem.
