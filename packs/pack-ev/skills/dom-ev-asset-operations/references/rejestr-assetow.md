# Rejestr assetów — typy, atrybuty, uzgadnianie

Spis: 1. Model danych · 2. Atrybuty · 3. Hierarchia i źródła · 4. Uzgadnianie rejestru ze stacją · 5. Legalizacja licznika.

## 1. Model danych
Trzy elementy: **asset** (tożsamość i atrybuty), **pozycja** (gdzie jest i do czego należy, z okresem ważności) oraz
**zdarzenie** (zmiana stanu, wymiana, serwis, pomiar). Pozycja ma daty od–do, więc ten sam asset może mieć kilka
pozycji w czasie (magazyn → stacja A → magazyn → stacja B). Stan i pozycję czytasz z ostatnich zdarzeń; nie
nadpisujesz ich w miejscu, bo historia jest dowodem dla gwarancji, SLA i legalizacji.

## 2. Atrybuty
| Grupa | Atrybuty | Uwagi |
|---|---|---|
| Tożsamość | typ, producent/vendor, model, numer seryjny, numer partii, tag magazynowy | numer seryjny z etykiety i z `BootNotification` to dwa pola do porównania |
| Oprogramowanie | firmware stacji i modułów, wersja OCPP, profil bezpieczeństwa, szablon konfiguracji | wersja firmware stacji to dane z telemetrii; wersje modułów często tylko z logu producenta |
| Daty | zakup, instalacja, commissioning, koniec gwarancji, koniec wsparcia producenta, planowana wymiana | commissioning = przejście do `OPERATIONAL`, nie data montażu |
| Pozycja | lokalizacja, stacja, EVSE, złącze, zasilanie (rozdzielnia, transformator), grupa DLM | pozycja w hierarchii z okresem ważności |
| Umowa | dostawca serwisu, poziom SLA (czas reakcji, czas naprawy), właściciel kosztowy, leasing | SLA jako dane, bo napędza alarmy i eskalację |
| Łączność | `iccid`, `imsi`, operator SIM, APN, numer umowy | pola `iccid`/`imsi` zgłasza `BootNotification` (1.6 i `modem` w 2.0.1) |
| Pomiar | numer seryjny licznika, klasa, ważność legalizacji, numer plomby | → `dom-ev-metering-calibration` |
| Historia | zgłoszenia serwisowe, wymiany części, zmiany stanu, zmiany firmware | niezmienne zdarzenia |

Asset zależny (moduł mocy, kabel, licznik, modem) ma wskazanie na asset nadrzędny (szafa, stacja) i własny okres
życia. Wymiana modułu zamyka jego pozycję i otwiera nową dla modułu zamiennego; stacja nie dostaje nowego numeru.

## 3. Hierarchia i źródła
Location → (grupa/pula EVSE) → Charging Station → EVSE → Connector (pojęcia: `dom-ev-glossary`).
| Poziom | Czyja prawda | Skąd |
|---|---|---|
| Location (adres, współrzędne, godziny) | rejestr operatora | umowa z właścicielem terenu, publikacja OCPI/EIPA |
| Grupa EVSE (DLM, wspólne przyłącze) | rejestr operatora | projekt, `dom-ev-energy-management` |
| Charging Station | rejestr (tożsamość, pozycja) i stacja (vendor, model, serial, firmware) | `BootNotification` |
| EVSE / Connector | rejestr (ID, moc nominalna, złącze) i stacja (liczba, statusy) | konfiguracja, `StatusNotification` |
| Licznik | rejestr (legalizacja) i stacja (odczyt) | `meterType`, `meterSerialNumber` (1.6) |
Pola `BootNotification` 1.6: `chargePointVendor` i `chargePointModel` wymagane (do 20 znaków), `chargePointSerialNumber`
i `chargeBoxSerialNumber` (do 25), `firmwareVersion` (do 50), `iccid`, `imsi`, `meterType`, `meterSerialNumber`.
W 2.0.1 `chargingStation` wymaga `model` i `vendorName`; opcjonalne `serialNumber`, `firmwareVersion`, `modem`
(`iccid`, `imsi`); osobno `reason` (m.in. `PowerUp`, `FirmwareUpdate`, `RemoteReset`, `Watchdog`, `Triggered`).
Stacja może wysłać puste lub obcięte pola (limity długości), więc brak numeru seryjnego nie dowodzi braku
urządzenia, a zgodność prefiksu nie dowodzi tożsamości.

## 4. Uzgadnianie rejestru ze stacją
| Rozjazd | Zwykła przyczyna | Reakcja |
|---|---|---|
| Inny numer seryjny niż w rejestrze | wymiana sprzętu bez zapisu, stacja przepięta pod cudzy identyfikator CSMS | alarm; stacja `Pending`, zlecenie weryfikacji w terenie |
| Inny model lub vendor | podmiana, błąd montera | alarm; brak `Accepted`; szablon konfiguracji nie jest stosowany |
| Firmware inny niż zlecony | aktualizacja nieudana lub ręczna, wycofanie | wpis zdarzenia; ponów aktualizację albo uznaj za odchylenie |
| Firmware nieznany w katalogu | niedopuszczona wersja | `Pending`; onboarding wersji: `dom-ev-charger-onboarding` |
| Stacja w CSMS, brak w rejestrze | brak procesu przyjęcia | `Rejected`, alarm; nie twórz rekordu automatycznie |
| Rekord w rejestrze, stacja milczy | stan `IN_STOCK`/`PLANNED` (oczekiwane) albo awaria | sprawdź stan: tylko w `OPERATIONAL` brak połączenia to incydent |
| Licznik: inny numer seryjny | wymiana licznika bez legalizacji | blokada publikacji danych legalnych; zdarzenie legalizacji |
Zasada: rozjazd zgłasza człowiekowi albo zleceniu; automatyczna aktualizacja rejestru dozwolona tylko dla pól
oznaczonych jako „telemetria” (np. firmware), z zapisem zdarzenia.

## 5. Legalizacja licznika jako zdarzenie
Rejestr trzyma: numer seryjny licznika, datę ostatniej legalizacji lub oceny zgodności, ważność, numer plomby,
zdarzenia (uruchomienie, wymiana, zerwanie plomby, zmiana firmware metrologicznego). Przypomnienie z wyprzedzeniem
wynikającym z umowy serwisowej [założenie]. Okres legalizacji i organ w Polsce: **[do weryfikacji]** (brak aktu
w bazie); szczegóły: `dom-ev-metering-calibration`, wymogi UDT: `dom-ev-regulations-pl`.
