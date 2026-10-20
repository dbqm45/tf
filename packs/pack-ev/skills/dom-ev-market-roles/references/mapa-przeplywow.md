# Mapa przepływów: kto z kim i czym

| Od | Do | Co | Kanał |
|---|---|---|---|
| Ładowarka | CSMS (CPO) | statusy, transakcje, liczniki | OCPP (`dom-ev-ocpp-16`, `dom-ev-ocpp-2x`) |
| CPO | eMSP / hub | Locations, Tariffs, Sessions, CDR | OCPI, CPO jako Sender |
| eMSP | CPO / hub | Tokens, komendy start/stop | OCPI, eMSP jako Sender (Tokens, Commands) |
| eMSP | kierowca / flota | faktura, powiadomienia | poza OCPI |
| eMSP | CPO | płatność hurtowa wg CDR | poza OCPI (umowa, przelew) |
| CPO | host | udział w przychodach, raport | poza OCPI |
| CPO | sprzedawca energii | zużycie, rozliczenie energii | umowa sprzedaży, liczniki |
| CPO | OSD | wniosek o przyłączenie, limity mocy | umowa przyłączeniowa |
| CPO | NAP | dane statyczne i dynamiczne | wg wymogów NAP [do weryfikacji] |
| Producent | CPO | firmware, serwis | umowa serwisowa |

Kierunek zawsze nazwij przez rolę Sender/Receiver w danym module (`dom-ev-charging/references/ocpi.md` §6a).

## Przykład
Pytanie „kto dostaje CDR?” → CPO jest Senderem CDR; Receiver to eMSP (albo hub). Host go nie dostaje przez OCPI,
raport dla hosta CPO przygotowuje z własnych sesji.
