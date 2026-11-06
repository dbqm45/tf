---
artifact: design
phase: design
status: proposed
version: 1
author: natalia
created: 2026-11-05
updated: 2026-11-05
inputs: [docs/project/changes/CHG-3/requirements.md, docs/project/changes/CHG-3/architecture.md, docs/project/changes/CHG-3/decisions.md]
change: CHG-3
source: PRB-27
source_reported_at: 2026-11-03
---
# Projekt zmiany CHG-3

## TL;DR
Jeden nowy element: akapit „Wdrożenia w ostatnich 7 dniach: N” w `<main>`, zaraz po akapicie „Środowisko”, widoczny
tylko przy fladze `deploy_counter` (test: on, prod: off). Bez nowego komponentu, bez JS klienta, bez zmiany CSS.
Przy fladze off strona jest bajt w bajt taka jak dziś (CHG-3/D2, DEC-0013).

Plik Figmy: brak — repo próbne nie ma projektu w Figmie (jak w CHG-1); stany opisane tekstem. Tryb: dopasowanie ramek
projektanta; szkicu ramek agent nie robi bez prośby człowieka.

## Ustalenia z bramek (nie do ponownego pytania)
- Etykieta: dosłowny tekst „Wdrożenia w ostatnich 7 dniach: N”, bez nazwy środowiska; nieznane `?env=` liczy dla
  środowiska domyślnego (CHG-3/D3, DEC-0014).
- Widoczność: każdy odwiedzający tam, gdzie flaga on; bez dodatkowej autoryzacji (CHG-3/D2, DEC-0013).
- Licznik zero jest widoczny, nie ukryty (E-02C).

## Przepływy

#### F1 — tor nominalny: flaga ON
Odwiedzający otwiera `/`. Serwer liczy wdrożenia środowiska z ostatnich 7 × 24 h (UTC). Pod „Środowisko: test”
pojawia się „Wdrożenia w ostatnich 7 dniach: 3”.

#### F2 — flaga OFF (prod na start)
Odwiedzający otwiera `/`. Strona bez licznika, identyczna z dzisiejszą. Tor domyślny na prod, nie błąd.

#### F3 — zero wdrożeń w oknie
Flaga ON, brak wdrożeń w oknie albo brak pliku bazy. Strona pokazuje „Wdrożenia w ostatnich 7 dniach: 0”. Licznika nie
ukrywamy: „0” jest informacją o tempie (E-02C, E-04A).

#### F4 — uszkodzona baza
Flaga ON, plik bazy nie jest SQLite. Serwer zwraca istniejący błąd 500 `{"error":"internal error"}`; szczegóły tylko
w logu (E-04B). Nie powstaje nowy ekran błędu.

### Układ i dostępność
- Miejsce: `<main>`, po akapicie „Środowisko”, przed `</main>`; kolejność czytania = kolejność w DOM.
- Element: `<p data-flag="deploy_counter">`, bez nowej klasy i bez CSS — dziedziczy styl akapitu „Środowisko”.
- N jako zwykły tekst w zdaniu (nie sama liczba w ikonie ani kolorze); kontrast i rozmiar jak reszta strony.
- Brak interakcji, brak stanu ładowania (render po stronie serwera), brak JS klienta (CSP bez zmian).
- Wszystkie wartości przez `escape` (NF-001).

## Ramki per wymaganie i stan

| Wymaganie | Ścieżka | Stan | Ramka | Uwagi |
|---|---|---|---|---|
| US-01 | Odwiedzający widzi tempo wdrożeń | idle | brak | Bez Figmy. Opis: akapit „Wdrożenia w ostatnich 7 dniach: N” pod „Środowisko”, flaga ON, N > 0 (F1, E-02A). |
| US-01 | Odwiedzający widzi tempo wdrożeń | success | nie dotyczy | Strona SSR bez asynchronicznej akcji; wartość dostarcza stan idle. |
| US-01 | Odwiedzający widzi tempo wdrożeń | empty | brak | Bez Figmy. „Wdrożenia w ostatnich 7 dniach: 0” widoczne, nie ukryte (F3, E-02C, E-04A). |
| US-01 | Odwiedzający widzi tempo wdrożeń | server_error | nie dotyczy | Odpowiedź 500 JSON `{"error":"internal error"}` istniejącej obsługi błędów; brak ekranu do zaprojektowania (F4, E-04B). |
| US-01 | Odwiedzający widzi tempo wdrożeń | permission_denied | nie dotyczy | Brak autoryzacji widoczności (CHG-3/D2, DEC-0013); flaga off = brak elementu, bez komunikatu (F2, E-02B). |

## Pytania do bramki
- Właściciel aplikacji sdlc-proba: ramki idle i empty nie mają ramki w Figmie, bo repo próbne nie ma projektu — czy akceptujesz opis tekstowy w tym dokumencie zamiast ramek (jak w CHG-1/DEC-0005), czy dostarczysz ramki projektanta?
