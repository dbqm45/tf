# Specyfikacja `2026-07-28` i MCP Apps

Spis treści: 1. Co zmienia `2026-07-28` · 2. Migracja serwera z sesją · 3. MCP Apps — kiedy App, a kiedy tekst ·
4. Bezpieczeństwo App · 5. Próba granicy

## 1. Co zmienia `2026-07-28`
- **Bezstanowy rdzeń:** nie ma już `initialize`/`notifications/initialized` ani nagłówka `Mcp-Session-Id`. Każde
  żądanie niesie wersję protokołu i możliwości klienta w `_meta` (`io.modelcontextprotocol/protocolVersion`,
  `…/clientCapabilities`). Serwer **musi** obsłużyć `server/discover` (wersje, możliwości, tożsamość).
- **Nagłówki `Mcp-Method` i `Mcp-Name`** są wymagane w Streamable HTTP. Bramka routuje i autoryzuje po nich bez
  parsowania treści; parametr narzędzia może trafić do nagłówka przez `x-mcp-header`.
- **Multi Round-Trip Requests (MRTR)** zastępują żądania wysyłane przez serwer (`sampling/createMessage`,
  `elicitation/create`, `roots/list`). Serwer zwraca wynik `resultType: "input_required"`, a klient ponawia żądanie
  z odpowiedzią. Każdy wynik ma `resultType` (`complete` albo `input_required`).
- **Listy z `ttlMs` i `cacheScope`**; `tools/list` w stałej kolejności (lepsze trafienia cache promptu po stronie
  klienta).
- `subscriptions/listen` zamiast GET i `resources/subscribe`; bez wznawiania strumienia SSE (zerwane żądanie klient
  ponawia jako nowe).
- **Zadania** (`tasks`) przeniesione z rdzenia do oficjalnego rozszerzenia `io.modelcontextprotocol/tasks`;
  rozszerzenia deklarowane w `extensions` w możliwościach.
- **Przestarzałe** (działają co najmniej 12 miesięcy): Roots, Sampling, Logging, transport HTTP+SSE, Dynamic Client
  Registration (zamiast niego Client ID Metadata Documents). Usunięte: `ping`, `logging/setLevel`.
- Kod błędu „zasób nie istnieje”: `-32602` (było `-32002`).

## 2. Migracja serwera z sesją
1. Stan rozmowy przenosisz do **jawnych uchwytów** wydawanych przez serwer (np. `cart_id`, `draft_id` zwracane
   z narzędzia i podawane w następnych wywołaniach), z czasem życia i autoryzacją przy każdym użyciu. Nie zakładasz
   powiązania z połączeniem.
2. Sampling zastępujesz wywołaniem API modelu po stronie serwera (z własnym kluczem i limitem) albo MRTR, gdy
   decyzja ma należeć do klienta. Roots zastępujesz parametrem narzędzia albo konfiguracją, logi idą na stderr lub do
   OpenTelemetry.
3. Dodajesz `server/discover` i obsługę wersji z `_meta`. Jeśli wspierasz starszych klientów, trzymasz obie ścieżki
   i testujesz je w CI (migawka kontraktu dla każdej wersji).
4. Bramkę uczysz reguł po `Mcp-Method`/`Mcp-Name` zamiast po ścieżce URL.
5. Zmiana zachowania widocznego dla klientów to MAJOR w wersji serwera (core-semver).

## 3. MCP Apps — kiedy App, a kiedy tekst
MCP Apps (rozszerzenie `io.modelcontextprotocol/ui`, SEP-1865, status Stable od 2026-01-26) pozwala serwerowi dać
hostowi interfejs: zasób `ui://…` typu `text/html;profile=mcp-app`, renderowany w sandboxowanym iframe, który
rozmawia z hostem przez JSON-RPC MCP.
- **App tylko wtedy, gdy interakcja ma strukturę:** zatwierdzenie, formularz, panel z akcjami, porównanie wyników.
  Odpowiedź, którą człowiek tylko czyta, zostaje tekstem.
- **Jedna App na domenę**, nie na narzędzie.
- **Dane w wyniku narzędzia**, a nie wpisane w HTML zasobu; zasób jest szablonem.
- **Łagodny powrót:** host bez rozszerzenia dostaje treść strukturalną z tego samego narzędzia.

## 4. Bezpieczeństwo App
- **Widoczność narzędzia:** `_meta.ui.visibility` (domyślnie `["model", "app"]`). Narzędzie z `["app"]` host ukrywa
  przed modelem, ale App może je wywołać. Akcja, którą ma wykonać tylko człowiek (np. „Zatwierdź”), ma
  `visibility: ["app"]`, więc model nie wywoła jej sam.
- **Zatwierdzenie przez ID i wersję obiektu:** przycisk wysyła `invoice_id` i `version`. Serwer odrzuca zatwierdzenie
  nieaktualnej karty (obiekt zmienił się po wyświetleniu).
- **UI nie jest granicą zaufania:** autoryzacja, walidacja, idempotencja i audyt są po stronie serwera, tak jak przy
  każdym wywołaniu narzędzia. App traktujesz jak niezaufany kod: deklarujesz wąskie CSP (`connect-src`,
  `frame-src 'none'`, jeśli nie trzeba zagnieżdżać).

## 5. Próba granicy
Filtr ścieżek w narzędziu plikowym serwera (rozwiązana ścieżka, `..`, dowiązania symboliczne) chroni tylko to
narzędzie. Przed przyznaniem dostępu robisz jedną operację potrzebną i jedną wykluczoną i zapisujesz, która warstwa
zatrzymała (agent, narzędzie, środowisko): core-agent-security, `references/uprawnienia-i-produkcja.md` §4b.

Źródła (sprawdzone 2026-11-01 w repozytoriach): github.com/modelcontextprotocol/modelcontextprotocol —
`docs/specification/2026-07-28/changelog.mdx` (commit 2026-10-31); github.com/modelcontextprotocol/ext-apps —
`specification/2026-01-26/apps.mdx` (status Stable, commit 2026-10-29). modelcontextprotocol.io niedostępne z sieci
sesji. Pozycja w TODO: blog.modelcontextprotocol.io (2026-10-29).
