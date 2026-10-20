# Rozliczenie kierowcy i wsparcie

Spis treści: 1. Od CDR do faktury · 2. Abonamenty i plany · 3. Historia i dowody · 4. Spory · 5. Zgłoszenia wsparcia ·
6. Co pokazać w aplikacji, żeby ograniczyć zgłoszenia

Źródło: OCPI `v2.3.0` (CDR, Sessions) i skille fabryki; praktyka wsparcia to wiedza ogólna branży, w bazie nie
ma jej źródła [do weryfikacji w konkretnej organizacji].

## 1. Od CDR do faktury
```
CDR od CPO -> weryfikacja -> pozycja kierowcy (cena kontraktowa) -> faktura eMSP -> płatność kierowcy
                                    \-> rozliczenie hurtowe wobec CPO (wg zatwierdzonych CDR)
```
- Weryfikacja: koszt z taryfy w CDR (kalkulator `.claude/skills/dom-ev-tariffs-pricing/scripts/ocpi_tariff_calc.py`),
  zgodność z sesją, duplikat po `id` (idempotencja); procedura w `dom-ev-cdr-settlement`.
- CDR jest niezmienny. Błąd u CPO = CDR kredytowy (`credit`, `credit_reference_id`) i nowy CDR. U kierowcy
  odpowiada temu **nota korygująca** do wystawionej faktury, a nie edycja faktury.
- Dwie ceny: kosztu hurtowego (CPO → eMSP, z CDR) i ceny dla kierowcy (marża, abonament, rabat). Różnicę wyjaśnia
  umowa eMSP↔CPO i regulamin eMSP. Nie myl ich w raportach.
- Czas: CDR przychodzi po zakończeniu sesji, ale nie natychmiast. Aplikacja pokazuje sesję jako „w rozliczeniu”, dopóki
  nie ma CDR, a kwotę z `total_cost`/szacunku oznacza jako wstępną.
- Faktura (VAT, numeracja, KSeF w Polsce) to osobny temat prawa lokalnego; nie podawaj jej szczegółów bez źródła
  [do weryfikacji], zob. `dom-ev-regulations-pl`.

## 2. Abonamenty i plany
- Plan to polityka eMSP (opłata miesięczna, rabat na kWh, pakiet kWh), niezwiązana z OCPI. OCPI przenosi tylko
  taryfę CPO i CDR. Cenę dla kierowcy liczysz własną regułą z planu.
- Zmiana planu w trakcie okresu: proporcjonalnie albo od następnego okresu (decyzja produktu, jawna w regulaminie).
- Sesja należy do okresu według czasu **zakończenia** lub **rozpoczęcia**, jedno rozstrzygnięcie, zapisane w regulaminie
  i konsekwentnie w kodzie (sesje na granicy miesiąca).
- Płatności cykliczne, nieudana płatność i blokada konta: model płatności `dom-ev-payments`. Blokada konta z powodu
  zaległości musi skutkować `valid: false` lub odpowiedzią `NOT_ALLOWED`/`BLOCKED` w real-time (`references/konto-i-tokeny.md`).

## 3. Historia i dowody
Dla każdej sesji trzymaj: identyfikator sesji i CDR, `authorization_reference`, token, EVSE (`uid`, `evse_id`),
czasy, kWh, taryfę widzianą przy starcie, wynik komendy startu, cenę dla kierowcy i hurtową. Historia ma być
stabilna po wymianie karty (przy koncie). Retencja: prawo podatkowe i RODO [do weryfikacji].

## 4. Spory
| Powód sporu | Dowód | Rozstrzygnięcie |
|---|---|---|
| zła cena | taryfa przy starcie vs taryfa w CDR; kalkulator | jeśli CPO policzył inaczej niż taryfa: spór z CPO i CDR kredytowy; jeśli zgodnie z taryfą: wyjaśnienie kierowcy |
| kWh nie zgadza się z autem | `kwh` w CDR, `signed_data` (OCMF) | licznik w stacji jest podstawą rozliczenia; ładowarka liczy po stronie sieci, auto po stronie baterii, więc różnica strat jest normalna (`dom-ev-metering-calibration`) |
| sesja, której kierowca nie zna | token, EVSE, czas; zablokowana karta po zgubieniu | sprawdź PATCH `valid: false` i jego czas |
| podwójne obciążenie | duplikat CDR po `id`; dwie sesje (podwójny start) | idempotencja; sekcja 4 w `start-zdalny-i-sesja.md` |
| opłata za postój po zakończeniu | czas końca ładowania vs odpięcia | komunikacja przed startem; progi z taryfy |
Kierowca nie czeka na rozstrzygnięcie sporu z CPO: eMSP rozstrzyga z kierowcą, a potem z CPO (kolejność umowna).

## 5. Zgłoszenia wsparcia
| Zgłoszenie | Pytania kontrolne | Dane z platformy | Typowe przyczyny |
|---|---|---|---|
| **Nie startuje** | który krok: komenda, kabel, autoryzacja? | `CommandResult`, `CommandResponse`, Session, token (`valid`, `whitelist`), status EVSE i jego wiek | stanowisko zajęte lub offline; token zablokowany; stacja bez zdalnego startu; kabel niepodłączony; brak kontraktu z CPO |
| **Wolno ładuje** | jaka moc, jakie auto, jaki SoC? | `charging_periods` (moc chwilowa), `max_electric_power` złącza, ewentualny profil (`dom-ev-smart-charging`) | auto ogranicza prąd (SoC wysoki, zimna bateria, krzywa), współdzielona moc stacji, limit lokacji |
| **Zła cena** | co kierowca widział przed startem? | taryfa zapisana przy starcie, CDR, cena kontraktowa | zmiana taryfy, opłata za postój, step_size, różnica ad hoc i kontrakt |
| **Karta nie działa** | czy token `valid`, jakiego typu? | token, `whitelist`, odpowiedź real-time, czas ostatniego PATCH | blokada nie dotarła, karta nie wysłana do danego CPO, `NO_CREDIT`, zła strona (stacja bez RFID_READER) |
Dalsza diagnoza po stronie sieci: `dom-ev-diagnostics` (np. skrypt `.claude/skills/dom-ev-diagnostics/scripts/ocpp_log_analyze.py`
do logów OCPP). „Wolno ładuje” od strony pojazdu: `dom-ev-vehicle-battery` (krzywa, SoC, temperatura baterii, 400/800 V).
Zasada: wsparcie bierze z kokpitu sesji wszystkie dane naraz, bez pytania kierowcy o numer EVSE i godzinę.

## 6. Co pokazać w aplikacji, żeby ograniczyć zgłoszenia
- **Przed startem:** pełna cena (kWh, minuta, start, postój), wiek statusu, możliwość startu zdalnego, brak kabla.
- **W trakcie:** moc chwilowa i szacowany czas do celu (ETA: `dom-ev-vehicle-battery`), z uwagą, że moc zależy od auta
  i stanu baterii; koszt bieżący jako szacunek.
- **Przy wolnym ładowaniu:** wyjaśnienie „Twoje auto ogranicza moc przy SoC powyżej X %” zamiast milczenia (próg zależy
  od auta, nie podawaj ogólnej wartości jako faktu).
- **Po sesji:** podsumowanie (kWh, czas, składniki ceny), status „w rozliczeniu”, link do faktury po CDR.
- **Błędy:** komunikat z powodem i kosztem (`start-zdalny-i-sesja.md`, sekcja 8).
- **Karta:** status karty (aktywna, zablokowana) i data ostatniej synchronizacji; przycisk blokady w aplikacji.
- **Kontakt:** zgłoszenie z automatycznym dołączeniem identyfikatora sesji, wyniku komendy i taryfy.
