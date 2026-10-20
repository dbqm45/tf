# Taryfa → CDR → CDR kredytowy (OCPI 2.2.1)

Przykład dydaktyczny i cel testu end-to-end fabryki. Pokazuje pełną ścieżkę pieniędzy po stronie CPO i eMSP: cenę sesji
z taryfy, CDR, wykrycie błędu, korektę CDR kredytowym i nowym CDR, a na końcu saldo u eMSP. Ceny są przykładowe.

## Historia
Sesja AC we wtorek 2026-10-20 w Warszawie: od 17:00 ładowanie przez 90 min (16,5 kWh), potem 40 min postoju (18:30–19:10).
Taryfa CPO (`data/tariff.json`): 1,79 zł/kWh netto i postój 12 zł/h netto w dni robocze. Błąd w konfiguracji: okno
postoju ustawiono na 08:00–20:00, a cennik dla kierowców mówi 08:00–18:00 (`data/tariff-corrected.json`).

| Krok | Wynik |
|---|---|
| CDR z błędną taryfą (`CDR-1001`) | 37,535 zł netto / 46,1681 zł brutto (energia 29,535 + postój 8,00) |
| CDR kredytowy (`CDR-1001-C`) | te same dane, `credit: true`, `credit_reference_id: CDR-1001`, ujemny tylko `total_cost` |
| Nowy CDR (`CDR-1001-R1`) | 29,535 zł netto / 36,3281 zł brutto, bez postoju |
| Saldo u eMSP | suma trzech CDR = koszt nowego CDR |

## Uruchomienie
```bash
D=examples/ocpi-tariff-cdr
python3 $D/cdr_flow.py make $D/data/tariff.json $D/data/session.json --id CDR-1001 --tz Europe/Warsaw > cdr.json
python3 .claude/skills/dom-ev-tariffs-pricing/scripts/ocpi_tariff_calc.py $D/data/tariff.json cdr.json --cdr cdr.json --tz Europe/Warsaw
python3 $D/cdr_flow.py correct cdr.json $D/data/tariff-corrected.json --tz Europe/Warsaw   # [CDR kredytowy, nowy CDR]
```

## Zasady, które pokazuje
- CDR się nie zmienia: OCPI nie ma PUT, PATCH ani DELETE dla CDR. Korekta to CDR kredytowy, a po nim nowy CDR.
- CDR kredytowy ma nowe `id` (tu z sufiksem `-C`), wszystkie dane oryginału i ujemny tylko `total_cost`.
- CDR niesie kopię taryfy z chwili sesji, więc koszt da się odtworzyć później (`ocpi_tariff_calc.py --cdr`).
- Restrykcje czasowe liczy się w strefie lokacji (`--tz`), nie w UTC.
- eMSP przyjmuje CDR idempotentnie po (`country_code`, `party_id`, `id`). Odrzuca kredyt do nieznanego CDR i drugi
  kredyt tego samego CDR (`EmspLedger` w `cdr_flow.py`).

## Czego brakuje do produkcji
- Wysyłka przez moduł CDRs (POST do eMSP, odpowiedź OCPI, ponowienia) — dom-ev-ocpi.
- Dokument dla kierowcy (faktura korygująca wg przepisów kraju) i termin, w jakim wolno wysłać CDR kredytowy (OCPI go nie
  określa; decyduje umowa i prawo).
- Uzgadnianie hurtowe i spory — dom-ev-cdr-settlement. Zasady taryf i `step_size` — dom-ev-tariffs-pricing.

## Test
`python3 tests/test_ocpi_tariff_cdr.py`. Katalog `examples/` nie trafia do projektu przy instalacji fabryki, więc w
projekcie test się pomija.
