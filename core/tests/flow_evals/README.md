# Flow evals — evale przebiegu fazy

Zestaw prawdziwych zadań, który bramkuje zmianę modelu/skilla/persony/promptu fazy. Źródło: pdi
`docs/plan-zespol-jednoosobowy.md` §8.3 N5, DZ13.

Zasada: zmiana w `modes/mode-pdi/**`, `core/skills/**`, `phase_run.py` albo w tym katalogu nie wchodzi, dopóki
raport evali nie pokaże **wyniku i kosztu** porównanego z poprzednim przebiegiem. CI (bez sekretu) sprawdza
tylko schemat (`--validate`); pełny przebieg puszcza człowiek lokalnie i w PR ustawia sekret.

## Uruchomienie

```
python3 tools/workspace.py flow-evals --validate                 # bez modelu, sprawdza schematy zadań i rubryki
python3 tools/workspace.py flow-evals --ids N5-sdlc-proba-CHG1-intent
python3 tools/workspace.py flow-evals --all --budget-usd 15 --yes
python3 tools/workspace.py flow-evals --all --baseline previous --save-baseline
```

Bez `--yes` runner wypisze prognozę kosztu z `COST_GUESS` i poprosi o potwierdzenie.

## Format zadania (`*.json`)

```json
{
  "id": "N5-<repo>-<CHG>-<phase>[-<attempt>]",
  "repo": "sdlc-proba|sprintdeck|synth",
  "product_sha": "sha1 commitu produktu albo 'any'",
  "phase": "intent|requirements|architecture|design|delivery",
  "change": "CHG-1",
  "budget_usd": 1.0,
  "type": "happy|negative|regression",
  "before_dir": "fixtures/<repo>/<CHG>/<slug>/",
  "expect": {
    "status": "done|waiting_gate|failed",
    "error": "any|repeated_question|<prefix>",
    "contains_detail": ["<tekst>", "..."],
    "max_cost_usd": 0.5,
    "max_duration_s": 180,
    "min_files_read": 0,
    "max_permission_denials": 0
  },
  "judge": {
    "run": true,
    "rubric": "rubrics/<phase>.md",
    "requirements": ["<wymagania do oceny przez sędziego>"]
  },
  "notes": "<kontekst, np. PRB-29>"
}
```

Pola `expect.*` są deterministyczne (`checks`); `judge.*` włącza N17 (rubryka + requirements).
Fixtury (`fixtures/`) są **read-only** — runner kopiuje je do katalogu tymczasowego przed uruchomieniem.

## Rubryki (`rubrics/<phase>.md`)

Trzy osie oceny, każda z przykładem per poziom 1–5:
1. **correctness** — zgodność z faktami z `decisions.md` zmiany i artefaktów poprzednich faz
2. **decision_adherence** — artefakt odwołuje się do wiążących decyzji (CHG-n/Dk)
3. **style** — czytelny, bez wypełniania; **kontrola długości**: > 1,8× średniej bazowej → auto -1

Reguły sędziego N17 (pdi §8.3, wiersz 368):
- oceniany model nigdy nie jest sędzią (`judge_model("auto", evaluated)` wymusza inną rodzinę; tf #127)
- obie kolejności przy porównaniu dwóch wyjść, różnica w raporcie
- `temperature: 0` wszędzie, gdzie API przyjmuje
- zgodność z oceną człowieka na próbce w raporcie (Cohen's κ)

## Budżet (`budget.json`)

```json
{
  "budget_usd": 15,
  "per_task_budget_usd": 1.0,
  "fail_on_pass_drop_pct": 5,
  "fail_on_cost_rise_pct": 20,
  "judge_kappa_min": 0.4,
  "judge_model_haiku": "claude-haiku-4-5-20251001",
  "judge_model_sonnet": "claude-sonnet-4-6"
}
```

## Czego **NIE** mierzymy

- Izolacji sieci (to mierzy Z8a — `src/pdi/phase_sandbox.py` w pdi).
- Jakości cięć Talosa (to mierzą skill evals `talos-story-run` i ci_for_sdlc Z8c-2).
- Wartości biznesowej artefaktu — mierzymy zgodność z decyzjami zmiany, nie trafność pomysłu.

## Źródła (odczyt 2026-11-06)

- Claude Code CLI: https://code.claude.com/docs/en/cli-reference, Agent SDK stream-json, Subagents, Settings
- Anthropic Messages API (temperature 0, tool_use): https://platform.claude.com/docs/en/api/messages
- `run_skill_evals.py:judge_model` — `JUDGE_FOR = {haiku: sonnet, sonnet: haiku, opus: sonnet}` (tf #127)
- `phase_run.py:cmd_run` — kształt pola `out` (PRB-28 2026-11-06)
- pdi `docs/plan-zespol-jednoosobowy.md` §8.3 N5, N17; `docs/decyzje.md` DZ13
