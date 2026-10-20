# CDR: pola, okresy, podpis, korekta

Spis treści: 1. Pola i sumy · 2. charging_periods · 3. tariffs w CDR · 4. signed_data · 5. Korekta krok po kroku ·
6. Sprawdzenie spójności CDR.

Źródło: `mod_cdrs.asciidoc` OCPI 2.2.1, 2.2.1-d2, 2.3.0 (sprawdzone 2026-10-20), własnymi słowami.

## 1. Pola i sumy
| Pole | Wymagane | Znaczenie / uwaga |
|---|---|---|
| `country_code`, `party_id`, `id` | tak | CPO-właściciel i numer CDR |
| `start_date_time`, `end_date_time` | tak | start sesji (przy rezerwacji bez sesji: start rezerwacji) i jej koniec; koniec sesji może być późniejszy niż koniec ładowania (postój) |
| `session_id` | nie | pominięcie dozwolone bez modułu Sessions albo przy rezerwacji bez sesji |
| `cdr_token`, `auth_method` | tak | token startu; `auth_method`: AUTH_REQUEST, COMMAND, WHITELIST — przy kilku metodach w jednej sesji obowiązuje ostatnia |
| `authorization_reference` | nie | wartość nadana przez eMSP; przy kilku wartościach — ostatnia |
| `cdr_location`, `meter_id` | tak / nie | miejsce (tylko właściwy EVSE i Connector), identyfikator licznika |
| `currency` | tak | ISO 4217 |
| `tariffs`, `charging_periods` | nie / tak | patrz niżej |
| `total_cost` | tak | suma wszystkich kosztów sesji (Price: `excl_vat`, `incl_vat`) |
| `total_fixed_cost`, `total_energy_cost`, `total_time_cost`, `total_parking_cost`, `total_reservation_cost` | nie | składowe; parking i rezerwacja zawierają swoje składniki stałe |
| `total_energy` | tak | kWh |
| `total_time` | tak | godziny całej sesji (ładowanie + postój) |
| `total_parking_time` | nie | godziny bez przepływu energii |
| `remark`, `invoice_reference_id` | nie | uwaga tekstowa; odniesienie do faktury (do 39 znaków) |
| `credit`, `credit_reference_id` | nie | CDR kredytowy; spec uzasadnia dublet szybszym zapytaniem po fladze logicznej |
| `home_charging_compensation` | nie | CDR z ładowarki domowej kierowcy, której koszt energii ma zostać mu zrekompensowany |
| `last_updated` | tak | dla CDR to w praktyce data utworzenia |

CDR bez znanego czasu startu lub końca zwykle nie może być wysłany. Wyjątek: obie strony zgadzają się, a prawo
lokalne pozwala fakturować takie sesje — wtedy brakujący czas ma wartość `1970-1-1T00:00:00Z` (zapis wg spec).

Kontrola sum (własna reguła, nie wymóg OCPI **[założenie]**): jeśli występują składowe, ich suma powinna dawać
`total_cost` w granicach zaokrąglenia; `total_time` ≥ `total_parking_time`.

## 2. charging_periods
- CPO **musi** zacząć nowy okres w każdej chwili, która zmienia składnik ceny: np. cena energii zmienia się o 17:00
  (energia do 17:00 trafia do okresu kończącego się o 17:00) albo prąd przekracza próg (np. 32 A). Dodatkowe okresy
  „pośrednie” są dozwolone.
- Okres: `start_date_time`, lista `dimensions` (`type`, `volume`), opcjonalnie `tariff_id`.
- Typy wymiarów (CdrDimensionType): CURRENT, ENERGY, ENERGY_EXPORT, ENERGY_IMPORT, MAX_CURRENT, MIN_CURRENT,
  MAX_POWER, MIN_POWER, PARKING_TIME, POWER, RESERVATION_TIME, STATE_OF_CHARGE, TIME (część tylko dla aktualizacji
  Session). Ujemna energia lub moc = przepływ z pojazdu do sieci.
- Domyślny `step_size`: ENERGY 1 (Wh), czasy 1 s; reguły zaokrąglania sum → `dom-ev-tariffs-pricing`.

## 3. tariffs w CDR
- Lista taryf obowiązujących w sesji, w stanie **z chwili startu**; okres wskazuje swoją taryfę przez `tariff_id`.
- Gdy sesja była darmowa, lista powinna zawierać taryfę „Free of Charge” (FLAT z ceną 0).
- eMSP może liczyć własną cenę z `tariffs` i `charging_periods`; może też zweryfikować cenę CPO (kalkulator:
  `ocpi_tariff_calc.py`, opis w SKILL.md).

## 4. signed_data
- Opcjonalny blok dowodowy (np. niemiecki Eichrecht): `encoding_method` (nazwa kodowania, np. OCMF — wg tabeli
  w spec), `encoding_method_version`, `public_key` (base64), `signed_values` (≥1) i `url` dla kierowcy.
- `signed_values`: `nature` (Start, End, Intermediate), `plain_data` (tekst jawny), `signed_data` (blob base64).
- Do czego: wykazać, że energia z CDR pochodzi z podpisanych odczytów licznika. Sprawdzanie podpisu zależy od kodowania
  i klucza — jest poza OCPI; `signed_data` nie zastępuje `total_energy`, tylko go dowodzi.
- Rozjazd `total_energy` ↔ podpisane odczyty (End − Start) to mocny argument w sporze (patrz `uzgadnianie-i-spory.md`).

## 5. Korekta krok po kroku
1. Ustal powód i oryginał (`id` = `12345`). Zdecyduj, czy to zmiana kwoty, energii, taryfy czy tokenu.
2. Zbuduj CDR kredytowy: kopia oryginału, `id` nowe (np. `12345-C`; maks. 39 znaków), `credit: true`,
   `credit_reference_id: "12345"`, `total_cost` z minusem (excl i incl).
3. Wyślij go (POST). Dopiero po przyjęciu wyślij CDR poprawiony: nowe `id` (np. `12346`, maks. 36 znaków dla zwykłego),
   bez `credit` i `credit_reference_id`.
4. Zapisz u siebie powiązanie oryginał → kredytowy → nowy. Saldo okresu: oryginał + kredytowy + nowy.
5. Gdy kolejna korekta dotyczy już poprawionego CDR, kredytujesz **ostatni** CDR (`12346`), nie pierwszy.

## 6. Sprawdzenie spójności CDR (przed wysłaniem lub po odbiorze)
| Kontrola | Test |
|---|---|
| waluta | `currency` = waluta taryf i `total_cost` |
| czas | `end_date_time` ≥ `start_date_time`; `total_time` ≈ różnica czasów (godziny) |
| energia | `total_energy` ≈ suma wolumenów ENERGY z okresów |
| koszt | `total_cost` ≈ wynik kalkulatora dla `tariffs` + `charging_periods` |
| kredytowy | `credit` = true ⇔ jest `credit_reference_id`; `total_cost` ujemny; oryginał istnieje |
| identyfikator | zwykły `id` ≤ 36 znaków, kredytowy ≤ 39 |
