# Plan: F5 w tf — pasma kontrolne na metrykach z ShipScope → `metric.breached`

Data: 2026-10-26 · Status: zrobione, PR w toku · Gałąź: `claude/f5-pasma-kontrolne`

## TL;DR
Plan jednego flow (dbqm45/pdi `docs/plan-jeden-flow-sdlc.md`, F5: „tf: pasma kontrolne na metrykach z ShipScope →
nowy PRB”; tabela zmian tf: „`control_band.py` + adapter API ShipScope; przy 3σ zdarzenie `metric.breached`”).
ShipScope oddaje już dzienny szereg PROD tokenem usługi (dbqm45/evdt-service-shipscope#110:
`GET /api/service/v1/metrics?from&to&format=csv`, kolumny `date,deployments,failed_deployments,rollbacks,
lead_time_days_median,lead_time_count`). Ten krok dokłada w trybie `mode-pdi` (opcjonalny, rdzeń bez zmian):

1. `metric_watch.py check` — czyta szereg z ShipScope (albo z pliku `--csv`), dla każdej metryki liczy pasma
   `control_band.py` ze skilla `core-delivery-lifecycle` (ta sama implementacja, reguły Western Electric) i pokazuje
   poziom (`ok`/`log`/`diagnose`/`act`) z naruszeniami po datach.
2. Punkt poza 3σ (reguła 1, poziom `act`) w ostatnich `recent` dniach (domyślnie 7) to zdarzenie `metric.breached`
   (kontrakt pdi 0.4.0: `metric`, `value`, `threshold`, `window`, `service`, `diagnosis`). Bez `--send` tylko
   drukowane; z `--send` wysyłane podpisane na `$PDI_EVENTS_URL/events/tf`, jak `gate.requested` z F4. ID zdarzenia
   `tf-metric-<metryka>-<dzień>` jest stałe, więc codzienne uruchomienie nie zdubluje zgłoszenia w pdi.
3. Szablon `metric-watch.yml` (`metric_watch.py workflow install`): raz dziennie i na żądanie, `check --send`.

Poziomy niższe niż `act` zostają w wyniku (zapis, diagnoza tylko do odczytu — jak w skillu); model nie jest wołany.

## Metryki domyślne
| Kolumna | Strona | Dlaczego |
|---|---|---|
| `rollbacks` | `upper` | więcej rollbacków = gorzej |
| `failed_deployments` | `upper` | j.w. |
| `lead_time_days_median` | `upper` | dłużej od Done do PROD = gorzej; dni bez wdrożeń pominięte |
| `deployments` | `lower` | spadek częstotliwości wdrożeń |

Nadpisanie w `.claude/pdi-metrics.json`: `{"baseline": 30, "recent": 7, "service": "sklep", "metrics":
{"rollbacks": {"side": "upper"}}}` (podane `metrics` zastępują domyślne; kolumna spoza CSV → błąd). Metryka bez
zmienności w linii bazowej (np. same zera rollbacków) albo z mniej niż `baseline + 1` punktami dostaje uwagę zamiast
poziomu — to nie błąd całego przebiegu.

## Elementy
- `modes/mode-pdi/skills/pdi-decisions/scripts/metric_watch.py` (stdlib): `check [--csv] [--days 120] [--baseline]
  [--recent] [--send]`, `workflow install [--force]`. ShipScope: `$SHIPSCOPE_URL` (https, http tylko dla localhost)
  i `$SHIPSCOPE_TOKEN` (token usługi `shps_…`), nigdy w wyjściu.
- `phase_run.py`: wysyłka podpisanego zdarzenia wydzielona do `post_event()` i używana przez oba skrypty.
- `templates/metric-watch.yml`; SKILL.md (sekcja „Pasma kontrolne z ShipScope”, akapit „Sieć”, scenariusz ewaluacji
  przed treścią); GUIDE.md; `settings.json`; `pack.yaml` 0.4.0.

## Testy (najpierw czerwone)
`modes/mode-pdi/tests/test_metric_watch.py`: skok rollbacków → `act` i zdarzenie zgodne z przykładem
`event-metric.breached.json` kontraktu; brak zmienności i za mało punktów → uwaga; stare naruszenie poza `recent` →
bez zdarzenia; spadek wdrożeń (`lower`) → próg średnia − 3σ; konfiguracja (usługa, wybór metryk, zła kolumna →
błąd); odczyt z ShipScope przez lokalny serwer HTTP (ścieżka, zapytanie, nagłówek Bearer; 401 → błąd bez tokenu);
brak `SHIPSCOPE_URL` / http poza localhost → błąd; `--send` → podpis sprawdzony lokalnym serwerem, nagłówek
`x-pdi-event: metric.breached`; brak sekretu → błąd; `workflow install` bez nadpisania. `test_phase_run.py` bez
zmian (refaktor `post_event()`). `test_mode_pdi.py`: skrypt, szablon, uprawnienie.

## Poza zakresem
Strona pdi: przyjęcie `metric.breached` od tf jako nowego zgłoszenia (PRB) — pdi dziś przyjmuje od tf tylko
`gate.requested` i odpowie 400; to osobny krok w pdi (F3, zgłoszenia). Drift (ShipScope nie ma jego historii).

## Bramki
`python3 tools/workspace.py check --packs mode-pdi` i `--packs all`, `python3 tools/workspace.py refs`,
`for t in tests/test_*.py; do python3 "$t" || exit 1; done`, `python3 factory/skill_gate.py pdi-decisions` w złożonym
projekcie (bez płatnej ewaluacji) i `workspace.py sync-gate`.

## Wynik (2026-10-26)
- `test_metric_watch.py` 24/24 (czerwony bez skryptu), `test_phase_run.py` 40/40 po wydzieleniu `post_event()`,
  `test_mode_pdi.py` z P-8 i P-9.
- `workspace.py check --packs mode-pdi` i `--packs all` zielone, `refs` bez odwołań między warstwami, testy repo
  zielone, bramka skilla `pdi-decisions` przeszła (scenariusz `pasma-kontrolne-shipscope` dopisany przed treścią;
  ewaluacja na modelu: brak).
- ShipScope i pdi sprawdzone lokalnymi serwerami HTTP, nie na działających usługach. pdi odpowie 400 na
  `metric.breached`, dopóki nie przyjmie go od tf (poza zakresem, wyżej).
