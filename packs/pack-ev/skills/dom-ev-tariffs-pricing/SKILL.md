---
name: dom-ev-tariffs-pricing
description: Użyj przy cenie sesji ładowania EV i taryfach OCPI — elementy, restrykcje, step_size, VAT i podatki, ad hoc vs kontrakt, zaokrąglanie, kalkulator.
metadata:
  przeglad: "2027-04-20"
  katalog: "Użyj, gdy trzeba zdefiniować, wyjaśnić albo przeliczyć cenę sesji ładowania z taryfy OCPI 2.2.1 i 2.3.0 — Tariff, TariffElement, PriceComponent, wymiary ENERGY, TIME, PARKING_TIME, FLAT, restrykcje (włącznie i wyłącznie, czas lokalny lokacji), kolejność elementów i element domyślny, step_size, VAT per składnik, tax_included i podatki w USA, min_price i max_price, TariffType, tariff_alt_text, taryfa ad hoc a kontraktowa, netto i brutto, waluta, ceny dynamiczne i komunikacja ceny kierowcy, zaokrąglanie, kalkulator ocpi_tariff_calc.py. Przypisanie taryf do EVSE i lokalizacji, `tariff_ids`, marże i opłaty, zmiana i publikacja ceny, audyt, taryfa zerowa. Nie do CDR, jego korekt i uzgodnień rozliczeń (dom-ev-cdr-settlement) ani protokołu OCPI — moduły, credentials, wersje (dom-ev-ocpi)."
  slowa: "taryfa OCPI, tariff, TariffElement, PriceComponent, restrykcje taryfy, TariffRestrictions, step_size, krok rozliczeniowy, cena za kWh, cena za minutę, opłata za postój, parking time, opłata startowa, flat fee, min_price, max_price, VAT, netto brutto, tax_included, podatek w USA, sales tax, taryfa ad hoc, AD_HOC_PAYMENT, tariff_alt_text, cena dynamiczna, dynamic pricing, cena dla kierowcy, zaokrąglanie ceny, rounding, ile kosztuje sesja, policz koszt sesji, zły koszt w CDR, okno nocne, taryfa weekendowa, kalkulator taryf, ocpi_tariff_calc, price calculation, idle fee, przypisanie taryfy do EVSE, tariff_ids, taryfa dla eMSP, marża na kWh, zmiana ceny, audyt cen, darmowe ładowanie B2B, hierarchia taryf"
---

# Taryfy OCPI i cena sesji

Skill odpowiada na pytanie „ile powinna kosztować ta sesja i dlaczego”. CDR i jego korekty to
dom-ev-cdr-settlement, protokół OCPI to dom-ev-ocpi. Taryfa jest własnością CPO; cenę kierowcy może jeszcze zmienić eMSP.

## Procedura: policz cenę sesji
1. **Ustal wersję i taryfę.** 2.2.1, 2.2.1-d2 (wydanie poprawione) albo 2.3.0 — liczą się różnice w
   `references/specyfikacja-taryf.md`. Taryfa jest w obiekcie Tariff albo w polu `tariffs` CDR; waluta w `currency`.
2. **Ustal strefę.** Restrykcje czasowe i daty są w czasie lokalnym wg `Location.time_zone` (strefa IANA), a znaczniki
   okresów w CDR są w UTC.
3. **Podziel sesję na okresy** (`charging_periods`): nowy okres zaczyna się, gdy zmienia się aktywny element
   (godzina, dzień, próg prądu lub mocy). Bez takiego podziału nie da się policzyć ceny z CDR.
4. **Wybierz składnik osobno dla każdego wymiaru** (reguła „pierwszy pasujący”, niżej).
5. **Zsumuj ilości per wymiar** i zastosuj `step_size` (raz na sesję, niżej).
6. **Cena = ilość × cena jednostkowa**, VAT osobno dla każdego składnika, potem `min_price` / `max_price`.
7. **Zaokrąglij wg przepisów lub umowy** (OCPI tego nie definiuje) i **porównaj z CDR** (`--cdr`, tolerancja 0,01).

## Model taryfy
| Obiekt | Co robi |
|---|---|
| **Tariff** | `country_code`, `party_id`, `id`, `currency`, `elements`, opcjonalnie `type`, `tariff_alt_text`, `tariff_alt_url`, `min_price`, `max_price`, `start_date_time`, `end_date_time`, `energy_mix` |
| **TariffElement** | grupa składników z wspólnymi restrykcjami (`price_components` + `restrictions`) |
| **PriceComponent** | `type` (wymiar), `price`, `vat` (%), `step_size` |
| **TariffRestrictions** | kiedy element jest aktywny; warunki łączą się przez AND |

| Wymiar | Jednostka ceny | Mnożnik `step_size` |
|---|---|---|
| `ENERGY` | za kWh | 1 Wh |
| `TIME` | za godzinę ładowania | 1 s |
| `PARKING_TIME` | za godzinę bez ładowania (auto podłączone) | 1 s |
| `FLAT` | jednorazowo (opłata startowa) | brak kroku |

Taryfa darmowa = jeden element bez restrykcji z `FLAT` 0.00. Element z `reservation`: koszt rezerwacji (`FLAT`, `TIME`).

## Który element obowiązuje
- Dla **każdego wymiaru** obowiązuje **pierwszy** (od góry listy `elements`) element, który ma ten wymiar i którego
  restrykcje w danej chwili pasują. Kolejność elementów zmienia cenę.
- W jednej chwili działa jeden składnik na wymiar, ale różne wymiary mogą pochodzić z różnych elementów.
- Brak pasującego elementu dla wymiaru = ten wymiar kosztuje 0. Dlatego **na końcu listy dodaj element domyślny bez
  restrykcji** dla każdego wymiaru, który ma kosztować zawsze.
- Przy dokładnie 32 A pasuje element z `min_current: 32`, nie z `max_current: 32` (`max` wyłączne, `min` włączne).

## Restrykcje: włącznie czy wyłącznie
| Pole | Granica | Uwaga |
|---|---|---|
| `start_time`, `end_time` | początek włącznie, koniec wyłącznie [założenie z `end_date`/`max_*`; spec nie mówi tego wprost] | `HH:MM`, czas lokalny; `end_time < start_time` = przez północ; koniec doby to `00:00` |
| `start_date` / `end_date` | włącznie / wyłącznie | data lokalna `YYYY-MM-DD` |
| `min_kwh` / `max_kwh` | włącznie / wyłącznie | energia skumulowana w sesji |
| `min_current` / `max_current` | `>=` / `<` | A, suma po fazach; chwilowa wartość, nie cała sesja |
| `min_power` / `max_power` | `>=` / `<` | kW; jw. |
| `min_duration` / `max_duration` | włącznie / wyłącznie | s od początku sesji |
| `day_of_week` | lista dni | `MONDAY`…`SUNDAY` |
| `reservation` | `RESERVATION`, `RESERVATION_EXPIRES` | element kosztów rezerwacji |

Restrykcje opisują **chwilę w sesji**, nie całą sesję; wszystkie ustawione pola muszą pasować jednocześnie.

## step_size
- Zaokrągla ilość **w górę do wielokrotności** kroku, ale **raz na sesję**: osobno dla `ENERGY` i wspólnie dla
  `TIME` + `PARKING_TIME` (nie osobno dla każdego okresu).
- Nie stosuje się przy przejściu między elementami tego samego wymiaru ani przy przejściu z `TIME` na `PARKING_TIME`
  (ładowanie liczy się wtedy dokładnie, krok zaokrągla postój).
- Liczy się `step_size` **ostatniego użytego** składnika; nadwyżka z zaokrąglenia ląduje w **ostatnim okresie** tego
  wymiaru, nie rozkłada się proporcjonalnie.
- **Sprzeczność w specyfikacji:** przykład „zmiana elementu #1” daje w 2.2.1 0,383 EUR, a w d2 i 2.3.0 0,55 EUR; obowiązuje
  **reguła z d2/2.3.0**, kalkulator też (szczegóły: `references/step-size-i-zaokraglanie.md`).
- 2.3.0 zaleca `step_size = 1` (OCPI 3.0 nie ma pola); prawo lokalne może ograniczać duże kroki.

## VAT, netto i brutto, waluta
- `price` w 2.2.1 jest **bez VAT**, `vat` to stawka w % **per składnik**. Brak pola `vat` = brak VAT (to nie to samo co
  `0.0`). Brutto liczysz dla każdego składnika osobno, nie jedną stawką od sumy (flat 15%, czas 20%, postój 10% w jednej
  taryfie).
- `min_price` i `max_price` działają **na obu poziomach**: suma netto i suma brutto nie mogą wyjść poza limit.
- **2.3.0 (Ameryka Północna):** podatek zwykle nieznany CPO z góry, więc `vat` zostaje puste, a pole `tax_included`
  (`YES`, `NO`, `N/A`) mówi, czy `price` zawiera podatek. W 2.3.0 limity to `PriceLimit` (`before_taxes`, `after_taxes`).
- Jedna waluta na taryfę i CDR (ISO 4217); przeliczania walut OCPI nie opisuje [założenie].

## Ad hoc a kontrakt
Ad hoc (karta, terminal, QR): taryfa `AD_HOC_PAYMENT`, CPO rozlicza się z kierowcą, **nie ma CDR do eMSP**. Kontrakt (token
eMSP): `REGULAR` lub `PROFILE_CHEAP`/`PROFILE_FAST`/`PROFILE_GREEN`, eMSP fakturuje kierowcę, CPO rozlicza się po CDR. Tabela
porównawcza i cena CPO a eMSP: `references/cena-dla-kierowcy.md`. Brak `type` = taryfa dla wszystkich sesji; profil wybiera
kierowca. W 2.3.0 `preauthorize_amount` mówi dostawcy terminala, ile zablokować (dom-ev-payments).

`tariff_alt_text` obok `elements` zawiera **tylko informacje dodatkowe**, bez powtarzania cen (eMSP może dodać opłaty).
Zasady, których model nie wyrazi (np. inna opłata dla debetu i kredytu), opisz tekstem i rozlicz rabatem w CDR.

## Przypisanie taryf do EVSE i zmiana ceny
- **Hierarchia (model własny CSMS):** domyślna sieci → lokalizacja → EVSE/złącze → grupa klientów; wygrywa najbardziej
  szczegółowy poziom. OCPI widzi tylko wynik: `Connector.tariff_ids` (kilka taryf, ale jednocześnie jedna na `type`;
  taryfy tego samego typu mają rozłączne `start_date_time`–`end_date_time`).
- **Per eMSP:** Tariff w OCPI 2.2.1-d2/2.3.0 nie ma pola adresata, jedynym selektorem jest `type`. AFIR art. 5 ust. 3 zakazuje
  dyskryminacji cenami między eMSP; różnicowanie tylko proporcjonalne i obiektywnie uzasadnione [do weryfikacji prawnie].
- **Zmiana ceny:** nowa taryfa z `start_date_time`, stara z `end_date_time`, publikacja z wyprzedzeniem, trwające sesje bez
  zmiany (OCPI: kierowca akceptuje taryfę z chwili startu; NEVI 23 CFR 680.116(a)(2): cena ze startu nie zmienia się w sesji).
  AFIR art. 5 ust. 4: cena ad hoc pokazana przed startem; zakazu zmiany w trakcie sesji w art. 5 nie znalazłem.
- **Marża i opłaty** (start `FLAT`, `ENERGY`, idle fee `PARKING_TIME`, AFIR: opłata za zajęcie jako cena za minutę przy ≥ 50 kW),
  **audyt zmian** (kto, kiedy, przed→po, powód, zatwierdzenie) i **taryfa zerowa B2B** (dom-ev-fleet-charging): `references/przypisanie-i-zarzadzanie.md`.
- Cen zmiennych w czasie rzeczywistym OCPI nie ma (`tariff_alt_url`); co pokazać kierowcy: `references/cena-dla-kierowcy.md`.

## Zaokrąglanie
OCPI **świadomie nie definiuje** reguł zaokrąglania cen (prawo, umowy, waluta). Ustal i zapisz poziom (składnik, okres, suma),
tryb (połowa w górę, bankowe) i liczbę miejsc. Licz na `Decimal`/`BigDecimal`, nigdy na `float`. Rozjazd o grosz między dwiema
implementacjami to **zwykle różnica zaokrąglenia**, nie błąd taryfy — stąd tolerancja przy porównaniu z CDR.

## Kalkulator `ocpi_tariff_calc.py`
`scripts/ocpi_tariff_calc.py <taryfa.json> <okresy.json> [--cdr <cdr.json>] [--json] [--tz <IANA>] [--tolerance <kwota>]`
liczy cenę sesji z taryfy OCPI 2.2.1 dla `charging_periods`. Sieć: brak. **Zawsze podaj `--tz`** (np. `Europe/Warsaw`): bez niej
restrykcje czasowe liczą się w UTC i okno 22:00–06:00 przesuwa się o 1–2 godziny. Kod wyjścia: 0 zgodne, 1 rozbieżność z CDR,
2 błąd wejścia. Opcje, format wejścia i wyniku: `references/przyklady.md` (sekcja 9); przykład: `examples/ocpi-tariff-cdr/`.

## Przykład
Taryfa `tariff_14_step_size` (DE, EUR, bez `vat`, więc same kwoty netto): element 1 (00:00–17:00) `TIME` 1,20/h krok
1800 s i `PARKING_TIME` 1,00/h krok 900 s; element 2 (17:00–20:00) `TIME` 2,40/h krok 900 s i `PARKING_TIME` 1,00/h krok 900 s;
element 3 (20:00–00:00) tylko `TIME` 2,40/h krok 900 s.

**A. Plug-in 16:55, ładowanie 10 min, potem 2 min postoju.**
1. Okresy: 16:55–17:00 `TIME` (element 1), 17:00–17:05 `TIME` (element 2), 17:05–17:07 `PARKING_TIME` (element 2).
2. Ładowanie nie jest zaokrąglane, bo po nim jest postój: 5 min × 1,20/h = 0,10 i 5 min × 2,40/h = 0,20.
3. Postój 2 min, krok ostatniego składnika 900 s: do 15 min × 1,00/h = 0,25.
4. `total_time_cost` 0,30, `total_parking_cost` 0,25, `total_cost` **0,55**. (Wersja 2.2.1 pierwotna dawała 0,383.)

**B. Plug-in 16:35, 35 min ładowania, bez postoju.**
1. Okresy: 16:35–17:00 (25 min, element 1) i 17:00–17:10 (10 min, element 2).
2. Po ładowaniu nie ma postoju, więc krok zaokrągla sumę 35 min, z krokiem ostatniego składnika (900 s): 35 → **45 min**.
3. Nadwyżka 10 min idzie do ostatniego okresu: 25 min × 1,20/h = 0,50 i 20 min × 2,40/h = 0,80, razem **1,30**.

Więcej (VAT per składnik, `max_price`, `max_power`): `references/przyklady.md`.

## Pułapki
- **Cena z jednego elementu na sesję:** restrykcje i wybór elementu dotyczą chwili i wymiaru, nie sesji.
- **`step_size` per okres** zamiast raz na sesję — zawyża cenę przy każdej zmianie elementu.
- **UTC w oknach godzinowych:** „po 22:00” to czas lokalny lokacji; doby ze zmianą czasu mają 23 lub 25 godzin.
- **Brak elementu domyślnego:** wymiar spoza restrykcji kosztuje 0 — do pierwszej reklamacji.
- **Jedna stawka VAT od sumy**; `vat` puste potraktowane jak 0%; `float` w kwotach; CDR porównany bez tolerancji.
- **Kopiowanie liczb z przykładów spec** bez przeliczenia: wersje się różnią.
- **Opłaty eMSP w taryfie CPO**, ceny w `tariff_alt_text` powielające `elements`, zmiana taryfy w sesji.

## Checklista
- [ ] Wersja specyfikacji i edycja (2.2.1, d2, 2.3.0) zapisane; reguła `step_size` jawna
- [ ] Strefa lokacji (IANA) ustalona i podana kalkulatorowi (`--tz`)
- [ ] Dla każdego wymiaru jest element domyślny bez restrykcji (lub świadomie darmowy)
- [ ] VAT per składnik; `tax_included` ustawione w 2.3.0; `min_price` i `max_price` sprawdzone netto i brutto
- [ ] Zaokrąglanie (poziom, tryb, miejsca) opisane i liczone na `Decimal`
- [ ] Cena widoczna dla kierowcy przed startem (AFIR art. 5 ust. 4, NEVI 680.116(a)); trwające sesje bez zmiany ceny
- [ ] Przypisania: efektywna taryfa EVSE znana, `tariff_ids` bez nakładających się okresów tego samego typu, wpis audytowy
- [ ] Wynik porównany z CDR (`--cdr`, kod wyjścia 0) albo rozbieżność wyjaśniona

## Czytaj references, gdy…
| Pytanie | Plik |
|---|---|
| pola obiektów, enumy, różnice 2.2.1 / d2 / 2.3.0, `tax_included`, `PriceLimit` | `references/specyfikacja-taryf.md` |
| reguła `step_size`, sprzeczność przykładów, zaokrąglanie, `Decimal` | `references/step-size-i-zaokraglanie.md` |
| dłuższe przykłady z liczbami (VAT per składnik, limity cen, moc, czas, CDR) | `references/przyklady.md` |
| ad hoc, ceny dynamiczne, komunikacja ceny, USA | `references/cena-dla-kierowcy.md` |
| hierarchia przypisań, `tariff_ids`, taryfa per eMSP, marże, publikacja i audyt zmian, taryfa zerowa B2B | `references/przypisanie-i-zarzadzanie.md` |

## Źródła
- github.com/ocpi/ocpi: `mod_tariffs`, `mod_cdrs`, `tariff_*.json` w tagach `2.2.1`, `v2.2.1-d2`, `v2.3.0`
  (sprawdzone 2026-10-20; daty wydań [do weryfikacji]); przeliczenia A i B własne, z JSON `tariff_14_step_size`.
- AFIR (UE) 2023/1804 art. 5 ust. 3–5, art. 20 (`eu-afir`, 08.01.2026), 23 CFR 680.116(a) (`us-nevi`), OCPI `mod_locations`
  (`tariff_ids`) i `mod_tariffs` (v2.2.1-d2, v2.3.0) — pobrane 2026-10-20; szczegóły w `references/przypisanie-i-zarzadzanie.md`.
- `.claude/skills/dom-ev-charging/references/ocpi.md` (import 2024–2025, §7 AFIR — [do weryfikacji]).
