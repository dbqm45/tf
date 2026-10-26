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

- **Fazy uruchamiane przez pdi (F4):** po decyzji na bramce skrzynka pdi wywołuje w repo workflow `sdlc-phase.yml`
  (`python3 .claude/skills/pdi-decisions/scripts/phase_run.py workflow install`). Workflow zapisuje decyzję w
  `decisions.md` (`decision_record.py decision gate`), uruchamia personę fazy bez interakcji (`phase_run.py run`:
  `intent` — maja, `requirements` — ewa, `architecture` — tomasz, `design` — natalia, `delivery` — talos; inna
  persona w `.claude/pdi-phases.json`), otwiera PR fazy na gałęzi `pdi/CHG-n-<faza>` i wysyła do pdi prośbę o
  następną bramkę (`phase_run.py gate request`, podpisane `gate.requested` na `PDI_EVENTS_URL/events/tf`).
  Potrzebne: sekrety `ANTHROPIC_API_KEY` i `PDI_TF_SIGNING_SECRET` (ten sam w odbiorniku pdi), zmienna
  `PDI_EVENTS_URL`; w pdi `PDI_DISPATCH_REPO` wskazuje to repo. Zatwierdzając bramkę, scal też PR fazy — następna
  faza zaczyna od gałęzi domyślnej. Każde uruchomienie kosztuje (model); limit fazy daje `PDI_PHASE_BUDGET_USD` w pdi.
  Przyjęcie zgłoszenia w pdi (F3) uruchamia fazę `intent` z wejściami `source` (PRB) i `problem` (treść zgłoszenia):
  workflow zakłada `docs/project/changes/CHG-n/` ze źródłem i dniem zgłoszenia (`source_reported_at`, od niego
  ShipScope liczy lead time od zgłoszenia), a persona pisze `intent.md` z problemu zgłaszającego.

- **Pasma kontrolne z ShipScope (F5):** `metric_watch.py check` czyta dzienny szereg PROD z API usług ShipScope
  (rollbacki, wdrożenia nieudane, lead time, liczba wdrożeń), liczy pasma `control_band.py` i przy punkcie poza 3σ
  z ostatnich dni wysyła do pdi `metric.breached` (`--send`). Codziennie: `metric_watch.py workflow install`
  (`metric-watch.yml`). Potrzebne: sekrety `SHIPSCOPE_TOKEN` (token usługi z ShipScope) i `PDI_TF_SIGNING_SECRET`,
  zmienne `SHIPSCOPE_URL` i `PDI_EVENTS_URL`; metryki i linia bazowa w `.claude/pdi-metrics.json`. Bez modelu, bez
  kosztu. pdi musi przyjmować `metric.breached` od tf (zgłoszenia, F3) — wcześniej odpowie 400.

## Warunek: serwer MCP pdi
Zapis do rejestru działa tylko wtedy, gdy w sesji jest serwer MCP `pdi` (narzędzia `record_decision`,
`find_decisions`, `get_decision`, `supersede_decision`). Instalację opisuje repo pdi
(`integrations/claude-code/README.md`; rejestracja `claude mcp add --scope user pdi …`). Bez niego decyzje zostają w `decisions.md` z pustym `id` i `wyslano: nie` — nic nie ginie.

## Czego nie zmienia
Rdzeń fabryki, dziennik faz projektu (`docs/project/0N-*`), inne nakładki i ustawienia — bez zmian. Projekt bez
katalogu `docs/project/changes/` nie widzi różnicy.

## Polecenia
`decision_record.py change new|check`, `decision add|pending|mark|export|gate`, `phase_run.py prompt|run|gate
request|workflow install`, `metric_watch.py check|workflow install` — pełny opis: `--help` skryptów.
