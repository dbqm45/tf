# Free vend, kiosk i STOP_FAILED

> **Spis treści:** 1. Free vend (ładowanie bez autoryzacji) · 2. Konfiguracja po stronie stacji · 3. Kiosk (terminal lub ekran jako punkt startu) · 4. STOP_FAILED · 5. Obsługa STOP_FAILED · 6. Wpływ na CDR i raporty · 7. Pułapki · 8. Źródła
> Spis: 1. Free vend · 2. Konfiguracja 1.6 i 2.0.1 · 3. Kiosk · 4. STOP_FAILED · 5. Obsługa krok po kroku · 6. Wpływ na CDR i raporty · 7. Pułapki · 8. Źródła

Wiedza ogólna branży o procesach operatora (CPO), bez nazw firm i systemów. Co sprawdzono w schematach JSON OCPP
(baza `ocpp-json-schemas`), oznaczono; reszta to praktyka lub [do weryfikacji] w specyfikacji OCA i karcie producenta.

## 1. Free vend (ładowanie bez autoryzacji)
Free vend: stacja zaczyna ładowanie po wpięciu kabla, bez karty, aplikacji i bez pytania CSMS. Używane przy ładowaniu
bezpłatnym lub rozliczanym poza systemem (hotel, recepcja, parking firmowy, serwis, stacja testowa).
- **To nadal pełna sesja:** transakcja (`StartTransaction` / `TransactionEvent Started`), `MeterValues`, zakończenie. Bez nich
  nie masz energii, kosztu własnego, utilization ani raportu.
- **Token techniczny:** w 1.6 `idTag` jest w `StartTransaction` wymagany (pole `required` w schemacie
  StartTransaction 1.6), więc stacja podstawia stały znacznik (nazwa zależy od producenta). W 2.0.1 `idToken` w `TransactionEvent` jest
  opcjonalny (schemat: wymagane tylko `eventType`, `timestamp`, `triggerReason`, `seqNo`, `transactionInfo`), a typ tokenu
  `NoAuthorization` istnieje w `IdTokenEnumType`. W CSMS utwórz **jawny token techniczny „free vend” per stacja lub grupa**,
  zamiast odrzucać nieznany `idTag`.
- **Dane do raportu:** oznacz sesję `sposob_autoryzacji = free_vend`, trzymaj energię z licznika, wyłącz naliczanie ceny
  (taryfa zerowa, `dom-ev-tariffs-pricing`) lub zapisz koszt własny energii do rozliczeń wewnętrznych.
- **Roaming:** sesja free vend nie ma tokenu eMSP, więc nie ma Session ani CDR do eMSP (`dom-ev-ocpi`).
- **Ryzyko:** każdy może ładować; publiczna stacja z free vend narusza założenia płatności ad hoc (AFIR art. 5 ust. 1,
  `dom-ev-payments`) — dozwolone tylko tam, gdzie punkt nie jest ogólnodostępny lub nie pobiera opłaty [do weryfikacji prawnie].

## 2. Konfiguracja po stronie stacji
Żadna wersja OCPP nie ma jednego przełącznika „free vend”; zestawia się go z ustawień autoryzacji albo ustawieniem producenta.
| Wersja | Gdzie | Co (nazwy) | Status |
|---|---|---|---|
| 1.6 | `ChangeConfiguration(key, value)` / `GetConfiguration` (schemat: `key` do 50, `value` do 500 znaków, oba stringi) | klucze autoryzacji z profilu Core: `AuthorizeRemoteTxRequests`, `LocalPreAuthorize`, `LocalAuthorizeOffline`, `AllowOfflineTxForUnknownId`, `AuthorizationCacheEnabled` | nazwy kluczy [do weryfikacji] w specyfikacji 1.6; sam free vend zwykle klucz producenta |
| 2.0.1 | `SetVariables` / `GetVariables` (Device Model) | komponent `AuthCtrlr` (np. `AuthorizeRemoteStart`, `LocalAuthorizeOffline`, `LocalPreAuthorize`, `OfflineTxForUnknownIdEnabled`) i `TxCtrlr.TxStartPoint` (kiedy powstaje transakcja) | nazwy zmiennych [do weryfikacji] w Part 2 |
| obie | konfiguracja lokalna stacji, tryb pracy, dip-switch | tryb „bez autoryzacji / swobodny” | zależy od modelu — karta producenta (`dom-ev-charger-onboarding`) |
Zasada: free vend ustawiasz **na poziomie stacji i dokumentujesz w rejestrze** (kto, kiedy, po co), a nie przez
zostawienie pustej autoryzacji w CSMS. Po zmianie sprawdź ramki: czy stacja nadal wysyła `Authorize`, jaki `idTag` w
`StartTransaction`, czy `MeterValues` płyną (`dom-ev-diagnostics`, `ocpp_log_analyze.py`).
Uwaga: `AuthorizeRemoteTxRequests` dotyczy startu **zdalnego** (czy stacja ma autoryzować token z komendy), nie free vend.

## 3. Kiosk (terminal lub ekran jako punkt startu)
Kiosk: kierowca zaczyna sesję na terminalu płatniczym albo ekranie stacji zamiast w aplikacji lub kartą RFID.
| Wariant | Start | Autoryzacja w CSMS |
|---|---|---|
| Terminal płatniczy | wybór EVSE → preautoryzacja karty → komenda startu | token ad hoc powiązany z `authorization_reference` (`dom-ev-payments`) |
| Ekran stacji (QR / kod) | wybór opcji → przekierowanie do płatności | start po potwierdzeniu płatności przez system płatniczy |
| Ekran bez płatności (np. gość hotelu, kod z recepcji) | kod jednorazowy lub wybór opcji | token techniczny jak w free vend |
- Start z kiosku zwykle idzie jako zdalny (`RemoteStartTransaction` / `RequestStartTransaction`) albo lokalny po stronie stacji
  — w obu przypadkach ważne jest, żeby **sesja miała powiązanie z płatnością lub tokenem technicznym**, inaczej nie
  zamkniesz rozliczenia. Pomyłka EVSE na terminalu to osobna pułapka (`dom-ev-payments`).
- Zatrzymanie z kiosku (przycisk Stop na ekranie) to zdarzenie lokalne: `reason = Local` (1.6) / `stoppedReason = Local` (2.0.1).

## 4. STOP_FAILED
**`STOP_FAILED` nie jest statusem ani wartością OCPP** — to stan operatorski w CSMS/CPMS (ta sama konwencja co w
`dom-ev-kpi-analytics`). Oznacza: CPO chciał zakończyć sesję, a stacja **nie potwierdziła zakończenia**, czyli brak
`StopTransaction` (1.6) / `TransactionEvent Ended` (2.0.1) mimo komendy lub mimo oczekiwania.
| Przyczyna | Objaw w ramkach | Uwagi |
|---|---|---|
| Stacja offline | brak Heartbeatów, ostatnia ramka dawno temu | komenda nie dotarła; po powrocie mogą przyjść zbuforowane `Stop` |
| Stop zdalny odrzucony | `RemoteStopTransaction` / `RequestStopTransaction` → `Rejected` (statusy odpowiedzi: `Accepted` albo `Rejected` — schematy RemoteStopTransactionResponse 1.6 i RequestStopTransactionResponse 2.0.1) | zły `transactionId`, sesja już zakończona, stacja nie zna transakcji |
| Błąd firmware | komenda `Accepted`, ale transakcja trwa, `MeterValues` płyną | znana wada modelu — odchylenia: `dom-ev-ocpp-16`, `dom-ev-charger-onboarding` |
| Pojazd nie wypuszcza | prąd spada, ale wtyczka zablokowana lub stan `SuspendedEV` | `reason` może być `EVDisconnected` lub `Other`; pojazd odpina się dopiero po komunikacie z auta |
| Stop wykonany, ramki nie ma | licznik stoi, status `Available`/`Finishing`, brak `StopTransaction` | zgubiona lub niewysłana ramka (restart, brak pamięci) |
| Uszkodzenie sprzętu | `Faulted` na złączu | `dom-ev-diagnostics` |
Różnica od sesji osieroconej (SKILL.md): osierocona = CSMS nie dostał Stop z powodu utraty zasilania lub łączności po stronie
stacji; `STOP_FAILED` = CPO **aktywnie próbował** zakończyć i nie dostał potwierdzenia. W praktyce to ta sama sesja domenowa
w stanie „aktywna, zakończenie niepotwierdzone”; różnią się obsługą i alarmem.

## 5. Obsługa STOP_FAILED
1. **Ustal stan stacji** (nie zakładaj): `TriggerMessage` z `requestedMessage = StatusNotification` (z `connectorId`) i
   `MeterValues` dla złącza. W 1.6 `TriggerMessage` **nie obejmuje** `StopTransaction` ani `StartTransaction` (schemat: BootNotification,
   DiagnosticsStatusNotification, FirmwareStatusNotification, Heartbeat, MeterValues, StatusNotification); w 2.0.1 lista zawiera
   `TransactionEvent`, więc możesz wymusić aktualne zdarzenie. Odpowiedź: `Accepted` / `Rejected` / `NotImplemented`.
2. **Ponów stop z limitem prób** (np. 3 próby w rosnących odstępach): ten sam `transactionId`, rejestruj każdą próbę
   i odpowiedź. Nie ponawiaj w pętli — kolejka stacji może się zapchać.
3. **Jeśli licznik nadal rośnie, a stop nie działa:** ogranicz moc profilem (`SetChargingProfile` z limitem 0 lub minimalnym,
   `dom-ev-smart-charging`), jeśli stacja go obsługuje; ostatecznie `Reset` (soft, potem hard) — **po zapisaniu odczytu licznika**
   i z ostrzeżeniem, że reset przerywa też inne sesje stacji.
4. **Jeśli stacja offline:** poczekaj na powrót (okno ustalone jawnie); po nim przyjdą zbuforowane `Stop`/`Ended`
   i sesja zamknie się sama — nie zamykaj wcześniej administracyjnie.
5. **Zamknięcie administracyjne** (ostatnia deska, po upływie limitu): operator zamyka sesję w CSMS z **wpisem**:
   kto, kiedy, powód, dowód (ostatni `MeterValues`, status złącza, próby stopu), przyjęty `meterStop` i flaga
   `energia_szacowana`. Czas końca = czas ostatniej ramki z licznikiem lub czas zamknięcia — decyzja zapisana w regule.
6. **Późny `Stop` po zamknięciu administracyjnym:** jak w SKILL.md (osierocone): jeśli CDR niewysłany — zastąp szacunek odczytem;
   jeśli wysłany — korekta, nie zmiana CDR.
7. **Alarm i serwis:** powtarzalny `STOP_FAILED` na jednym modelu/firmware to wada (zgłoszenie do producenta,
   `dom-ev-certification-testing`, `dom-ev-asset-operations`); na jednym złączu — sprzęt lub pojazd.

## 6. Wpływ na CDR i raporty
- **CDR** (dom-ev-cdr-settlement): nie wystawiaj CDR dla sesji w `STOP_FAILED`. Po zamknięciu CDR niesie energię z ostatniego odczytu i
  flagę szacunku; przy roamingu poinformuj eMSP, że odczyt końcowy nie pochodzi ze `Stop` (zasada: nie udawaj odczytu).
- **Czas trwania i utilization:** sesja wisząca zawyża czas zajęcia; liczysz do czasu ostatniego `MeterValues`, nie do zamknięcia.
- **KPI:** `STOP_FAILED` osobno, nie do sukcesu ani porażki bez reguły (`dom-ev-kpi-analytics`).
- **Koszt dla kierowcy (ad hoc):** capture wyłącznie za zmierzoną energię; blokada karty wraca po zamknięciu (`dom-ev-payments`).

## 7. Pułapki
- Traktowanie `STOP_FAILED` jako statusu z protokołu i szukanie go w ramkach.
- Zamknięcie administracyjne bez odczytu licznika i wpisu — później nie da się obronić kwoty.
- Zamknięcie, zanim stacja offline wróciła — tracisz prawdziwy `Stop`.
- Resetowanie stacji bez zapisania odczytów; reset przerywa inne sesje.
- Free vend ustawiony „tymczasowo” i zapomniany na publicznej stacji.
- Odrzucanie nieznanego `idTag` z free vend → stacja nie startuje albo pętla ponowień.
- Brak tokenu technicznego: sesje bez właściciela w raportach.

## 8. Źródła
- Schematy JSON OCPP 1.6 i 2.0.1 (`mobilityhouse/ocpp`, baza `ocpp-json-schemas`, pobrane 2026-10-20): `ChangeConfiguration`,
  `TriggerMessage` (1.6 i 2.0.1), `TriggerMessageResponse` (1.6), `StopTransaction` (1.6: `reason`, wymagane pola),
  `TransactionEvent` (2.0.1: `idToken` opcjonalny, `triggerReason`, `stoppedReason`/`ReasonEnumType`), `IdTokenEnumType` (`NoAuthorization`).
- Nazwy kluczy 1.6 i zmiennych `AuthCtrlr`/`TxCtrlr`, statusy `RemoteStop`/`RequestStop`, wymagalność `idTag` w `StartTransaction`: wiedza
  o specyfikacji OCA, [do weryfikacji]. Procesy zamknięcia administracyjnego i kiosku: praktyka branży [założenie].
