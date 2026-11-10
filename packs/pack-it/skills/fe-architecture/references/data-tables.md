# Tabele danych

Tabela w aplikacji biznesowej to zwykle najczęściej używany ekran: lista zamówień, klientów, zgłoszeń. Typowe
problemy biorą się z tego, że traktuje się ją jak zwykły komponent, a nie jak widok na zbiór danych po stronie
serwera.

## 1. Stan w adresie URL
- Filtry, sortowanie, strona (lub kursor) i rozmiar strony trzymasz w parametrach adresu, np.
  `?status=new&sort=-created_at&cursor=…`. Po odświeżeniu, wstecz i wysłaniu linku widok jest ten sam.
- Wartości w URL są wejściem od użytkownika: walidujesz je schematem (nieznane pole sortowania → domyślne),
  a nie wstawiasz bezpośrednio do zapytania.
- Zmiana filtra zastępuje wpis historii (`replace`), a nie dodaje nowego przy każdym znaku; pole wyszukiwania
  z opóźnieniem (`performance/debounce.md`).
- Zaznaczenie wierszy i rozwinięte szczegóły to stan lokalny. Nie trzymasz ich w URL.

## 2. Dane po stronie serwera
- Filtrowanie, sortowanie i paginacja są po stronie serwera, gdy zbiór nie jest mały i stały. Ściąganie 100 tys.
  rekordów do przeglądarki to wolny start i przestarzałe dane. Kontrakt API (kursor, lista dozwolonych pól):
  be-api-design (pack-it), `.claude/skills/be-api-design/references/http-w-praktyce.md` §4.
- Dane serwera trzymasz w warstwie z cache zapytań (np. TanStack Query, SWR, RTK Query). Klucz zapytania to
  parametry z URL, więc powrót do poprzedniego filtra jest natychmiastowy.
- Każdy stan widoku: ładowanie (bez skakania układu), błąd z ponowieniem, pusto po filtrze („brak wyników dla…
  — wyczyść filtry”) i pusto w ogóle (`resilience/loading-state.md`).

## 3. Wydajność przy wielu wierszach
- Paginacja albo „wczytaj więcej” to pierwszy wybór. Wirtualizacja (renderowanie tylko widocznych wierszy,
  np. TanStack Virtual, react-window) jest dla list, które muszą być długie: logi, podgląd importu.
- Przy wirtualizacji: stała albo mierzona wysokość wierszy, a przewijanie i fokus klawiatury działają na
  całej liście. Wyszukiwanie strony przeglądarki (Ctrl+F) nie widzi wierszy, których nie ma w DOM, więc daj
  własne wyszukiwanie.
- Ciężkie komórki (wykresy, obrazy) renderujesz leniwie (`performance/lazy-loading.md`).

## 4. Zaznaczanie i operacje masowe
- „Zaznacz wszystko” ma dwa poziomy: wiersze na tej stronie i **wszystkie pasujące do filtra** z liczbą
  („zaznaczono 50 na stronie — zaznacz wszystkie 12 413 pasujące”).
- Operacja na „wszystkich pasujących” wysyła na serwer **filtr**, a nie listę ID z przeglądarki. Serwer liczy
  zbiór, sprawdza uprawnienia dla każdego rekordu i wykonuje operację w tle. Wzorzec: be-business-app-patterns
  (pack-it), `.claude/skills/be-business-app-patterns/references/operacje-masowe.md`.
- Po zmianie filtra zaznaczenie „wszystkich pasujących” się kasuje: inny filtr to inny zbiór.

## 5. Paleta poleceń i skróty
- Przy wielu akcjach i ekranach: paleta poleceń (Ctrl/Cmd+K) z wyszukiwaniem akcji i rekordów. Akcje niszczące
  także tu wymagają potwierdzenia.
- Skróty klawiszowe w tabeli (strzałki, spacja do zaznaczenia) muszą dać się wyłączyć i nie mogą kolidować
  z czytnikiem ekranu (WCAG 2.2 SC 2.1.4).

## 6. Dostępność
- Prawdziwa tabela (`<table>`, `<thead>`, `<th scope="col">`) zamiast siatki z `div`. Siatkę z rolą `grid`
  i nawigacją strzałkami robisz tylko wtedy, gdy komórki są edytowalne i to przemyślane.
- Kolumna sortowalna: przycisk w nagłówku i `aria-sort="ascending" | "descending"` na `<th>` aktualnie
  sortowanej kolumny (pozostałe bez atrybutu albo `none`).
- Zmiana wyników po filtrze ogłaszana przez region `aria-live="polite"` („12 413 wyników”), bez przenoszenia
  fokusu.
- Pole zaznaczenia wiersza ma etykietę z nazwą rekordu („Zaznacz zamówienie 1042”), a nie pustą.
- Na wąskim ekranie: przewijanie poziome z widoczną pierwszą kolumną albo widok kart. Nie ukrywasz kolumn bez
  informacji.

## Uwagi (stan 2026)
- Biblioteki w przykładach to typowy wybór w React. W innym frameworku zasady są te same, zmienia się tylko
  narzędzie (Angular CDK Table i Virtual Scroll, TanStack Table dla Vue i Solid). Wersje sprawdzasz w projekcie
  (core-grounding).
- `aria-sort` i role tabeli: WAI-ARIA 1.2 i wzorce APG (Table, Sortable Table) [niezweryfikowane w źródle 2026-11-10].
