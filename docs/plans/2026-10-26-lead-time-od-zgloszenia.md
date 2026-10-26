# Plan: data zgłoszenia w nagłówku zmiany (lead time od zgłoszenia)

Data: 2026-10-26 · Status: zrobione, PR w toku · Gałąź: `claude/lead-time-prb`

## TL;DR
Część tf planu dbqm45/pdi `docs/plan-f5-lead-time-prb.md`: kontrakt pdi 0.5.0 dodaje do `change.schema.json`
opcjonalne `source_reported_at` (dbqm45/pdi#26), a pdi wysyła `reported_at` w treści zgłoszenia do fazy `intent`.
W tf (tryb `mode-pdi`):
- `decision_record.py change new CHG-n --source PRB-n --source-reported-at RRRR-MM-DD` zapisuje dzień zgłoszenia w
  nagłówkach artefaktów (zła data albo data bez źródła → błąd, nic nie powstaje); `check` zna pole i sprawdza datę.
- `sdlc-phase.yml`: krok zakładający dziennik zmiany bierze `reported_at` z `PDI_PROBLEM`.
- SKILL.md (punkt 1 „Dziennik zmiany”), GUIDE.md, `pack.yaml` 0.6.0.

## Testy (najpierw czerwone)
`test_decision_record.py` S-1…S-5, `test_phase_run.py` W-8; czerwone przed zmianą, potem 79/79 i 47/47.
