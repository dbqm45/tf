---
name: dom-ev-cdr-settlement
description: Użyj przy CDR i rozliczeniu CPO↔eMSP — korekta CDR kredytowym, idempotencja odbioru, uzgadnianie CDR z sesjami i fakturą, spory, sprawdzenie kosztu kalkulatorem.
metadata:
  przeglad: 2027-04-20
  katalog: "Użyj, gdy pracujesz na CDR jako niezmiennym zapisie rozliczeniowym OCPI 2.2.1/2.3.0 — pola i sumy, charging_periods, tariffs w CDR, signed_data, kiedy CPO wysyła CDR (push, pull), CDR kredytowy i korekta (credit, credit_reference_id, nowy CDR), idempotencja odbioru po id CDR, rozliczenie hurtowe CPO↔eMSP, uzgadnianie CDR z sesjami i fakturą (rozjazdy kWh i kosztów, CDR bez sesji, sesja bez CDR), spory, fakturowanie kierowcy przez eMSP (invoice_reference_id) oraz sprawdzanie kosztu CDR kalkulatorem ocpi_tariff_calc.py. Nie do liczenia ceny z taryfy i step_size (dom-ev-tariffs-pricing), protokołu OCPI — endpointy, paginacja, uwierzytelnianie (dom-ev-ocpi), przebiegu sesji i sesji osieroconych (dom-ev-session-lifecycle) ani ról rynku (dom-ev-market-roles). Płatności kartą to osobny, przyszły temat."
  slowa: "CDR, charge detail record, CDR kredytowy, credit CDR, credit_reference_id, korekta CDR, zła kwota w CDR, poprawić CDR, rozliczenie hurtowe, settlement, reconciliation, uzgadnianie, rozjazd kWh, CDR bez sesji, sesja bez CDR, duplikat CDR, idempotencja CDR, spór o rozliczenie, dispute, faktura kierowcy, invoice_reference_id, signed_data, Eichrecht, OCMF, charging_periods, total_cost, total_energy, sprawdzić koszt CDR, ocpi_tariff_calc, rozliczenie CPO eMSP, miesięczne rozliczenie roamingu, billing roaming"
---

# CDR i rozliczenie CPO↔eMSP

CDR (Charge Detail Record) to **jedyny obiekt OCPI istotny dla rozliczenia**. Skill mówi, co CDR zawiera, jak go
korygować, jak go przyjąć bez dubli i jak uzgodnić z sesjami i fakturą. Cenę z taryfy liczy `dom-ev-tariffs-pricing`;
endpointy i paginację opisuje `dom-ev-ocpi`; powstanie CDR z sesji — `dom-ev-session-lifecycle`; role stron i obieg
pieniędzy — `dom-ev-market-roles`.

## Czytaj references, gdy…
| Plik | Kiedy |
|---|---|
| `references/cdr-pola-i-korekty.md` | potrzebujesz tabeli pól i sum CDR, zasad `charging_periods`, `signed_data`, pełnego przebiegu korekty |
| `references/uzgadnianie-i-spory.md` | budujesz uzgadnianie (CDR vs sesje vs faktura), tabelę rozjazdów, proces sporu, fakturowanie kierowcy |

## Fakty o CDR (OCPI 2.2.1, 2.2.1-d2 i 2.3.0)
- CDR opisuje **zakończoną** sesję i tworzy go CPO. Po wysłaniu do eMSP jest **niezmienny**: moduł nie ma PUT,
  PATCH ani DELETE, a zmiany „są po prostu niedozwolone”.
- Zawiera Location, EVSE, Token i **taryfy tak, jak były w chwili startu sesji** — późniejsza zmiana taryfy ani nazwy
  ulicy nie zmienia CDR.
- Wysyłka: CPO robi POST na endpoint CDR u eMSP (push) albo eMSP pobiera GET od CPO (pull; filtr po `date_from` /
  `date_to`, dla CDR liczy się tylko data utworzenia). Pull służy też do dociągnięcia CDR z czasu awarii eMSP.
- Termin wysyłki: po końcu sesji, „jak najszybciej” to dobra praktyka, ale umowa może przewidywać wysyłkę zbiorczą
  (np. raz w miesiącu). CPO nie musi wysyłać wszystkich CDR wszystkim eMSP, tylko właściwemu.
- Wersje: 2.3.0 w CDR zmienia wobec 2.2.1-d2 tylko odwołania do norm dla `evse_id` i `contract_id` (diff plików
  `mod_cdrs`). Daty wydań **[do weryfikacji]**.

## Anatomia CDR — to, co sprawdzasz najczęściej
| Grupa | Pola | Reguła |
|---|---|---|
| Klucz | `country_code`, `party_id`, `id` | `id` unikalny per `country_code`/`party_id`; do 36 znaków (do 39 dla kredytowego) |
| Powiązania | `session_id`, `cdr_token`, `auth_method`, `cdr_location` | `session_id` wolno pominąć tylko bez modułu Sessions albo przy rezerwacji bez sesji |
| Energia i czas | `total_energy` (kWh), `total_time` (h, z postojem), `total_parking_time` (h bez ładowania) | czas ładowania = `total_time` − `total_parking_time` |
| Koszt | `total_cost` (Price: `excl_vat`, `incl_vat`) + składowe `total_fixed_cost`, `total_energy_cost`, `total_time_cost`, `total_parking_cost`, `total_reservation_cost` | `total_cost` to suma wszystkich kosztów sesji; składowe opcjonalne |
| Wyliczalność | `tariffs`, `charging_periods` | wystarczają, by eMSP przeliczył koszt; spec zaleca dać eMSP dość danych do własnej ceny |
| Dowód | `signed_data` | podpisane odczyty licznika (np. Eichrecht), osobno od kosztu |
| Rozliczenie | `invoice_reference_id`, `credit`, `credit_reference_id`, `remark` | patrz niżej |

`charging_periods`: nowy okres zaczyna się, gdy zmienia się składnik taryfy lub wartość istotna dla ceny (zmiana
ceny po 17:00, prąd powyżej progu). Każdy okres ma `dimensions` (typ + `volume`) i `tariff_id`. Zachowanie `step_size`
i wybór elementu taryfy → `dom-ev-tariffs-pricing`.

## Korekta: CDR kredytowy + nowy CDR
1. Wyślij **CDR kredytowy**: `credit: true`, `credit_reference_id` = `id` korygowanego CDR, **nowe `id`** (zupełnie
   inne albo stare z dopiskiem, np. `-C`). Zawiera dane oryginału; spec wymaga, by `total_cost` miał kwoty
   **ujemne** względem oryginału.
2. Potem wyślij **nowy CDR** z poprawnymi wartościami, z kolejnym unikalnym `id`, bez pól `credit` i
   `credit_reference_id`.
3. Okres, jak daleko wstecz wolno korygować, OCPI **nie definiuje** — wynika z umowy i prawa lokalnego.
4. Znak pozostałych sum (`total_energy_cost` itd.) w kredytowym CDR spec nie rozstrzyga wprost **[do weryfikacji]**;
   ustal z partnerem, a rozliczaj po `total_cost`.

## Odbiór CDR: idempotencja
Kluczem jest trójka (`country_code`, `party_id`, `id`) CPO-nadawcy. Reguły eMSP:
- Ten sam klucz i **identyczna treść** → sukces bez drugiego skutku (bez drugiej księgi, faktury, naliczenia).
- Ten sam klucz i **inna treść** → nie nadpisuj: CDR jest niezmienny. Odrzuć i zgłoś jako anomalię w sporze
  **[założenie]** — kod odpowiedzi na duplikat ustal w umowie **[do weryfikacji]**.
- Kredytowy CDR to osobny rekord z własnym kluczem; łącz go z oryginałem przez `credit_reference_id`.
- Zapisz CDR **w całości i bez zmian** (surowy JSON) oraz własne dane obok: czas odbioru, status uzgodnienia.
- Odbiór pull + push naraz daje dublety — klucz chroni także przed tym.

## Rozliczenie hurtowe i uzgadnianie
CPO i eMSP rozliczają się zbiorczo za okres wg umowy, nie sesja po sesji. Saldo okresu per CPO i waluta =
suma `total_cost` CDR zwykłych + suma kredytowych (ujemnych). Przed zapłatą eMSP uzgadnia **trzy źródła**:
CDR, własne Sessions z OCPI i (po stronie CPO) transakcje z licznika. Tabela rozjazdów, progi i proces sporu:
`references/uzgadnianie-i-spory.md`. Najczęstsze:

| Objaw | Pierwsza hipoteza | Działanie |
|---|---|---|
| CDR bez sesji u eMSP | brak modułu Sessions, sesja zgubiona, sesja z innego kontraktu | sprawdź `session_id`, token, czas; nie płać bez wyjaśnienia |
| sesja bez CDR | CDR jeszcze nie wysłany (umowa: zbiorczo) albo sesja osierocona u CPO | po upływie terminu pull po `date_from`; potem zapytanie do CPO |
| `total_energy` ≠ ostatnia energia Session | Session to podgląd, CDR to wartość końcowa | licz CDR; różnicę wyjaśnij odczytem licznika/`signed_data` |
| `total_cost` ≠ koszt z taryfy | zły element taryfy, `step_size`, VAT, zaokrąglenie | przelicz kalkulatorem (niżej); rozbieżność → spór |

## Sprawdzanie kosztu CDR kalkulatorem
Skrypt fabryki (interfejs; powstaje w skillu `dom-ev-tariffs-pricing`):
`python3 .claude/skills/dom-ev-tariffs-pricing/scripts/ocpi_tariff_calc.py <taryfa>.json <cdr>.json --cdr <cdr>.json`
- Pierwszy plik: jedna taryfa OCPI (element z `tariffs` CDR, wyjęty do osobnego pliku **[założenie: skrypt czyta
  jeden obiekt Tariff]**). Drugi: plik okresów — CDR zawiera `charging_periods`, więc może nim być. `--cdr` porównuje
  wynik z kosztami z CDR; `--json` daje wynik maszynowy.
- Kod wyjścia: **0** zgodne lub policzone, **1** rozbieżność z CDR, **2** błąd wejścia (zły plik, brak pola).
- Kalkulator liczy `step_size` wg reguły z 2.2.1-d2/2.3.0 i oceniający restrykcje na początku okresu; sama specyfikacja
  nie podaje reguł zaokrąglania cen (zależą od przepisów lokalnych), więc różnice groszowe to temat do umowy, nie błąd.
- Przykład z taryfą, CDR i CDR kredytowym: `examples/ocpi-tariff-cdr/`.
- Kod 1 to **sygnał do rozmowy z partnerem**, nie dowód winy: sprawdź najpierw, którą taryfę wskazuje `tariff_id` w okresie.

## Fakturowanie kierowcy (po stronie eMSP)
- eMSP ma **własną** relację z kierowcą; jego cennik może różnić się od taryfy CPO. CDR dostarcza dane (dimensions),
  a nie fakturę kierowcy. OCPI nie realizuje płatności ani faktur.
- `invoice_reference_id` (opcjonalne) łączy CDR z fakturą, która zostanie wysłana później, i może grupować CDR na
  jednej fakturze. Kto je nadaje i kiedy — ustal w umowie **[do weryfikacji]**.
- Korekta po zafakturowaniu kierowcy: kredytowy CDR od CPO uruchamia po stronie eMSP dokument korygujący wg przepisów
  kraju (przepisy o fakturach **[do weryfikacji]**).
- Płatność ad hoc kartą bez eMSP nie przechodzi przez CDR do eMSP — to osobny temat płatności.

## Przykład
Wejście: CDR `12345` (CPO `BE`/`BEC`): taryfa `12` TIME 2,00 EUR/h bez VAT, VAT 10 %, `step_size` 300 s; jeden okres
`TIME` `volume` 1,973 h (118,4 min); `total_cost` 4,00 excl / 4,40 incl; `total_energy` 15,342 kWh. eMSP ma Session
tej sesji z `kwh` 15,342.
Wynik: (1) klucz (`BE`,`BEC`,`12345`) nowy → zapis i uzgodnienie; (2) kWh zgodne; (3) koszt: 118,4 min zaokrąglone w górę
do kroku 5 min = 120 min = 2 h × 2,00 = 4,00 excl, ×1,10 = 4,40 incl → zgodne (kalkulator zwraca kod 0). Gdyby CPO
policzył 1,973 h × 2,00 = 3,946, kod 1 wskazałby brak `step_size`. Korekta po stwierdzeniu błędu: CDR `12345-C`
(`credit: true`, `credit_reference_id: 12345`, `total_cost` −4,00/−4,40), potem CDR `12346` z poprawną kwotą; ponowny
POST `12345` o tej samej treści = sukces bez drugiego skutku.

## Pułapki
- **Poprawianie wysłanego CDR** (PUT/PATCH/nadpisanie w bazie eMSP): narusza niezmienność; użyj kredytowego + nowego.
- **Kredytowy CDR z tym samym `id`** co oryginał — kolizja klucza i odrzucenie jako duplikat.
- **Kredytowy bez nowego CDR:** klient zostaje bez rozliczenia sesji.
- **Dodatnie kwoty w kredytowym** — saldo rośnie zamiast maleć.
- **Idempotencja po samym `id`** bez `country_code`/`party_id`: dwóch CPO może mieć to samo `id`.
- **Płatność po `Session` zamiast po CDR** — Session to podgląd, tylko CDR rozlicza.
- **Przeliczanie starego CDR bieżącą taryfą** — CDR niesie taryfę z chwili startu sesji.
- **Pomijanie waluty i VAT:** sumy z różnych walut ani netto z brutto się nie dodają.
- **Utożsamienie rozbieżności kosztu z błędem CPO:** najpierw `tariff_id`, `step_size`, restrykcje czasu lokalnego.
- **Zapis kWh bez surowego JSON-a CDR** — w sporze nie ma czego pokazać.

## Checklista
- [ ] Klucz CDR = (`country_code`, `party_id`, `id`); duplikat identyczny = sukces, różny = anomalia.
- [ ] CDR zapisany surowo i tylko do odczytu; status uzgodnienia osobno.
- [ ] Korekta = kredytowy (`credit`, `credit_reference_id`, nowe `id`, ujemny `total_cost`) + nowy CDR.
- [ ] Uzgodnienie okresu: CDR ↔ Sessions ↔ licznik; CDR bez sesji i sesja bez CDR na liście wyjątków.
- [ ] Koszt sprawdzony kalkulatorem; kod 1 opisany w sporze z `tariff_id` i okresem.
- [ ] Saldo per CPO i waluta (zwykłe + kredytowe); faktura kierowcy powiązana przez `invoice_reference_id`.
- [ ] Zasady spoza OCPI (termin korekt, tolerancje, kod przy duplikacie) zapisane w umowie z partnerem.

## Źródła
- Specyfikacja OCPI, repozytorium github.com/ocpi/ocpi, pliki `mod_cdrs.asciidoc` z tagów `2.2.1`, `v2.2.1-d2`,
  `v2.3.0` oraz przykładowy plik CDR z katalogu przykładów specyfikacji (sprawdzone 2026-10-20; zob. fakty fazy 2a). Treść opracowana własnymi słowami.
- `.claude/skills/dom-ev-charging/references/ocpi.md` i `cykl-sesji-ladowania.md` (import 2024–2025).
- Reguły uzgadniania, progi i zachowanie przy duplikacie to praktyka autora oznaczona **[założenie]** lub
  **[do weryfikacji]**; potwierdź z umową partnera (stan: 2026-10-20).
