# Aplikacja z AI: awarie poza modelem

Ewaluacje (ai-evals) oceniają odpowiedź modelu. Duża część awarii aplikacji z AI dzieje się wokół niego: w UI,
sesji, routingu, narzędziach, integracjach, danych i rozliczeniach. Każda klasa niżej ma test, który da się
zautomatyzować albo przejść ręcznie przed wydaniem. Klasy pochodzą z przeglądu S. Gundetiego („9 AI Application
Failures That Aren't Model Problems”, 2026-10); przykłady autora są uogólnione — traktuj je jako klasy awarii.

| # | Klasa | Test |
|---|---|---|
| 1 | UI pokazuje sukces mimo błędu API | wymuś 403, 500, timeout i wygasły token; porównaj ekran z odpowiedzią serwera; akcja naprawcza pasuje do przyczyny („zaloguj ponownie”, a nie „spróbuj później”) |
| 2 | Długie zadanie agenta a zerwane połączenie | rozłącz klienta w trakcie, pozwól zadaniu skończyć się w tle, wróć: widać prawdziwy stan końcowy, nie wieczne „pracuję…” |
| 3 | Routing modeli | pierwsza trywialna wiadomość nie przypina sesji do taniej trasy; wyłączony model nie jest dalej serwowany; fallback zgodny z polityką i widoczny dla użytkownika |
| 4 | Kontrakt narzędzi | pusty, zniekształcony, zdublowany i za duży wynik narzędzia; przerwane oczekujące wywołanie (agent pyta, użytkownik pisze nową wiadomość); pętla bez postępu (podniesienie limitu rekursji to objaw, nie naprawa); wartości przepisywane przez model (URL, ID, tokeny) traktowane jako niezaufane |
| 5 | Text-to-SQL | nieistniejące kolumny, identyfikatory ze spacjami; trzy różne wyniki rozróżnione dla użytkownika: puste trafienie, błąd zapytania, metryka niezdefiniowana (zero, które „wygląda jak fakt”) |
| 6 | Integracje | konta osobiste i firmowe, odwołany token, lista dłuższa niż jedna strona, link do pliku otwarty spoza aplikacji; jawne, czyją tożsamością działa agent |
| 7 | Migracje | testy na kontach z danymi sprzed zmiany, nie tylko na świeżych |
| 8 | Izolacja | API wywołane wprost jako użytkownik o niskich uprawnieniach; pamięć i cache nie przekraczają granic użytkownika i najemcy; odebranie roli działa od razu |
| 9 | Koszty | zużycie uzgodnione z surowymi rekordami dostawcy per wywołanie; tury dłuższe niż okno synchronizacji i sesje przez północ; zmiana cennika nie przepisuje historii |

Priorytet nadajesz jak każdemu ryzyku (SKILL.md, „Priorytet”): skutek × prawdopodobieństwo. Klasy 1, 4 i 8 zwykle są
najwyżej — widoczny fałszywy sukces, niekontrolowane działanie narzędzia, wyciek między użytkownikami.

Powiązane: ocena odpowiedzi i trajektorii agenta — ai-evals; stany widoku (ładowanie, błąd, pusto, dane) —
fe-architecture; uprawnienia per zasób — be-auth-security; uprawnienia w indeksie RAG — ai-rag.
