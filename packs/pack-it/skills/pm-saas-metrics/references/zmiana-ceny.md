# Ocena zmiany ceny

1. **Cel** — przychód, marża, przejście na wyższy plan, wyrównanie do wartości? Jedna miara sukcesu i metryki
   ochronne (churn, konwersja z okresu próbnego, liczba zgłoszeń).
2. **Kogo dotyczy** — nowi klienci, obecni, oba; plany i segmenty; liczba klientów i MRR w każdej grupie.
3. **Scenariusze** — dla podwyżki o p: nowy MRR = MRR × (1 + p) × (1 − dodatkowy churn). Próg opłacalności:
   dodatkowy churn < p / (1 + p) (np. podwyżka 20% opłaca się, dopóki dodatkowo odejdzie mniej niż ok. 16,7%
   przychodu grupy). Pokaż trzy scenariusze churnu (optymistyczny, bazowy, pesymistyczny) i ich źródło.
4. **Test przed zmianą dla wszystkich** — najpierw nowi klienci (cennik A/B albo zmiana z datą i porównanie
   kohort), potem obecni; badania gotowości do zapłaty (np. Van Westendorp) jako sygnał, nie dowód.
5. **Obecni klienci** — okres ochronny ceny („grandfathering”) albo zapowiedź z wyprzedzeniem; warunki umów
   i regulaminu (prawo do zmiany ceny, okres wypowiedzenia); komunikat z wartością, nie tylko kwotą.
6. **Po zmianie** — NRR, GRR, konwersja i zgłoszenia co miesiąc przez 3–6 miesięcy na kohortach przed i po.
   Implementacja w systemie rozliczeń: be-billing-subscriptions.
