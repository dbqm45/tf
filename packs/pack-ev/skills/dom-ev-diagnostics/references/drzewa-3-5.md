# Drzewa 3–5: sesja bez końca, energia, statusy usterek

> **Spis treści:** Drzewo 3 — brak CDR albo sesja wisi · Drzewo 4 — rozjazd energii: licznik vs CSMS vs CDR · Drzewo 5 — Faulted i Unavailable

Poprawny przebieg sesji i moment CDR: `dom-ev-session-lifecycle` oraz `dom-ev-charging/references/cykl-sesji-ladowania.md`
(CDR powstaje po zakończeniu transakcji i jest niezmienny; korekta = CDR kredytowy). Reszta — wiedza ogólna,
**[do weryfikacji]** u producenta.

## Drzewo 3 — brak CDR albo sesja wisi

### Pytania
1. Sesja ma status „aktywna” w CSMS, a kierowca jest już poza pojazdem? Od kiedy?
2. Co jest **ostatnią ramką** transakcji: `MeterValues`, `StatusNotification`, nic?
3. Czy stacja była w tym czasie offline, restartowana, bez zasilania (`reboot`)?
4. Czy CSMS dostał `StopTransaction` / `TransactionEvent Ended`, ale **nie utworzył CDR**?

### Co sprawdzić w logu
| Pytanie | Dowód | Ustalenie skryptu |
|---|---|---|
| jest koniec transakcji? | `StopTransaction` (1.6) lub `TransactionEvent` z `eventType: Ended` (2.x) | `open-transaction` — brak |
| koniec dla nieznanej transakcji? | `transactionId` w `StopTransaction`/`TransactionEvent` bez wcześniejszego startu | `unknown-transaction` |
| były zerwania i restart? | BootNotification w środku sesji, luka w czasie | `reboot`, `clock-skew` |
| 2.x: czy brakuje zdarzeń? | ciąg `seqNo` w jednej transakcji | `seqno-gap`, `seqno-duplicate` |
| ramka odrzucona? | odpowiedź CSMS na zbuforowany Stop/Ended | `callerror`, `call-no-response` |

### Typowe przyczyny
- **Utrata zasilania lub restart** bez wysłania końca transakcji — sesja „wisi” (`.claude/skills/dom-ev-ocpp-16/references/odchylenia-i-offline.md`). Dowód: `reboot` po ostatnim `MeterValues`, status `Available` na złączu bez `Stop`.
- **Offline z kolejką:** ramki końcowe czekają w buforze ładowarki; po reconnect przychodzą ze starymi znacznikami.
  Sprawdź, czy po powrocie połączenia **są** i jak CSMS na nie odpowiedział.
- **CSMS odrzucił lub zgubił zbuforowaną ramkę końcową** (zły schemat, nieznana transakcja, błąd wewnętrzny) —
  stacja ponawia w kółko lub porzuca. Dowód: `callerror` na `StopTransaction`.
- **Osierocona transakcja** blokuje token (`ConcurrentTx` w drzewie 2) i kolejną sesję na złączu.
- **Koniec dotarł, CDR nie powstał:** problem w przetwarzaniu po stronie CSMS (kolejka, outbox, taryfa, błąd
  walidacji) — to nie jest problem ładowarki; dowód to ramka końcowa w logu i brak CDR w bazie.
- 2.x: moment końca transakcji zależy od konfiguracji (`TxStopPoint`); sesja może kończyć się później niż kierowca
  oczekuje (`cykl-sesji-ladowania.md`).

### Działanie
- Zamknięcie osieroconej sesji: heurystyka (nowy Boot, `Available` na złączu), energia **oznaczona jako szacowana**,
  nigdy ciche zgadywanie. Decyzję o rozliczeniu szacowanej energii podejmuje człowiek (odpowiedzialność wobec eMSP).
- Zapisz, jaką regułą zamknięto sesję i które dane są niepełne; CDR kredytowy zamiast edycji istniejącego.
- Przyczynę systemową (brak obsługi zbuforowanej ramki) zgłoś jako defekt CSMS z ramką jako testem regresji.

## Drzewo 4 — rozjazd energii: licznik vs CSMS vs CDR

### Pytania
1. Jaka jest **różnica** (bezwzględna i procentowa) i w którą stronę? Dokładnie ×1000, ×0,001, kilka procent, losowa?
2. Które trzy wartości porównujesz: odczyt licznika, `meterStop − meterStart` w CSMS, `total_energy` w CDR
   (nazwa pola OCPI — **[do weryfikacji]** w wersji używanej)?
3. Ta sama jednostka we wszystkich trzech? Ten sam przedział czasu (start/stop)?
4. Dotyczy jednego modelu ładowarki, jednej stacji czy wszystkich?

### Co sprawdzić w logu
| Krok | Dowód |
|---|---|
| wartości źródłowe | `meterStart`, `meterStop` (1.6: w **Wh**), `MeterValues` z `measurand`, `unit` i wartością |
| jednostka | pole jednostki w `sampledValue` (`unit`); brak lub nieoczekiwana (kWh zamiast Wh) |
| ciągłość | `meter-decrease` — licznik malejący; wymiana lub reset licznika w trakcie sesji |
| czas | `clock-skew`; granice sesji wg zegara stacji vs CSMS |
| przeliczenie | kod/konfiguracja CSMS: dzielenie przez 1000, zaokrąglanie, jednostka w CDR |

### Typowe przyczyny
- **Wh vs kWh:** `meterStart`/`meterStop` są w Wh; 12 kWh = 12000 Wh. Wartość 12000 w polu, które eMSP czyta jako
  kWh, daje „×1000”. Zlokalizuj etap, na którym brakuje (lub jest nadmiarowe) przeliczenie: ładowarka (`unit`),
  parser CSMS, generator CDR, eksport do eMSP. Różnica dokładnie ×1000 to prawie zawsze jednostka.
- **Zły `measurand` lub kontekst:** moc zamiast energii, energia „import” vs „export”, wartość chwilowa zamiast
  skumulowanej. Nazwy measurandów — **[do weryfikacji]** w specyfikacji.
- **Licznik malejący:** wymiana licznika, reset firmware, przepełnienie rejestru, błąd odczytu. Energii nie liczysz
  wtedy prostą różnicą — oznacz sesję do ręcznej weryfikacji.
- **Zegar:** zła granica sesji powoduje, że `MeterValues` spoza okna są wliczone lub pominięte.
- **Zaokrąglenia:** różnica rzędu ułamka kWh; sprawdź, na którym etapie obcinasz (Wh→kWh, kWh→wartość w CDR).
- **Licznik rozliczeniowy vs telemetria:** `MeterValues` służą kontroli; do rozliczeń zwykle obowiązują wymogi prawne
  dla licznika (`.claude/skills/dom-ev-ocpp-16/references/status-i-transakcje.md`) — porównuj z właściwym źródłem.

### Działanie
- Naprawa błędu jednostki w kodzie CSMS zaczyna się od testu, który nie przechodzi (12000 Wh → 12 kWh), potem poprawka.
- Skutek dla rozliczeń: CDR jest niezmienny — poprawka to CDR kredytowy i nowy CDR (`dom-ev-charging`), uzgodniony
  z eMSP; skalę (ile sesji, od kiedy) ustal zapytaniem po modelu ładowarki i wersji CSMS.

## Drzewo 5 — Faulted i Unavailable

### Pytania
1. `Faulted` czy `Unavailable`? Dla złącza czy całej stacji (`connectorId` 0)?
2. Jaki `errorCode` i `vendorErrorCode` niesie `StatusNotification`? Jaki tekst `info`?
3. Czy ktoś **wysłał** `ChangeAvailability` (stan celowy), czy stacja zgłosiła sama?
4. Czy stan trwa, czy flapuje (częste zmiany)? Co było tuż **przed** zmianą statusu?

### Co sprawdzić w logu
| Pytanie | Dowód |
|---|---|
| kto wprowadził stan? | CALL `ChangeAvailability` w `csms>cp` w oknie przed `Unavailable`; jego odpowiedź (`Accepted`/`Scheduled`/`Rejected` — **[do weryfikacji]**) |
| co zgłosiła stacja? | `StatusNotification`: `status`, `errorCode`, `vendorErrorCode`, `info`, `timestamp` |
| flapowanie | liczba zmian statusu w jednostce czasu; powiązanie z temperaturą, prądem, firmware |
| przyczyna sprzętowa | log producenta po stronie ładowarki; `DiagnosticsStatusNotification` po `GetDiagnostics` |

### Typowe przyczyny
- **`Unavailable` celowe** (zdalne `ChangeAvailability`, tryb serwisowy) zostawione po pracach — wniosek z logu
  `csms>cp`, nie z domysłu.
- **`Faulted` z `errorCode`:** nazwy `errorCode` ze specyfikacji (lista **[do weryfikacji]** — nie zgaduj) wskazują
  klasę usterki; `vendorErrorCode` jest specyficzny dla producenta i **wymaga jego dokumentacji**. Bez niej nie
  twierdź, co oznacza.
- **Zabezpieczenia:** temperatura, przetężenie, zwarcie doziemne, blokada złącza — sprawdź, czy kod pasuje do
  warunków (upał, mocne obciążenie lokalizacji).
- **Aktualizacja firmware / reset** — przejściowy `Unavailable` po restarcie; porównaj z `reboot`.
- **Odchylenie producenta:** `Faulted` bez `errorCode` (`NoError`), `errorCode` bez sensu dla stanu, brak powrotu do
  `Available` po usunięciu usterki → zapisz jako odchylenie (`raport-diagnozy.md`).

### Działanie — komendy zdalne (safety-critical)
- Najpierw odczyt: `TriggerMessage` (`StatusNotification`), `GetConfiguration`/`GetVariables`, `GetDiagnostics`.
- `Reset`, `UnlockConnector`, `ChangeAvailability` (z `Operative`) i `UpdateFirmware` **tylko z planem i akceptacją
  człowieka**: cel (stacja/złącze), powód z dowodem, ryzyko (aktywna sesja, pojazd podłączony, napięcie), sposób
  cofnięcia, kto potwierdza skutek. Brak planu = brak komendy.
- Usterka fizyczna (`Faulted` powtarzalny, zabezpieczenia) trafia do serwisu — nie próbuj jej „przeklikać” resetami.
- Po akcji: nowy `StatusNotification`, zapis w raporcie; powtórka komendy dopiero po analizie, dlaczego pierwsza nie zadziałała.
