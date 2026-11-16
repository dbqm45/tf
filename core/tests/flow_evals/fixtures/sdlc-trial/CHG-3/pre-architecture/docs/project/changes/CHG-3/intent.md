---
artifact: intent
phase: discovery
status: proposed
version: 1
author: pdi
created: 2026-11-03
updated: 2026-11-03
inputs: []
change: CHG-3
source: PRB-27
source_reported_at: 2026-11-03
---
# Zamiar zmiany CHG-3

## TL;DR
Dodajemy na stronie głównej licznik „Wdrożenia w ostatnich 7 dniach: N" za flagą `deploy_counter` (off na prod na start).
Liczbę wylicza serwer z tabeli `deployments`. Przyjęcie zgłoszenia PRB-27 rozstrzyga CHG-3/D1 (DEC-0012).

## Problem
Właściciel aplikacji sdlc-proba nie widzi na stronie głównej, ile wdrożeń było w ostatnich 7 dniach w danym
środowisku. Żeby to ustalić, pyta endpoint `/deployments` i liczy ręcznie. Skutek: nie widać tempa wdrożeń bez
narzędzi, a to prosta miara, o którą pytamy przy każdym przeglądzie (źródło: zgłoszenie PRB-27, dane od zgłaszającego).

Stan obecny (sprawdzony w kodzie): `src/server.js` udostępnia `GET /deployments?env=` ze stronicowaniem
(domyślnie 20, maks. 100 na stronę; `src/deployments.js`). Nie ma funkcji liczącej wdrożenia w oknie czasu.
Flagi czyta `readFlags`/`isOn` z `config/flags.{test,prod}.json`; `renderPage` dostaje `on(key)`.

## Warianty
Pomysł zgłaszającego to wariant A, nie wymaganie.

| Wariant | Koszt | Za | Przeciw |
|---|---|---|---|
| A. Licznik renderowany po stronie serwera: nowa funkcja `countDeployments(file, env, since)` (jedno zapytanie `COUNT` po indeksie `env, julianday(deployed_at)`), wynik w `renderPage`, za flagą `deploy_counter`; środowisko z `?env=` (domyślnie `APP_ENV`) | mały: 1 funkcja, zmiana `page.js` i `server.js`, flaga w obu plikach flag, testy | dokładna liczba; bez JS po stronie klienta (CSP `default-src 'self'` zostaje); jedno źródło prawdy z `/deployments`; indeks już jest | `?env=` trzeba walidować jak w `/deployments` (lista `ENVIRONMENTS`); strona zależy od bazy wdrożeń (brak pliku = 0) |
| B. Licznik w przeglądarce: skrypt pobiera `/deployments` i liczy | mały–średni: nowy plik JS, zmiana CSP lub plik statyczny | brak zmian po stronie serwera strony | błędna liczba przy więcej niż 100 wdrożeniach w oknie albo przy stronicowaniu; wymaga JS i zmiany routingu plików statycznych (serwer podaje tylko `/style.css`); wiele zapytań |
| C. Nowy endpoint `/deployments/count?env=&days=7` i licznik renderowany z niego | średni: endpoint, kontrakt, testy, dokumentacja API | liczbę da się odczytać także poza stroną | większa powierzchnia API niż wymaga zgłoszenie (YAGNI); nikt o endpoint nie prosił |
| D. Nic nie zmieniać; opisać w README użycie `/deployments` | zerowy | brak ryzyka | problem zostaje: ręczne liczenie, brak miary na stronie |

## Wybrany wariant
**A.** Mieści się w obecnej architekturze (strona + odczyt z tabeli `deployments`), zwraca dokładną liczbę (B jej nie
gwarantuje), nie rozszerza API (C). Ryzyko regresji ogranicza flaga `deploy_counter`: `enabled: false` na prod na
start, włączona na test. Zakres decyzji triażu: CHG-3/D1 (DEC-0012).

Ustalenia robocze (zmieniają się, jeśli człowiek odpowie inaczej na pytania niżej):
- **[propozycja]** Okno „ostatnie 7 dni" to 7 × 24 h wstecz od chwili renderowania strony (UTC), nie dni kalendarzowe.
- **[propozycja]** Środowisko: `?env=` (tylko wartości z `ENVIRONMENTS`), domyślnie bieżące `APP_ENV`. Nieznane `env` → komunikat
  jak w `/deployments` albo wartość domyślna (do potwierdzenia w fazie requirements).
- **[propozycja]** Flaga za mechanizmem `readFlags`/`isOn` jak `welcome_banner`; etapy rolloutu na prod w `release.yaml` (faza plan).

## Metryki sukcesu
- Z włączoną flagą strona główna pokazuje „Wdrożenia w ostatnich 7 dniach: N", gdzie N równa się liczbie wierszy
  `deployments` dla wybranego środowiska z `deployed_at` w oknie 7 dni — dla wszystkich N, także > 100 (próg: 0 różnic
  względem zapytania wprost do bazy w teście).
- Z wyłączoną flagą strona jest bajt w bajt taka jak dziś (próg: istniejące testy strony przechodzą bez zmian).
- Właściciel nie musi już wołać `/deployments` i liczyć ręcznie: cel przy przeglądzie wpływu — brak takich zapytań
  ręcznych w kolejnym przeglądzie **[założenie: sprawdzane pytaniem do właściciela, bo repo nie zbiera tej miary]**.

## Poza zakresem
- Nowy endpoint API i zmiany kontraktu `/deployments` (wariant C).
- Wykres, trend, porównanie okresów, konfigurowalne okno (inne niż 7 dni).
- Licznik rollbacków i innych metryk ShipScope.
- Zmiany w zapisie wdrożeń (`scripts/record-deployment.js`) i w schemacie bazy.
- Włączenie flagi na prod (zapada w etapach rolloutu, nie w tej fazie).

## Ograniczenia
- Brak nowych zależności (decyzja DL4: Node bez zależności, `node:sqlite`).
- CSP `default-src 'self'` zostaje bez zmian (bez skryptów inline).
- Strona nie może się wysypać, gdy brak pliku bazy wdrożeń (jak `listDeployments`: brak pliku = 0 wdrożeń).
- Pozostałe ograniczenia (budżet, termin, urządzenia) — brak w zgłoszeniu, zob. pytania do bramki.

## Kiedy to porażka
Brak w zgłoszeniu; człowiek podaje to w odpowiedzi na pytanie 2 poniżej. Robocze kryterium techniczne **[propozycja]**:
licznik pokazuje inną liczbę niż `/deployments` dla tego samego środowiska i okna albo spowalnia stronę głównej.

## Powiązania
- Zgłoszenie PRB-27; triaż: CHG-3/D1 (DEC-0012).
- Kod: `src/deployments.js`, `src/server.js`, `src/page.js`, `src/flags.js`, `config/flags.{test,prod}.json`.
- Odczyt `/deployments` (istniejący, bez zmian); wcześniejsza zmiana CHG-1 (inny temat, brak zależności znanej z repo).

## Pytania do bramki
- Właściciel aplikacji sdlc-proba: co oznacza „ostatnie 7 dni" — 7 × 24 h wstecz od chwili wyświetlenia strony (UTC) czy 7 dni kalendarzowych, i czy liczą się wszystkie wdrożenia ze środowiska, czy tylko udane?
- Właściciel aplikacji sdlc-proba: kiedy ta zmiana jest porażką, nawet jeśli licznik działa (np. strona wolniejsza niż próg, liczba rozbieżna z /deployments, widoczna publicznie na prod)?
- Właściciel aplikacji sdlc-proba: czy licznik ma być widoczny każdemu odwiedzającemu, czy wystarczy, że widzi go właściciel (np. tylko na test, na prod po włączeniu flagi)?
