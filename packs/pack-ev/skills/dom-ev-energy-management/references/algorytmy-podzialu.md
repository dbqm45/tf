# Algorytmy podziału mocy

## 1. Jednostki i reguły wspólne
Planuj w amperach na fazę, bo ograniczeniem instalacji jest prąd fazy, a nie moc. Moc to A × 230 V × liczba faz.

| Prąd | 1 faza | 3 fazy |
|---|---|---|
| 6 A (minimum) | 1,38 kW | 4,14 kW |
| 16 A | 3,68 kW | 11,04 kW |
| 32 A | 7,36 kW | 22,08 kW |
| 63 A | 14,49 kW | 43,47 kW |

Reguły, które spełnia każdy algorytm:
- **Minimum 6 A.** Poniżej pojazd nie ładuje (PWM 10 %, dom-ev-charger-hardware), więc przydział < 6 A zamień na 0 — nie na 5 A.
- **Maksimum** = najmniejsza z wartości: nastawa stacji, limit kabla (PP), prąd, który pobiera pojazd.
- **Rozdzielczość 0,1 A:** schemat OCPP przyjmuje `limit` z jedną cyfrą po przecinku; zaokrąglaj w dół (wynik w górę łamie limit).
- **Suma pod limitem w każdej fazie**, razem z pomiarem budynku i rezerwą.
- Gdy wolny prąd < 6 A × liczba pojazdów, część pojazdów **czeka** (limit 0). Przy 63 A i pojazdach trójfazowych ładuje naraz
  najwyżej ⌊63 / 6⌋ = 10.

## 2. Porównanie algorytmów
| Algorytm | Zasada | Dobry, gdy | Wada |
|---|---|---|---|
| Równy podział | limit ÷ liczba pojazdów | parking publiczny, brak wiedzy o odjazdach | ignoruje potrzeby i terminy; oddaje prąd pojazdom, które go nie wezmą |
| Proporcjonalny | udział ∝ maks. prąd lub potrzebna energia | stacje o różnej mocy | nadal bez terminów |
| FIFO | kto pierwszy, ten pełna moc | prosty regulamin | późny gość stoi na 0 A |
| EDF (najwcześniejszy odjazd) | najpierw pojazd, który odjeżdża najwcześniej | flota z harmonogramem | gdy terminy są równe, o kolejności decyduje remis (w `depot.py` nazwa EVSE) |
| Najmniejszy luz (LLF) | luz = czas do odjazdu − czas ładowania pełną mocą | termin ważniejszy od kolejności | wymaga SoC i mocy pojazdu; zmienia kolejność często |
| Priorytety | klasy (karetka, taksówka, gość) i w klasie EDF | umowy SLA, flota mieszana | źle dobrane klasy głodzą niski priorytet |
| Cena | najtańsze sloty przed terminem | taryfy dynamiczne | wymaga wykonalności terminów (sekcja PV/BESS/taryfy) |

Algorytm z `depot.py` jest chciwy (ASAP): daje pojazdowi tyle, ile weźmie, aż się naładuje. Nie wygładza obciążenia
ani nie szuka tanich slotów. To wystarcza do sprawdzenia wykonalności, ale nie do kosztu.

## 3. Fazy i nierównowaga
- Ładowarka trójfazowa ładuje pojazd równym prądem na fazie, więc **dostępny prąd = minimum z faz**, nie suma.
- Dla każdej fazy: `wolne(Lx) = limit − budynek(Lx) − rezerwa − Σ prądów EV na Lx`.
- Stacja 3-fazowa zużywa prąd na L1, L2 i L3 jednocześnie; stacja 1-fazowa tylko na swojej fazie.
- Przypisuj stacje 1-fazowe do faz **rotacyjnie** (L1, L2, L3, L1…) przy instalacji i dziel limit per faza, żeby nie przeciążyć jednej.
- Pojazd 1-fazowy na stacji 3-fazowej obciąża fazę, którą wybiera pojazd (zwykle L1); CSMS często nie zna tej fazy.
  Przyjmij najgorszy przypadek albo mierz prąd faz ładowarki [do weryfikacji w MeterValues].
- Stacje z przełączaniem faz: w OCPP 2.0.1 pole `phaseToUse` w okresie profilu i `ACPhaseSwitchingSupported` (libocpp K01.FR.19–20, 48).
  `numberPhases` w okresie profilu domyślnie 3 (schemat `SetChargingProfile`).
- Dopuszczalna asymetria prądów jest narzucona przez OSD lub normę instalacyjną [do weryfikacji — brak w bazie].

Rachunek (scenariusz biuro 3×80 A, rezerwa 5 A): budynek L1 55, L2 30, L3 20 A → wolne L1 20, L2 45, L3 55 A.
Dwie stacje 3-fazowe dzielą najsłabszą fazę: 20 A ÷ 2 = 10 A każda. Zużywają 20 A na każdej fazie, więc zostaje
L1 0, L2 25, L3 35 A. Stacja 1-fazowa na L3 dostaje min(32, 35) = 32 A. Błąd: (240 − 105) ÷ 3 stacje = 45 A — suma po fazach nie ma sensu.

## 4. Przykład: równy podział kontra EDF
Limit 24 A (3 fazy), pojazd A: 24 kWh do 20:00 (2 h), pojazd B: 20 kWh do 21:00+ (3 h). Obaj 3-fazowi.
- Równy podział 12 A: A dostaje 12 × 0,69 kW × 2 h = 16,6 kWh < 24 → **niespełnione**.
- EDF: A 24 A do ok. 19:20 (24 kWh), potem B; B dostaje 20 kWh przed odjazdem → **oba spełnione**
  (wynik `depot.py` dla tego scenariusza).

## 5. Odzyskiwanie niewykorzystanego prądu
Pojazd zwykle pobiera mniej niż limit (koniec krzywej CC/CV, grzanie, ładowarka pokładowa). Mierz prąd EVSE
(MeterValues `Current.Import`) i licz zajętość z pomiaru, nie z limitu. Algorytm: pojazd, który przez N próbek bierze < 80 % limitu,
dostaje limit = pobór + zapas 2 A; reszta wraca do puli. Gdy pobór znów rośnie do limitu, podnoś limit stopniowo.
Wartości 80 %, 2 A i N [założenie — dobierz na symulacji i stacji].
