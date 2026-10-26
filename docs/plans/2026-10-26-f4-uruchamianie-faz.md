# Plan: F4 w tf — fazy uruchamiane przez pdi, bez interakcji

Data: 2026-10-26 · Status: zrobione, PR w toku · Gałąź: `claude/f4-tf`

## TL;DR
Strona pdi fazy F4 działa (dbqm45/pdi#16): po decyzji na bramce pdi wywołuje `workflow_dispatch` szablonu fazy
w repo produktu z wejściami `change`, `phase`, `gate`, `outcome`, `decision`, `rework`, `budget_usd`, a prośby
o bramkę przyjmuje na `POST /events/tf` (podpis `v1=HMAC-SHA256(sekret, "<timestamp>.<body>")`, nagłówki
`X-PDI-Timestamp`, `X-PDI-Event`, `X-PDI-Signature`). Ten krok dokłada w tf drugą stronę — w trybie `mode-pdi`
(opcjonalny, rdzeń bez zmian, jak cała integracja z pdi):

1. `phase_run.py run --change CHG-12 --phase requirements …` — persona fazy pracuje bez interakcji
   (`claude -p --agent <persona> --max-budget-usd …`) i kończy stanem „czeka na bramkę” (kod wyjścia 0) albo błędem.
2. `phase_run.py gate request` — podpisane `gate.requested` do pdi (bramka fazy, podsumowanie, link do PR, pytania
   z artefaktu).
3. `decision_record.py decision gate` — decyzja z `gate.decided` zapisana w `changes/CHG-n/decisions.md` z numerem
   `DEC-n` z pdi i `wyslano: tak` (D2/R1: źródło prawdy decyzji o zmianie jest w repo).
4. Szablon `sdlc-phase.yml` (`phase_run.py workflow install` kopiuje go do `.github/workflows/`): decyzja → faza →
   PR → prośba o bramkę.

## Faza → persona, artefakt i bramka

| Faza (`phase` z pdi) | Persona (domyślnie, pack-it / mode-talos) | Artefakt w `changes/CHG-n/` | Bramka po fazie |
|---|---|---|---|
| `intent` | `maja` | `intent.md` | `B1` |
| `requirements` | `ewa` | `requirements.md` | `B2` |
| `architecture` | `tomasz` | `plan.md` (+ `release.yaml`, ADR) | `B3` |
| `design` | `natalia` (pack-ux) | `design.md` | `design-review` |
| `delivery` | `talos` | kod i PR na cięcie (`/talos-story-run --auto`) | — (merge w GitHubie, gotowość liczy ci_for_sdlc) |

Mapę nadpisuje `.claude/pdi-phases.json` (`{"requirements": {"persona": "jan"}}`). Persona musi istnieć w
`.claude/agents/_generated/`; brak → błąd z podpowiedzią, bez uruchamiania modelu.

## Elementy
- `modes/mode-pdi/skills/pdi-decisions/scripts/phase_run.py` (stdlib):
  - `prompt --change --phase [--rework] [--gate --decision]` → JSON `{persona, artifact, gate, prompt}` (czyste, bez
    modelu);
  - `run … [--budget-usd N] [--dry-run]` → wywołuje `claude` (`PDI_CLAUDE_BIN`, domyślnie `claude`) z
    `--print --output-format json --agent <persona> --permission-mode acceptEdits [--max-budget-usd N]`; wynik JSON
    `{status: waiting_gate | done | failed, persona, phase, gate, cost_usd}`; kod wyjścia 0 / 1;
  - `gate request --change --phase|--gate [--summary] [--url] [--dry-run]` → zdarzenie z kopertą kontraktu 0.4.0,
    pytania z sekcji „Pytania do bramki” artefaktu, POST na `$PDI_EVENTS_URL/events/tf` (https, albo http tylko dla
    localhost) z podpisem z `PDI_TF_SIGNING_SECRET`; `--dry-run` drukuje zdarzenie bez wysyłki i bez sekretu;
  - `workflow install [--force]` → kopia szablonu do `.github/workflows/sdlc-phase.yml`, bez nadpisania.
- `decision_record.py decision gate CHG-12 --gate B1 --outcome approved --id DEC-41 [--by pdi] [--date]` → wpis
  `## Bramka B1: approved` z `id`, `wyslano: tak`, `rodzaj: gate`; ponowienie z tym samym `--id` nic nie dopisuje.
- `modes/mode-pdi/skills/pdi-decisions/templates/sdlc-phase.yml` — `workflow_dispatch` z wejściami z pdi;
  kroki: checkout, Claude Code w przypiętej wersji, `decision gate` (gdy jest decyzja), `phase_run.py run`, commit na
  gałęzi `pdi/CHG-n-<faza>`, PR (`gh pr create`), `phase_run.py gate request --url`. Sekrety: `ANTHROPIC_API_KEY`,
  `PDI_TF_SIGNING_SECRET`; zmienna `PDI_EVENTS_URL`. Uprawnienia: `contents: write`, `pull-requests: write`.
- SKILL.md `pdi-decisions`: sekcja „Fazy uruchamiane przez pdi” (scenariusz ewaluacji przed treścią); GUIDE.md;
  `settings.json` (uprawnienie dla `phase_run.py`); `pack.yaml` 0.3.0.

## Testy (najpierw czerwone)
`modes/mode-pdi/tests/test_phase_run.py`: mapa faz i nadpisanie z `.claude/pdi-phases.json`, brak persony, prompt
(faza, ponowna praca z decyzją, delivery przez Talosa), `run` z podstawionym `claude` (sukces → `waiting_gate`,
`delivery` → `done`, błąd modelu i kod ≠ 0 → `failed`, budżet przekazany), `gate request` (koperta i treść zgodne
z przykładem `event-gate.requested.json` z kontraktu, pytania z artefaktu, podpis sprawdzony lokalnym serwerem HTTP,
brak sekretu / adresu → błąd, http poza localhost → błąd, `--dry-run` bez sekretu w wyjściu), `workflow install`
(kopia, brak nadpisania). `test_decision_record.py`: `decision gate` (wpis, idempotencja, złe wartości).
`test_mode_pdi.py`: skrypt, szablon workflow i uprawnienie w zainstalowanym projekcie.

## Bramki
`python3 tools/workspace.py check --packs mode-pdi` i `--packs all` (w tle), `python3 tools/workspace.py refs`,
`for t in tests/test_*.py; do python3 "$t" || exit 1; done`, `python3 factory/skill_gate.py pdi-decisions` w złożonym
projekcie. Bez płatnej ewaluacji. Tytuł PR: `scripts/check_commit_message.py`.

## Poza zakresem
ci_for_sdlc (gotowość i „Approve for implementation” przez pdi) — osobny krok. Wgranie i uruchomienie na koncie
(koszt) — tylko za zgodą człowieka.

## Wynik (2026-10-26)
- `modes/mode-pdi/tests/test_phase_run.py` 40/40 i `decision gate` w `test_decision_record.py` (G-1…G-8), najpierw
  czerwone; `test_mode_pdi.py` 7/7.
- `workspace.py check --packs mode-pdi` i `--packs all` zielone, `refs` bez odwołań między warstwami, testy repo
  zielone, bramka skilla `pdi-decisions` przeszła (bez ewaluacji na modelu).
- Domyślne persony faz są w pełnej instalacji: maja, ewa, tomasz, natalia (`_generated/<persona>/`), talos
  (`_generated/shared/`).
- Razem z pdi (main po dbqm45/pdi#16): `phase_run.py gate request` do lokalnego `pdi-receiver` → 202, pozycja B2
  w skrzynce z pytaniem z artefaktu i dopiskiem „poza kolejnością: brak B1”; zły sekret → 401.
- Nie uruchomiono: workflow na GitHubie i model (koszt; Actions na koncie są zablokowane).
