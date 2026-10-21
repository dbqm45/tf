# Nakładki i tryby jako pluginy Claude Code — analiza

Stan: 2026-10-21. Fakty o pluginach z dokumentacji code.claude.com (odczyt 2026-10-21, strony `/en/plugins/*`,
`/en/sub-agents`, `/en/skills`, `/en/hooks`, `/en/plugin-evals`). Czego dokumentacja nie mówi, oznaczam
[niezweryfikowane]. Dokument służy decyzji człowieka; kodu jeszcze nie ma.

## Wniosek
- **Tryb `mode-talos` — tak, jako eksport.** Mieści się w modelu pluginu prawie bez strat. Potrzebne są dwie małe
  zmiany w samym trybie, użyteczne także bez pluginu.
- **Nakładki — na razie nie w całości.** Persony i role powstają w projekcie z rdzenia i wszystkich nakładek naraz
  (`build.py`). Plugin to pliki statyczne, więc to złożenie by się rozpadło. Wykonalny jest eksport samych skilli
  nakładki („biblioteka skilli”), z ograniczeniami opisanymi niżej.
- **Rdzeń — nie.** Plugin nie dostarcza `CLAUDE.md`, reguł ani uprawnień, a rdzeń z nich składa się w dużej części.
- **Źródło pozostaje jedno.** Plugin byłby artefaktem budowanym z `modes/` i `packs/` narzędziem w `tools/`, nie
  drugą kopią do utrzymania. Instalator `tf` zostaje podstawową drogą instalacji.

## Co plugin umie, a czego nie (fakty)
| Obszar | Plugin | Źródło |
|---|---|---|
| Składniki | `skills/`, `agents/`, `hooks/hooks.json`, `.mcp.json`, `bin/` (na `PATH` Bash), `settings.json`, `output-styles/`, `workflows/`, manifest `.claude-plugin/plugin.json` (wymagane tylko `name`) | `/en/plugins/manifest-reference` |
| Agenci | ignorowane pola: `permissionMode`, `hooks`, `mcpServers`, `initialPrompt`; działają m.in. `model`, `effort`, `maxTurns`, `tools`, `disallowedTools`, `skills`, `omitClaudeMd`, `isolation` | `/en/plugins/components#agents` |
| Agent sesji głównej | `claude --agent talos` znajduje agenta z pluginu po samej nazwie (`<plugin>:talos` przy kolizji); `settings.json` pluginu może ustawić `agent` | `/en/sub-agents`, `/en/plugins/components#default-settings` |
| Ustawienia | działają tylko `agent` i `subagentStatusLine`, reszta (w tym `permissions`) jest odrzucana | `/en/plugins/components#default-settings` |
| Uprawnienia do skryptu | skill może zatwierdzić własny skrypt: `allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/… *)` | `/en/skills` |
| `CLAUDE.md` | `CLAUDE.md` w pluginie nie jest wczytywany; instrukcje tylko przez skill | `/en/plugins/manifest-reference` |
| Hooki | `hooks/hooks.json` w kształcie `hooks` z `settings.json`; rejestrowane przy załadowaniu pluginu, blokują jak każde inne (exit 2, `onFailure: "block"`); dostają `CLAUDE_PLUGIN_ROOT`, `CLAUDE_PLUGIN_DATA` | `/en/plugins/components#hooks`, `/en/hooks` |
| Pliki | instalacja kopiuje plugin do `~/.claude/plugins/cache/<marketplace>/<plugin>/<wersja>/`; pliki spoza katalogu pluginu (`../shared`) nie są kopiowane; stan trwały w `${CLAUDE_PLUGIN_DATA}` | `/en/plugins/loading` |
| Nazwy | wszystko pod przestrzenią `<plugin>:`; skill także jako `/<nazwa>`, jeśli nie ma kolizji; nazwy zaczynające się od `claude-`, `anthropic-`, `cc-plugin-` są błędem walidacji | `/en/plugins/manifest-reference`, `/en/skills` |
| Zależności i wersje | `dependencies` z zakresem SemVer (`^2.0`, `>=1.4`), rozwiązywane po tagach git `<plugin>--v<wersja>` (`claude plugin tag --push`) | `/en/plugins/dependencies` |
| Zespół | `extraKnownMarketplaces` i `enabledPlugins` w `.claude/settings.json` repozytorium; działa tylko w zaufanym folderze; plugin z zewnętrznego źródła każdy instaluje sam (`claude plugin install … --scope project`) | `/en/plugins/org` |
| Sesje w chmurze | nie ładują pluginów zainstalowanych lokalnie ani włączonych w `.claude/settings.json` repozytorium | `/en/plugins/install` |
| Sprawdzenie | `claude plugin validate <katalog> --strict` (bez modelu); `claude plugin eval` — płatne wywołania modelu | `/en/plugins/cli-reference`, `/en/plugin-evals` |

## Co tracimy, element po elemencie
### `mode-talos`
| Element trybu | W pluginie | Zmiana |
|---|---|---|
| agent `talos` (`main_only`, lista `Agent(…)`) | działa: `claude --agent talos` | brak |
| skill `talos-story-run` (`disable-model-invocation`) | działa: `/talos-story-run` | brak |
| ścieżka `.claude/skills/talos-story-run/scripts/run_report.py` | w pluginie inna ścieżka | skill i agent wskazują skrypt przez `${CLAUDE_SKILL_DIR}/scripts/run_report.py`; agent czyta skill — ścieżkę w agencie podstawia eksport |
| uprawnienie z `settings.json` trybu | odrzucane | `allowed-tools` w skillu; z `claude --agent talos` skill nie jest wywoływany, więc pierwszy raz pojawi się pytanie o zgodę [niezweryfikowane: czy `allowed-tools` działa przy odczycie skilla narzędziem Read — raczej nie] |
| ceny z `factory/config.yaml` | pliku nie ma bez fabryki | `run_report.py` z zapasowym cennikiem przy skrypcie |
| `.claude/runs/` ignorowane przez rdzeń | bez rdzenia nikt go nie ignoruje | `run_report.py start` zakłada `.claude/runs/.gitignore` z `*` — działa wszędzie |
| wykonawcy `scout`, `scope-reviewer`, `quick-fixer`, `architect`, `security-reviewer`, `researcher` | to agenci rdzenia | wariant A: plugin wymaga zainstalowanej fabryki; wariant B: plugin zawiera kopie tych agentów (wtedy nazwy `<plugin>:scout` itd.) [niezweryfikowane: czy `Agent(…)` przyjmuje nazwy z przestrzeni pluginu] |
| hooki rdzenia (TDD, ochrona ścieżek) | bez fabryki ich nie ma | Talos bez fabryki traci straż TDD z hooka; zostaje TDD z treści skilla |

### Nakładki (`pack-*`)
- **Persony i role:** w projekcie powstają z ról, cech, umowy pracy, kontraktu raportu, tabeli konsultantów i routingu
  wszystkich zainstalowanych nakładek, w języku pracy projektu. Plugin mógłby nieść tylko jedno zamrożone złożenie
  (np. rdzeń + ta nakładka, język `pl`). To dokładnie to, czego `build.py` unika.
- **Skille:** przenoszą się dobrze (zwykły `SKILL.md` z `references/`, `scripts/`). Tracimy:
  - widoczność skilli według stacku projektu (`skillOverrides`, `detect_stack.py`);
  - podpowiedzi hooka `skill_hint`;
  - bramkę jakości i rejestr z wersją;
  - odwołania do skilli innych nakładek, sprawdzane dziś przez `workspace.py refs`.
- **Koszt kontekstu:** opis każdego skilla z pluginu jest w kontekście w każdej turze, a w `pack-it` jest 124 skille.
  Fabryka ogranicza to widocznością według stacku, plugin — nie.

### Rdzeń
- Sekcja w `CLAUDE.md`, uprawnienia, `onFailure` przy hookach w ustawieniach projektu, `factory/` (budowa, instalacja,
  aktualizacja, migracje), dziennik `docs/project/` — plugin nie ma na to miejsca.
- Same hooki dałoby się przenieść, ale część czyta konfigurację projektu (`cleanroom.json`, ustawienia), a plugin
  włączony dla użytkownika działa w każdym repozytorium.

## Ryzyka i pytania do decyzji
1. **Publiczne repozytorium.** Marketplace to plik `.claude-plugin/marketplace.json` z nazwami i opisami pluginów.
   W publicznym repo `tf` ujawnia, czym jest projekt — podobnie jak README, którego na razie nie chcesz. Opcje:
   osobne prywatne repo na marketplace albo eksport tylko lokalnie (`--plugin-dir`), bez publikacji.
2. **Talos z fabryką czy samodzielny** (wariant A czy B wyżej). A jest prostszy i bez kopii agentów; B daje Talosa
   każdemu, ale dubluje 6 agentów rdzenia.
3. **Nazwa pluginu:** np. `tf-talos` (nie może zaczynać się od `claude-`).
4. **Sesje w chmurze nie ładują pluginów z ustawień repozytorium** — tam nadal potrzebna jest instalacja `tf`.

## Proponowane kroki (po decyzji)
1. **Samodzielność `mode-talos`** (przydatna też bez pluginu):
   - zapasowy cennik w `run_report.py`;
   - `.claude/runs/.gitignore` zakładany przez skrypt;
   - ścieżka skryptu względem katalogu skilla.
2. **`tools/plugin_export.py --mode mode-talos`:** buduje `dist/plugins/<id>/` (manifest, agent, skill), sprawdza
   eksport przez `claude plugin validate --strict` i dodaje test do CI. Ewaluacje `claude plugin eval` są płatne,
   więc tylko za zgodą.
3. **Publikacja** według decyzji z punktu 1 ryzyk.
4. **Później, osobno:** eksport samych skilli nakładki, z ostrzeżeniem o koszcie kontekstu przy dużych nakładkach.
