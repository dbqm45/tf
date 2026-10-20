# Composite schedule wg libocpp — reguły i przypadki brzegowe
> Recurring · 4. Jednostki i fazy · 5. Czego libocpp nie rozstrzyga

Źródło: EVerest libocpp, `doc/common/smart_charging_profiles.md` (L1-246 w `.claude/knowledge/everest-libocpp-smart-charging/doc.txt`),
`doc/v2/ocpp_201_smart_charging_in_depth.md` (L247-429), testy `test_composite_schedule.cpp` (od L430); pobrane
2026-10-20. To implementacja referencyjna (ranga W). Specyfikacja OCA nie jest w bazie.

## 1. Algorytm
- `get_valid_profiles` zostawia profile właściwego złącza i (przy trwającej transakcji) właściwego `transactionId`.
- `calculate_enhanced_composite_schedule`: (1) czas startu transakcji, (2) podział na zbiory `ChargePointMax`,
  `TxDefault`, `Tx`, (3) osobny harmonogram dla każdego zbioru w jednostce docelowej, (4) połączenie. W obrębie
  zbioru wyższy `stackLevel` ma pierwszeństwo.
- Łączenie: `TxDefault` jest limitem początkowym, `Tx` go zastępuje, a `Max` może go tylko obniżyć. Wynik nie
  przekracza `Max`.
- 2.0.1 (K08): do czterech zbiorów dochodzi `ChargingStationExternalConstraints`; `GetCompositeSchedule` liczy
  wynik dla `evseId`, a `evseId` = 0 daje oczekiwany pobór całej stacji. Nieobsługiwana jednostka i nieistniejące
  EVSE kończą się błędem (`ChargingScheduleChargingRateUnitUnsupported`, `EvseDoesNotExist`).
- Wynik zawsze zaczyna się w `start_time` i ma stałe `duration`, nawet bez profili.
- Test `ExtraSeconds`: okno 12:01:59-13:02:01 (3602 s) przy profilu `Absolute` od 12:02. Wynik: okres 0 s z limitem
  domyślnym, 32 A od 1 s, 31 A od 1801 s, 30 A od 2701 s i znów limit domyślny od 3601 s. Luki na brzegach profilu
  wypełnia więc limit domyślny.

## 2. Limit domyślny i niespójność dokumentacji
OCPP 1.6 nie dopuszcza luk w harmonogramie. Gdy w jakiejś chwili żaden profil nie działa, libocpp musi coś wpisać.

| Miejsce w źródle | Co mówi |
|---|---|
| „Default limit” | gdy limit nieznany, używany jest domyślny **48,0 A**; inny domyślny daje profil `TxDefault` o niższym `stackLevel` |
| „No valid profiles” | przykład odpowiedzi `Accepted` z jednym okresem `startPeriod` 0 i `limit` **0.0**; pusta lista okresów byłaby niepoprawna wg 7.13 spec |
| test `NoSchedulesPresent` | oczekuje `getCompositeScheduleDefaultLimitAmps().value_or(DEFAULT_LIMIT_AMPS)` — wartość z konfiguracji, a gdy jej brak, stała |

Dokumentacja jest więc wewnętrznie sprzeczna: „brak ładowania” (0 A) vs 48 A. Test sugeruje, że realne zachowanie to
konfigurowalny limit z domyślną stałą, ale źródła nie podają wartości stałej poza opisem 48 A **[do weryfikacji w
kodzie używanej wersji libocpp]**. Praktyka dla CSMS: (a) instaluj `TxDefaultProfile` z niskim `stackLevel` (np. 0)
jako jawny limit domyślny, np. 6 A albo bezpieczne 16 A; (b) w testach asercje na okresy bez źródła limitu traktuj jako
niepewne; (c) skrypt `composite_schedule.py` ma `--default-limit` (domyślnie 48; 0 = nie ładuj) właśnie dlatego.

## 3. Czas
**Relative i transakcja.** Profile `Relative` liczą się od startu transakcji, a bez niej od początku okna
(„zakłada się, że transakcja właśnie ruszyła”). Libocpp celowo nie sięga po bieżący czas, żeby testy były powtarzalne.

**validFrom / validTo (przykład z dokumentacji).** `TxDefault`, `Relative`, `stackLevel` 1: okres 0 s: 32 A,
3600 s: 6 A; `validFrom` 12:00, `validTo` 20:00 (2024-01-01).
- Pojazd wpięty o 10:00: według źródła brak ładowania do 12:00 (profil jeszcze nieważny; wynik zależy od limitu
  domyślnego z sekcji 2), od 12:00 limit 6 A, bo 32 A obowiązuje tylko przez pierwszą godzinę transakcji, a ta minęła.
- Wpięty o 19:50: 10 minut po 32 A, potem profil wygasa.

**Recurring Daily.** `startSchedule` 12:00, okresy 0 s: 32 A, 3600 s: 6 A. Pojazd wpięty 10.01 o 11:50 dostaje 10 minut
po 6 A (okres z poprzedniej doby), a od 12:00 po 32 A.

**Recurring Daily z `duration` 18000 s (5 h)** i `validFrom` 2024-02-01 12:00, `validTo` 2024-03-01 09:00:
- 10.02 o 11:50: 10 minut z poprzedniej doby — źródło opisuje to jako limit domyślny (profil trwa tylko 5 h), potem
  32 A od 12:00;
- 01.02 o 11:50: profil jeszcze nieważny, limit domyślny do 12:00, potem 32 A;
- 01.03 o 08:00: 6 A (z poprzedniej doby), a o 09:00 profil przestaje obowiązywać.
Wniosek: przy `Recurring` z `duration` krótszym niż doba luka między końcem okresu a następnym powtórzeniem
jest wypełniana limitem domyślnym. Pod takim profilem połóż `TxDefault` o niższym `stackLevel`.

## 4. Jednostki i fazy
- Harmonogram można zażądać w `A` lub `W`; libocpp przelicza `W = A × napięcie × fazy`. Gdy profile mają różną liczbę
  faz (`numberPhases` 1 i 3), osobne okresy odpowiedzi mają własne `numberPhases` (test
  `TxProfilePerEvseWithMultipleEvses_DifferentNrOfPhases`: 32 A × 3 fazy, potem 30 A × 1 faza, potem 28 A × 3 fazy).
- Testy `MixingCurrentAndPower_*` łączą sufit w amperach z `TxDefault` w watach dla stacji 1- i 3-fazowej; wynik
  zależy od liczby faz. Sprawdzaj oba warianty.
- Skrypt bierze najmniejszą podaną liczbę faz aktywnych profili okresu, domyślnie 3, i napięcie z `--voltage`.

## 5. Czego libocpp nie rozstrzyga
- Zgodności ze specyfikacją OCA w szczegółach (np. kolejność `ExternalConstraints` wobec `Max`) **[do weryfikacji w spec]**.
- Zachowania innych implementacji stacji: różnią się. Zawsze porównaj skrypt z `GetCompositeSchedule` na sprzęcie.
- ISO 15118 (K15-K17): w libocpp w rozwoju; skrypt liczy tylko pierwszy `chargingSchedule`.
