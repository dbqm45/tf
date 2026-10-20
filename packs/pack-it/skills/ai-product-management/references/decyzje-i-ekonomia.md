# Decyzje i ekonomia funkcji AI

## Wybór narzędzia: reguła, ML, LLM
| Sytuacja | Narzędzie | Uwaga |
|---|---|---|
| logika zapisywalna, audytowalna, prawo wymaga wyjaśnienia | reguła | tania, deterministyczna; zacznij tu |
| są etykiety, wąskie zadanie, stały kształt danych (scoring, klasyfikacja) | klasyczny ML | wymaga danych i utrzymania modelu |
| otwarty tekst, streszczanie, generowanie, wiele zadań naraz | LLM | niedeterministyczny; wymaga ewaluacji i ochrony |
| mieszane | reguły dla łatwej większości, LLM dla reszty | zmniejsza koszt i powierzchnię błędów |

Test koszt błędu × nosiciel: dla każdego typu błędu wpisz skutek, kto go ponosi (klient, pracownik, firma),
czy da się go wykryć i cofnąć. Błąd nieodwracalny i niewykrywalny wymaga człowieka przed skutkiem.

## Ekonomia jednostkowa
- **Koszt na udane zadanie** = (koszt wywołań modelu z ponowieniami + wyszukiwanie + sędzia/ocena + czas człowieka
  weryfikującego) / liczba zadań ukończonych poprawnie. Koszt na zapytanie zaniża obraz.
- Ceny tokenów i limity pobierz z cennika dostawcy w dniu liczenia (zmieniają się); wynik oznacz datą.
- Porównaj z kosztem dziś (czas × stawka) i z wartością (przychód, retencja). Wrażliwość: policz wariant z
  2× dłuższym kontekstem i 2× większym ruchem.
- Dźwignie kosztu: mniejszy model do łatwych przypadków, cache promptu, krótszy kontekst, reguły przed modelem
  (core-cost-control, ai-prompt-engineering).
- Sprzężenie celów: wyższa jakość zwykle = droższy model lub więcej prób = większe opóźnienie. Zapisz kolejność ustępowania.

## Kup, zbuduj, API
Szczeble: gotowy produkt → API z własnym promptem i kontekstem (ai-rag) → dostrojenie (ai-fine-tuning) → własny model.
Dla każdego: koszt wejścia, czas do pierwszej wartości, zależność od dostawcy i jej plan wyjścia, gdzie trafiają dane,
kontrola nad zmianami modelu (wycofanie wersji przez dostawcę = regresja bez zmiany w kodzie).
Wybór architektury: arch-ai-solutions.

## Dane
Tabela: rodzaj danych (przykłady do ewaluacji, etykiety, treści źródłowe) | czy mamy | właściciel | podstawa użycia
(RODO: arch-privacy-compliance) | świeżość | koszt przygotowania. Zbiór ewaluacyjny od realnych zgłoszeń ma pierwszeństwo.
