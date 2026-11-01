---
name: ai-mcp-server
description: Użyj przy budowie własnego serwera MCP — czy MCP, transport, kontrakt narzędzi, bezpieczeństwo i autoryzacja, testy w CI bez modelu, wersje, rejestracja w Claude Code.
metadata:
  przeglad: "2027-01-23"
  katalog: "Użyj, gdy budujesz własny serwer MCP (Model Context Protocol) dla agentów — decyzja: serwer MCP czy skill ze skryptem, transport (stdio, Streamable HTTP) i jego reguły, narzędzia jako kontrakt (nazwy, schematy z ograniczeniami, adnotacje readOnly/destructive/idempotent, błędy z następnym krokiem), bezpieczeństwo (stdout tylko dla protokołu, wynik narzędzia jako niezaufane dane, potwierdzenie operacji niszczących, autoryzacja OAuth 2.1 z odbiorcą tokenu, bez przekazywania tokenu dalej, Origin i localhost), testy w CI bez modelu (sesja w pamięci, migawka kontraktu, proces stdio, surowy stdout), wersjonowanie narzędzi, rejestracja w Claude Code (.mcp.json, zakresy). Nie do projektu pętli agenta i doboru narzędzi po stronie agenta (ai-agents), oceny i podłączania obcych serwerów MCP (core-agent-security), zagrożeń aplikacji LLM ogólnie (sec-llm-security) ani ewaluacji jakości na modelu (ai-evals)."
  slowa: "serwer MCP, MCP server, Model Context Protocol, własny serwer mcp, wystawić API jako MCP, narzędzia dla agentów, FastMCP, mcp python sdk, typescript sdk mcp, stdio, streamable http, testy serwera mcp, MCP Inspector, .mcp.json, claude mcp add, autoryzacja mcp, oauth mcp, token mcp, readOnlyHint, destructiveHint, skill czy serwer mcp, 2026-07-28, mcp-session-id, bezstanowy mcp, sampling przestarzały, mrtr, mcp app, mcp apps, interfejs w czacie, przycisk zatwierdź, ui://"
---

# Własny serwer MCP

Proces budowy i przewodniki SDK (Python, TypeScript) daje oficjalny skill Anthropic `mcp-builder`
(github.com/anthropics/skills, Apache 2.0) — przed instalacją audyt (core-agent-security). Ten skill dokłada to,
czego tam nie ma: decyzję, bezpieczeństwo, testy w CI, wersje i rejestrację w Claude Code. Projekt narzędzi po
stronie agenta: ai-agents.

## Procedura
1. **Czy serwer MCP?** Serwer, gdy z tych samych narzędzi korzysta **wiele klientów** (Claude Code, inne agenty,
   aplikacja) albo potrzebny jest stan, połączenie lub uwierzytelnienie, którego nie da się bezpiecznie dać
   skryptowi. Jeden zespół w Claude Code i proste wywołanie API → skill ze skryptem (core-skill-authoring): mniej
   kodu, brak procesu do utrzymania.
2. **Transport**: stdio dla serwera lokalnego (proces klienta), Streamable HTTP dla zdalnego. Reguły:
   - stdio — na stdout **tylko** wiadomości MCP (specyfikacja: „MUST NOT”); logi na stderr. Klient Python SDK
     pomija obce linie, inni klienci mogą zerwać połączenie — sprawdza to test surowego stdout;
   - HTTP — walidacja nagłówka `Origin` (403 przy nieznanym), lokalnie nasłuch tylko na `127.0.0.1`.
3. **Narzędzia jako kontrakt**: nazwa czasownik + rzecz, opis „co i kiedy”, schemat wejścia z ograniczeniami
   (zakres, wzorzec, długość), wynik strukturalny, adnotacje `readOnlyHint` / `destructiveHint` /
   `idempotentHint` / `openWorldHint` zgodne z prawdą. Błąd to wynik narzędzia z następnym krokiem („użyj
   find_rooms”), nie wyjątek protokołu. Lista z paginacją i limitem.
4. **Bezpieczeństwo**:
   - wynik narzędzia to dane dla modelu, nie polecenia — treść z zewnętrznych systemów oznaczaj jako cudzą,
     nie wykonuj instrukcji z danych (sec-llm-security);
   - operacje niszczące: osobne narzędzie z `destructiveHint`, potwierdzenie po stronie klienta, idempotencja;
   - zdalny serwer z autoryzacją: OAuth 2.1, serwer przyjmuje tylko tokeny wystawione **dla niego** (odbiorca,
     RFC 8707), nieważny token → 401; **nie przekazuje tokenu klienta dalej** do API za sobą (problem
     „zdezorientowanego zastępcy”) — do API używa własnych poświadczeń z minimalnymi uprawnieniami;
     rejestracja klienta przez Client ID Metadata Documents (DCR przestarzałe), PKCE, `iss` (RFC 9207),
     `application_type` dla klientów CLI i desktop — stan specyfikacji `2026-07-28`: be-auth-security,
     `.claude/skills/be-auth-security/references/tokeny-sesje-oauth.md` §7;
   - sekrety ze zmiennych środowiskowych, nigdy w `.mcp.json` w repozytorium.
   - interfejs dla człowieka (MCP App): akcja tylko dla człowieka z `_meta.ui.visibility: ["app"]`, zatwierdzenie
     z ID i wersją obiektu, autoryzacja i walidacja na serwerze — `references/spec-2026-07-28-i-apps.md` §3–4;
5. **Testy w CI bez modelu** (szablon w `references/serwer-i-testy.md`): sesja w pamięci
   (`create_connected_server_and_client_session`) — migawka kontraktu (nazwy, wymagane parametry, adnotacje),
   wynik strukturalny, błędy, odrzucenie złego wejścia przez schemat; prawdziwy proces po stdio; surowy stdout
   tylko z JSON-RPC. Ręcznie: MCP Inspector. Jakość użycia przez model — ewaluacja (ai-evals, 10 pytań wg
   `mcp-builder`).
6. **Wersja specyfikacji:** `2026-07-28` jest bezstanowa (bez `initialize` i `Mcp-Session-Id`, `server/discover`,
   nagłówki `Mcp-Method`/`Mcp-Name`, MRTR zamiast Sampling i żądań od serwera). Serwer z sesją przenosi stan do jawnych
   uchwytów — `references/spec-2026-07-28-i-apps.md` §1–2.
7. **Wersje**: kontrakt narzędzi to publiczne API serwera — usunięcie narzędzia, zmiana nazwy albo nowy wymagany
   parametr to MAJOR; nowe narzędzie lub parametr opcjonalny to MINOR (core-semver). Zmianę niezgodną
   wprowadzasz nowym narzędziem i wycofaniem starego, migawka kontraktu w teście wymusza świadomą decyzję.
8. **Rejestracja w Claude Code**: `claude mcp add --scope project <nazwa> -e KLUCZ=wartość -- <polecenie>`
   (nazwa przed `-e`) zapisuje `.mcp.json` do repozytorium; zakres `local` — konfiguracja użytkownika z sekretami.
   Uprawnienia narzędzi serwera w ustawieniach jak dla każdego narzędzia (`mcp__<serwer>__<narzędzie>`).

## Przykład
Serwer `booking` (Python, `mcp` 1.29.0): `find_rooms(min_seats, limit)` — tylko odczyt, wynik strukturalny
z `total`; `block_room(room_id, by)` — `room_id` ze wzorcem `^sala-\d+$`, idempotentne dla tej samej osoby,
konflikt → `ToolError("Sala sala-1 jest zajęta przez jan. Wybierz inną salę z find_rooms.")`. Sześć testów
w CI bez modelu; test surowego stdout wykrył dopisany `print()`, którego test sesją nie zauważył. Kod, testy
i `.mcp.json`: `references/serwer-i-testy.md`.

## Checklista
- [ ] uzasadnienie „serwer, nie skill” (klienci, stan, uwierzytelnienie)
- [ ] stdout tylko JSON-RPC (test), logi na stderr; przy HTTP `Origin` i localhost
- [ ] schematy z ograniczeniami, adnotacje zgodne z działaniem, błędy z następnym krokiem
- [ ] tokeny tylko dla tego serwera, bez przekazywania dalej; sekrety poza repozytorium
- [ ] migawka kontraktu w CI, zmiana kontraktu = decyzja o wersji

## Źródła
- Specyfikacja MCP 2026-07-28 (changelog) i MCP Apps 2026-01-26 — sprawdzone 2026-11-01, szczegóły w references.
- Specyfikacja MCP 2025-11-25: „Transports”, „Authorization”, „Security Best Practices”
  (github.com/modelcontextprotocol/modelcontextprotocol, commit dae694f, odczyt 2026-10-23).
- Python SDK `mcp` 1.29.0 (PyPI), Claude Code 2.1.309 (`claude mcp add --help`) — sprawdzone w działaniu 2026-10-23.
- Anthropic, skill `mcp-builder` (github.com/anthropics/skills, commit dbd4588, Apache 2.0) — odesłanie, treści nie przejęto.
Opisane własnymi słowami.
