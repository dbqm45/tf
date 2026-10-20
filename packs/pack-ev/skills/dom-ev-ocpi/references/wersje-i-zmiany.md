# Wersje OCPI i zmiany 2.2.1 → 2.3.0

Spis treści: 1. Tagi i wydania · 2. Co zmienia 2.3.0 · 3. Migracja · 4. Co się nie zmieniło

Źródło: `changelog.asciidoc` i moduły w tagach `2.2.1`, `v2.2.1-d2`, `v2.3.0` repozytorium github.com/ocpi/ocpi,
czytane 2026-10-20.

## 1. Tagi i wydania
| Tag | Znaczenie |
|---|---|
| `2.2.1` | pierwotne wydanie 2.2.1 |
| `v2.2.1-d2` | wydanie poprawione 2.2.1 (zmiany niżej) |
| `v2.3.0` | wydanie 2.3.0 |
| `v2.3.0-ed1`, `v2.3.0-ed2`, `v2.3.0-payments`, `v2.3.0-bookings` | edycje i moduły dodatkowe |
Daty wydań, treść Edition 2 i status uzupełnień: [do weryfikacji] na evroaming.org. OCPI 3.0 rozwijane osobno; tu nie opisane.
Zapisuj w integracji **tag**, nie samą wersję.

2.2.1-d2 wobec 2.2.1 (zmiany treści, nie formatu): przepisana dokumentacja Tariffs i `step_size`, poprawione przykłady,
wyjaśnienie Base64 w nagłówku `Authorization`, notatka o braku reguł zaokrąglania cen, zalecenie by `EVSE.uid` nie był
sprzętowym ID, usunięcie wymogu różnych taryf w każdym `charging_period`.

## 2. Co zmienia 2.3.0 (wobec 2.2.1-d2)
| Obszar | Zmiana |
|---|---|
| Rozszerzalność | można dodawać moduły, pola i wartości enum (`OpenEnum`); platforma **nie odrzuca** żądań ani odpowiedzi z nieznanymi polami |
| Credentials | pole `hub_party_id` (5 znaków: kraj + party hub); platforma huba wymienia w `roles` strony osiągalne przez hub |
| Locations | `help_phone`, informacje dla osób z niepełnosprawnościami, `parking[]` przy EVSE (typ pojazdu, wymiary, ograniczenia), `accepted_service_providers`, nowe wartości (np. złącze MCS, `TESLA_S`), `capabilities` EVSE |
| Zgodność z ISO 15118 | `ConnectorCapability`: `ISO_15118_2_PLUG_AND_CHARGE`, `ISO_15118_20_PLUG_AND_CHARGE` |
| Tokens | `TokenType` `EMAID` (eMSP zalecany, by nie pchać); `contract_id` wg „E-mobility ID-codes” |
| Identyfikatory | `evse_id` wg „E-mobility ID-codes” (IDACS) zamiast eMI3 — `dom-ev-identifiers` |
| Tariffs | `min_price`/`max_price` jako `PriceLimit` (przed i po podatku), `tax_included`, `preauthorize_amount`, podatki Ameryki Płn. — `dom-ev-tariffs-pricing` |
| Nowy moduł | Payments (płatności); Bookings jako osobny tag — poza głębokim zakresem tego skilla |
Z draftu 3.0 przeniesiono proste wartości enum. Przepisy (AFIR) wpływają na treść Locations i Tariffs, ale OCPI nie
zastępuje obowiązków regulacyjnych: opisz je słowami „przepisy (AFIR)”, nie jako cechę protokołu.

## 3. Migracja 2.2.1 → 2.3.0
1. Wdróż tolerancję nieznanych pól (parser, który ich nie odrzuca) **przed** przejściem na 2.3.0 u partnerów.
2. Upewnij się, że oba końce mają 2.3.0, i przełącz przez `PUT` na `credentials` nowej wersji; stare połączenie 2.2.1 działa równolegle.
3. Dodaj nowe wartości enum do walidatorów (otwarte enumy: nieznana wartość ≠ błąd). Dotyczy `TokenType`, typów złączy, możliwości.
4. Hub: wypełnij `hub_party_id` i raportuj strony w `roles`; partnerzy 2.2.1 nadal czytają strony przez `hubclientinfo`.
5. Zakres rejestru wersji: trzymaj mapę partner → wersja → tag specyfikacji.
6. Przetestuj kontraktowo oba stosy (`references/test-kontraktowy.md`).

## 4. Co się nie zmieniło
- Mechanika handshake A/B/C, nagłówek `Authorization` z Base64, paginacja, kody statusu 1000–4003.
- Sessions i Commands (treść modułów identyczna w `v2.2.1-d2` i `v2.3.0`; sprawdzone różnicą plików).
- Zasada: CDR niezmienny, korekta CDR kredytowym — `dom-ev-cdr-settlement`.
