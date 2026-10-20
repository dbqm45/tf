# Mapa i dostępność ładowarek

Spis treści: 1. Pola Locations do mapy · 2. Status EVSE i jego opóźnienie · 3. Filtry · 4. Deduplikacja ·
5. Jakość danych · 6. Wymogi: AFIR i NEVI · 7. Integracje samochodowe i nawigacja

Źródło: OCPI `v2.3.0` i `v2.2.1-d2`, mod_locations (baza wiedzy, pobrane 2026-10-20); AFIR art. 5 i 20 (`eu-afir`,
eur-lex, wersja skonsolidowana 08.01.2026); NEVI 23 CFR 680.116 (`us-nevi`, ecfr.gov). Pozostałe: wiedza ogólna.

## 1. Pola Locations do mapy
| Potrzeba UI | Pole OCPI | Uwaga |
|---|---|---|
| pinezka | `Location.coordinates` | |
| kto operuje | `operator`, `owner`, `suboperator` | |
| udogodnienia | `facilities` (`HOTEL`, `RESTAURANT`, `CAFE`, `MALL`, `SUPERMARKET`, `WIFI`, `TAXI_STAND` i inne) | `OpenEnum`: nieznane wartości nie psują odbioru |
| godziny | `opening_times` (`twentyfourseven`, `regular_hours`, `exceptional_openings`, `exceptional_closings`), `time_zone` | czas lokalny lokacji; `charging_when_closed` mówi, czy trwające ładowanie przeżyje zamknięcie |
| status | `EVSE.status` (`AVAILABLE`, `CHARGING`, `BLOCKED`, `RESERVED`, `INOPERATIVE`, `OUTOFORDER`, `PLANNED`, `REMOVED`, `UNKNOWN`), `status_schedule` | `UNKNOWN` także gdy stacja offline |
| złącze | `Connector.standard`, `format` (socket/cable), `power_type` | |
| moc | `Connector.max_electric_power` (W), jeśli brak: `max_voltage` × `max_amperage` | gdy `max_electric_power` jest niższe niż iloczyn, ono wygrywa |
| cena | `Connector.tariff_ids` → Tariffs | `dom-ev-tariffs-pricing` |
| możliwości | `EVSE.capabilities`: `REMOTE_START_STOP_CAPABLE`, `RFID_READER`, `RESERVABLE`, `CREDIT_CARD_PAYABLE` itd.; złącze: `ISO_15118_2_PLUG_AND_CHARGE`, `ISO_15118_20_PLUG_AND_CHARGE` | steruje przyciskami w aplikacji |
| parking | `parking_type`, `EVSE.parking_restrictions` (`CUSTOMERS`, `DISABLED`, `EV_ONLY`, `PLUGGED`, `TAXIS`...) | |
| prywatność | `publish`, `publish_allowed_to` | `publish: false` → pokaż tylko tokenom z listy; lokalizacji prywatnych nie publikuj |

Zasady: przycisk Start pokazuj tylko przy `REMOTE_START_STOP_CAPABLE`; płatność kartą na miejscu sygnalizuj
capability `CREDIT_CARD_PAYABLE`/`DEBIT_CARD_PAYABLE`/`CONTACTLESS_CARD_SUPPORT` (płatność: `dom-ev-payments`).
Lokalizacja bez ważnych EVSE jest wygasła i nie ma być na mapie. `EVSE.uid` jest kluczem technicznym, a
`evse_id` nazwą dla człowieka (`dom-ev-identifiers`).

## 2. Status EVSE i jego opóźnienie
Droga statusu: ładowarka (OCPP `StatusNotification`) → CSMS → push OCPI PATCH Location/EVSE → eMSP → cache →
aplikacja. Każdy człon dodaje opóźnienie, a przerwa w łączności ładowarki może go zatrzymać bez żadnej zmiany w danych.
- Specyfikacja mówi tylko, że push przekazuje zmiany „(semi) real-time”; **gwarantowanego czasu nie podaje**.
  Konkretne opóźnienia zmierz u partnera [do weryfikacji, w bazie brak liczb].
- Zmierz i alarmuj: różnicę między `EVSE.last_updated` a czasem odbioru, p95 per CPO. To jest metryka jakości źródła.
- Reguły prezentacji: pokaż wiek („zaktualizowano 3 min temu”); po progu nieświeżości traktuj status jak
  `UNKNOWN`; `AVAILABLE` nie jest obietnicą (kierowca może zająć miejsce wcześniej); `RESERVED`, `BLOCKED`
  (przeszkoda fizyczna, np. auto bez ładowania) i `CHARGING` ukrywaj za filtrem „dostępne teraz”.
- Nie odpytuj CPO co minutę zamiast push; pull służy do odtworzenia po przerwie (`dom-ev-ocpi`).
- Statusów OCPP nie mapuj na kierowcę 1:1: `Faulted`/`Unavailable` to `OUTOFORDER`/`INOPERATIVE`, a nie „zajęte”.

## 3. Filtry
| Filtr | Źródło | Pułapka |
|---|---|---|
| typ złącza | `Connector.standard` | auto z gniazdem CCS wymaga także `format` kabel; adaptery poza OCPI |
| moc | `max_electric_power` | moc stacji ≠ moc dla auta; auto ogranicza krzywa (`dom-ev-vehicle-battery`) |
| cena | wyliczenie z Tariffs dla profilu kierowcy | prosta „cena za kWh” ukrywa opłaty za postój i startową; porównuj koszt typowej sesji |
| dostępność | `EVSE.status` + wiek | patrz sekcja 2 |
| udogodnienia | `facilities` | |
| godziny | `opening_times` w `time_zone` lokacji | liczysz „otwarte teraz” w strefie lokacji, nie kierowcy |
| tylko moje karty/roaming | umowa eMSP↔CPO | pokaż tylko stacje, na których kierowca może ładować (kontrakt, hub) |

Cena według filtra, którą pokazujesz na liście, musi być tą samą, co przed startem; zapisz identyfikator taryfy.

## 4. Deduplikacja stacji z kilku źródeł
- **Klucz silny:** `evse_id` (jeśli oba źródła go mają, po normalizacji z `dom-ev-identifiers`) albo ta sama trójka
  (`country_code`, `party_id`, `Location.id`) z OCPI. Ten sam CPO widziany bezpośrednio i przez hub: wybierz
  jedno źródło dla statusu (preferuj bezpośrednie).
- **Klucz słaby:** odległość współrzędnych, ta sama nazwa, ten sam operator. Daje **kandydata do scalenia**, nie
  scalenie; w sporze kandyduje człowiek.
- **Nie scalaj** różnych operatorów na tym samym parkingu: to różne stacje z różnymi cenami.
- **Zasada źródła prawdy:** dla każdego pola jedno źródło (status i cena od CPO, zdjęcia/opinie od własnych danych).
- Zapisuj mapowanie źródło → stacja kanoniczna z historią, żeby cofnąć błędne scalenie.
- Usunięcie: `REMOVED` w źródle → zdejmij z mapy, ale nie kasuj mapowania (sesje historyczne się do niego odnoszą).

## 5. Jakość danych
Kontrola przy każdym imporcie: współrzędne w kraju i nie `0,0`; `time_zone` ważna; złącze z mocą > 0; `tariff_ids`
wskazuje istniejącą taryfę; EVSE bez złączy odrzuć; ostatnia aktualizacja nie starsza niż próg. Zgłaszaj CPO
błędy zbiorczo i mierz odsetek odrzuceń per źródło. Dane od kierowców (zgłoszenie „nie ma tu stacji”, zdjęcia)
traktuj jako dane pomocnicze, nie nadpisuj nimi danych CPO.

## 6. Wymogi: AFIR i NEVI
- **AFIR art. 20 ust. 2** (zapis w bazie `eu-afir`): operatorzy ogólnodostępnych punktów zapewniają **bezpłatnie** dane
  statyczne (m.in. nazwa operatora, liczba punktów, helpdesk, udogodnienia, godziny otwarcia, typ złącza, moc stacji
  i punktu, Plug & Charge, smart charging, 100 % OZE) oraz dynamiczne: **operational status, availability, ad hoc price**.
  Dane trafiają przez API do krajowych punktów dostępu (NAP). To obowiązek operatora punktu, więc eMSP odbiera dane
  przez OCPI od CPO i nie musi dublować NAP. Pełna lista pozycji i terminy: `dom-ev-regulations-eu`.
- **AFIR art. 5 ust. 3–4:** ceny rozsądne, porównywalne, przejrzyste i niedyskryminujące (także wobec eMSP);
  od 50 kW cena ad hoc oparta na cenie za kWh, ewentualnie plus opłata za minutę za zajmowanie, i pokazana przed startem.
  Dotyczy ceny ad hoc na stacji; cena dla kontraktu eMSP ma własne warunki, a prezentację w aplikacji uzgodnij z prawnikiem.
- **NEVI 23 CFR 680.116(c)** (`us-nevi`): dane dla stron trzecich bezpłatnie przez API, m.in. identyfikator stacji,
  adres, współrzędne, operator, status stacji, godziny, liczba portów, **identyfikator portu**, typy złączy, poziom
  ładowania, moc portu, **status portu w czasie rzeczywistym w terminach OCPI 2.2.1**, struktura ceny, cena w czasie
  rzeczywistym, akceptowane metody płatności. Punkt (a): cena pokazana przed startem, w USD za kWh, cena z chwili
  startu nie zmienia się w trakcie sesji. Wymóg dotyczy stacji dofinansowanych NEVI.
- Dla UE zasada ta sama co w NEVI (a)(2): zablokuj cenę wyświetloną przy starcie dla tej sesji.

## 7. Integracje samochodowe i nawigacja [do weryfikacji, w bazie brak źródeł]
- **Apple CarPlay i Android Auto:** aplikacje ładowania/nawigacji działają w nich w ramach szablonów platform
  (listy, mapy, przyciski), z ograniczeniami interakcji w czasie jazdy. Kategorie aplikacji, wymagania zgód
  (entitlement u Apple, kategoria w Google Play) i lista dozwolonych szablonów musisz sprawdzić w aktualnej
  dokumentacji platform przed obietnicą funkcji. Zakładaj: lista najbliższych ładowarek z krótkim opisem, bez
  swobodnego wpisywania tekstu, bez długich formularzy, start sesji najlepiej przez telefon.
- **Nawigacja w aucie:** producenci aut bywają odbiorcą tych samych danych (Locations, status, cena) w swoich
  systemach; kontrakt, format (często OCPI lub API pośrednika) i wymagania SLA ustalasz z producentem/hubem.
  Zadbaj o: stabilny identyfikator stacji kanonicznej, wiek statusu w odpowiedzi i trasę do `coordinates` wejścia na parking.
- Dla trasy z ładowaniem (planer): potrzebne są moc ładowarki, krzywa auta i status; ETA ładowania:
  `dom-ev-vehicle-battery`.
