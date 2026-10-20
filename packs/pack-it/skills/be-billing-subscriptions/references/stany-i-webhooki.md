# Stany subskrypcji, webhooki, idempotencja, VAT — fakty

Fakty sprawdzone przez agenta `researcher` 2026-10-18. Strony źródłowe nie zostały otwarte z sesji w chmurze
(WebFetch ENOTFOUND, proxy 403), więc werdykty opierają się na streszczeniach wyszukiwarki z oficjalnych domen —
oznaczenie [wtórne]. Przykładem jest Stripe; u innych dostawców nazwy i reguły są inne — sprawdź ich dokumentację.

## Stripe — fakty
| Fakt | Źródło | Status |
|---|---|---|
| Statusy subskrypcji: `trialing`, `active`, `past_due`, `unpaid`, `canceled`, `incomplete`, `incomplete_expired`, `paused` (`paused` m.in. po końcu okresu próbnego bez metody płatności). | docs.stripe.com/api/subscriptions/object | [wtórne; lista nie widziana w całości] |
| Proporcjonalne rozliczenie zmiany planu: domyślnie `create_prorations` (pozycje na następnej fakturze); `always_invoice` wystawia fakturę od razu; `none` wyłącza dla danego żądania. | docs.stripe.com/billing/subscriptions/prorations; docs.stripe.com/api/subscriptions/update | [wtórne] |
| Webhooki: kolejność zdarzeń nie jest gwarantowana, możliwe duplikaty (deduplikacja po id zdarzenia), podpis w nagłówku `Stripe-Signature`; odpowiedź inna niż 2xx powoduje ponowienie. | docs.stripe.com/webhooks; docs.stripe.com/events/how-events-work | [wtórne] |
| Smart Retries ponawia nieudane płatności; zalecane ustawienie: 8 prób w ciągu 2 tygodni, konfigurowalne. | docs.stripe.com/billing/revenue-recovery/smart-retries | [wtórne] |
| Nagłówek `Idempotency-Key`, maks. 255 znaków; API v1 przechowuje klucze co najmniej 24 h, API v2 — okno 30 dni. | docs.stripe.com/api/idempotent_requests | [wtórne] |

## Mapowanie stanów na dostęp (szablon do decyzji biznesu)
| Stan | Znaczenie | Dostęp (propozycja) |
|---|---|---|
| okres próbny | przed pierwszą płatnością | pełny |
| aktywna | opłacona | pełny |
| zaległa | płatność nie przeszła, trwają ponowienia | pełny + baner (okres łaski) |
| niezapłacona | ponowienia wyczerpane, subskrypcja trwa | tylko odczyt i eksport |
| wstrzymana | np. koniec próby bez karty | tylko odczyt i eksport |
| niekompletna / wygasła niekompletna | pierwsza płatność nie przeszła | brak (konto bez planu) |
| anulowana | koniec | brak; dane wg retencji i prawa do eksportu |

## Pieniądze i VAT
| Fakt | Źródło | Status |
|---|---|---|
| Od 1.07.2021 jeden unijny próg 10 000 EUR (sprzedaż towarów na odległość i usług TBE łącznie) dla dostawcy z jednego państwa UE; powyżej progu VAT kraju konsumenta, rozliczenie przez OSS. Dla usług TBE próg istniał już od 1.01.2019. | taxation-customs.ec.europa.eu/online-sellers_en; vat-one-stop-shop.ec.europa.eu/one-stop-shop_en | [wtórne; do potwierdzenia przez księgowość] |
| Miejsca po przecinku: JPY 0, KWD 3, BHD 3 (CLDR `supplementalData.xml`, `<fractions>`; listy SIX nie sprawdzono). Kwota jako liczba całkowita w najmniejszej jednostce to praktyka, nie zapis normy. | github.com/unicode-org/cldr, `common/supplemental/supplementalData.xml` (main, dostęp 2026-10-20) | potwierdzone w CLDR |

Fakty prawne i podatkowe (KSeF, prawa konsumenta, odstąpienie) są poza zakresem fabryki — notatki
w `.claude/skills/arch-eu-product-law/references/poza-zakresem-fabryki.md`; przed wdrożeniem sprawdź
w źródłach pierwotnych (EUR-Lex, ISAP, strony administracji skarbowej) albo z księgowością.

## Webhook — szkic obsługi
1. Odczyt surowego ciała → weryfikacja podpisu i tolerancji czasu → 400 przy błędzie.
2. `INSERT … ON CONFLICT (event_id) DO NOTHING` do tabeli zdarzeń → 2xx.
3. Worker (inbox): w jednej transakcji efekt + oznaczenie zdarzenia jako obsłużonego; przy wątpliwej kolejności
   pobiera aktualny obiekt z API dostawcy i uzgadnia stan.
