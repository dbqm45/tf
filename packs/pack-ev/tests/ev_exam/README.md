# Egzamin branżowy EV

Pytania sprawdzają, czy model z fabryką odpowiada na pytania z branży ładowania EV lepiej niż bez niej. Runner:
`tests/run_ev_exam.py` (walidacja bez modelu: `--validate`; przebieg na modelu jest płatny — tylko za zgodą człowieka).

## Format pliku `<obszar>.json`
```json
{"obszar": "<nazwa pliku bez .json>",
 "pytania": [
  {"id": "faulted-vs-unavailable",
   "pytanie": "Czym różni się Faulted od Unavailable w OCPP 1.6 i co odpowiada im w 2.0.1?",
   "wzorzec": "Odpowiedź wzorcowa w 1–4 zdaniach, spełniająca checks.all i niezawierająca checks.none.",
   "checks": {"all": [["faulted"], ["unavailable"], ["2\\.0\\.1"]], "none": ["faulted i unavailable to to samo"]},
   "zrodlo": "dom-ev-ocpp-16, dom-ev-ocpp-2x",
   "trudnosc": 2}
 ]}
```
- `checks.all` — grupy alternatyw (wyrażenia regularne, bez rozróżniania wielkości liter); każda grupa musi trafić.
  Sprawdzaj wiedzę, nie sformułowanie: dopuszczaj odmianę polską (`przyłącz`), angielskie nazwy pól i liczby
  w kilku zapisach (`97 ?%|97 proc`).
- `checks.none` — typowy błąd, który dyskwalifikuje odpowiedź.
- `wzorzec` musi spełniać własne sprawdzenia — walidator to sprawdza.
- `zrodlo` — skill fabryki albo `kb:<id>` z bazy wiedzy (kilka po przecinku); odpowiedź musi wynikać z tego źródła.
- `trudnosc` — 1 (podstawy), 2 (praktyka), 3 (pułapka, którą zna tylko praktyk albo specyfikacja).

Fakty oznaczone w skillach [do weryfikacji] nie są dobrym materiałem na pytanie.
