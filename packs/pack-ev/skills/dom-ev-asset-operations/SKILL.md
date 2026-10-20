---
name: dom-ev-asset-operations
description: Użyj przy rejestrze assetów i utrzymaniu stacji CPO — cykl życia, wygaszanie EVSE ID, zdalne komendy, O&M, degradacja, PAUSED, decommissioning.
metadata:
  przeglad: 2027-04-20
  katalog: "Użyj, gdy CPO prowadzi rejestr assetów infrastruktury ładowania i jej utrzymanie od strony software — atrybuty assetu, maszyna stanów cyklu życia i jej skutki dla OCPI (PLANNED, REMOVED) oraz NEVI, nadawanie i wygaszanie EVSE ID, wymiana sprzętu pod tym samym EVSE, rozjazd rejestru z BootNotification, zdalne komendy, szablony konfiguracji, runbooki, O&M, części zamienne, degradacja z telemetrii i predictive maintenance, firmware, repowering, decommissioning. Nie do diagnozy konkretnej awarii od objawu (dom-ev-diagnostics), onboardingu nowego modelu (dom-ev-charger-onboarding), liczenia KPI i raportów (dom-ev-kpi-analytics), migracji między CSMS (dom-ev-csms-migration) ani formatu EVSE ID (dom-ev-identifiers)."
  slowa: "rejestr assetów, asset management, cykl życia stacji, magazyn, IN_STOCK, commissioning, decommissioning, likwidacja stacji, demontaż, wymiana ładowarki, ponowne użycie EVSE ID, wygaszone EVSE ID, REMOVED, PLANNED, PAUSED, wyłączenie z ruchu, serwis, O&M, przegląd prewencyjny, zgłoszenie serwisowe, części zamienne, moduł mocy, degradacja, spadek mocy, predictive maintenance, runbook, zdalny reset, ChangeAvailability, TriggerMessage, GetLog, UpdateFirmware, szablon konfiguracji, nr seryjny, legalizacja licznika, repowering, asset register, lifecycle, spare parts, charger degradation, ładowarki dają coraz mniej kW, ten sam kod producenta wraca, wyłapać ładowarki do przeglądu, zanim padną, flota ładowarek DC tego samego modelu"
---

# Aktywa CPO — rejestr, cykl życia i utrzymanie

Skill o tym, **co operator ma, w jakim jest stanie i co z tego widzi świat**. Nazwy stanów to przykład z branży;
w konkretnym CSMS bywają inne [założenie]. Granice:
- diagnoza awarii od objawu i dowód z ramek → `dom-ev-diagnostics`;
- wprowadzenie nowego modelu lub firmware do sieci (karta, testy, pilotaż) → `dom-ev-charger-onboarding`;
- uptime, MTTR, MTBF jako liczby i raporty → `dom-ev-kpi-analytics`; przeniesienie stacji do innego CSMS → `dom-ev-csms-migration`;
- format EVSE ID → `dom-ev-identifiers`; pola komunikatów → `dom-ev-ocpp-16`, `dom-ev-ocpp-2x`; moc lokacji → `dom-ev-energy-management`;
- licznik i legalizacja → `dom-ev-metering-calibration`; wymogi prawne → `dom-ev-regulations-pl`, `dom-ev-regulations-us`, `dom-ev-regulations-eu`.

## Procedura: zmiana stanu assetu
1. **Zidentyfikuj asset** w rejestrze (numer seryjny, pozycja w hierarchii), nie po tym, co zgłasza stacja.
2. **Sprawdź przejście** w tabeli stanów niżej; niedozwolone przejście = odmowa z powodem.
3. **Zapisz zdarzenie** w historii (kto, kiedy, powód, zlecenie); stan zmienia się tylko przez zdarzenie.
4. **Wykonaj skutki:** CSMS (przyjmowanie połączeń, komendy), publikacja (OCPI, mapy, rejestry), alarmy (wyciszenie
   na czas prac), licznik i legalizacja.
5. **Sprawdź skutek** po drugiej stronie: stacja zgłosiła się z oczekiwanym vendor/model/firmware, eMSP widzi nowy status.

## Co jest assetem
Szczegóły i atrybuty: `references/rejestr-assetow.md`. Asset ma własny cykl życia, numer seryjny lub inną tożsamość i
historię serwisową; stacja jest tylko jednym z nich.
| Grupa | Przykłady | Dlaczego osobny rekord |
|---|---|---|
| Ładowarka | stacja, dispenser, szafa mocy, moduły mocy, kable DC | moduł i kabel wymienia się bez wymiany stacji |
| Pomiar | licznik energii z datą legalizacji, plomby | legalizacja to zdarzenie z terminem |
| Łączność | modem, karta SIM, router | SIM ma własną umowę i `iccid`/`imsi` |
| Płatność | terminal płatniczy | osobny dostawca, serwis i certyfikacja |
| Energia | transformator, rozdzielnia, BESS, PV | wspólne dla wielu stacji |
| Budowlane | fundament, wiata, oznakowanie, ogrodzenie | koszt i okres życia inne niż sprzętu |

## Cykl życia — stany i przejścia
| Stan | Znaczenie | Publikacja zewnętrzna |
|---|---|---|
| `PLANNED` | w planie lub umowie; sprzęt jeszcze nie jest przypisany | NEVI: *planned*; OCPI: `PLANNED` albo brak publikacji [decyzja operatora] |
| `UNDER_CONSTRUCTION` | budowa lub montaż w toku | NEVI: *under construction*; OCPI nie ma osobnej wartości → `PLANNED` |
| `IN_STOCK` | sprzęt w magazynie, bez lokalizacji | brak; stacja nie ma prawa łączyć się z produkcją |
| `COMMISSIONING` | zamontowana, odbiory i testy (`dom-ev-charger-onboarding`) | OCPI `INOPERATIVE` („not yet active”) albo `PLANNED`; nie `AVAILABLE` |
| `OPERATIONAL` | w ruchu; status chwilowy (`Available`, `Faulted`) to inny wymiar | NEVI: *operational*; OCPI według `StatusNotification` |
| `MAINTENANCE` | prace serwisowe, krótkie, z planem powrotu | `INOPERATIVE` (planowane) lub `OUTOFORDER` (awaria) |
| `PAUSED` | wyłączona z ruchu decyzją operatora, sprzęt sprawny | `INOPERATIVE`; uptime: sekcja „PAUSED” niżej |
| `OBSOLETE` | koniec wsparcia lub opłacalności, jeszcze działa | bez zmian do wyłączenia |
| `DECOMMISSIONED` | trwale wyłączona | OCPI `REMOVED` (nie usuwasz obiektu); NEVI: *decommissioned* |

| Przejście | Kto wyzwala | Warunek i skutek |
|---|---|---|
| `PLANNED` → `UNDER_CONSTRUCTION` | projekt/budowa | pozwolenie i umowa; EVSE ID zarezerwowane, nie aktywne |
| → `IN_STOCK` | magazyn | numer seryjny w rejestrze; blokada w CSMS |
| `IN_STOCK` → `COMMISSIONING` | monter + operator | przypisanie do lokalizacji; stacja dostaje `Accepted` dopiero tu |
| `COMMISSIONING` → `OPERATIONAL` | odbiór (protokół, test sesji, licznik) | publikacja `AVAILABLE`, wpis EIPA/rejestru (→ `dom-ev-regulations-pl`) |
| `OPERATIONAL` ↔ `MAINTENANCE`, `PAUSED` | NOC, serwis, handlowy | `ChangeAvailability`; powrót przez test sesji |
| `OPERATIONAL` → `OBSOLETE` | zarząd aktywami | plan repoweringu; nic nie zmienia się w publikacji |
| `OPERATIONAL`/`OBSOLETE` → `DECOMMISSIONED` | zarząd + NOC | ostatnia sesja zamknięta, `REMOVED` wypchnięte, dane i licznik rozliczone |
| `DECOMMISSIONED` → inny | nie wolno | sprzęt wraca jako **nowy** asset lub idzie do utylizacji; EVSE ID nie wraca |
Pełne reguły, skutki w CSMS i wyjątki (RMA, sprzęt z demontażu): `references/cykl-zycia-i-publikacja.md`.

## EVSE ID — kiedy się nie zmienia
| Zdarzenie | EVSE ID | Uwaga |
|---|---|---|
| Wymiana sprzętu 1:1 w tym samym miejscu | bez zmian | zmieniają się numer seryjny i firmware w rejestrze; historia (CDR, sesje) zostaje przy EVSE |
| Aktualizacja firmware, wymiana modułu, kabla, licznika | bez zmian | legalizacja nowego licznika jako zdarzenie |
| Zmiana liczby lub typu złączy | decyzja | złącze to Connector; nowy punkt ładowania dostaje nowe ID |
| Przeniesienie do innej lokalizacji | nowe | stare ID → `DECOMMISSIONED`/`REMOVED` |
| Zmiana operatora (nowy `operator_id`) | nowe | ID zawiera identyfikator operatora (`dom-ev-identifiers`) |
| Wygaszone EVSE ID | nigdy ponownie | eMSP i huby trzymają je w historii, CDR i fakturach |
`uid` w OCPI jest stały i nie powinien być numerem sprzętu — wtedy wymiana stacji nie łamie jego unikalności i
reguły „EVSE nie jest usuwane” (OCPI 2.2.1-d2, Locations).

## Hierarchia i źródło prawdy
Location → (grupa EVSE) → Charging Station → EVSE → Connector. **Rejestr jest źródłem prawdy** o tym, co operator ma
i gdzie; **stacja** jest źródłem prawdy o tym, co ma w sobie teraz (`BootNotification`: w 1.6 `chargePointVendor`,
`chargePointModel`, `chargePointSerialNumber`, `firmwareVersion`, `iccid`, `imsi`, `meterType`, `meterSerialNumber`;
w 2.0.1 `chargingStation` z `vendorName`, `model`, `serialNumber`, `firmwareVersion`, `modem`, plus `reason`). Rozjazd
(inny numer seryjny, inny model, nieznany firmware) to alarm, nie cicha aktualizacja rejestru. Reguły uzgadniania:
`references/rejestr-assetow.md`.

## Operacje (NOC)
| Cel | Komenda 1.6 / 2.0.1 | Pułapka |
|---|---|---|
| Wyłączyć z ruchu | `ChangeAvailability` (`connectorId`, `type`: Inoperative/Operative) / (`evse`, `operationalStatus`) | przy trwającej sesji stacja odpowiada `Scheduled` i odracza zmianę; potwierdź `StatusNotification` |
| Zrestartować | `Reset` (`Hard`/`Soft`) / (`Immediate`/`OnIdle`, opcjonalnie `evseId`) | reset przerywa sesję; użyj `OnIdle` lub sprawdź, że nie ma sesji |
| Wymusić odczyt stanu | `TriggerMessage` (`StatusNotification`, `Heartbeat`, `BootNotification`, `MeterValues`, …) | w 2.0.1 inna lista wartości (m.in. `LogStatusNotification`) |
| Pobrać logi | `GetDiagnostics` (`location`, `startTime`, `stopTime`) / `GetLog` (`logType`: DiagnosticsLog, SecurityLog; `requestId`; `log.remoteLocation`) | URL z danymi uwierzytelniającymi trafia do logów |
| Zaktualizować firmware | `UpdateFirmware` (`location`, `retrieveDate`, `retries`) / (`firmware`: `location`, `retrieveDateTime`, `installDateTime`, `signature`) | tylko po onboardingu wersji i etapami |
| Zmienić konfigurację | `ChangeConfiguration` (klucz, wartość) / `SetVariables` (komponent, zmienna, `attributeType`) | wartość z szablonu per model i firmware, nie ręcznie |
Pola komend i wartości wyliczeniowe: `references/operacje-i-komendy.md` (w tym statusy odpowiedzi i runbooki).

## O&M, degradacja, firmware
Prewencyjne i korekcyjne zgłoszenia, części, SLA: `references/om-i-degradacja.md`. Degradację z telemetrii
(spadek maks. mocy, moduły, temperatury, powtarzające się kody) analizujesz **kohortą model × firmware**, nie pojedynczą
stacją. Firmware wdrażasz etapami (pilotaż → fala → flota) i tylko podpisany. Decommissioning kończy się
usunięciem danych osobowych, rozliczeniem licznika i utylizacją.

## PAUSED a uptime
`PAUSED` ukrywa przestój w widoku NOC, ale **nie** w liczeniu dostępności: port wyłączony decyzją operatora jest
niedostępny dla kierowcy. W NEVI (23 CFR 680.116(b)) wyłączone są tylko wymienione przyczyny (m.in. zaplanowana
konserwacja, godziny poza czasem pracy stacji), więc `PAUSED` z powodu np. oszczędności tego nie spełnia. Liczby:
`dom-ev-kpi-analytics` (`uptime_kpi.py`).

## Przykład
Wejście: zamykamy parking A (stacje `PL*ABC*E100`, `PL*ABC*E101`), nową stację stawiamy przy sklepie B; ktoś proponuje
nadać jej `PL*ABC*E100`.
Wynik:
1. Decyzja: nie. Zmiana lokalizacji = nowe EVSE ID (`PL*ABC*E200`, `PL*ABC*E201`); stare nie wracają.
2. Stare EVSE: `OPERATIONAL` → `DECOMMISSIONED`; `PATCH`/`PUT` z `status: REMOVED` do eMSP (bez `DELETE`), Location
   bez ważnych EVSE uznana za wygasłą.
3. Nowe: `PLANNED` → `UNDER_CONSTRUCTION` → `IN_STOCK` → `COMMISSIONING` (`INOPERATIVE`) → `OPERATIONAL` (`AVAILABLE`).
4. Zdemontowana stacja wraca do magazynu jako ten sam asset (numer seryjny) z nowym przypisaniem — nie jako stare EVSE.

## Pułapki
- Stacja w `IN_STOCK` wysyła `BootNotification` (podpięta na biurku, zła konfiguracja): odpowiedź `Rejected` lub
  `Pending`, alarm w rejestrze; `Accepted` nie może być efektem ubocznym.
- Usunięcie EVSE z bazy zamiast `REMOVED`: sesje, CDR i `Sessions` w OCPI tracą odniesienie.
- Wymiana stacji pod tym samym EVSE ID bez zapisu w rejestrze: stary numer seryjny nadal ma w historii przypisany
  punkt, szablon konfiguracji i certyfikat pochodzą z poprzedniego modelu.
- Rejestr nadpisywany automatycznie danymi z `BootNotification`: zły wpis stacji staje się „prawdą”.
- `MAINTENANCE` bez końca: ręczny stan bez terminu zawyża przestój lub go ukrywa. Wymagaj terminu i przypomnienia.
- `PAUSED` liczony jako dostępność albo jako wyłączenie z uptime bez podstawy.
- Terminal płatniczy, SIM i licznik poza rejestrem: wygasła umowa SIM lub legalizacja wychodzi po awarii.
- Rejestr w płaskiej tabeli: moduł mocy nie ma własnej historii, więc degradacji nie da się przypisać.

## Checklista
- [ ] Asset ma tożsamość (numer seryjny), pozycję w hierarchii i historię zdarzeń
- [ ] Stan zmienia się tylko dozwolonym przejściem, ze zdarzeniem i powodem
- [ ] Publikacja zgodna ze stanem (OCPI `PLANNED`/`INOPERATIVE`/`REMOVED`, NEVI, EIPA)
- [ ] EVSE ID nie użyte ponownie; `uid` niezależny od numeru sprzętu
- [ ] Rozjazd rejestr ↔ `BootNotification` generuje alarm
- [ ] Szablon konfiguracji przypisany do modelu i firmware; firmware podpisany, wdrażany etapami
- [ ] Wyłączenie z ruchu (`PAUSED`, `MAINTENANCE`) ma właściciela, powód i termin
- [ ] Decommissioning: sesje zamknięte, `REMOVED`, dane usunięte, licznik rozliczony, utylizacja udokumentowana

## Czytaj references, gdy…
| Pytanie | Plik |
|---|---|
| lista typów assetów, atrybuty, model danych, uzgadnianie rejestru ze stacją, legalizacja jako zdarzenie | `references/rejestr-assetow.md` |
| pełne przejścia, publikacja OCPI/NEVI/EIPA, reguły EVSE ID, wymiana, repowering, decommissioning | `references/cykl-zycia-i-publikacja.md` |
| pola komend, szablony konfiguracji, monitoring, alarmy, runbooki i eskalacja | `references/operacje-i-komendy.md` |
| O&M, części, SLA, analiza degradacji, predictive maintenance, firmware i cyberbezpieczeństwo | `references/om-i-degradacja.md` |

## Źródła
Baza wiedzy fabryki (pobrane 2026-10-20): OCPI 2.2.1-d2 i 2.3.0, `mod_locations.asciidoc` (EVSE `status`, `REMOVED`,
`PLANNED`, `INOPERATIVE`, zasada „nigdy nie usuwaj EVSE”, `StatusSchedule`; github.com/ocpi/ocpi, tagi v2.2.1-d2 i v2.3.0);
23 CFR 680.112 i 680.116 (eCFR, status stacji i wzór uptime); schematy OCPP 1.6 i 2.0.1 (`BootNotification`,
`StatusNotification`, `ChangeAvailability`, `Reset`, `TriggerMessage`, `GetDiagnostics`, `GetLog`, `UpdateFirmware`,
`SetVariables`; github.com/mobilityhouse/ocpp); skille fabryki wymienione w tekście. Luki: `docs/backlog-wiedza-ogolna-ev.md`, sekcje 10 i 14. Stany cyklu życia i praktyki O&M to wiedza branżowa [założenie], nie wymóg specyfikacji.
