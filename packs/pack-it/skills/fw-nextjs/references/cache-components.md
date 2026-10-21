# Cache Components (Next.js 16+) — model, klucze, ograniczenia, migracja

> **Spis treści:** 1. Trzy rodzaje treści · 2. Gdzie stawiasz `'use cache'` · 3. Czas życia i warianty · 4. Klucz cache
> · 5. Unieważnianie · 6. Dane z żądania · 7. Ograniczenia · 8. Migracja ze starych ustawień

Włączasz flagą `cacheComponents: true` w `next.config.ts`; zastępuje ona eksperymentalne `experimental.ppr`.
Przed zmianą sprawdź w dokumentacji dopasowanej do zainstalowanej wersji (`.next-docs/`, SKILL.md), bo API
cache zmieniało się między wydaniami 15 i 16.

## 1. Trzy rodzaje treści na jednej stronie
- **Statyczna:** kod synchroniczny, importy i czyste obliczenia trafiają do powłoki prerenderowanej przy buildzie.
- **Cache'owana:** dane asynchroniczne, które nie muszą być świeże przy każdym żądaniu, oznaczasz `'use cache'`.
- **Dynamiczna:** dane, które muszą być świeże albo zależą od żądania (cookies, nagłówki, parametry wyszukiwania),
  owijasz w `<Suspense>`. Doczytują się strumieniem po wysłaniu powłoki.

Komponent asynchroniczny bez `'use cache'` i bez `<Suspense>` nad nim to błąd builda: Next.js nie wie, czy ma go
prerenderować, czy czekać na żądanie. Rozstrzygasz to jawnie jednym z dwóch sposobów.

## 2. Gdzie stawiasz `'use cache'`
- **Plik:** cała strona lub moduł jest cache'owany. Używaj rzadko, bo trudno potem wydzielić część dynamiczną.
- **Komponent:** cache'owany fragment drzewa, np. lista produktów na stronie z koszykiem użytkownika.
- **Funkcja:** odczyt danych w DAL (`references/wzorce.md`, sekcja 3). Najłatwiejszy do testów i ponownego użycia.

## 3. Czas życia i warianty
- `cacheLife('minutes' | 'hours' | 'days' | 'weeks' | 'max')` albo obiekt z trzema czasami: jak długo podawać
  starą wartość bez pytania serwera, co ile odświeżać w tle i kiedy wpis bezwzględnie wygasa.
  Domyślny profil bez `cacheLife` ma krótkie czasy rzędu minut [niezweryfikowane: dokładne wartości sprawdź
  w dokumentacji wersji].
- `'use cache: remote'` — wpisy w magazynie platformy (np. Redis, KV) wspólnym dla instancji.
- `'use cache: private'` — wyjątek dla danych konkretnego użytkownika, który pozwala czytać `cookies()`; wynik
  nie trafia do wspólnego cache. Używaj, gdy nie da się przekazać wartości argumentem (sekcja 6).

## 4. Klucz cache
Klucz powstaje automatycznie z identyfikatora builda (nowe wdrożenie unieważnia wszystko), położenia funkcji,
serializowalnych argumentów i zmiennych z domknięcia. Wnioski:
- wszystko, od czego zależy wynik, musi być argumentem albo zmienną z domknięcia;
- argument nieserializowalny (klasa, funkcja) psuje klucz — przekazuj identyfikatory i proste dane;
- argument o dużej liczbie wartości (np. pełny obiekt filtra) mnoży wpisy — przekazuj tylko potrzebne pola.

## 5. Unieważnianie
- `cacheTag('products', 'product-' + id)` wewnątrz funkcji: ogólny tag dla list i szczegółowy dla jednego rekordu.
- W Server Action po zapisie `updateTag(tag)`: ten sam użytkownik od razu widzi swój zapis.
- Z webhooka lub zadania w tle `revalidateTag(tag, 'max')`: następne żądania dostaną świeże dane, bieżące mogą
  dostać starą wersję.

## 6. Dane z żądania
W funkcji z `'use cache'` nie czytasz `cookies()`, `headers()` ani `searchParams`. Odczytujesz je wyżej, poza
funkcją cache'owaną, i przekazujesz potrzebną wartość jako argument; staje się częścią klucza. Część strony, która
czyta te dane, leży w `<Suspense>`.

## 7. Ograniczenia
- Wymaga środowiska Node.js: nie działa w Edge Runtime ani przy eksporcie statycznym (`output: 'export'`).
- Wartości niedeterministyczne (`Math.random()`, `Date.now()`, `crypto.randomUUID()`) w `'use cache'` liczą się
  raz i zostają w cache. Gdy mają być inne przy każdym żądaniu, poza cache wywołaj najpierw `await connection()`
  z `next/server`.
- Przy kilku instancjach wpisy w pamięci jednej instancji nie są widoczne w innych (`references/wdrozenie.md`).

## 8. Migracja ze starych ustawień
| Było (15 i starsze) | Z Cache Components |
|---|---|
| `experimental.ppr` | `cacheComponents: true` |
| `export const dynamic = 'force-dynamic'` | usuń; dynamiczność jest domyślna |
| `export const dynamic = 'force-static'` | `'use cache'` + `cacheLife('max')` |
| `export const revalidate = N` | `cacheLife({ revalidate: N })` |
| `unstable_cache(fn, keyParts, { tags, revalidate })` | funkcja z `'use cache'`, `cacheTag(...)`, `cacheLife(...)`; bez ręcznych kluczy |

Kolejność: włącz flagę na gałęzi, uruchom `next build` i usuwaj błędy po kolei (każdy wskazuje komponent bez
decyzji „cache czy Suspense”). Potem przegląd wszystkich `revalidateTag` i `revalidatePath`.

Gdy migrujesz większą aplikację, autorzy Next.js udostępniają skille procesowe `next-cache-components-adoption`
i `next-cache-components-optimizer` w repozytorium `vercel/next.js` (katalog `skills`). Instaluje je człowiek po
audycie (core-agent-security).
