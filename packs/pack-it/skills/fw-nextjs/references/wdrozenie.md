# Wdrożenie poza Vercelem i aktualizacja wersji

> **Spis treści:** 1. Obraz kontenera · 2. Wiele instancji · 3. Obrazy i zmienne środowiskowe · 4. Środowisko
> uruchomieniowe · 5. Aktualizacja wersji krok po kroku

## 1. Obraz kontenera
- `output: 'standalone'` w `next.config` tworzy katalog z serwerem (`server.js`) i tylko produkcyjnymi zależnościami.
  Katalogi `.next/static` i `public` kopiujesz do obrazu osobno; bez nich strona nie ma CSS ani plików statycznych.
- Obraz wieloetapowy (zależności, build, uruchomienie), proces jako użytkownik bez uprawnień roota, healthcheck na
  lekkiej trasie. Zasady obrazów: ops-docker.

## 2. Wiele instancji
Domyślny cache (ISR, wpisy `'use cache'`, wynik `revalidatePath` i `revalidateTag`) żyje na dysku lub w pamięci
**jednej** instancji. Za load balancerem każda replika ma własny cache, więc po unieważnieniu część użytkowników
widzi stare dane. Rozwiązania:
- wspólny magazyn przez własny cache handler (`cacheHandler` / `cacheHandlers` w `next.config`, np. na Redisie)
  [niezweryfikowane: nazwy opcji zależą od wersji — sprawdź w dokumentacji wersji];
- dla Cache Components wariant `'use cache: remote'` z magazynem platformy;
- adapter wdrożeniowy platformy (stabilne od 16.2) albo projekt OpenNext dla środowisk serverless.

SSR, strony statyczne z buildu, `next/font` i Draft Mode działają przy wielu instancjach bez dodatkowej konfiguracji.

## 3. Obrazy i zmienne środowiskowe
- Optymalizacja `next/image` obciąża CPU serwera. Ogranicz warianty (`deviceSizes`, `imageSizes`), wydłuż
  `minimumCacheTTL` albo użyj zewnętrznego loadera (CDN obrazów). Zdalne źródła wymieniasz w `images.remotePatterns`.
- `NEXT_PUBLIC_*` są wpisywane przy buildzie, więc jeden obraz nie zmieni ich między środowiskami. Konfigurację,
  która ma się różnić między środowiskami, czytasz na serwerze z `process.env` w czasie żądania i przekazujesz do
  klienta propsami.

## 4. Środowisko uruchomieniowe
Domyślnie i dla nowego kodu: Node.js (pełne API, baza danych, większość paczek). Edge Runtime tylko przy jawnym
wymaganiu opóźnienia z lokalizacji brzegowych i po sprawdzeniu, że wszystkie zależności w nim działają. W 16
`proxy.ts` działa na Node.js, a Cache Components nie działają w Edge.

## 5. Aktualizacja wersji krok po kroku
1. Odczytaj wersje `next`, `react`, `react-dom` i typów z `package.json` oraz lockfile'a (grep, bez czytania całego
   pliku). Podniesienie robisz tylko na prośbę człowieka (ops-dependency-upgrades, core-stack-sync).
2. Przeczytaj przewodnik aktualizacji dla każdej wersji głównej po drodze (nextjs.org/docs/app/guides/upgrading)
   albo dokumentację z paczki nowej wersji. Przy skoku o kilka wersji głównych idziesz po jednej (14 → 15 → 16).
3. Najpierw codemody: `npx @next/codemod@latest upgrade` (podnosi zależności i uruchamia potrzebne transformacje),
   w razie potrzeby pojedyncze transformacje, np. `next-async-request-api` (15), `middleware-to-proxy` (16).
4. Podnieś razem `next`, `react`, `react-dom`, `@types/react`, `@types/react-dom` i `eslint-config-next`.
5. Przejrzyj zmiany ręczne z przewodnika: konfiguracja w `next.config`, usunięte opcje, domyślne zachowanie cache.
6. Sprawdzenie: `next build`, testy jednostkowe i e2e, ręczny przegląd kluczowych ścieżek w `next dev`.
