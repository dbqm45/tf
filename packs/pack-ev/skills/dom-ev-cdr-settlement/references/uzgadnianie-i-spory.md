# Uzgadnianie, spory i fakturowanie kierowcy

Spis treści: 1. Trzy źródła · 2. Procedura okresu · 3. Tabela rozjazdów · 4. Spór · 5. Faktura kierowcy ·
6. Model danych uzgadniania.

Zasady spoza OCPI (progi, terminy, kody odpowiedzi) to **[założenie]** — zapisz je w umowie z partnerem.

## 1. Trzy źródła
| Źródło | Strona | Rola w uzgadnianiu |
|---|---|---|
| Transakcja i odczyty licznika | CPO | prawda o energii (`dom-ev-session-lifecycle`) |
| Session (OCPI) | oba | podgląd w trakcie; stan końcowy bywa niepełny |
| CDR | oba | rekord rozliczeniowy; podstawa płatności |
| Faktura / nota zbiorcza | CPO→eMSP lub wg umowy | dokument księgowy za okres; powinna sumować się do CDR |

Zasada: płaci się za **CDR**, nie za Session. Session i licznik służą do wyjaśniania rozbieżności.

## 2. Procedura okresu (eMSP, miesięcznie lub wg umowy)
1. Zamknij okno: wszystkie CDR z `end_date_time` w okresie; pull po `date_from`/`date_to` uzupełnia braki po awarii.
2. Dla każdego CDR sprawdź klucz (idempotencja) i spójność (`cdr-pola-i-korekty.md`, pkt 6).
3. Dopasuj CDR do Session po `session_id`, a gdy go brak — po tokenie, EVSE i czasie.
4. Policz koszt kalkulatorem; kod 1 = pozycja do wyjaśnienia.
5. Zbuduj listę wyjątków (tabela niżej), wyślij partnerowi.
6. Zsumuj CDR zwykłe i kredytowe per CPO i waluta; porównaj z fakturą zbiorczą.
7. Zapłać pozycje bezsporne; sporne wstrzymaj za zgodą umowy.

## 3. Tabela rozjazdów
| Rozjazd | Typowe przyczyny | Co sprawdzić | Skutek |
|---|---|---|---|
| CDR bez sesji | eMSP nie dostał Session (moduł wyłączony, utracone PUT); inny `session_id`; sesja z innego kontraktu | `session_id`, token, EVSE, czas; czy CPO wysyła Sessions | wyjaśnić przed zapłatą |
| sesja bez CDR | CDR zbiorczo później; sesja osierocona u CPO; CDR odrzucony przez eMSP | termin z umowy, pull po `date_from`, log odrzuceń | czekać do terminu, potem zapytanie |
| Duplikat CDR | push + pull; ponowienie po timeout | klucz (`country_code`, `party_id`, `id`) | bez skutku, nie liczyć dwa razy |
| ten sam `id`, inna treść | błąd CPO (nadpisał rekord) | surowy JSON pierwszego CDR | anomalia; kredytowy + nowy |
| `total_energy` ≠ Session `kwh` | Session = ostatni podgląd; zaokrąglenia; brak ostatniego update | `signed_data`, odczyty Start/End | wiążący jest CDR; duża różnica → spór |
| `total_energy` ≠ suma ENERGY z okresów | okresy niepełne | wolumeny w `charging_periods` | spór o dane |
| `total_cost` ≠ kalkulator | zły `tariff_id`, `step_size`, restrykcja czasu lokalnego, VAT, zaokrąglenie | taryfa z chwili startu; strefa czasowa lokacji | różnica groszowa → umowa; większa → spór |
| kredytowy bez oryginału | oryginał nie dotarł | `credit_reference_id` | dociągnąć oryginał, nie księgować samego minusu |
| waluta inna niż w umowie | błąd konfiguracji | `currency` | spór/odrzucenie wg umowy |
| suma CDR ≠ faktura zbiorcza | pominięte kredytowe, VAT, opłaty huba | rozbicie faktury na CDR | korekta faktury |

Tolerancje (np. dopuszczalna różnica kWh lub groszy) ustalają strony; domyślnie nie milcz o różnicy, tylko
zapisz ją i jej decyzję **[założenie]**.

## 4. Spór
1. Zgłoś pozycję z dowodem: `id` CDR, `session_id`, wartość deklarowana vs obliczona, plik wyniku kalkulatora
   (`--json`), odczyty `signed_data`, taryfa z CDR.
2. Strona CPO weryfikuje u siebie: transakcję i odczyty licznika, taryfę w chwili startu, konfigurację.
3. Rozstrzygnięcie: (a) CDR poprawny → pozycja wraca do płatności; (b) błąd → CDR kredytowy + nowy CDR;
   (c) wątpliwość co do energii → dowód z licznika (Eichrecht/legalizacja, jeśli dotyczy).
4. Kwoty bezsporne płać w terminie; sporne rozlicz po decyzji.
5. Korekta idzie zawsze nowymi rekordami; nie ma edycji historii po żadnej stronie.

## 5. Faktura kierowcy (eMSP)
- Wejście: CDR (dimensions, `total_energy`, `total_time`, czasy) i **własny cennik** kontraktu kierowcy; może
  różnić się od taryfy CPO (marża, abonament, pakiety).
- `invoice_reference_id` łączy CDR z fakturą wysłaną później i może grupować CDR na jednej fakturze; nadawca wartości
  — umowa **[do weryfikacji]**.
- Zbiorcza faktura miesięczna kierowcy: wiele CDR → jedna pozycja per sesja z energią, czasem i cenami.
- Kredytowy CDR po zafakturowaniu: dokument korygujący dla kierowcy wg przepisów kraju **[do weryfikacji]**;
  dla flot — faktura na flotę, tokeny jak zwykle.
- Ładowanie ad hoc kartą płatniczą bez eMSP nie przechodzi tą ścieżką (płatności ad hoc: osobny temat, AFIR).

## 6. Model danych uzgadniania
| Tabela | Kolumny kluczowe |
|---|---|
| `cdr_received` | (`country_code`, `party_id`, `id`) unikalny; `raw_json`; `received_at`; `credit_reference_id`; `status` (nowy, uzgodniony, sporny, zapłacony) |
| `cdr_check` | klucz CDR; `calc_total_excl`, `calc_total_incl`; `exit_code` (0/1/2); `checked_at` |
| `reconciliation_item` | klucz CDR; typ rozjazdu z tabeli 3; decyzja; autor; data |
| `settlement_period` | CPO; waluta; okres; suma zwykłych; suma kredytowych; saldo; faktura zbiorcza |
