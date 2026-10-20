# Offline i odchylenia producentów (1.6J)

Podstawa z `ocpp.md`: lokalna lista autoryzacji (`SendLocalList`) pozwala autoryzować po utracie WebSocket;
transakcje buforowane lokalnie i wysyłane po powrocie; krytyczne `StartTransaction`/`StopTransaction` są wysyłane
ponownie po reconnect. Reszta poniżej to wzorce z praktyki — **[do weryfikacji]** u konkretnego producenta.

## Kolejka offline
| Zjawisko | Skutek dla CSMS | Zachowanie |
|---|---|---|
| Po reconnect przychodzi seria zbuforowanych ramek | stare znaczniki czasu, kolejność może być inna niż rzeczywista | nie wyciągaj stanu „teraz” z ostatnio odebranej ramki; sortuj po `timestamp` z korektą zegara |
| `StopTransaction` bez znanego `StartTransaction` | nieznany `transactionId` | odpowiedz poprawnie, zapisz w kwarantannie |
| Ponowienie tej samej ramki | duplikat | idempotencja po `messageId` + `chargePointId` |
| Transakcja rozpoczęta offline | CSMS nie nadał `transactionId` | sposób identyfikacji offline — **[do weryfikacji]** |

## Typowe odchylenia (do sprawdzenia na sprzęcie)
- **Brak `StopTransaction` po utracie zasilania** — transakcja wisi „aktywna”. Zamknij ją heurystyką (nowy
  `BootNotification`, status `Available` na złączu), oznacz energię jako szacowaną.
- **Zegar** — ładowarka bez RTC startuje z datą 1970 lub starą; znaczniki w zbuforowanych ramkach są wtedy błędne.
  Synchronizuj z `currentTime` w BootNotification/Heartbeat; zapisuj czas odbioru obok czasu z ramki.
- **`connectorId` 0** — używany nie tylko w statusach całej ładowarki; niektóre urządzenia wysyłają go w miejscach,
  gdzie spec oczekuje numeru złącza. Waliduj i loguj, nie odrzucaj od razu.
- **Dodatkowe lub brakujące pola** — payload nieco poza schematem; ścisła walidacja daje CALLERROR i pętlę
  ponowień. Decyzja: tryb tolerancyjny z alertem per model ładowarki.
- **Nietypowe wartości `status`/`measurand`** — loguj nieznane, nie psuj sesji.
- **Heartbeat ignoruje `interval`** — monitoruj ciszę względem własnego progu, nie tylko względem `interval`.
- **Wielokrotny BootNotification** po krótkich zerwaniach — nie resetuj stanu sesji przy każdym.

## Ochrona przed pętlami
Odrzucanie komunikatu, który ładowarka musi dostarczyć (np. `StopTransaction`), kończy się ponawianiem. Dla
błędów po naszej stronie raczej CALLERROR `InternalError` z backoffem po stronie ładowarki niż ciche przyjęcie;
dla błędów danych (nieznane id) — przyjąć i odłożyć do analizy.
