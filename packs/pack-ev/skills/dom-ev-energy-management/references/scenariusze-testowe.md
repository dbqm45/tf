# Testowanie zarządzania energią na scenariuszach z liczbami

## 1. Zasady
Test = wejście z liczbami + oczekiwana wartość + niezmiennik („suma w każdej fazie ≤ limit w każdej chwili”). Sprawdzaj niezmiennik
**w każdym slocie i po każdym zdarzeniu**, nie tylko wynik końcowy. Czas w symulatorze sterowany zegarem testu. Wzorzec wyniku policz niezależnie (ręcznie lub drugim kodem).

## 2. Scenariusze DLM
| # | Wejście | Oczekiwane |
|---|---|---|
| D1 | 3×80 A, budynek 55/30/20 A, rezerwa 5 A, dwie stacje 3-fazowe, jedna 1-fazowa na L3 | 3-fazowe po 10 A, 1-fazowa 32 A (stacja maks. 32 A) |
| D2 | budynek L1 = 80 A (wypełnia limit) | stacje 3-fazowe 0 A, 1-fazowa na L3 dalej ładuje |
| D3 | 63 A, 11 pojazdów 3-fazowych, brak budynku | najwyżej 10 ładuje po 6 A (60 A), jeden czeka na 0 |
| D4 | wolne 17 A, trzy pojazdy 3-fazowe | dwa po 8,5 A albo jeden 17 A; nigdy 3 × 5,7 A |
| D5 | pojazd ma limit 32 A, pobiera 16 A przez 60 s | po N próbkach limit = 18 A, 14 A wraca do puli; wzrost poboru → limit rośnie stopniowo |
| D6 | skok budynku o +30 A w 2 s | limit EV obcięty w czasie ≤ T (ustal T z zabezpieczeniem i czasem reakcji pojazdu) |
| D7 | umowna 40 kW, zabezpieczenie 63 A | limit na fazę = min(63, 40 000 / 690 = 57,97 → w dół do 0,1 A) = 57,9 A, minus rezerwa |

## 3. Scenariusze zajezdni
| # | Wejście | Oczekiwane |
|---|---|---|
| Z1 | depot.json | EVSE-1 30,0, EVSE-2 40,0, EVSE-3 50,0, EVSE-4 22,08 kWh; kod wyjścia 1 |
| Z2 | depot.json, limit 22 A | pierwsze trzy spełnione, EVSE-4 22,08 kWh |
| Z3 | depot.json, limit 21 A | EVSE-1 28,98 kWh (niespełnione) |
| Z4 | A: 24 kWh do 2 h, B: 20 kWh do 3 h, limit 24 A | EDF: oba spełnione; równy podział 12 A: A 16,6 kWh |
| Z5 | EVSE-3 przyjeżdża 18:00 zamiast 20:00 | plan bez zmiany wyników (4 pojazdy, te same energie) |
| Z6 | pojazd odjeżdża godzinę wcześniej w trakcie ładowania | ponowne planowanie: nowy profil, zgłoszenie niedoboru |

## 4. Awarie
| # | Zdarzenie | Oczekiwane |
|---|---|---|
| A1 | brak łącza CSMS 30 min | stacje na limicie domyślnym; suma ≤ limit przyłącza |
| A2 | brak próbek pomiaru > T | limit fail-safe, alarm; po powrocie podwyżka stopniowa |
| A3 | restart kontrolera | start z fail-safe, nie z ostatniego limitu |
| A4 | stacja nie potwierdza profilu (Rejected) | kontroler zakłada stary limit stacji; sumuje najgorszy przypadek |
| A5 | sygnał OSD „krytyczny” | limit z sygnału ma pierwszeństwo przed terminami floty; raport niedoboru |

## 5. Narzędzia
- `examples/depot-smart-charging/depot.py` — plan i profile; wariant limitu: skopiuj depot.json do katalogu roboczego, zmień `grid_limit_a`.
- `.claude/skills/dom-ev-smart-charging/scripts/composite_schedule.py <profile>.json --start <ISO> --duration <s>` — sprawdź, że stacja odtworzy plan.
- Symulator stacji OCPP i nagrane logi: dom-ev-simulation-testing.
