# Plan: target `managed-agents` w `build.py`

Data: 2026-10-24 · Status: zrobione (kroki 1–4), PR w toku · Gałąź: `claude/great-hypatia-angvam`

## TL;DR
`build.py` generuje dziś agentów tylko dla Claude Code (`.claude/agents/_generated/`). Nowy target `managed-agents`
(włączany w `.claude/factory-settings.json`: `"targets": ["claude", "managed-agents"]`) generuje te same persony,
wykonawców i agentów wspólnych jako pliki dla `ant apply` (Claude Managed Agents): `managed-agents/agents/*.md`,
`managed-agents/environments/default.yaml`, `managed-agents/README.md`. Skille nie są kopiowane — agent wskazuje
katalogi `.claude/skills/<skill>` ścieżką względną, a `ant apply` wgrywa je jako skille własne.

## Format docelowy (źródło: skill `claude-api` 2.1.310, `shared/anthropic-cli.md`, `managed-agents-core.md`,
`managed-agents-tools.md`, `managed-agents-multiagent.md`; odczyt 2026-10-24)
- Agent = plik `.md`: frontmatter YAML = konfiguracja (`name`, `description`, `model`, `tools`, `skills`,
  `multiagent`, `metadata`), treść Markdown = prompt systemowy.
- `model`: identyfikator albo obiekt `{id, effort}`.
- Narzędzia: `agent_toolset_20260401` z `default_config` i `configs` (`bash`, `read`, `write`, `edit`, `glob`,
  `grep`, `web_fetch`, `web_search`); polityka `auto`.
- Skille: ścieżki do katalogów ze `SKILL.md` względem pliku agenta; maks. 500 skilli na sesję (wszyscy agenci).
- Podagenci: `multiagent: {type: multiagent_20261001, subagents: {type: enabled, predefined_agents: [ścieżki]},
  workflows: ...}` tylko na koordynatorze; maks. 20 pozycji, jeden poziom (członek nie ma własnego `multiagent`).
  Ścieżki plików w `predefined_agents` wymagają `ant` ≥ 1.40.0.
- `ant apply` zapisuje `claude-lock.json` — fabryka go nie dotyka.

## Mapowanie
| Fabryka | Managed Agents |
|---|---|
| persona (orkiestrator) | `agents/<persona>.md`, `multiagent` z rosterem: wykonawcy, agenci wspólni, konsultanci, `extra_agents` (w tej kolejności, do 20; nadmiar → ostrzeżenie) |
| wykonawca `<persona>-<rola>` | `agents/<persona>-<rola>.md`, bez `multiagent` |
| agent wspólny (scout, researcher…) | `agents/<nazwa>.md` |
| konsultant nakładki | `agents/<nazwa>.md` |
| tier → model | `haiku`→`claude-haiku-5-5`, `sonnet`→`claude-sonnet-5-5`, `opus`→`claude-opus-5-5`, `fable`→`claude-fable-5-1`, `claude-…` bez zmian, `inherit`→`claude-opus-5-5`; mapa nadpisywalna `managed_agents.models` w `config.yaml`; `effort` z tieru |
| narzędzia Claude Code | `Read/Grep/Glob/Edit/Write/Bash/WebFetch/WebSearch` → narzędzia toolsetu; reszta (`Skill`, `Agent`, …) bez odpowiednika |
| skille persony/roli | `skills: [../../.claude/skills/<s>, …]` |
| prompt | ten sam co dla Claude Code (bez frontmattera i komentarza HTML) + sekcja „Środowisko Managed Agents” (skille ładują się same, delegowanie przez podagentów z rosteru, hooki fabryki nie działają — testy i bramki uruchamiasz sam, repozytorium montowane jako zasób sesji) |
| workflows | domyślnie wyłączone (koszt; włączenie świadomą decyzją, opis w README) |

## Kroki (TDD)
1. Test `core/tests/test_target_managed.py` (czerwony): mapowanie modelu, toolset, ścieżki skilli, roster z limitem,
   frontmatter parsowalny YAML-em, prompt bez frontmattera, integracja: render całości w workspace — każdy plik
   agenta ma poprawny frontmatter, skille istnieją, roster ≤ 20, członkowie rosteru bez `multiagent`, < 500 skilli.
2. Moduł `core/factory/target_managed.py` (render czysty, bez zapisu).
3. `build.py`: `TARGETS["managed-agents"]`, zapis w `cmd_build` (usuwa tylko własne wygenerowane pliki, nie rusza
   `claude-lock.json` ani plików użytkownika), kontrola aktualności i błędów w `validate`.
4. `config.yaml` (`managed_agents.models`, komentarz o targetach), `PUBLIC_API.md`, `docs/todo.md`.
5. Bramki: testy rdzenia, `workspace.py check`, `refs`, testy główne, PR.

## Wgranie tylko poleceniem (decyzja człowieka, 2026-10-24)
`build.py` i `build.py check` tylko piszą i porównują pliki lokalne. Na konto wysyła wyłącznie
`python3 factory/build.py managed-apply --yes`; bez `--yes` to sam plan (`ant apply --dry-run`). Test AP-5 pilnuje,
że render i zapis nie uruchamiają procesów.

## Poza zakresem
Sesje, vaulty, wdrożenia cykliczne, `ant apply` na koncie (płatne, za zgodą człowieka), środowisko z repozytorium
GitHub (opis w README, bez generowania).

## Wynik (2026-10-24)
- `core/tests/test_target_managed.py`: 28/28 (najpierw czerwone).
- Workspace pack-it z włączonym targetem: 79 agentów; `ant apply --dry-run agents environments` (ant 2.3.0 zbudowany
  ze źródeł, bez danych logowania): plan 235 zasobów (155 skilli, 79 agentów, środowisko), bez błędów. Na koncie
  nic nie wgrano.
- Maja (dyspozytor) ma 34 agentów — roster obcięty do 20, ostrzeżenie w `build.py check`.

## Przekazanie
Wgranie na konto (`ant apply` bez `--dry-run`) i sesja próbna — tylko za zgodą człowieka (koszt).
