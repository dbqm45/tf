---
name: dom-ev-ocpi
description: Użyj przy integracji OCPI 2.2.1 i 2.3.0 między CPO, eMSP i hubem — handshake tokenów, nagłówki routingu, Sessions, Tokens, Commands, Locations, kody statusu.
metadata:
  przeglad: 2027-04-20
  katalog: "Użyj, gdy budujesz, debugujesz albo testujesz integrację OCPI 2.2.1 lub 2.3.0 jako protokół między CPO, eMSP i hubem — moduły i interfejsy Sender/Receiver, endpoint versions i szczegóły wersji, credentials handshake (token A/B/C, Base64 w Authorization), nagłówki OCPI-from/to-country-code i party-id, paginacja, push vs pull, kody HTTP i statusy OCPI 1000-4003, Sessions (PUT/PATCH, statusy), Tokens (whitelist vs real-time authorization), Commands (asynchroniczny wynik na response_url), Locations (Location/EVSE/Connector, uid vs evse_id), różnice 2.2.1 do 2.3.0, test kontraktowy z partnerem. Nie do taryf, step_size i liczenia ceny (dom-ev-tariffs-pricing), CDR, korekt i rozliczenia (dom-ev-cdr-settlement), sesji end-to-end OCPP+OCPI (dom-ev-session-lifecycle), formatów identyfikatorów (dom-ev-identifiers), komunikatów OCPP (dom-ev-ocpp-16, dom-ev-ocpp-2x) ani protokołu OICP i komercyjnych hubów."
  slowa: "OCPI, OCPI 2.2.1, OCPI 2.3.0, integracja z eMSP, integracja z CPO, roaming, credentials, handshake, CREDENTIALS_TOKEN_A, token A B C, Authorization Token Base64, 401 Unauthorized, versions endpoint, Sender, Receiver, push, pull, paginacja, X-Total-Count, OCPI-from-party-id, OCPI-to-country-code, routing hub, broadcast push, status_code 2001, 3001, 4001, Sessions PATCH, charging_periods, Tokens whitelist, real-time authorization, POST authorize, START_SESSION, response_url, CommandResult, EVSE uid, evse_id, REMOVED, hub_party_id, sandbox partnera, test kontraktowy OCPI, partner OCPI zwraca błąd, eMSP nie widzi naszych stacji"
---

# OCPI 2.2.1 i 2.3.0 — protokół CPO ↔ eMSP ↔ hub

OCPI przenosi dane biznesowe między firmami (lokalizacje, tokeny, sesje, komendy, CDR). Nie steruje sprzętem
(OCPP: `dom-ev-ocpp-16`, `dom-ev-ocpp-2x`) i nie realizuje płatności. Role stron: `dom-ev-market-roles`. Granice tego skilla:
- cena i pola taryfy → `dom-ev-tariffs-pricing`;
- CDR, korekty, rozliczenie → `dom-ev-cdr-settlement`;
- sesja od wpięcia kabla do CDR (OCPP + OCPI razem) → `dom-ev-session-lifecycle`;
- formaty `country_code`, `party_id`, EVSE ID → `dom-ev-identifiers`;
- protokół OICP i huby komercyjne — poza zakresem (osobny temat, jeszcze bez skilla).

## Procedura: nowa integracja z partnerem
1. **Ustal wersję i role.** Wspólna wersja (2.2.1 albo 2.3.0), role obu stron (CPO, eMSP, hub) i moduły partnera.
   Zapisz tag specyfikacji (`references/wersje-i-zmiany.md`).
2. **Przekaż poza OCPI** (bezpiecznym kanałem) `CREDENTIALS_TOKEN_A` i adres `versions`.
3. **Handshake** (niżej); brak oczekiwanych modułów u partnera → 3003.
4. **Pierwsza synchronizacja** pull-em (Locations, Tokens, Tariffs), potem push zmian.
5. **Test kontraktowy** na sandboxie partnera (`references/test-kontraktowy.md`).
6. **Obserwuj:** loguj kod HTTP i `status_code` OCPI, `X-Total-Count` oraz nagłówki routingu.

## Moduły i kierunek
Każdy moduł ma interfejs **Sender** (właściciel danych, partner może pobierać) i **Receiver** (przyjmuje push).
Szczegóły wersji podają `role` interfejsu (`SENDER`/`RECEIVER`), więc firma z kilkoma rolami potrzebuje jednego połączenia.

| Moduł (`ModuleID`) | Właściciel danych | Kierunek zwykły | Uwaga |
|---|---|---|---|
| `credentials`, `versions` | obie strony | symetryczny | moduły konfiguracyjne, bez nagłówków routingu |
| `locations` | CPO | CPO → eMSP (PUT/PATCH), eMSP pobiera GET | status `REMOVED`, bez usuwania |
| `tariffs` | CPO | CPO → eMSP | szczegóły: `dom-ev-tariffs-pricing` |
| `sessions` | CPO | CPO → eMSP | PUT/PATCH, brak DELETE |
| `cdrs` | CPO | CPO → eMSP | szczegóły: `dom-ev-cdr-settlement` |
| `tokens` | eMSP | eMSP → CPO (PUT/PATCH), CPO pobiera GET i `POST authorize` | odwrotny kierunek niż reszta |
| `commands` | brak (wywołanie) | eMSP → CPO, wynik CPO → eMSP | asynchroniczne |
| `chargingprofiles`, `hubclientinfo` | zależnie | — | poza głębokim zakresem |

Pełne endpointy, struktury URL i metody: `references/moduly-i-endpointy.md`.

## Transport w skrócie
| Sprawa | Reguła (OCPI 2.2.1-d2 i 2.3.0) |
|---|---|
| Nagłówek | `Authorization: Token <credentials token po Base64>`; brak lub nieznany token → HTTP 401 |
| Token A | wolno nim tylko `credentials` i `versions`; inny moduł → 401 |
| Odpowiedź | JSON `data`, `status_code` (4 cyfry), `status_message`, `timestamp` |
| Client Owned Object | URL `{base}/{endpoint}/{country_code}/{party_id}/{object_id}`; PUT tworzy i zastępuje, POST nie jest wspierany |
| PUT / PATCH | PUT: wszystkie wymagane pola, pominięte opcjonalne wracają do domyślnych; PATCH: tylko zmiany, po błędzie GET, a gdy obiektu brak — PUT |
| Pull | wymagany (odzyskanie synchronizacji po przerwie); push zalecany na produkcji |

**Paginacja** (każdy GET listy): `offset`, `limit`, `date_from` (włącznie), `date_to` (wyłącznie), według `last_updated`.
Odpowiedź niesie `Link` (`rel="next"` z filtrami), `X-Total-Count` i `X-Limit` (górny limit serwera, nie liczba
zwróconych). Idź po `Link`; serwer może zwrócić mniej niż `limit`.

## Credentials handshake (token A, B, C)
1. **Receiver** tworzy `CREDENTIALS_TOKEN_A` i przekazuje go z adresem `versions` poza OCPI.
2. **Sender** (uzgodniony poza OCPI przed startem) pobiera `versions` i szczegóły wersji tokenem A.
3. Sender generuje `CREDENTIALS_TOKEN_B` i wysyła go w `POST` do `credentials` Receivera (obiekt: `token`,
   `url` swojego `versions`, `roles`).
4. Receiver zapisuje B (używa go wobec Sendera), pobiera endpointy Sendera i zwraca `CREDENTIALS_TOKEN_C`.
5. Od teraz Sender używa **C**; token A wygasa. Ponowne `POST` po rejestracji → HTTP 405, aktualizacja przez `PUT`.

Token w obiekcie Credentials jest jawny (ASCII, do 64 znaków), a w nagłówku `Authorization` idzie po Base64.
Wiele wdrożeń 2.1.1 i 2.2 wysyła token bez Base64 — częsta przyczyna 401 na starcie z partnerem.
Rotacja: `PUT` na `credentials` z nowym tokenem (zalecane co miesiąc, natychmiast przy wycieku). Brak oczekiwanych
modułów: Sender nie wysyła POST, a Receiver odpowiada 3003; błąd połączenia zwrotnego Receivera → 3001.

## Routing (hub i platformy z wieloma rolami)
Cztery nagłówki na żądaniu i odpowiedzi modułów funkcjonalnych: `OCPI-from-country-code`, `OCPI-from-party-id`,
`OCPI-to-country-code`, `OCPI-to-party-id`; odpowiedź zamienia strony. Nie używaj ich w `credentials`, `versions`
i `hubclientinfo`. **Broadcast Push** (do wszystkich o roli przeciwnej, adres huba w `to`) tylko dla danych
wspólnych (Locations, Tokens), nigdy dla Sessions i CDR; GET nie idzie broadcastem. **Open routing** (bez `to`)
zostawia wybór odbiorcy hubowi. W URL obiektu zostaje oryginalna trójka nadawcy.

## Kody statusu
HTTP opisuje transport, `status_code` w ciele — OCPI. Poprawny JSON z istniejącym zasobem nie dostaje błędu HTTP.
Nowy obiekt → 201, zaktualizowany → 200; niepoprawny JSON → 400; GET nieistniejącego → 404.

| Kod OCPI | Znaczenie | Typowy powód |
|---|---|---|
| 1000 | sukces | — |
| 2000 | błąd klienta (ogólny) | — |
| 2001 | złe lub brakujące parametry | PATCH bez `last_updated`; `{id}` w URL ≠ `id` w obiekcie |
| 2002 | za mało informacji | real-time authorize bez `LocationReferences` |
| 2003 | nieznana lokalizacja | START_SESSION na nieznany `location_id` |
| 2004 | nieznany token | real-time authorize nieznanego tokena |
| 3000 | błąd serwera | — |
| 3001 | nie można użyć API klienta | błąd wywołania zwrotnego przy rejestracji |
| 3002 | nieobsługiwana wersja | brak wspólnej wersji |
| 3003 | brak wspólnych endpointów | partner nie wystawia oczekiwanego modułu |
| 4000–4003 | hub: ogólny, nieznany odbiorca, timeout przekazania, odbiorca niepołączony | błąd routingu w hubie |


## Sessions
Właścicielem jest CPO. Statusy: `PENDING` (początkowy), `ACTIVE`, `COMPLETED` (końcowy), `INVALID` (nie będzie
rozliczona), `RESERVATION`. Sesji nie usuwasz.
- **PUT** zastępuje obiekt i **całą listę** `charging_periods` (pusta lista usuwa okresy).
- **PATCH** wymaga `last_updated` i **dodaje** podane `charging_periods` do istniejących; pominięta lub pusta lista nic
  nie zmienia. Aby zastąpić lub usunąć okres, wyślij PUT z całą sesją. PATCH działa tylko na całym obiekcie Session.
- Pull: `GET` sesji wymaga `date_from`; przy wątpliwym stanie u eMSP CPO czyta sesję `GET`-em z Receivera.
- Rezerwacja tworzy Session `RESERVATION`; bez ładowania kończy się `COMPLETED`.
Szczegóły: `references/sesje-tokeny-komendy.md`; powiązanie z transakcją OCPP: `dom-ev-session-lifecycle`.

## Tokens: whitelist czy real-time
Token to **dane kierowcy** (RFID, aplikacja), nie token z `credentials`; eMSP pcha je do CPO.
| `whitelist` | CPO może… |
|---|---|
| `ALWAYS` | zawsze autoryzować z pamięci podręcznej; real-time niedozwolony |
| `ALLOWED` | wybrać pamięć podręczną albo real-time |
| `ALLOWED_OFFLINE` | real-time, a przy braku łączności z eMSP przepuścić |
| `NEVER` | zawsze pytać eMSP (`POST .../tokens/{token_uid}/authorize`) |
Odpowiedź real-time niesie `AuthorizationInfo` (`allowed`: `ALLOWED`, `BLOCKED`, `EXPIRED`, `NO_CREDIT`,
`NOT_ALLOWED`); nieznany token → 2004. Tokeny `APP_USER` i `AD_HOC_USER` zalecane jako `NEVER`. Pull pełnej listy
służy do synchronizacji, nie do autoryzacji.

## Commands (asynchronicznie)
Odpowiedź na `POST {commands}/…` mówi tylko, że **CPO** przyjął polecenie; wynik ze stacji przychodzi później
na `response_url` (`CommandResult`).
- `ACCEPTED` na komendę ≠ sesja wystartowała (sesja istnieje dopiero jako Session). Brak wyniku w `timeout`
  (sekundy, pole komendy) → komenda nieudana.
- Unikalny identyfikator wstaw do `response_url`, by dopasować wynik do żądania.

## Locations
Hierarchia: **Location → EVSE → Connector**; EVSE obsługuje jeden pojazd naraz, więc dostępność czytasz z EVSE.
- `EVSE.uid` to stały identyfikator techniczny CPO; nie zmienia się i nie powinien być numerem sprzętu (EVSE nie
  jest usuwane, a `uid` musi pozostać unikalny po wymianie urządzenia). Sesje i komendy wskazują EVSE przez `uid`.
- `evse_id` jest opcjonalny, czytelny dla człowieka (eMI3, w 2.3.0 IDACS) i może zniknąć przy `REMOVED`
  (format: `dom-ev-identifiers`).
- Usunięcie to `status` = `REMOVED` w PUT/PATCH; Location bez ważnych EVSE jest wygasła. Lokalizacji prywatnych nie publikuj.
- Grupę punktów OCPP mapuj na jedną Location; OCPP 1.x z wieloma złączami na EVSE: jedno „wirtualne” EVSE na złącze.

## Różnice 2.2.1 → 2.3.0 (skrót)
Rozszerzalność (nowe pola i wartości `OpenEnum`; odbiorca **nie odrzuca** nieznanych pól), `Parking` przy EVSE,
`hub_party_id` w Credentials (hub wymienia w `roles` strony za sobą), `EMAID` w `TokenType`, zgodność z ISO 15118
w możliwościach złącza, podatki w Tariff, moduł Payments. Sessions i Commands bez zmian. Tabela i migracja:
`references/wersje-i-zmiany.md`.

## Przykład
Wejście: CPO `PL/ABC` wysyła Session do eMSP, bo przyszły dwa kolejne okresy ładowania.
```
PATCH {sessions_emsp}/PL/ABC/s-1001      Authorization: Token <Base64(C)>
{ "kwh": 11.4, "last_updated": "2026-10-20T10:20:00Z",
  "charging_periods": [ {"start_date_time":"2026-10-20T10:10:00Z","dimensions":[{"type":"ENERGY","volume":5.7}]} ] }
```
Wynik: eMSP **dopisuje** okres. Ponowiony PATCH zdubluje okres, więc po timeoucie najpierw `GET` sesji u eMSP;
przy niepewnym stanie CPO wysyła `PUT` z całą sesją i wszystkimi okresami. Zakończenie: PATCH z `status: COMPLETED`; CDR osobno.

## Pułapki
- Token A użyty po handshake albo token bez Base64 w `Authorization` (401).
- Uznanie odpowiedzi na komendę za start sesji; ignorowanie `CommandResult` i `timeout`.
- PATCH z listą `charging_periods` traktowany jak zamiana listy (dubluje okresy).
- Real-time authorize z kontrolą godzin otwarcia lub statusu EVSE po stronie eMSP (zabronione).
- Sessions i CDR jako Broadcast Push; nagłówki routingu w `credentials`.
- `EVSE.uid` równy numerowi seryjnemu albo `evse_id`; usuwanie EVSE zamiast `REMOVED`.
- Odrzucanie żądań z nieznanymi polami (w 2.3.0 zabronione).
- Polling co minuty zamiast push i pull co godziny.

## Checklista
- [ ] Wersja (2.2.1 / 2.3.0) i role zapisane; wspólne moduły potwierdzone
- [ ] Handshake A → B → C przeszedł; Base64 w `Authorization`; rotacja tokenu opisana
- [ ] Nagłówki routingu tylko na modułach funkcjonalnych; Broadcast Push bez Sessions i CDR
- [ ] Paginacja po `Link`; pull jako odtworzenie po przerwie
- [ ] Sessions: PUT zastępuje, PATCH dopisuje i niesie `last_updated`
- [ ] Tokens: `whitelist` zgodne z modelem autoryzacji; real-time szybki
- [ ] Commands: wynik na `response_url` obsłużony, `timeout` zdefiniowany
- [ ] `uid` stały, `REMOVED` zamiast usuwania
- [ ] Test kontraktowy z partnerem wykonany (`references/test-kontraktowy.md`)
- [ ] Niepewne fakty oznaczone [do weryfikacji]

## Czytaj references, gdy…
| Pytanie | Plik |
|---|---|
| endpointy, struktury URL, paginacja, routing przez hub, pola Locations | `references/moduly-i-endpointy.md` |
| Sessions, Tokens, Commands: przepływy, statusy, wyniki, przypadki brzegowe | `references/sesje-tokeny-komendy.md` |
| zmiany w 2.3.0, migracja 2.2.1 → 2.3.0, tagi specyfikacji | `references/wersje-i-zmiany.md` |
| scenariusze testu kontraktowego z partnerem | `references/test-kontraktowy.md` |

## Źródła
- Specyfikacja OCPI, repozytorium github.com/ocpi/ocpi, tagi `2.2.1`, `v2.2.1-d2`, `v2.3.0` (pliki `transport_and_format`,
  `credentials`, `version_information_endpoint`, `status_codes`, `mod_sessions`, `mod_tokens`, `mod_commands`,
  `mod_locations`, `changelog`), czytane 2026-10-20; treść opracowana własnymi słowami.
- `.claude/skills/dom-ev-charging/references/ocpi.md` (import 2024–2025); przy sprzeczności wygrywa specyfikacja.
- Daty wydań i status Edition 2: [do weryfikacji] (evroaming.org).
