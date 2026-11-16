# Rejestr ryzyk i UX niepewności

## Rejestr ryzyk funkcji AI
| Ryzyko | Scenariusz | Środek (przykłady) |
|---|---|---|
| halucynacja | model podaje nieprawdziwy fakt z pewnością | oparcie na źródłach z cytatem, odmowa przy braku danych, ewaluacja zgodności |
| uprzedzenia | gorsze wyniki dla grupy użytkowników lub języka | ewaluacja po kawałkach (język, segment), przegląd przykładów |
| bezpieczeństwo treści | szkodliwa lub niestosowna odpowiedź | filtry, odmowy, zbiór adwersaryjny, eskalacja |
| prywatność | dane osobowe w promptach, logach lub danych dostawcy | minimalizacja, anonimizacja, umowa powierzenia (arch-privacy-compliance) |
| prompt injection | treść z zewnątrz zmienia zachowanie modelu | separacja danych i instrukcji, minimalne uprawnienia narzędzi (arch-threat-modeling) |
| zależność od dostawcy | zmiana wersji, ceny lub wycofanie modelu | przypięta wersja, ewaluacja przy zmianie, plan wyjścia |
| drift | jakość spada, bo zmieniły się dane lub język użytkowników | próbki z ruchu, alerty, cykliczna ewaluacja |
| klasa regulacyjna | funkcja trafia w kategorię o obowiązkach | klasyfikację i obowiązki ustala ai-governance-compliance |

Każdy wiersz: prawdopodobieństwo, skutek, właściciel, termin przeglądu. Ryzyko bez właściciela nie istnieje.

## UX niepewności i człowiek w pętli
1. **Oczekiwania:** powiedz na starcie, co funkcja robi i że się myli; nazwij wynik „propozycją”, jeśli tak jest.
2. **Pewność:** pokazuj ją tylko, gdy jest skalibrowana (zmierzona na zbiorze); inaczej lepsze są źródła, cytaty
   i możliwość sprawdzenia. Surowa liczba „87%” bez kalibracji wprowadza w błąd.
3. **Stopień autonomii** wg kosztu błędu: sugestia → akcja po zatwierdzeniu → akcja z możliwością cofnięcia → automat.
4. **Fallback:** ścieżka bez AI (formularz, kontakt z człowiekiem) zawsze dostępna i wyraźna.
5. **Korekta:** edycja wyniku jednym gestem, „zły wynik” z powodem; poprawki trafiają do przeglądu i do zbioru ewaluacyjnego
   (za zgodą i z uwzględnieniem prywatności).
6. **Porażka:** komunikat o błędzie mówi, co się stało i co dalej; model nie przeprasza w nieskończoność.
Wytyczne: Microsoft HAX (cztery fazy: początek, w trakcie, gdy AI się myli, z czasem) i Google PAIR (modele mentalne,
wyjaśnialność i zaufanie, informacja zwrotna i kontrola, błędy). Teksty komunikatów: ux-content-design; przepływy: ux-feature-design.
