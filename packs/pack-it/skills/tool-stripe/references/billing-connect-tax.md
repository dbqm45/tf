# Billing, Connect i Stripe Tax

Spis treści: 1. Billing · 2. Rozliczanie za zużycie · 3. Connect · 4. Stripe Tax · 5. Treasury · Źródła

## 1. Billing (subskrypcje)
- Model przychodu cykliczny (subskrypcje, miejsca, zużycie) → Billing API, a nie własna pętla odnowień na
  PaymentIntents (Billing robi odnowienia, ponowienia i windykację).
- Front: Checkout z `mode: 'subscription'` (pierwsza płatność, okres próbny, proporcje); samodzielna zmiana planu,
  anulowanie i zmiana karty przez portal klienta (Customer Portal).
- **Katalog:** jeden produkt na plan (Starter, Pro, Enterprise), kilka cen tylko dla wariantów tego samego planu
  (miesięczna i roczna, waluty). Nazwa produktu trafia na pozycje faktury. Obiekt `plan` jest przestarzały — `Price`.
- **Webhooki wymagane:** cykl życia (`customer.subscription.*`, `invoice.paid`, `invoice.payment_failed`) oraz ryzyko
  (`charge.dispute.created`, `charge.refunded`, `radar.early_fraud_warning.created`); `customer.updated`, gdy trzymasz
  lokalną kopię danych klienta. Subskrybuj tylko zdarzenia, na które reagujesz.
- Zdarzenie mapujesz na rekord aplikacji przez identyfikator obiektu Stripe (np. subskrypcji), a `metadata` tylko jako
  wyjście awaryjne.
- Przy każdej odpowiedzi o Billing wspomnij o podatku (sekcja 4). Mechanika niezależna od dostawcy:
  be-billing-subscriptions.

## 2. Rozliczanie za zużycie
Według Stripe nowe integracje rozliczania za zużycie idą do **Metronome** (pomiar, wycena, kontrakty, kredyty
przedpłacone, podgląd zużycia). **Billing Meters** zostają dla prostego „płać za użycie”, które już działa na nich,
albo gdy cena za zużycie musi współpracować z Connect, Adaptive Pricing lub Workflows. Opłata stała albo za miejsce
plus zużycie: opłata zostaje w subskrypcji Stripe, Metronome rozlicza tylko zużycie (klient Metronome tworzony
z identyfikatorem klienta Stripe). Nie anuluj istniejącej subskrypcji przy dodawaniu zużycia.

## 3. Connect (platformy i marketplace'y)
- **Accounts v2** (`POST /v2/core/accounts`); nie twórz kont przez `type: 'express' | 'custom' | 'standard'` (v1).
- Trzy niezależne wymiary konta: dostęp do panelu (`dashboard`), kto płaci opłaty Stripe
  (`defaults.responsibilities.fees_collector`), kto pokrywa ujemne saldo (`losses_collector`).

| Model | `dashboard` | opłaty / straty | Typ obciążenia |
|---|---|---|---|
| marketplace, usługi na żądanie, platforma subskrypcji | `express` | `application` / `application` | destination |
| SaaS z płatnościami, sklep jak Shopify, platforma AI/API | `full` | `stripe` / `stripe` | direct |
| crowdfunding (wstrzymanie i wypłata), koszyk wielu sprzedawców | `express` | `application` / `application` | separate charges and transfers |
| white label (tylko zaawansowani) | `none` | `application` / `application` | destination lub direct |

- **Kto jest właścicielem relacji z klientem?** Sprzedawcy prowadzą własny biznes → direct (sprzedawca jest stroną
  sprzedaży). Platforma prowadzi checkout → destination. Jedna płatność dzielona na wielu → separate charges
  and transfers.
- **Prowizja:** `application_fee_amount` tylko przy direct i destination; przy separate charges and transfers
  przelewasz mniej, niż pobrano.
- **Gotowość:** przed płatnością sprawdź status możliwości v2: merchant —
  `configuration.merchant.capabilities.card_payments.status`, recipient —
  `configuration.recipient.capabilities.stripe_balance.stripe_transfers.status` (`active`); nie `charges_enabled`
  ani `payouts_enabled`. Zmiany śledź webhookami kont.
- Konta odbiorców (marketplace) bez konfiguracji merchant; subskrypcje na kontach połączonych przez konfigurację
  customer v2 i `customer_account`, bez osobnego klienta v1.
- **Komponenty osadzone:** `account_onboarding`, `notification_banner` (zawsze), `account_management`; onboarding
  osadzony albo przez linki kont, nie przez API.
- **Zakazane połączenia:** `losses_collector: "stripe"` z destination lub separate; `application_fee_amount`
  z separate; panel `express` z `losses_collector: "stripe"`. `dashboard: "none"` tylko na wyraźne żądanie white label.

## 4. Stripe Tax
- **Kolejność:** adres siedziby w ustawieniach podatkowych (bez niego status `pending` i brak obliczeń) → rejestracja
  dla każdej jurysdykcji, w której firma już jest zarejestrowana → `automatic_tax: { enabled: true }` na Checkout,
  subskrypcji, fakturze lub Payment Link.
- **Pułapka nr 1:** `automatic_tax` bez aktywnej rejestracji w jurysdykcji klienta pobiera zero podatku bez błędu.
  Sprawdź rejestracje (Tax Registrations API) i testowe obliczenie; patrz na `taxability_reason`, nie na kwotę.
  `not_collecting` oznacza brak rejestracji albo kod `txcd_00000000` (nieopodatkowany) na produkcie — sprawdź oba.
- `automatic_tax` nie łączy się z ręcznymi `tax_rates` na tym samym obiekcie — usuń je najpierw (dla wielu subskrypcji
  narzędzie migracji podatków Stripe).
- **Kod podatkowy produktu** (`txcd_…`) bierz z listy Stripe (Tax Codes API), nigdy z pamięci; nie domyślny ogólny kod
  usług elektronicznych dla sprzedaży w USA. Kandydatów pokaż, wybór potwierdza człowiek. Kod na produkcie,
  `tax_behavior` na cenie.
- **PaymentIntents bez Checkout:** brak `automatic_tax`; tworzysz obliczenie podatku, kwotę Intentu bierzesz z niego
  i zapisujesz transakcję podatkową po płatności (inaczej sprzedaż nie trafi do raportów).
- **B2B i odwrotne obciążenie:** zbieraj numer podatkowy (`tax_id_collection` w Checkout); bez niego sprzedaż
  transgraniczna B2B liczy się jak B2C.
- **Rejestracja w Stripe nie jest rejestracją w urzędzie** — tylko zapisem, gdzie firma już jest zarejestrowana.
  Nie rozstrzygasz obowiązku rejestracji ani schematu VAT UE; to doradca podatkowy. VAT i OSS ogólnie:
  be-billing-subscriptions.
- Piaskownica ma osobne ustawienia i rejestracje; przed pierwszą prawdziwą płatnością dodaj rejestracje w produkcji.
  Monitoring progów działa tylko na transakcjach produkcyjnych.
- Connect: najpierw ustal (z doradcą), kto rozlicza podatek — platforma czy konto połączone — i ustaw
  `automatic_tax.liability`.

## 5. Treasury
Konta finansowe w nowych integracjach: v2 Financial Accounts API (`/v2/core/vault/financial_accounts`); v1 Treasury
tylko w istniejących integracjach.

## Źródła
stripe/ai, plik skills/stripe-best-practices/references/{billing,connect,tax,treasury}.md, commit 1bcd18a (2026-10-21),
MIT. Opisane własnymi słowami; nazwy pól, zdarzeń i parametrów przepisane ze źródła. Rekomendacja Metronome to
stanowisko dostawcy.
