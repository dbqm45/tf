---
name: dom-ev-payments
description: Użyj przy płatności za ładowanie EV — terminal kartowy, preautoryzacja, OCPI Payments, zwroty i chargeback, PCI DSS, SCA, płatność ad hoc.
metadata:
  przeglad: "2027-04-20"
  katalog: "Użyj, gdy trzeba zaprojektować lub wyjaśnić płatność za ładowanie — ad hoc (terminal kartowy na stacji, QR i strona WWW, aplikacja CPO) i kontraktowa (eMSP, abonament, karta flotowa); preautoryzacja i jej zwolnienie, obciążenie końcowe, sesja przerwana; OCPI 2.3.0 Payments (Payment Terminal Provider, Terminal, Financial Advice Confirmation, authorization_reference, preauthorize_amount); przypisanie terminali do stacji i EVSE (jeden terminal na kilka EVSE, wymiana, wycofanie, tap-to-pay offline, AFIR art. 5); paragon i faktura przy płatności ad hoc; zwroty i chargeback; PCI DSS na poziomie architektury; SCA/PSD2 i AFIR opisowo. Nie do wyliczenia ceny z taryfy (dom-ev-tariffs-pricing), CDR i rozliczenia hurtowego CPO-eMSP (dom-ev-cdr-settlement), ogólnego protokołu OCPI (dom-ev-ocpi) ani UX aplikacji kierowcy."
  slowa: "płatność kartą na stacji, terminal płatniczy, terminal kartowy, preautoryzacja, blokada na karcie, zwolnienie blokady, pre-auth, capture, obciążenie końcowe, płatność ad hoc, bez umowy, QR kod płatność, strona WWW płatność, PTP, Payment Terminal Provider, Financial Advice Confirmation, eft_data, preauthorize_amount, authorization_reference, paragon, faktura ad hoc, zwrot płatności, chargeback, spór z bankiem, PCI DSS, tokenizacja karty, SCA, PSD2, 3-D Secure, AFIR płatność, karta flotowa, abonament, PSP, payment service provider, przypisanie terminala do EVSE, terminal na kilka ładowarek, wymiana terminala, tap-to-pay, terminal offline, card payment, refund, contactless, terminal activation"
---

# Płatności za ładowanie EV

Skill odpowiada na pytanie „kto, kiedy i na jakiej podstawie pobiera pieniądze od kierowcy”. Cenę sesji liczy
**dom-ev-tariffs-pricing**, CDR i rozliczenie CPO↔eMSP — **dom-ev-cdr-settlement**, ogólny protokół OCPI —
**dom-ev-ocpi**, role i przepływy pieniędzy — **dom-ev-market-roles**. Wygląd ekranów aplikacji opisuj słowami
(co kierowca widzi i potwierdza), bez projektu UI.

## Dwie ścieżki płatności
| | Ad hoc | Kontrakt |
|---|---|---|
| Kto płaci i komu | kierowca bez umowy → CPO (przez PSP) | kierowca → eMSP; CPO ← eMSP po CDR |
| Sposób | terminal kartowy, QR i strona WWW, aplikacja CPO | token RFID, aplikacja eMSP, Plug & Charge |
| Podstawa kwoty | taryfa `AD_HOC_PAYMENT` + preautoryzacja | taryfy `REGULAR`/`PROFILE_*` + CDR |
| Dowód zakupu | CPO (albo PTP, zob. niżej) | faktura eMSP |
| Ryzyko braku zapłaty | CPO (karta odrzucona po sesji) | eMSP (spór, windykacja) |

Kontrakt obejmuje trzy modele: **eMSP** (kierowca ma umowę i token), **abonament** (stała opłata + stawki
preferencyjne, ustalane w umowie eMSP↔kierowca, nie w OCPI) i **kartę flotową** (płaci firma; eMSP fakturuje flotę,
kierowca nie widzi płatności). Dla CPO to nadal sesja roamingowa z CDR — płatności kierowcy nie dotyka. Jedna firma
może pełnić obie role (CPO i eMSP); wtedy rozdziel konteksty płatności ad hoc i kontraktowej w modelu.

## Przebieg płatności ad hoc (karta)
1. **Wybór złącza i pokazanie ceny.** Kierowca wybiera EVSE; system pokazuje taryfę `AD_HOC_PAYMENT` (`tariff_alt_text`).
2. **Preautoryzacja** — blokada kwoty na karcie u PSP; wysokość z `preauthorize_amount` taryfy (OCPI 2.3.0).
3. **Autoryzacja ładowania** — po akceptacji ceny start sesji (w OCPI: `StartSession` z `authorization_reference`;
   w ścieżce bez OCPI: komenda OCPP z CSMS, zob. dom-ev-ocpp-16, dom-ev-ocpp-2x).
4. **Ładowanie** — aktualizacje sesji; limit blokady pilnuje CSMS albo dostawca płatności.
5. **Koniec** — ustalenie kwoty rzeczywistej (cena z taryfy po ostatnich danych licznika).
6. **Capture** — obciążenie karty kwotą rzeczywistą, **nie większą niż zablokowana**; reszta blokady wraca kierowcy.
7. **Dowód zakupu** — paragon lub faktura z danymi transakcji kartą.

Szczegóły stanów blokady, sesji przerwanej i czasów: `references/preautoryzacja-i-sesja.md`.

## OCPI 2.3.0 Payments w skrócie
Moduł `payments`, właściciel danych: **PTP** (Payment Terminal Provider — dostawca terminala i rozliczenia karty).
Dwa obiekty: **Terminal** (fizyczny terminal, mapowanie do `location_ids` / `evse_uids`) i **Financial Advice
Confirmation** (wynik capture u PSP z `total_costs`, `eft_data`, `capture_status_code`). Powiązanie płatności z sesją
robi `authorization_reference`, podane przez PTP w `StartSession`, a potem widoczne w Session i CDR.

| Krok | Kto | Co |
|---|---|---|
| Aktywacja | CPO → PTP | `POST …/terminals/activate` z referencją od producenta stacji (np. numer seryjny); PTP zakłada Terminal u CPO |
| Przypisanie | CPO → PTP | `PATCH` Terminal z `location_ids` i/lub `evse_uids` (suma obu zbiorów); `PUT` — dane terminala |
| Dezaktywacja | CPO → PTP | `POST …/{terminal_id}/deactivate` (uszkodzenie, zmiana adresu) |
| Cena | PTP ← CPO | pobranie konektora → `tariff_id` → taryfa z `preauthorize_amount` |
| Start | PTP → CPO | `StartSession` z `authorization_reference` |
| Koniec | CPO → PTP | CDR; `invoice_reference_id` ustawione = fakturę wystawia CPO, puste = PTP |
| Rozliczenie | PTP → CPO | `POST` Financial Advice Confirmation po capture, gdy fakturę robi CPO |

Zatrzymanie sesji w tym module: przez auto lub stację, przez `StopSession` od PTP po osiągnięciu limitu preautoryzacji, albo zatrzymanie
przez backend CPO z tego samego powodu. `InvoiceCreator` (`CPO`/`PTP`) w Terminal mówi, kto wystawia dokument;
`invoice_base_url` + `authorization_reference` daje link do faktury. `CaptureStatusCode`: `SUCCESS`,
`PARTIAL_SUCCESS`, `FAILED`. Tabele pól i punkty końcowe: `references/ocpi-payments.md`. Wysyłanie OCPI
(nagłówki, envelope, idempotencja) — dom-ev-ocpi.

## Przykład
Wejście: kierowca płaci kartą w terminalu PTP na EVSE z taryfą `AD_HOC_PAYMENT`, `preauthorize_amount` = 40 EUR.
Sesja kończy się po 12,5 kWh za 6,25 EUR.
1. PTP pobiera konektor → `tariff_id` → taryfę, pokazuje cenę, blokuje 40 EUR u PSP.
2. PTP wysyła `StartSession` z `authorization_reference` = `AR-7731`.
3. CPO zamyka sesję; CDR zawiera `authorization_reference` = `AR-7731`, `total_cost` 6,25 EUR i `invoice_reference_id`.
4. PTP wykonuje capture 6,25 EUR; blokada 33,75 EUR wraca do kierowcy.
5. PTP wysyła Financial Advice Confirmation (`authorization_reference` = `AR-7731`, `total_costs` 6,25 EUR, `eft_data`,
   `capture_status_code` = `SUCCESS`). CPO dopisuje `eft_data` do faktury z `invoice_base_url`/`AR-7731`.
Wynik: jedno `authorization_reference` łączy kartę, sesję, CDR i fakturę. Gdy `capture_status_code` = `FAILED` — sprawa
windykacyjna u CPO/PTP (kto ponosi stratę, ustala umowa z PTP), a nie korekta CDR.

## Terminal a stacja i EVSE
Terminal (fizyczny, z numerem seryjnym) jest przypisany do lokacji i/lub EVSE; **jeden terminal może obsługiwać kilka
EVSE** (słupek przy kilku złączach), a kierowca wskazuje EVSE na terminalu albo na ekranie stacji. AFIR art. 5 ust. 1 wprost
dopuszcza jeden terminal dla wielu punktów w puli ładowania (jedna lub więcej stacji w jednym miejscu).
- **Model:** `terminal_id`, `reference` (serial), PTP, status, przypisania z datą od–do; w OCPI 2.3.0 `location_ids` i
  `evse_uids` w Terminal (suma obu zbiorów), zmiana przez `PATCH`.
- **Cykl życia:** rejestracja i aktywacja u PTP → przypisanie → test płatności na każdym EVSE → eksploatacja → wymiana
  (nowy aktywuj przed dezaktywacją starego) → wycofanie. Rejestr, wymiana i decommissioning: dom-ev-asset-operations.
- **Tap-to-pay offline:** bez łączności terminala z PTP nie startuj sesji; terminal offline w trakcie sesji to limit
  `preauthorize_amount` i capture po powrocie łączności [do weryfikacji z PTP]. „Ładowanie bez płatności” to osobny,
  jawny tryb (free vend, dom-ev-session-lifecycle), nie obejście awarii.
- **Terminal przypisany do złego EVSE** = zła cena, zła preautoryzacja i obciążenie karty za cudzą sesję.
Pola, wymogi art. 5 ust. 1 (a)–(c), termin 1.01.2027 i tabela offline: `references/terminale-przypisanie.md`.

## Dowód zakupu przy płatności ad hoc
- Dokument wystawia CPO albo PTP (zależnie od `InvoiceCreator`); musi zawierać kwotę rzeczywistą z capture, nie
  zablokowaną. Dane z karty (`eft_data`) dopisujesz z Financial Advice Confirmation.
- Paragon/faktura/KSeF w Polsce, numeracja, VAT: przepisy lokalne [do weryfikacji] — CSMS tylko dostarcza dane
  (kwota netto/brutto z taryfy, `tax_included`, czas, kWh, EVSE).
- Wersja dla kierowcy bez konta: link z `authorization_reference` albo e-mail/SMS podany przy płatności (RODO:
  minimalizacja, retencja — pytanie do prawnika).

## Zwroty i spory
| Sytuacja | Postępowanie |
|---|---|
| Capture większy niż trzeba (błąd taryfy) | zwrot (refund) przez PSP/PTP, korekta dokumentu; w roamingu — CDR kredytowy to dom-ev-cdr-settlement |
| Sesja nie ruszyła, blokada została | zwolnienie preautoryzacji (void/cancel), bez capture |
| Kierowca kwestionuje u banku (chargeback) | zbierz dowody: `authorization_reference`, czas, kWh z licznika, EVSE, taryfa widziana przy starcie, potwierdzenie ceny; odpowiedź w terminie banku |
| Kłótnia o cenę | ta sama taryfa co przy starcie (zob. dom-ev-tariffs-pricing); zmiany ceny w trakcie sesji — ryzyko prawne |

Terminy chargeback i zasady schematów kartowych: u PSP [niezweryfikowane].

## PCI DSS, SCA i AFIR — na poziomie architektury
- **CSMS nie dotyka danych karty.** Numer karty (PAN), CVV, dane paska nigdy nie trafiają do CSMS, logów ani bazy.
  Terminal fizyczny szyfruje dane u siebie (PTP); strona WWW używa pól hostowanych przez PSP (hosted fields,
  przekierowanie); aplikacja — SDK PSP. CSMS widzi tylko **token** i status (autoryzacja, capture, void).
- Zakres audytu PCI DSS zależy od tego, co dotyka systemów — dąż do najmniejszego zakresu [do weryfikacji
  z kwalifikowanym oceniającym; wersje standardu i wymagania sprawdza `researcher`].
- **SCA / PSD2:** płatność inicjowana przez kierowcę wymaga silnego uwierzytelnienia (np. 3-D Secure, PIN,
  urządzenie przy terminalu) [do weryfikacji]. Późniejsze dobicie kwoty bez udziału kierowcy to osobny tryb
  (transakcja inicjowana przez sprzedawcę) — wymaga zgody i zasad PSP [do weryfikacji].
- **AFIR** (rozporządzenie UE 2023/1804, baza `eu-afir`, art. 5 ust. 1): w punktach uruchomionych od 13.04.2024 płatność
  ad hoc instrumentem szeroko używanym w UE przez co najmniej jedno z: czytnik kart, urządzenie zbliżeniowe, a poniżej
  50 kW także QR; od 1.01.2027 punkty ≥ 50 kW na TEN-T lub bezpiecznym parkingu — czytnik lub zbliżeniowo (nie sam QR).
  Wymogi nie dotyczą ładowania bez opłaty. Zakres „publicznie dostępny” i wyjątki sprawdź w tekście, nie z tego skilla.

## Pułapki
- Capture na kwotę zablokowaną „na wszelki wypadek”: pobierasz kwotę rzeczywistą.
- Brak `authorization_reference` w Session/CDR — nie da się dopasować płatności do sesji i faktury.
- Preautoryzacja po sesji: blokada bez capture wygasa u banku; kierowca widzi ją długo i zgłasza spór.
- Mylenie `AD_HOC_PAYMENT` (typ taryfy) z modułem Payments (terminal, capture): taryfa opisuje cenę i
  `preauthorize_amount`, moduł obsługuje kartę.
- Założenie, że ad hoc generuje CDR do eMSP — w ścieżce CPO↔kierowca nie ma eMSP; w module Payments CDR trafia do PTP.
- Logowanie ciała żądań płatniczych: sekrety i dane osobowe w logach.
- Retry capture bez klucza idempotencji u PSP → podwójne obciążenie.
- Zmiana kwoty `preauthorize_amount` w taryfie w trakcie sesji bez przechowania wartości z chwili startu.
- Terminal przypisany do złego EVSE albo nadal do lokacji po dodaniu EVSE bez dostępu do terminala; brak historii przypisań.

## Checklista
- [ ] Ścieżka: ad hoc czy kontrakt; kto wystawia dokument (`InvoiceCreator`, `invoice_reference_id`)
- [ ] `preauthorize_amount` ≥ realistyczny koszt do limitu; kto zatrzymuje sesję przy limicie
- [ ] Capture = kwota rzeczywista; zwolnienie reszty; obsługa sesji przerwanej i zawieszonej
- [ ] `authorization_reference` w StartSession, Session, CDR i Financial Advice Confirmation
- [ ] CSMS bez PAN/CVV; tylko token i statusy; klucz idempotencji capture/refund
- [ ] Terminal: przypisania z historią, test płatności na każdym EVSE, `capabilities` zgodne ze stanem
- [ ] Dowody pod chargeback zapisane przy sesji
- [ ] Wymogi SCA/PSD2, PCI, AFIR i podatkowe oznaczone [do weryfikacji] do sprawdzenia przez `researcher`

## Czytaj references, gdy…
| Pytanie | Plik |
|---|---|
| przypisanie terminala do stacji i EVSE, cykl życia, tap-to-pay offline, AFIR art. 5 ust. 1, pomyłka EVSE | `references/terminale-przypisanie.md` |
| stany blokady, kwota preautoryzacji, sesja przerwana, zawieszona, offline, retry | `references/preautoryzacja-i-sesja.md` |
| pola Terminal i Financial Advice Confirmation, endpointy, enumy, kolejność wywołań | `references/ocpi-payments.md` |

## Źródła
- OCPI 2.3.0, `mod_payments.asciidoc` i `mod_tariffs.asciidoc` (pole `preauthorize_amount`, `TariffType`),
  github.com/ocpi/ocpi tag v2.3.0, baza fabryki `ocpi-2.3.0`, pobrane 2026-10-20.
- OICP 2.3 (`oicp`, Hubject, CC BY-SA 4.0): w tym wydaniu tylko `PaymentOptions` (`Direct`, `Contract`, `No Payment`)
  i `Direct Payment` jako metoda uwierzytelnienia — brak modułu płatności; pobrane 2026-10-20.
- AFIR (UE) 2023/1804, art. 5 ust. 1–4, EUR-Lex, wersja skonsolidowana 08.01.2026, baza `eu-afir`, pobrane 2026-10-20.
- OCPI 2.3.0 `mod_payments` (Terminal, `location_ids`, `evse_uids`), baza `ocpi-2.3.0`, pobrane 2026-10-20.
- PSD2 i PCI DSS — wiedza ogólna [niezweryfikowane]; tryby offline terminali — [do weryfikacji] z PTP.
