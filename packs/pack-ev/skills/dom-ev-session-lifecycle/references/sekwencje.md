# Sekwencje komunikatów — sesja ładowania

Źródło: `cykl-sesji-ladowania.md` w `dom-ev-charging` (import 2024–2025) i skille `dom-ev-ocpp-16`, `dom-ev-ocpp-2x`.
Nazwy pól i wartości spoza tych źródeł: **[do weryfikacji]**. Strzałki OCPI: HTTP między CSMS (rola CPO) a eMSP.

## 1. OCPP 1.6 z aplikacji eMSP
```
Kierowca -> aplikacja -> eMSP
eMSP  -> CPO      OCPI Commands START_SESSION (token, evse_uid, response_url)
CPO   -> eMSP     HTTP odpowiedź: komenda przyjęta (nie wynik)
CSMS  -> ładowarka  RemoteStartTransaction(idTag, connectorId)
ładowarka -> CSMS   RemoteStartTransaction.conf  Accepted | Rejected
CSMS  -> eMSP     POST response_url: wynik komendy (ACCEPTED / błąd)            [asynchronicznie]
(kabel wpięty) ładowarka -> CSMS  StatusNotification(Preparing)
ładowarka -> CSMS   StartTransaction(connectorId, idTag, meterStart[Wh], timestamp)
CSMS  -> ładowarka  StartTransaction.conf(transactionId, idTagInfo)    <- id nadaje CSMS
ładowarka -> CSMS   StatusNotification(Charging)
CSMS  -> eMSP     PUT Session  status ACTIVE
ładowarka -> CSMS   MeterValues(transactionId, odczyty)    <- pierwszy podgląd energii
CSMS  -> eMSP     PATCH Session (kwh, last_updated)
...
ładowarka -> CSMS   StopTransaction(transactionId, meterStop[Wh], timestamp, reason)
ładowarka -> CSMS   StatusNotification(Finishing) -> Available
CSMS  -> eMSP     Session: zakończona
CSMS  -> eMSP     POST CDR   (po ustaleniu energii i oknie na spóźnione ramki)
```
- Kolejność `StatusNotification(Preparing)` względem `RemoteStartTransaction` zależy od tego, czy kabel jest
  już wpięty. Ładowarka bez kabla zwykle czeka na wpięcie **[do weryfikacji]** u producenta.
- Czy ładowarka dodatkowo wysyła `Authorize` po `RemoteStartTransaction`, zależy od jej konfiguracji
  **[do weryfikacji]** (klucze: `GetConfiguration`, nie z pamięci).

## 2. OCPP 2.0.1 z aplikacji eMSP
```
eMSP  -> CPO      OCPI START_SESSION
CSMS  -> stacja     RequestStartTransaction(idToken, evseId, remoteStartId)
stacja -> CSMS      response: Accepted | Rejected
CSMS  -> eMSP     POST response_url: wynik komendy
stacja -> CSMS      TransactionEvent(Started, seqNo 0, transactionInfo.transactionId)   <- id nadaje stacja
CSMS  -> eMSP     PUT Session ACTIVE
stacja -> CSMS      TransactionEvent(Updated, seqNo 1..n, meterValue)   (okresowo)
stacja -> CSMS      TransactionEvent(Ended, seqNo n+1, stoppedReason, meterValue)
CSMS  -> eMSP     Session zakończona, potem POST CDR
```
- Pierwszy `seqNo` w transakcji (0 lub 1) i wartości `triggerReason`: **[do weryfikacji]** w specyfikacji.
- Moment końca transakcji zależy od konfiguracji (`TxStopPoint`, `cykl-sesji-ladowania.md`); ustal go jawnie.
- Luki i duplikaty `seqNo`: `dom-ev-ocpp-2x`.

## 3. RFID (obie wersje)
```
kierowca -> czytnik
ładowarka -> CSMS   Authorize(idTag | idToken)
CSMS: lokalna lista / token z OCPI Tokens / zapytanie do eMSP (real-time authorization)
CSMS  -> ładowarka  Authorize.conf (Accepted | Blocked | Expired | Invalid ...)
dalej jak w sekcji 1 (StartTransaction) lub 2 (TransactionEvent Started)
```
Offline: ładowarka sięga do lokalnej listy (`SendLocalList`) i cache. Sesja z lokalnej listy może wejść do CSMS
dopiero po powrocie łączności — zob. `projekt-obslugi-sesji.md`.

## 4. Terminal płatniczy (ad hoc)
Terminal blokuje kwotę (preautoryzacja) → system płatności zleca start CSMS → dalej jak w sekcji 1/2, ale token
jest wewnętrzny, a rozliczenie bezpośrednie (capture po CDR/zamknięciu sesji). OCPI nie uczestniczy **[założenie]**,
chyba że terminal działa przez eMSP/hub.

## 5. Porównanie
| Zdarzenie | 1.6 | 2.0.1 |
|---|---|---|
| Polecenie zdalnego startu | `RemoteStartTransaction` | `RequestStartTransaction` |
| Start transakcji | `StartTransaction` | `TransactionEvent` `Started` |
| Kto nadaje id transakcji | CSMS | stacja |
| Telemetria | `MeterValues` | `TransactionEvent` `Updated` (może być też `MeterValues` poza transakcją) |
| Koniec | `StopTransaction` | `TransactionEvent` `Ended` |
| Energia | `meterStop − meterStart` (Wh) | odczyty licznika w zdarzeniach |
| Kolejność zdarzeń offline | czas zdarzenia | `seqNo` |
