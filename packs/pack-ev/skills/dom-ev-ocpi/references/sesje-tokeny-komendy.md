# Sessions, Tokens, Commands — przepływy i przypadki brzegowe

Spis treści: 1. Sessions · 2. Tokens · 3. Commands · 4. Powiązanie z OCPP

Źródło: specyfikacja OCPI `v2.2.1-d2` i `v2.3.0` (moduły sessions, tokens, commands; w Sessions i Commands obie wersje
mają tę samą treść), czytana 2026-10-20.

## 1. Sessions
- **Własność:** CPO (`country_code`, `party_id`, `id` do 36 znaków). Obiekt niesie m.in. `start_date_time`,
  `end_date_time`, `kwh`, `cdr_token`, `auth_method`, `location_id`, `evse_uid`, `connector_id`, `currency`,
  `charging_periods`, `total_cost`, `status`, `last_updated`.
- **Cykl push:** CPO tworzy obiekt przez PUT, każdą zmianę przekazuje PATCH-em, końcowy status `COMPLETED`.
  Gdy stan u eMSP jest niepewny (np. błąd PATCH), CPO czyta obiekt GET-em z Receivera.
- **Cykl pull:** eMSP bez push pobiera listę GET-em z `date_from`; pull służy też do nadrobienia po awarii eMSP.
- **PUT na istniejący obiekt:** nowy obiekt zastępuje stary; `charging_periods` zastępowane w całości, brak pola lub
  pusta lista usuwa okresy.
- **PATCH:** wymaga `last_updated`; `charging_periods` w PATCH są **dodawane**; zamiana lub usunięcie okresu tylko
  przez PUT całej sesji. Niedozwolone są dodatkowe segmenty URL do pól wewnętrznych.
- **Statusy:** `PENDING` (początkowy, warunki niespełnione), `ACTIVE` (autoryzacja i łączność pojazdu OK, ładowanie
  trwa lub może trwać), `COMPLETED`, `INVALID` (nierozliczana), `RESERVATION`. Przejście `RESERVATION` → `ACTIVE`, gdy
  rezerwacja zamienia się w ładowanie tym samym tokenem; w innym razie `COMPLETED`.
- **`total_cost`:** to cena, którą eMSP zapłaci CPO; `charging_periods` służą do jej policzenia i weryfikacji.
  Sposób liczenia: `dom-ev-tariffs-pricing`. Okres z innego elementu taryfy lub istotnej zmiany (np. prąd) = nowy okres.
- **Charging Preferences:** `PUT {sessions}/{session_id}/charging_preferences` (eMSP → CPO) w trakcie sesji; CPO odpowiada
  jedną z wartości `ChargingPreferencesResponse`; eMSP sprawdza wsparcie po `CHARGING_PREFERENCES_CAPABLE` w EVSE.
- **`evse_uid`, `connector_id`:** przy sesji z rezerwacji, gdy EVSE lub złącze nie jest jeszcze przydzielone, dozwolona wartość `#NA`; nie wstawiaj `evse_id`.

## 2. Tokens
- **Własność:** eMSP. Pola: `uid`, `type` (`RFID`, `APP_USER`, `AD_HOC_USER`, `OTHER`; w 2.3.0 także `EMAID`), `contract_id`
  (zalecany format eMA ID), `visual_number`, `issuer`, `group_id`, `valid`, `whitelist`, `language`, `last_updated`.
  Para (`uid`, `type`) unikalna u eMSP.
- `group_id` łączy tokeny (start jednym, stop drugim); dla OCPP 1.x do 20 znaków (`parentId`).
- **Push:** eMSP PUT-em/PATCH-em wysyła zmiany; unieważnienie = `valid: false` (tokenu nie usuwasz).
- **Pull:** CPO GET-em budując pamięć podręczną na starcie lub gdy jest niepewny; nie do autoryzacji w czasie rzeczywistym.
- **Real-time:** `POST {tokens}/{token_uid}/authorize` z opcjonalnym `LocationReferences` (location_id, evse_uids).
  Brak informacji o lokalizacji → 2002; nieznany token → 2004. eMSP nie sprawdza godzin otwarcia ani statusu EVSE.
  Lokalizacja nieopublikowana (prywatna) zwykle daje `ALLOWED`. Opóźnienie w RFID psuje UX przy czytniku.
- **Wartości `whitelist`:** `ALWAYS` (tylko pamięć podręczna), `ALLOWED` (dowolnie), `ALLOWED_OFFLINE` (real-time,
  a przy braku łączności z eMSP przepuść), `NEVER` (zawsze real-time). `valid=false` nie wyłącza obowiązku real-time.
- `authorization_reference` z `AuthorizationInfo` trafia do Session i CDR — zachowaj, by powiązać autoryzację z rozliczeniem.
- **2.3.0 `EMAID`:** eMSP nie powinien pchać tokenów tego typu; CPO poznaje wystawcę ze stacji (ISO 15118) i pyta
  go real-time. Zarządzanie certyfikatami kontraktu leży poza OCPI. Mechanizm: `.claude/skills/dom-ev-charging/references/iso-15118.md`.

## 3. Commands
- **Komendy:** `START_SESSION`, `STOP_SESSION`, `RESERVE_NOW`, `CANCEL_RESERVATION`, `UNLOCK_CONNECTOR` (tylko operator lub
  eMSP, nigdy bezpośrednio kierowca; do zablokowanego po sesji złącza).
- **Przepływ:** eMSP POST na komendę CPO z `response_url` → CPO odpowiada `CommandResponse` (`ACCEPTED`, `REJECTED`,
  `NOT_SUPPORTED`, `UNKNOWN_SESSION`; tu: czy CPO przekaże komendę) i zawiera `timeout` (sekundy) → CPO przekazuje
  komendę do stacji (np. OCPP) → wynik POST-em na `response_url`.
- **`CommandResult`:** `ACCEPTED`, `CANCELED_RESERVATION`, `EVSE_OCCUPIED`, `EVSE_INOPERATIVE`, `FAILED`, `NOT_SUPPORTED`,
  `REJECTED`, `TIMEOUT`, `UNKNOWN_RESERVATION`. Wynik `ACCEPTED` stacji nadal nie oznacza rozpoczętej sesji — sesja
  pojawia się jako Session.
- **`START_SESSION`:** `token` (autoryzowany przez eMSP), `location_id`, opcjonalnie `evse_uid` (wymagany z
  `connector_id`). Stacje bez zdalnego startu bez kabla kończą się brakiem sesji po limicie czasu.
- **Token `NEVER`:** CPO nie weryfikuje go przed przekazaniem; real-time robi tylko przy późniejszym OCPP `Authorize`
  RFID, gdy `START_SESSION` był ponad 15 minut wcześniej.
- **Rezerwacja:** CPO może ją anulować wywołaniem tego samego `response_url` (wynik `CANCELED_RESERVATION`); rób to
  tylko w sytuacjach awaryjnych (awaria punktu, roboty drogowe).
- Dla `RESERVE_NOW` powstaje Session `RESERVATION`.

## 4. Powiązanie z OCPP (skrót)
| OCPI | OCPP |
|---|---|
| `START_SESSION` | 1.6: `RemoteStartTransaction`; 2.0.1: `RequestStartTransaction` |
| `STOP_SESSION` | 1.6: `RemoteStopTransaction`; 2.0.1: `RequestStopTransaction` |
| `RESERVE_NOW`, `CANCEL_RESERVATION` | `ReserveNow`, `CancelReservation` |
| `UNLOCK_CONNECTOR` | `UnlockConnector` |
| Tokens (pamięć podręczna) | `Authorize` / lista lokalna |
Szczegóły kolejności: `dom-ev-session-lifecycle` (`.claude/skills/dom-ev-session-lifecycle/references/sekwencje.md`), komunikaty: `dom-ev-ocpp-16`, `dom-ev-ocpp-2x`.
Nazwy komunikatów OCPP wg wiedzy ogólnej, nie ze specyfikacji OCPI [do weryfikacji w specyfikacji OCPP].
