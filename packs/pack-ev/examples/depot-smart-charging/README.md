# Smart charging zajezdni pod limit przyłącza (OCPP 1.6)

Przykład dydaktyczny i cel testu end-to-end fabryki. Pokazuje drogę od potrzeb pojazdów do profili ładowania: CSMS
planuje prąd na każde EVSE w slotach 15-minutowych pod limit przyłącza, zamienia plan na `SetChargingProfile`
(`TxProfile`, Absolute) i sprawdza, że composite schedule każdego EVSE odtwarza plan. Stacja dostaje dodatkowo
`ChargePointMaxProfile` jako bezpiecznik niezależny od CSMS.

## Scenariusz (`data/depot.json`)
Przyłącze 63 A na fazę (3 fazy, 230 V), cztery pojazdy:

| EVSE | Przyjazd | Odjazd | Potrzeba | Maks. prąd | Wynik |
|---|---|---|---|---|---|
| EVSE-1 | 18:00 | 22:00 | 30 kWh | 32 A | spełnione |
| EVSE-2 | 18:00 | 04:00 | 40 kWh | 16 A | spełnione |
| EVSE-3 | 20:00 | 06:00 | 50 kWh | 32 A | spełnione |
| EVSE-4 | 18:00 | 20:00 | 60 kWh | 16 A | **niespełnione**: 16 A × 3 × 230 V × 2 h ≈ 22 kWh |

## Uruchomienie
```bash
python3 examples/depot-smart-charging/depot.py examples/depot-smart-charging/data/depot.json --profiles out/
python3 .claude/skills/dom-ev-smart-charging/scripts/composite_schedule.py out/EVSE-1.json \
  --start 2026-10-20T18:00:00Z --duration 43200
```
Kod wyjścia 1 oznacza, że któryś pojazd nie dostanie energii przed odjazdem. CSMS powinien wtedy zgłosić to
dyspozytorowi floty, zamiast milczeć.

## Algorytm
W każdym slocie pojazdy obecne i niedoładowane dostają prąd w kolejności najwcześniejszego odjazdu (EDF):
min(maks. pojazdu, prąd potrzebny do końca, wolny limit). Przydział poniżej 6 A to 0, bo przy wypełnieniu PWM
poniżej 10 % pojazd nie ładuje (dom-ev-charger-hardware). Algorytm jest celowo prosty: łatwo go sprawdzić i wytłumaczyć.

## Czego brakuje do produkcji
- Pomiar rzeczywistego poboru: pojazd zwykle bierze mniej niż limit, a niewykorzystany prąd trzeba oddać innym.
- Nierównowaga faz i pojazdy 1-fazowe, rezerwa na obciążenie budynku, PV, magazyn energii, ceny dynamiczne.
- Ponowne planowanie po zdarzeniach (przyjazd, odłączenie, utrata łączności) i zachowanie stacji offline
  (TxDefaultProfile jako bezpieczny limit).
- ISO 15118: harmonogram uzgadniany z pojazdem. OCPP 2.0.1/2.1: `NotifyEVChargingNeeds`, ExternalConstraints.

Wiedza: dom-ev-smart-charging (profile, composite schedule), dom-ev-energy-management (przyłącze, PV, magazyn, taryfy).

## Test
`python3 tests/test_depot_smart_charging.py`. Katalog `examples/` nie trafia do projektu przy instalacji fabryki, więc
w projekcie test się pomija.
