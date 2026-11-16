---
artifact: design
phase: architecture
status: proposed
version: 2
author: natalia
created: 2026-10-30
updated: 2026-10-31
inputs: [docs/project/changes/CHG-1/intent.md, docs/project/changes/CHG-1/requirements.md]
change: CHG-1
source: PRB-1
source_reported_at: 2026-10-30
---
# Projekt zmiany CHG-1

Część „Architektura” przygotował tomasz (faza architecture), część „Doświadczenie” natalia (faza design). Plik Figmy:
brak — repo próbne nie ma projektu w Figmie (D-F3 otwarta), stany opisane tekstem.

## Architektura

### Rozwiązanie przyjęte

Wariant A z `intent.md`: data wdrożenia czytana z `config/build.json`, renderowana w stopce strony za flagą
`show_last_deployed`. Plik `config/build.json` generowany przez skrypt w repo — analogia do istniejącego wzorca
`config/flags.*.json` (plik JSON w `config/`, czytany przez serwer).

### DT-1: Plik JSON jako źródło daty wdrożenia (nie zmienna środowiskowa)

**Powód:** Projekt czyta już `config/flags.*.json` z dysku przy obsłudze żądania. Dodanie `config/build.json`
z polem `deployedAt` (format ISO 8601, `YYYY-MM-DD`) jest spójne z istniejącym wzorcem i nie wymaga nowej
infrastruktury. Zmienna środowiskowa byłaby alternatywą, ale wymagałaby innej ścieżki w `server.js` i
utrudniałaby lokalne odtworzenie zachowania produkcyjnego.

**Struktura pliku:**
```json
{ "deployedAt": "2026-10-30" }
```

### DT-2: Flaga `show_last_deployed` w istniejącym systemie flag

**Powód:** System flag (`src/flags.js`, `config/flags.*.json`) obsługuje już `welcome_banner`. Dodanie
`show_last_deployed` do tych samych plików nie wymaga nowej infrastruktury i jest kompatybilne z ShipScope
(czyta `config/flags.{env}.json`). Stan domyślny: `enabled: false` na `prod` (bezpieczny rollout).

### DT-3: Odczyt `config/build.json` przy starcie serwera (nie per żądanie)

**Powód:** Data wdrożenia nie zmienia się w trakcie życia procesu. Odczyt przy starcie (`createServer`)
jest prostszy i eliminuje powtarzalne I/O. Zmiana daty (nowe wdrożenie) wymaga restartu serwera — co i tak
jest warunkiem wdrożenia. Bez zmiany: `readFlags` pozostaje per żądanie (flagi mogą się zmieniać bez restartu).
Brak pliku, błąd odczytu albo brak pola `deployedAt` daje `deployedAt` puste — serwer startuje normalnie.

### DT-4: Renderowanie w elemencie `<footer>` w `src/page.js`

**Powód:** Stopka jest semantycznie właściwym miejscem dla metadanych strony. Wymaga dodania parametru
`deployedAt` do sygnatury `renderPage({ env, on, deployedAt })`. Wartość jest escapowana przez istniejącą
funkcję `escape()`. Data renderowana tylko gdy `on('show_last_deployed')` zwraca `true` i `deployedAt` nie jest
puste.

### Przepływ danych

```
npm run build (przed startem aplikacji)
  → zapisuje config/build.json { "deployedAt": "YYYY-MM-DD" }

createServer() (startup)
  → readBuildInfo() czyta config/build.json → { deployedAt } (puste przy braku lub błędzie)

GET /
  → readFlags(env) → flags
  → visitorOf(req) → visitor
  → renderPage({ env, on: (key) => isOn(flags, key, visitor.id), deployedAt })
     ↳ on('show_last_deployed') = true i deployedAt niepuste
        → <footer>Ostatnie wdrożenie: <time>YYYY-MM-DD</time></footer>
     ↳ w przeciwnym razie
        → stopka bez daty
```

### Zmiany w komponentach

| Komponent | Zmiana |
|---|---|
| `config/build.json` | Nowy plik generowany przez `npm run build`; pole `deployedAt` (ISO 8601). Nie jest commitowany. |
| `package.json` | Nowy skrypt `build` zapisujący `config/build.json` z bieżącą datą. |
| `.gitignore` | Wpis `config/build.json` (DEC-0003). |
| `src/server.js` | Odczyt `config/build.json` przy starcie; przekazanie `deployedAt` do `renderPage`. |
| `src/page.js` | Nowy parametr `deployedAt`; data w istniejącej stopce za flagą `show_last_deployed`. |
| `public/style.css` | Styl daty w istniejącej stopce (bez nowego komponentu). |
| `config/flags.prod.json` | Wpis `"show_last_deployed": { "enabled": false, "rollout": 0 }` (domyślnie wyłączony). |
| `config/flags.test.json` | Wpis `"show_last_deployed": { "enabled": true, "rollout": 100 }` (widoczny w testach). |
| `test/page.test.js` | Nowe testy TDD: flaga on → stopka z datą; flaga off → brak daty; puste `deployedAt` → brak daty; escape daty. |
| `test/server.test.js` | Nowe testy: brak `config/build.json` albo błędny plik → strona 200 bez daty. |

## Doświadczenie

### Przepływy

#### F1 — tor nominalny: odwiedzający widzi datę wdrożenia (flaga ON)

Odwiedzający wchodzi na stronę. Serwer odczytuje flagi; `show_last_deployed` jest włączona. `deployedAt` z
`config/build.json` jest niepuste. `renderPage` wstawia datę w stopce. Odwiedzający widzi „Ostatnie wdrożenie:
RRRR-MM-DD”.

#### F2 — flaga wyłączona (tor przed rollout, domyślny)

Odwiedzający wchodzi na stronę. Serwer odczytuje flagi; `show_last_deployed` jest wyłączona. `renderPage`
renderuje stronę bez daty. Stopka bez daty — tor nominalny przed R1, nie jest stanem błędu.

#### F3 — błąd odczytu `config/build.json`

Odwiedzający wchodzi na stronę. Flaga `show_last_deployed` jest włączona. `config/build.json` jest niedostępny
lub błędny. Stopka bez daty, strona działa normalnie (HTTP 200), nigdy HTTP 500 (FR-003, DEC-0005).

#### F4 — brak pola `deployedAt` w `build.json`

Odwiedzający wchodzi na stronę. Flaga ON, `config/build.json` wczytany poprawnie, ale brak pola `deployedAt`
lub wartość pusta. Stopka bez daty, strona działa normalnie (DEC-0005).

### Ramki per wymaganie i stan

| Wymaganie | Ścieżka | Stan | Ramka | Uwagi |
|---|---|---|---|---|
| US-1 | Odwiedzający sprawdza aktualność strony | idle | brak | Bez Figmy (D-F3). Istniejąca stopka z „Ostatnie wdrożenie: RRRR-MM-DD” (flaga ON, `deployedAt` niepuste). |
| US-1 | Odwiedzający sprawdza aktualność strony | success | nie dotyczy | Strona SSR bez asynchronicznej akcji użytkownika; wartość dostarcza stan idle. |
| US-1 | Odwiedzający sprawdza aktualność strony | server_error | brak | Bez Figmy (D-F3). `config/build.json` niedostępny lub błędny → stopka bez daty, HTTP 200. |
| US-1 | Odwiedzający sprawdza aktualność strony | empty | brak | Bez Figmy (D-F3). Brak lub puste `deployedAt` → stopka bez daty. |

## Rozstrzygnięcia z bramek

- `config/build.json` gitignorowany, generowany przez skrypt w repo (`npm run build`) przed startem aplikacji, bez
  commitowania placeholdera; `sdlc deploy` tylko zakłada GitHub Deployment (B2, DEC-0003).
- Format daty: ISO `RRRR-MM-DD` (B2, DEC-0003).
- Brak lub błąd `config/build.json` albo puste `deployedAt`: stopka bez daty, nigdy HTTP 500 (B2, DEC-0003;
  design-review, DEC-0005).
- Właściciel flagi `show_last_deployed`: dbqm45 (B3, DEC-0004).
- Plik Figmy: brak (repo próbne, D-F3 otwarta); rozszerzenie istniejącej stopki w `src/page.js` i
  `public/style.css`, bez nowego komponentu (design-review, DEC-0005).
