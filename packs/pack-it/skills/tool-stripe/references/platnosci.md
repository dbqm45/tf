# Płatności w Stripe: wybór API, interfejs, webhooki, migracje

## 1. Hierarchia API
- **Checkout Sessions** (`checkout.sessions.create`) — płatności z obecnym klientem, jednorazowe i subskrypcje;
  rabaty, wysyłka i adaptacyjne ceny w pakiecie. Podatek tylko z `automatic_tax` i aktywną rejestracją.
- **PaymentIntents** — płatności bez obecności klienta albo gdy stan koszyka modelujesz sam.
- **SetupIntents** — zapis metody płatności na później.
- Wyżej: Invoicing, Payment Links, API subskrypcji. Integracja korzysta tylko z tych poziomów.
- Od wersji API `2026-03-25.dahlia` Checkout przyjmuje `integration_identifier`: własną etykietę sesji do porównań
  w panelu; źródło zaleca dopisać do niej 8 losowych liter.

## 2. Interfejs płatności (od najprostszego)
1. **Payment Links** — bez kodu, proste produkty.
2. **Checkout** — formularz hostowany przez Stripe albo osadzony; wystarcza większości aplikacji.
3. **Payment Element** — osadzony komponent przy pełnej kontroli wyglądu; zasilaj go sesją Checkout
   (`ui_mode: 'custom'`), a dopiero gdy się nie da — surowym PaymentIntent.

Nie proponuj Card Element ani Payment Element w trybie tylko kart; przy Card Element wskaż migrację do Payment
Element. Dopłata za metodę płatności albo podgląd danych karty przed utworzeniem Intentu: Confirmation Tokens
(finalizacja na serwerze), a nie `createPaymentMethod` ani `createToken` ze Stripe.js.

## 3. Realizacja zamówienia z webhooka
- Klient może zapłacić i nie wrócić na stronę sukcesu (zerwane połączenie), więc logika tylko na tej stronie gubi
  zamówienia.
- Obsłuż `checkout.session.completed` i `checkout.session.async_payment_succeeded`; realizuj, gdy `payment_status`
  nie jest `unpaid`. Przy metodach z opóźnionym potwierdzeniem `completed` przychodzi przed zapłatą.
  `checkout.session.async_payment_failed` — porażka.
- Webhooki są wymagane przy subskrypcjach, metodach z opóźnionym potwierdzeniem i każdym skutku po płatności
  (dostęp, e-mail, stan magazynu, zapis zamówienia). W prototypie: zalecane od razu, wymagane przed produkcją.
- Podpis weryfikujesz przed obsługą (`references/bezpieczenstwo.md`).

## 4. Dynamiczne metody płatności
- `checkout.sessions.create`: pomiń `payment_method_types` (dynamiczny dobór to zachowanie domyślne).
- `paymentIntents.create`, `setupIntents.create`: pomiń; od wersji API 2023-08-16 dynamiczne metody są domyślne,
  na starszych `automatic_payment_methods: { enabled: true }`.
- `subscriptions.create`: pomiń `payment_settings.payment_method_types`.
- Terminal stacjonarny: `payment_method_types: ['card_present']` (w Kanadzie także `interac_present`) — jedyny
  dozwolony przypadek.
- Lista dozwolonych metod dla Intentu: `allowed_payment_method_types`; wykluczenia: `excluded_payment_method_types`;
  zestawy: `payment_method_configurations`.

## 5. Przestarzałe API i migracje
| API | Status | Zamiast |
|---|---|---|
| Charges | nie używać | Checkout Sessions albo PaymentIntents (przewodnik migracji Stripe) |
| Sources | przestarzałe | SetupIntents |
| Tokens | nieaktualne | SetupIntents albo Checkout Sessions |
| Card Element | starsze | Payment Element |

## 6. PCI DSS
Wysyłanie surowego numeru karty (PAN) z serwera (`payment_method_data`) może wymagać wykazania zgodności z PCI DSS.
Przeniesienie numerów kart od innego operatora: proces importu PAN w Stripe. Program zgodności:
sec-governance-compliance.

## Źródła
stripe/ai, plik skills/stripe-best-practices/references/payments.md, commit 1bcd18a (2026-10-21), MIT. Opisane własnymi
słowami.
