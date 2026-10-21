# Bezpieczeństwo integracji ze Stripe

## 1. Klucze API
- Klucza nie ma w kodzie źródłowym ani w commitowanych plikach środowiska. Ciągi `sk_live_…` i `rk_live_…` to klucze
  produkcyjne; `sk_test_…` w kodzie też jest ryzykiem — ostrzeż.
- Przechowywanie: sejf sekretów platformy (AWS Secrets Manager lub Parameter Store jako `SecureString`, Google Secret
  Manager, Azure Key Vault) z odczytem tylko dla aplikacji, która klucza potrzebuje. Vercel nie ma wbudowanego sejfu:
  dodatek synchronizujący sekrety albo zmienna oznaczona jako wrażliwa. Zmienna środowiskowa tylko, gdy platforma
  nie ma sejfu. Ogólnie: ops-secrets-identities.
- Osobne klucze dla produkcji, stagingu i QA; klucza nie logujesz ani nie zwracasz w błędach; żaden endpoint nie
  zrzuca zmiennych środowiskowych.
- Hook pre-commit wykrywający `sk_` i `rk_` (eng-local-quality-gates); rotacja przy odejściu osób z dostępem.
- Klucze nigdy w kodzie klienta ani aplikacji mobilnej (da się je wydobyć). Wywołania przez własny backend; gdy klient
  musi rozmawiać ze Stripe — klucze efemeryczne (krótkie, ograniczone do zasobu).

## 2. Klucze ograniczone (RAK, `rk_`)
Mają tylko nadane uprawnienia, więc wyciek szkodzi mniej niż wyciek `sk_`. Jeden klucz na usługę, minimum uprawnień.
Migracja z klucza tajnego:
1. Z logów żądań w Workbench wypisz wywołania, które robi klucz tajny.
2. Utwórz klucz ograniczony w trybie testowym z tymi uprawnieniami.
3. Obserwuj logi (`stripe logs tail` w Stripe CLI) i testuj; każdy `403` to brakujące uprawnienie.
4. Utwórz odpowiednik produkcyjny, podmień klucz, potem wycofaj lub wygaś stary klucz tajny.

Dodatkowo polityki dostępu (ograniczenie IP) per klucz, różne dla środowisk.

## 3. Wyciek klucza
1. Natychmiast obróć (roll) albo usuń klucz w panelu — także przy niepewności, czy ktoś go użył.
2. Przejrzyj logi żądań tego klucza w Workbench.
3. Nieznana aktywność → wsparcie Stripe. Obsługa incydentu: ops-security-operations.

Przygotowanie: ćwicz obracanie kluczy, skanuj repozytorium, hook pre-commit.

## 4. Webhooki, przeglądarka, OAuth
- Podpis webhooka weryfikujesz zawsze przed obsługą; sekret podpisu traktujesz jak klucz API. Dodatkowo lista
  dozwolonych adresów IP Stripe na endpoincie.
- **CSP:** nagłówek `Content-Security-Policy` w każdej aplikacji ze Stripe.js; co najmniej `https://*.stripe.com`
  w `script-src`, `frame-src`, `connect-src` (pełna lista: przewodnik bezpieczeństwa integracji Stripe). Nie
  `default-src *`. Ogólnie: fe-web-platform.
- **OAuth (Connect, Link, Stripe Apps):** parametr `state` — unikalny, nieprzewidywalny, sprawdzany w callbacku (CSRF).

## 5. Dostęp do panelu i Connect
- Dwuskładnikowe logowanie przez klucze dostępu (passkeys) albo aplikację, nie SMS (przejęcie numeru). SSO przez SAML
  i provisioning SCIM dla zespołów.
- Connect: przy kontach Express i Custom platforma odpowiada za oszustwa i spory; onboarding hostowany przez Stripe
  zamiast własnego (mniej danych osobowych po stronie platformy). Konfiguracja kont: `references/billing-connect-tax.md`.

## Źródła
stripe/ai, plik skills/stripe-best-practices/references/security.md, commit 1bcd18a (2026-10-21), MIT. Opisane własnymi
słowami.
