# Renderowanie, SSR, hydratacja i `@defer`

Spis treści: 1. Wybór sposobu renderowania · 2. Tryb renderowania per trasa · 3. Hydratacja · 4. Kod zgodny
z serwerem · 5. Dane żądania i transfer cache · 6. `@defer` · Źródła

## 1. Wybór sposobu renderowania
| Sposób | Kiedy | Koszt |
|---|---|---|
| **CSR** (domyślny) | panele, narzędzia wewnętrzne, treść po zalogowaniu | słabe SEO, treść dopiero po załadowaniu JS |
| **SSG** (prerendering) | strony marketingowe, blog, dokumentacja, katalog znany w czasie budowania | zmiana treści wymaga przebudowy; nie dla danych użytkownika |
| **SSR** | strony produktów, wiadomości, treść dynamiczna z SEO | serwer lub środowisko serverless, wyższy koszt i opóźnienie |

Sposób wybierasz per trasa, nie dla całej aplikacji.

## 2. Tryb renderowania per trasa
- W konfiguracji serwera tablica `ServerRoute[]` przypisuje trasom `RenderMode.Client`, `RenderMode.Prerender` albo
  `RenderMode.Server`; podpięta przez `provideServerRendering(withRoutes(serverRoutes))`.
- Zasady:
  - ścieżki szczegółowe przed `**`; ścieżki serwera zgodne z trasami routera;
  - `Prerender` tylko wtedy, gdy dane są dostępne w czasie budowania. Parametry tras dynamicznych zwraca
    `getPrerenderParams()`: `inject()` przed pierwszym `await`, klucze równe nazwom parametrów, wartości jako tekst;
  - ścieżki niewygenerowane w czasie budowania obsługuje `fallback` (`PrerenderFallback.Server`, domyślnie, albo
    `Client`, `None`);
  - nagłówki statyczne w `headers`; `status` tylko dla tras CSR i SSR.

## 3. Hydratacja
- `provideClientHydration()` w konfiguracji wspólnej dla przeglądarki i serwera. Od v22 włącza domyślnie
  hydratację przyrostową i odtwarzanie zdarzeń sprzed hydratacji; nie dodawaj wycofanego `withIncrementalHydration()`.
- **DOM z serwera i z przeglądarki musi być identyczny:**
  - bez różnych szablonów zależnych od `isPlatformBrowser`;
  - bez ręcznego wstawiania, usuwania i przenoszenia węzłów DOM;
  - poprawny HTML; `preserveWhitespaces` jednakowe po obu stronach.
- `ngSkipHydration` na komponencie to ostateczność i rozwiązanie tymczasowe: Angular renderuje wtedy całe poddrzewo od
  nowa.

## 4. Kod zgodny z serwerem
- Na serwerze nie ma DOM, `localStorage` ani pomiarów układu. Pracę tylko dla przeglądarki umieszczasz
  w `afterNextRender`, `afterEveryRender` albo `afterRenderEffect` (nie działają na serwerze).
- `afterRenderEffect` dzieli pracę na fazy w kolejności `earlyRead` → `write` → `mixedReadWrite` → `read`: w fazie
  zapisu nie czytasz układu, w fazie odczytu nie zapisujesz; zapobiega to wymuszonym przeliczeniom układu.
- `DOCUMENT` z wstrzykiwania zamiast globalnego `document`; różne implementacje dla przeglądarki i serwera za jednym
  tokenem aplikacji.
- **Brak wycieku między żądaniami:** wartości zależne od żądania nie trafiają do zmiennych modułu ani do providerów
  `useValue` najwyższego poziomu; tworzy je fabryka.

## 5. Dane żądania i transfer cache
- Tokeny z `@angular/core`: `REQUEST` (obiekt `Request`), `RESPONSE_INIT` (status i nagłówki odpowiedzi),
  `REQUEST_CONTEXT` (kontekst od adaptera serwera). Mogą być `null` (CSR, SSG, budowanie), więc zawsze to sprawdzasz.
- Transfer cache HTTP zostawiasz domyślny, ale żądania zależne od użytkownika wyłączasz
  (`withHttpTransferCacheOptions({ filter })` albo `transferCache: false` w żądaniu). Odpowiedzi uwierzytelnionych nie
  przenosisz do HTML strony.
- Własna praca asynchroniczna, na którą serwer ma poczekać przed wysłaniem HTML: `PendingTasks` albo
  `pendingUntilEvent()`.
- Produkcyjna lista `allowedHosts` bez symboli wieloznacznych; `trustProxyHeaders` tylko za zaufanym proxy, które
  podmienia nagłówki przekazywane dalej.

## 6. `@defer`
- Do bloku trafiają tylko zależności standalone, do których nie ma odwołań poza blokiem w tym samym pliku (także
  w zapytaniach widoku). Importy przez pliki zbiorcze (`index.ts`) potrafią to zepsuć.
- Bloki `@placeholder`, `@loading` (z `after` i `minimum` przeciw miganiu) i `@error` ładują się od razu, więc są małe.
- Wyzwalacze: `on idle` (domyślny), `viewport`, `interaction`, `hover`, `immediate`, `timer`; `when <wyrażenie>`
  działa raz, gdy wyrażenie stanie się prawdziwe. `prefetch on …` pobiera kod wcześniej.
- `viewport`, `interaction` i `hover` potrzebują placeholdera z jednym elementem głównym albo referencji do elementu.
- **SSR:** serwer renderuje sam placeholder i nie uruchamia wyzwalaczy. Gdy treść ma być renderowana na serwerze
  i ożyć później, dodaj `hydrate on …` (np. `@defer (on viewport; hydrate on interaction)`).
- **Stabilność układu:** nie odkładasz treści widocznej od razu ani elementu LCP; placeholder ma wymiary treści
  docelowej; zagnieżdżone bloki mają różne wyzwalacze.

## Źródła
- angular/skills, skill `angular-developer` (pliki angular-developer/references: rendering-strategies, server-side-rendering,
  deferrable-views, effects), commit 43ec6adc2b35049734d0d114e3948e022f1cd1e7 z 2026-10-21, licencja MIT,
  autor Google LLC. Opisane własnymi słowami; odczyt 2026-10-21.
