# Moduły, endpointy, paginacja i routing OCPI

Spis treści: 1. Wersje i endpoint `versions` · 2. Struktury URL modułów · 3. Paginacja · 4. Routing przez hub ·
5. Locations — pola i statusy

Źródło: specyfikacja OCPI (github.com/ocpi/ocpi, tagi `v2.2.1-d2` i `v2.3.0`), czytana 2026-10-20. Zgodne w obu wersjach,
o ile nie zaznaczono inaczej.

## 1. Wersje i endpoint `versions`
- Każda strona (CPO, eMSP) wystawia **endpoint wersji** (lista wersji OCPI z adresami) i **szczegóły wersji** (lista
  modułów: `identifier`, `role`, `url`). Struktura adresów jest dowolna; adres `versions` przekazuje się poza OCPI.
- `role` to `SENDER` albo `RECEIVER`. Dla `credentials` pole nie ma znaczenia (zalecane `SENDER` dla własnego).
- Platforma z rolami CPO i eMSP może wystawić jedno szczegółowe zestawienie dla obu ról (od 2.2).
- Własne moduły: dodatkowe `ModuleID` z prefiksem strony (`kraj+party_id`), wysyłane tylko partnerom po umowie.
- Zmiana listy endpointów w bieżącej wersji: `PUT` na `credentials` partnera (pobierze endpointy ponownie).
- Przejście na nowszą wersję (2.2.1 → 2.3.0): `PUT` na `credentials` w nowej wersji; obie strony muszą ją wdrożyć.

## 2. Struktury URL modułów
| Moduł | Interfejs | URL i metody |
|---|---|---|
| `credentials` | obie | `{credentials}`: GET (moje poświadczenia), POST (rejestracja), PUT (aktualizacja), DELETE (wyrejestrowanie); PATCH niedostępny |
| `locations` | Sender (CPO) | `GET {locations}?date_from&date_to&offset&limit`; `GET {locations}/{location_id}[/{evse_uid}][/{connector_id}]` |
| `locations` | Receiver (eMSP) | `{locations}/{country_code}/{party_id}/{location_id}[/{evse_uid}][/{connector_id}]`: GET, PUT, PATCH |
| `sessions` | Sender (CPO) | `GET {sessions}?date_from=...` (`date_from` wymagany); `PUT {sessions}/{session_id}/charging_preferences` |
| `sessions` | Receiver (eMSP) | `{sessions}/{country_code}/{party_id}/{session_id}`: GET, PUT, PATCH |
| `tokens` | Sender (eMSP) | `GET {tokens}?...`; `POST {tokens}/{token_uid}/authorize[?type=]` (ciało: opcjonalne `LocationReferences`) |
| `tokens` | Receiver (CPO) | `{tokens}/{country_code}/{party_id}/{token_uid}[?type=]`: GET, PUT, PATCH; brak DELETE |
| `commands` | Receiver (CPO) | `POST {commands}/{command}` |
| `commands` | Sender (eMSP) | `POST {response_url}` podany w żądaniu (wynik) |
| `cdrs`, `tariffs` | — | jak `sessions`; CDR bez PUT/PATCH/DELETE — `dom-ev-cdr-settlement`, `dom-ev-tariffs-pricing` |

`type` tokena domyślnie `RFID`; ten sam `uid` może istnieć w różnych typach. Obiekty „klienta” (Client Owned Object)
nie mają POST: nowy obiekt tworzysz PUT-em. `{id}` w URL musi równać się `id` w obiekcie (inaczej 2001). Serwer może
odpowiedzieć 404 na URL z trójką, której nie zgłoszono w `roles` podczas handshake.

## 3. Paginacja
- Parametry: `offset` (domyślnie 0), `limit`, `date_from` (≥, według `last_updated`), `date_to` (<).
  Kolejne zapytanie zaczyna od `date_to` poprzedniego bez nakładania.
- Nagłówki: `Link` (następna strona; tylko gdy nie ostatnia; zawiera filtry), `X-Total-Count` (wszystkie pasujące
  dla tego klienta — serwer może ukrywać cudze obiekty), `X-Limit` (górna granica, także gdy zwrócono mniej).
- Kolejność obiektów stabilna (rosnąco po utworzeniu). Nowy obiekt w trakcie → `X-Total-Count` rośnie, zmienia się tylko
  ostatnia strona. Aktualizacja obiektu przy filtrze `date_to` → liczba maleje: cofnij `offset` o 1.
- „Starsze informacje niewymienione w odpowiedzi” przy pełnym pull są nieważne; pola pominięte traktuj jak NULL.
- Klient przetwarza poprawne obiekty z listy, a niepoprawne loguje; serwerowi nie ma jak zwrócić błędu.

## 4. Routing przez hub
- Nagłówki: `OCPI-from-country-code`, `OCPI-from-party-id`, `OCPI-to-country-code`, `OCPI-to-party-id` (kod: 2 znaki,
  party: 3 znaki). Wymagane do zaimplementowania dla każdego żądania i odpowiedzi modułu funkcjonalnego.
- Bez huba, dwie strony po jednej roli: nagłówki zwykle zbędne, ale implementuj je (partner może mieć kilka ról).
- Platforma ↔ platforma: żądanie `from` = nadawca, `to` = odbiorca; odpowiedź odwrotnie. Przez hub ten sam układ na każdym odcinku.
- **Broadcast Push**: `to` = hub; hub rozsyła do wszystkich klientów o przeciwnej roli (rola „Other” traktowana jak eMSP;
  od „Other” tylko do CPO). Tylko dane przeznaczone dla wszystkich: Locations, Tokens.
- **Open routing**: pominięcie `to`; hub dobiera odbiorcę z treści lub rozsyła. Działa dla GET (nie „GET All”), POST, PUT, PATCH, DELETE.
- **GET All** przez hub: `to` = hub, GET na interfejsie Sender huba; właściciela obiektu poznajesz z pól obiektu.
- Błędy huba: 4001 nieznany odbiorca, 4002 timeout przekazanego żądania, 4003 odbiorca niepołączony; błąd 2xxx/3xxx
  odbiorcy hub przekazuje nadawcy (poza Broadcast Push).
- 2.3.0: pole `hub_party_id` w Credentials i raportowanie stron za hubem w `roles` (inaczej niż w 2.2.1, gdzie hub
  zgłaszał tylko siebie, a strony szły przez moduł `hubclientinfo`) — `references/wersje-i-zmiany.md`.

## 5. Locations — pola i statusy
| Obiekt | Klucz | Uwaga |
|---|---|---|
| Location | `id` (do 36 znaków) | wiele EVSE; nie usuwasz |
| EVSE | `uid` (do 36), opcjonalny `evse_id` (do 48) | `uid` stały; `physical_reference` to napis na urządzeniu |
| Connector | `id` w obrębie EVSE | typ złącza, moc, `tariff_ids` |

- `status` EVSE: `AVAILABLE`, `BLOCKED` (np. zastawione autem), `CHARGING`, `INOPERATIVE`, `OUTOFORDER`, `PLANNED`,
  `REMOVED`, `RESERVED`, `UNKNOWN` (też gdy offline). Mapowanie z `StatusNotification` OCPP: `dom-ev-ocpp-16`, `dom-ev-ocpp-2x`.
- Aktualizacje: PUT całego obiektu albo PATCH tylko zmian (PATCH może dotyczyć Location, EVSE lub Connector przez dłuższy URL).
- Pull po pierwszym połączeniu albo gdy cache eMSP jest wątpliwy; push w normalnej pracy (małe opóźnienie statusu).
- Moduł Locations na Receiverze zależy od Tariffs: eMSP ma znać taryfy przypisane do złączy.
- 2.3.0: `evse_id` wg „E-mobility ID-codes” (IDACS), `parking[]`, `accepted_service_providers`, `help_phone`,
  `capabilities` ze zgodnością z ISO 15118, nowe typy złączy (np. MCS) — `references/wersje-i-zmiany.md`.
