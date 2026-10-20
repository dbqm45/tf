# Pozwolenia, umowy, pipeline i dane lokalizacji

> **Spis treści:** 1. Pozwolenia · 2. Umowy z gospodarzem lokalizacji · 3. Pipeline jako dane · 4. Bramka go/no-go · 5. Future-proofing · 6. Przekazanie do rejestru assetów i CSMS · 7. Publikacja lokalizacji w OCPI

Spis treści: 1. Pozwolenia · 2. Umowy · 3. Pipeline jako dane · 4. Bramka go/no-go · 5. Future-proofing · 6. Przekazanie ·
7. Publikacja OCPI.

## 1. Pozwolenia
| Obszar | Pytanie | Uwaga |
|---|---|---|
| planistyczne | czy plan miejscowy lub decyzja o warunkach zabudowy dopuszcza stację | zależne od gminy [do weryfikacji] |
| budowlane | pozwolenie czy zgłoszenie; zakres: fundamenty, stacja SN/nN, zadaszenie | zależy od zakresu robót [do weryfikacji] |
| zgoda właściciela | pisemna zgoda na budowę, przyłącze i dostęp 24/7 | wymóg przy cudzym gruncie |
| OSD | warunki i umowa o przyłączenie | patrz `przylacze-i-budowa.md` |
| UDT (PL) | opinia o dokumentacji (opcjonalnie), badanie przed oddaniem | art. 15–16 ustawy; dom-ev-regulations-pl |
| zabytki | zgoda konserwatora (w budynkach ustawa art. 12b ust. 11) | dla terenów zabytkowych sprawdź osobno |
| przeciwpożarowe | uzgodnienia, parking podziemny, BESS | brak aktu w bazie [do weryfikacji] |
Śledź każde pozwolenie jako osobny rekord: wniosek, data, organ, termin ważności, warunki.

## 2. Umowy z gospodarzem lokalizacji
| Element | Co ustalić |
|---|---|
| tytuł do terenu | dzierżawa, najem, służebność; prawo do przyłącza i prac |
| długość | typowa długość dzierżawy [do weryfikacji]; co najmniej okres zwrotu z bramki 4 plus rezerwa |
| opłata | czynsz stały, procent przychodu lub hybryda; wartości z własnych negocjacji |
| podział przychodu | od przychodu brutto z ładowania czy od marży; definicja bazy (po prowizjach?), raportowanie, audyt |
| wyłączność | zakaz konkurencyjnych ładowarek na terenie, prawo pierwszeństwa rozbudowy |
| dostęp | 24/7 dla stacji publicznej, godziny dla klientów; wpływ na `opening_times` |
| energia | kto jest stroną umowy dystrybucyjnej, podlicznik, refaktura [do weryfikacji] |
| zakończenie | demontaż, koszt przywrócenia, prawo odkupu, cesja umowy |
| zmiana ceny | kto ustala cenę dla kierowcy (dom-ev-tariffs-pricing) |
Rola gospodarza (site host) i rozliczenia pieniędzy: dom-ev-market-roles. NEVI: stacje poza korytarzem muszą być
dostępne co najmniej w godzinach działalności gospodarza (680.106(e)) — godziny z umowy trafiają do danych stacji.
EPBD art. 14 ust. 2 wymaga w budynkach niemieszkalnych z ponad 20 miejscami m.in. punktu na każde 10 miejsc albo
kanałów dla 50 % miejsc (od 1.01.2027; państwa transponują) — gospodarz bywa zobowiązany do infrastruktury, więc
rozmowa o podziale kosztów zaczyna się od jego obowiązków.

## 3. Pipeline jako dane
Pola rekordu lokalizacji (model danych zespołu rozwoju; nazwy robocze):
| Pole | Opis |
|---|---|
| site_id | stały identyfikator wewnętrzny, **nie** `Location.id` OCPI i nie EVSE ID (dom-ev-identifiers) |
| stage | lead · assessment · agreement · design · grid · construction · commissioning · operations |
| owner, host | osoba odpowiedzialna, gospodarz |
| score, score_version | wynik i wersja wag |
| requested_kva, granted_kva, osd_case_id, grid_date | z pisma OSD, nie z przeglądu |
| permits[] | rodzaj, organ, status, ważność |
| lease | początek, koniec, podział przychodu, wyłączność |
| gate_history[] | decyzja, data, osoba, dokument |
| evse_plan | liczba punktów, moc, typ, złącza, faza etapowania |
Każde przejście etapu zapisuj ze znacznikiem czasu i osobą; zmiana wag punktacji zwiększa `score_version`.
Etapy mogą się nakładać (przyłącze równolegle z umową), więc przechowuj status per ścieżka (grid, permits), nie jeden `stage`.

## 4. Bramka go/no-go
Wejście: koszt z ofert (CAPEX: sprzęt, przyłącze, budowa), warunki przyłączenia, dzierżawa, założenie utilization i ceny,
dotacje. Policz `python3 .claude/skills/dom-ev-business-economics/scripts/station_economics.py <stacja>.json --json`:
NPV, okres zwrotu, próg rentowności utilization, wrażliwość. Kod wyjścia 1 = NPV ujemne.
Decyzja: go, no-go lub go warunkowy (np. po rozmowie o czynszu). Zapisz założenia, nie tylko wynik. Liczb z przykładów
w skillach (np. utilization 10 %) nie traktuj jako rynkowych.

## 5. Future-proofing
| Element | Dlaczego teraz |
|---|---|
| rury kablowe i studnie pod przyszłe pola | wykop jest droższy niż rura |
| miejsce na dodatkowe dispensery, szafy, BESS | rozbudowa popytu bywa szybsza niż przyłącza |
| moc: wniosek na moc docelową, uruchomienie etapami | druga umowa o przyłączenie to druga kolejka |
| rozdzielnica z zapasem pól | wymiana jest droższa niż zapas |
| miejsca pod inne pojazdy (pull-through, ciężkie) | zmiana flot i segmentów |
| zapas w łączności (drugie łącze) | nowe punkty zwiększają ruch danych |
Rezerwę wpisz do projektu i do umowy z gospodarzem (prawo rozbudowy). Wymiarowanie na jednoczesne użycie wszystkich
miejsc to wymóg EPBD dla okablowania wstępnego w nowych budynkach mieszkalnych (art. 14 ust. 4).

## 6. Przekazanie do rejestru assetów i CSMS
| Kto | Dostaje | Skill |
|---|---|---|
| rejestr assetów | hierarchia lokalizacja → stacja → EVSE, numery seryjne, daty montażu i legalizacji, gwarancje, SIM, transformator, BESS | dom-ev-asset-operations |
| CSMS i onboarding | model ładowarki, firmware, parametry, kontrola Pending vs Accepted | dom-ev-charger-onboarding |
| identyfikatory | EVSE ID zgodne z formatem operatora | dom-ev-identifiers |
| zarządzanie energią | limit przyłącza z umowy, rezerwa, topologia faz | dom-ev-energy-management |
| rozliczenia | taryfy, strona gospodarza | dom-ev-tariffs-pricing, dom-ev-cdr-settlement |
| zgodność | numer EIPA, badanie UDT (PL) | dom-ev-regulations-pl |
Commissioning kończy się, gdy testy akceptacyjne przeszły, lokalizacja jest widoczna u partnerów (OCPI) i stacja ma
przypisanych właścicieli operacji. Bez wpisu w rejestrze assetów lokalizacja nie przechodzi do etapu operations.

## 7. Publikacja lokalizacji w OCPI
Baza `ocpi-2.2.1-d2` i `ocpi-2.3.0`, moduł Locations. Rola protokołu i wersje: dom-ev-ocpi.
| Dane z budowy | Pole | Wartości i uwagi |
|---|---|---|
| typ miejsca | `Location.parking_type` | ALONG_MOTORWAY, PARKING_GARAGE, PARKING_LOT, ON_DRIVEWAY, ON_STREET, UNDERGROUND_GARAGE |
| udogodnienia | `Location.facilities` | HOTEL, RESTAURANT, CAFE, MALL, SUPERMARKET, SPORT, RECREATION_AREA, NATURE, MUSEUM, BIKE_SHARING, BUS_STOP, TAXI_STAND, TRAM_STOP, METRO_STATION, TRAIN_STATION, AIRPORT, PARKING_LOT, CARPOOL_PARKING, FUEL_STATION, WIFI |
| godziny | `Location.opening_times` (Hours) | `twentyfourseven`; `regular_hours` tylko gdy `twentyfourseven=false`; `exceptional_openings`, `exceptional_closings` |
| strefa czasowa | `Location.time_zone` | IANA, np. Europe/Warsaw |
| piętro | `EVSE.floor_level` | garaże |
| ograniczenia miejsca | `EVSE.parking_restrictions` | EV_ONLY, PLUGGED, DISABLED, CUSTOMERS, MOTORCYCLES |
| współrzędne | `GeoLocation` | WGS 84, co najmniej pięć miejsc po przecinku |
| dojazd | `Location.directions`, `EVSE.directions`, `physical_reference` | tekst dla kierowcy |
| miejsca parkingowe (tylko 2.3.0) | `Location.parking_places` (`Parking`), `EVSE.parking` (`EVSEParking`) | `vehicle_types`, `max_vehicle_*` i `parking_space_*` w cm, `drive_through`, `roofed`, `lighting`, `refrigeration_outlet`, `time_limit`, `reservation_required`, `restricted_to_type`, `dangerous_goods_allowed`; w `EVSEParking` `parking_id` i `evse_position` |
`Parking` dodano w OCPI 2.3.0 względem 2.2.1 (cel: raportowanie AFIR). Integracja wielowersyjna: wersja 2.2.1 pomija te
pola, więc nie polegaj na nich u partnerów, którzy ich nie odbierają. `opening_times` ma wpływ na wyświetlanie dostępności
i na obowiązek 24/7 w korytarzu NEVI; zmiana godzin jest aktualizacją `Location`.

## Źródła
Baza wiedzy fabryki, pobrane 2026-10-20: `ocpi-2.2.1-d2` i `ocpi-2.3.0` (mod_locations.asciidoc: Location, EVSE, Hours,
Facility, ParkingType, ParkingRestriction, Parking, VehicleType), `eu-epbd` (art. 14 ust. 2, 4), `pl-elektromobilnosc`
(art. 12b, 15, 16), `us-nevi` (680.106(e)). Pozostałe zasady — przegląd wiedzy ogólnej EV, [do weryfikacji].
