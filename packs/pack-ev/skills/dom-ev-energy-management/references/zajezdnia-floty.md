# Zajezdnia floty: harmonogram, SoC docelowy, ponowne planowanie

## 1. Dane wejściowe (na pojazd)
`evse`, `arrival`, `departure` (planowany odjazd), `needed_kwh` (z SoC), `max_a` (stacja, kabel, pojazd), `phases`, priorytet.
Źródła: harmonogram dyspozytora, telematyka pojazdu (SoC; RED III art. 20a ust. 3), OCPP `MeterValues` (SoC, jeśli stacja je podaje).

## 2. Od SoC do kWh
`needed_kwh = (SoC_docelowy − SoC_teraz) / 100 × pojemność_użyteczna / sprawność`. Sprawność ładowania AC ok. 0,90 [założenie — zmierz na flocie].
Przykład: 80 kWh użytecznych, 30 % → 90 %: 0,60 × 80 / 0,90 = 53,3 kWh z sieci. Przy 11,04 kW (16 A, 3 fazy) to 4,8 h.
Odejmij **bufor na odjazd** (np. koniec planu 30 min przed odjazdem [założenie]) i dolicz margines na SoC niższy od deklarowanego.

## 3. Wykonalność przed algorytmem
Dla każdego pojazdu policz granicę fizyczną: `max_kWh = max_a × 0,23 × fazy × czas_postoju`.
EVSE-4 w przykładzie: 16 A × 0,23 × 3 × 2 h = 22,08 kWh < 60 kWh → plan **nie może** się udać, niezależnie od limitu przyłącza.
Zgłoś to od razu dyspozytorowi (obniż SoC docelowy, wydłuż postój, zmień stację, wymień pojazd), zanim zacznie się ładowanie.

## 4. Ponowne planowanie
Przelicz plan od bieżącego slotu po zdarzeniu: przyjazd, odjazd wcześniejszy lub późniejszy, odłączenie, zmiana SoC docelowego, utrata łączności,
zmiana limitu (OSD), awaria stacji. Zachowaj energię już dostarczoną (z licznika). Nie wysyłaj nowych profili, jeśli plan się nie zmienił
(oszczędność ruchu OCPP). Stała kolejność remisów (priorytet, potem luz), nie nazwa EVSE.

## 5. Wynik przykładu depot.json (63 A, 230 V, sloty 15 min)
`python3 examples/depot-smart-charging/depot.py examples/depot-smart-charging/data/depot.json` — kod wyjścia 1.
| EVSE | Dostarczone | Cel | Wniosek |
|---|---|---|---|
| EVSE-1 | 30,0 kWh | 30 | spełnione, 32 A do 19:15, potem 13,9 A i 6 A |
| EVSE-2 | 40,0 kWh | 40 | spełnione, 15 A w pierwszych slotach, 16 A potem |
| EVSE-3 | 50,0 kWh | 50 | spełnione, start od 20:00 (przyjazd) |
| EVSE-4 | 22,08 kWh | 60 | **niespełnione**, fizyka: 16 A × 2 h |
Wnioski (z uruchomień wariantów `depot.py`):
- Limit 63 A jest w pełni wykorzystany tylko 18:00–19:15; reszta nocy poniżej 48 A, od 22:30 zero.
- Przy limicie 22 A trzy wykonalne pojazdy nadal są spełnione, przy 21 A EVSE-1 dostaje 28,98 kWh. Nadmiar przyłącza jest realnym
  zasobem (większa flota, dodatkowe stacje, mniejsza moc umowna) — wniosek z tego heurystycznego algorytmu, nie dowód optimum.
- Skrócenie postoju EVSE-1 do 20:00 przy limicie 40 A: EVSE-4 spada do 15,18 kWh, bo remis terminów rozstrzyga nazwa EVSE, a nie luz.
- Każdy plan przekłada się na `TxProfile` (Absolute) i `ChargePointMaxProfile` jako bezpiecznik; kontrola odtworzenia planu przez
  `composite_schedule.py` (dom-ev-smart-charging).
