# Specyfikacja taryf OCPI — pola i różnice wersji
> 6. Interfejsy modułu · 7. Źródła

## 1. Wersje
Tagi w repozytorium OCPI: `2.2.1` (wydanie pierwotne), `v2.2.1-d2` (wydanie poprawione), `v2.3.0`. Daty wydań: [do weryfikacji].

| Zmiana | 2.2.1 → 2.2.1-d2 | 2.2.1-d2 → 2.3.0 |
|---|---|---|
| Dokumentacja Tariffs i `step_size` | przepisana, poprawione przykłady | bez zmian reguły; dopisana uwaga o OCPI 3.0 |
| Zaokrąglanie cen | notatka „OCPI nie definiuje” | jw. |
| `min_price`, `max_price` | typ Price (`excl_vat`, `incl_vat`) | typ `PriceLimit` (`before_taxes` wymagane, `after_taxes` opcjonalne) |
| Podatki | `vat` per składnik, `price` bez VAT | dodane `tax_included` (wymagane), `price` zależy od niego |
| Terminal płatniczy | brak | `preauthorize_amount` |

Wniosek praktyczny: dla CDR od partnera ustal, w której wersji i edycji jest napisany. Sama „2.2.1” nie wystarcza —
przykłady w tekście 2.2.1 pierwotnego liczą `step_size` inaczej niż d2.

## 2. Tariff
| Pole | Uwaga |
|---|---|
| `country_code`, `party_id` | CPO będący właścicielem; `id` unikalne w platformie CPO (do 36 znaków) |
| `currency` | ISO 4217, trzy znaki |
| `type` | `TariffType`; brak = ważna dla wszystkich sesji |
| `tariff_alt_text` | lista `DisplayText` (wiele języków); przy `elements` tylko informacje dodatkowe |
| `tariff_alt_url` | strona z objaśnieniem; użyteczna przy cenach zależnych od rynku |
| `min_price`, `max_price` | patrz sekcja 4 SKILL.md; oba poziomy (netto i brutto) obowiązują łącznie |
| `elements` | co najmniej jeden `TariffElement`; kolejność ma znaczenie |
| `start_date_time`, `end_date_time` | okno ważności w UTC; do przygotowania nowej taryfy z wyprzedzeniem |
| `energy_mix` | opcjonalne dane o energii |
| `last_updated` | do filtrowania `date_from`/`date_to` w GET |

Zmiana taryfy w trakcie sesji: zwyczajowo taryfa obowiązuje do końca trwającej sesji, ale OCPI tego nie wymaga; w wielu
krajach prawo konsumenckie zabrania zmiany ceny w trakcie sesji (uwaga w specyfikacji).

## 3. PriceComponent i wymiary
| Pole | Znaczenie |
|---|---|
| `type` | `ENERGY`, `FLAT`, `PARKING_TIME`, `TIME` |
| `price` | cena jednostkowa: 2.2.1 bez VAT; 2.3.0 z lub bez podatku wg `tax_included` |
| `vat` | % podatku dla tego wymiaru; brak pola = brak VAT; `0.0` = VAT 0% (rozróżnienie wprost w d2) |
| `step_size` | wielokrotność mnożnika wymiaru: `ENERGY` 1 Wh, `TIME` i `PARKING_TIME` 1 s |

`TIME` bywa też używany z restrykcją `reservation` do ceny czasu rezerwacji. Przy rezerwacji z `RESERVATION` i
`RESERVATION_EXPIRES` oba z `TIME`, czas wygasłej rezerwacji liczy się z elementu `RESERVATION_EXPIRES`.

## 4. TariffRestrictions
Pola jak w tabeli w SKILL.md, plus reguły:
- Wszystkie ustawione pola łączą się przez AND.
- Restrykcje nie czynią elementu (nie)ważnym dla całej sesji, tylko dla chwili.
- `min_current`/`max_current`, `min_power`/`max_power`: wartość chwilowa. Element jest aktywny, gdy prąd lub moc w tej
  chwili spełnia warunek, i przestaje być, gdy warunek przestaje być prawdziwy. Prąd jest sumą po fazach.
- `min_duration`/`max_duration`: czas trwania sesji od startu (sekundy); `max_duration` wyłączne.
- `day_of_week` jest listą; brak pola = każdy dzień [założenie].
- Dla okna przez północ (`end_time < start_time`) specyfikacja w sprawdzonym tekście nie rozstrzyga, do którego dnia
  tygodnia należy część po północy [niezweryfikowane] — jeśli to istotne, rozbij okno na dwa elementy.
- Granice `start_time`/`end_time`: tekst spec mówi „valid from”/„valid until”; wyłączność końca przyjmujemy jak przy
  datach i progach [założenie]. Sprawdź na danych partnera, gdy wynik zależy od minuty granicy.

## 5. TariffType
| Wartość | Kiedy |
|---|---|
| `AD_HOC_PAYMENT` | płatność ad hoc na stacji (karta, terminal) |
| `REGULAR` | RFID bez preferencji albo preferencja `REGULAR` |
| `PROFILE_CHEAP`, `PROFILE_FAST`, `PROFILE_GREEN` | gdy kierowca wybrał odpowiedni profil w preferencjach ładowania |

Konektor może mieć wiele taryf; dla każdego wspieranego profilu CPO musi podać taryfę. Przy przejściu między dwiema
taryfami w trakcie sesji `step_size` nie jest brany pod uwagę.

## 6. Interfejsy modułu
Interfejs Sender (CPO): tylko GET listy z filtrami `date_from` (włącznie), `date_to` (wyłącznie), `offset`, `limit`.
Receiver (eMSP): GET, PUT, DELETE pod `{tariffs_endpoint_url}/{country_code}/{party_id}/{tariff_id}`. Przed DELETE
upewnij się, że taryfa nie występuje w `tariff_ids` żadnego konektora. Szczegóły transportu i paginacji:
dom-ev-ocpi.

## 7. Źródła
`mod_tariffs.asciidoc` i `mod_cdrs.asciidoc` w tagach `2.2.1`, `v2.2.1-d2`, `v2.3.0` (github.com/ocpi/ocpi, sprawdzone
2026-10-20); `changelog.asciidoc` z 2.3.0.
