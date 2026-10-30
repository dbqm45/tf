---
name: tool-stripe
description: Użyj przy integracji ze Stripe — wybór API (Checkout, Payment Element, Intents), webhooki, klucze ograniczone, Billing, Connect, Tax, aktualizacja wersji API i SDK.
metadata:
  przeglad: "2027-01-21"
  katalog: "Użyj, gdy planujesz, piszesz, przeglądasz lub testujesz integrację ze Stripe — wybór API (Checkout Sessions, Payment Element, PaymentIntents, SetupIntents) i odejście od przestarzałych (Charges, Sources, Tokens, Card Element), dynamiczne metody płatności zamiast payment_method_types, realizacja zamówienia z webhooka, piaskownice i tryb testowy, klucze ograniczone (rk_), sejf sekretów, rotacja, podpis webhooka, CSP, Billing z Checkout i portalem klienta, rozliczanie zużycia, Connect (Accounts v2, typy obciążeń, prowizja platformy), Stripe Tax (rejestracje, kody podatkowe, automatic_tax), aktualizacja wersji API, SDK, Stripe.js i miejsc docelowych zdarzeń. Nie do modelu subskrypcji niezależnego od dostawcy (be-billing-subscriptions), ogólnego projektu API (be-api-design) ani PCI DSS jako programu zgodności (sec-governance-compliance)."
  slowa: "stripe, stripe checkout, checkout session, payment intent, paymentintent, setup intent, payment element, card element, payment_method_types, charges api, stripe webhook, checkout.session.completed, klucz stripe, sk_live, rk_live, restricted key, klucz ograniczony, stripe billing, customer portal, stripe connect, accounts v2, destination charges, application_fee_amount, stripe tax, automatic_tax, txcd, wersja api stripe, stripe-version, upgrade stripe, stripe sdk, stripe.js, stripe cli, piaskownica stripe"
---

# Stripe

**Rola agenta:** prowadzi integrację ze Stripe drogą, którą zaleca sam dostawca: najwyższy poziom API, który
wystarcza, realizacja zamówienia z webhooka, klucze z minimalnymi uprawnieniami i jawnie przypięta wersja API.
Model subskrypcji, stany i windykacja niezależne od dostawcy: be-billing-subscriptions.

## 1. Wersja i środowisko
- **Wersja API:** sprawdź aktualną w dokumentacji Stripe (strona „API versioning”). Migawka ze źródła z 2026-10-21:
  `2026-09-30.endive`; starsza niż miesiąc jest prawdopodobnie nieaktualna. Nie zgaduj nowszego numeru.
- **Wersję przypinasz w kodzie** (konfiguracja klienta SDK), a nie zdajesz się na domyślną wersję konta.
- **Klient SDK jako instancja** (`new Stripe(...)`, `StripeClient`); globalny klucz modułu (`stripe.api_key = …`)
  jest przestarzały we wszystkich aktualnych SDK.
- **Środowiska:** do nowej integracji osobne piaskownice (sandboxes) dla pracy lokalnej i CI zamiast wspólnego trybu
  testowego konta. Tryb testowy tylko dla istniejącej integracji, która od niego zależy.

## 2. Które API — mapa decyzji
| Budujesz | Użyj | Szczegóły |
|---|---|---|
| płatność jednorazową | Checkout Sessions (hostowany lub osadzony) | `references/platnosci.md` |
| własny formularz płatności | Checkout Sessions + Payment Element (`ui_mode: 'custom'`) | `references/platnosci.md` |
| zapis metody płatności na później | SetupIntents | `references/platnosci.md` |
| płatność bez obecności klienta, własny stan koszyka | PaymentIntents | `references/platnosci.md` |
| subskrypcje i odnowienia | Billing API + Checkout (`mode: 'subscription'`) + portal klienta | `references/billing-connect-tax.md` |
| rozliczanie za zużycie (nowa integracja) | Metronome (według Stripe); Billing Meters tylko przy istniejącym prostym użyciu | `references/billing-connect-tax.md` |
| platformę lub marketplace | Connect, Accounts v2 (`/v2/core/accounts`) | `references/billing-connect-tax.md` |
| podatek (sales tax, VAT, GST) | Stripe Tax + rejestracje | `references/billing-connect-tax.md` |
| aktualizację wersji API, SDK, Stripe.js | procedura | `references/aktualizacja.md` |

Kolejność preferencji interfejsu: Payment Links (bez kodu) → Checkout → Payment Element. Przed kodem przeczytaj
właściwy plik z `references/`.

## 3. Zasady krytyczne
- **Nie przekazuj `payment_method_types`.** Pominięcie włącza dynamiczne metody płatności (konfiguracja w panelu,
  dobór metod do klienta). Wyjątek: terminal stacjonarny (`card_present`). Ograniczenia przez
  `payment_method_configurations`, `excluded_payment_method_types` albo `allowed_payment_method_types`.
- **Webhook nie jest opcjonalny.** Realizacja zamówienia w obsłudze zdarzeń, nie na stronie sukcesu: klient może nie
  wrócić na stronę po udanej płatności. Dla Checkout obsłuż `checkout.session.completed`
  i `checkout.session.async_payment_succeeded`, realizuj, gdy `payment_status` nie jest `unpaid`;
  `checkout.session.async_payment_failed` dla porażek. Webhooki są wymagane przy subskrypcjach i metodach
  z opóźnionym potwierdzeniem.
- **Podpis webhooka** weryfikujesz przed obsługą; sekret podpisu to sekret jak klucz API. Idempotencja i kolejność
  zdarzeń: be-billing-subscriptions §5.
- **Klucz ograniczony (`rk_`) zamiast tajnego (`sk_`)**, osobny na usługę i środowisko, z minimalnymi uprawnieniami;
  klucze w sejfie sekretów platformy, nigdy w repozytorium, logach ani kodzie klienta. `references/bezpieczenstwo.md`.
- **Przestarzałe API:** nie proponuj Charges, Sources, Tokens ani Card Element; wskaż migrację (`references/platnosci.md`).
- **`automatic_tax` bez aktywnej rejestracji nie pobiera podatku i nie zwraca błędu.** Najpierw potwierdź rejestrację
  w jurysdykcji klienta (`references/billing-connect-tax.md`).

## 4. Typowe błędy w przeglądzie kodu
- Integracja „gotowa” bez obsługi webhooków albo z realizacją zamówienia na stronie powrotu.
- `payment_method_types: ['card']` „bo klient chce tylko karty”.
- Klucz `sk_live_` w kodzie, pliku `.env` w repozytorium albo w aplikacji mobilnej; brak hooka pre-commit na `sk_`/`rk_`.
- Ręczna pętla odnowień na PaymentIntents zamiast Billing; obiekt `plan` zamiast `Price`; różne plany jako ceny jednego
  produktu.
- Mapowanie zdarzeń na obiekty aplikacji przez `metadata` zamiast przez identyfikatory obiektów Stripe.
- Brak przypiętej wersji API; webhook z inną wersją API niż kod.

## 5. Dokumenty startowe Stripe
Integration Options (wybór drogi), API Tour (przegląd), Go Live Checklist (przed uruchomieniem produkcji) —
docs.stripe.com.

## Przykład
**Sytuacja:** „Sklep w Next.js, płatność kartą przez `charges.create` z tokenem z Card Element; zamówienie oznaczamy
jako opłacone na stronie `/success`.”
**Wynik (skrót):**
- Migracja na Checkout Sessions (hostowany albo osadzony), bez `payment_method_types`; Card Element → Payment Element
  tylko przy własnym formularzu.
- Webhook z weryfikacją podpisu; realizacja przy `checkout.session.completed` lub `async_payment_succeeded`
  z `payment_status` różnym od `unpaid`; strona `/success` tylko pokazuje stan.
- Klucz ograniczony z uprawnieniami do Checkout i odczytu zdarzeń, w sejfie sekretów; wersja API przypięta w kliencie.
- Testy w piaskownicy: płatność, metoda z opóźnionym potwierdzeniem, to samo zdarzenie dwa razy.

## Checklista
- [ ] wersja API przypięta w kodzie i sprawdzona w dokumentacji; klient SDK jako instancja
- [ ] najwyższy wystarczający poziom API; brak Charges, Sources, Tokens, Card Element
- [ ] brak `payment_method_types` (poza terminalem)
- [ ] webhook z podpisem; realizacja z webhooka; zdarzenia asynchroniczne obsłużone
- [ ] klucze ograniczone w sejfie, osobne na środowisko; plan rotacji i reakcji na wyciek
- [ ] podatek: rejestracje potwierdzone przed `automatic_tax`; Connect na Accounts v2

## Źródła
- Repozytorium stripe/ai, skille `stripe-best-practices` i `upgrade-stripe`, commit
  1bcd18aa0e69b0e4dad9e268b873c7e245d6da5e (2026-10-21), licencja MIT. Ranga: pierwotne (materiał dostawcy).
  Opisane własnymi słowami; nazwy parametrów, zdarzeń i wersji przepisane ze źródła.
- Stron docs.stripe.com nie czytano w tej sesji; zalecenia dostawcy podane za skillami, a nie za dokumentacją
  [niezweryfikowane względem docs.stripe.com].
