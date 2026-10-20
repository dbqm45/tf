# Wybór lokalizacji — model punktacji, dane, korytarz

Spis treści: 1. Dane wejściowe · 2. Model punktacji · 3. Czas postoju i typ ładowarki · 4. Dostęp pojazdów · 5. Korytarz.

## 1. Dane wejściowe
| Cecha | Skąd (typowo) | Uwaga |
|---|---|---|
| ruch | pomiary zarządcy drogi, dane geolokalizacyjne | w korytarzu AFIR progi ruchu (np. poniżej 8 500 lekkich pojazdów dziennie) dotyczą odstępstw państw (art. 3 ust. 7–9) |
| EV w okolicy | rejestracje, dane flot | to popyt potencjalny; popyt realny mierzą sąsiednie stacje |
| konkurencja | mapy publiczne, dane o statusie (AFDC, NAP) | patrz moc, liczba punktów i niezawodność, nie tylko odległość |
| floty i tranzyt | rozmowy z flotami, trasy | duży popyt to często kilka umów, nie ruch przypadkowy |
| udogodnienia i bezpieczeństwo | wizja lokalna | oświetlenie, WC, jedzenie, monitoring — wpływają na wybór kierowcy i na `facilities` w OCPI |
Danych o cenach, utilization i kosztach przyłączy **nie ma w bazie wiedzy fabryki**: wpisujesz własne z podaniem źródła.

## 2. Model punktacji
1. Ustal listę knock-outów (SKILL.md) — odrzuć przed liczeniem.
2. Wagi sumują się do 100; ocena 0–5 z opisanej skali (np. popyt: 0 brak danych, 5 potwierdzony kontrakt floty).
3. Wynik = Σ(waga × ocena) / 5. Zapisuj oceny i uzasadnienie, nie tylko wynik — przy rewizji widać, co się zmieniło.
4. Test wrażliwości: zmień wagę popytu i przyłącza o ±20 % i sprawdź kolejność.
5. Kalibracja: po 6–12 miesiącach porównaj wynik punktowy z realnym utilization stacji (dom-ev-kpi-analytics) i popraw wagi.

Przykład wag (ilustracja): popyt 25 · przyłącze 25 · postój 10 · konkurencja 10 · udogodnienia 10 · dostęp pojazdów 5 ·
umowa 10 · rozbudowa 5. Dla stacji korytarzowej dopuszczalne jest podniesienie wagi dostępu pojazdów i mocy.

Punktacja nie zastępuje ekonomii: wynik bez CAPEX i przychodu to ranking, nie decyzja. Dla finalistów policz
`station_economics.py` (dom-ev-business-economics) i podejmij decyzję na bramce 4.

## 3. Czas postoju i typ ładowarki
Progi z przeglądu wiedzy ogólnej [do weryfikacji]:
| Postój | Typ | Dlaczego |
|---|---|---|
| 5–40 min (trasa) | DC 150–400 kW | kierowca chce wrócić na drogę; liczy się moc szczytowa i niezawodność |
| 1–3 h (zakupy, obiad) | AC 22 kW lub DC 50 kW | energia dopasowana do postoju, niższy koszt przyłącza |
| 8 h i więcej (praca, hotel, noc) | AC 7–11 kW | wolne ładowanie wystarczy; liczy się liczba miejsc, nie moc |
Sprawdź realny postój w danych (czas pobytu na parkingu, nie czas ładowania). Moc użyteczna zależy też od pojazdu i
baterii (dom-ev-vehicle-battery) oraz od sprzętu (dom-ev-charger-hardware).

## 4. Dostęp pojazdów
| Pojazd | Co sprawdzić |
|---|---|
| van | wysokość wjazdu, szlabany, garaż podziemny; w OCPI 2.3.0 `VAN` (wysokość poniżej 275 cm) |
| auto z przyczepą | miejsca pull-through lub pochylone; kabel wystarczająco długi; `PERSONAL_VEHICLE_WITH_TRAILER` |
| ciężarówka | promienie skrętu, nośność nawierzchni, wysokość zadaszenia; MCS [do weryfikacji]; `SEMI_TRACTOR`, `RIGID`, `TRUCK_WITH_TRAILER` |
| autobus | zajezdnia — dom-ev-fleet-charging i dom-ev-energy-management |
Dla ciężkich pojazdów AFIR art. 4 określa pule na sieci TEN-T, bezpieczne parkingi i węzły miejskie (np. do 31.12.2025
w węźle miejskim agregat ≥ 900 kW ze stacji ≥ 150 kW, do 31.12.2030 ≥ 1 800 kW).

## 5. Korytarz
- AFIR art. 3 ust. 4: pula co najwyżej co 60 km w każdym kierunku, moc i liczba punktów rosnąca w czasie (SKILL.md).
- Art. 3 ust. 5: procent długości sieci kompleksowej liczy się tylko odcinki między pulami, które nie są od siebie dalej niż 60 km.
- Art. 3 ust. 11: sąsiednie państwa dbają, by odległości nie były przekroczone na odcinkach transgranicznych.
- NEVI 680.106(b), (d), (e): konfiguracja stacji korytarzowej; 680.116 — dane dla stron trzecich (dom-ev-regulations-us).
- Planując pulę, policz moc **wszystkich** punktów w puli (suma) i najsilniejszy pojedynczy punkt osobno: oba progi muszą być spełnione.
- Uwaga: AFIR adresuje państwa; wymóg dla projektu wynika z konkursu dotacyjnego, koncesji lub planu krajowego.

## Źródła
Baza wiedzy fabryki, pobrane 2026-10-20: `eu-afir` (linie 561–800, art. 3–4), `us-nevi` (linie 80–119), `ocpi-2.3.0`
(VehicleType, mod_locations.asciidoc), przegląd wiedzy ogólnej EV (progi postoju) — [do weryfikacji].
