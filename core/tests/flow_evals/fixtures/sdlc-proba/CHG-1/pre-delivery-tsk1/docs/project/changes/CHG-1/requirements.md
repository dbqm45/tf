---
artifact: requirements
phase: requirements
status: proposed
version: 1
author: ewa
created: 2026-10-30
updated: 2026-10-30
inputs: [docs/project/changes/CHG-1/intent.md]
change: CHG-1
source: PRB-1
source_reported_at: 2026-10-30
---
# Wymagania zmiany CHG-1

## Historia użytkownika

**US-01** — Odwiedzający widzi datę wdrożenia  
Jako odwiedzający, gdy flaga `show_last_deployed` jest włączona, widzę datę ostatniego
wdrożenia w stopce strony, żeby wiedzieć, jak aktualne są wyświetlane treści.

## Wymagania funkcjonalne

### FR-001 — Artefakt daty wdrożenia

Plik `config/build.json` zawiera pole `deployed_at` z datą wdrożenia w formacie ISO 8601
(`RRRR-MM-DD`). Plik generuje krok wdrożenia; nie jest źródłem danych dla środowiska
lokalnego dewelopera (szczegóły: pytanie P-01 w bramce).

**Kryteria akceptacji:**

- **E-01A** — plik wygenerowany przez krok wdrożenia zawiera pole `deployed_at` spełniające
  wzorzec `^\d{4}-\d{2}-\d{2}$`:
  ```
  wejście: krok wdrożenia uruchomiony dla commita z 2026-10-30
  oczekiwany wynik: config/build.json → { "deployed_at": "2026-10-30" }
  ```

### FR-002 — Data wdrożenia w stopce za flagą

Gdy flaga `show_last_deployed` jest włączona dla odwiedzającego, `GET /` zwraca HTML
zawierający datę wdrożenia z pola `deployed_at` pliku `config/build.json` w stopce strony.
Gdy flaga jest wyłączona, HTML nie zawiera elementu z datą wdrożenia.

**Kryteria akceptacji:**

- **E-02A** — flaga ON, plik obecny:
  ```
  wejście: config/build.json → { "deployed_at": "2026-10-30" }, flaga show_last_deployed ON
  oczekiwany wynik: GET / → 200, HTML zawiera "2026-10-30" w elemencie stopki
  ```

- **E-02B** — flaga OFF:
  ```
  wejście: config/build.json → { "deployed_at": "2026-10-30" }, flaga show_last_deployed OFF
  oczekiwany wynik: GET / → 200, HTML nie zawiera elementu z datą wdrożenia
  ```

- **E-02C** — eskapowanie wartości (NF-001):
  ```
  wejście: config/build.json → { "deployed_at": "<xss>" }, flaga show_last_deployed ON
  oczekiwany wynik: GET / → 200, HTML zawiera "&lt;xss&gt;", nie surowy "<xss>"
  ```

### FR-003 — Odporność na brak artefaktu [propozycja]

Gdy `config/build.json` nie istnieje lub nie zawiera pola `deployed_at`, `GET /` zwraca
200 i HTML bez elementu z datą wdrożenia (serwer nie przerywa działania).
Szczegóły: pytanie P-03 w bramce.

**Kryteria akceptacji:**

- **E-03A** — brak pliku:
  ```
  wejście: config/build.json nie istnieje, flaga show_last_deployed ON
  oczekiwany wynik: GET / → 200, HTML bez elementu z datą wdrożenia
  ```

- **E-03B** — brak pola:
  ```
  wejście: config/build.json → {}, flaga show_last_deployed ON
  oczekiwany wynik: GET / → 200, HTML bez elementu z datą wdrożenia
  ```

## Wymagania jakości

**NF-001 — Eskapowanie HTML (musi)**  
Wartość `deployed_at` jest eskpapowana przed wstawieniem do HTML — tak jak `env` w
istniejącej funkcji `escape` w `src/page.js`. Weryfikacja: E-02C.

**NF-002 — Format daty wyświetlanej (musi, do potwierdzenia)**  
Data wyświetlana w formacie ISO `RRRR-MM-DD`. Szczegóły: pytanie P-02 w bramce.

## Priorytety

| ID | Opis | Waga | Wydanie |
|---|---|---|---|
| FR-001 | Artefakt daty wdrożenia (`config/build.json`) | musi | R1 |
| FR-002 | Data w stopce za flagą `show_last_deployed` | musi | R1 |
| FR-003 | Odporność na brak artefaktu [propozycja] | powinno | R1 |
| NF-001 | Eskapowanie wartości `deployed_at` w HTML | musi | R1 |
| NF-002 | Format wyświetlania: ISO `RRRR-MM-DD` | musi | R1 |

## Pytania do bramki

- [właściciel] P-01: Czy `config/build.json` ma być gitignorowany i generowany wyłącznie przez krok wdrożenia (`uv run sdlc deploy`), czy dopuszczalne jest commitowanie go z datą lokalnego budowania jako placeholdera dla dewelopera? (przeniesione z intent.md; wpływa na FR-001 i środowisko lokalne)
- [właściciel] P-02: Jaki format wyświetlania daty jest oczekiwany dla użytkownika: ISO `RRRR-MM-DD` (jak w pliku) czy data sformatowana po polsku, np. „30 paź 2026"? (wpływa na NF-002 i implementację `renderPage`)
- [właściciel] P-03: Czy zachowanie opisane w FR-003 (cicha nieobecność daty przy braku `config/build.json`) jest właściwe, czy oczekiwany jest tekst zastępczy (np. „brak danych wdrożenia") albo błąd 500?
