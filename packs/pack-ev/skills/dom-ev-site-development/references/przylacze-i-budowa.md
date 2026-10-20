# Przyłącze i prace budowlane

Spis treści: 1. Przyłącze · 2. Elementy elektryczne · 3. Alternatywy przy słabym przyłączu · 4. Polska ustawa · 5. Budowa ·
6. Łączność · 7. Przepisy bez aktu w bazie.

## 1. Przyłącze — przebieg
| Krok | Co robisz | Dane do zapisania |
|---|---|---|
| 1 | zapytanie wstępne do OSD o dostępną moc w okolicy | data, numer sprawy, odpowiedź |
| 2 | wniosek o określenie warunków przyłączenia: moc [kVA], napięcie (nN lub SN), miejsce punktu przyłączenia | moc wnioskowana, data złożenia |
| 3 | warunki przyłączenia od OSD: moc, punkt, zakres prac po obu stronach, zabezpieczenia, ważność warunków | moc przyznana, ważność, koszt (z pisma OSD) |
| 4 | umowa o przyłączenie, zaliczka, harmonogram OSD | termin przyłączenia z umowy |
| 5 | realizacja: sieć OSD i instalacja inwestora | status, ryzyka (pozwolenia OSD, służebność) |
| 6 | odbiór, umowa dystrybucyjna, licznik OSD, załączenie | data energii na rozdzielnicy |
Przepisy Prawa energetycznego o warunkach przyłączenia, opłatach i terminach są **poza bazą wiedzy** fabryki
[do weryfikacji]. Czas oczekiwania traktuj jako główne wąskie gardło: zbiera się go z pism OSD, nie z przeglądu.
Przyłącze jest ścieżką krytyczną całego pipeline — składaj wniosek równolegle z umową i projektem.

## 2. Elementy elektryczne
| Element | Po co | Co zapisać |
|---|---|---|
| moc w kVA | kVA to moc pozorna, kW czynna; kW ≈ kVA × współczynnik mocy | kVA wnioskowane, współczynnik, kW dostępne dla ładowarek |
| stacja transformatorowa SN/nN | przy dużych mocach DC; własna (inwestor) albo OSD | typ, moc transformatora, rezerwa |
| rozdzielnica główna | zasilanie pól ładowarek, zabezpieczenia, miejsce na rozbudowę | zapas pól, zabezpieczenie główne w A |
| licznik główny OSD | wyznacza limit w eksploatacji; punkt pomiaru dla DLM | numer, moc umowna, przekładniki |
| uziemienie i ochrona | uziom, wyrównanie potencjałów, ochrona przeciwprzepięciowa | wartości z protokołów pomiarowych |
| potrzeby własne | chłodzenie szaf DC, oświetlenie, łączność, CCTV | moc stała, wlicz do bilansu |
Ładowarka DC ma sprawność poniżej 100 %, więc moc z sieci jest większa niż moc na złączu; nie zakładaj, że 8 × 150 kW
mieści się w 1 200 kW przyłącza. Sprzęt i liczba modułów: dom-ev-charger-hardware.

## 3. Alternatywy przy słabym przyłączu
| Opcja | Efekt | Koszt/ryzyko (własne dane) |
|---|---|---|
| BESS | magazyn pokrywa szczyt, przyłącze obsługuje średnią | CAPEX magazynu, żywotność, bezpieczeństwo pożarowe [do weryfikacji] |
| load management | podział mocy między punkty w eksploatacji (dom-ev-energy-management, dom-ev-smart-charging) | mniejsza moc na pojazd w szczycie |
| etapowanie | mniejsza moc teraz, rozbudowa z gotowymi rurami | druga umowa o przyłączenie |
| mniej mocy szczytowej | AC lub DC 50 kW tam, gdzie postój jest długi | niższa przepustowość |
| inna lokalizacja | gdy ani opcje 1–4 nie domykają bramki | utrata leada |
Rozmiar BESS i limit w eksploatacji liczy dom-ev-energy-management; tu decydujesz, czy lokalizacja w ogóle wchodzi do realizacji.

## 4. Polska ustawa o elektromobilności (baza `pl-elektromobilnosc`, Dz.U. 2026 poz. 1243)
| Przepis | Treść własnymi słowami |
|---|---|
| art. 12b ust. 9–10 | gdy ekspertyza wymaga zmiany umowy o przyłączenie budynku lub nowej instalacji, zgodę można dać tylko, gdy wnioskodawca pokryje koszty; OSD montuje układ pomiarowy na stanowisku z wyłącznym prawem użytku |
| art. 12c ust. 5 | ekspertyza określa m.in. moc przyłączeniową budynku dostępną dla punktu, punkty przyłączenia, maksymalną moc punktu, wymagania bezpieczeństwa pożarowego |
| art. 62 ust. 4–6, 11–12 | w gminach spełniających progi plan budowy ogólnodostępnych stacji uzgadnia OSD, uwzględniając moce przyłączeniowe; OSD opracowuje program przyłączania z technicznymi i ekonomicznymi warunkami i przewidywanymi terminami |
| art. 67 | budowa wskazanych w planie stacji i przyłączenie to cel publiczny w rozumieniu ustawy o gospodarce nieruchomościami |
| art. 15 | przed budową można wnioskować do Prezesa UDT o opinię o dokumentacji; UDT wydaje ją w ciągu 30 dni od wniosku (opłata) |
| art. 16 | badanie techniczne UDT przed oddaniem do eksploatacji i po rozbudowie o punkty |
Ustawa nie wyznacza terminu przyłączenia przez OSD dla pojedynczego inwestora — nie podawaj takiego terminu.
Szczegóły UDT, EIPA i ról: dom-ev-regulations-pl.

## 5. Budowa
| Element | Co ustalić | Uwaga |
|---|---|---|
| fundamenty | nośność pod szafy i dispensery, kanały kablowe | geotechnika, głębokość przemarzania [do weryfikacji] |
| miejsca | długość, szerokość, dostęp, pull-through | wymiary w PL: Warunki techniczne i normy [do weryfikacji]; miejsce dla osób z niepełnosprawnością szersze od standardowego |
| bollardy i odbojniki | ochrona dispenserów przed uderzeniem | zakres z oceny ryzyka |
| zadaszenie | komfort, ale wysokość ogranicza vany i ciężarówki | OCPI 2.3.0 `roofed`, `max_vehicle_height` |
| oświetlenie | bezpieczeństwo kierowcy | OCPI 2.3.0 `lighting` |
| odwodnienie | spadki, separator przy parkingach, ochrona szaf | |
| oznakowanie | pionowe i poziome, numeracja miejsc (`physical_reference`), tablica z informacją o cenie i płatności | wymagania płatności ad hoc: dom-ev-regulations-eu |
| CCTV | bezpieczeństwo i wandalizm; RODO przy monitoringu | zgoda gospodarza, tablice informacyjne [do weryfikacji] |
| MCS (ciężkie) | osobne pole, duże moce, chłodzenie kabla | [do weryfikacji] |
Dostępność: ustawa art. 13 wymaga dostępu dla osób niepełnosprawnych; w NEVI płatność ma być dostępna dla osób
z niepełnosprawnościami (680.106(f)). W OCPI `parking_restrictions` ma wartość DISABLED, a `Parking` zdjęcie
(`images`) miejsca dla osób z niepełnosprawnościami (2.3.0).

## 6. Łączność
| Warstwa | Zalecenie |
|---|---|
| LTE | podstawowe łącze stacji i CCTV; antena na zewnątrz szafy; karty SIM dwóch operatorów lub roaming krajowy |
| światłowód | gdy stacja dużej mocy lub wiele punktów; trasa kablowa w projekcie |
| redundancja | drugie łącze (LTE + światłowód); stacja przechodzi w tryb offline — dom-ev-cpms-architecture, dom-ev-diagnostics |
| zasilanie komunikacji | UPS lub zasilanie z niezależnego obwodu dla modemu |
| tryb offline | profile awaryjne i lista autoryzacji: dom-ev-smart-charging, dom-ev-ocpp-16 |
Zapisz w danych lokalizacji: operator, numer SIM, typ łącza, RSSI z odbioru (wejście dla rejestru assetów).

## 7. Przepisy bez aktu w bazie [do weryfikacji]
Przepisy przeciwpożarowe dla stacji i parkingów podziemnych (PL, UE, USA), wymagania dla BESS, Warunki techniczne dla
miejsc parkingowych, Prawo budowlane (kwalifikacja robót), ochrona konserwatorska i wymagania lokalne. Nie ma ich w bazie:
sprawdź przez źródło pierwotne i konsultację z rzeczoznawcą ppoż. i projektantem. W Polsce art. 12c ust. 5 pkt 5 ustawy
wymienia bezpieczeństwo pożarowe jako przedmiot ekspertyzy dla instalacji w budynkach.

## Źródła
Baza wiedzy fabryki, pobrane 2026-10-20: `pl-elektromobilnosc` (art. 12b, 12c, 13, 15, 16, 62, 67), `us-nevi` (680.106(f)),
`ocpi-2.3.0` (Parking), `eu-epbd`. Pozostałe elementy — przegląd wiedzy ogólnej EV, [do weryfikacji].
