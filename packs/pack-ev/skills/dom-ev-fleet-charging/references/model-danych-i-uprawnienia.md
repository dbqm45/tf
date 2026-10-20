# Model danych floty i uprawnienia tokenu

Spis: 1. Encje · 2. Przypisania z okresem · 3. Uprawnienia do lokalizacji (OCPI, OCPP) · 4. Raport · 5. Przykład

## 1. Encje
```
Organizacja (płatnik, umowa)
  └─ CentrumKosztów (budżet, właściciel)
       └─ Kierowca (osoba; dane osobowe)
            └─ Token (nośnik: RFID, APP_USER, kod gościa)
Auto (VIN, tablica, typ złącza, przypisane do centrum kosztów)
Polityka (lokalizacje, godziny, limity) ─ przypisana do organizacji, centrum, grupy tokenów
```
| Encja | Klucz | Uwaga |
|---|---|---|
| Organizacja | własny `org_id` | strona umowy; fakturowanie zbiorcze |
| Centrum kosztów | `cost_center_id` + `org_id` | nadrzędne dla auta **i** kierowcy; jedno auto = jedno centrum w danym okresie |
| Kierowca | `driver_id` | osoba może zmienić centrum; usunięcie = anonimizacja po retencji, nie kasowanie sesji |
| Token | (`uid`, `type`) unikalna u wydawcy | `group_id` łączy karty jednej organizacji (OCPI; w OCPP 1.x `parentId` ≤ 20 znaków) |
| Auto | `vehicle_id` (VIN w osobnym, chronionym polu) | tablica rejestracyjna to dana osobowa kierowcy w kontekście floty |

## 2. Przypisania z okresem
Trzy tabele łączące, każda z `valid_from`, `valid_to` (puste = bezterminowo) i regułą „brak nakładania w obrębie
jednego klucza”:
- `token_driver` — kto trzyma token (karta zgubiona → koniec okresu, nowa karta → nowy wiersz);
- `driver_vehicle` — kto jeździ jakim autem (auta pool: wielu kierowców, rozłączne okresy; albo brak, wtedy koszt idzie
  na auto z tokenu auta);
- `vehicle_cost_center` — do którego centrum liczysz koszt auta.

Raport łączy sesję z wierszami obowiązującymi w chwili **startu sesji**. Edycja wstecz tworzy korektę przypisania z
adnotacją, a nie nadpisanie — dowód dla księgowości.

## 3. Uprawnienia tokenu do lokalizacji
**OCPI (roaming, tokeny eMSP):** pole `whitelist` tokenu (`ALWAYS`, `ALLOWED`, `ALLOWED_OFFLINE`, `NEVER`) mówi,
**czy CPO może autoryzować lokalnie z kopii**, a nie gdzie token działa. Gdzie działa, rozstrzyga eMSP w odpowiedzi
na `POST authorize`: `AuthorizationInfo.allowed` = `ALLOWED`, `NOT_ALLOWED` (token ważny, ale nie na tej lokalizacji),
`BLOCKED`, `EXPIRED`, `NO_CREDIT`; zapytanie zawiera opcjonalne `LocationReferences` (lokalizacja i EVSE).
Wniosek: polityka flotowa „tylko te lokalizacje” wymaga **real-time authorization** (`whitelist` = `NEVER` albo `ALLOWED`),
a przy `ALWAYS` CPO przepuści token wszędzie. Brak `LocationReferences` w zapytaniu → eMSP nie ma jak ocenić lokalizacji
(kod OCPI 2002).

**Własna sieć CPO (karty firmowe, goście, B2B) w OCPP:**
| Wersja | Mechanizm |
|---|---|
| 1.6 | `Authorize` → CSMS decyduje wg tokenu i stacji (CSMS zna `chargePointId`); Local Authorization List i cache offline; `parentIdTag` grupuje karty |
| 2.0.1 / 2.1 | `AuthorizeResponse.idTokenInfo`: `status`, `cacheExpiryDateTime`, `evseId` (token tylko na wybranych EVSE stacji), `groupIdToken`, `chargingPriority` |

Reguły praktyczne: uprawnienie do **lokalizacji** trzymaj w CSMS jako tabelę `token_group → location` (lub grupa
lokalizacji), a do **EVSE** w stacji przez `evseId`; `cacheExpiryDateTime` ustaw krótko dla tokenów gości, żeby cache
nie przedłużał dostępu; offline użyj białej listy lokalnej tylko dla stałych uprawnionych (pracownicy), nie dla gości.
Autoryzacja tokenu ≠ prawo do darmowej ceny: cena wynika z taryfy przypisanej grupie (dom-ev-tariffs-pricing).

## 4. Raport
Minimalne kolumny: `session_id`, `cdr_id`, start/koniec (UTC i lokalny), `location_id`, `evse_id`, kWh, koszt
netto/brutto, waluta, `auth_method` (np. `WHITELIST`, `AUTH_REQUEST`), `token`, `driver_id`, `vehicle_id`,
`cost_center_id`, źródło ładowania (publiczne, depo, dom, biuro). Agregaty: per auto, kierowca, centrum, miesiąc;
kolumna „do wyjaśnienia” dla sesji bez przypisania (token nieznany, okres nieobjęty). Koszt bierz z CDR (sesje
roamingowe) albo z własnej taryfy (sieć własna); kontrola spójności CDR — dom-ev-cdr-settlement.

## 5. Przykład
Token `RFID-77` w `token_driver` od 2026-03-01 do 2026-09-30 → kierowca `D12`; `driver_vehicle` D12 → auto `V4` od
2026-06-01; `vehicle_cost_center` V4 → „Sprzedaż” od 2026-01-01. Sesja z 2026-08-10: koszt idzie na D12, V4, „Sprzedaż”.
Sesja z 2026-10-05 tym samym tokenem trafia do „do wyjaśnienia” (token po okresie ważności).
