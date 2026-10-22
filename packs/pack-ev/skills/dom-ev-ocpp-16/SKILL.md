---
name: dom-ev-ocpp-16
description: Użyj przy OCPP 1.6J między ładowarką a CSMS — ramki CALL, BootNotification, StatusNotification, transakcje, MeterValues, offline, odchylenia producentów.
metadata:
  przeglad: 2027-04-20
  katalog: "Użyj przy implementacji, diagnozie i obsłudze logów OCPP 1.6 JSON/WebSocket (1.6J) po stronie CSMS (Central System) i ładowarki — ramki RPC i kody błędów, cykl połączenia i BootNotification, katalog komunikatów wg profili, statusy złącza, StartTransaction/StopTransaction i MeterValues, autoryzacja, konfiguracja, Security Whitepaper, offline, odchylenia producentów oraz procedura obsługi nowego komunikatu. Nie do OCPP 2.0.1/2.1 i migracji (dom-ev-ocpp-2x), słownika pojęć (dom-ev-glossary) ani roamingu OCPI (dom-ev-charging)."
  slowa: "OCPP 1.6, 1.6J, ocpp1.6, Central System, CSMS, CALL, CALLRESULT, CALLERROR, BootNotification, Heartbeat, StatusNotification, Preparing, SuspendedEV, StartTransaction, StopTransaction, transactionId, MeterValues, idTag, Authorize, SendLocalList, GetConfiguration, ChangeConfiguration, Security Whitepaper, ładowarka nie łączy się, ładowarka offline, charge point, wallbox, messageId"
---

# OCPP 1.6J — ładowarka ↔ CSMS

Skill dotyczy **OCPP 1.6 przez JSON/WebSocket** (1.6J). SOAP/XML istnieje w 1.6, ale nowe wdrożenia go nie używają —
tu tylko wzmianka. Ładowarka (*Charge Point*) jest klientem WebSocket, backend (*Central System*, w 2.x CSMS) serwerem.
Szczegóły i tabele: `references/`. Granice: 2.0.1/2.1 i migracja → `dom-ev-ocpp-2x`; pojęcia → `dom-ev-glossary`;
roaming i CDR → `dom-ev-charging`.

## Czytaj references, gdy…
| Plik | Kiedy |
|---|---|
| `references/komunikaty-i-profile.md` | potrzebujesz pełnej listy komunikatów wg profili z kierunkiem |
| `references/status-i-transakcje.md` | analizujesz przejścia statusów złącza, kolejność ramek transakcji, MeterValues |
| `references/odchylenia-i-offline.md` | ładowarka gubi ramki, ma zły zegar, wysyła `connectorId` 0, działa offline |

## Ramki RPC
| Typ | Ramka | Uwaga |
|---|---|---|
| CALL | `[2, "<messageId>", "<Action>", {payload}]` | żądanie; id unikalne w obrębie nadawcy |
| CALLRESULT | `[3, "<messageId>", {payload}]` | to samo id co CALL; bez nazwy akcji |
| CALLERROR | `[4, "<messageId>", "<errorCode>", "<opis>", {szczegóły}]` | błąd na poziomie protokołu, nie „Rejected” |

- Każda strona ma najwyżej **jedno niezakończone CALL naraz**; typowy timeout ~30 s. Obie strony wysyłają CALL niezależnie.
- Kody błędów 1.6J (z `ocpp.md`): `NotImplemented`, `NotSupported`, `InternalError`, `ProtocolError`, `SecurityError`,
  `FormationViolation`, `PropertyConstraintViolation`, `OccurenceConstraintViolation` (literówka w specyfikacji —
  piszesz tak, nie „Occurrence”), `TypeConstraintViolation`, `GenericError`. W 2.0.1 nazwy są inne (`FormatViolation`).
- Odmowa biznesowa to **CALLRESULT** ze `status: Rejected`, nie CALLERROR. CALLERROR dla ramki, której nie da się
  przetworzyć (zły schemat, nieznana akcja).

## Cykl połączenia
1. Ładowarka otwiera WebSocket (zwykle `wss://host/<chargePointId>` — układ ścieżki **[do weryfikacji]**) z
   nagłówkiem `Sec-WebSocket-Protocol: ocpp1.6`. CSMS, który nie obsługuje podprotokołu, nie powinien go potwierdzać
   w odpowiedzi upgrade **[do weryfikacji]**.
2. Natychmiast **BootNotification** (vendor, model, numer seryjny, firmware). Odpowiedź: `status`
   `Accepted` / `Pending` / `Rejected`, `currentTime`, `interval`.
3. `Accepted` — normalna praca; `interval` to odstęp Heartbeatów w sekundach. `Pending` — CSMS jeszcze nie przyjął
   ładowarki (np. konfiguruje ją); `Rejected` — ładowarka nieznana, ponawia Boot po `interval`. Co wolno w `Pending`
   i `Rejected` — **[do weryfikacji]** w specyfikacji; w praktyce ładowarka nie startuje transakcji.
4. **Heartbeat** co `interval`; odpowiedź niesie `currentTime` (UTC) — zegar ładowarki synchronizuj z niej.
5. Zerwanie → reconnect z exponential backoff, potem znów BootNotification.

## Profile i kierunek komunikatów
Profile 1.6: **Core**, **Firmware Management**, **Local Auth List Management**, **Reservation**, **Smart Charging**,
**Remote Trigger**. Pełny wykaz z kierunkiem: `references/komunikaty-i-profile.md`. Skrót:
- ładowarka → CSMS: `BootNotification`, `Heartbeat`, `StatusNotification`, `Authorize`, `StartTransaction`,
  `StopTransaction`, `MeterValues`, `FirmwareStatusNotification`, `DiagnosticsStatusNotification`;
- CSMS → ładowarka: `RemoteStartTransaction`, `RemoteStopTransaction`, `ChangeConfiguration`, `GetConfiguration`,
  `ChangeAvailability`, `Reset`, `UnlockConnector`, `ClearCache`, `SetChargingProfile`, `TriggerMessage` itd.;
- `DataTransfer` — w obu kierunkach, dane producenta.

## Statusy złącza (StatusNotification)
`Available`, `Preparing`, `Charging`, `SuspendedEV`, `SuspendedEVSE`, `Finishing`, `Reserved`, `Unavailable`, `Faulted`.
Typowa ścieżka sesji: `Available` → `Preparing` (kabel wpięty, brak autoryzacji **albo** autoryzacja bez kabla) →
`Charging` → `Finishing` (transakcja zakończona, kabel jeszcze w gnieździe) → `Available`. `SuspendedEV` — pojazd
wstrzymał pobór; `SuspendedEVSE` — wstrzymuje ładowarka (np. limit mocy z profilu). Tabela przejść:
`references/status-i-transakcje.md`. W 2.0.1 słownik jest inny (`Occupied`) — nie mieszaj wersji.

## Transakcje
- **Start:** `StartTransaction` niesie `connectorId`, `idTag`, `meterStart` (**Wh**), `timestamp`. **`transactionId`
  nadaje CSMS** w odpowiedzi (CALLRESULT razem z `idTagInfo`). Ładowarka nie wymyśla go sama.
- **Stop:** `StopTransaction` niesie `transactionId`, `meterStop` (Wh), `timestamp`, opcjonalnie `reason` i
  `transactionData`. Energia sesji = `meterStop − meterStart` (w Wh; podziel przez 1000 na kWh).
- **MeterValues** w trakcie sesji: wartości z `measurand` (np. energia czynna, moc, prąd, napięcie, SoC) i jednostką;
  dokładne nazwy measurandów i domyślne wartości **[do weryfikacji]** w specyfikacji.
- Krytyczne `StartTransaction`/`StopTransaction` ładowarka buforuje offline i wysyła po reconnect (`ocpp.md`).

## Autoryzacja
`Authorize` z `idTag` → odpowiedź `idTagInfo.status` (m.in. `Accepted`, `Blocked`, `Expired`, `Invalid`,
`ConcurrentTx` — pełny zestaw **[do weryfikacji]**). Offline ładowarka sięga do **lokalnej listy** (`SendLocalList`,
`GetLocalListVersion`) i cache (`ClearCache`). Autoryzację z aplikacji robi `RemoteStartTransaction`.

## Konfiguracja
`GetConfiguration` odczytuje klucze, `ChangeConfiguration` zapisuje jeden. **Nazw kluczy nie zgaduj** — repozytorium
ich nie wylicza **[do weryfikacji]** w specyfikacji OCPP 1.6 i dokumentacji producenta. Praktyka: wyślij
`GetConfiguration` bez listy kluczy, zapisz odpowiedź (klucze, `readonly`, `unknownKey`) i na niej oprzyj logikę.
Odpowiedź na zapis: `Accepted`, `Rejected`, `RebootRequired`, `NotSupported` **[do weryfikacji]**.

## Security Whitepaper (dodatek do 1.6)
Core 1.6 ma bezpieczeństwo minimalne (TLS opcjonalny). Dodatek *Security Whitepaper* (edycja 2) daje profile:
1 — Basic Auth przez `ws://` (tylko testy/sieci izolowane); 2 — TLS + Basic Auth (minimum do produkcji);
3 — TLS + certyfikaty klienta (mTLS, wymaga PKI). Dodaje też komunikaty bezpieczeństwa (11 według `ocpp.md`;
lista **[do weryfikacji]**). To opt-in, nie obowiązek jak w 2.0.1.

## Procedura: obsługa nowego komunikatu po stronie CSMS
1. **Zapisz surową ramkę** (id, akcja, payload, czas, `chargePointId`) zanim cokolwiek zinterpretujesz.
2. **Waliduj schemat** akcji z wersji 1.6 (JSON Schema OCA — pobierz ze specyfikacji, **[do weryfikacji]** wersję).
   Zły schemat → CALLERROR (`FormationViolation` / `TypeConstraintViolation` / `PropertyConstraintViolation`);
   nieznana akcja → `NotImplemented`.
3. **Idempotencja po `messageId`** (w parze z `chargePointId`): ten sam CALL przyszedł drugi raz (retry po
   zerwaniu) → zwróć **tę samą** odpowiedź, bez ponownego skutku ubocznego. Dla `StartTransaction` nie twórz drugiej
   transakcji; klucz zapasowy to (`connectorId`, `idTag`, `timestamp`, `meterStart`) **[założenie]**.
4. **Odpowiedz w czasie** (< ~30 s). Ciężką pracę (rozliczenie, wywołania zewnętrzne) wykonaj po odpowiedzi,
   z kolejki; nie blokuj pętli odbioru tej ładowarki.
5. **Skutki uboczne po zapisie** (outbox), nie przed odpowiedzią i nie w pamięci procesu.
6. **Test na nagranej ramce:** z logu wytnij prawdziwy CALL, odtwórz go (też dwa razy) i sprawdź: schemat, odpowiedź
   (CALLRESULT z tym samym id), brak duplikatu skutku, stan w bazie. Dodaj ramkę do zestawu regresji.

## Przykład
Wejście: ładowarka po restarcie wysyła `[2,"a7","StopTransaction",{"transactionId":4521,"meterStop":18340,
"timestamp":"2026-10-20T08:15:00Z"}]`, a CSMS nie ma transakcji 4521.
Wynik: ramka jest poprawna składniowo, więc odpowiedz **CALLRESULT** `[3,"a7",{}]` (pole `idTagInfo` jest opcjonalne
**[do weryfikacji]**) — CALLERROR lub ciągłe odrzucanie sprawi, że ładowarka będzie ponawiać komunikat bez końca i
zablokuje kolejkę. Zapisz ramkę w kwarantannie „nieznana transakcja” do ręcznego wyjaśnienia (może przepadł
`StartTransaction`; liczniki `meterStop` mogą być jedynym dowodem energii), zgłoś alert.

## Pułapki
- **Odrzucanie w pętli:** CALLERROR/Rejected na zbuforowane `StopTransaction` → ładowarka ponawia w nieskończoność.
- **`transactionId` po stronie ładowarki:** nadaje go CSMS; ładowarka offline używa własnego tymczasowego identyfikatora
  tylko lokalnie **[do weryfikacji]** — nie zakładaj, że jest unikalny globalnie.
- **Energia w kWh:** `meterStart`/`meterStop` są w Wh; mnożenie/dzielenie przez 1000 przy rozliczeniu.
- **`OccurenceConstraintViolation`:** nazwa z literówką jest poprawna w 1.6; „Occurrence” to 2.x.
- **Zegar ładowarki:** znaczniki czasu offline bywają błędne — porównuj z czasem odbioru, koryguj Heartbeatem.
- **`connectorId` 0:** oznacza całą ładowarkę (`StatusNotification`, `ChangeAvailability`); nie traktuj jak złącza.
- **Brak `StopTransaction` po utracie zasilania:** sesje „wiszą”; zamykaj po `StatusNotification`/BootNotification
  z `Available` na tym złączu i oznacz jako szacowane.
- **Mieszanie wersji:** ładowarka na 1.6 nie zna `TransactionEvent`; ten komunikat to `dom-ev-ocpp-2x`.

## Checklista
- [ ] Podprotokół `ocpp1.6` negocjowany; BootNotification zwraca `Accepted` i `interval`.
- [ ] Surowa ramka zapisana przed przetwarzaniem; schemat walidowany wg 1.6.
- [ ] Idempotencja po `messageId` + `chargePointId`; retry nie duplikuje transakcji.
- [ ] Odpowiedź w < 30 s; ciężka praca poza ścieżką odpowiedzi.
- [ ] `transactionId` nadaje CSMS; energia liczona z Wh.
- [ ] Nazwy kluczy konfiguracji z `GetConfiguration`, nie z pamięci.
- [ ] Test na nagranej ramce (też zduplikowanej) w regresji.
- [ ] Oznaczone wszystkie fakty spoza `ocpp.md` (w dom-ev-charging) jako [do weryfikacji].

## Źródła
- plik `ocpp.md` skilla dom-ev-charging (import 2024–2025, włączony 2026-09-27): ramki, kody błędów,
  cykl połączenia, katalog komunikatów, statusy 1.6, Security Whitepaper, offline.
- Wiedza ogólna autora skilla o specyfikacji OCPP 1.6 (OCA) — oznaczona **[do weryfikacji]** tam, gdzie nie ma jej w
  `ocpp.md`; sprawdź w specyfikacji OCA przed użyciem w umowie lub certyfikacji (stan: 2026-10-20).
