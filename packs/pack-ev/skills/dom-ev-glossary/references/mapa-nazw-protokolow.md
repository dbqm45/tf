# Mapa nazw — ta sama rzecz w różnych słownikach

Źródła: `dom-ev-charging/references/ocpp.md`, `ocpi.md` (import 2024–2025) i wiedza ogólna. Pozycje oznaczone
**[do weryfikacji]** sprawdź w specyfikacji przed użyciem w kodzie.

## Urządzenia i hierarchia
| Poziom | Kanoniczna (domena) | OCPP 1.6 | OCPP 2.0.1 | OCPI 2.2.1 | Slang |
|---|---|---|---|---|---|
| Adres / parking | Location | — | — | `Location` | „lokalizacja”, „stacja” |
| Urządzenie | ChargingStation | Charge Point | Charging Station | brak obiektu (pole lub grupa EVSE) | „słupek”, „ładowarka”, „wallbox” |
| Miejsce na jedno auto | Evse | w praktyce `connector` **[do weryfikacji]** | EVSE | `EVSE` | „punkt ładowania” |
| Wtyczka | Connector | connector (`connectorId`) | Connector | `Connector` | „gniazdo”, „port”, „plug” |
| Backend operatora | CSMS | Central System | CSMS | (strona: CPO) | CPMS |

## Procesy
| Pojęcie | Domena | OCPP | OCPI |
|---|---|---|---|
| Ładowanie widziane przez urządzenie | Transaction | 1.6 `transactionId`; 2.0.1 `TransactionEvent` | — |
| Ładowanie widziane przez eMSP | Session | — | `Session` |
| Zapis do rozliczenia | Cdr | — | `CDR` (niezmienny) |
| Nośnik uprawnienia | Token | 1.6 `idTag`; 2.0.1 `idToken` **[do weryfikacji]** | `Token` |
| Telemetria | MeterValue | `MeterValues` | pola `Session`/`CDR` |

## Jak używać przy migracji
1. Zrób listę nazw z kodu (`grep -rniE "chargepoint|cpms|central.?system|station"`).
2. Przypisz każdą do wiersza tabeli i oceń: domena (nazwa kanoniczna) czy adapter (nazwa protokołu).
3. Zmień nazwy w domenie jednym commitem, adaptery zostaw — mapowanie w jednym module.
4. Dodaj test, że DTO protokołu nie wycieka poza adapter.
