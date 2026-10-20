# Adaptery OCPI i OICP nad jednym modelem

Spis: [Zasada](#zasada) · [Mapowanie](#mapowanie) · [Różnice semantyczne](#różnice-semantyczne) · [Szkic adaptera](#szkic-adaptera)

Źródło: OICP 2.3 (`.claude/knowledge/oicp/`), OCPI 2.2.1 d2 i 2.3.0 (`.claude/knowledge/ocpi-*`), pobrane 2026-10-20.
Mapowanie semantyczne to wniosek z dwóch specyfikacji, nie tabela z żadnej z nich: oznaczone [założenie] wymaga testu z partnerem.

## Zasada
- Model wewnętrzny (lokalizacja, EVSE, token/uprawnienie, sesja, CDR, taryfa, strona) nie zna nazw pól OCPI ani OICP.
- Adapter na wejściu tłumaczy wiadomość partnera na zdarzenie modelu; na wyjściu zdarzenie modelu na wiadomość.
  Jeden adapter na protokół i kierunek; logika biznesowa (autoryzacja, wycena, korekty) jest poza adapterem.
- Klucz zewnętrzny partnera (SessionID huba, `id` sesji OCPI, `uid` lokalizacji) zapisuj obok klucza wewnętrznego;
  nie zakładaj, że da się go wyprowadzić.
- Architektura bramy partnerów i rozdział kontekstów: `dom-ev-cpms-architecture`.

## Mapowanie
| Pojęcie modelu | OCPI | OICP | Uwaga |
|---|---|---|---|
| strona (kto) | `country_code` + `party_id` | `OperatorID` / `ProviderID` | tabela tłumaczeń jawna [założenie dla DIN] |
| lokalizacja, EVSE, złącze | Location, EVSE, Connector | `EvseDataRecord` (płaski rekord EVSE) | OICP nie ma obiektu Location; grupuje `ChargingStationID` |
| dostępność | `status` EVSE | `EvseStatusRecord`: `Available`, `Reserved`, `Occupied`, `OutOfService`, `Unknown` | zestawy statusów różne; mapuj w adapterze, nie w modelu |
| autoryzacja kierowcy | Token + whitelist / `POST authorize` | `AuthorizeStart` online; `PushAuthenticationData` offline | w OICP o autoryzacji może zdecydować hub |
| zdalny start | Command `START_SESSION` (wynik asynchroniczny) | `AuthorizeRemoteStart` → `Acknowledgement` | model potrzebuje stanu „zlecono”, osobnego od „ruszyło” [założenie] |
| sesja w toku | Session (PUT/PATCH, okresy) | `ChargingNotifications` Start/Progress/End | OICP nie ma pełnej encji sesji z okresami |
| rozliczenie | CDR | `ChargeDetailRecord` | zob. `dom-ev-cdr-settlement` |
| cennik | Tariff (elementy, restrykcje) | `PricingProductData` + `EVSEPricing` | inny model wyceny; kalkulacja po stronie CPO |

## Różnice semantyczne
- **Kto nadaje identyfikator sesji:** w OICP hub (SessionID) po pierwszym żądaniu; w OCPI CPO. Model: osobne
  pola `external_session_id` na protokół, nie jedno wspólne.
- **Synchroniczność:** OICP odpowiada od razu `Acknowledgement` (czas żądania poniżej 10 s zalecany); OCPI komendy
  kończą się wynikiem później. Stan „zlecono → potwierdzono przez ładowarkę” musi istnieć w modelu niezależnie.
- **CDR:** OICP przyjmuje jeden CDR na SessionID; OCPI ma CDR niezmienne z korektą kredytową. Zasady wewnętrzne
  (kiedy zamykasz sesję i wystawiasz CDR) muszą spełniać oba, więc wysyłka jest idempotentna, a korekta trafia
  tylko tam, gdzie protokół ją opisuje [do weryfikacji dla OICP].
- **Status i dane EVSE:** OICP pull wymaga paginacji i może dać `null` w polach wypchniętych starszą wersją; OCPI
  ma własne reguły push/pull i `last_updated`.
- **Strefy czasu:** OICP zachowuje czas w oryginalnej formie z offsetem; w modelu trzymaj instant UTC **i** strefę
  stacji, by odtworzyć oba formaty.
- **Błędy:** kody OICP (`000`, `017`, `603`…) kontra statusy OCPI 1xxx–4xxx (`dom-ev-ocpi`); jedna taksonomia błędów
  modelu, mapowanie w adapterach.

## Szkic adaptera
```
domain event (SessionClosed)  ->  OcpiCdrAdapter  -> PUT /cdrs (dom-ev-ocpi)
                              ->  OicpCdrAdapter  -> eRoamingChargeDetailRecord (SessionID huba)
                                   |- wymusza: ChargingStart, ChargingEnd, ConsumedEnergy, strefa
                                   |- idempotencja po (sessionId huba): drugi send = brak wysyłki
                                   `- odpowiedź Acknowledgement.Result=false -> kolejka ponowień z limitem
```
Kolejki push OICP: po jednej na operację i na partnera; w kolejce jedno wysyłanie naraz, następne po odpowiedzi.
Test: nagrane odpowiedzi huba (kody 017, 018, 603, 604) jako przypadki kontraktowe adaptera; testy bez prawdziwego
huba — `dom-ev-simulation-testing`.
