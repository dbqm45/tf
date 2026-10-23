# pdi — decyzje w jednym źródle

Tryb `mode-pdi` dokłada do fabryki zapis decyzji zgodny z rejestrem pdi. Bez niego fabryka działa jak dotąd.
Instalacja: `tf add mode-pdi`, usunięcie: `tf remove mode-pdi`.

## Co daje
- **Dziennik zmiany:** `python3 .claude/skills/pdi-decisions/scripts/decision_record.py change new CHG-12 --source PRB-34`
  tworzy `docs/project/changes/CHG-12/` z `intent.md`, `plan.md` i `decisions.md`; nagłówki są zgodne z kontraktem
  pdi 0.3.0 (`contract/change.schema.json`). `decision_record.py check` sprawdza nagłówki.
- **Decyzje:** skill `pdi-decisions` (wspólny dla wszystkich person) po zatwierdzeniu szkicu przez człowieka zapisuje
  decyzję o zmianie w `decisions.md` (`decision add`) i — gdy serwer MCP pdi jest podłączony — w rejestrze pdi
  (`record_decision`), który nadaje numer `DEC-n` (`decision mark`). Niewysłane: `decision pending`; wszystkie
  w JSON: `decision export`.

## Warunek: serwer MCP pdi
Zapis do rejestru działa tylko wtedy, gdy w sesji jest serwer MCP `pdi` (narzędzia `record_decision`,
`find_decisions`, `get_decision`, `supersede_decision`). Instalację opisuje repo pdi
(`integrations/claude-code/README.md`; rejestracja `claude mcp add --scope user pdi …`). Bez niego decyzje zostają w `decisions.md` z pustym `id` i `wyslano: nie` — nic nie ginie.

## Czego nie zmienia
Rdzeń fabryki, dziennik faz projektu (`docs/project/0N-*`), inne nakładki i ustawienia — bez zmian. Projekt bez
katalogu `docs/project/changes/` nie widzi różnicy.

## Polecenia
`decision_record.py change new|check`, `decision add|pending|mark|export` — pełny opis: `--help` skryptu.
