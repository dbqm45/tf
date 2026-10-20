# Komunikaty OCPP 1.6 wg profili

Źródło: `dom-ev-charging/references/ocpp.md` (sekcja 4). Przypisanie do profili i kierunki, których tam nie ma —
**[do weryfikacji]** w specyfikacji OCA. Kierunek: CP = ładowarka, CS = CSMS.

| Profil | CP → CS | CS → CP |
|---|---|---|
| Core | `BootNotification`, `Heartbeat`, `StatusNotification`, `Authorize`, `StartTransaction`, `StopTransaction`, `MeterValues` | `RemoteStartTransaction`, `RemoteStopTransaction`, `ChangeConfiguration`, `GetConfiguration`, `ChangeAvailability`, `Reset`, `UnlockConnector`, `ClearCache` |
| Firmware Management | `FirmwareStatusNotification`, `DiagnosticsStatusNotification` | `UpdateFirmware`, `GetDiagnostics` |
| Local Auth List Management | — | `SendLocalList`, `GetLocalListVersion` |
| Reservation | — | `ReserveNow`, `CancelReservation` |
| Smart Charging | — | `SetChargingProfile`, `ClearChargingProfile`, `GetCompositeSchedule` |
| Remote Trigger | — | `TriggerMessage` |
| (poza profilami) | `DataTransfer` | `DataTransfer` |

Uwagi:
- Przypisanie `RemoteStartTransaction`/`ChangeConfiguration` itd. do Core i `DataTransfer` do Core — **[do weryfikacji]**.
- `ocpp.md` liczy 28 akcji w 1.6 Edition 2 (10 od ładowarki, 18–19 od CSMS, plus `DataTransfer`); dokładny podział
  przy liczbie 18 vs 19 — **[do weryfikacji]**.
- Security Whitepaper ed. 2 dodaje komunikaty bezpieczeństwa (11 wg `ocpp.md`; nazwy **[do weryfikacji]** — nie
  wymyślaj ich z pamięci).
- `TriggerMessage` prosi ładowarkę o wysłanie wskazanego komunikatu (np. `StatusNotification`, `MeterValues`,
  `BootNotification`); lista obsługiwanych **[do weryfikacji]**.
- Odpowiedź ładowarki na komendy CSMS to zwykle `status` (`Accepted`/`Rejected`/`NotSupported` itp. —
  wartości per komunikat **[do weryfikacji]**).
