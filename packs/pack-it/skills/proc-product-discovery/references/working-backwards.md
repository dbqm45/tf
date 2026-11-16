# Od klienta wstecz: komunikat prasowy, epik jako hipoteza, roadmapa według wyników

## Komunikat prasowy i FAQ przed budową
Piszesz dokument z dnia premiery, zanim powstanie kod — sprawdzian, czy wiemy, dla kogo i po co.
**Komunikat (najwyżej 1 strona, język klienta, bez żargonu):**
1. Tytuł — nazwa i korzyść dla konkretnego klienta.
2. Podtytuł — kto i co zyskuje, jednym zdaniem.
3. Problem — jak klient radzi sobie dziś i ile go to kosztuje (z dowodem z odkrywania).
4. Rozwiązanie — co się zmienia dla klienta, nie jak to działa w środku.
5. Cytat z firmy — dlaczego to robimy.
6. Jak zacząć — pierwszy krok klienta.
7. Cytat klienta — jak opisałby korzyść (hipoteza do sprawdzenia w rozmowach).
**FAQ zewnętrzne** — pytania klientów (cena, migracja, bezpieczeństwo, czego nie robi).
**FAQ wewnętrzne** — pytania zespołu i zarządu: kto jest klientem i ilu ich jest, jaki wynik i jak go zmierzymy,
koszt i zespół, największe ryzyka w czterech kategoriach (wartość, użyteczność, wykonalność, opłacalność), co
musi być prawdą, czego nie zrobimy, co przerwie projekt.
**Test**: 5–8 rozmów z klientami docelowymi na podstawie komunikatu (czy chcieliby, co by zmienili, ile by
zapłacili) i przegląd FAQ wewnętrznego z inżynierią i finansami. Dokument przepisujesz, aż odpowiedzi się
ustabilizują; dopiero potem zakres i plan.

## Epik jako hipoteza
```
Wierzymy, że [rozwiązanie] dla [klient] rozwiąże [problem / szansa].
Poznamy to po [wynik i metryka: wartość wyjściowa → docelowa] w [czas].
Wczesne sygnały: [metryki wiodące po 2–4 tygodniach].
Przerywamy albo zmieniamy kierunek, jeśli [kryterium przerwania].
Najpierw sprawdzimy [najsłabsze ważne założenie] przez [najtańszy test].
```
Epik bez metryki i bez kryterium przerwania to lista prac, nie hipoteza. Po wydaniu porównujesz wynik z hipotezą
i zapisujesz decyzję (kontynuować, zmienić, wycofać).

## Roadmapa według wyników
Zamiast funkcji z datami na rok — trzy kolumny:
- **Teraz** — problemy i wyniki, nad którymi zespół pracuje (z metryką i znanym zakresem);
- **Dalej** — problemy następne w kolejce, z hipotezami rozwiązań, bez zobowiązań co do funkcji;
- **Później** — szanse i obszary do zbadania, bez rozwiązań.
Każda pozycja: problem lub szansa, wynik i metryka, dowody, pewność. Daty tylko tam, gdzie jest zewnętrzne
zobowiązanie (przepis, umowa, wydarzenie). Przegląd po każdym wydaniu: pozycje przesuwają się według wyników,
a nie według kalendarza. Interesariuszom pokazujesz, co chcemy zmienić i jak to zmierzymy (pm-stakeholders).

## Źródła
- C. Bryar, B. Carr, *Working Backwards* (2021) — komunikat prasowy i FAQ przed budową (praktyka Amazon).
- J. Bastow, roadmapa teraz / dalej / później (ProdPad, 2012 i późniejsze opisy).
- J. Gothelf, J. Seiden, *Lean UX* (wyd. 3, 2021) — hipoteza z wynikiem i metryką.
Opisane własnymi słowami.
