# Podziały danych i wyciek

Wyciek (leakage) to informacja z testu lub z przyszłości, która dostaje się do treningu. Wynik jest wtedy
zawyżony, a model po wdrożeniu rozczarowuje. Kapoor i Narayanan (Patterns 2023) opisują osiem typów wycieku, od
błędów podręcznikowych po otwarte problemy badawcze.

## Dobór podziału
| Sytuacja | Podział |
|---|---|
| dane z czasem, model przewiduje przyszłość | czasowy: trening wcześniej, test później; walidacja kroczącym oknem |
| wiele wierszy na tę samą jednostkę (klient, pacjent, urządzenie, dokument) | grupowy (GroupKFold): jednostka po jednej stronie |
| oba naraz | czasowy z grupami: jednostka nie przechodzi przez granicę |
| duplikaty i bliskie duplikaty (kopie tekstu, zrzuty tego samego obiektu) | deduplikacja przed podziałem, także przybliżona |
| rzadka klasa | warstwowy (stratified), ale nadal czasowy/grupowy, jeśli wymaga tego sytuacja |
| mało danych | walidacja krzyżowa zagnieżdżona (strojenie wewnątrz, ocena na zewnątrz) |

## Typowe źródła wycieku
- skalowanie, imputacja, selekcja cech lub PCA policzone na całym zbiorze przed podziałem;
- cecha znana dopiero po zdarzeniu (data zwrotu przy przewidywaniu zwrotu), w tym pochodna etykiety;
- ta sama jednostka w treningu i teście; duplikaty;
- etykiety tworzone na podstawie przyszłości względem momentu predykcji;
- strojenie hiperparametrów i wybór modelu na zbiorze testowym (cichy wyciek, najczęstszy);
- kontaminacja benchmarku: zbiór testowy lub jego odpowiedzi były w danych treningowych modelu bazowego.
  Dla modeli językowych sprawdź zgłaszane nakładanie się (n-gramy), użyj zbioru własnego lub utajonego i nie
  przypisuj przyrostu wyniku metodzie bez kontroli.

## Wykrywanie
1. Wynik zbyt dobry: porównaj z prostym baseline i z literaturą; skok o kilkanaście punktów to powód do audytu.
2. Kontrola negatywna: pomieszaj etykiety treningowe — wynik na teście ma spaść do poziomu losowego.
3. Ważność cech: cecha dominująca, której nie znasz w chwili predykcji, to podejrzany.
4. Test „w przód”: wytrenuj na starszych danych, oceń na najnowszych, nie widzianych w ogóle.
5. Różnica walidacja↔pilotaż większa niż rozrzut między seedami → szukaj wycieku lub dryfu.

## Higiena zbioru testowego
- Zbiór testowy zamrożony (skrót, data), dostęp ograniczony; liczba odczytów zapisana.
- Każdy odczyt „spala” zbiór: po wielu rundach zmian na podstawie testu traktuj go jak walidacyjny i zbierz nowy.
- Decyzje o architekturze, progu i cechach zapadają na walidacji.
- Raportuj wynik testu raz, razem z liczbą przebiegów strojenia, które do niego doprowadziły.
