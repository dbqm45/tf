# Dochodzenie z wielu źródeł dowodów

Żadne pojedyncze źródło nie wystarcza. W raporcie wypisz, co wniósł każdy kanał.

## Zgłoszenie od użytkownika
Jedno zdanie bez stack trace („zapis notatki nie działa”) rozpisujesz na pytania, nie na diagnozę: kroki odtworzenia,
zakres (co działa, co nie), częstotliwość, od kiedy, podejrzany obszar.

## Od czego zacząć
| Objaw | Pierwsze źródło |
|---|---|
| wyjątek, 5xx, crash | monitoring błędów (stack trace, ślad zdarzeń przed błędem, kontekst żądania) |
| „sukces”, ale efekt nie zachodzi (200, dane bez zmian) | monitoring + logi aplikacji (warn/error bez propagacji) |
| problem tylko w UI, API zdrowe | przeglądarka: konsola, ruch sieciowy, drzewo dostępności |
| padający test | wynik testu i stack trace, potem kod |
| losowe albo tylko na produkcji | monitoring (częstość, wersje, użytkownicy), logi z identyfikatorem żądania |

## Kanały i co dają
- **Monitoring błędów** (Sentry lub odpowiednik, także przez MCP): miejsce i nazwa błędu, stos, zdarzenia przed błędem.
  Ostrzeżenie z konsoli trafi tam tylko przy włączonym przechwytywaniu konsoli — to zużywa limit zdarzeń; przy ruchu
  zawęź do błędów albo zgłaszaj wybrane przypadki jawnie.
- **Logi aplikacji/platformy** (z filtrem po komunikacie): skala — pojedynczy incydent czy każde wywołanie.
- **Przeglądarka** (Playwright: konsola, lista żądań, szczegóły jednego żądania): oddziela front od backendu.
- **Kod**: przyczyna źródłowa — czytany dopiero z hipotezą z poprzednich kanałów.

## Sygnał wizualny (tylko błędy w pikselach)
Nakładanie się, z-index, ucięty tekst, animacja — konsola i sieć milczą. Zrzut ekranu i otwarte pytanie do modelu
z obrazem; odpowiedź to hipoteza (modele mylą położenie i potrafią zgłosić fałszywy alarm albo przeoczyć problem).
Regresję wizualną w testach sprawdzasz narzędziami deterministycznymi (qa-regression), nie modelem.

## Test odtwarzający
Pada z właściwego powodu i sprawdza **trwały skutek** (wiersz w bazie, plik, wysłaną wiadomość), nie status odpowiedzi.
Zostaje jako strażnik regresji.

## Połknięty błąd — poprawka w dwóch częściach
1. **Przestań ukrywać:** zwróć błąd (5xx albo kod domenowy), nie „sukces” z danymi z pamięci.
2. **Napraw samą operację.** Sama część 1 zamienia ciche 200 w widoczne 500 — dopiero obie dają działanie.

Przeszukaj kod pod ten sam wzorzec (obsługa błędu, która loguje i zwraca sukces) — zwykle jest kilka kopii
(eng-clean-code, sekcja „Błędy”).

## Weryfikacja = lustro dochodzenia
Każdy kanał, który pokazał problem, musi pokazać jego brak: test zielony, brak nowych zdarzeń w monitoringu, brak
komunikatu w logach, poprawny przebieg w przeglądarce.

## Dlaczego bramki tego nie złapały
Dopisz analizę ucieczki (qa-test-design, `strategia-i-plan-testow.md`): ryzyko nazwane w strategii testów, ale bez
zbudowanej fazy testów, to jeszcze nie bramka.

## Hook pokazał padający test
Trywialne (format, import, typ) agent naprawia sam. Test logiki biznesowej pada po 1–2 próbach poprawki → stop i ta
procedura (albo osobna zmiana); nie poprawiasz kodu „na rozum” do zielonego (eng-local-quality-gates).

## Źródła
- Kurs 10xDevs, ed. 3 (2026), moduł 3, lekcja 5 (debugowanie z monitoringiem, logami i przeglądarką) — materiał
  szkoleniowy (dostęp 2026-10-09).
Opisane własnymi słowami.
