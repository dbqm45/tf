---
name: dom-ev-glossary
description: Użyj przy nazewnictwie w branży EV — hierarchia Location/EVSE/Connector, CSMS vs CPMS, sesja vs transakcja, kW vs kWh, nazwy w kodzie, UI i dokumentacji.
metadata:
  przeglad: 2027-04-20
  katalog: "Użyj, gdy trzeba ustalić lub ujednolicić pojęcia EV po polsku i angielsku — hierarchia Location → stacja → EVSE → Connector i liczenie punktów ładowania po EVSE, CSMS/CPMS/Central System, Charge Point vs Charging Station, sesja vs transakcja, token, SoC/SoH, kW vs kWh, AC/DC, skróty (CDR, EMAID, SECC, DLM) oraz reguły nazw w kodzie, UI i dokumentacji (evse_id, energy_kwh, power_kw). Nie do ról rynku i przepływów pieniędzy (dom-ev-market-roles), formatów identyfikatorów (dom-ev-identifiers) ani komunikatów OCPP (dom-ev-ocpp-16, dom-ev-ocpp-2x)."
  slowa: "słownik, glossary, terminologia, nazewnictwo, punkt ładowania, charging point, stacja ładowania, charging station, charge point, EVSE, connector, złącze, CSMS, CPMS, Central System, sesja, transakcja, token, SoC, SoH, kW, kWh, AC, DC, Mode 3, SECC, EVCC, DLM, load management, ujednolicić nazwy, naming, ubiquitous language"
---

# Słownik EV — pojęcia i nazwy

Skill daje **jedno znaczenie na termin** i regułę, jak to nazwać w kodzie, UI i dokumentacji. Źródła: references skilla
`dom-ev-charging` (import 2024–2025) i wiedza ogólna; fakty spoza źródeł oznaczono **[do weryfikacji]**.
Kto komu płaci → `dom-ev-market-roles`. Jak wygląda ID → `dom-ev-identifiers`. Jaki komunikat → `dom-ev-ocpp-16`,
`dom-ev-ocpp-2x`.

## Procedura
1. Rozpoznaj **poziom hierarchii**, o którym mowa (lokalizacja, urządzenie, miejsce do ładowania, wtyczka).
2. Wybierz jedną nazwę kanoniczną z tabeli „Hierarchia” i „Mówimy / nie mówimy”.
3. Rozstrzygnij kontekst nazwy: protokół (OCPP/OCPI) zachowuje własne słownictwo w warstwie integracji; **domena i UI
   używają słownika kanonicznego**, a mapowanie jest w jednym miejscu (adapter).
4. Nazwy w kodzie: jednostka w nazwie lub w typie, ID z prefiksem poziomu (`evse_id`, nie `id`).
5. Zapisz decyzję w słowniku projektu (np. `docs/glossary.md`) — jedna tabela, nie rozproszone komentarze.

## Hierarchia (od ogółu)
| Poziom | Nazwa kanoniczna | Co to jest | Uwaga |
|---|---|---|---|
| 1 | **Location** (lokalizacja) | adres / pinezka na mapie, parking | w OCPI obiekt `Location` |
| 2 | **Charging Station** (stacja, słupek) | fizyczne urządzenie z elektroniką, jedno połączenie z CSMS | OCPI nie ma osobnego obiektu: Location → EVSE bezpośrednio |
| 3 | **EVSE** | część, która **ładuje jedno auto naraz** | jednostka dostępności („wolne/zajęte”), rezerwacji i sesji |
| 4 | **Connector** (złącze) | fizyczna wtyczka: Type 2, CCS2, CHAdeMO, NACS | na EVSE aktywne jedno naraz |

**Liczenie punktów ładowania = liczba EVSE.** Słupek z dwoma gniazdami, z których auto używa jednego naraz, to **jeden**
punkt. Przykład: 6 słupków × 2 złącza (Type 2 i CCS2) na EVSE po jednym → **6** punktów, nie 12 i nie 6 „słupków” z
założenia — policz EVSE. Jeśli słupek ma dwa niezależne EVSE (dwa auta naraz), to 2 punkty.
Zgodność z unijnym AFIR (definicja „punktu ładowania”) — **[do weryfikacji]**; w tej definicji kluczowe jest „jeden
pojazd naraz”.

## Mówimy / nie mówimy
| Mówimy | Nie mówimy | Dlaczego |
|---|---|---|
| **EVSE** (punkt ładowania w sensie dostępności) | „port”, „gniazdo”, „ładowarka” jako jednostka liczenia | te słowa nie mówią, czy chodzi o wtyczkę, czy miejsce na auto |
| **Connector** / złącze | „EVSE” dla wtyczki | dwa złącza na jednym EVSE to jedno miejsce |
| **Charging Station** (stacja) = urządzenie | „stacja” dla całego parkingu | cały parking to **Location** |
| **Location** | „stacja” dla adresu | w PL „stacja ładowania” bywa i adresem, i słupkiem — unikaj w specyfikacji |
| **CSMS** (nazwa kanoniczna w kodzie i docs) | CPMS i Central System jako osobne byty | jedna rola, trzy nazwy z różnych źródeł (tabela niżej) |
| **sesja** (biznes, OCPI) | „transakcja” dla sesji eMSP | transakcja jest pojęciem urządzenia (OCPP) |
| **transakcja** (OCPP) | „sesja” przy `transactionId` | inne ID, inny właściciel danych |
| **energy_kwh**, **power_kw** | `power` dla energii, „kW” dla zużycia | kW to moc, kWh to energia |
| **token** (identyfikator uprawnienia: RFID, aplikacja) | „token” dla JWT/sekretu API | w EV token to nośnik tożsamości płatnika, nie sekret |
| **SoC** (stan naładowania, %) | „poziom baterii” w modelu | SoC może być niedostępny bez ISO 15118 |

## CSMS, CPMS, Central System
To **ta sama rola**: backend, z którym łączą się stacje po OCPP.
| Nazwa | Skąd | Gdzie używać |
|---|---|---|
| **Central System** | OCPP 1.6 | tylko przy cytowaniu 1.6 |
| **CSMS** (Charging Station Management System) | OCPP 2.0.1 (termin formalny) | **domyślnie w kodzie i dokumentacji** |
| **CPMS** (Charge Point Management System) | slang branżowy | w rozmowie, w UI marketingowym; nie w nowym kodzie |
CSMS bywa mylony z całym CPO: **CPO** to firma/rola rynkowa, **CSMS** to oprogramowanie (`dom-ev-market-roles`).

## Charge Point vs Charging Station
- OCPP 1.6 mówi **Charge Point**, OCPP 2.0.1 mówi **Charging Station** — to ten sam poziom urządzenia.
- Hierarchia 2.0.1: Charging Station → EVSE → Connector. W 1.6: Charge Point → connector (numerowany `connectorId`);
  osobnego EVSE nie ma, więc w 1.6 **connector odgrywa rolę EVSE** — ostrożnie przy mapowaniu **[do weryfikacji]**.
- W kodzie domeny: `ChargingStation`; w adapterze 1.6 zostaw `ChargePoint` i mapuj.
- Dodatkowa pułapka polska: „punkt ładowania” (prawo, AFIR) odpowiada **EVSE**, a „stacja ładowania” — urządzeniu lub
  miejscu z wieloma punktami. Pełne tabele nazw → `references/mapa-nazw-protokolow.md`.

## Sesja, transakcja, CDR, token
| Pojęcie | Warstwa | Znaczenie |
|---|---|---|
| **Transaction** | OCPP | okres ładowania widziany przez urządzenie: od startu do stopu; 1.6 `transactionId`, 2.0.1 `TransactionEvent` |
| **Session** | OCPI / biznes | trwające ładowanie widziane przez eMSP; zmienia się w czasie |
| **CDR** (Charge Detail Record) | OCPI | **zamknięty, niezmienny** zapis do rozliczenia; korekta = nowy CDR kredytowy |
| **Token** | OCPI / OCPP | nośnik uprawnienia: karta RFID, aplikacja, certyfikat (1.6 `idTag`, 2.0.1 `idToken`) |
Zwykle jedna sesja OCPI odpowiada jednej transakcji OCPP, ale **nie zakładaj 1:1 w modelu** **[do weryfikacji]**.
Szczegóły przebiegu (cykl sesji) → `dom-ev-charging`.

## Skróty (krótkie hasła)
| Skrót | Znaczenie |
|---|---|
| **EMAID** | identyfikator kontraktu e-mobility; Plug & Charge — format → `dom-ev-identifiers` |
| **EVCO** (EVCO ID) | w obiegu jako synonim identyfikatora kontraktu **[do weryfikacji]** |
| **SECC** | kontroler komunikacji po stronie ładowarki (ISO 15118) **[do weryfikacji]** |
| **EVCC** | kontroler komunikacji po stronie pojazdu (ISO 15118) **[do weryfikacji]** |
| **DLM** (Dynamic Load Management) | dynamiczny podział mocy między punktami, by nie przekroczyć przyłącza; to nie sterowanie wg taryfy ani smart charging CSMS |
| **SoC / SoH** | SoC = stan naładowania (%), SoH = stan zdrowia akumulatora (zużycie, **nie** ten sam wskaźnik) |
| **AC / DC** | AC: konwersja w aucie (ładowarka pokładowa, typowo 3,7–22 kW); DC: prąd stały do baterii |
| **Mode 1–4** | tryby ładowania wg IEC 61851 — tu tylko pojęcie; Mode 3 = AC ze stacją z komunikacją, Mode 4 = DC **[do weryfikacji]**; szczegóły sprzętowe poza zakresem |
Pełniejsza lista A–Z → `references/skroty-a-z.md`.

## Reguły nazw w kodzie
| Reguła | Dobrze | Źle |
|---|---|---|
| ID z prefiksem poziomu | `evse_id`, `connector_id`, `location_id` | `id`, `station_id` dla EVSE |
| ID publiczne a techniczne | `evse_id` (łańcuch roamingowy) obok `evse_uid`/klucz bazy | jedno pole `id` na oba |
| Energia | `energy_kwh` (kWh) | `kwh`, `power` |
| Moc | `power_kw` (kW) | `kw` dla energii |
| SoC | `soc_percent` | `battery` |
| Pieniądze | kwota + `currency` w typie `Money` | `float price` |
| Czas | UTC w ISO 8601, `_at` | lokalny czas bez strefy |
| Stany | enum domenowy + mapowanie protokołów w adapterze | stringi statusów OCPP w domenie |
| Wersje | wersja protokołu w nazwie adaptera: `ocpp16`, `ocpp201` | jeden „ocpp” dla obu |
Jednostka w nazwie nie zastępuje typu: jeśli język ma typy wartości (`Energy`, `Power`), użyj ich i zachowaj sufiks w
polach serializowanych (DTO, kolumny, JSON). Pole w OCPI zachowuj w oryginale (`country_code`, `party_id`, `evse_id`).

## Przykład
**Wejście:** „W kodzie `ChargePoint`, w UI «punkt», w specyfikacji 2.0.1 «Charging Station»; backend raz CPMS, raz
Central System.”
**Wynik:**
1. Domena: `Location` → `ChargingStation` → `Evse` → `Connector`; backend = **CSMS**.
2. UI: „punkt ładowania” = **EVSE** (liczone po EVSE), „stacja” = urządzenie, adres = „lokalizacja”.
3. Adapter OCPP 1.6: `ChargePoint`/`Central System` mapowane na domenę w jednym pliku; w 2.0.1 bez mapowania.
4. Dopisz 8–10 wierszy do `docs/glossary.md` i sprawdź grepem, że `CPMS` i `ChargePoint` zostały tylko w adapterach.

## Pułapki
- Liczenie punktów po słupkach lub złączach zamiast po EVSE.
- „Stacja” w jednym dokumencie to adres, w innym słupek.
- `power` w polu, w którym leży kWh (i odwrotnie); Excel/CSV bez jednostki w nagłówku.
- Utożsamianie sesji z transakcją i CDR z sesją (CDR powstaje po zakończeniu i jest niezmienny).
- SoC jako wymagane pole sesji; SoH liczony z SoC.
- 22 kW na stacji nie znaczy 22 kW w aucie — limituje ładowarka pokładowa (AC).
- Tłumaczenie terminów protokołu na własne słowa w warstwie integracji; to utrudnia szukanie w specyfikacji.

## Checklista
- [ ] Jednostka liczenia punktów = EVSE; stacja, lokalizacja i złącze nazwane osobno
- [ ] Jedna nazwa backendu (CSMS), mapowanie CPMS/Central System w słowniku
- [ ] Sesja (OCPI) i transakcja (OCPP) nie mieszają się w modelu ani UI
- [ ] Nazwy pól mają jednostki (`_kwh`, `_kw`, `_percent`); waluta osobno
- [ ] Słownik projektu zapisany i podlinkowany z README/AGENTS
- [ ] Fakty oznaczone [do weryfikacji] przekazane do `researcher`

## Czytaj references, gdy…
| Pytanie | Plik |
|---|---|
| ta sama rzecz w OCPP 1.6, OCPP 2.0.1, OCPI i slangu; przepisanie nazw przy migracji | `references/mapa-nazw-protokolow.md` |
| znaczenie skrótu (EMAID, SECC, DLM, SoH, AFIR…) i różnice łatwe do pomylenia | `references/skroty-a-z.md` |

## Źródła
- `dom-ev-charging/references/` (ocpp.md, ocpi.md, cykl-sesji-ladowania.md, infrastruktura-ladowania.md), import
  2024–2025, włączony 2026-09-27; opracowanie własnymi słowami.
- Wiedza ogólna dla SECC/EVCC, Mode 1–4, DLM, AFIR — oznaczona **[do weryfikacji]**, sprawdź przez `researcher`.
