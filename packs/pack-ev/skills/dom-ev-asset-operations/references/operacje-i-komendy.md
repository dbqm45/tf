# Operacje NOC — monitoring, komendy, szablony, runbooki

Spis: 1. Monitoring · 2. Alarmy i kody błędów · 3. Zdalne komendy (pola) · 4. Szablony konfiguracji · 5. Runbook ·
6. Eskalacja i SLA · 7. PAUSED.

## 1. Monitoring
| Sygnał | Co mówi | Uwaga |
|---|---|---|
| Połączenie WebSocket | stacja jest podłączona | połączenie bywa „zombie”: brak ruchu mimo otwartego gniazda |
| `Heartbeat` | żywotność w odstępie z odpowiedzi na `BootNotification` (`interval`) | brak 2–3 odstępów = offline [próg do ustawienia per model] |
| `StatusNotification` | stan konektora i `errorCode`, `vendorErrorCode`, `info` | tylko zmiany; stan po restarcie z `TriggerMessage` |
| `MeterValues` | moc, energia, temperatury (jeśli stacja je wysyła) | źródło danych degradacji |
| `BootNotification` | restart lub nowa stacja; w 2.0.1 `reason` | częste boot-y = pętla restartów lub zasilanie |
| `FirmwareStatusNotification` / `DiagnosticsStatusNotification` | postęp aktualizacji i wysyłki logów | w 2.0.1 `LogStatusNotification` |
Offline: stacja bez połączenia nie zgłasza usterek. Odróżnij „offline” od „Faulted”: inny runbook (`dom-ev-diagnostics`).
Stacja offline w stanie `IN_STOCK`, `PLANNED`, `DECOMMISSIONED` nie jest incydentem.

## 2. Alarmy i kody błędów
- `errorCode` w `StatusNotification` 1.6 to zamknięty zbiór: `ConnectorLockFailure`, `EVCommunicationError`,
  `GroundFailure`, `HighTemperature`, `InternalError`, `LocalListConflict`, `NoError`, `OtherError`, `OverCurrentFailure`,
  `PowerMeterFailure`, `PowerSwitchFailure`, `ReaderFailure`, `ResetFailure`, `UnderVoltage`, `OverVoltage`, `WeakSignal`.
  `vendorErrorCode` (do 50 znaków) i `vendorId` niosą kod producenta; przy `OtherError` to jedyna treść.
- Katalog kodów producentów: tabela (vendor, model, firmware, `vendorErrorCode`) → znaczenie, wpływ, runbook, część.
  Znaczenie bierz z dokumentacji producenta; własne domysły oznacz [założenie]. Bez wpisu w katalogu kod trafia
  do kolejki „nieznane”, a nie jest ignorowany.
- Priorytet = wpływ × zasięg: port nieczynny, stacja nieczynna, kilka stacji tego samego modelu (przyczyna wspólna:
  firmware, sieć, zasilanie lokacji). Alarmy grupuj po lokalizacji i po (model, firmware).
- Deduplikacja i wyciszenia: powtarzający się `errorCode` zliczaj (to sygnał degradacji, `references/om-i-degradacja.md`),
  alarmu nie rozsyłaj co minutę; wyciszenie na czas `MAINTENANCE` z terminem.

## 3. Zdalne komendy (pola ze schematów)
| Komenda | OCPP 1.6 | OCPP 2.0.1 |
|---|---|---|
| `Reset` | `type`: `Hard`, `Soft` | `type`: `Immediate`, `OnIdle`; opcjonalnie `evseId` |
| `ChangeAvailability` | `connectorId`, `type`: `Inoperative`, `Operative` | `operationalStatus` (te same wartości), opcjonalnie `evse` (`id`, `connectorId`) |
| `TriggerMessage` | `requestedMessage`: `BootNotification`, `DiagnosticsStatusNotification`, `FirmwareStatusNotification`, `Heartbeat`, `MeterValues`, `StatusNotification`; opcjonalnie `connectorId` | `requestedMessage` m.in. `BootNotification`, `LogStatusNotification`, `FirmwareStatusNotification`, `Heartbeat`, `MeterValues`, `StatusNotification`, `TransactionEvent`, `SignChargingStationCertificate`, `PublishFirmwareStatusNotification`; opcjonalnie `evse` |
| Logi | `GetDiagnostics`: `location` (URI), `startTime`, `stopTime`, `retries`, `retryInterval` | `GetLog`: `logType` (`DiagnosticsLog`, `SecurityLog`), `requestId`, `log` (`remoteLocation`, `oldestTimestamp`, `latestTimestamp`), `retries`, `retryInterval` |
| Firmware | `UpdateFirmware`: `location`, `retrieveDate`, `retries`, `retryInterval` | `UpdateFirmware`: `requestId`, `firmware` (`location`, `retrieveDateTime`, `installDateTime`, `signingCertificate`, `signature`), `retries`, `retryInterval` |
| Konfiguracja | `GetConfiguration`, `ChangeConfiguration` (`key`, `value`) | `GetVariables`/`SetVariables` (komponent, zmienna, `attributeType`: `Actual`, `Target`, `MinSet`, `MaxSet`, domyślnie `Actual`) |
| Odblokowanie złącza | `UnlockConnector` (`connectorId`) | `UnlockConnector` (`evseId`, `connectorId`) |
Statusy odpowiedzi wg schematów (ocpp-json-schemas, pobrane 2026-10-20):
| Komenda | 1.6 | 2.0.1 |
|---|---|---|
| `ChangeAvailability` | Accepted, Rejected, Scheduled | Accepted, Rejected, Scheduled |
| `Reset` | Accepted, Rejected | Accepted, Rejected, Scheduled |
| `TriggerMessage` | Accepted, Rejected, NotImplemented | Accepted, Rejected, NotImplemented |
| `UnlockConnector` | Unlocked, UnlockFailed, NotSupported | Unlocked, UnlockFailed, OngoingAuthorizedTransaction, UnknownConnector |
| `UpdateFirmware` | (brak statusu w odpowiedzi; postęp przez FirmwareStatusNotification) | Accepted, Rejected, AcceptedCanceled, InvalidCertificate, RevokedCertificate |

`Accepted` znaczy „przyjąłem polecenie”, nie „wykonałem”: skutek sprawdzaj zdarzeniem (StatusNotification, Boot,
FirmwareStatusNotification). `Scheduled` przy `ChangeAvailability` to odroczenie do końca trwającej sesji.
Zasady komend:
1. Komenda to polecenie z numerem zlecenia i właścicielem; zapisz ramkę i odpowiedź. Komendy jak `Reset` i
   `UpdateFirmware` wykonuje rola z uprawnieniem, nie każdy operator NOC.
2. Przed `Reset`/`UpdateFirmware` sprawdź trwającą sesję; `Hard` i `Immediate` ją przerywają.
3. Komenda na stacji w stanie `IN_STOCK`/`DECOMMISSIONED` jest zablokowana w CSMS.
4. Odpowiedź asynchroniczna (`FirmwareStatusNotification`, `LogStatusNotification`) kończy zlecenie, nie wysłanie.
5. URL w `GetDiagnostics`/`GetLog`/`UpdateFirmware` o krótkim czasie życia, bez haseł w ścieżce, z kontrolą pobrań.

## 4. Szablony konfiguracji
Szablon = zestaw wartości `ChangeConfiguration` (1.6) lub `SetVariables` (2.0.1) per **(vendor, model, wersja firmware,
wersja OCPP)**. Wersjonuj szablon; stacja wchodzi w `OPERATIONAL` z szablonem przypisanym przy `COMMISSIONING`.
Dla 1.6 klucze są płaskie i część jest zależna od producenta; dla 2.0.1 adresujesz komponent i zmienną. Po
zastosowaniu odczytaj wartości (`GetConfiguration`/`GetVariables`) i porównaj z szablonem; różnica = rozjazd (alarm
„drift konfiguracji”). Klucze dotyczące bezpieczeństwa (profil, poświadczenia) zmieniaj osobnym, uprawnionym przepływem.
Zawartość kart modeli i odchylenia producentów: `dom-ev-charger-onboarding`.

## 5. Runbook — szkielet
Nazwa i wyzwalacz (alarm/kod) · wpływ · warunki wstępne (brak sesji, stan assetu) · kroki zdalne w kolejności od
najmniej inwazyjnego (odczyt → `TriggerMessage` → `Soft`/`OnIdle` reset → `Hard` reset) · kryterium sukcesu
(`StatusNotification` `Available`, sesja testowa) · kiedy eskalować (nie wraca po N próbach, powtarza się w tej
samej kohorcie) · dane do zgłoszenia (stacja, EVSE, vendor, model, firmware, kod, ramki, logi `GetLog`).
Diagnozę z dowodem prowadzi `dom-ev-diagnostics`; runbook mówi, co zrobić operacyjnie i kiedy przekazać dalej.

## 6. Eskalacja i SLA
Poziomy: NOC (zdalnie) → serwis zewnętrzny/własny technik → producent (RMA, błąd firmware). Zgłoszenie serwisowe
dostaje czas reakcji i naprawy z SLA assetu; zegar startuje od utworzenia zgłoszenia lub od incydentu zgodnie z umową
[do ustalenia w umowie]. MTTR i dostępność liczysz w `dom-ev-kpi-analytics`; tu zapisujesz znaczniki czasu zdarzeń
(wykrycie, zgłoszenie, przyjazd, naprawa, test sesji), z których KPI powstaje.

## 7. PAUSED
Decyzja operatora (np. pogorszone bezpieczeństwo, spór z właścicielem terenu, oczekiwanie na przyłącze). Port jest
niedostępny dla kierowcy, publikujesz `INOPERATIVE` (nie `OUTOFORDER`: sprzęt sprawny). Dostępność: liczy się jako
przestój, dopóki umowa lub przepis nie wyłącza tej przyczyny (NEVI wyłącza tylko wymienione przyczyny, 23 CFR
680.116(b)(3)). Zapisz powód, właściciela i datę przeglądu; `PAUSED` bez terminu przechodzi po czasie w
`OBSOLETE`/`DECOMMISSIONED` albo wraca do `OPERATIONAL`.
