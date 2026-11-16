# Aktualizacja wersji Stripe: API, SDK, Stripe.js, webhooki

## 1. Wersja docelowa
- Wersję podaną przez człowieka bierzesz wprost. W przeciwnym razie sprawdzasz aktualną w dokumentacji (strona „API
  versioning”, zdanie „The current version is…”; w Stripe CLI `stripe docs /api/versioning`).
- Migawka ze źródła (2026-10-21): `2026-09-30.endive`. Nowe stabilne wersje wychodzą co miesiąc, więc migawka starsza
  niż miesiąc jest prawdopodobnie nieaktualna. Bez dostępu do dokumentacji mów, że najnowsza wersja jest
  niezweryfikowana; nie zgaduj nowszego numeru.
- Porównaj cel z każdym przypięciem w integracji: konfiguracja klienta, nadpisania per żądanie, endpointy webhooków.
  Nie cofaj przypięcia do starszej wersji ani nie zmieniaj stabilnej na podglądową bez prośby; przypięcie zgodne
  z celem zgłoś jako bez zmian.

## 2. Jak wersjonuje Stripe
- Wersje datowane (`RRRR-MM-DD.nazwa`, np. `2024-12-18.acacia`, `2025-08-27.basil`). Od `2024-09-30.acacia` co miesiąc
  wersja bez zmian łamiących, a dwa razy w roku wydanie główne, które zaczyna się od wersji ze zmianami łamiącymi.
- **Zgodne wstecz:** nowe zasoby, nowe opcjonalne parametry, nowe pola w odpowiedziach, zmiana długości
  identyfikatorów, nowe typy zdarzeń. **Łamiące:** zmiana nazwy lub usunięcie pola, zmiana zachowania, usunięte
  endpointy i parametry.
- Identyfikatory obiektów Stripe przechowuj w kolumnach do 255 znaków z porównaniem rozróżniającym wielkość liter.

## 3. SDK serwerowe
- **Ruby, Python, PHP, Node.js:** wersję API ustawiasz w konfiguracji klienta (Node: `apiVersion`) i możesz ją
  nadpisać per żądanie — tak testujesz nową wersję fragmentami.
- **Java, Go, .NET:** wersja API jest stała dla wydania SDK (typy odpowiedzi jej odpowiadają). Nie nadpisuj jej —
  podnieś SDK do wydania celującego w wersję docelową.
- Wersja podglądowa wymaga wydania `beta` SDK w każdym języku.
- Zawsze jawna wersja w kodzie, nie domyślna wersja konta.

## 4. Stripe.js i SDK mobilne
- Stripe.js: model „evergreen” z wydaniami głównymi dwa razy w roku (Acacia, Basil, Clover, Dahlia, Endive). Wersja
  Stripe.js jest sparowana z wersją API i tego nie nadpiszesz; ładujesz ją ścieżką skryptu z nazwą wydania albo
  paczką `@stripe/stripe-js` (wersja główna paczki odpowiada wydaniu). v3 jest wspierane bezterminowo; przed zmianą
  Stripe.js podnieś najpierw wersję API.
- iOS i Android: SemVer, poprawki tylko w najnowszej wersji głównej. React Native: schemat `0.x.y`, gdzie zmiana `x`
  może łamać. SDK mobilne działają z każdą wersją API backendu, chyba że dokumentacja mówi inaczej.

## 5. Webhooki i miejsca docelowe zdarzeń
- Zdarzenia „snapshot” mają wersję API; zdarzenia „thin” nie, więc ich miejsc docelowych nie zmieniasz (wywołania,
  które pobierają pełne zdarzenie lub zasób, nadal są wersjonowane).
- Miejsce docelowe v2 (webhook, Amazon EventBridge, Azure Event Grid) ma `snapshot_api_version` niezmienne po
  utworzeniu: tworzysz nowe, testujesz, w czasie przełączenia obsługa przyjmuje oba sekrety podpisu, potem wyłączasz
  stare (inaczej zdarzenia przychodzą podwójnie).
- Obsługa webhooków ignoruje nieznane typy zdarzeń bez błędu.

## 6. Procedura
1. Przejrzyj changelog API między wersją obecną a docelową i przewodnik „API upgrades”.
2. Podnieś paczkę SDK (np. `npm update stripe`, `pip install --upgrade stripe`) w osobnym PR (ops-dependency-upgrades).
3. Zmień przypiętą wersję w konfiguracji klienta.
4. Testuj z nagłówkiem `Stripe-Version` (curl) albo nadpisaniem per żądanie w piaskownicy.
5. Miejsca docelowe zdarzeń wg sekcji 5.
6. Stripe.js i SDK mobilne, jeśli trzeba.
7. Wdrożenie. Przez 72 godziny po podniesieniu wersji konta można wrócić do poprzedniej w Workbench.

## Źródła
stripe/ai, plik skills/upgrade-stripe/SKILL.md, commit 1bcd18a (2026-10-21), MIT. Opisane własnymi słowami; nazwy
wersji i wydań przepisane ze źródła.
