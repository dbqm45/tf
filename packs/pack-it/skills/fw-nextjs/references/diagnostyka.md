# Diagnostyka typowych błędów Next.js (App Router)

> **Spis treści:** 1. Granica serwer–klient · 2. Błędy hydratacji · 3. Utrata renderowania na serwerze bez
> `<Suspense>` · 4. Paczki niezgodne z serwerem · 5. Nawigacja w `try/catch` · 6. Narzędzia serwera deweloperskiego

## 1. Granica serwer–klient
- **Asynchroniczny komponent kliencki** (`'use client'` i `async function`) jest niedozwolony. Dane pobierz
  w rodzicu serwerowym i przekaż je propsami albo użyj `use(promise)` w kliencie.
- **Nieserializowalne propsy** z serwera do klienta: zwykłe funkcje, instancje klas, `Map`, `Set`, cykle,
  symbole. `Date` zamieniaj na tekst ISO (np. `toISOString()`), a kolekcje na tablice lub obiekty. Funkcje
  przekazujesz tylko jako Server Actions (`'use server'`).
- **Obiekt domenowy** (klasa z metodami) przechodzi jako DTO i jest odtwarzany fabryką po stronie klienta
  (tabela „Pojęcia domenowe” w SKILL.md).

## 2. Błędy hydratacji
Typowe przyczyny: API przeglądarki w renderze, data i czas (inna strefa i chwila), losowe identyfikatory (`useId()`),
niepoprawne zagnieżdżenie HTML. Datę formatuj w kliencie po zamontowaniu albo przekaż z serwera tekst dla jednej, jawnej
strefy. `suppressHydrationWarning` tylko dla pojedynczego elementu z celowo różną treścią, nie jako ogólne wyciszenie.

## 3. Utrata renderowania na serwerze bez `<Suspense>`
`useSearchParams()` w trasie statycznej bez `<Suspense>` nad komponentem przenosi renderowanie całej trasy do
przeglądarki. To samo dotyczy `usePathname()` w trasie dynamicznej bez `generateStaticParams`. Owiń najmniejszy
komponent, który ich używa, w `<Suspense>` z zastępczą treścią. `useParams()` i `useRouter()` tego nie wymagają.

## 4. Paczki niezgodne z serwerem
- **Paczki używające `window` lub `document`** (wykresy, edytory, mapy): import dynamiczny bez SSR w komponencie
  klienckim.
- **Paczki z natywnymi modułami lub źle pakujące się** (np. `sharp`, `bcrypt`, część ORM): wpis w
  `serverExternalPackages` w `next.config`.
- **Błędy ESM/CommonJS** w paczce z `node_modules`: `transpilePackages`.
- CSS importujesz w module (`import './x.css'`), a nie znacznikiem `<link>`; typowych polifilli nie dodajesz, bo
  Next.js je dołącza.
- Rozmiar paczek sprawdzasz analizatorem paczek dla Turbopacka albo webpacka [niezweryfikowane: nazwa polecenia
  zależy od wersji — sprawdź w dokumentacji wersji].

## 5. Nawigacja w `try/catch`
`redirect()`, `permanentRedirect()`, `notFound()`, `forbidden()` i `unauthorized()` działają przez rzucenie
specjalnego wyjątku. Nie wołaj ich wewnątrz `try`, którego `catch` połyka błędy: przenieś wywołanie za blok albo
w `catch` przekaż wyjątek dalej (`unstable_rethrow`). `forbidden()` i `unauthorized()` wymagają włączenia w
konfiguracji i plików `forbidden.tsx` / `unauthorized.tsx` [niezweryfikowane: status eksperymentalny zależy od wersji].
`error.tsx` jest komponentem klienckim; `global-error.tsx` zawiera własne `<html>` i `<body>`.

## 6. Narzędzia serwera deweloperskiego
- **Punkt MCP serwera deweloperskiego** (`/_next/mcp`, w 16 domyślnie, w 15 za flagą `experimental.mcpServer`):
  zwraca bieżące błędy builda i działania z mapowaniem źródeł, listę tras i ścieżkę logu. Sprawdź port uruchomionego
  serwera zamiast zakładać 3000. Podłączenie nowego serwera MCP do agenta to decyzja człowieka (core-agent-security).
- **Przebudowa wybranych tras:** `next build --debug-build-paths "<ścieżka lub wzorzec>"` (16+) skraca sprawdzenie
  poprawki błędu builda w dużej aplikacji.
