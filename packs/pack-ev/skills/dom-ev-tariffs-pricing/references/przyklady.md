# Przykłady z liczbami
> 5. Ad hoc · 6. Podatek w USA · 7. CDR z krokiem · 8. Jak użyć w testach · 9. Wejście kalkulatora

Wszystkie liczby z `mod_tariffs.asciidoc` (tagi `v2.2.1-d2` / `v2.3.0`) i `examples/*.json`, sprawdzone 2026-10-20;
przeliczenia własne oznaczono. Kwoty w EUR, o ile nie napisano inaczej.

## 1. Taryfa złożona (`tariff_4_complex`, DE)
Elementy w kolejności: (1) `FLAT` 2,50, VAT 15%; (2) `TIME` 1,00/h, VAT 20%, krok 900 s, `max_current: 32`;
(3) `TIME` 2,00/h, VAT 20%, krok 600 s, `min_current: 32`, pon.–pt.; (4) `TIME` 1,25/h, VAT 20%, krok 600 s,
`min_current: 32`, sob.–niedz.; (5) `PARKING_TIME` 5,00/h, VAT 10%, krok 300 s, 09:00–18:00, pon.–pt.; (6) `PARKING_TIME` 6,00/h,
VAT 10%, krok 300 s, sobota 10:00–17:00.

**Poniedziałek, plug-in 09:30, 165 min ładowania prądem 16 A, 42 min postoju.**
| Wymiar | Ilość | Cena | Netto | VAT | Brutto |
|---|---|---|---|---|---|
| `FLAT` | 1 | 2,50 | 2,50 | 15% | 2,875 |
| `TIME` (element 2) | 165 min | 1,00/h | 2,75 | 20% | 3,30 |
| `PARKING_TIME` (element 5) | 42 → 45 min | 5,00/h | 3,75 | 10% | 4,125 |
| Razem | | | **9,00** | | **10,30** |

Pasuje do specyfikacji. Postój zaokrąglony krokiem 300 s; ładowanie dokładne, bo po nim jest postój.

**Sobota, plug-in 13:30, 114 min ładowania prądem 43 A, 71 min postoju.** Specyfikacja podaje 12,28 netto i 13,861 brutto
z ładowaniem 2,28 EUR. Z JSON wynika inaczej [moje przeliczenie]: element 4 daje 114 min × 1,25/h = **2,375** (ładowanie nie
jest zaokrąglane), więc netto 2,50 + 2,375 + 7,50 = **12,375**, brutto 2,875 + 2,85 + 8,25 = **13,975**. Postój 71 → 75 min
po 6,00/h = 7,50 zgadza się ze spec. Liczba 2,28 odpowiada stawce 1,20/h, więc wygląda na błąd w przykładzie.
Wniosek: nie kopiuj liczb ze spec do testów bez przeliczenia.

## 2. Limity cen (`tariff_6`, `tariff_12`)
- `max_price` 10,00 netto / 11,00 brutto; `FLAT` 0,50 (VAT 20%) + `ENERGY` 0,25/kWh (VAT 10%).
  - 50 kWh: bez limitu 0,50 + 12,50 = 13,00 netto (brutto 0,60 + 13,75 = 14,35); limit ścina do **10,00 / 11,00**.
  - 30 kWh: 0,50 + 7,50 = 8,00 netto, brutto 0,60 + 8,25 = **8,85**, limit nie działa.
- `min_price` 0,50 netto / 0,55 brutto, `ENERGY` 0,25/kWh (VAT 10%): 20 kWh = 5,00 / 5,50; poniżej 2 kWh płacisz 0,50 / 0,55.
  To nie jest opłata startowa: dopłata zachodzi tylko, gdy suma jest niższa niż minimum.
- Limit sprawdzasz osobno netto i brutto; w 2.3.0 pola `before_taxes` i `after_taxes` (to drugie opcjonalne).

## 3. Restrykcje mocy i czasu
- `max_power`: 0,20/kWh poniżej 16 kW, 0,35/kWh od 16 do 32 kW, 0,50/kWh bez restrykcji (element domyślny na końcu).
  Sesja: 1 kWh przy 6 kW, 40 kWh przy 48 kW, 0,5 kWh przy 4 kW daje 0,20 + 20,00 + 0,10 = **20,30** netto.
  Ostatnia pozycja jest tania, bo moc w tej chwili spadła do 4 kW — restrykcja dotyczy chwili, nie sesji.
- `max_duration`: pierwsze 30 min za darmo, 0,25/kWh po 30 min, 0,40/kWh po 60 min. Sesja 40 min, 5 kWh w pierwszych 30 min
  i 1,2 kWh w następnych 10 min: **0,30** (1,2 × 0,25). Okresy muszą być rozdzielone w chwili 30. minuty.

## 4. Prosty czas i postój
- `TIME` 2,00/h, VAT 10%, krok 60 s, 2,5 h: 5,00 netto / 5,50 brutto. Postoju nie ma, bo nie ma składnika `PARKING_TIME`.
- `TIME` 3,00/h (VAT 10%, krok 60 s) + `PARKING_TIME` 5,00/h (VAT 20%, krok 300 s); 150 min ładowania, 42 min postoju:
  ładowanie 7,50, postój 45 min = 3,75, razem **11,25** netto; brutto 8,25 + 4,50 = **12,75**.

## 5. Ad hoc (`tariff_2_alt_text`)
`TIME` 1,90/h, VAT 5,2%, krok 300 s, `type` = `AD_HOC_PAYMENT`, 2,5 h: 4,75 netto / 5,00 brutto (4,997 przed zaokrągleniem).
Dla kierowcy ważniejszy jest tekst w `tariff_alt_text`, bo eMSP nie bierze udziału. Zasady niewyrażalne w OCPI (inna
opłata za debet i kredyt) zapisz tekstem i rozlicz rabatem w rozliczeniu.

## 6. Podatek w USA (2.3.0)
`TIME` 2,00/h, `tax_included` = `NO`, brak `vat`, 2,5 h: 5,00 plus podatki wg lokalnych przepisów (kwota podatku dochodzi
z zewnątrz). Wersja z `tax_included` = `YES` i ceną 2,10/h: 5,25 zawiera wszystkie należne podatki. W obu przypadkach
`vat` zostaje puste, bo CPO zwykle nie zna stawki z góry.

## 7. CDR z krokiem (`cdr_example`, BE, EUR)
Jedna taryfa: `TIME` 2,00/h, VAT 10%, krok 300 s. Jeden okres, `TIME` = 1,973 h = 7102,8 s. Krok 300 s: 7102,8 → 7200 s = 2,0 h.
Koszt 2,0 × 2,00 = **4,00 netto / 4,40 brutto** — dokładnie `total_cost` i `total_time_cost` z CDR. Gdyby ktoś liczył bez kroku:
1,973 × 2,00 = 3,946 netto, czyli rozbieżność 0,054 większa niż tolerancja 0,01.

## 8. Jak użyć w testach kalkulatora
Przypadki ze zgodnymi liczbami: sekcje 1 (poniedziałek), 2, 3, 4, 5, 7 i przykłady A, B z SKILL.md (`tariff_14`). Przypadki
ze specyfikacją niezgodną z JSON (sobota w sekcji 1, przykład #3 d2) testuj liczbami z przeliczenia, nie ze spec, i
opisz to w komentarzu testu. Przypadek brzegowy: dokładnie 32 A w `tariff_4_complex` (element 2 wyłączny, 3 włączny) i
dokładnie 17:00 w `tariff_14` (koniec elementu 1 wyłączny, początek elementu 2 włączny [założenie]).

## 9. Wejście kalkulatora dla przykładu A (`tariff_14`, plug-in 16:55 czasu lokalnego)
Lokacja w Niemczech, 2026-10-20 (czas letni, UTC+2), więc 16:55 lokalnie to 14:55Z. Wywołanie
`ocpi_tariff_calc.py <taryfa.json> <okresy.json> --tz Europe/Berlin` z plikiem okresów:

```json
{"start_date_time": "2026-10-20T14:55:00Z", "end_date_time": "2026-10-20T15:07:00Z",
 "charging_periods": [
  {"start_date_time": "2026-10-20T14:55:00Z", "dimensions": [{"type": "TIME", "volume": 0.0833333}], "tariff_id": "22"},
  {"start_date_time": "2026-10-20T15:00:00Z", "dimensions": [{"type": "TIME", "volume": 0.0833333}], "tariff_id": "22"},
  {"start_date_time": "2026-10-20T15:05:00Z", "dimensions": [{"type": "PARKING_TIME", "volume": 0.0333333}], "tariff_id": "22"}]}
```

Wynik (uruchomione 2026-10-20): `total_time_cost` 0,3, `total_parking_cost` 0,25, koszt sesji 0,55; kod wyjścia 0. Okres o
15:00Z (17:00 lokalnie) trafia do elementu 2 (krok 900 s). Bez `--tz` ten sam plik policzy godziny jako UTC i wybierze
inne elementy. Przykład B (35 min ładowania od 14:35Z, dwa okresy 25 + 10 min) daje 1,3.


## Kalkulator: opcje i wynik (przeniesione z SKILL.md)
`scripts/ocpi_tariff_calc.py <taryfa.json> <okresy.json> [--cdr <cdr.json>]
[--json] [--tz <IANA>] [--tolerance <kwota>]` liczy cenę sesji z taryfy OCPI 2.2.1 dla `charging_periods`. Sieć: brak.
- `--tz <IANA>`: strefa lokacji (np. `Europe/Warsaw`), domyślnie UTC. **Bez niej restrykcje czasowe liczą się w UTC**
  i okno 22:00–06:00 przesuwa się o 1–2 godziny.
- `<okresy.json>`: obiekt z `start_date_time`, `end_date_time` i `charging_periods` (np. sam CDR); `tariff` to JSON taryfy.
- Wynik: rozbicie na okresy i wymiary oraz koszty jak w CDR: `total_cost`, `total_energy_cost`, `total_time_cost`,
  `total_parking_cost`, `total_fixed_cost`. `--json` daje to samo maszynowo.
- `--cdr`: porównanie z kosztami z CDR; `--tolerance` (domyślnie 0.01) to dopuszczalna różnica kwot.
- Kod wyjścia: 0 zgodne lub policzone, 1 rozbieżność z CDR, 2 błąd wejścia.
- Stosuje regułę `step_size` z d2/2.3.0 i sprawdza restrykcje na początku okresu, więc okresy muszą być podzielone przy
  każdej zmianie elementu. Przykładowe wejście: `references/przyklady.md`, sekcja 9.
- Przykład: `examples/ocpi-tariff-cdr/` (taryfa, CDR, CDR kredytowy).

