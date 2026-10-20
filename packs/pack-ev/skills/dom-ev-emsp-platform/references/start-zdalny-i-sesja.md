# Start zdalny i sesja w aplikacji

Spis treści: 1. Przepływ · 2. Stany aplikacji · 3. CommandResult na komunikat · 4. Idempotencja i ponowienia ·
5. Postęp sesji · 6. Stop · 7. Cena przed startem · 8. Błędy pokazywane kierowcy

Źródło: OCPI `v2.2.1-d2` i `v2.3.0`, mod_commands i mod_sessions (baza wiedzy, pobrane 2026-10-20; w tych modułach obie
wersje mają tę samą treść). Szczegóły protokołu: `dom-ev-ocpi`; kolejność z OCPP: `dom-ev-session-lifecycle`.

## 1. Przepływ
```
aplikacja -> backend eMSP -> POST {commands CPO}/START_SESSION { response_url, token, location_id, evse_uid, authorization_reference }
CPO -> eMSP:   CommandResponse { result: ACCEPTED|REJECTED|NOT_SUPPORTED|UNKNOWN_SESSION, timeout }   (HTTP, od razu)
CPO -> stacja: OCPP RemoteStartTransaction / RequestStartTransaction
CPO -> eMSP:   POST response_url { result: CommandResult }                                          (asynchronicznie)
CPO -> eMSP:   PUT/PATCH Sessions (status ACTIVE)                                                   (dopiero gdy ładowanie trwa)
```
Odpowiedź `CommandResponse` mówi, czy CPO **przekaże** polecenie. `CommandResult` mówi, co zrobiła stacja.
Nawet `CommandResult: ACCEPTED` nie oznacza sesji: ta pojawia się jako obiekt Session. Stacja, która czeka na
kabel, bez niego nie utworzy sesji do końca limitu czasu.

## 2. Stany aplikacji
| Stan UI | Wejście | Wyjście |
|---|---|---|
| Wysyłam polecenie | tap Start | `CommandResponse` lub błąd sieci |
| Stacja przyjęła polecenie, podłącz kabel | `CommandResponse: ACCEPTED` | `CommandResult` albo Session |
| Czekam na start ładowania | `CommandResult: ACCEPTED` | Session `ACTIVE` |
| Ładuje | Session `ACTIVE` | Session `COMPLETED` lub Stop |
| Nie udało się | `REJECTED`, `NOT_SUPPORTED`, `FAILED`, `EVSE_OCCUPIED`, `EVSE_INOPERATIVE`, `TIMEOUT` lub brak wyniku po `timeout` | użytkownik wybiera dalej |
| Sesja zakończona | Session `COMPLETED` | rachunek po CDR |

Okno oczekiwania = `timeout` z `CommandResponse` (sekundy), plus zapas na Session. Nie ustawiaj własnych zegarów
krótszych niż `timeout` CPO. Wynik komendy wiąż z żądaniem przez unikalny element `response_url`.

## 3. CommandResult na komunikat
| Wartość | Komunikat dla kierowcy | Akcja backendu |
|---|---|---|
| `ACCEPTED` | „Stacja przyjęła polecenie” | czekaj na Session |
| `REJECTED` | „Stacja odrzuciła polecenie, spróbuj ponownie lub wybierz inną” | log; przy powtórkach zgłoś CPO |
| `EVSE_OCCUPIED` | „Stanowisko jest zajęte” | odśwież status; zaproponuj sąsiednie EVSE |
| `EVSE_INOPERATIVE` | „Stanowisko nie działa” | oznacz w mapie nieświeże; zaproponuj alternatywę |
| `NOT_SUPPORTED` | „Ta stacja nie obsługuje startu z aplikacji. Użyj karty” | ukryj Start dla EVSE bez `REMOTE_START_STOP_CAPABLE` |
| `FAILED` | „Start się nie powiódł, nic nie pobraliśmy” | log z `message` z CPO; sprawdź Sessions |
| `TIMEOUT` | „Stacja nie odpowiedziała w czasie” | sprawdź GET Sessions przed ponownym startem |
| brak wyniku po `timeout` | jak `TIMEOUT` | jak wyżej; traktuj komendę jako nieudaną |
Komunikaty pokazuj prostym językiem, bez wartości enum. W logu trzymaj wartość oryginalną (wsparcie jej potrzebuje).

## 4. Idempotencja i ponowienia
- Nie wysyłaj drugiego `START_SESSION` na to samo EVSE, zanim nie wiesz, co się stało z pierwszym: ryzyko dwóch sesji.
- Po `TIMEOUT` lub błędzie sieci najpierw `GET` Sessions (z `date_from` bliskim startowi) i dopasuj po
  `authorization_reference` / `cdr_token`. Dopiero brak sesji pozwala na ponowienie.
- Przycisk Start blokuj do rozstrzygnięcia; jeden aktywny start na konto i EVSE.
- Jeden żądany start = jeden `authorization_reference` zapisany w backendzie i w logu, żeby wiązać sesję i CDR.
- `STOP_SESSION` wymaga `session_id`; `UNKNOWN_SESSION` oznacza, że CPO nie zna sesji (np. już zakończona): odśwież stan.

## 5. Postęp sesji
Sesja trafia do eMSP PUT-em, potem PATCH-ami; przy niepewnym stanie CPO wysyła PUT z całą sesją.
- **Wyświetlaj:** `status`, `kwh`, `start_date_time`, bieżący koszt `total_cost` (jeśli CPO go podaje), moc chwilowa
  z ostatniego `charging_periods` (okres ENERGY ÷ czas), czas postoju.
- **Nie zakładaj** równych odstępów między aktualizacjami ani ciągłości `kwh`: CPO wysyła zmiany, gdy chce.
  Pokaż „ostatnia aktualizacja o HH:MM” z `last_updated`.
- PATCH **dopisuje** `charging_periods`; po błędzie nie ponawiaj bez sprawdzenia (zdublowanie). Po stronie
  odbiorcy deduplikuj więc okresy po `start_date_time`.
- **`total_cost`** to cena CPO dla eMSP, nie cena dla kierowcy; jeśli masz marżę lub abonament, licz własną cenę
  (`dom-ev-tariffs-pricing`) i pokazuj ją jako „szacunek”. Wartość ostateczna dopiero z CDR.
- Statusy: `PENDING` (jeszcze nie ładuje), `ACTIVE`, `COMPLETED`, `INVALID` (nie będzie rozliczona; pokaż
  „sesja nierozliczana” i powiadom wsparcie), `RESERVATION`.
- Powiadomienie push o końcu ładowania (pełna bateria, limit) wyzwalaj z Session, a nie z timera.

## 6. Stop
`STOP_SESSION` kończy sesję z aplikacji (nie z kodu auta). Wynik także asynchroniczny przez `response_url`; odblokowanie
kabla zależy od stacji. Jeśli kabel pozostaje zablokowany po sesji, `UNLOCK_CONNECTOR` jest komendą operatora lub eMSP,
nie kierowcy bezpośrednio. Pokaż kierowcy, że sesja trwa (i nalicza opłatę za postój) do czasu Session `COMPLETED`.

## 7. Cena przed startem
- Źródło: taryfy wskazane w `Connector.tariff_ids` (tej samej stacji, którą kierowca wybrał). Przy wielu taryfach różnych
  typów (`TariffType`: `AD_HOC_PAYMENT`, `PROFILE_CHEAP`, `PROFILE_FAST`, `PROFILE_GREEN`, `REGULAR`) wybierz zgodną
  z kontraktem kierowcy.
- Pokaż: cenę za kWh, za minutę (np. postój), opłatę startową, minimalną opłatę, walutę, brutto/netto
  (`dom-ev-tariffs-pricing`, `.claude/skills/dom-ev-tariffs-pricing/references/cena-dla-kierowcy.md`).
- Zapisz **identyfikator taryfy i jej `last_updated` w chwili startu** razem z sesją; to dowód w sporze o cenę.
- AFIR art. 5 ust. 3–4 (baza `eu-afir`): ceny przejrzyste, porównywalne, niedyskryminujące; od 50 kW cena ad hoc
  wyrażona za kWh plus ewentualnie za minutę, pokazana przed startem. Dotyczy ceny ad hoc stacji; komunikację ceny
  kontraktowej projektuj w tym samym duchu [rekomendacja].
- Zmiana taryfy między mapą a startem: odśwież cenę przy ekranie startu i zaakceptuj ją jawnie, gdy się zmieniła.

## 8. Błędy pokazywane kierowcy
Zasada: komunikat mówi (1) co się stało, (2) czy kierowca poniósł koszt, (3) co zrobić dalej.
Odrębne przypadki do obsłużenia: brak kontraktu z CPO na tej stacji; token `BLOCKED`/`EXPIRED`/`NO_CREDIT`
(`AuthorizationInfo`); stacja offline; kabel niepodłączony; stanowisko zajęte; limit czasu; brak środków
w abonamencie przedpłaconym; konto zawieszone. Każdy błąd zapisuj z identyfikatorem żądania, wynikiem CPO i
czasem, aby wsparcie widziało go bez pytania kierowcy.
