# Przypisanie taryf do EVSE i zarządzanie cenami
> Spis: 1. Hierarchia przypisań · 2. OCPI: tariff_ids · 3. Taryfa per eMSP · 4. Marże i opłaty · 5. Zmiana ceny i publikacja · 6. Audyt · 7. Taryfa zerowa B2B · 8. Źródła

Wiedza ogólna branży o procesie operatora (CPO), bez nazw firm i systemów. Pola OCPI i artykuły przepisów sprawdzone
w bazie (zob. Źródła). Policzenie ceny sesji z taryfy: SKILL.md i `scripts/ocpi_tariff_calc.py`.

## 1. Hierarchia przypisań (model własny CSMS)
OCPI nie ma hierarchii taryf: Connector niesie płaską listę `tariff_ids`. Hierarchia istnieje w systemie operatora,
a do OCPI publikujesz jej **wynik**.
| Poziom | Przykład | Kiedy wygrywa |
|---|---|---|
| Domyślna sieci | „AC publiczne”, „DC ≥ 50 kW” | gdy żaden niższy poziom nie ma przypisania |
| Lokalizacja | lotnisko, parking galerii | nadpisuje domyślną dla wszystkich EVSE lokalizacji |
| EVSE / złącze | jedno szybkie złącze droższe | nadpisuje lokalizację; najbardziej szczegółowe |
| Grupa klientów | flota B2B, pracownicy, goście hotelu | poza publicznym modelem OCPI: decyduje token/grupa w CSMS przy starcie sesji |

- Reguła: **wygrywa najbardziej szczegółowy poziom**; zapisz wynik rozwiązania (efektywna taryfa EVSE) i skąd pochodzi.
- Grupa klientów dotyczy sesji z własnym tokenem CPO. Dla roamingu (token eMSP) cenę widzi się z Locations i Tariffs, więc
  zniżka grupowa CPO nie wyrazi się w `tariff_ids` — rozlicz ją osobno albo przez typ taryfy (zob. 2).
- Zmiana przypisania wyższego poziomu przelicza efektywną taryfę wielu EVSE: pokaż podgląd („zmieni się N złączy”) przed zapisem.

## 2. OCPI: `tariff_ids` w Connector
Źródło: `mod_locations` (Connector), `mod_tariffs`, 2.2.1-d2 i 2.3.0.
- `tariff_ids` (CiString(36), 0..*) = identyfikatory **aktualnie ważnych** taryf złącza. Kilka taryf jest dozwolone, ale
  **jednocześnie aktywna może być tylko jedna taryfa danego `Tariff.type`**; taryfy tego samego typu muszą mieć
  rozłączne okresy `start_date_time`–`end_date_time`.
- Przy ładowaniu z preferencjami (smart charging) podaj po jednej taryfie na każdy możliwy `ProfileType`
  (`PROFILE_CHEAP`, `PROFILE_FAST`, `PROFILE_GREEN`, `REGULAR`) — kierowca widzi opcje i ceny.
- `AD_HOC_PAYMENT` to osobny typ: cena dla płatności terminalem/kodem (zob. dom-ev-payments).
- Usuwając taryfę (DELETE u eMSP), upewnij się, że żaden Connector jej już nie wskazuje (spec zaleca).
- Brak `type` = taryfa dla wszystkich sesji. CDR niesie taryfy **z chwili startu sesji** — nie podmieniaj ich wstecz.
Przepływ: tworzysz Tariff → przypisujesz id w Connector → wysyłasz Location (PUT/PATCH) i Tariff (PUT) do eMSP; kolejność:
taryfa najpierw, potem lokalizacja, żeby eMSP nie widział złącza ze wskazaniem na nieznaną taryfę [praktyka, nie wymóg spec].

## 3. Taryfa per eMSP / odbiorca
- W OCPI 2.2.1-d2 i 2.3.0 obiekt Tariff **nie ma pola adresata** (eMSP, grupy eMSP). Jedyny wbudowany selektor to `type`
  (profil), więc standard zakłada **jedną cenę CPO dla złącza** widoczną dla wszystkich.
- Technicznie CPO wysyła Locations i Tariffs osobnym wywołaniem do każdego eMSP, więc mógłby podać inną zawartość każdemu;
  spec tego nie opisuje i nie zakazuje [do weryfikacji w praktyce hubów i umów]. Cena kierowcy u eMSP bywa inna (marża
  eMSP, abonament) — to umowa eMSP↔kierowca, nie OCPI.
- **AFIR art. 5 ust. 3** (baza `eu-afir`): ceny w publicznie dostępnych punktach mają być rozsądne, czytelnie porównywalne,
  przejrzyste i niedyskryminujące; operator **nie dyskryminuje cenami** między użytkownikami końcowymi a dostawcami usług
  mobilności ani między dostawcami; poziom cen można różnicować **tylko, gdy różnicowanie jest proporcjonalne i obiektywnie
  uzasadnione**. Cena osobna dla jednego eMSP wymaga więc zapisanego uzasadnienia (np. wolumen, koszt obsługi) i oceny prawnej.
- Zniżki umowne dla partnera dawaj poza taryfą publiczną (rabat w rozliczeniu CPO↔eMSP, dom-ev-cdr-settlement), a nie jako
  osobną taryfę „ukrytą” dla jednego odbiorcy.

## 4. Marże i opłaty
| Składnik | Wymiar OCPI | Uwagi |
|---|---|---|
| Opłata startowa / za sesję | `FLAT` | jednorazowa; AFIR ust. 4 (<50 kW) wymienia „cenę za sesję” w kolejności: kWh, minuta, sesja, inne |
| Cena energii | `ENERGY` | koszt energii + marża CPO; marża jest wielkością wewnętrzną, kierowca widzi cenę |
| Opłata za czas ładowania | `TIME` | rzadziej przy DC; patrz `step_size` |
| Opłata za zajęcie (idle fee) | `PARKING_TIME` | AFIR ust. 4: przy punktach ≥ 50 kW opłata za zajęcie wyrażona jako cena za minutę, obok ceny za kWh |

- **Marża na kWh** = cena sprzedaży − koszt energii − koszty zmienne na kWh. Trzymaj ją w modelu własnym obok taryfy; liczenie
  progu rentowności: `dom-ev-business-economics` (`station_economics.py`). Zmiana ceny energii od dostawcy nie zmienia
  taryfy sama — wymaga decyzji i publikacji.
- **Idle fee i karencja:** OCPI `min_duration` w restrykcjach liczy czas **od początku sesji**, nie od końca ładowania, więc „15 minut
  postoju za darmo, potem opłata” nie jest wyrażalne dokładnie; opisz karencję w `tariff_alt_text` albo przybliż krokiem
  `step_size` [do weryfikacji]. Wyłącz opłatę za zajęcie w godzinach, gdy parking jest bezpłatny (restrykcja czasowa).
- Opłaty eMSP (roaming, abonament) nie należą do taryfy CPO; AFIR ust. 5 wymaga od eMSP pokazania kierowcy przed sesją
  wszystkich składników, w tym kosztów e-roamingu.

## 5. Zmiana ceny i jej publikacja
1. **Przygotuj nową taryfę** z nowym `id`, z `start_date_time` w przyszłości; stara dostaje `end_date_time` = start nowej.
2. **Wskaż obie w `tariff_ids`** na czas przejścia (dozwolone, bo okresy są rozłączne) albo podmień przypisanie w chwili startu.
3. **Opublikuj z wyprzedzeniem** do eMSP (Tariff PUT, Location) i do własnych kanałów (aplikacja, ekran, dane otwarte).
4. **Nie zmieniaj ceny trwających sesji.** OCPI mówi wprost: zmiana taryfy w trakcie sesji nie jest wymagana, w wielu krajach
   prawo konsumenckie jej zabrania, a kierowca akceptuje taryfę z chwili startu. USA: 23 CFR 680.116(a)(2) — cena w chwili startu
   nie może się zmienić w trakcie sesji (baza `us-nevi`); wymaga też wyświetlenia ceny przed rozpoczęciem transakcji
   w $/kWh (a)(1) oraz jasnego pokazania struktury opłat (a)(3).
5. **AFIR (UE):** art. 5 ust. 4 wymaga pokazania ceny ad hoc (kWh, ewentualnie opłata za minutę) na stacji **przed startem**
   sesji; art. 20 ust. 2 wlicza *ad hoc price* do danych dynamicznych udostępnianych bezpłatnie przez API. Jawnego zakazu
   zmiany ceny w trakcie sesji w art. 5 **nie znalazłem** — zamrożenie na sesję wynika z OCPI i prawa konsumenckiego
   [do weryfikacji w prawie krajowym].
6. **Po publikacji sprawdź** spójność: wylosuj kilka EVSE, porównaj cenę w CSMS, w Locations u eMSP i na terminalu/ekranie.

## 6. Audyt zmian cen
Każda zmiana przypisania lub taryfy zostawia wpis: **kto, kiedy, co (przed→po), dlaczego, kto zatwierdził, od kiedy obowiązuje**,
zakres (liczba EVSE). Wpisy niemodyfikowalne (dopisywane). Wersje taryf nie są usuwane, dopóki istnieją sesje i CDR, które
na nie wskazują. Cztery oczy przy zmianie na wielu EVSE (zmiana ceny masowa = ryzyko błędu i sporów). Dowód dla sporu o cenę:
taryfa z chwili startu, jej wersja i znacznik czasu publikacji.

## 7. Taryfa zerowa (B2B, goście, pracownicy)
- Dla własnych tokenów (flota, pracownicy): taryfa z jednym elementem `FLAT` 0,00 przypisana **grupie klientów** w CSMS,
  a nie złączu publicznemu — inaczej obniżysz cenę wszystkim. Kierowca spoza grupy nadal widzi cenę publiczną.
- Zero w taryfie ≠ brak sesji: powstaje sesja i CDR/raport o kosztach 0 (energia nadal kosztuje CPO i trafia do
  rozliczeń wewnętrznych, centrów kosztów). Zasady B2B, zwrot za prąd i darmowe ładowanie: `dom-ev-fleet-charging`.
- Sesje bez autoryzacji (free vend) to osobny tryb po stronie stacji: `dom-ev-session-lifecycle`.
- AFIR art. 5 ust. 3: darmowe ładowanie wybranej grupy musi mieć obiektywne uzasadnienie, jeśli punkt jest publicznie dostępny
  [do weryfikacji z prawnikiem].

## 8. Źródła
- OCPI 2.2.1-d2 i 2.3.0, `mod_locations.asciidoc` (Connector `tariff_ids`) i `mod_tariffs.asciidoc` (Tariff `type`,
  `start_date_time`, `end_date_time`, noty o zmianie taryfy w sesji, DELETE), `mod_cdrs.asciidoc` (taryfy z chwili startu),
  github.com/ocpi/ocpi tagi v2.2.1-d2 i v2.3.0, bazy `ocpi-2.2.1-d2`, `ocpi-2.3.0`, pobrane 2026-10-20.
- AFIR (UE) 2023/1804, art. 5 ust. 3–5, art. 20 ust. 2, EUR-Lex, wersja skonsolidowana 08.01.2026, baza `eu-afir`, pobrane 2026-10-20.
- 23 CFR 680.116(a), baza `us-nevi`, pobrane 2026-10-20.
- Hierarchia przypisań, audyt i kolejność publikacji: praktyka branży [założenie].
