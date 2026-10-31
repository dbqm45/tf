# Model zastępczy w optymalizacji i rejestr hipotez

## 1. Model zastępczy w pętli optymalizacji
Szybki model (np. sieć) zastępuje drogi symulator, a algorytm szuka na nim najlepszego projektu:
1. **Augmentacja a podział:** przykłady z augmentacji (odbicie, obrót) trafiają do tego samego zbioru co oryginał,
   inaczej wynik testu jest zawyżony (`wyciek-i-podzialy.md`). Uśrednianie predykcji dla wersji symetrycznych
   w czasie testu to tani zysk.
2. **Optymalizacja wyszukuje błędy modelu na swoją korzyść.** Zwycięzca zawsze wygląda lepiej, niż jest. Wynik
   sprawdzasz prawdziwym symulatorem albo eksperymentem, a raport podaje **obie liczby**: przewidzianą i zmierzoną.
3. **Cel spoza zakresu danych treningowych** (także fizycznie niemożliwy) daje pewną, złą odpowiedź. Najpierw liczysz
   granicę wykonalności, potem szukasz.
4. **Algorytm ewolucyjny:** zbyt duża mutacja zamienia przeszukiwanie w losowanie; parametry operatorów to też
   hiperparametry do sprawdzenia.
Źródło: A. Janmohamed, „How I Recreated a Research Paper…” (2026-10-22); liczby autora [niezweryfikowane].

## 2. Rejestr hipotez jako graf z werdyktami
- Hipoteza, której nie da się przypiąć do węzła ontologii (mechanizm, naruszone założenie, kto jest po drugiej
  stronie), odpada przed kosztownym eksperymentem.
- **Status węzła wynika z wyników eksperymentów** (potwierdzony / pogrzebany), nie z deklaracji autora.
- Pogrzebany węzeł ma zapisany z góry **warunek ponownego otwarcia** (nowa konstrukcja, niezależne potwierdzenie) —
  bez niego zespół wraca do tych samych pomysłów co kwartał.
- Zapis „próbowano, tak się nie udało” ma zakres i warunki eksperymentu. Im szersze twierdzenie, tym więcej
  niezależnych porażek potrzeba do jego odrzucenia.
- Luki wskazuje topologia grafu (rodziny bez mechanizmów), nie pytanie do modelu.
- Prosta implementacja: SQLite z tabelami `nodes` i `edges` (klucz krawędzi = cała trójka), graf w pamięci tylko do
  odczytu. Wybór kręgosłupa ontologii decyduje, które pytania są tanie.
